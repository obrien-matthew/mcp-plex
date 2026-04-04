"""Tests for input validation helpers."""

import pytest

from plex_mcp.validation import (
    validate_limit,
    validate_rating_key,
    validate_rating_keys,
)


class TestValidateRatingKey:
    def test_valid_numeric_string(self):
        assert validate_rating_key("12345") == "12345"

    def test_strips_whitespace(self):
        assert validate_rating_key("  42  ") == "42"

    def test_rejects_non_numeric(self):
        with pytest.raises(ValueError, match="Invalid rating key"):
            validate_rating_key("abc")

    def test_rejects_empty_string(self):
        with pytest.raises(ValueError, match="Invalid rating key"):
            validate_rating_key("")

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="Invalid rating key"):
            validate_rating_key("-1")

    def test_rejects_float_string(self):
        with pytest.raises(ValueError, match="Invalid rating key"):
            validate_rating_key("1.5")


class TestValidateRatingKeys:
    def test_valid_list(self):
        assert validate_rating_keys(["1", "2", "3"]) == ["1", "2", "3"]

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            validate_rating_keys([])

    def test_invalid_key_in_list_raises(self):
        with pytest.raises(ValueError, match="Invalid rating key"):
            validate_rating_keys(["1", "abc", "3"])


class TestValidateLimit:
    def test_within_range(self):
        assert validate_limit(10) == 10

    def test_clamps_to_min(self):
        assert validate_limit(0) == 1
        assert validate_limit(-5) == 1

    def test_clamps_to_max(self):
        assert validate_limit(100) == 50

    def test_custom_max(self):
        assert validate_limit(200, max_val=100) == 100

    def test_boundary_values(self):
        assert validate_limit(1) == 1
        assert validate_limit(50) == 50
