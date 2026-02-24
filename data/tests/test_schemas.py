"""Tests for data_pipeline.schemas module (Pydantic models)."""

import pytest
from datetime import date

from pydantic import ValidationError

from data_pipeline.schemas import Player, Transfer, MarketValue


# ---------------------------------------------------------------------------
# Transfer model
# ---------------------------------------------------------------------------

class TestTransferSchema:
    """Tests for the Transfer Pydantic model."""

    def test_valid_transfer(self):
        t = Transfer(
            player_id="12345",
            season="2023/24",
            transfer_date="Jul 1, 2023",
            from_club="Maccabi Tel Aviv",
            to_club="Hapoel Beer Sheva",
            fee="€500K",
            loan=False,
        )
        assert t.player_id == "12345"
        assert t.season == "2023/24"
        assert t.transfer_date == "Jul 1, 2023"
        assert t.from_club == "Maccabi Tel Aviv"
        assert t.to_club == "Hapoel Beer Sheva"
        assert t.fee == "€500K"
        assert t.loan is False

    def test_loan_transfer(self):
        t = Transfer(
            player_id="67890",
            season="2024/25",
            transfer_date="Aug 15, 2024",
            from_club="Club A",
            to_club="Club B",
            fee="Loan fee: €100K",
            loan=True,
        )
        assert t.loan is True

    def test_missing_required_field_player_id(self):
        with pytest.raises(ValidationError) as exc_info:
            Transfer(
                season="2023/24",
                transfer_date="Jul 1, 2023",
                from_club="Club A",
                to_club="Club B",
                fee="Free",
                loan=False,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("player_id",) for e in errors)

    def test_missing_required_field_season(self):
        with pytest.raises(ValidationError) as exc_info:
            Transfer(
                player_id="123",
                transfer_date="Jul 1, 2023",
                from_club="Club A",
                to_club="Club B",
                fee="Free",
                loan=False,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("season",) for e in errors)

    def test_missing_required_field_loan(self):
        with pytest.raises(ValidationError) as exc_info:
            Transfer(
                player_id="123",
                season="2023/24",
                transfer_date="Jul 1, 2023",
                from_club="Club A",
                to_club="Club B",
                fee="Free",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("loan",) for e in errors)

    def test_empty_strings_accepted(self):
        """Pydantic str fields accept empty strings by default."""
        t = Transfer(
            player_id="",
            season="",
            transfer_date="",
            from_club="",
            to_club="",
            fee="",
            loan=False,
        )
        assert t.player_id == ""
        assert t.fee == ""

    def test_loan_field_must_be_bool(self):
        """Non-bool-coercible value for loan should raise a ValidationError."""
        with pytest.raises(ValidationError):
            Transfer(
                player_id="123",
                season="2023/24",
                transfer_date="Jul 1, 2023",
                from_club="Club A",
                to_club="Club B",
                fee="Free",
                loan="not a bool",
            )

    def test_serialization_round_trip(self):
        t = Transfer(
            player_id="999",
            season="2024/25",
            transfer_date="Jan 10, 2025",
            from_club="X",
            to_club="Y",
            fee="€1M",
            loan=True,
        )
        data = t.model_dump()
        t2 = Transfer(**data)
        assert t == t2


# ---------------------------------------------------------------------------
# MarketValue model
# ---------------------------------------------------------------------------

class TestMarketValueSchema:
    """Tests for the MarketValue Pydantic model."""

    def test_valid_market_value(self):
        mv = MarketValue(
            player_id="12345",
            value_date="Dec 15, 2024",
            value="€2.50m",
            team="Hapoel Beer Sheva",
        )
        assert mv.player_id == "12345"
        assert mv.value_date == "Dec 15, 2024"
        assert mv.value == "€2.50m"
        assert mv.team == "Hapoel Beer Sheva"

    def test_missing_required_field_player_id(self):
        with pytest.raises(ValidationError) as exc_info:
            MarketValue(
                value_date="Dec 15, 2024",
                value="€2.50m",
                team="Some Team",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("player_id",) for e in errors)

    def test_missing_required_field_value(self):
        with pytest.raises(ValidationError) as exc_info:
            MarketValue(
                player_id="123",
                value_date="Dec 15, 2024",
                team="Some Team",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("value",) for e in errors)

    def test_missing_required_field_team(self):
        with pytest.raises(ValidationError) as exc_info:
            MarketValue(
                player_id="123",
                value_date="Dec 15, 2024",
                value="€1m",
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("team",) for e in errors)

    def test_empty_strings_accepted(self):
        mv = MarketValue(
            player_id="",
            value_date="",
            value="",
            team="",
        )
        assert mv.value == ""

    def test_serialization_round_trip(self):
        mv = MarketValue(
            player_id="555",
            value_date="Jun 1, 2024",
            value="€500K",
            team="Team Z",
        )
        data = mv.model_dump()
        mv2 = MarketValue(**data)
        assert mv == mv2


# ---------------------------------------------------------------------------
# Player model
# ---------------------------------------------------------------------------

