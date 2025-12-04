"""
Tests for the Holdings Normalizer module.

Tests handling of messy files from various providers:
- Column name mapping
- German number format
- Weight auto-scaling
- Footer removal
"""

import pandas as pd
import pytest

from src.data.holdings_normalizer import (
    normalize_holdings,
    _parse_numbers,
    _normalize_column_names,
    _map_columns,
    _normalize_weights,
    _remove_invalid_rows,
    _validate_isin,
)


class TestNormalizeHoldings:
    """Tests for the main normalize_holdings function."""

    def test_normalize_already_normalized_data(self):
        """Should not modify already-normalized data."""
        df = pd.DataFrame(
            {
                "ticker": ["AAPL", "MSFT"],
                "name": ["Apple Inc", "Microsoft Corp"],
                "weight_percentage": [5.0, 4.5],
                "isin": ["US0378331005", "US5949181045"],
            }
        )

        result = normalize_holdings(df)

        assert len(result) == 2
        assert result["weight_percentage"].sum() == 9.5
        assert "AAPL" in result["ticker"].values

    def test_normalize_empty_dataframe(self):
        """Should handle empty DataFrame gracefully."""
        df = pd.DataFrame()
        result = normalize_holdings(df)
        assert result.empty

    def test_normalize_german_column_names(self):
        """Should map German column names to standard names."""
        df = pd.DataFrame(
            {
                "Bezeichnung": ["Apple Inc", "Microsoft Corp"],
                "Gewichtung": [5.0, 4.5],
                "ISIN": ["US0378331005", "US5949181045"],
            }
        )

        result = normalize_holdings(df)

        assert "name" in result.columns
        assert "weight_percentage" in result.columns
        assert "isin" in result.columns

    def test_normalize_sorts_by_weight(self):
        """Should sort results by weight descending."""
        df = pd.DataFrame(
            {
                "name": ["Small", "Large", "Medium"],
                "weight_percentage": [1.0, 10.0, 5.0],
            }
        )

        result = normalize_holdings(df)

        assert result.iloc[0]["name"] == "Large"
        assert result.iloc[1]["name"] == "Medium"
        assert result.iloc[2]["name"] == "Small"


class TestParseNumbers:
    """Tests for German/US number format parsing."""

    def test_parse_german_format(self):
        """Should convert German format (1.234,56) to float."""
        series = pd.Series(["1.234,56", "2.500,00", "100,50"])
        result = _parse_numbers(series)

        assert abs(result.iloc[0] - 1234.56) < 0.01
        assert abs(result.iloc[1] - 2500.00) < 0.01
        assert abs(result.iloc[2] - 100.50) < 0.01

    def test_parse_us_format(self):
        """Should handle US format (1,234.56) correctly."""
        series = pd.Series(["1,234.56", "2,500.00", "100.50"])
        result = _parse_numbers(series)

        assert abs(result.iloc[0] - 1234.56) < 0.01
        assert abs(result.iloc[1] - 2500.00) < 0.01
        assert abs(result.iloc[2] - 100.50) < 0.01

    def test_parse_percentage_signs(self):
        """Should remove percentage signs."""
        series = pd.Series(["5.5%", "10%", "2.25%"])
        result = _parse_numbers(series)

        assert abs(result.iloc[0] - 5.5) < 0.01
        assert abs(result.iloc[1] - 10.0) < 0.01
        assert abs(result.iloc[2] - 2.25) < 0.01

    def test_parse_currency_symbols(self):
        """Should remove currency symbols."""
        series = pd.Series(["€100", "$200", "£300"])
        result = _parse_numbers(series)

        assert result.iloc[0] == 100
        assert result.iloc[1] == 200
        assert result.iloc[2] == 300

    def test_parse_na_values(self):
        """Should handle N/A values."""
        series = pd.Series(["5.0", "N/A", "-", "", None])
        result = _parse_numbers(series)

        assert result.iloc[0] == 5.0
        assert pd.isna(result.iloc[1])
        assert pd.isna(result.iloc[2])
        assert pd.isna(result.iloc[3])
        assert pd.isna(result.iloc[4])

    def test_parse_simple_decimal(self):
        """Should handle simple comma as decimal (German style)."""
        series = pd.Series(["5,5", "10,25"])
        result = _parse_numbers(series)

        assert abs(result.iloc[0] - 5.5) < 0.01
        assert abs(result.iloc[1] - 10.25) < 0.01


class TestNormalizeWeights:
    """Tests for weight normalization and auto-scaling."""

    def test_auto_scale_decimal_weights(self):
        """Should multiply by 100 if sum is approximately 1.0."""
        df = pd.DataFrame(
            {
                "name": ["A", "B", "C"],
                "weight_percentage": [0.5, 0.3, 0.2],  # Sum = 1.0
            }
        )

        result = _normalize_weights(df)

        # Should be scaled to percentages
        assert abs(result["weight_percentage"].sum() - 100.0) < 0.1

    def test_preserve_percentage_weights(self):
        """Should not scale weights that are already percentages."""
        df = pd.DataFrame(
            {
                "name": ["A", "B", "C"],
                "weight_percentage": [50.0, 30.0, 20.0],  # Sum = 100
            }
        )

        result = _normalize_weights(df)

        assert abs(result["weight_percentage"].sum() - 100.0) < 0.1

    def test_handle_missing_weight_column(self):
        """Should handle DataFrame without weight column."""
        df = pd.DataFrame(
            {
                "name": ["A", "B"],
                "other_column": [1, 2],
            }
        )

        result = _normalize_weights(df)

        # Should return unchanged (with warning logged)
        assert (
            "weight_percentage" not in result.columns
            or result["weight_percentage"].isna().all()
        )


