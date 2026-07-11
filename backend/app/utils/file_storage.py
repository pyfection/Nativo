"""
File storage for user uploads (audio + future image attachments), with two
interchangeable backends behind one API:

- **Local disk** (default, dev): files land under `UPLOADS_DIR` (default
  `<repo>/uploads`) and are served by the StaticFiles mount in main.py.
- **S3-compatible object storage** (production): enabled by setting
  `BUCKET_NAME` (or `S3_BUCKET`). Credentials/endpoint come from the usual
  AWS env vars — on Fly, `fly storage create` (Tigris) sets BUCKET_NAME,
  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_ENDPOINT_URL_S3 and
  AWS_REGION automatically. Reads are served by a redirect route in main.py
  that hands the browser a short-lived presigned URL, so the bucket can stay
  private and nothing else changes.

Either way the stored `Audio.file_path` is the same URL path
(`/uploads/audio/<yyyy>/<mm>/<uuid>.<ext>`), so switching backends never
invalidates existing rows — after copying the blobs across with
`backend/scripts/migrate_uploads_to_s3.py`.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

# Sentinel value: where to write files on disk (local backend only).
UPLOADS_ROOT = Path(os.environ.get("UPLOADS_DIR", "uploads")).resolve()

# Subdirectory under UPLOADS_ROOT for audio (kept narrow so the same util can
# later add `images/` etc. without ambiguity).
AUDIO_SUBDIR = "audio"

# Whitelist of MIME types we accept for audio. Browser MediaRecorder emits
# webm/opus by default; mp3/wav are accepted for desktop file uploads. Other
# types are rejected by the endpoint, not silently accepted with a wrong ext.
ALLOWED_AUDIO_MIME = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/flac": ".flac",
}

# Soft cap so a single contributor can't fill the volume with one upload.
# Tuned for ~30-60 second recordings; raise once we have proper transcoding.
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MiB

# How long presigned GET URLs stay valid. Long enough to finish playing a
# recording after the page loaded, short enough that shared links go stale.
PRESIGN_EXPIRY_SECONDS = 3600


class StorageError(Exception):
    """Raised on rejected uploads (bad mime, too large, write failure)."""


def s3_bucket() -> str | None:
    """The configured object-storage bucket, or None for local disk."""
    return os.environ.get("BUCKET_NAME") or os.environ.get("S3_BUCKET") or None


@lru_cache(maxsize=1)
def _s3_client():
    # boto3 is imported lazily so local-disk deployments never pay for it.
    import boto3

    return boto3.client("s3", endpoint_url=os.environ.get("AWS_ENDPOINT_URL_S3") or None)


def _resolve_extension(mime_type: str, original_filename: str | None) -> str:
    ext = ALLOWED_AUDIO_MIME.get(mime_type.lower())
    if ext is None:
        # Fall back to the original filename extension if the browser-reported
        # mime is unhelpful (e.g. application/octet-stream from some upload
        # flows). Even then, only honour an ext we'd accept.
        if original_filename:
            guess = "." + original_filename.rsplit(".", 1)[-1].lower()
            if guess in set(ALLOWED_AUDIO_MIME.values()):
                ext = guess
        if ext is None:
            raise StorageError(f"Unsupported audio type: {mime_type!r}")
    return ext


def store_audio(
    raw_bytes: bytes,
    mime_type: str,
    original_filename: str | None = None,
) -> tuple[str, int]:
    """Persist an audio blob and return (url_path, byte_size).

    The returned `url_path` is what to store on `Audio.file_path`; it's the
    public URL prefix `/uploads/audio/<yyyy>/<mm>/<uuid>.<ext>`. The byte size
    matches `len(raw_bytes)` and is what to store on `Audio.file_size`.
    """
    if not raw_bytes:
        raise StorageError("Empty upload.")
    if len(raw_bytes) > MAX_AUDIO_BYTES:
        raise StorageError(f"File too large ({len(raw_bytes)} bytes; max {MAX_AUDIO_BYTES}).")

    ext = _resolve_extension(mime_type, original_filename)

    now = datetime.now(UTC)
    key = f"{AUDIO_SUBDIR}/{now.year:04d}/{now.month:02d}/{uuid.uuid4().hex}{ext}"

    bucket = s3_bucket()
    if bucket:
        try:
            _s3_client().put_object(
                Bucket=bucket,
                Key=key,
                Body=raw_bytes,
                ContentType=mime_type,
            )
        except Exception as exc:  # boto's error zoo — surface as one type
            raise StorageError(f"Object storage write failed: {exc}") from exc
    else:
        abs_path = UPLOADS_ROOT / key
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(raw_bytes)

    return f"/uploads/{key}", len(raw_bytes)


def presigned_url(key: str, expires: int = PRESIGN_EXPIRY_SECONDS) -> str:
    """Short-lived GET URL for an object-storage key (S3 backend only)."""
    bucket = s3_bucket()
    if not bucket:
        raise StorageError("Object storage is not configured.")
    return _s3_client().generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires,
    )


def delete_blob(url_path: str) -> bool:
    """Best-effort deletion of the blob behind a stored `file_path`.

    Returns True if a blob was deleted, False if there was nothing to delete
    or the path is not ours. Never raises — a DB delete must not fail because
    the blob is already gone.
    """
    prefix = "/uploads/"
    if not url_path.startswith(prefix):
        return False
    key = url_path[len(prefix):]

    bucket = s3_bucket()
    if bucket:
        try:
            _s3_client().delete_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    abs_path = (UPLOADS_ROOT / key).resolve()
    # Refuse anything that escapes the uploads root (defence against a
    # tampered file_path ending up in the DB).
    if not abs_path.is_relative_to(UPLOADS_ROOT):
        return False
    try:
        abs_path.unlink()
        return True
    except FileNotFoundError:
        return False
