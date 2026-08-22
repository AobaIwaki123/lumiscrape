"""Storage interface and data contracts for object storage operations."""

from datetime import datetime
from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class StoredObjectMetadata(BaseModel):
    """Metadata describing a raw scrape object saved in storage."""

    object_key: str = Field(description="S3 object key path")
    site_id: str = Field(description="Target site identifier")
    url: str = Field(description="Source URL scraped")
    status_code: int = Field(default=200, description="HTTP status code")
    content_type: str = Field(default="text/html", description="Content-Type header")
    fetched_at: datetime = Field(description="Timestamp when payload was fetched")
    compressed_size: int = Field(description="Size in bytes after Gzip compression")
    uncompressed_size: int = Field(description="Original payload size in bytes")
    sha256_checksum: str = Field(description="Hex digest of uncompressed body")
    is_gzipped: bool = Field(default=True, description="Whether payload is Gzip compressed")


class StoredPayload(BaseModel):
    """Container for retrieved content and its attached metadata."""

    content: str = Field(description="Decompressed UTF-8 content string")
    metadata: StoredObjectMetadata = Field(description="Object metadata")


@runtime_checkable
class RawStorageClient(Protocol):
    """Protocol defining the In/Out interface for raw scraping data lake."""

    def save_raw_html(
        self,
        site_id: str,
        url: str,
        body: bytes | str,
        status_code: int = 200,
        content_type: str = "text/html",
    ) -> StoredObjectMetadata:
        """Compresses and uploads raw HTML to storage lake with attached metadata."""
        ...

    def get_raw_html(self, object_key: str) -> StoredPayload:
        """Retrieves and decompresses raw HTML and returns payload with metadata."""
        ...

    def list_objects(
        self, site_id: str | None = None, prefix: str | None = None
    ) -> list[StoredObjectMetadata]:
        """Lists stored objects filtered by site_id and prefix."""
        ...

    def exists(self, object_key: str) -> bool:
        """Checks if the specified object key exists in storage."""
        ...

    def delete_object(self, object_key: str) -> bool:
        """Deletes object from storage."""
        ...
