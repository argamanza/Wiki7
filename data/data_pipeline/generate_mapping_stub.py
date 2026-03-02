"""Generate a Hebrew mapping stub YAML from normalized player/transfer data.

Creates a YAML file with all unique positions, clubs, nationalities, and
player names that need Hebrew translation. Existing translations are preserved.

Usage:
    python -m data_pipeline.generate_mapping_stub [--players-path PATH] [--transfers-path PATH] [--mapping-path PATH]
"""

import json
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_PLAYERS_PATH = Path(__file__).resolve().parent / "output" / "merged" / "players.jsonl"
DEFAULT_TRANSFERS_PATH = Path(__file__).resolve().parent / "output" / "merged" / "transfers.jsonl"
DEFAULT_MAPPING_PATH = Path(__file__).resolve().parent / "output" / "merged" / "mappings.he.yaml"


def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_existing_mapping(mapping_path):
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def generate_stub(
    players_path: Path | None = None,
    transfers_path: Path | None = None,
    mapping_path: Path | None = None,
):
    """Generate or update the Hebrew mapping stub YAML."""
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
        nat for p in players for nat in p.get("nationality", []) or []
    })
    missing_name_he = sorted({
        p["name_english"] for p in players if not p.get("name_hebrew")
    })

    # Use existing or fallback to empty dict
    position_map = existing.get("positions", {})
    club_map = existing.get("clubs", {})
    nationality_map = existing.get("nationalities", {})
    names_map = existing.get("names", {})

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
    logger.info(
        "  %d positions, %d clubs, %d nationalities, %d names",
        len(position_map), len(club_map), len(nationality_map), len(names_map),
    )


def main():
    """CLI entry point."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Generate Hebrew mapping stub YAML")
    parser.add_argument("--players-path", type=Path, default=None)
    parser.add_argument("--transfers-path", type=Path, default=None)
    parser.add_argument("--mapping-path", type=Path, default=None)
    args = parser.parse_args()

    generate_stub(
        players_path=args.players_path,
        transfers_path=args.transfers_path,
        mapping_path=args.mapping_path,
    )


if __name__ == "__main__":
    main()
