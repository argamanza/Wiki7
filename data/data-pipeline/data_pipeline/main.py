import fetch, extract, export

def run():
    print("Starting data pipeline...")

    # Fetch data from the API
    raw_data = fetch.fetch_all_season_players()
    print(f"Fetched {len(raw_data)} players from the API.")

    # Process the players (remove duplicates)
    print("Removing duplicates...")
    players = extract.process_players(raw_data)

    # Convert to dictionary for easy access
    players_by_id = {player["id"]: player for player in players}

    # Fetch additional data for each player
    print("Enriching player data...")
    fetch.enrich_players(players_by_id)

    export.to_json(players_by_id, "data/players.json")

if __name__ == "__main__":
    run()
