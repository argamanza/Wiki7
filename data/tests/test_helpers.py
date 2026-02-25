"""Tests for data_pipeline.helpers module."""

import pytest
from datetime import date

from data_pipeline.helpers import (
    is_all_hebrew,
    parse_birth_date,
    parse_countries,
    is_homegrown,
    is_retired,
    _get_country_variants,
    _greedy_country_match,
    _is_valid_word_boundary,
    _standardize_country_name,
)


# ---------------------------------------------------------------------------
# is_all_hebrew
# ---------------------------------------------------------------------------

class TestIsAllHebrew:
    """Tests for the is_all_hebrew() function."""

    def test_pure_hebrew(self):
        assert is_all_hebrew("שלום") is True

    def test_hebrew_with_spaces(self):
        assert is_all_hebrew("שלום עולם") is True

    def test_pure_english(self):
        assert is_all_hebrew("Hello") is False

    def test_mixed_hebrew_and_english(self):
        assert is_all_hebrew("שלום Hello") is False

    def test_hebrew_with_numbers(self):
        assert is_all_hebrew("שלום123") is False

    def test_hebrew_with_punctuation(self):
        assert is_all_hebrew("שלום!") is False

    def test_empty_string(self):
        assert is_all_hebrew("") is False

    def test_only_spaces(self):
        """Spaces-only should return False because the regex requires at least
        one character from the Hebrew block + spaces set, but fullmatch with
        '+' requires at least one match which spaces satisfy — however, the
        intent is unclear, so we just document the actual behaviour."""
        # The regex [\u0590-\u05FF\s]+ will match spaces-only
        assert is_all_hebrew("   ") is True

    def test_single_hebrew_char(self):
        assert is_all_hebrew("א") is True

    def test_hebrew_with_niqqud(self):
        # Niqqud (vowel diacritics) are in the \u0590-\u05FF range
        assert is_all_hebrew("שָׁלוֹם") is True


# ---------------------------------------------------------------------------
# parse_birth_date
# ---------------------------------------------------------------------------

class TestParseBirthDate:
    """Tests for the parse_birth_date() function."""

    def test_standard_date(self):
        result = parse_birth_date("Jan 15, 1990")
        assert result == date(1990, 1, 15)

    def test_date_with_age_suffix(self):
        """Transfermarkt dates often include ' (32)' age suffix."""
        result = parse_birth_date("Mar 10, 1992 (32)")
        assert result == date(1992, 3, 10)

    def test_iso_format(self):
        result = parse_birth_date("1995-07-20")
        assert result == date(1995, 7, 20)

    def test_european_format(self):
        result = parse_birth_date("20.07.1995")
        assert result == date(1995, 7, 20)

    def test_empty_string(self):
        assert parse_birth_date("") is None

    def test_none_input(self):
        assert parse_birth_date(None) is None

    def test_garbage_string(self):
        assert parse_birth_date("not a date at all") is None

    def test_only_year(self):
        result = parse_birth_date("1990")
        # dateutil.parser.parse("1990") treats it as a datetime; just ensure
        # it returns a date object (implementation-dependent)
        assert result is not None
        assert isinstance(result, date)

    def test_date_with_parentheses_in_middle(self):
        """The split(' (') logic should only strip the first '(' part."""
        result = parse_birth_date("Feb 28, 1988 (36)")
        assert result == date(1988, 2, 28)


# ---------------------------------------------------------------------------
# parse_countries
# ---------------------------------------------------------------------------

