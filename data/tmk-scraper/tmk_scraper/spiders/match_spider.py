import scrapy
import json
from scrapy.http import Request

class MatchSpider(scrapy.Spider):
    name = "match"
    allowed_domains = ["transfermarkt.com", "api.scraperapi.com"]

    async def start(self):
        use_scraperapi = self.settings.getbool("USE_SCRAPERAPI", False)
        api_key = self.settings.get("SCRAPERAPI_KEY")

        with open("output/fixtures.json", encoding="utf-8") as f:
            fixtures = json.load(f)

        for match in fixtures:
            target_url = match["match_report_url"]
            if use_scraperapi:
                url = (
                    f"http://api.scraperapi.com/?api_key={api_key}"
                    f"&url={target_url}&country_code=us&render=false"
                )
            else:
                url = target_url

            yield Request(
                url=url,
                callback=self.parse_match_report,
                meta={"match_data": match, "use_scraperapi": use_scraperapi, "api_key": api_key}
            )

    def parse_match_report(self, response):
        match = response.meta["match_data"]

        if response.css(".formation-player-container"):
            lineups = self.extract_from_graphic_field(response)
        else:
            lineups = self.extract_from_simple_table(response)

        yield {
            **match,
            "report_scraped_from": response.url,
            "home_lineup": lineups.get("home"),
            "away_lineup": lineups.get("away")
        }

    def extract_from_simple_table(self, response):
        lineup_boxes = response.css(".aufstellung-box")
        teams_data = {}

        for idx, box in enumerate(lineup_boxes):
            team_name = box.css(".aufstellung-unterueberschrift-mannschaft a::text").get()
            players_by_position = {}
            for row in box.css("table tr"):
                position = row.css("td b::text").get()
                names = row.css("td:nth-child(2) a::text").getall()
                if position:
                    players_by_position[position.strip().lower()] = names
                elif row.css("td:nth-child(1)::text").re(".*manager.*"):
                    players_by_position["manager"] = row.css("td:nth-child(2) a::text").get()

            teams_data["home" if idx == 0 else "away"] = {
                "team": team_name,
                **players_by_position
            }
        return teams_data

    def extract_from_graphic_field(self, response):
        team_players = {"home": [], "away": []}
        lineup_boxes = response.css("div.box > div.large-6.columns")

        for idx, box in enumerate(lineup_boxes):
            team_key = "home" if idx == 0 else "away"
            player_containers = box.css(".formation-player-container")

            for player in player_containers:
                name = player.css(".formation-number-name a::text").get(default="").strip()
                number = player.css(".tm-shirt-number::text").get(default="").strip()
                is_captain = bool(player.css(".kapitaenicon-formation"))

                team_players[team_key].append({
                    "name": name,
                    "number": number,
                    "captain": is_captain
                })

        return team_players
