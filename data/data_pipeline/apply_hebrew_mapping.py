"""Apply Hebrew translations from mapping YAML to normalized player data.

Reads the reviewed mappings.he.yaml and applies Hebrew translations for
positions, nationalities, and player names to produce players.he.jsonl.

Usage:
    python -m data_pipeline.apply_hebrew_mapping [--input PATH] [--output PATH] [--mapping PATH]
"""

import json
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "merged" / "players.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "merged" / "players.he.jsonl"
DEFAULT_MAPPING = Path(__file__).resolve().parent / "output" / "merged" / "mappings.he.yaml"


def load_mapping(mapping_path: Path) -> dict:
    with open(mapping_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def apply_hebrew(player: dict, mapping: dict) -> dict:
    pos_map = mapping.get("positions", {})
    nationality_map = mapping.get("nationalities", {})
    names_map = mapping.get("names", {})

    if player.get("main_position"):
        translated = pos_map.get(player["main_position"])
        if translated:
            player["main_position"] = translated

    if player.get("nationality"):
        player["nationality"] = [
            nationality_map.get(n, n) if nationality_map.get(n) else n
            for n in player["nationality"]
        ]

    if not player.get("name_hebrew"):
        translated_name = names_map.get(player["name_english"])
        if translated_name:
            player["name_hebrew"] = translated_name

    return player


def apply_mappings(
    input_path: Path | None = None,
    output_path: Path | None = None,
    mapping_path: Path | None = None,
):
    """Apply Hebrew mappings to player data."""
    resolved_input = input_path or DEFAULT_INPUT
    resolved_output = output_path or DEFAULT_OUTPUT
    resolved_mapping = mapping_path or DEFAULT_MAPPING

    mapping = load_mapping(resolved_mapping)

    count = 0
    with open(resolved_input, "r", encoding="utf-8") as fin, \
         open(resolved_output, "w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            player = json.loads(line)
            player = apply_hebrew(player, mapping)
            fout.write(json.dumps(player, ensure_ascii=False) + "\n")
            count += 1

    logger.info("Applied Hebrew mappings to %d players -> %s", count, resolved_output)


def main():
    """CLI entry point."""
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Apply Hebrew mappings to player data")
    parser.add_argument("--input", type=Path, default=None, dest="input_path")
    parser.add_argument("--output", type=Path, default=None, dest="output_path")
    parser.add_argument("--mapping", type=Path, default=None, dest="mapping_path")
    args = parser.parse_args()

    apply_mappings(
        input_path=args.input_path,
        output_path=args.output_path,
        mapping_path=args.mapping_path,
    )


if __name__ == "__main__":
    main()
