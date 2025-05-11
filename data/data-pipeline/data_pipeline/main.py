import fetch, extract, export

def run():
    print("Starting data pipeline...")
    raw_data = fetch.fetch_all_season_players()
    print(f"Fetched {len(raw_data)} players from the API.")
    players = extract.process_players(raw_data)
    export.to_json(players, "data/players.json")

if __name__ == "__main__":
    run()
