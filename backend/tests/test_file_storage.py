"""
Tests for the two file-storage backends behind store_audio/delete_blob.

Local disk is the default; the S3 path is exercised against moto's mock so
no network or credentials are involved. Both must return identical
`/uploads/...` url paths so switching backends never breaks stored rows.
"""

import os

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from app.utils import file_storage  # noqa: E402
from app.utils.file_storage import StorageError, delete_blob, store_audio  # noqa: E402


@pytest.fixture
def local_root(tmp_path, monkeypatch):
    """Point the local backend at a temp dir and make sure S3 is off."""
    monkeypatch.delenv("BUCKET_NAME", raising=False)
    monkeypatch.delenv("S3_BUCKET", raising=False)
    monkeypatch.setattr(file_storage, "UPLOADS_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def s3_backend(monkeypatch):
    """moto-mocked bucket configured via env, client cache cleared."""
    moto = pytest.importorskip("moto")
    with moto.mock_aws():
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
        monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
        monkeypatch.delenv("AWS_ENDPOINT_URL_S3", raising=False)
        monkeypatch.setenv("BUCKET_NAME", "test-uploads")
        file_storage._s3_client.cache_clear()
        client = file_storage._s3_client()
        client.create_bucket(Bucket="test-uploads")
        yield client
    file_storage._s3_client.cache_clear()


def test_local_store_and_delete(local_root):
    url_path, size = store_audio(b"RIFFdata", "audio/wav")
    assert url_path.startswith("/uploads/audio/")
    assert url_path.endswith(".wav")
    assert size == 8

    on_disk = local_root / url_path.removeprefix("/uploads/")
    assert on_disk.read_bytes() == b"RIFFdata"

    assert delete_blob(url_path) is True
    assert not on_disk.exists()
    assert delete_blob(url_path) is False  # already gone — still no raise


def test_local_delete_refuses_path_escape(local_root):
    (local_root.parent / "victim.txt").write_text("keep me")
    assert delete_blob("/uploads/../victim.txt") is False
    assert (local_root.parent / "victim.txt").exists()


def test_rejects_bad_uploads(local_root):
    with pytest.raises(StorageError):
        store_audio(b"", "audio/wav")
    with pytest.raises(StorageError):
        store_audio(b"x", "video/mp4")
    with pytest.raises(StorageError):
        store_audio(b"x" * (file_storage.MAX_AUDIO_BYTES + 1), "audio/wav")


def test_filename_extension_fallback(local_root):
    url_path, _ = store_audio(b"data", "application/octet-stream", "voice-note.mp3")
    assert url_path.endswith(".mp3")
    with pytest.raises(StorageError):
        store_audio(b"data", "application/octet-stream", "notes.txt")


def test_s3_store_presign_delete(s3_backend):
    url_path, size = store_audio(b"opusdata", "audio/webm")
    assert url_path.startswith("/uploads/audio/")
    assert size == 8

    key = url_path.removeprefix("/uploads/")
    obj = s3_backend.get_object(Bucket="test-uploads", Key=key)
    assert obj["Body"].read() == b"opusdata"
    assert obj["ContentType"] == "audio/webm"

    signed = file_storage.presigned_url(key)
    assert key in signed and "Signature" in signed

    assert delete_blob(url_path) is True
    with pytest.raises(Exception):
        s3_backend.get_object(Bucket="test-uploads", Key=key)


def test_presign_requires_bucket(local_root):
    with pytest.raises(StorageError):
        file_storage.presigned_url("audio/2026/07/x.webm")
