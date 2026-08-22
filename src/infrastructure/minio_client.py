"""MinIO client wrapper for raw HTML/JSON storage with Gzip compression and metadata."""

import gzip
import hashlib
import io
import os
from datetime import UTC, datetime
from typing import Any

from minio import Minio
from minio.error import S3Error

from core.exceptions import StorageError
from infrastructure.storage_interface import (
    RawStorageClient,
    StoredObjectMetadata,
    StoredPayload,
)

METADATA_HEADER_KEY = "lumiscrape-meta"


class MinIOStorageClient(RawStorageClient):
    """MinIO implementation of RawStorageClient interface."""

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
        self.secret_key: str = secret_key or os.getenv("MINIO_SECRET_KEY") or "minioadminpassword"
        self.bucket_name: str = bucket_name or os.getenv("MINIO_BUCKET_NAME") or "lumiscrape-raw"
        self.secure = secure
        self._client: Minio | None = None

    @property
    def client(self) -> Minio:
        """Lazy initialization of Minio client."""
        if self._client is None:
            self._client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
        return self._client

    def ensure_bucket(self) -> None:
        """Ensures that the target bucket exists in MinIO."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except Exception as e:
            raise StorageError(
                f"Failed to verify or create bucket '{self.bucket_name}': {e}"
            ) from e

    def save_raw_html(
        self,
        site_id: str,
        url: str,
        body: bytes | str,
        status_code: int = 200,
        content_type: str = "text/html",
    ) -> StoredObjectMetadata:
        """Gzip compresses the raw payload, uploads it to MinIO, and attaches metadata."""
        if isinstance(body, str):
            body_bytes = body.encode("utf-8")
        else:
            body_bytes = body

        uncompressed_size = len(body_bytes)
        sha256_hash = hashlib.sha256(body_bytes).hexdigest()
        now = datetime.now(UTC)

        date_prefix = now.strftime("%Y/%m/%d")
        timestamp_ms = int(now.timestamp() * 1000)
        object_key = f"{site_id}/{date_prefix}/{timestamp_ms}.html.gz"

        try:
            # Gzip compression
            compressed_buffer = io.BytesIO()
            with gzip.GzipFile(fileobj=compressed_buffer, mode="wb", mtime=0.0) as gz_file:
                gz_file.write(body_bytes)
            compressed_data = compressed_buffer.getvalue()
            compressed_size = len(compressed_data)

            metadata = StoredObjectMetadata(
                object_key=object_key,
                site_id=site_id,
                url=url,
                status_code=status_code,
                content_type=content_type,
                fetched_at=now,
                compressed_size=compressed_size,
                uncompressed_size=uncompressed_size,
                sha256_checksum=sha256_hash,
                is_gzipped=True,
            )

            user_meta: dict[str, Any] = {
                METADATA_HEADER_KEY: metadata.model_dump_json(),
            }

            self.ensure_bucket()

            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_key,
                data=io.BytesIO(compressed_data),
                length=compressed_size,
                content_type="application/gzip",
                metadata=user_meta,
            )
            return metadata
        except Exception as e:
            raise StorageError(f"Failed to upload raw response to MinIO '{object_key}': {e}") from e

    def get_raw_html(self, object_key: str) -> StoredPayload:
        """Fetches, decompresses raw HTML from MinIO, and parses attached metadata."""
        try:
            stat = self.client.stat_object(self.bucket_name, object_key)
            response = self.client.get_object(self.bucket_name, object_key)
            try:
                raw_data = response.read()
            finally:
                response.close()
                response.release_conn()

            meta_dict = stat.metadata or {}
            raw_meta_json = meta_dict.get(f"x-amz-meta-{METADATA_HEADER_KEY}")

            if raw_meta_json:
                metadata = StoredObjectMetadata.model_validate_json(raw_meta_json)
            else:
                site_id = object_key.split("/")[0] if "/" in object_key else "unknown"
                metadata = StoredObjectMetadata(
                    object_key=object_key,
                    site_id=site_id,
                    url=f"s3://{self.bucket_name}/{object_key}",
                    status_code=200,
                    content_type="text/html",
                    fetched_at=stat.last_modified or datetime.now(UTC),
                    compressed_size=len(raw_data),
                    uncompressed_size=len(raw_data),
                    sha256_checksum=stat.etag or "",
                    is_gzipped=object_key.endswith(".gz"),
                )

            # Decompress Gzip
            if object_key.endswith(".gz") or metadata.is_gzipped:
                with gzip.GzipFile(fileobj=io.BytesIO(raw_data), mode="rb") as gz_file:
                    content_str = gz_file.read().decode("utf-8", errors="replace")
            else:
                content_str = raw_data.decode("utf-8", errors="replace")

            return StoredPayload(content=content_str, metadata=metadata)
        except Exception as e:
            raise StorageError(f"Failed to fetch raw HTML from MinIO '{object_key}': {e}") from e

    def list_objects(
        self, site_id: str | None = None, prefix: str | None = None
    ) -> list[StoredObjectMetadata]:
        """Lists objects within bucket, optionally filtered by site_id and prefix."""
        search_prefix = ""
        if site_id:
            search_prefix = f"{site_id}/"
        if prefix:
            search_prefix += prefix

        try:
            objects: list[StoredObjectMetadata] = []
            minio_objs = self.client.list_objects(
                self.bucket_name, prefix=search_prefix, recursive=True
            )
            for obj in minio_objs:
                if not obj.object_name:
                    continue
                site_part = obj.object_name.split("/")[0] if "/" in obj.object_name else "unknown"
                metadata = StoredObjectMetadata(
                    object_key=obj.object_name,
                    site_id=site_part,
                    url=f"s3://{self.bucket_name}/{obj.object_name}",
                    status_code=200,
                    content_type="application/gzip"
                    if obj.object_name.endswith(".gz")
                    else "text/html",
                    fetched_at=obj.last_modified or datetime.now(UTC),
                    compressed_size=obj.size or 0,
                    uncompressed_size=obj.size or 0,
                    sha256_checksum=obj.etag or "",
                    is_gzipped=obj.object_name.endswith(".gz"),
                )
                objects.append(metadata)
            return objects
        except Exception as e:
            raise StorageError(
                f"Failed to list objects in MinIO with prefix '{search_prefix}': {e}"
            ) from e

    def exists(self, object_key: str) -> bool:
        """Checks if the object exists in MinIO."""
        try:
            self.client.stat_object(self.bucket_name, object_key)
            return True
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket", "ResourceNotFound"):
                return False
            raise StorageError(f"Error checking existence of '{object_key}': {e}") from e
        except Exception as e:
            raise StorageError(f"Unexpected error checking existence of '{object_key}': {e}") from e

    def delete_object(self, object_key: str) -> bool:
        """Deletes object from MinIO."""
        try:
            self.client.remove_object(self.bucket_name, object_key)
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete object '{object_key}': {e}") from e
