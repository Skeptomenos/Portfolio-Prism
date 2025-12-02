"""Tests for the ISIN resolution module."""

import os
import unittest
from unittest.mock import MagicMock, patch

from src.data.resolution import (
    AssetUniverse,
    ISINResolver,
    ResolutionResult,
    resolve_isin,
)
from src.utils.isin_validator import (
    generate_group_key,
    is_placeholder_isin,
    is_valid_isin,
)


class TestISINValidator(unittest.TestCase):
    """Tests for ISIN validation functions."""

    def test_valid_isin_apple(self) -> None:
        """Apple ISIN is valid."""
        self.assertTrue(is_valid_isin("US0378331005"))

    def test_valid_isin_microsoft(self) -> None:
        """Microsoft ISIN is valid."""
        self.assertTrue(is_valid_isin("US5949181045"))

    def test_valid_isin_german(self) -> None:
        """German ISIN is valid."""
        self.assertTrue(is_valid_isin("DE0007164600"))

    def test_invalid_isin_wrong_length(self) -> None:
        """Invalid length ISINs are rejected."""
        self.assertFalse(is_valid_isin("US037833100"))  # Too short
        self.assertFalse(is_valid_isin("US03783310055"))  # Too long

    def test_invalid_isin_wrong_checksum(self) -> None:
        """Invalid checksum ISINs are rejected."""
        self.assertFalse(is_valid_isin("US0378331009"))  # Wrong check digit

    def test_invalid_isin_none(self) -> None:
        """None is not a valid ISIN."""
        self.assertFalse(is_valid_isin(None))

    def test_invalid_isin_empty(self) -> None:
        """Empty string is not a valid ISIN."""
        self.assertFalse(is_valid_isin(""))

    def test_placeholder_fallback(self) -> None:
        """FALLBACK patterns are placeholders."""
        self.assertTrue(is_placeholder_isin("FALLBACK|AAPL|Apple"))

    def test_placeholder_unresolved(self) -> None:
        """UNRESOLVED patterns are placeholders."""
        self.assertTrue(is_placeholder_isin("UNRESOLVED:AAPL:1234567890"))

    def test_placeholder_na(self) -> None:
        """N/A is a placeholder."""
        self.assertTrue(is_placeholder_isin("N/A"))
        self.assertTrue(is_placeholder_isin("NA"))

    def test_placeholder_pipe(self) -> None:
        """Strings with pipes are placeholders."""
        self.assertTrue(is_placeholder_isin("some|value|here"))


class TestGroupKey(unittest.TestCase):
    """Tests for group key generation."""

    def test_generate_group_key_format(self) -> None:
        """Group key has correct format."""
        key = generate_group_key("AAPL", "Apple Inc.")
        self.assertTrue(key.startswith("UNRESOLVED:AAPL:"))

        # Hash part is 10 digits
        hash_part = key.split(":")[-1]
        self.assertEqual(len(hash_part), 10)
        self.assertTrue(hash_part.isdigit())

    def test_generate_group_key_deterministic(self) -> None:
        """Same input produces same key."""
        key1 = generate_group_key("AAPL", "Apple Inc.")
        key2 = generate_group_key("AAPL", "Apple Inc.")
        self.assertEqual(key1, key2)

    def test_generate_group_key_different_inputs(self) -> None:
        """Different inputs produce different keys."""
        key1 = generate_group_key("AAPL", "Apple Inc.")
        key2 = generate_group_key("MSFT", "Microsoft Corp")
        self.assertNotEqual(key1, key2)


class TestResolutionResult(unittest.TestCase):
    """Tests for ResolutionResult dataclass."""

    def test_valid_isin_preserved(self) -> None:
        """Valid ISIN is preserved in result."""
        result = ResolutionResult(isin="US0378331005", status="resolved", detail="test")
        self.assertEqual(result.isin, "US0378331005")
        self.assertEqual(result.status, "resolved")

    def test_invalid_isin_cleared(self) -> None:
        """Invalid ISIN is cleared and status updated."""
        result = ResolutionResult(isin="INVALID123XX", status="resolved", detail="test")
        self.assertIsNone(result.isin)
        self.assertEqual(result.status, "unresolved")
        self.assertEqual(result.detail, "isin_format_invalid")


