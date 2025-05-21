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

        # Extract both formats
        graphic_lineups = self.extract_from_graphic_field(response)
        table_lineups = self.extract_from_simple_table(response)

        # Prefer graphic if it exists; else fallback to table
        home_lineup = graphic_lineups.get("home") or table_lineups.get("home")
        away_lineup = graphic_lineups.get("away") or table_lineups.get("away")

        yield {
            **match,
            "report_scraped_from": response.url,
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
        }

    def extract_from_simple_table(self, response):
        teams_data = {}

        for box in response.css("div.aufstellung-box, div.large-6.columns"):
            team_name = box.css(".aufstellung-unterueberschrift-mannschaft a::text").get()
            if not team_name:
                continue

            team_key = self.resolve_team_key(team_name, response)
            players_by_position = {}

            for row in box.css("table tr"):
                position = row.css("td b::text").get()
                names = row.css("td:nth-child(2) a::text").getall()
                if position:
                    players_by_position[position.strip().lower()] = names
                elif row.css("td:nth-child(1)::text").re(".*manager.*"):
                    players_by_position["manager"] = row.css("td:nth-child(2) a::text").get()

            teams_data[team_key] = {
                **players_by_position
            }

        return {
            key: val for key, val in teams_data.items() if val
        }

    def extract_from_graphic_field(self, response):
        team_players = {}

        for box in response.css("div.box > div.large-6.columns"):
            team_name = box.css(".aufstellung-unterueberschrift-mannschaft a::text").get()
            if not team_name:
                continue

            team_key = self.resolve_team_key(team_name, response)

            players = []
            for player in box.css(".formation-player-container"):
                name = player.css(".formation-number-name a::text").get()
                if not name:
                    continue
                number = player.css(".tm-shirt-number::text").get(default="").strip()
                is_captain = bool(player.css(".kapitaenicon-formation"))
                players.append({
                    "name": name.strip(),
                    "number": number,
                    "captain": is_captain
                })

            team_players[team_key] = {
                "team": team_name,
                **({"players": players} if players else {})
            }

        return {
            key: val.get("players") for key, val in team_players.items()
        }

    def resolve_team_key(self, team_name, response):
        match = response.meta["match_data"]
        home = match.get("home_team", "").lower()
        away = match.get("away_team", "").lower()

        if team_name.lower() in home:
            return "home"
        elif team_name.lower() in away:
            return "away"
        else:
            # fallback: assign by appearance order
            if "home" not in response.meta:
                response.meta["home"] = team_name
                return "home"
            else:
                return "away"
