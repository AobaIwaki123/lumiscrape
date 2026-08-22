"""Scrapy item definitions wrapping canonical Pydantic models."""

import scrapy


class EventItem(scrapy.Item):
    """Scrapy Item carrying canonical EventSchedule model instance."""

    event_model = scrapy.Field()
