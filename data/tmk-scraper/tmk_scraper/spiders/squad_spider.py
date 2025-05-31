import scrapy


class SquadSpider(scrapy.Spider):
    name = "squad"
    allowed_domains = ["transfermarkt.com"]

    def __init__(self, season="2024", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.players_scraped = 0
        self.base_url = "https://www.transfermarkt.com"
        self.start_urls = [
            f"{self.base_url}/hapoel-beer-sheva/kader/verein/2976/saison_id/{self.season}"
        ]
        self.loan_url = f"{self.base_url}/hapoel-beer-sheva/leihspieler/verein/2976"

    def parse(self, response: scrapy.http.Response, **kwargs):
        rows = response.css("table.items > tbody > tr")

        for row in rows:
            number = row.css("div.rn_nummer::text").get()
            name = row.css("td.hauptlink a::text").get()
            link = row.css("td.hauptlink a::attr(href)").get()

            if name and link:
                self.players_scraped += 1
                yield {
                    "name_english": name.strip(),
                    "profile_url": response.urljoin(link.strip()),
                    "number": number.strip() if number else "-",
                    "season": self.season,
                    "loaned": False
                }

        # Now follow to the loaned players page
        yield scrapy.Request(
            url=self.loan_url,
            callback=self.parse_loans
        )

    def parse_loans(self, response: scrapy.http.Response):
        rows = response.css("table.items > tbody > tr")

        for row in rows:
            name = row.css("td > table.inline-table td.hauptlink a::text").get()
            link = row.css("td > table.inline-table td.hauptlink a::attr(href)").get()

            if name and link:
                self.players_scraped += 1
                yield {
                    "name_english": name.strip(),
                    "profile_url": response.urljoin(link.strip()),
                    "number": "-",  # loan page doesn't include jersey number
                    "season": self.season,
                    "loaned": True
                }

        self.logger.info(f"Scraped total {self.players_scraped} players for season {self.season}")
