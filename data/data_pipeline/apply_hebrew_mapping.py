import json
import logging
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_INPUT = Path(__file__).resolve().parent / "output" / "players.jsonl"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "output" / "players.he.jsonl"
DEFAULT_MAPPING = Path(__file__).resolve().parent / "output" / "mappings.he.yaml"


def load_mapping(mapping_path: Path | None = None) -> dict:
    """Load Hebrew translation mapping from a YAML file.

    Raises FileNotFoundError if the mapping file does not exist.
    """
    path = mapping_path or DEFAULT_MAPPING
    if not path.exists():
        raise FileNotFoundError(
            f"Hebrew mapping file not found: {path}. "
            "Run generate_mapping_stub first and fill in translations."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping in {path}, got {type(data).__name__}")
    return data


def apply_hebrew(player: dict, mapping: dict) -> dict:
    """Apply Hebrew translations to a player dict using the mapping."""
    pos_map = mapping.get("positions", {}) or {}
    club_map = mapping.get("clubs", {}) or {}
    nationality_map = mapping.get("nationalities", {}) or {}
    names_map = mapping.get("names", {}) or {}

    if player.get("main_position"):
        player["main_position"] = pos_map.get(player["main_position"], player["main_position"])

    if player.get("nationality"):
        player["nationality"] = [nationality_map.get(n, n) for n in player["nationality"]]

    if not player.get("name_hebrew"):
        player["name_hebrew"] = names_map.get(player["name_english"])

    return player


def main(
    input_path: Path | None = None,
    output_path: Path | None = None,
    mapping_path: Path | None = None,
) -> None:
    """Apply Hebrew mappings to normalized player data."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    resolved_input = input_path or DEFAULT_INPUT
    resolved_output = output_path or DEFAULT_OUTPUT

    if not resolved_input.exists():
        raise FileNotFoundError(
            f"Input file not found: {resolved_input}. "
            "Run normalize_enrich_players first."
        )

    mapping = load_mapping(mapping_path)
    count = 0

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    with open(resolved_input, "r", encoding="utf-8") as fin, \
         open(resolved_output, "w", encoding="utf-8") as fout:
        for line in fin:
            try:
                player = json.loads(line)
                player = apply_hebrew(player, mapping)
                fout.write(json.dumps(player, ensure_ascii=False) + "\n")
                count += 1
            except json.JSONDecodeError as exc:
                logger.warning("Skipping malformed JSON line: %s", exc)

    logger.info("Applied Hebrew mapping to %d players -> %s", count, resolved_output)


if __name__ == "__main__":
    main()
