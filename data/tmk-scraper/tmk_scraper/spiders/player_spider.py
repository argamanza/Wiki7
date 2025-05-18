import scrapy
import json
from scrapy.http import Request
from datetime import datetime


class PlayerSpider(scrapy.Spider):
    name = "player"
    allowed_domains = ["transfermarkt.com", "api.scraperapi.com"]

    async def start(self):
        use_scraperapi = self.settings.getbool("USE_SCRAPERAPI", False)
        api_key = self.settings.get("SCRAPERAPI_KEY")

        # Load player URLs from output of squad spider
        with open("output/squad.json", encoding="utf-8") as f:
            players = json.load(f)

        for player in players:
            target_url = player["profile_url"]
            if use_scraperapi:
                url = (
                    f"http://api.scraperapi.com/?api_key={api_key}"
                    f"&url={target_url}&country_code=us&render=false"
                )
            else:
                url = target_url

            yield Request(
                url=url,
                callback=self.parse_profile,
                meta={"player_data": player, "use_scraperapi": use_scraperapi, "api_key": api_key}
            )

    def parse_profile(self, response):
        player = response.meta["player_data"]
        use_scraperapi = response.meta["use_scraperapi"]
        api_key = response.meta["api_key"]

        # Facts
        keys = response.css("div.spielerdatenundfakten span.info-table__content--regular::text").getall()
        values = response.css("div.spielerdatenundfakten span.info-table__content--bold").xpath("string()").getall()
        facts = {
            k.strip().rstrip(":"): v.strip().replace("\xa0", " ") for k, v in zip(keys, values) if v
        }

        # Positionד
        main_position = response.css("div.detail-position__box dd.detail-position__position::text").get()
        position_divs = response.css("div.detail-position__box div.detail-position__position")
        other_positions = position_divs.css("dd.detail-position__position::text").getall() if len(position_divs) > 0 else []

        # Extract player ID from profile URL (last numeric segment)
        player_id = player["profile_url"].split("/")[-1]

        # Construct AJAX request for market value history
        mv_url = f"https://www.transfermarkt.com/ceapi/marketValueDevelopment/graph/{player_id}"
        if use_scraperapi:
            mv_url = (
                f"http://api.scraperapi.com/?api_key={api_key}"
                f"&url={mv_url}&country_code=us&render=false"
            )

        # Store interim player object in meta and call market value endpoint
        meta = {
            "player_data": {
                **player,
                "profile_scraped_from": response.url,
                "facts": facts,
                "positions": {
                    "main": main_position.strip() if main_position else None,
                    "other": [pos.strip() for pos in other_positions if pos.strip()]
                }
            },
            "player_id": player_id,
            "use_scraperapi": use_scraperapi,
            "api_key": api_key
        }

        yield Request(url=mv_url, callback=self.parse_market_value, meta=meta)

    def parse_market_value(self, response):
        player = response.meta["player_data"]
        player_id = response.meta["player_id"]
        use_scraperapi = response.meta["use_scraperapi"]
        api_key = response.meta["api_key"]

        try:
            data = json.loads(response.text)
            history = [
                {
                    "date": datetime.strptime(p["datum_mw"], "%b %d, %Y").strftime("%Y-%m-%d"),
                    "value": p["mw"],
                    "team": p["verein"]
                }
                for p in data.get("list", [])
            ]
            player["market_value_history"] = sorted(history, key=lambda x: x["date"])
        except Exception as e:
            self.logger.warning(f"Failed to parse market value history: {e}")
            player["market_value_history"] = []

        # Proceed to transfer history
        transfer_url = f"https://www.transfermarkt.com/ceapi/transferHistory/list/{player_id}"
        if use_scraperapi:
            transfer_url = (
                f"http://api.scraperapi.com/?api_key={api_key}"
                f"&url={transfer_url}&country_code=us&render=false"
            )

        yield Request(url=transfer_url, callback=self.parse_transfer_history, meta={"player_data": player})

    def parse_transfer_history(self, response):
        player = response.meta["player_data"]

        try:
            data = json.loads(response.text)
            history = [
                {
                    "season": t.get("season"),
                    "date": t.get("dateUnformatted"),
                    "from": t.get("from", {}).get("clubName"),
                    "to": t.get("to", {}).get("clubName"),
                    "fee": t.get("fee")
                }
                for t in data.get("transfers", [])
            ]
            player["transfers"] = sorted(history, key=lambda x: x["date"])
        except Exception as e:
            self.logger.warning(f"Failed to parse transfer history: {e}")
            player["transfers"] = []

        yield player
