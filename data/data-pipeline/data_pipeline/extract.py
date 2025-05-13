def process_players(players):
    seen = {}
    for player in players:
        pid = player.get("id")
        if pid and pid not in seen:
            seen[pid] = player
    return list(seen.values())