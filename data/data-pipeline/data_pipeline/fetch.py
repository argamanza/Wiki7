import requests
from data_pipeline import config

def fetch_all_season_players():
    all_players = []
    for year in config.SEASON_RANGE:
        r = requests.get(f"{config.API_BASE_URL}/clubs/{config.CLUB_ID}/players?season_id={year}")
        if r.ok:
            data = r.json()
            all_players.extend(data.get("players", []))
    return all_players
