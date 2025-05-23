import scrapy
from urllib.parse import urljoin


class FixturesSpider(scrapy.Spider):
    name = "fixtures"
    allowed_domains = ["transfermarkt.com"]

    def __init__(self, season="2024", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.players_scraped = 0
        self.base_url = "https://www.transfermarkt.com"
        self.start_urls = [
            f"{self.base_url}/hapoel-beer-sheva/spielplandatum/verein/2976/saison_id/{season}"
        ]

    def parse(self, response: scrapy.http.Response, **kwargs):
        current_competition = None

        for row in response.css("div.box div.responsive-table table tbody tr"):
            # Detect competition header
            if row.css("td.extrarow a::text"):
                current_competition = row.css("a::text").get().strip()
                continue

            # Skip rows without match data
            if not row.css("td"):
                continue

            columns = row.css("td")
            if len(columns) < 10:
                continue

            matchday = columns[0].xpath("normalize-space()").get()
            date = columns[1].xpath("normalize-space()").get()
            time = columns[2].xpath("normalize-space()").get()
            venue = columns[3].xpath("normalize-space()").get()
            opponent = columns[6].css("a::text").get()
            system_of_play = columns[7].xpath("normalize-space()").get()
            attendance = columns[8].xpath("normalize-space()").get()

            result_element = columns[9].css("a span::text").getall()
            if len(result_element) == 1:
                result = result_element[0].strip()
            else:
                result = result_element[0].strip() + " (penalties)"

            match_report_relative = columns[9].css("a::attr(href)").get()
            match_report = urljoin(self.base_url, match_report_relative) if match_report_relative else None

            yield {
                "competition": current_competition,
                "matchday": matchday,
                "date": date,
                "time": time,
                "venue": venue,
                "opponent": opponent,
                "system_of_play": system_of_play,
                "attendance": attendance,
                "result": result,
                "match_report_url": match_report,
            }
