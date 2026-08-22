from datetime import UTC, datetime

from pydantic import HttpUrl

from core.schemas import EventSchedule, ScrapeMetadata


def test_event_schedule_schema() -> None:
    now = datetime.now(UTC)
    event = EventSchedule(
        site_id="test_site",
        source_url=HttpUrl("https://example.com/events/1"),
        title="Sample Concert",
        start_at=now,
        venue="Tokyo Dome",
    )
    assert event.site_id == "test_site"
    assert str(event.source_url) == "https://example.com/events/1"
    assert event.title == "Sample Concert"
    assert event.venue == "Tokyo Dome"
    assert event.extracted_via == "mechanical"


def test_scrape_metadata_schema() -> None:
    now = datetime.now(UTC)
    meta = ScrapeMetadata(
        site_id="test_site",
        url="https://example.com",
        status_code=200,
        content_type="text/html",
        fetched_at=now,
        content_length=1024,
    )
    assert meta.site_id == "test_site"
    assert meta.is_gzipped is True
