import requests
from data_pipeline import config
from time import sleep
import random

def retry_request(url, max_retries=config.MAX_RETRIES):
    retriable_statuses = {500, 502, 503, 504}
    for attempt in range(max_retries):
        try:
            r = requests.get(url, verify=config.VERIFY_SSL)
            if r.ok:
                return r.json()
            elif r.status_code in retriable_statuses:
                wait = config.RETRY_BASE_DELAY_SECONDS * (attempt + 1)
                print(f"{r.status_code} received from {url}. Retrying in {wait} seconds...")
                sleep(wait)
            else:
                print(f"Failed to fetch {url}: {r.status_code}")
                break
        except requests.RequestException as e:
            print(f"Request exception on {url}: {e}. Retrying...")
            sleep(config.RETRY_BASE_DELAY_SECONDS * (attempt + 1))
    return None

def fetch_all_season_players():
    all_players = []
    for year in config.SEASON_RANGE:
        print(f"Fetching {year}...", end="", flush=True)
        url = f"{config.API_BASE_URL}/clubs/{config.CLUB_ID}/players?season_id={year}"
        data = retry_request(url)
        if data:
            players = data.get("players", [])
            for _ in players:
                print(".", end="", flush=True)
            all_players.extend(players)
        print()  # new line after the year's progress
        sleep(random.uniform(config.SLEEP_SEASON_MIN, config.SLEEP_SEASON_MAX))
    return all_players

def fetch_generic(endpoint):
    url = f"{config.API_BASE_URL}{endpoint}"
    return retry_request(url)

def enrich_players(players_by_id):
    total = len(players_by_id)
    fetch_tasks = [
        ("/players/{}/profile", "profile updated"),
        ("/players/{}/market_value", "market value updated"),
        ("/players/{}/transfers", "transfers updated"),
        ("/players/{}/jersey_numbers", "jersey numbers updated"),
        ("/players/{}/stats", "stats updated"),
        ("/players/{}/achievements", "achievements updated"),
        ("/players/{}/injuries", "injuries updated"),
    ]

    for idx, (player_id, player_data) in enumerate(players_by_id.items(), start=1):
        for endpoint_template, label in fetch_tasks:
            endpoint = endpoint_template.format(player_id)
            result = fetch_generic(endpoint)
            if result:
                player_data.update(result)
                print(f"→ ({idx}/{total}) {player_data['name']} {label}")
            sleep(random.uniform(config.SLEEP_PROFILE_MIN, config.SLEEP_PROFILE_MAX))
