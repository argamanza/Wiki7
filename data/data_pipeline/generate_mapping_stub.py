import json
import yaml
from pathlib import Path

players_path = Path("output/players.jsonl")
transfers_path = Path("output/transfers.jsonl")
mapping_path = Path("output/mappings.he.yaml")

def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def load_existing_mapping():
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

players = load_jsonl(players_path)
transfers = load_jsonl(transfers_path)
existing = load_existing_mapping()

# Extract unique values
unique_positions = sorted({p["main_position"] for p in players if p.get("main_position")})
unique_clubs = sorted({
    t["from_club"] for t in transfers if t.get("from_club")
}.union({
    t["to_club"] for t in transfers if t.get("to_club")
}))
unique_nationalities = sorted({
    nat for p in players for nat in p.get("nationality", [])
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
    "names": names_map
}

with open(mapping_path, "w", encoding="utf-8") as f:
    yaml.dump(updated, f, allow_unicode=True, sort_keys=False)

print("Updated mapping stub saved to output/mappings.he.yaml")
