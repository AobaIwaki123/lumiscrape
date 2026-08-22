import gzip
import io
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from infrastructure.minio_client import METADATA_HEADER_KEY, MinIOStorageClient
from infrastructure.storage_interface import (
    RawStorageClient,
    StoredObjectMetadata,
    StoredPayload,
)


def test_storage_interface_conformance() -> None:
    client = MinIOStorageClient()
    assert isinstance(client, RawStorageClient)


def test_stored_object_metadata_model() -> None:
    now = datetime.now(UTC)
    meta = StoredObjectMetadata(
        object_key="test_site/2026/08/22/1000.html.gz",
        site_id="test_site",
        url="https://example.com/test",
        status_code=200,
        content_type="text/html",
        fetched_at=now,
        compressed_size=120,
        uncompressed_size=500,
        sha256_checksum="abcdef123456",
        is_gzipped=True,
    )
    assert meta.object_key.startswith("test_site/")
    assert meta.compressed_size == 120
    assert meta.uncompressed_size == 500
    assert meta.is_gzipped is True


@patch("infrastructure.minio_client.Minio")
def test_save_raw_html(mock_minio_cls: MagicMock) -> None:
    mock_minio = MagicMock()
    mock_minio.bucket_exists.return_value = True
    mock_minio_cls.return_value = mock_minio

    client = MinIOStorageClient(endpoint="localhost:9000")
    html_content = "<html><body><h1>Hello World</h1></body></html>"

    meta = client.save_raw_html(
        site_id="sample_site",
        url="https://example.com/sample",
        body=html_content,
        status_code=200,
    )

    assert meta.site_id == "sample_site"
    assert meta.url == "https://example.com/sample"
    assert meta.uncompressed_size == len(html_content.encode("utf-8"))
    assert meta.is_gzipped is True
    assert mock_minio.put_object.called


@patch("infrastructure.minio_client.Minio")
def test_get_raw_html(mock_minio_cls: MagicMock) -> None:
    html_content = "<html><body><h1>Hello World</h1></body></html>"
    compressed_buf = io.BytesIO()
    with gzip.GzipFile(fileobj=compressed_buf, mode="wb", mtime=0.0) as gz:
        gz.write(html_content.encode("utf-8"))
    compressed_bytes = compressed_buf.getvalue()

    now = datetime.now(UTC)
    meta_model = StoredObjectMetadata(
        object_key="sample_site/2026/08/22/1000.html.gz",
        site_id="sample_site",
        url="https://example.com/sample",
        status_code=200,
        content_type="text/html",
        fetched_at=now,
        compressed_size=len(compressed_bytes),
        uncompressed_size=len(html_content.encode("utf-8")),
        sha256_checksum="hash123",
        is_gzipped=True,
    )

    mock_stat = MagicMock()
    mock_stat.metadata = {
        f"x-amz-meta-{METADATA_HEADER_KEY}": meta_model.model_dump_json(),
    }
    mock_stat.last_modified = now

    mock_resp = MagicMock()
    mock_resp.read.return_value = compressed_bytes

    mock_minio = MagicMock()
    mock_minio.stat_object.return_value = mock_stat
    mock_minio.get_object.return_value = mock_resp
    mock_minio_cls.return_value = mock_minio

    client = MinIOStorageClient(endpoint="localhost:9000")
    payload = client.get_raw_html("sample_site/2026/08/22/1000.html.gz")

    assert isinstance(payload, StoredPayload)
    assert payload.content == html_content
    assert payload.metadata.site_id == "sample_site"
    assert payload.metadata.url == "https://example.com/sample"
    assert payload.metadata.status_code == 200


@patch("infrastructure.minio_client.Minio")
def test_list_and_delete_objects(mock_minio_cls: MagicMock) -> None:
    mock_obj = MagicMock()
    mock_obj.object_name = "site_a/2026/08/22/1.html.gz"
    mock_obj.size = 150
    mock_obj.etag = "hash123"
    mock_obj.last_modified = datetime.now(UTC)

    mock_minio = MagicMock()
    mock_minio.list_objects.return_value = [mock_obj]
    mock_minio_cls.return_value = mock_minio

    client = MinIOStorageClient()
    items = client.list_objects(site_id="site_a")
    assert len(items) == 1
    assert items[0].object_key == "site_a/2026/08/22/1.html.gz"

    assert client.delete_object("site_a/2026/08/22/1.html.gz") is True
    assert mock_minio.remove_object.called
