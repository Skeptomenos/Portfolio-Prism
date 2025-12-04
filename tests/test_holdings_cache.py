"""
Tests for the Holdings Cache module.

Tests the 3-tier resolution system:
1. Local cache
2. Community data
3. Scraper fallback
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.data.holdings_cache import (
    HoldingsCache,
    ManualUploadRequired,
    LOCAL_CACHE_DIR,
    COMMUNITY_DIR,
)


@pytest.fixture
def temp_cache_dirs(tmp_path):
    """Create temporary cache directories for testing."""
    local_cache = tmp_path / "local_cache"
    community_dir = tmp_path / "community_data"
    manual_dir = tmp_path / "manual_uploads"

    local_cache.mkdir()
    community_dir.mkdir()
    manual_dir.mkdir()

    return {
        "local": local_cache,
        "community": community_dir,
        "manual": manual_dir,
    }


@pytest.fixture
def sample_holdings_df():
    """Create a sample holdings DataFrame."""
    return pd.DataFrame(
        {
            "ticker": ["AAPL", "MSFT", "GOOGL"],
            "name": ["Apple Inc", "Microsoft Corp", "Alphabet Inc"],
            "weight_percentage": [5.0, 4.5, 3.0],
        }
    )


@pytest.fixture
def holdings_cache(temp_cache_dirs):
    """Create a HoldingsCache instance with temporary directories."""
    with (
        patch("src.data.holdings_cache.LOCAL_CACHE_DIR", temp_cache_dirs["local"]),
        patch("src.data.holdings_cache.COMMUNITY_DIR", temp_cache_dirs["community"]),
        patch("src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]),
    ):
        cache = HoldingsCache(max_cache_age_days=7)
        # Patch the directories on the instance too
        return cache, temp_cache_dirs


class TestHoldingsCache:
    """Tests for HoldingsCache class."""

    def test_init_creates_directories(self, temp_cache_dirs):
        """Should create cache directories if they don't exist."""
        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", temp_cache_dirs["local"]),
            patch(
                "src.data.holdings_cache.COMMUNITY_DIR", temp_cache_dirs["community"]
            ),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()
            assert temp_cache_dirs["local"].exists()
            assert temp_cache_dirs["manual"].exists()

    def test_get_holdings_from_community_data(
        self, temp_cache_dirs, sample_holdings_df
    ):
        """Should return DataFrame when ISIN exists in community_data."""
        isin = "IE00B4L5Y983"
        community_dir = temp_cache_dirs["community"]

        # Write sample data to community dir
        csv_file = community_dir / f"{isin}.csv"
        sample_holdings_df.to_csv(csv_file, index=False)

        # Write metadata
        metadata = {
            isin: {
                "name": "Test ETF",
                "cached_at": datetime.now().isoformat(),
                "holdings_count": len(sample_holdings_df),
            }
        }
        (community_dir / "_metadata.json").write_text(json.dumps(metadata))

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", temp_cache_dirs["local"]),
            patch("src.data.holdings_cache.COMMUNITY_DIR", community_dir),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()
            holdings = cache.get_holdings(isin)

            assert holdings is not None
            assert len(holdings) == 3
            assert "AAPL" in holdings["ticker"].values

    def test_get_holdings_from_local_cache(self, temp_cache_dirs, sample_holdings_df):
        """Should return DataFrame when ISIN exists in local cache."""
        isin = "IE00B5BMR087"
        local_dir = temp_cache_dirs["local"]

        # Write sample data to local cache
        csv_file = local_dir / f"{isin}.csv"
        sample_holdings_df.to_csv(csv_file, index=False)

        # Write metadata (fresh)
        metadata = {
            isin: {
                "name": "Test ETF",
                "cached_at": datetime.now().isoformat(),
                "holdings_count": len(sample_holdings_df),
            }
        }
        (local_dir / "_metadata.json").write_text(json.dumps(metadata))

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", local_dir),
            patch(
                "src.data.holdings_cache.COMMUNITY_DIR", temp_cache_dirs["community"]
            ),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()
            holdings = cache.get_holdings(isin)

            assert holdings is not None
            assert len(holdings) == 3

    def test_local_cache_overrides_community(self, temp_cache_dirs):
        """Local cache should take priority over community data."""
        isin = "IE00B4L5Y983"
        local_dir = temp_cache_dirs["local"]
        community_dir = temp_cache_dirs["community"]

        # Write different data to local and community
        local_df = pd.DataFrame(
            {
                "ticker": ["LOCAL"],
                "name": ["Local Data"],
                "weight_percentage": [100.0],
            }
        )
        community_df = pd.DataFrame(
            {
                "ticker": ["COMMUNITY"],
                "name": ["Community Data"],
                "weight_percentage": [100.0],
            }
        )

        (local_dir / f"{isin}.csv").write_text(local_df.to_csv(index=False))
        (community_dir / f"{isin}.csv").write_text(community_df.to_csv(index=False))

        # Write metadata for both (local is fresh)
        local_metadata = {
            isin: {"cached_at": datetime.now().isoformat(), "name": "Local"}
        }
        community_metadata = {
            isin: {"cached_at": datetime.now().isoformat(), "name": "Community"}
        }
        (local_dir / "_metadata.json").write_text(json.dumps(local_metadata))
        (community_dir / "_metadata.json").write_text(json.dumps(community_metadata))

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", local_dir),
            patch("src.data.holdings_cache.COMMUNITY_DIR", community_dir),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()
            holdings = cache.get_holdings(isin)

            # Should get local data, not community
            assert "LOCAL" in holdings["ticker"].values
            assert "COMMUNITY" not in holdings["ticker"].values

    def test_stale_local_cache_falls_back_to_community(self, temp_cache_dirs):
        """Should fall back to community when local cache is stale."""
        isin = "IE00B4L5Y983"
        local_dir = temp_cache_dirs["local"]
        community_dir = temp_cache_dirs["community"]

        # Write data to both
        local_df = pd.DataFrame(
            {
                "ticker": ["LOCAL"],
                "name": ["Local Data"],
                "weight_percentage": [100.0],
            }
        )
        community_df = pd.DataFrame(
            {
                "ticker": ["COMMUNITY"],
                "name": ["Community Data"],
                "weight_percentage": [100.0],
            }
        )

        (local_dir / f"{isin}.csv").write_text(local_df.to_csv(index=False))
        (community_dir / f"{isin}.csv").write_text(community_df.to_csv(index=False))

        # Local metadata is STALE (8 days old)
        stale_date = (datetime.now() - timedelta(days=8)).isoformat()
        local_metadata = {isin: {"cached_at": stale_date, "name": "Local"}}
        community_metadata = {
            isin: {"cached_at": datetime.now().isoformat(), "name": "Community"}
        }
        (local_dir / "_metadata.json").write_text(json.dumps(local_metadata))
        (community_dir / "_metadata.json").write_text(json.dumps(community_metadata))

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", local_dir),
            patch("src.data.holdings_cache.COMMUNITY_DIR", community_dir),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache(max_cache_age_days=7)
            holdings = cache.get_holdings(isin)

            # Should get community data since local is stale
            assert "COMMUNITY" in holdings["ticker"].values

    def test_raises_manual_upload_required_when_not_found(self, temp_cache_dirs):
        """Should raise ManualUploadRequired when ISIN not in any cache."""
        isin = "UNKNOWN_ISIN"

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", temp_cache_dirs["local"]),
            patch(
                "src.data.holdings_cache.COMMUNITY_DIR", temp_cache_dirs["community"]
            ),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()

            with pytest.raises(ManualUploadRequired) as exc_info:
                cache.get_holdings(isin)

            assert exc_info.value.isin == isin

    def test_save_holdings_writes_to_local_cache(
        self, temp_cache_dirs, sample_holdings_df
    ):
        """Should write CSV to local cache directory."""
        isin = "NEW_ISIN_123"
        local_dir = temp_cache_dirs["local"]

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", local_dir),
            patch(
                "src.data.holdings_cache.COMMUNITY_DIR", temp_cache_dirs["community"]
            ),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()
            cache._save_to_local_cache(isin, sample_holdings_df, source="test")

            # Check file was created
            csv_file = local_dir / f"{isin}.csv"
            assert csv_file.exists()

            # Check metadata was updated
            metadata_file = local_dir / "_metadata.json"
            assert metadata_file.exists()
            metadata = json.loads(metadata_file.read_text())
            assert isin in metadata
            assert metadata[isin]["source"] == "test"
            assert metadata[isin]["holdings_count"] == 3

    def test_get_cache_stats_returns_correct_counts(
        self, temp_cache_dirs, sample_holdings_df
    ):
        """Should return accurate cache statistics."""
        local_dir = temp_cache_dirs["local"]
        community_dir = temp_cache_dirs["community"]

        # Create 2 local, 3 community
        for i, isin in enumerate(["LOCAL1", "LOCAL2"]):
            (local_dir / f"{isin}.csv").write_text(
                sample_holdings_df.to_csv(index=False)
            )

        for isin in ["COMM1", "COMM2", "COMM3"]:
            (community_dir / f"{isin}.csv").write_text(
                sample_holdings_df.to_csv(index=False)
            )

        # Metadata
        local_metadata = {
            "LOCAL1": {"cached_at": datetime.now().isoformat()},
            "LOCAL2": {"cached_at": datetime.now().isoformat()},
        }
        community_metadata = {
            "COMM1": {"cached_at": datetime.now().isoformat()},
            "COMM2": {"cached_at": datetime.now().isoformat()},
            "COMM3": {"cached_at": datetime.now().isoformat()},
        }
        (local_dir / "_metadata.json").write_text(json.dumps(local_metadata))
        (community_dir / "_metadata.json").write_text(json.dumps(community_metadata))

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", local_dir),
            patch("src.data.holdings_cache.COMMUNITY_DIR", community_dir),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()
            stats = cache.get_cache_stats()

            assert stats["local_count"] == 2
            assert stats["community_count"] == 3

    def test_has_holdings_returns_true_for_cached(
        self, temp_cache_dirs, sample_holdings_df
    ):
        """Should return True when holdings are available."""
        isin = "IE00B4L5Y983"
        community_dir = temp_cache_dirs["community"]

        (community_dir / f"{isin}.csv").write_text(
            sample_holdings_df.to_csv(index=False)
        )

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", temp_cache_dirs["local"]),
            patch("src.data.holdings_cache.COMMUNITY_DIR", community_dir),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()

            assert cache.has_holdings(isin) is True
            assert cache.has_holdings("UNKNOWN") is False

    def test_invalidate_removes_from_cache(self, temp_cache_dirs, sample_holdings_df):
        """Should remove cached data when invalidated."""
        isin = "IE00B4L5Y983"
        local_dir = temp_cache_dirs["local"]

        # Create cached data
        csv_file = local_dir / f"{isin}.csv"
        csv_file.write_text(sample_holdings_df.to_csv(index=False))

        metadata = {isin: {"cached_at": datetime.now().isoformat()}}
        (local_dir / "_metadata.json").write_text(json.dumps(metadata))

        with (
            patch("src.data.holdings_cache.LOCAL_CACHE_DIR", local_dir),
            patch(
                "src.data.holdings_cache.COMMUNITY_DIR", temp_cache_dirs["community"]
            ),
            patch(
                "src.data.holdings_cache.MANUAL_UPLOAD_DIR", temp_cache_dirs["manual"]
            ),
        ):
            cache = HoldingsCache()
            cache.invalidate(isin)

            # File should be deleted
            assert not csv_file.exists()

            # Metadata should be updated
            metadata = json.loads((local_dir / "_metadata.json").read_text())
            assert isin not in metadata


class TestManualUploadRequired:
    """Tests for ManualUploadRequired exception."""

    def test_exception_attributes(self):
        """Should store isin, provider, download_url."""
        exc = ManualUploadRequired(
            isin="IE00B4L5Y983",
            provider="iShares",
            message="Test message",
            download_url="https://example.com",
        )

        assert exc.isin == "IE00B4L5Y983"
        assert exc.provider == "iShares"
        assert exc.download_url == "https://example.com"
        assert "Test message" in str(exc)

    def test_exception_with_minimal_args(self):
        """Should work with just isin and provider."""
        exc = ManualUploadRequired(
            isin="IE00B4L5Y983",
            provider="iShares",
        )

        assert exc.isin == "IE00B4L5Y983"
        assert exc.provider == "iShares"
        assert exc.download_url is None
