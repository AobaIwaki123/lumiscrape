"""Downloader middlewares for raw payload preservation to MinIO."""

import logging
from typing import Any

from scrapy import signals
from scrapy.http import Request, Response

from infrastructure.minio_client import MinIOStorageClient

logger = logging.getLogger(__name__)


class MinIORawStorageMiddleware:
    """Saves raw HTTP response to MinIO immediately upon receipt."""

    def __init__(self) -> None:
        self.storage = MinIOStorageClient()

    @classmethod
    def from_crawler(cls, crawler: Any) -> "MinIORawStorageMiddleware":
        mw = cls()
        crawler.signals.connect(mw.spider_opened, signal=signals.spider_opened)
        return mw

    def spider_opened(self, spider: Any) -> None:
        logger.info("MinIORawStorageMiddleware initialized for spider: %s", spider.name)

    def process_response(
        self, request: Request, response: Response, spider: Any = None, **_kwargs: Any
    ) -> Response:
        """Uploads raw response body to MinIO and attaches object key to request.meta."""
        try:
            site_id = getattr(spider, "name", "unknown")
            raw_content_type = response.headers.get(b"Content-Type")
            content_type = raw_content_type.decode("utf-8") if raw_content_type else "text/html"
            stored_meta = self.storage.save_raw_html(
                site_id=site_id,
                url=response.url,
                body=response.body,
                status_code=response.status,
                content_type=content_type,
            )
            request.meta["raw_payload_key"] = stored_meta.object_key
            response.meta["raw_payload_key"] = stored_meta.object_key
            response.meta["storage_metadata"] = stored_meta
        except Exception as e:
            logger.warning("Failed to save raw response to MinIO: %s", e)

        return response
