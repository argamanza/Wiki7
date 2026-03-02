import scrapy


class TransfersSpider(scrapy.Spider):
    """Scrape all incoming/outgoing transfers from the club-level transfers page."""

    name = "transfers"
    allowed_domains = ["transfermarkt.com"]

    def __init__(self, season="2024", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.base_url = "https://www.transfermarkt.com"
        self.start_urls = [
            f"{self.base_url}/hapoel-beer-sheva/alletransfers/verein/2976"
            f"/saison_id/{self.season}"
        ]

    def parse(self, response: scrapy.http.Response, **kwargs):
        count = 0

        # The page has two main sections: Arrivals and Departures
        # Each is in a div.box with a table
        boxes = response.css("div.box")

        for box in boxes:
            header = box.css("div.table-header::text, h2::text").get("").strip().lower()

            if "arrival" in header or "in" in header or "zugang" in header.lower():
                direction = "in"
            elif "departure" in header or "out" in header or "abgang" in header.lower():
                direction = "out"
            else:
                continue

            for row in box.css("table.items > tbody > tr"):
                name_link = row.css("td.hauptlink a")
                if not name_link:
                    continue

                player_name = name_link.css("::text").get("").strip()
                profile_url = name_link.attrib.get("href", "")
                player_id = profile_url.strip().split("/")[-1] if profile_url else ""

                if not player_name:
                    continue

                # Extract transfer details from cells
                cells = row.xpath("./td")
                zentriert = row.css("td.zentriert::text").getall()
                zentriert = [z.strip() for z in zentriert if z.strip()]

                age = zentriert[0] if zentriert else ""
                position = row.css("td:nth-child(2) tr:nth-child(2) td::text").get("").strip()

                # From/To club
                club_links = row.css("td.vereinswappen a, td.no-border-links a")
                from_club = ""
                to_club = ""

                if direction == "in":
                    # For arrivals: the other club is where they came FROM
                    from_club_el = row.css("td.vereinswappen img::attr(title), td.no-border-links a::text")
                    from_club = from_club_el.get("").strip() if from_club_el else ""
                    to_club = "Hapoel Beer Sheva"
                else:
                    # For departures: the other club is where they're GOING
                    to_club_el = row.css("td.vereinswappen img::attr(title), td.no-border-links a::text")
                    to_club = to_club_el.get("").strip() if to_club_el else ""
                    from_club = "Hapoel Beer Sheva"

                # Fee
                fee_cell = row.css("td.rechts a::text, td.rechts::text").getall()
                fee_cell = [f.strip() for f in fee_cell if f.strip()]
                fee = fee_cell[0] if fee_cell else "-"

                is_loan = "loan" in fee.lower()

                count += 1
                yield {
                    "season": self.season,
                    "player_name": player_name,
                    "player_id": player_id,
                    "age": age,
                    "position": position,
                    "from_club": from_club,
                    "to_club": to_club,
                    "fee": fee,
                    "loan": is_loan,
                    "direction": direction,
                }

        self.logger.info("Scraped %d transfers for season %s", count, self.season)
