import scrapy


class SquadSpider(scrapy.Spider):
    name = "squad"
    allowed_domains = ["transfermarkt.com"]

    def __init__(self, season="2024", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.start_urls = [
            f"https://www.transfermarkt.com/hapoel-beer-sheva/kader/verein/2976/saison_id/{self.season}"
        ]
        self.players_scraped = 0

    def parse(self, response: scrapy.http.Response, **kwargs):
        rows = response.css("table.items > tbody > tr")

        for row in rows:
            link = row.css("td.hauptlink a::attr(href)").get()
            name = row.css("td.hauptlink a::text").get()

            if link and name:
                self.players_scraped += 1
                yield {
                    "name": name.strip(),
                    "profile_url": response.urljoin(link.strip()),
                    "season": self.season
                }

        self.logger.info(f"Scraped {self.players_scraped} players for season {self.season}")