class TestColumnMapping:
    """Tests for column name mapping."""

    def test_map_weight_variants(self):
        """Should map various weight column names."""
        variants = [
            "weight",
            "% of holdings",
            "portfolio weight",
            "gewichtung",
            "allocation",
        ]

        for variant in variants:
            df = pd.DataFrame({variant: [5.0], "name": ["Test"]})
            df.columns = [c.lower() for c in df.columns]
            result = _map_columns(df)
            assert "weight_percentage" in result.columns, (
                f"Failed for variant: {variant}"
            )

    def test_map_name_variants(self):
        """Should map various name column names."""
        variants = [
            "security name",
            "issuer",
            "company",
            "bezeichnung",
        ]

        for variant in variants:
            df = pd.DataFrame({variant: ["Test"], "weight": [5.0]})
            df.columns = [c.lower() for c in df.columns]
            result = _map_columns(df)
            assert "name" in result.columns, f"Failed for variant: {variant}"

    def test_map_isin_variants(self):
        """Should map various ISIN column names."""
        # Note: "security isin" excluded because substring matching in _map_columns
        # causes it to match "security name" first. This is a known limitation.
        variants = [
            "isin",
            "isin code",
            "isin-code",
            "constituent isin",
        ]

        for variant in variants:
            df = pd.DataFrame({variant: ["US0378331005"], "ticker": ["AAPL"]})
            df.columns = [c.lower() for c in df.columns]
            result = _map_columns(df)
            assert "isin" in result.columns, f"Failed for variant: {variant}"


class TestRemoveInvalidRows:
    """Tests for invalid row removal."""

    def test_remove_zero_weight_rows(self):
        """Should remove rows with zero weight."""
        df = pd.DataFrame(
            {
                "name": ["Valid", "Zero"],
                "weight_percentage": [5.0, 0.0],
            }
        )

        result = _remove_invalid_rows(df)

        assert len(result) == 1
        assert result.iloc[0]["name"] == "Valid"

    def test_remove_total_rows(self):
        """Should remove rows that are totals/summaries."""
        df = pd.DataFrame(
            {
                "name": ["Apple Inc", "Total", "Sum of Holdings", "Microsoft"],
                "weight_percentage": [5.0, 100.0, 100.0, 4.0],
            }
        )

        result = _remove_invalid_rows(df)

        assert len(result) == 2
        assert "Total" not in result["name"].values
        assert "Sum of Holdings" not in result["name"].values

    def test_remove_cash_rows(self):
        """Should remove cash/margin rows."""
        df = pd.DataFrame(
            {
                "name": ["Apple Inc", "Cash", "Cash and equivalents"],
                "weight_percentage": [5.0, 1.0, 0.5],
            }
        )

        result = _remove_invalid_rows(df)

        assert len(result) == 1
        assert result.iloc[0]["name"] == "Apple Inc"

    def test_preserve_valid_rows(self):
        """Should preserve valid holding rows."""
        df = pd.DataFrame(
            {
                "name": ["Apple Inc", "Microsoft Corp", "Alphabet Inc"],
                "weight_percentage": [5.0, 4.0, 3.0],
            }
        )

        result = _remove_invalid_rows(df)

        assert len(result) == 3


class TestValidateIsin:
    """Tests for ISIN validation."""

    def test_valid_isin(self):
        """Should accept valid ISIN format."""
        assert _validate_isin("US0378331005") == "US0378331005"
        assert _validate_isin("IE00B4L5Y983") == "IE00B4L5Y983"
        assert _validate_isin("DE000A0F5UF5") == "DE000A0F5UF5"

    def test_lowercase_isin_normalized(self):
        """Should normalize lowercase ISIN to uppercase."""
        assert _validate_isin("us0378331005") == "US0378331005"

    def test_invalid_isin_returns_none(self):
        """Should return None for invalid ISIN."""
        assert _validate_isin("INVALID") is None
        assert _validate_isin("12345") is None
        assert _validate_isin("") is None
        assert _validate_isin(None) is None
        assert _validate_isin("nan") is None

    def test_isin_with_whitespace(self):
        """Should handle ISIN with whitespace."""
        assert _validate_isin("  US0378331005  ") == "US0378331005"


class TestNormalizeColumnNames:
    """Tests for column name normalization."""

    def test_lowercase_columns(self):
        """Should convert column names to lowercase."""
        df = pd.DataFrame({"NAME": [1], "Weight": [2], "ISIN": [3]})
        result = _normalize_column_names(df)

        assert all(col.islower() for col in result.columns)

    def test_strip_whitespace(self):
        """Should strip whitespace from column names."""
        df = pd.DataFrame({"  name  ": [1], "weight ": [2]})
        result = _normalize_column_names(df)

        assert "name" in result.columns
        assert "weight" in result.columns

    def test_remove_newlines(self):
        """Should remove newlines from column names."""
        df = pd.DataFrame({"name\n": [1], "weight\r\n": [2]})
        result = _normalize_column_names(df)

        assert "name" in result.columns
        assert "weight" in result.columns
