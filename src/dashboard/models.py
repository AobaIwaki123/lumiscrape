"""Data models for the lumiscrape management dashboard."""

from datetime import datetime

from pydantic import BaseModel, Field


class SiteConfig(BaseModel):
    """Configuration for a registered crawling target site."""

    site_id: str = Field(description="Unique site identifier (e.g. equal_love)")
    name: str = Field(description="Human readable site title")
    url: str = Field(description="Seed URL to crawl")
    cron_schedule: str | None = Field(default="0 */6 * * *", description="Cron schedule expression")
    render_js: bool = Field(default=False, description="Whether to use Browserless rendering")
    enabled: bool = Field(default=True, description="Whether automated crawling is enabled")
    minio_object_count: int = Field(default=0, description="Total raw objects stored in MinIO")
    last_fetched_at: datetime | None = Field(
        default=None, description="Timestamp of most recent crawl"
    )


class JobExecutionRecord(BaseModel):
    """Execution status and metadata of a Kubernetes crawler Job."""

    job_name: str = Field(description="Kubernetes Job name")
    site_id: str = Field(description="Target site identifier")
    status: str = Field(description="Job status: Pending, Running, Completed, Failed")
    started_at: datetime | None = Field(default=None, description="Job start timestamp")
    completed_at: datetime | None = Field(default=None, description="Job completion timestamp")
    duration_seconds: int | None = Field(default=None, description="Execution duration in seconds")