class TestParseCountries:
    """Tests for the parse_countries() function."""

    def test_single_country(self):
        result = parse_countries("Germany")
        assert result == ["Germany"]

    def test_multiple_countries_space_separated(self):
        result = parse_countries("Israel Germany")
        assert "Israel" in result
        assert "Germany" in result
        assert len(result) == 2

    def test_multiple_countries_comma_separated(self):
        result = parse_countries("Israel, Germany")
        assert "Israel" in result
        assert "Germany" in result
        assert len(result) == 2

    def test_multiple_countries_slash_separated(self):
        result = parse_countries("Israel/Germany")
        assert "Israel" in result
        assert "Germany" in result
        assert len(result) == 2

    def test_empty_string(self):
        assert parse_countries("") == []

    def test_none_input(self):
        assert parse_countries(None) == []

    def test_whitespace_only(self):
        assert parse_countries("   ") == []

    def test_preserves_order(self):
        """Countries should appear in the order they were found in the text."""
        result = parse_countries("France Spain")
        assert result.index("France") < result.index("Spain")

    def test_special_case_usa(self):
        result = parse_countries("USA")
        assert result == ["United States"]

    def test_special_case_uk(self):
        result = parse_countries("UK")
        assert result == ["United Kingdom"]

    def test_special_case_ivory_coast(self):
        result = parse_countries("Ivory Coast")
        assert result == ["Côte d'Ivoire"]

    def test_special_case_south_korea(self):
        result = parse_countries("South Korea")
        assert result == ["Korea, Republic of"]

    def test_special_case_iran(self):
        result = parse_countries("Iran")
        assert result == ["Iran, Islamic Republic of"]

    def test_special_case_russia(self):
        result = parse_countries("Russia")
        assert result == ["Russian Federation"]

    def test_special_case_bosnia(self):
        result = parse_countries("Bosnia")
        assert result == ["Bosnia and Herzegovina"]

    def test_extra_whitespace_is_handled(self):
        result = parse_countries("  France   Spain  ")
        assert "France" in result
        assert "Spain" in result


# ---------------------------------------------------------------------------
# _get_country_variants  (private, but worth validating)
# ---------------------------------------------------------------------------

class TestGetCountryVariants:
    """Tests for the _get_country_variants() helper."""

    def test_returns_non_empty_set(self):
        variants = _get_country_variants()
        assert isinstance(variants, set)
        assert len(variants) > 0

    def test_contains_standard_countries(self):
        variants = _get_country_variants()
        # pycountry.countries includes 'germany' (lower-cased)
        assert "germany" in variants
        assert "france" in variants

    def test_contains_custom_aliases(self):
        variants = _get_country_variants()
        assert "usa" in variants
        assert "uk" in variants
        assert "ivory coast" in variants
        assert "south korea" in variants


# ---------------------------------------------------------------------------
# _is_valid_word_boundary
# ---------------------------------------------------------------------------

class TestIsValidWordBoundary:
    """Tests for the _is_valid_word_boundary() helper."""

    def test_word_at_start(self):
        assert _is_valid_word_boundary("france is great", 0, 6) is True

    def test_word_at_end(self):
        text = "hello france"
        start = 6
        end = 12
        assert _is_valid_word_boundary(text, start, end) is True

    def test_word_in_middle(self):
        text = "in france now"
        assert _is_valid_word_boundary(text, 3, 9) is True

    def test_not_at_boundary_left(self):
        # "xfrance" — 'x' is alphanumeric before the start
        text = "xfrance"
        assert _is_valid_word_boundary(text, 1, 7) is False

    def test_not_at_boundary_right(self):
        # "francex" — 'x' is alphanumeric after the end
        text = "francex"
        assert _is_valid_word_boundary(text, 0, 6) is False

    def test_entire_string(self):
        assert _is_valid_word_boundary("france", 0, 6) is True


# ---------------------------------------------------------------------------
# _greedy_country_match
# ---------------------------------------------------------------------------

class TestGreedyCountryMatch:
    """Tests for the _greedy_country_match() helper."""

    def test_single_match(self):
        variants = {"france"}
        result = _greedy_country_match("France", variants)
        assert result == ["France"]

    def test_no_match(self):
        variants = {"france"}
        result = _greedy_country_match("Germany", variants)
        assert result == []

    def test_longer_variant_preferred(self):
        """Greedy matching should prefer 'south korea' over 'korea'."""
        variants = {"south korea", "korea"}
        result = _greedy_country_match("South Korea", variants)
        assert len(result) == 1
        assert result[0].lower() == "south korea"

    def test_multiple_countries_in_text(self):
        variants = {"france", "germany"}
        result = _greedy_country_match("France Germany", variants)
        assert len(result) == 2

    def test_preserves_original_case(self):
        variants = {"france"}
        result = _greedy_country_match("FRANCE", variants)
        assert result == ["FRANCE"]


# ---------------------------------------------------------------------------
# _standardize_country_name
# ---------------------------------------------------------------------------

