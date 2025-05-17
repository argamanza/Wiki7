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
        with open("output/players.json", encoding="utf-8") as f:
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

        player.update({
            "full_name": full_name.strip() if full_name else None,
            "profile_scraped_from": response.url
        })

        yield player
