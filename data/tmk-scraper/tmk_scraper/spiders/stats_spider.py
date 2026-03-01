import scrapy


class StatsSpider(scrapy.Spider):
    """Scrape per-season player statistics from Transfermarkt leistungsdaten page."""

    name = "stats"
    allowed_domains = ["transfermarkt.com"]

    def __init__(self, season="2024", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.season = season
        self.base_url = "https://www.transfermarkt.com"
        # reldata=%26 = all competitions combined
        self.start_urls = [
            f"{self.base_url}/hapoel-beer-sheva/leistungsdaten/verein/2976"
            f"/plus/0?reldata=%26&saison_id={self.season}"
        ]

    def parse(self, response: scrapy.http.Response, **kwargs):
        rows = response.css("table.items > tbody > tr")
        stats_count = 0

        for row in rows:
            # Skip spacer rows (even rows in Transfermarkt tables)
            if not row.css("td.hauptlink"):
                continue

            # Extract player profile URL and ID
            link = row.css("td.hauptlink a::attr(href)").get()
            if not link:
                continue

            player_id = link.strip().split("/")[-1]
            name = row.css("td.hauptlink a::text").get("").strip()

            # Extract all numeric stat cells (td.zentriert)
            stat_cells = row.css("td.zentriert::text").getall()
            stat_cells = [c.strip() for c in stat_cells]

            # The leistungsdaten table typically has these zentriert columns:
            # [age, ..., appearances, goals, assists, yellow, second_yellow, red, minutes]
            # The exact layout may vary; we parse from the right side which is more stable.
            # The last cell before minutes is usually in a td.rechts (right-aligned).

            # Try to get the right-aligned cells (minutes played is often in td.rechts)
            rechts_cells = row.css("td.rechts::text").getall()
            rechts_cells = [c.strip() for c in rechts_cells]

            # Parse stats - use defensive approach
            appearances = self._parse_stat(stat_cells, -5) if len(stat_cells) >= 5 else 0
            goals = self._parse_stat(stat_cells, -4) if len(stat_cells) >= 4 else 0
            assists = self._parse_stat(stat_cells, -3) if len(stat_cells) >= 3 else 0
            yellow_cards = self._parse_stat(stat_cells, -2) if len(stat_cells) >= 2 else 0
            red_cards = self._parse_stat(stat_cells, -1) if len(stat_cells) >= 1 else 0
            minutes_played = self._parse_minutes(rechts_cells[-1]) if rechts_cells else 0

            self.logger.debug(
                "Player %s (%s): apps=%d, goals=%d, assists=%d, yellow=%d, red=%d, min=%d | "
                "raw_zentriert=%s, raw_rechts=%s",
                name, player_id, appearances, goals, assists, yellow_cards, red_cards,
                minutes_played, stat_cells, rechts_cells,
            )

            stats_count += 1
            yield {
                "player_id": player_id,
                "season": self.season,
                "appearances": appearances,
                "goals": goals,
                "assists": assists,
                "yellow_cards": yellow_cards,
                "red_cards": red_cards,
                "minutes_played": minutes_played,
            }

        self.logger.info("Scraped stats for %d players in season %s", stats_count, self.season)

    @staticmethod
    def _parse_stat(cells, index):
        """Parse a numeric stat from a cell list by index. Returns 0 for missing/invalid."""
        try:
            raw = cells[index].strip().replace("-", "0")
            return int(raw)
        except (IndexError, ValueError):
            return 0

    @staticmethod
    def _parse_minutes(raw):
        """Parse minutes played, handling formats like '2.450' or \"2'450\" or '2450'."""
        try:
            cleaned = raw.strip().replace(".", "").replace("'", "").replace("-", "0")
            return int(cleaned)
        except (ValueError, AttributeError):
            return 0