class TestStandardizeCountryName:
    """Tests for the _standardize_country_name() helper."""

    def test_standard_pycountry_name(self):
        result = _standardize_country_name("Germany")
        assert result == "Germany"

    def test_lowercase_pycountry_name(self):
        result = _standardize_country_name("germany")
        assert result == "Germany"

    def test_special_case_usa(self):
        result = _standardize_country_name("USA")
        assert result == "United States"

    def test_special_case_uk(self):
        result = _standardize_country_name("uk")
        assert result == "United Kingdom"

    def test_special_case_ivory_coast(self):
        result = _standardize_country_name("ivory coast")
        assert result == "Côte d'Ivoire"

    def test_special_case_russia(self):
        result = _standardize_country_name("russia")
        assert result == "Russian Federation"

    def test_unknown_falls_back_to_title_case(self):
        result = _standardize_country_name("unknown country")
        assert result == "Unknown Country"

    def test_leading_trailing_whitespace(self):
        result = _standardize_country_name("  France  ")
        assert result == "France"


# ---------------------------------------------------------------------------
# is_homegrown
# ---------------------------------------------------------------------------

class TestIsHomegrown:
    """Tests for the is_homegrown() function."""

    def test_player_from_youth_u19(self):
        player = {
            "transfers": [
                {"from": "H. B. Sheva U19", "to": "Hapoel Beer Sheva"}
            ]
        }
        assert is_homegrown(player) is True

    def test_player_from_full_youth_name(self):
        player = {
            "transfers": [
                {"from": "Hapoel Beer Sheva U19", "to": "Hapoel Beer Sheva"}
            ]
        }
        assert is_homegrown(player) is True

    def test_player_not_from_youth(self):
        player = {
            "transfers": [
                {"from": "Maccabi Tel Aviv", "to": "Hapoel Beer Sheva"}
            ]
        }
        assert is_homegrown(player) is False

    def test_no_transfers(self):
        player = {"transfers": []}
        assert is_homegrown(player) is False

    def test_missing_transfers_key(self):
        player = {}
        assert is_homegrown(player) is False

    def test_multiple_transfers_one_from_youth(self):
        player = {
            "transfers": [
                {"from": "Some Club", "to": "Another Club"},
                {"from": "H. B. Sheva U19", "to": "Hapoel Beer Sheva"},
            ]
        }
        assert is_homegrown(player) is True

    def test_keyword_as_substring(self):
        """Even if the keyword appears as part of a longer string, it counts."""
        player = {
            "transfers": [
                {"from": "Academy: H. B. Sheva U19 (Reserves)", "to": "First Team"}
            ]
        }
        assert is_homegrown(player) is True

    def test_transfer_missing_from_key(self):
        """Transfer dict without 'from' key should not cause an error."""
        player = {
            "transfers": [
                {"to": "Some Club"}
            ]
        }
        assert is_homegrown(player) is False


# ---------------------------------------------------------------------------
# is_retired
# ---------------------------------------------------------------------------

class TestIsRetired:
    """Tests for the is_retired() function."""

    def test_retired_player(self):
        player = {
            "transfers": [
                {"from": "Hapoel Beer Sheva", "to": "Retired"}
            ]
        }
        assert is_retired(player) is True

    def test_retired_lowercase(self):
        player = {
            "transfers": [
                {"from": "Club", "to": "retired"}
            ]
        }
        assert is_retired(player) is True

    def test_retired_as_substring(self):
        player = {
            "transfers": [
                {"from": "Club", "to": "Career Retired - End"}
            ]
        }
        assert is_retired(player) is True

    def test_active_player(self):
        player = {
            "transfers": [
                {"from": "Club A", "to": "Club B"}
            ]
        }
        assert is_retired(player) is False

    def test_no_transfers(self):
        player = {"transfers": []}
        assert is_retired(player) is False

    def test_missing_transfers_key(self):
        player = {}
        assert is_retired(player) is False

    def test_multiple_transfers_last_is_retired(self):
        player = {
            "transfers": [
                {"from": "Club A", "to": "Club B"},
                {"from": "Club B", "to": "Retired"},
            ]
        }
        assert is_retired(player) is True

    def test_transfer_missing_to_key(self):
        """Transfer dict without 'to' key should not cause an error."""
        player = {
            "transfers": [
                {"from": "Some Club"}
            ]
        }
        assert is_retired(player) is False
