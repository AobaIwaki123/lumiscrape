import logging
from datetime import UTC, datetime

import pytest
from scrapy.http import HtmlResponse, Request

from infrastructure.storage_interface import StoredObjectMetadata
from scrapers.base_crawler import BaseRawCrawler
from scrapers.scrapy_project.spiders.equal_love import EqualLoveSpider


def test_base_raw_crawler_initialization() -> None:
    spider = BaseRawCrawler()
    assert spider.name == "base_raw_crawler"
    assert spider.start_urls == []
    assert spider.render_js is False


def test_equal_love_spider_attributes() -> None:
    spider = EqualLoveSpider()
    assert spider.name == "equal_love"
    assert spider.start_urls == ["https://equal-love.jp/schedule/"]
    assert issubclass(EqualLoveSpider, BaseRawCrawler)


def test_start_requests_generation() -> None:
    spider = EqualLoveSpider()
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert isinstance(requests[0], Request)
    assert requests[0].url == "https://equal-love.jp/schedule/"
    assert requests[0].meta.get("site_id") == "equal_love"
    assert requests[0].meta.get("render_js") is False


def test_parse_with_storage_metadata() -> None:
    spider = EqualLoveSpider()
    mock_meta = StoredObjectMetadata(
        object_key="equal_love/2026/08/22/1000.html.gz",
        site_id="equal_love",
        url="https://equal-love.jp/schedule/",
        status_code=200,
        content_type="text/html",
        fetched_at=datetime.now(UTC),
        compressed_size=500,
        uncompressed_size=2000,
        sha256_checksum="mockhash",
        is_gzipped=True,
    )

    request = Request(url="https://equal-love.jp/schedule/")
    response = HtmlResponse(
        url="https://equal-love.jp/schedule/",
        request=request,
        body=b"<html><body><h1>=LOVE Schedule</h1></body></html>",
        encoding="utf-8",
    )
    response.meta["storage_metadata"] = mock_meta

    results = list(spider.parse(response))
    assert len(results) == 1
    item = results[0]
    assert item.site_id == "equal_love"
    assert item.url == "https://equal-love.jp/schedule/"
    assert item.content_length == 500
    assert item.is_gzipped is True


def test_parse_without_storage_metadata(caplog: pytest.LogCaptureFixture) -> None:
    spider = EqualLoveSpider()
    request = Request(url="https://equal-love.jp/schedule/")
    response = HtmlResponse(
        url="https://equal-love.jp/schedule/",
        request=request,
        body=b"<html><body><h1>Empty</h1></body></html>",
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        results = list(spider.parse(response))
        assert len(results) == 0
        assert "Raw payload was not saved to MinIO" in caplog.text
