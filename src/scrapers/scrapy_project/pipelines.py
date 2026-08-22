"""Item pipelines for Pydantic validation and PostgreSQL persistence."""

import logging
from typing import Any

from core.exceptions import ParseError
from core.schemas import EventSchedule
from infrastructure.db_client import PostgresClient
from scrapers.scrapy_project.items import EventItem

logger = logging.getLogger(__name__)


class PydanticValidationPipeline:
    """Validates scraped event records against canonical Pydantic model."""

    def process_item(self, item: Any, _spider: Any = None) -> Any:
        if isinstance(item, EventItem):
            event = item.get("event_model")
            if not isinstance(event, EventSchedule):
                raise ParseError(f"Item event_model is not an EventSchedule instance: {event}")
        return item


class PostgresPersistencePipeline:
    """Persists validated events into PostgreSQL master database."""

    def __init__(self) -> None:
        self.db = PostgresClient()

    def open_spider(self, _spider: Any = None) -> None:
        try:
            self.db.init_tables()
        except Exception as e:
            logger.warning("Could not initialize DB tables on open_spider: %s", e)

    def process_item(self, item: Any, _spider: Any = None) -> Any:
        if isinstance(item, EventItem):
            event = item.get("event_model")
            if isinstance(event, EventSchedule):
                try:
                    self.db.upsert_events([event])
                except Exception as e:
                    logger.error("Failed to persist event into PostgreSQL: %s", e)
        return item
