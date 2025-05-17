# === Project identity ===
BOT_NAME = "tmk_scraper"
SPIDER_MODULES = ["tmk_scraper.spiders"]
NEWSPIDER_MODULE = "tmk_scraper.spiders"

# === ScraperAPI toggle ===
USE_SCRAPERAPI = True
SCRAPERAPI_KEY = "a0dd5b987ccf04c58d3347ba9edd1206"

# === Logging ===
LOG_LEVEL = "DEBUG"

# === Concurrency ===
CONCURRENT_REQUESTS = 5
CONCURRENT_REQUESTS_PER_DOMAIN = 5

# === Retry behavior ===
RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [500, 503, 504, 522, 524, 408, 429]
RETRY_BACKOFF_BASE = 2

# === User-Agent rotation ===
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,
    'scrapy_fake_useragent.middleware.RandomUserAgentMiddleware': 400,
    'scrapy_fake_useragent.middleware.RetryUserAgentMiddleware': 401,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 410,
}

FAKEUSERAGENT_PROVIDERS = [
    'scrapy_fake_useragent.providers.FakerProvider',
    'scrapy_fake_useragent.providers.FixedUserAgentProvider',
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# === Output ===
FEED_FORMAT = "json"
FEED_EXPORT_ENCODING = "utf-8"

# === Conditional tuning ===
if USE_SCRAPERAPI:
    DOWNLOAD_DELAY = 0
    AUTOTHROTTLE_ENABLED = False
else:
    DOWNLOAD_DELAY = 3
    AUTOTHROTTLE_ENABLED = True
    AUTOTHROTTLE_START_DELAY = 3
    AUTOTHROTTLE_MAX_DELAY = 30
    AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
    AUTOTHROTTLE_DEBUG = False
