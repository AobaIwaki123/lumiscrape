#!/usr/bin/env python3
"""Local testing helper script for running Scrapy spiders locally."""

import sys

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


def run_spider(spider_name: str) -> None:
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(spider_name)
    process.start()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/local_tester.py <spider_name>")
        sys.exit(1)
    run_spider(sys.argv[1])
