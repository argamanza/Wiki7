API_BASE_URL = "http://localhost:8000"
CLUB_ID = 2976

# Season range (inclusive)
SEASON_START = 2024
SEASON_END = 2024
SEASON_RANGE = list(range(SEASON_START, SEASON_END + 1))

# Request retry settings
MAX_RETRIES = 3
RETRY_BASE_DELAY_SECONDS = 15

# Sleep settings to avoid rate limiting
SLEEP_SEASON_MIN = 1.5
SLEEP_SEASON_MAX = 5.0
SLEEP_PROFILE_MIN = 5
SLEEP_PROFILE_MAX = 30

# SSL verification (set to False to suppress InsecureRequestWarning)
VERIFY_SSL = False