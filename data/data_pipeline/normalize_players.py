import json
from pathlib import Path
from data_pipeline.schemas import Player, MarketValue, Transfer
from data_pipeline.helpers import is_all_hebrew, parse_birth_date, parse_countries
from tqdm import tqdm
from typing import List


RAW_PATH = Path("../tmk-scraper/output/players.json")
OUT_DIR = Path("output")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def load_raw_players():
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_player(player) -> Player:
    facts = player.get("facts", {})

    name_hebrew = None  # Default in case the condition fails

    if is_all_hebrew(facts.get("Name in home country", "")):
        name_hebrew = facts.get("Name in home country")

    return Player(
        id=player["profile_url"].split("/")[-1],
        name_english=player["name"],
        name_hebrew=name_hebrew,
        birth_date=parse_birth_date(facts.get("Date of birth/Age", "").split(" (")[0]),
        nationality=parse_countries(facts.get("Citizenship")),
        main_position=player.get("positions", {}).get("main"),
        current_squad=not player.get("loaned", False),
        current_jersey_number=None if player["number"] == "-" else int(player["number"]),
    )

def normalize_transfers(player) -> List[Transfer]:
    uid = player["profile_url"].split("/")[-1]
    return [
        Transfer(
            player_id=uid,
            season=tr["season"],
            date=tr["date"],
            from_club=tr["from"],
            to_club=tr["to"],
            fee=tr["fee"],
            loan=("loan" in tr["fee"].lower())
        )
        for tr in player.get("transfers", [])
    ]

def normalize_market_values(player) -> List[MarketValue]:
    uid = player["profile_url"].split("/")[-1]
    return [
        MarketValue(
            player_id=uid,
            value_date=mv["date"],
            value=mv["value"],
            team=mv["team"]
        )
        for mv in player.get("market_value_history", [])
    ]

def write_jsonl(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(item.model_dump_json() + "\n")

def main():
    raw_players = load_raw_players()

    all_players = []
    all_transfers = []
    all_values = []

    for p in tqdm(raw_players):
        all_players.append(normalize_player(p))
        all_transfers.extend(normalize_transfers(p))
        all_values.extend(normalize_market_values(p))

    write_jsonl(all_players, OUT_DIR / "players.jsonl")
    write_jsonl(all_transfers, OUT_DIR / "transfers.jsonl")
    write_jsonl(all_values, OUT_DIR / "market_values.jsonl")

if __name__ == "__main__":
    main()
