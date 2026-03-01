"""Tests for wiki_import module — template rendering and dry-run behavior."""

from pathlib import Path

import pytest

from data_pipeline.normalize_enrich_players import main as normalize_main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def normalized_data(tmp_path):
    """Run normalization on fixtures and return output directory."""
    normalize_main(
        raw_path=str(FIXTURES_DIR / "players_sample.json"),
        out_dir=str(tmp_path),
    )
    return tmp_path


class TestPlayerPageRendering:
    def test_render_player_page(self, normalized_data):
        from wiki_import.import_players import _build_player_page, _load_jsonl

        players = _load_jsonl(normalized_data / "players.jsonl")
        transfers = _load_jsonl(normalized_data / "transfers.jsonl")
        market_values = _load_jsonl(normalized_data / "market_values.jsonl")

        content = _build_player_page(players[0], transfers, market_values)
        assert "Player infobox" in content
        assert "Sagiv Jehezkel" in content
        assert "[[Category:Players]]" in content
        assert "[[Category:Current Squad]]" in content

    def test_render_player_page_with_stats(self, normalized_data):
        from wiki_import.import_players import _build_player_page, _load_jsonl

        players = _load_jsonl(normalized_data / "players.jsonl")
        transfers = _load_jsonl(normalized_data / "transfers.jsonl")
        market_values = _load_jsonl(normalized_data / "market_values.jsonl")
        stats = [
            {"player_id": players[0]["id"], "season": "2024", "appearances": 30,
             "goals": 8, "assists": 5, "yellow_cards": 3, "red_cards": 0, "minutes_played": 2450},
        ]

        content = _build_player_page(players[0], transfers, market_values, stats)
        assert "Season Statistics" in content
        assert "2024" in content
        assert "30" in content  # appearances

    def test_dry_run_import(self, normalized_data):
        from wiki_import.import_players import import_players

        summary = import_players(
            players_path=normalized_data / "players.jsonl",
            transfers_path=normalized_data / "transfers.jsonl",
            market_values_path=normalized_data / "market_values.jsonl",
            dry_run=True,
        )
        assert summary["created"] == 3
        assert summary["failed"] == 0


class TestMatchReportRendering:
    def test_render_match_report(self):
        from wiki_import.import_matches import import_matches

        summary = import_matches(
            matches_path=FIXTURES_DIR / "matches_sample.json",
            dry_run=True,
        )
        assert summary["created"] == 2
        assert summary["failed"] == 0

    def test_match_page_title(self):
        from wiki_import.import_matches import _match_page_title

        match = {
            "date": "2024-08-24",
            "opponent": "Maccabi Tel Aviv",
            "competition": "Israeli Premier League",
        }
        title = _match_page_title(match)
        assert "2024-08-24" in title
        assert "Maccabi Tel Aviv" in title
        assert "Israeli Premier League" in title


class TestCargoTemplates:
    def test_dry_run_cargo_templates(self):
        from wiki_import.import_templates import import_cargo_templates

        summary = import_cargo_templates(dry_run=True)
        assert summary["created"] == 5
        assert summary["failed"] == 0

    def test_cargo_template_content(self):
        from wiki_import.import_templates import _build_cargo_template

        content = _build_cargo_template("players", {"name": "String", "age": "Integer"})
        assert "#cargo_declare" in content
        assert "#cargo_store" in content
        assert "_table=players" in content
        assert "name=String" in content


class TestSquadPage:
    def test_dry_run_squad_page(self, normalized_data):
        from wiki_import.import_templates import import_squad_page

        summary = import_squad_page(
            season="2024",
            players_path=normalized_data / "players.jsonl",
            dry_run=True,
        )
        assert summary["created"] == 1
        assert summary["failed"] == 0


class TestTransferPage:
    def test_dry_run_transfer_page(self, normalized_data):
        from wiki_import.import_templates import import_transfer_page

        summary = import_transfer_page(
            season="2024",
            players_path=normalized_data / "players.jsonl",
            transfers_path=normalized_data / "transfers.jsonl",
            dry_run=True,
        )
        # May be 0 or 1 depending on whether fixture transfers match HBS keywords
        assert summary["failed"] == 0
