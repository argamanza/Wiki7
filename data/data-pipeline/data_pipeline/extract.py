def process_players(players):
    seen = {}
    for player in players:
        print(f"Processing player: {player.get('name')}")
        pid = player.get("id")
        if pid and pid not in seen:
            seen[pid] = player
    return list(seen.values())