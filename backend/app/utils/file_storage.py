"""
Local-disk file storage for user uploads (audio + future image attachments).

The directory comes from the `UPLOADS_DIR` env var; in dev it defaults to
`<repo>/uploads`, in production (Fly) it's the mount path of the persistent
volume — `/data/uploads`. The chosen path is *also* mounted into the FastAPI
app at `/uploads/*` so files can be fetched without a separate auth call.

Files are stored under deterministic subdirectories so we can reason about
counts and add per-subdir rotation later if needed:

  uploads/
    audio/
      <yyyy>/<mm>/<uuid>.<ext>

The stored `file_path` we put on the Audio row is the URL path (`/uploads/…`),
not the on-disk path, so it's directly servable.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Sentinel value: where to write files on disk.
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


class StorageError(Exception):
    """Raised on rejected uploads (bad mime, too large, write failure)."""


def store_audio(
    raw_bytes: bytes,
    mime_type: str,
    original_filename: str | None = None,
) -> tuple[str, int]:
    """Persist an audio blob to disk and return (url_path, byte_size).

    The returned `url_path` is what to store on `Audio.file_path`; it's the
    public URL prefix `/uploads/audio/<yyyy>/<mm>/<uuid>.<ext>`. The byte size
    matches `len(raw_bytes)` and is what to store on `Audio.file_size`.
    """
    if not raw_bytes:
        raise StorageError("Empty upload.")
    if len(raw_bytes) > MAX_AUDIO_BYTES:
        raise StorageError(f"File too large ({len(raw_bytes)} bytes; max {MAX_AUDIO_BYTES}).")

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

    now = datetime.now(UTC)
    rel_dir = Path(AUDIO_SUBDIR) / f"{now.year:04d}" / f"{now.month:02d}"
    abs_dir = UPLOADS_ROOT / rel_dir
    abs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    abs_path = abs_dir / filename
    abs_path.write_bytes(raw_bytes)

    # URL path the client will fetch through (relative to the API origin).
    url_path = f"/uploads/{rel_dir.as_posix()}/{filename}"
    return url_path, len(raw_bytes)
