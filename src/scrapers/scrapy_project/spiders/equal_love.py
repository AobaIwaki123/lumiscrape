"""Example Spider implementation for equal-love official schedule."""

from collections.abc import Generator
from datetime import datetime
from typing import Any

import scrapy
from pydantic import HttpUrl
from scrapy.http import Response

from core.schemas import EventSchedule
from scrapers.scrapy_project.items import EventItem


class EqualLoveSpider(scrapy.Spider):
    """Spider for crawling equal-love official site schedules."""

    name = "equal_love"
    allowed_domains = ["equal-love.jp"]
    start_urls = ["https://equal-love.jp/schedule/"]

    def parse(self, response: Response, **_kwargs: Any) -> Generator[EventItem, None, None]:
        """Parses schedule page and extracts event items."""
        raw_key = response.meta.get("raw_payload_key")

        for item_node in response.css("ul.schedule-list li, .schedule-item"):
            title = item_node.css(".title::text, h3::text").get(default="").strip()
            link = item_node.css("a::attr(href)").get(default=response.url)

            if not title:
                continue

            start_at = datetime.now()

            event = EventSchedule(
                site_id=self.name,
                source_url=HttpUrl(response.urljoin(link)),
                title=title,
                start_at=start_at,
                raw_payload_key=raw_key,
                extracted_via="mechanical",
            )
            yield EventItem(event_model=event)
