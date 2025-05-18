import scrapy
import json
from scrapy.http import Request


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
                meta={"player_data": player}
            )

    def parse_profile(self, response):
        player = response.meta["player_data"]

        full_name = response.css("h1.spielerdaten-header__headline::text").get()

        # Extract facts table
        keys = response.css("div.spielerdatenundfakten span.info-table__content--regular::text").getall()
        values = response.css("div.spielerdatenundfakten span.info-table__content--bold").xpath("string()").getall()

        facts = {}
        for k, v in zip(keys, values):
            key = k.strip().rstrip(":")
            val = v.strip().replace("\xa0", " ") if v else None
            facts[key] = val

        # Extract positions
        main_position = response.css("div.detail-position__box dd.detail-position__position::text").get()
        position_divs = response.css("div.detail-position__box div.detail-position__position")
        other_positions = position_divs.css("dd.detail-position__position::text").getall() if len(
            position_divs) > 0 else []

        # Update player with structured data
        player.update({
            "full_name": full_name.strip() if full_name else None,
            "profile_scraped_from": response.url,
            "facts": facts,
            "positions": {
                "main": main_position.strip() if main_position else None,
                "other": [pos.strip() for pos in other_positions if pos.strip()]
            }
        })

        yield player

