"""Base raw crawler spider for universal data lake ingestion without per-site boilerplate."""

from collections.abc import Generator
from typing import Any

import scrapy
from scrapy.http import Request, Response

from core.schemas import ScrapeMetadata
from infrastructure.storage_interface import StoredObjectMetadata


class BaseRawCrawler(scrapy.Spider):
    """Base spider for collecting raw HTML/JSON directly into MinIO data lake.

    Subclasses only need to define `name` and `start_urls`.
    All raw payload persistence, Gzip compression, and metadata storage
    are handled automatically by the attached downloader middleware.
    """

    name: str = "base_raw_crawler"
    start_urls: list[str] = []
    render_js: bool = False
    custom_settings: dict[str, Any] = {
        "DOWNLOADER_MIDDLEWARES": {
            "scrapers.scrapy_project.middlewares.MinIORawStorageMiddleware": 543,
        },
        "ROBOTSTXT_OBEY": True,
        "CONCURRENT_REQUESTS": 8,
        "DOWNLOAD_TIMEOUT": 30,
    }

    def start_requests(self) -> Generator[Request, None, None]:
        """Generates initial requests with optional JS rendering flag in meta."""
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                meta={"render_js": self.render_js, "site_id": self.name},
                dont_filter=True,
            )

    def parse(self, response: Response, **_kwargs: Any) -> Generator[ScrapeMetadata, None, None]:
        """Default parse handler that yields the raw object metadata saved to MinIO."""
        storage_meta: StoredObjectMetadata | None = response.meta.get("storage_metadata")

        if storage_meta:
            self.logger.info(
                "Successfully persisted raw payload to MinIO: key=%s (site=%s, size=%d bytes)",
                storage_meta.object_key,
                storage_meta.site_id,
                storage_meta.compressed_size,
            )
            yield ScrapeMetadata(
                site_id=storage_meta.site_id,
                url=storage_meta.url,
                status_code=storage_meta.status_code,
                content_type=storage_meta.content_type,
                fetched_at=storage_meta.fetched_at,
                content_length=storage_meta.compressed_size,
                is_gzipped=storage_meta.is_gzipped,
            )
        else:
            self.logger.warning(
                "Raw payload was not saved to MinIO for response: url=%s (status=%d)",
                response.url,
                response.status,
            )
