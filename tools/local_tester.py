#!/usr/bin/env python3
"""Local testing CLI to run a Scrapy spider and verify MinIO raw storage."""

import argparse
import sys
from pathlib import Path

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))


def main() -> None:
    parser = argparse.ArgumentParser(description="Test a lumiscrape spider locally.")
    parser.add_argument("spider_name", help="Name of the spider to crawl (e.g. equal_love)")
    parser.add_argument(
        "--output",
        "-o",
        help="Optional local output file path for items (e.g. output.json)",
        default=None,
    )
    args = parser.parse_args()

    print(f"Starting local crawl for spider: {args.spider_name}")
    settings = get_project_settings()
    settings.setmodule("scrapers.scrapy_project.settings")

    if args.output:
        settings.set("FEEDS", {args.output: {"format": "json", "overwrite": True}})

    process = CrawlerProcess(settings)
    process.crawl(args.spider_name)
    process.start()
    print(f"Finished crawling spider: {args.spider_name}")


if __name__ == "__main__":
    main()
