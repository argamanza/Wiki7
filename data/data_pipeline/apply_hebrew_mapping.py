import json
import yaml
from pathlib import Path

INPUT = Path("output/players.jsonl")
OUTPUT = Path("output/players.he.jsonl")
MAPPING = Path("output/mappings.he.yaml")

def load_mapping():
    with open(MAPPING, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def apply_hebrew(player: dict, mapping: dict) -> dict:
    pos_map = mapping.get("positions", {})
    club_map = mapping.get("clubs", {})
    nationality_map = mapping.get("nationalities", {})
    names_map = mapping.get("names", {})

    if player.get("main_position"):
        player["main_position"] = pos_map.get(player["main_position"], player["main_position"])

    if player.get("nationality"):
        player["nationality"] = [nationality_map.get(n, n) for n in player["nationality"]]

    if not player.get("name_hebrew"):
        player["name_hebrew"] = names_map.get(player["name_english"])

    return player

def main():
    mapping = load_mapping()
    with open(INPUT, "r", encoding="utf-8") as fin, open(OUTPUT, "w", encoding="utf-8") as fout:
        for line in fin:
            player = json.loads(line)
            player = apply_hebrew(player, mapping)
            fout.write(json.dumps(player, ensure_ascii=False) + "\n")

if __name__ == "__main__":
    main()
