"""Tests for data_pipeline.schemas Pydantic models."""

import pytest
from datetime import date
from data_pipeline.schemas import Player, Transfer, MarketValue


class TestPlayerSchema:
    def test_valid_player(self):
        player = Player(
            id="503642",
            name_english="Sagiv Jehezkel",
            name_hebrew="שגיב יחזקאל",
            nationality=["Israel"],
            birth_date=date(2000, 1, 14),
            birth_place="Be'er Sheva, Israel",
            main_position="Attacking Midfield",
            current_squad=True,
            current_jersey_number=10,
            homegrown=True,
            retired=False,
        )
        assert player.id == "503642"
        assert player.name_english == "Sagiv Jehezkel"
        assert player.name_hebrew == "שגיב יחזקאל"

    def test_minimal_player(self):
        player = Player(
            id="123",
            name_english="Test Player",
            name_hebrew=None,
            nationality=None,
            birth_date=None,
            birth_place=None,
            main_position=None,
            current_squad=False,
            current_jersey_number=None,
            homegrown=False,
            retired=False,
        )
        assert player.id == "123"
        assert player.name_hebrew is None

    def test_serialization(self):
        player = Player(
            id="503642",
            name_english="Sagiv Jehezkel",
            name_hebrew=None,
            nationality=["Israel"],
            birth_date=date(2000, 1, 14),
            birth_place=None,
            main_position="Attacking Midfield",
            current_squad=True,
            current_jersey_number=10,
            homegrown=True,
            retired=False,
        )
        data = player.model_dump()
        assert data["id"] == "503642"
        assert data["birth_date"] == date(2000, 1, 14)

    def test_json_serialization(self):
        player = Player(
            id="1",
            name_english="Test",
            name_hebrew=None,
            nationality=None,
            birth_date=None,
            birth_place=None,
            main_position=None,
            current_squad=True,
            current_jersey_number=None,
            homegrown=False,
            retired=False,
        )
        json_str = player.model_dump_json()
        assert '"id":"1"' in json_str


class TestTransferSchema:
    def test_valid_transfer(self):
        transfer = Transfer(
            player_id="503642",
            season="2022/23",
            transfer_date="Aug 1, 2022",
            from_club="Hapoel Beer Sheva U19",
            to_club="Hapoel Beer Sheva",
            fee="-",
            loan=False,
        )
        assert transfer.player_id == "503642"
        assert transfer.loan is False

    def test_loan_transfer(self):
        transfer = Transfer(
            player_id="101577",
            season="2020/21",
            transfer_date="Aug 10, 2020",
            from_club="Charlton Athletic",
            to_club="Bnei Sakhnin",
            fee="Loan",
            loan=True,
        )
        assert transfer.loan is True
        assert transfer.fee == "Loan"


class TestMarketValueSchema:
    def test_valid_market_value(self):
        mv = MarketValue(
            player_id="503642",
            value_date="Dec 2023",
            value="€2.50m",
            team="Hapoel Beer Sheva",
        )
        assert mv.player_id == "503642"
        assert mv.value == "€2.50m"
