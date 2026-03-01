import scrapy


class CoachSpider(scrapy.Spider):
    """Scrape coach/manager history from Transfermarkt trainer page."""

    name = "coach"
    allowed_domains = ["transfermarkt.com"]

    def __init__(self, season="2024", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.base_url = "https://www.transfermarkt.com"
        self.start_urls = [
            f"{self.base_url}/hapoel-beer-sheva/trainer/verein/2976"
        ]

    custom_settings = {
        "HTTPERROR_ALLOWED_CODES": [404],
    }

    def parse(self, response: scrapy.http.Response, **kwargs):
        if response.status == 404:
            self.logger.warning("Coach/trainer page not available for this club (404)")
            return

        rows = response.css("table.items > tbody > tr")
        count = 0

        for row in rows:
            # Skip spacer/header rows
            name_link = row.css("td.hauptlink a")
            if not name_link:
                continue

            name = name_link.css("::text").get("").strip()
            profile_url = name_link.attrib.get("href", "")
            coach_id = profile_url.strip().split("/")[-1] if profile_url else ""

            if not coach_id or not name:
                continue

            # Extract all direct child td cells
            cells = row.xpath("./td")

            # Parse tenure dates (typically in zentriert cells)
            tenure_start = ""
            tenure_end = ""
            zentriert_cells = row.css("td.zentriert::text").getall()
            zentriert_cells = [c.strip() for c in zentriert_cells if c.strip()]
            if len(zentriert_cells) >= 2:
                tenure_start = zentriert_cells[0]
                tenure_end = zentriert_cells[1]
            elif len(zentriert_cells) == 1:
                tenure_start = zentriert_cells[0]

            # Parse numeric stats from zentriert cells with numbers
            # Typical columns: matches, W, D, L, PPM
            rechts_cells = row.css("td.rechts::text").getall()
            rechts_cells = [c.strip() for c in rechts_cells if c.strip()]

            # Try to extract match record from the row
            all_text = row.css("td::text").getall()
            all_text = [t.strip() for t in all_text if t.strip()]

            matches = self._parse_int(rechts_cells, 0)
            wins = self._parse_int(rechts_cells, 1)
            draws = self._parse_int(rechts_cells, 2)
            losses = self._parse_int(rechts_cells, 3)
            ppm = rechts_cells[4].strip() if len(rechts_cells) > 4 else ""

            count += 1
            yield {
                "id": coach_id,
                "name": name,
                "tenure_start": tenure_start,
                "tenure_end": tenure_end,
                "matches": matches,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "ppm": ppm,
            }

        self.logger.info("Scraped %d coaches", count)

    @staticmethod
    def _parse_int(cells, index):
        try:
            raw = cells[index].strip().replace("-", "0").replace(".", "").replace("'", "")
            return int(raw)
        except (IndexError, ValueError):
            return 0
