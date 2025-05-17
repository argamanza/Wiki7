# === Project identity ===
BOT_NAME = "tmk_scraper"
SPIDER_MODULES = ["tmk_scraper.spiders"]
NEWSPIDER_MODULE = "tmk_scraper.spiders"

# === Logging ===
# Controls verbosity of console output. Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
LOG_LEVEL = "INFO"

# === Crawl behavior ===
# Ignore robots.txt since Transfermarkt blocks bots
ROBOTSTXT_OBEY = False

# Allow cookies to help maintain session state if Transfermarkt sets them
COOKIES_ENABLED = True

# Delay between requests to avoid being flagged
DOWNLOAD_DELAY = 3

# Retry failed requests automatically (e.g. if rate limited)
RETRY_ENABLED = True
RETRY_TIMES = 5

# === Request headers ===
# Spoof a real browser to bypass basic bot detection
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# === Output settings ===
# Save scraped items to this file in JSON format
FEED_FORMAT = "json"
FEED_URI = "output/players.json"
FEED_EXPORT_ENCODING = "utf-8"
