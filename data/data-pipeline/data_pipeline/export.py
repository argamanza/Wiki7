import json
import os

def to_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)  # ensure directory exists
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
