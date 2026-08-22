"""Scrapy settings for lumiscrape project."""

BOT_NAME = "lumiscrape"

SPIDER_MODULES = ["scrapers.scrapy_project.spiders"]
NEWSPIDER_MODULE = "scrapers.scrapy_project.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Concurrency and delays
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 1.0

# User-Agent
USER_AGENT = "lumiscrape/1.0 (+https://github.com/AobaIwaki123/lumiscrape)"

# Downloader Middlewares (hooks for MinIO raw upload & Browserless proxy)
DOWNLOADER_MIDDLEWARES = {
    "scrapers.scrapy_project.middlewares.MinIORawStorageMiddleware": 543,
}

# Item Pipelines (Pydantic validation and PostgreSQL persistence)
ITEM_PIPELINES = {
    "scrapers.scrapy_project.pipelines.PydanticValidationPipeline": 300,
    "scrapers.scrapy_project.pipelines.PostgresPersistencePipeline": 400,
}

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
