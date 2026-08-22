"""Pydantic schemas defining canonical domain models."""

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class EventSchedule(BaseModel):
    """Canonical schema for scraped event schedule data."""

    site_id: str = Field(description="Identifier for the source website")
    source_url: HttpUrl = Field(description="Original URL of the event")
    title: str = Field(description="Title of the event")
    start_at: datetime = Field(description="Event start timestamp (ISO8601)")
    end_at: datetime | None = Field(default=None, description="Event end timestamp (ISO8601)")
    venue: str | None = Field(default=None, description="Event venue or location")
    description: str | None = Field(default=None, description="Event details or description")
    raw_payload_key: str | None = Field(
        default=None, description="MinIO object key for raw HTML/JSON"
    )
    extracted_via: str = Field(
        default="mechanical", description="Extraction method: mechanical or llm_fallback"
    )


class ScrapeMetadata(BaseModel):
    """Metadata attached to raw crawled data stored in MinIO."""

    site_id: str = Field(description="Identifier for the source website")
    url: str = Field(description="Original scraped URL")
    status_code: int = Field(default=200, description="HTTP response status code")
    content_type: str = Field(default="text/html", description="HTTP Content-Type header")
    fetched_at: datetime = Field(description="Timestamp when payload was fetched")
    content_length: int = Field(description="Compressed payload size in bytes")
    is_gzipped: bool = Field(default=True, description="Whether the payload is Gzip compressed")
