import pytest
from isin_parser import parse_description


def test_parse_description_found_middle():
    """Tests that an ISIN is found when it's in the middle of the string."""
    description = "Savings plan execution LU0908500753 Amundi Index Solutions..."
    assert parse_description(description) == {"isin": "LU0908500753"}


def test_parse_description_found_start():
    """Tests that an ISIN is found when it's at the beginning of the string."""
    description = "DE0007472060 WIRECARD AG direct sell"
    assert parse_description(description) == {"isin": "DE0007472060"}


def test_parse_description_not_found():
    """Tests that None is returned when no ISIN is present."""
    description = "Core S&P 500 UCITS ETF USD (Acc), quantity: 0.017220"
    assert parse_description(description) == {"isin": None}


def test_parse_description_empty_string():
    """Tests that None is returned for an empty string."""
    description = ""
    assert parse_description(description) == {"isin": None}


def test_parse_description_no_isin():
    """Tests that None is returned for a string without an ISIN."""
    description = "just some random text without a valid isin"
    assert parse_description(description) == {"isin": None}


def test_parse_description_another_valid_isin():
    """Tests another valid ISIN format."""
    description = "US0378331005 APPLE INC."
    assert parse_description(description) == {"isin": "US0378331005"}


def test_parse_description_lowercase_isin_fails():
    """Tests that a lowercase ISIN-like string is not matched."""
    description = "de0007472060 wirecard ag"
    assert parse_description(description) == {"isin": None}


def test_parse_description_too_short_fails():
    """Tests that a string shorter than an ISIN is not matched."""
    description = "DE123456789"
    assert parse_description(description) == {"isin": None}


def test_parse_description_too_long_fails():
    """Tests that a string longer than an ISIN is not matched unless it contains one."""
    description = "DE00074720601 EXTRA DIGIT"
    assert parse_description(description) == {"isin": "DE0007472060"}


def test_parse_description_mixed_case_country_code_fails():
    """Tests that a mixed case country code is not matched."""
    description = "De0007472060 WIRECARD AG"
    assert parse_description(description) == {"isin": None}