class TestAssetUniverse(unittest.TestCase):
    """Tests for AssetUniverse lookup."""

    def test_load_empty_if_missing(self) -> None:
        """Returns empty universe if file missing."""
        with patch("os.path.exists", return_value=False):
            universe = AssetUniverse.load()
            self.assertTrue(universe.df.empty)
            self.assertEqual(len(universe.ticker_index), 0)

    def test_lookup_by_ticker(self) -> None:
        """Ticker lookup works correctly."""
        universe = AssetUniverse.load()
        # If AAPL is in the universe, it should resolve
        result = universe.lookup_by_ticker("AAPL")
        if result:
            self.assertTrue(is_valid_isin(result))


class TestISINResolver(unittest.TestCase):
    """Tests for ISINResolver class."""

    def test_resolve_provider_isin(self) -> None:
        """Provider ISIN is used when valid."""
        resolver = ISINResolver()
        result = resolver.resolve(
            ticker="AAPL",
            name="Apple Inc.",
            provider_isin="US0378331005",
            weight=5.0,
        )

        self.assertEqual(result.status, "resolved")
        self.assertEqual(result.isin, "US0378331005")
        self.assertEqual(result.detail, "provider")

    def test_resolve_invalid_provider_isin_falls_back(self) -> None:
        """Invalid provider ISIN triggers fallback resolution."""
        resolver = ISINResolver()
        result = resolver.resolve(
            ticker="AAPL",
            name="Apple Inc.",
            provider_isin="INVALID123",
            weight=5.0,
        )

        # Should fall back to other methods (universe, cache, etc.)
        self.assertNotEqual(result.detail, "provider")

    def test_resolve_tier2_skipped(self) -> None:
        """Low weight holdings are skipped."""
        resolver = ISINResolver(tier1_threshold=1.0)
        result = resolver.resolve(
            ticker="UNKNOWN",
            name="Unknown Corp",
            provider_isin=None,
            weight=0.5,  # Below threshold
        )

        self.assertEqual(result.status, "skipped")
        self.assertEqual(result.detail, "tier2_skipped")
        self.assertIsNone(result.isin)

    def test_stats_tracking(self) -> None:
        """Resolution stats are tracked correctly."""
        resolver = ISINResolver()

        # Resolve with provider ISIN
        resolver.resolve("AAPL", "Apple", "US0378331005", 5.0)

        # Resolve skipped
        resolver.resolve("UNKNOWN", "Unknown", None, 0.1)

        self.assertEqual(resolver.stats["total"], 2)
        self.assertGreaterEqual(resolver.stats["resolved"], 1)
        self.assertGreaterEqual(resolver.stats["skipped"], 1)

    def test_stats_summary(self) -> None:
        """Stats summary is formatted correctly."""
        resolver = ISINResolver()
        resolver.resolve("AAPL", "Apple", "US0378331005", 5.0)

        summary = resolver.get_stats_summary()

        self.assertIn("Resolution Summary", summary)
        self.assertIn("Total processed:", summary)


class TestResolveISINConvenience(unittest.TestCase):
    """Tests for the resolve_isin convenience function."""

    def test_resolve_isin_with_valid_provider(self) -> None:
        """Convenience function works with valid provider ISIN."""
        result = resolve_isin(
            ticker="AAPL",
            name="Apple Inc.",
            provider_isin="US0378331005",
            weight=5.0,
        )

        self.assertEqual(result.status, "resolved")
        self.assertEqual(result.isin, "US0378331005")


if __name__ == "__main__":
    unittest.main()
