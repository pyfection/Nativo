"""
One-off: copy existing local uploads into the configured object-storage
bucket, preserving keys, so stored `Audio.file_path` values keep working
after the switch.

Run *with the bucket env configured* (on Fly: `fly ssh console` after
`fly storage create`, or locally with the Tigris/S3 credentials exported):

    BUCKET_NAME=... AWS_ENDPOINT_URL_S3=... uv run python backend/scripts/migrate_uploads_to_s3.py

Idempotent: objects that already exist in the bucket (same key + size) are
skipped, so it's safe to re-run after a partial migration. Local files are
NOT deleted — remove the volume/directory yourself once you've verified.
"""

import mimetypes
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.file_storage import UPLOADS_ROOT, _s3_client, s3_bucket  # noqa: E402


def main() -> int:
    bucket = s3_bucket()
    if not bucket:
        print("BUCKET_NAME (or S3_BUCKET) is not set — nothing to migrate to.")
        return 1
    if not UPLOADS_ROOT.is_dir():
        print(f"No local uploads directory at {UPLOADS_ROOT} — nothing to migrate.")
        return 0

    client = _s3_client()
    uploaded = skipped = 0
    for path in sorted(UPLOADS_ROOT.rglob("*")):
        if not path.is_file():
            continue
        key = path.relative_to(UPLOADS_ROOT).as_posix()
        size = path.stat().st_size
        try:
            head = client.head_object(Bucket=bucket, Key=key)
            if head["ContentLength"] == size:
                skipped += 1
                continue
        except Exception:
            pass  # not there yet — upload below
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        client.put_object(
            Bucket=bucket, Key=key, Body=path.read_bytes(), ContentType=content_type
        )
        uploaded += 1
        print(f"uploaded  {key}  ({size} bytes)")

    print(f"Done: {uploaded} uploaded, {skipped} already present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
