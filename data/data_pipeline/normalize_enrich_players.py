import json
import logging
import sys
from pathlib import Path
from data_pipeline.schemas import Player, MarketValue, Transfer
from data_pipeline.helpers import is_all_hebrew, parse_birth_date, parse_countries, is_homegrown, is_retired
from tqdm import tqdm
from typing import List

logger = logging.getLogger(__name__)

# Default paths — can be overridden via environment or function arguments
DEFAULT_RAW_PATH = Path(__file__).resolve().parent.parent / "tmk-scraper" / "output" / "players.json"
DEFAULT_OUT_DIR = Path(__file__).resolve().parent / "output"


def load_raw_players(raw_path: Path | None = None) -> list:
    """Load raw player JSON from the scraper output.

    Raises FileNotFoundError if the file does not exist.
    Raises json.JSONDecodeError if the file is not valid JSON.
    """
    path = raw_path or DEFAULT_RAW_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Raw players file not found: {path}. "
            "Have you run the squad and player spiders first?"
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(data).__name__}")
    return data


def normalize_player(player: dict) -> Player:
    """Normalize a single raw player dict into a Player schema object."""
    facts = player.get("facts", {})

    name_hebrew = None
    home_country_name = facts.get("Name in home country", "")
    if home_country_name and is_all_hebrew(home_country_name):
        name_hebrew = home_country_name

    try:
        jersey = int(player["number"]) if player.get("number", "-") != "-" else None
    except (ValueError, TypeError):
        logger.warning("Invalid jersey number %r for player %s", player.get("number"), player.get("name_english", "?"))
        jersey = None

    return Player(
        id=player["profile_url"].split("/")[-1],
        name_english=player["name_english"],
        name_hebrew=name_hebrew,
        birth_date=parse_birth_date(facts.get("Date of birth/Age", "").split(" (")[0]),
        birth_place=facts.get("Place of birth"),
        nationality=parse_countries(facts.get("Citizenship")),
        main_position=player.get("positions", {}).get("main"),
        current_squad=not player.get("loaned", False),
        current_jersey_number=jersey,
        homegrown=is_homegrown(player),
        retired=is_retired(player),
    )


def normalize_transfers(player: dict) -> List[Transfer]:
    """Extract and normalize transfer records from a raw player dict."""
    uid = player["profile_url"].split("/")[-1]
    transfers = []
    for tr in player.get("transfers", []):
        try:
            fee = tr.get("fee", "")
            transfers.append(Transfer(
                player_id=uid,
                season=tr["season"],
                transfer_date=tr["date"],
                from_club=tr["from"],
                to_club=tr["to"],
                fee=fee,
                loan=("loan" in fee.lower()) if fee else False,
            ))
        except (KeyError, TypeError) as exc:
            logger.warning("Skipping malformed transfer for player %s: %s", uid, exc)
    return transfers


def normalize_market_values(player: dict) -> List[MarketValue]:
    """Extract and normalize market value records from a raw player dict."""
    uid = player["profile_url"].split("/")[-1]
    values = []
    for mv in player.get("market_value_history", []):
        try:
            values.append(MarketValue(
                player_id=uid,
                value_date=mv["date"],
                value=mv["value"],
                team=mv["team"],
            ))
        except (KeyError, TypeError) as exc:
            logger.warning("Skipping malformed market value for player %s: %s", uid, exc)
    return values


def write_jsonl(data: list, path: Path) -> None:
    """Write a list of Pydantic models as newline-delimited JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(item.model_dump_json() + "\n")
    logger.info("Wrote %d records to %s", len(data), path)


def main(raw_path: Path | None = None, out_dir: Path | None = None) -> None:
    """Run the full normalization pipeline."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    resolved_out = out_dir or DEFAULT_OUT_DIR
    resolved_out.mkdir(parents=True, exist_ok=True)

    raw_players = load_raw_players(raw_path)
    logger.info("Loaded %d raw player records", len(raw_players))

    all_players: List[Player] = []
    all_transfers: List[Transfer] = []
    all_values: List[MarketValue] = []
    errors = 0

    for p in tqdm(raw_players, desc="Normalizing players"):
        try:
            all_players.append(normalize_player(p))
            all_transfers.extend(normalize_transfers(p))
            all_values.extend(normalize_market_values(p))
        except (KeyError, ValueError, TypeError) as exc:
            errors += 1
            logger.error("Failed to normalize player %s: %s", p.get("name_english", "?"), exc)

    write_jsonl(all_players, resolved_out / "players.jsonl")
    write_jsonl(all_transfers, resolved_out / "transfers.jsonl")
    write_jsonl(all_values, resolved_out / "market_values.jsonl")

    logger.info(
        "Normalization complete: %d players, %d transfers, %d market values (%d errors)",
        len(all_players), len(all_transfers), len(all_values), errors,
    )
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
