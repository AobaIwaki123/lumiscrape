"""Thin spider definition for =LOVE (Equal Love) official schedule crawler."""

from scrapers.base_crawler import BaseRawCrawler


class EqualLoveSpider(BaseRawCrawler):
    """Raw data crawler for =LOVE official schedule page."""

    name: str = "equal_love"
    start_urls: list[str] = ["https://equal-love.jp/schedule/"]
