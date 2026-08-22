"""MinIO client wrapper for raw HTML/JSON storage with Gzip compression."""

import gzip
import io
import os
from datetime import UTC, datetime

from minio import Minio

from core.exceptions import StorageError
from core.schemas import ScrapeMetadata


class MinIOStorageClient:
    """Handles object storage interactions for raw scraping payloads."""

    def __init__(
        self,
        endpoint: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        bucket_name: str | None = None,
        secure: bool = False,
    ) -> None:
        self.endpoint: str = endpoint or os.getenv("MINIO_ENDPOINT") or "localhost:9000"
        self.access_key: str = access_key or os.getenv("MINIO_ACCESS_KEY") or "minioadmin"
        self.secret_key: str = secret_key or os.getenv("MINIO_SECRET_KEY") or "minioadmin"
        self.bucket_name: str = bucket_name or os.getenv("MINIO_BUCKET_NAME") or "lumiscrape-raw"
        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=secure,
        )

    def save_raw_response(
        self,
        site_id: str,
        url: str,
        body_bytes: bytes,
        status_code: int = 200,
        content_type: str = "text/html",
    ) -> str:
        """Gzip compresses the raw payload and uploads it to MinIO."""
        now = datetime.now(UTC)
        date_prefix = now.strftime("%Y/%m/%d")
        timestamp = int(now.timestamp())
        object_key = f"{site_id}/{date_prefix}/{timestamp}.html.gz"

        try:
            compressed_buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=compressed_buffer, mode="wb") as gz_file:
                gz_file.write(body_bytes)
            compressed_data = compressed_buffer.getvalue()

            metadata = ScrapeMetadata(
                site_id=site_id,
                url=url,
                status_code=status_code,
                content_type=content_type,
                fetched_at=now,
                content_length=len(compressed_data),
                is_gzipped=True,
            )

            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=io.BytesIO(compressed_data),
                length=len(compressed_data),
                content_type="application/gzip",
                metadata={"x-amz-meta-lumiscrape": metadata.model_dump_json()},
            )
            return object_key
        except Exception as e:
            raise StorageError(f"Failed to upload raw response to MinIO: {e}") from e

    def fetch_raw_html(self, object_key: str) -> str:
        """Fetches and decompresses raw HTML from MinIO."""
        try:
            response = self.client.get_object(self.bucket_name, object_key)
            compressed_data = response.read()
            response.close()
            response.release_conn()

            with gzip.GzipFile(fileobj=io.BytesIO(compressed_data), mode="rb") as gz_file:
                return gz_file.read().decode("utf-8", errors="replace")
        except Exception as e:
            raise StorageError(f"Failed to fetch raw HTML from MinIO: {e}") from e
