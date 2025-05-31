import json
import yaml
from pathlib import Path

# Load data
players_path = Path("output/players.jsonl")
transfers_path = Path("output/transfers.jsonl")

def load_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

players = load_jsonl(players_path)
transfers = load_jsonl(transfers_path)

# Extract unique values
unique_positions = sorted({p["main_position"] for p in players if p.get("main_position")})
unique_clubs = sorted({
    t["from_club"] for t in transfers if t.get("from_club")
}.union({
    t["to_club"] for t in transfers if t.get("to_club")
}))

# Generate mapping dicts
position_map = {pos: "" for pos in unique_positions}
club_map = {club: "" for club in unique_clubs}

# Combine
mapping = {
    "positions": position_map,
    "clubs": club_map
}

# Save as YAML
with open("output/mapping_stub.yaml", "w", encoding="utf-8") as f:
    yaml.dump(mapping, f, allow_unicode=True, sort_keys=False)

print("Mapping stub saved to output/mapping_stub.yaml")
