"""Tests for data_pipeline.normalize_enrich_players end-to-end."""

import json
import tempfile
from pathlib import Path

import pytest

from data_pipeline.normalize_enrich_players import main, normalize_player, normalize_transfers, normalize_market_values

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestNormalizePlayer:
    def test_normalize_basic_player(self):
        raw = {
            "name_english": "Test Player",
            "profile_url": "https://www.transfermarkt.com/test/profil/spieler/12345",
            "number": "7",
            "season": "2024",
            "loaned": False,
            "facts": {
                "Date of birth/Age": "Jan 1, 1995 (29)",
                "Place of birth": "Tel Aviv, Israel",
                "Citizenship": "Israel",
            },
            "positions": {"main": "Centre-Forward", "others": []},
            "transfers": [],
            "market_value_history": [],
        }
        player = normalize_player(raw)
        assert player.id == "12345"
        assert player.name_english == "Test Player"
        assert player.current_jersey_number == 7
        assert player.current_squad is True

    def test_normalize_loaned_player(self):
        raw = {
            "name_english": "Loaned Player",
            "profile_url": "https://www.transfermarkt.com/test/profil/spieler/99999",
            "number": "-",
            "season": "2024",
            "loaned": True,
            "facts": {},
            "positions": {},
            "transfers": [],
            "market_value_history": [],
        }
        player = normalize_player(raw)
        assert player.current_squad is False
        assert player.current_jersey_number is None

    def test_normalize_hebrew_name(self):
        raw = {
            "name_english": "Sagiv Jehezkel",
            "profile_url": "https://www.transfermarkt.com/test/profil/spieler/503642",
            "number": "10",
            "season": "2024",
            "loaned": False,
            "facts": {
                "Name in home country": "שגיב יחזקאל",
            },
            "positions": {},
            "transfers": [],
            "market_value_history": [],
        }
        player = normalize_player(raw)
        assert player.name_hebrew == "שגיב יחזקאל"


class TestNormalizeTransfers:
    def test_basic_transfer(self):
        raw = {
            "profile_url": "https://www.transfermarkt.com/test/profil/spieler/12345",
            "transfers": [
                {
                    "season": "2022/23",
                    "date": "Aug 1, 2022",
                    "from": "Club A",
                    "to": "Club B",
                    "fee": "€1m",
                }
            ],
        }
        transfers = normalize_transfers(raw)
        assert len(transfers) == 1
        assert transfers[0].player_id == "12345"
        assert transfers[0].loan is False

    def test_loan_detection(self):
        raw = {
            "profile_url": "https://www.transfermarkt.com/test/profil/spieler/12345",
            "transfers": [
                {
                    "season": "2023/24",
                    "date": "Jan 1, 2024",
                    "from": "Club A",
                    "to": "Club B",
                    "fee": "Loan fee: €100k",
                }
            ],
        }
        transfers = normalize_transfers(raw)
        assert transfers[0].loan is True


class TestNormalizeMarketValues:
    def test_basic_market_values(self):
        raw = {
            "profile_url": "https://www.transfermarkt.com/test/profil/spieler/12345",
            "market_value_history": [
                {"date": "Dec 2023", "value": "€2.50m", "team": "Hapoel Beer Sheva"},
            ],
        }
        mvs = normalize_market_values(raw)
        assert len(mvs) == 1
        assert mvs[0].value == "€2.50m"


class TestMainFunction:
    def test_end_to_end_with_fixtures(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            main(
                raw_path=str(FIXTURES_DIR / "players_sample.json"),
                out_dir=tmpdir,
            )
            out = Path(tmpdir)
            assert (out / "players.jsonl").exists()
            assert (out / "transfers.jsonl").exists()
            assert (out / "market_values.jsonl").exists()

            with open(out / "players.jsonl") as f:
                players = [json.loads(line) for line in f if line.strip()]
            assert len(players) == 3
            assert players[0]["name_english"] == "Sagiv Jehezkel"
            assert players[0]["name_hebrew"] == "שגיב יחזקאל"

            with open(out / "transfers.jsonl") as f:
                transfers = [json.loads(line) for line in f if line.strip()]
            assert len(transfers) >= 1

            with open(out / "market_values.jsonl") as f:
                mvs = [json.loads(line) for line in f if line.strip()]
            assert len(mvs) >= 1
