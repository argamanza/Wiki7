import json
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_PLAYERS_PATH = Path(__file__).resolve().parent / "output" / "players.jsonl"
DEFAULT_TRANSFERS_PATH = Path(__file__).resolve().parent / "output" / "transfers.jsonl"
DEFAULT_MAPPING_PATH = Path(__file__).resolve().parent / "output" / "mappings.he.yaml"


def load_jsonl(path: Path) -> list:
    """Load a JSONL file into a list of dicts.

    Raises FileNotFoundError if the file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"JSONL file not found: {path}. "
            "Run the normalization pipeline first."
        )
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_existing_mapping(mapping_path: Path) -> dict:
    """Load an existing mapping file, or return empty dict if not found."""
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def main(
    players_path: Path | None = None,
    transfers_path: Path | None = None,
    mapping_path: Path | None = None,
) -> None:
    """Generate or update the Hebrew mapping stub YAML file."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    resolved_players = players_path or DEFAULT_PLAYERS_PATH
    resolved_transfers = transfers_path or DEFAULT_TRANSFERS_PATH
    resolved_mapping = mapping_path or DEFAULT_MAPPING_PATH

    players = load_jsonl(resolved_players)
    transfers = load_jsonl(resolved_transfers)
    existing = load_existing_mapping(resolved_mapping)

    # Extract unique values
    unique_positions = sorted({p["main_position"] for p in players if p.get("main_position")})
    unique_clubs = sorted(
        {t["from_club"] for t in transfers if t.get("from_club")}
        | {t["to_club"] for t in transfers if t.get("to_club")}
    )
    unique_nationalities = sorted({
        nat for p in players for nat in p.get("nationality", [])
    })
    missing_name_he = sorted({
        p["name_english"] for p in players if not p.get("name_hebrew")
    })

    # Use existing or fallback to empty dict
    position_map = existing.get("positions", {}) or {}
    club_map = existing.get("clubs", {}) or {}
    nationality_map = existing.get("nationalities", {}) or {}
    names_map = existing.get("names", {}) or {}

    # Update only missing keys
    for pos in unique_positions:
        position_map.setdefault(pos, "")
    for club in unique_clubs:
        club_map.setdefault(club, "")
    for nat in unique_nationalities:
        nationality_map.setdefault(nat, "")
    for name in missing_name_he:
        names_map.setdefault(name, "")

    # Combine and write
    updated = {
        "positions": position_map,
        "clubs": club_map,
        "nationalities": nationality_map,
        "names": names_map,
    }

    resolved_mapping.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved_mapping, "w", encoding="utf-8") as f:
        yaml.dump(updated, f, allow_unicode=True, sort_keys=False)

    logger.info("Updated mapping stub saved to %s", resolved_mapping)


if __name__ == "__main__":
    main()