class TestPlayerSchema:
    """Tests for the Player Pydantic model."""

    @pytest.fixture
    def valid_player_data(self):
        """Return a dictionary with all fields set to valid values."""
        return {
            "id": "12345",
            "name_english": "John Doe",
            "name_hebrew": "ג'ון דו",
            "nationality": ["Israel", "Germany"],
            "birth_date": date(1995, 3, 15),
            "birth_place": "Tel Aviv",
            "main_position": "Centre-Forward",
            "current_squad": True,
            "current_jersey_number": 9,
            "homegrown": False,
            "retired": False,
        }

    def test_valid_player(self, valid_player_data):
        p = Player(**valid_player_data)
        assert p.id == "12345"
        assert p.name_english == "John Doe"
        assert p.name_hebrew == "ג'ון דו"
        assert p.nationality == ["Israel", "Germany"]
        assert p.birth_date == date(1995, 3, 15)
        assert p.birth_place == "Tel Aviv"
        assert p.main_position == "Centre-Forward"
        assert p.current_squad is True
        assert p.current_jersey_number == 9
        assert p.homegrown is False
        assert p.retired is False

    def test_minimal_player_with_optional_none(self):
        """All Optional fields set to None should still be valid."""
        p = Player(
            id="99999",
            name_english="Jane Smith",
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
        assert p.id == "99999"
        assert p.name_hebrew is None
        assert p.nationality is None
        assert p.birth_date is None
        assert p.birth_place is None
        assert p.main_position is None
        assert p.current_jersey_number is None

    def test_missing_required_field_id(self):
        with pytest.raises(ValidationError) as exc_info:
            Player(
                name_english="Test",
                current_squad=True,
                homegrown=False,
                retired=False,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("id",) for e in errors)

    def test_missing_required_field_name_english(self):
        with pytest.raises(ValidationError) as exc_info:
            Player(
                id="123",
                current_squad=True,
                homegrown=False,
                retired=False,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("name_english",) for e in errors)

    def test_missing_required_field_current_squad(self):
        with pytest.raises(ValidationError) as exc_info:
            Player(
                id="123",
                name_english="Test",
                homegrown=False,
                retired=False,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("current_squad",) for e in errors)

    def test_missing_required_field_homegrown(self):
        with pytest.raises(ValidationError) as exc_info:
            Player(
                id="123",
                name_english="Test",
                current_squad=True,
                retired=False,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("homegrown",) for e in errors)

    def test_missing_required_field_retired(self):
        with pytest.raises(ValidationError) as exc_info:
            Player(
                id="123",
                name_english="Test",
                current_squad=True,
                homegrown=False,
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("retired",) for e in errors)

    def test_invalid_birth_date_type(self):
        """Passing a non-date, non-parseable value for birth_date should fail."""
        with pytest.raises(ValidationError):
            Player(
                id="123",
                name_english="Test",
                birth_date="not-a-date",
                current_squad=True,
                homegrown=False,
                retired=False,
            )

    def test_jersey_number_as_int(self, valid_player_data):
        valid_player_data["current_jersey_number"] = 99
        p = Player(**valid_player_data)
        assert p.current_jersey_number == 99

    def test_jersey_number_none(self, valid_player_data):
        valid_player_data["current_jersey_number"] = None
        p = Player(**valid_player_data)
        assert p.current_jersey_number is None

    def test_nationality_as_empty_list(self, valid_player_data):
        valid_player_data["nationality"] = []
        p = Player(**valid_player_data)
        assert p.nationality == []

    def test_nationality_single_item(self, valid_player_data):
        valid_player_data["nationality"] = ["Brazil"]
        p = Player(**valid_player_data)
        assert p.nationality == ["Brazil"]

    def test_birth_date_as_date_object(self, valid_player_data):
        valid_player_data["birth_date"] = date(2000, 1, 1)
        p = Player(**valid_player_data)
        assert p.birth_date == date(2000, 1, 1)

    def test_birth_date_as_iso_string(self, valid_player_data):
        """Pydantic v2 can parse ISO date strings for date fields."""
        valid_player_data["birth_date"] = "2000-06-15"
        p = Player(**valid_player_data)
        assert p.birth_date == date(2000, 6, 15)

    def test_serialization_round_trip(self, valid_player_data):
        p = Player(**valid_player_data)
        data = p.model_dump()
        p2 = Player(**data)
        assert p == p2

    def test_json_serialization(self, valid_player_data):
        p = Player(**valid_player_data)
        json_str = p.model_dump_json()
        assert '"id":"12345"' in json_str or '"id": "12345"' in json_str

    def test_empty_name_english_accepted(self):
        """Empty string for name_english is accepted (no min-length constraint)."""
        p = Player(
            id="123",
            name_english="",
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
        assert p.name_english == ""

    def test_multiple_missing_required_fields(self):
        """When multiple required fields are missing, all should be reported."""
        with pytest.raises(ValidationError) as exc_info:
            Player()
        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors if e["type"] == "missing"}
        assert "id" in missing_fields
        assert "name_english" in missing_fields
        assert "current_squad" in missing_fields
        assert "homegrown" in missing_fields
        assert "retired" in missing_fields
