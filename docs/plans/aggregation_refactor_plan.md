# Aggregation Module Refactoring Plan (v2)

## Approach: Parallel Development (Option B)

**Strategy:** Build the new package alongside the old file, then migrate callers atomically.

**Key Principle:** The old `aggregation.py` stays working until we're 100% ready to switch.

---

## Prerequisites

### Current State
- Old file: `src/core/aggregation.py` (359 lines, working)
- Callers:
  - `scripts/run_pipeline.py` (line 11)
  - `tests/test_aggregation.py` (line 7)
- Test coverage: 1 test case (limited)

### Naming Strategy
- New package: `src/core/aggregation_v2/` (temporary name)
- After migration: rename to `src/core/aggregation/`

---

## Phase 1: Build New Package (No Breaking Changes)

All steps in this phase are **additive only** - the old code keeps working.

### Step 1.1: Create Package Structure
**Time:** 5 min | **Risk:** None

```bash
mkdir -p src/core/aggregation_v2
touch src/core/aggregation_v2/__init__.py
touch src/core/aggregation_v2/direct.py
touch src/core/aggregation_v2/output.py
touch src/core/aggregation_v2/classification.py
touch src/core/aggregation_v2/grouping.py
touch src/core/aggregation_v2/enrichment.py
```

**Verification:**
```bash
ls src/core/aggregation_v2/
# Should show: __init__.py, direct.py, output.py, classification.py, grouping.py, enrichment.py
```

---

### Step 1.2: Create `direct.py`
**Time:** 10 min | **Risk:** None

**File:** `src/core/aggregation_v2/direct.py`

```python
"""Direct holdings processing."""
import pandas as pd

from src.models import AggregatedExposure
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def process_direct_holdings(
    direct_positions: pd.DataFrame,
    exposures: AggregatedExposure
) -> None:
    """
    Process direct stock holdings and add to exposure aggregator.
    
    Args:
        direct_positions: DataFrame with columns [isin, name, market_value]
        exposures: AggregatedExposure instance to add records to
    """
    logger.info("Processing direct holdings...")
    
    if direct_positions.empty:
        logger.info("No direct holdings to process.")
        return
    
    for _, row in direct_positions.iterrows():
        record = exposures.get_or_create_record(
            isin=row["isin"],
            name=row["name"],
            asset_class="Equity"
        )
        record.direct = row["market_value"]
        record.sector = "Direct Holding"
        record.geography = "Global"
    
    logger.info(f"Processed {len(direct_positions)} direct holdings.")
```

**Verification:**
```bash
python -c "from src.core.aggregation_v2.direct import process_direct_holdings; print('OK')"
```

---

### Step 1.3: Create `output.py`
**Time:** 10 min | **Risk:** None

**File:** `src/core/aggregation_v2/output.py`

```python
"""Output formatting and file saving."""
import pandas as pd

from src.models import AggregatedExposure
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def finalize_and_save(
    exposures: AggregatedExposure,
    output_filepath: str
) -> pd.DataFrame:
    """
    Calculate totals, format output DataFrame, and save to CSV.
    
    Args:
        exposures: Aggregated exposure data
        output_filepath: Path to save CSV
        
    Returns:
        Final DataFrame with portfolio percentages
    """
    logger.info("--- Finalizing and Formatting Output ---")
    
    exposures.calculate_total()
    
    if not exposures.records:
        logger.warning("No holdings to process. Output file will be empty.")
        empty_df = pd.DataFrame(
            columns=[
                "isin", "name", "direct", "indirect",
                "total_exposure", "portfolio_percentage",
            ]
        )
        empty_df.to_csv(output_filepath, index=False)
        return empty_df
    
    final_df = exposures.to_dataframe()
    final_df.to_csv(output_filepath, index=False)
    logger.info(f"Report saved to {output_filepath}")
    
    return final_df
```

**Verification:**
```bash
python -c "from src.core.aggregation_v2.output import finalize_and_save; print('OK')"
```

---

### Step 1.4: Create `classification.py`
**Time:** 10 min | **Risk:** None

**File:** `src/core/aggregation_v2/classification.py`

```python
"""Asset classification for ETF holdings."""
import pandas as pd

from src.utils.classification import classify_holding
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def classify_etf_holdings(holdings: pd.DataFrame) -> pd.DataFrame:
    """
    Classify ETF holdings as Equity, Cash, or Derivative.
    
    Args:
        holdings: DataFrame with columns [ticker, name, ...]
        
    Returns:
        DataFrame with added 'asset_class' column
    """
    holdings = holdings.copy()
    
    holdings["asset_class"] = holdings.apply(
        lambda x: classify_holding(x.get("ticker", ""), x.get("name", "")),
        axis=1,
    )
    
    non_equity_count = len(holdings[holdings["asset_class"] != "Equity"])
    if non_equity_count > 0:
        logger.info(f"    - Classified {non_equity_count} rows as Non-Equity (Cash/Derivatives).")
    
    return holdings
```

**Verification:**
```bash
python -c "from src.core.aggregation_v2.classification import classify_etf_holdings; print('OK')"
```

---

### Step 1.5: Create `grouping.py`
**Time:** 20 min | **Risk:** Low

**File:** `src/core/aggregation_v2/grouping.py`

```python
"""Grouping and aggregation logic for indirect holdings."""
from typing import Literal

import pandas as pd

from src.models import AggregatedExposure
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def calculate_indirect_values(
    holdings: pd.DataFrame,
    etf_market_value: float
) -> pd.DataFrame:
    """
    Calculate indirect EUR value for each holding based on weight.
    
    Args:
        holdings: DataFrame with weight_percentage column
        etf_market_value: Total market value of the ETF position
        
    Returns:
        DataFrame with 'indirect' column added
    """
    holdings = holdings.copy()
    
    if "weight_percentage" in holdings.columns:
        holdings["weight_percentage"] = (
            holdings["weight_percentage"]
            .astype(str)
            .str.replace(",", ".")
            .apply(pd.to_numeric, errors="coerce")
            .fillna(0.0)
        )
    else:
        holdings["weight_percentage"] = 0.0
    
    holdings["indirect"] = holdings["weight_percentage"] / 100 * etf_market_value
    
    return holdings


def generate_group_id(row: pd.Series) -> str:
    """
    Generate unique group ID for aggregation.
    
    Uses ISIN if valid, otherwise falls back to Ticker+Name.
    
    Args:
        row: DataFrame row with isin, ticker, name columns
        
    Returns:
        Group ID string
    """
    isin = row.get("isin", "N/A")
    
    # Check for valid ISIN
    if (
        isin
        and str(isin) not in ("N/A", "nan", "None", "")
        and not str(isin).startswith("UNKNOWN")
        and not str(isin).startswith("NON_EQUITY")
    ):
        return str(isin)
    
    # Fallback: Ticker + Name
    ticker = str(row.get("ticker", ""))
    name = str(row.get("name", ""))
    return f"FALLBACK|{ticker}|{name}"


def normalize_special_assets(holdings: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Cash and other special asset ISINs for proper aggregation.
    
    Args:
        holdings: DataFrame with asset_class column
        
    Returns:
        DataFrame with normalized ISINs for special assets
    """
    if holdings.empty:
        return holdings
        
    holdings = holdings.copy()
    
    # Ensure asset_class column exists
    if "asset_class" not in holdings.columns:
        return holdings
    
    cash_mask = holdings["asset_class"] == "Cash"
    holdings.loc[cash_mask, "isin"] = "CASH_USD"
    holdings.loc[cash_mask, "name"] = "Cash & Equivalents"
    
    return holdings


def aggregate_indirect_holdings(
    all_holdings: pd.DataFrame,
    exposures: AggregatedExposure
) -> None:
    """
    Group indirect holdings by ID and add to exposure aggregator.
    
    Args:
        all_holdings: Combined holdings from all ETFs
        exposures: AggregatedExposure instance to add records to
    """
    if all_holdings.empty:
        logger.info("No indirect holdings to aggregate.")
        return
    
    # Normalize special assets (Cash, etc.)
    all_holdings = normalize_special_assets(all_holdings)
    
    # Generate group IDs
    all_holdings = all_holdings.copy()
    all_holdings["group_id"] = all_holdings.apply(generate_group_id, axis=1)
    
    # Aggregate by group
    aggregated = (
        all_holdings.groupby("group_id")
        .agg(
            indirect=("indirect", "sum"),
            name=("name", "first"),
            isin=("isin", "first"),
            asset_class=("asset_class", "first"),
        )
        .reset_index()
    )
    
    # Add to exposures
    for _, row in aggregated.iterrows():
        raw_asset_class = row.get("asset_class", "Equity")
        asset_class: Literal["Equity", "Cash", "Derivative"] = (
            "Cash" if raw_asset_class == "Cash"
            else "Derivative" if raw_asset_class == "Derivative"
            else "Equity"
        )
        
        record = exposures.get_or_create_record(
            isin=row["group_id"],
            name=row["name"],
            asset_class=asset_class
        )
        record.add_indirect(row["indirect"])
    
    logger.info("Indirect holdings aggregated.")
```

**Verification:**
```bash
python -c "from src.core.aggregation_v2.grouping import calculate_indirect_values, aggregate_indirect_holdings; print('OK')"
```

---

### Step 1.6: Create `enrichment.py`
**Time:** 30 min | **Risk:** Medium (most complex)

**File:** `src/core/aggregation_v2/enrichment.py`

```python
"""Tiered ISIN enrichment for ETF holdings."""
from typing import Tuple

import pandas as pd

from src.core.health import health
from src.data.enrichment import enrich_securities
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Default threshold: only enrich holdings with weight > 1%
ENRICHMENT_THRESHOLD = 1.0


def enrich_etf_holdings(
    holdings: pd.DataFrame,
    etf_market_value: float,
    threshold: float = ENRICHMENT_THRESHOLD
) -> pd.DataFrame:
    """
    Enrich equity holdings with ISIN data using tiered strategy.
    
    Tier 1 (weight > threshold): Full ISIN resolution via API
    Tier 2 (weight <= threshold): Skip resolution, use fallback aggregation
    
    Args:
        holdings: Classified ETF holdings DataFrame (must have 'asset_class' column)
        etf_market_value: Total ETF value for coverage calculation
        threshold: Weight percentage threshold for Tier 1 (default 1.0)
        
    Returns:
        Holdings DataFrame with 'isin' column populated
    """
    # If ISIN column already exists, nothing to enrich
    if "isin" in holdings.columns:
        return holdings
    
    holdings = holdings.copy()
    
    logger.info("    - 'isin' column not found. Enriching Equity holdings data...")
    
    # Only enrich equities
    if "asset_class" not in holdings.columns:
        logger.warning("    - 'asset_class' column missing. Cannot filter equities.")
        holdings["isin"] = [f"UNKNOWN_{i}" for i in range(len(holdings))]
        return holdings
    
    equity_mask = holdings["asset_class"] == "Equity"
    equity_holdings = holdings[equity_mask].copy()
    
    # Filter out invalid tickers
    if "ticker" in equity_holdings.columns:
        equity_holdings = equity_holdings.dropna(subset=["ticker"])
        equity_holdings = equity_holdings[
            equity_holdings["ticker"].apply(lambda x: isinstance(x, str) and len(str(x)) > 0)
        ]
    
    if equity_holdings.empty:
        logger.info("    - No valid equity holdings to enrich.")
        holdings["isin"] = [f"NON_EQUITY_{i}" for i in range(len(holdings))]
        return holdings
    
    # Split into tiers based on weight
    tier1_holdings, tier2_holdings = _split_by_weight(
        equity_holdings, etf_market_value, threshold
    )
    
    # Enrich Tier 1 only
    enriched_df = _enrich_tier1(tier1_holdings)
    
    # Merge enrichment back into original holdings
    holdings = _merge_enrichment(holdings, enriched_df, tier2_holdings, threshold)
    
    return holdings


def _split_by_weight(
    equity_holdings: pd.DataFrame,
    etf_market_value: float,
    threshold: float
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split holdings into Tier 1 (>threshold) and Tier 2 (<=threshold).
    
    Args:
        equity_holdings: Equity-only holdings DataFrame
        etf_market_value: ETF total value for coverage calculation
        threshold: Weight percentage threshold
        
    Returns:
        Tuple of (tier1_holdings, tier2_holdings)
    """
    if "weight_percentage" not in equity_holdings.columns:
        logger.warning("    ⚠️  'weight_percentage' column missing. Enriching all holdings.")
        return equity_holdings.copy(), pd.DataFrame()
    
    # Ensure numeric
    equity_holdings = equity_holdings.copy()
    equity_holdings["weight_percentage"] = pd.to_numeric(
        equity_holdings["weight_percentage"], errors="coerce"
    ).fillna(0.0)
    
    # Split by threshold
    tier1_mask = equity_holdings["weight_percentage"] > threshold
    tier1 = equity_holdings[tier1_mask].copy()
    tier2 = equity_holdings[~tier1_mask].copy()
    
    # Record health metrics
    health.record_metric("tier1_holdings", len(tier1))
    health.record_metric("tier2_holdings", len(tier2))
    
    # Calculate value coverage
    tier1_weight = tier1["weight_percentage"].sum()
    tier2_weight = tier2["weight_percentage"].sum()
    total_weight = tier1_weight + tier2_weight
    
    if total_weight > 0:
        tier1_val = (tier1_weight / total_weight) * etf_market_value
        tier2_val = (tier2_weight / total_weight) * etf_market_value
        health.record_value_coverage(tier1_val, tier2_val)
    
    logger.info(
        f"    - Tiered Enrichment: {len(tier1)} major (>{threshold}%), "
        f"{len(tier2)} minor (≤{threshold}%)"
    )
    logger.info(
        f"    - Skipping ISIN resolution for {len(tier2)} minor holdings"
    )
    
    return tier1, tier2


def _enrich_tier1(tier1_holdings: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich Tier 1 holdings via ISIN resolution API.
    
    Args:
        tier1_holdings: Holdings with weight > threshold
        
    Returns:
        DataFrame with [ticker, isin] columns from enrichment
    """
    if tier1_holdings.empty:
        return pd.DataFrame(columns=["ticker", "isin"])
    
    holdings_list = tier1_holdings.to_dict("records")
    enriched = enrich_securities(holdings_list)
    
    if enriched:
        enriched_df = pd.DataFrame(enriched)
        health.record_metric("tier1_resolved", len(enriched_df))
        return enriched_df
    
    return pd.DataFrame(columns=["ticker", "isin"])


def _merge_enrichment(
    holdings: pd.DataFrame,
    enriched_df: pd.DataFrame,
    tier2_holdings: pd.DataFrame,
    threshold: float
) -> pd.DataFrame:
    """
    Merge enriched ISINs back into holdings DataFrame.
    
    Args:
        holdings: Original holdings DataFrame
        enriched_df: Enrichment results with [ticker, isin]
        tier2_holdings: Tier 2 holdings (to mark as N/A)
        threshold: Weight threshold for failure logging
        
    Returns:
        Holdings with 'isin' column populated
    """
    holdings = holdings.copy()
    
    # Check if we can merge
    if "ticker" not in holdings.columns:
        logger.error("    - Cannot merge enriched data: 'ticker' column missing in holdings.")
        holdings["isin"] = [f"UNKNOWN_{i}" for i in range(len(holdings))]
        return holdings
    
    if enriched_df.empty or "ticker" not in enriched_df.columns:
        logger.warning("    - No enrichment data to merge.")
        holdings["isin"] = "N/A"
    else:
        # Merge on ticker
        holdings = pd.merge(
            holdings,
            enriched_df[["ticker", "isin"]],
            on="ticker",
            how="left",
        )
        logger.info("    - Enrichment complete. Merged ISINs into holdings.")
    
    # Mark Tier 2 holdings as N/A (they were intentionally skipped)
    if not tier2_holdings.empty and "ticker" in tier2_holdings.columns:
        tier2_tickers = set(tier2_holdings["ticker"].tolist())
        tier2_mask = holdings["ticker"].isin(tier2_tickers)
        holdings.loc[tier2_mask, "isin"] = "N/A"
    
    # Log Tier 1 failures
    _log_tier1_failures(holdings, threshold)
    
    # Fill remaining missing ISINs (non-equities, etc.)
    if "isin" in holdings.columns:
        missing_mask = holdings["isin"].isna()
        holdings.loc[missing_mask, "isin"] = [
            f"NON_EQUITY_{i}" for i in range(missing_mask.sum())
        ]
    else:
        holdings["isin"] = [f"UNKNOWN_{i}" for i in range(len(holdings))]
    
    return holdings


def _log_tier1_failures(holdings: pd.DataFrame, threshold: float) -> None:
    """
    Log and record health metrics for Tier 1 ISIN resolution failures.
    
    Args:
        holdings: Holdings after enrichment merge
        threshold: Weight threshold used for Tier 1
    """
    # Need both columns to identify failures
    if "weight_percentage" not in holdings.columns or "asset_class" not in holdings.columns:
        return
    
    if "isin" not in holdings.columns:
        return
    
    # Find Tier 1 holdings that failed to resolve
    tier1_failed = holdings[
        (holdings["asset_class"] == "Equity")
        & (holdings["isin"].isin(["N/A", None, ""]) | holdings["isin"].isna())
        & (holdings["weight_percentage"] > threshold)
    ]
    
    if tier1_failed.empty:
        return
    
    health.record_metric("tier1_failed", len(tier1_failed))
    logger.warning(
        f"    ⚠️  {len(tier1_failed)} major holdings (>{threshold}%) FAILED ISIN resolution:"
    )
    
    for i, (_, row) in enumerate(tier1_failed.iterrows()):
        if i >= 10:
            logger.warning(f"        ... and {len(tier1_failed) - 10} more")
            break
        
        ticker = row.get("ticker", "unknown")
        logger.warning(f"        - {ticker}")
        health.record_failure(
            stage="ENRICHMENT",
            item=str(ticker),
            error="Tier 1 ISIN Resolution Failed",
            fix=f"Add {ticker} to config/asset_universe.csv",
            severity="MEDIUM",
        )
```

**Verification:**
```bash
python -c "from src.core.aggregation_v2.enrichment import enrich_etf_holdings; print('OK')"
```

---

### Step 1.7: Create `__init__.py` (Orchestrator)
**Time:** 20 min | **Risk:** Low

**File:** `src/core/aggregation_v2/__init__.py`

```python
"""
Aggregation module for portfolio exposure calculation (v2).

This module decomposes ETF holdings and aggregates all exposures
(direct + indirect) into a single report.

Public API:
    run_aggregation(direct_positions, etf_positions, etf_holdings_map) -> DataFrame
"""
from typing import Dict

import pandas as pd

from src.config import TRUE_EXPOSURE_REPORT
from src.models import AggregatedExposure
from src.utils.logging_config import get_logger

from .classification import classify_etf_holdings
from .direct import process_direct_holdings
from .enrichment import enrich_etf_holdings
from .grouping import aggregate_indirect_holdings, calculate_indirect_values
from .output import finalize_and_save

logger = get_logger(__name__)

__all__ = ["run_aggregation"]


def run_aggregation(
    direct_positions: pd.DataFrame,
    etf_positions: pd.DataFrame,
    etf_holdings_map: Dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Run the entire exposure aggregation process.
    
    This function:
    1. Processes direct stock holdings
    2. Decomposes ETF holdings via classification, enrichment, and value calculation
    3. Aggregates all exposures by security
    4. Saves results to CSV
    
    Args:
        direct_positions: DataFrame with columns [isin, name, market_value]
        etf_positions: DataFrame with columns [isin, name, market_value]
        etf_holdings_map: Dict mapping ETF ISIN to holdings DataFrame
        
    Returns:
        DataFrame with aggregated true exposure per security
    """
    output_filepath = TRUE_EXPOSURE_REPORT
    
    if direct_positions.empty and etf_positions.empty:
        logger.warning("No positions found. Exiting aggregation.")
        return pd.DataFrame()
    
    # Initialize aggregator
    exposures = AggregatedExposure()
    
    # Step 1: Process direct holdings
    process_direct_holdings(direct_positions, exposures)
    
    # Step 2: Process ETF holdings
    logger.info("Processing indirect holdings (via ETFs)...")
    logger.info(f"Total ETFs to process: {len(etf_positions)}")
    
    all_holdings = pd.DataFrame()
    
    if not etf_positions.empty:
        for etf in etf_positions.to_dict("records"):
            etf_isin = etf["isin"]
            etf_market_value = etf["market_value"]
            
            logger.info(
                f"  - Processing ETF: {etf['name']} "
                f"(ISIN: {etf_isin}, Value: €{etf_market_value:,.2f})"
            )
            
            # Get holdings for this ETF
            holdings = etf_holdings_map.get(etf_isin)
            if holdings is None or holdings.empty:
                logger.warning(f"    - No holdings found for {etf_isin}. Skipping.")
                continue
            
            # Process: Classify -> Enrich -> Calculate values
            holdings = holdings.copy()
            holdings = classify_etf_holdings(holdings)
            holdings = enrich_etf_holdings(holdings, etf_market_value)
            holdings = calculate_indirect_values(holdings, etf_market_value)
            
            # Debug: log large holdings
            _log_large_holdings(holdings, etf_isin, etf["name"])
            
            # Accumulate
            all_holdings = pd.concat([all_holdings, holdings], ignore_index=True)
    
    # Debug: save intermediate results
    if not all_holdings.empty:
        try:
            all_holdings.to_csv("outputs/debug_all_holdings.csv", index=False)
        except Exception as e:
            logger.debug(f"Could not save debug file: {e}")
    
    # Step 3: Aggregate all indirect holdings
    aggregate_indirect_holdings(all_holdings, exposures)
    
    # Step 4: Finalize and save
    return finalize_and_save(exposures, output_filepath)


def _log_large_holdings(
    holdings: pd.DataFrame,
    etf_isin: str,
    etf_name: str
) -> None:
    """Log holdings with indirect value > €1000 for debugging."""
    if "indirect" not in holdings.columns:
        return
    
    large = holdings[holdings["indirect"] > 1000]
    if large.empty:
        return
    
    logger.info(f"🔎 FOUND LARGE HOLDING in ETF {etf_isin} ({etf_name}):")
    for _, row in large.iterrows():
        weight = row.get("weight_percentage", 0)
        indirect = row.get("indirect", 0)
        name = row.get("name", "Unknown")
        isin = row.get("isin", "No ISIN")
        logger.info(f"    -> {name} ({isin}): {weight:.2f}% = €{indirect:,.2f}")
```

**Verification:**
```bash
python -c "from src.core.aggregation_v2 import run_aggregation; print('OK')"
```

---

## Phase 2: Test New Package

### Step 2.1: Create Unit Tests for New Modules
**Time:** 30 min | **Risk:** None

**File:** `tests/test_aggregation_v2.py`

```python
"""Unit tests for aggregation_v2 package."""
import unittest
import pandas as pd

from src.core.aggregation_v2.direct import process_direct_holdings
from src.core.aggregation_v2.classification import classify_etf_holdings
from src.core.aggregation_v2.grouping import (
    calculate_indirect_values,
    generate_group_id,
    normalize_special_assets,
)
from src.models import AggregatedExposure


class TestDirect(unittest.TestCase):
    """Tests for direct.py"""
    
    def test_process_empty_dataframe(self):
        """Empty input should not add any records."""
        exposures = AggregatedExposure()
        empty_df = pd.DataFrame()
        process_direct_holdings(empty_df, exposures)
        self.assertEqual(len(exposures.records), 0)
    
    def test_process_single_holding(self):
        """Single holding should create one record."""
        exposures = AggregatedExposure()
        df = pd.DataFrame({
            "isin": ["US0378331005"],
            "name": ["Apple Inc."],
            "market_value": [1000.0]
        })
        process_direct_holdings(df, exposures)
        self.assertEqual(len(exposures.records), 1)
        self.assertEqual(exposures.records[0].direct, 1000.0)


class TestClassification(unittest.TestCase):
    """Tests for classification.py"""
    
    def test_classify_adds_column(self):
        """Classification should add asset_class column."""
        df = pd.DataFrame({
            "ticker": ["AAPL", "CASH"],
            "name": ["Apple", "US Dollar Cash"]
        })
        result = classify_etf_holdings(df)
        self.assertIn("asset_class", result.columns)
    
    def test_original_not_modified(self):
        """Original DataFrame should not be modified."""
        df = pd.DataFrame({"ticker": ["AAPL"], "name": ["Apple"]})
        original_cols = list(df.columns)
        classify_etf_holdings(df)
        self.assertEqual(list(df.columns), original_cols)


class TestGrouping(unittest.TestCase):
    """Tests for grouping.py"""
    
    def test_calculate_indirect_values(self):
        """Indirect value should be weight% * market_value / 100."""
        df = pd.DataFrame({"weight_percentage": [10.0, 5.0]})
        result = calculate_indirect_values(df, etf_market_value=1000.0)
        self.assertAlmostEqual(result["indirect"].iloc[0], 100.0)
        self.assertAlmostEqual(result["indirect"].iloc[1], 50.0)
    
    def test_generate_group_id_with_valid_isin(self):
        """Valid ISIN should be used as group ID."""
        row = pd.Series({"isin": "US0378331005", "ticker": "AAPL", "name": "Apple"})
        self.assertEqual(generate_group_id(row), "US0378331005")
    
    def test_generate_group_id_fallback(self):
        """Invalid ISIN should use fallback format."""
        row = pd.Series({"isin": "N/A", "ticker": "AAPL", "name": "Apple"})
        self.assertEqual(generate_group_id(row), "FALLBACK|AAPL|Apple")
    
    def test_normalize_cash(self):
        """Cash holdings should get normalized ISIN."""
        df = pd.DataFrame({
            "asset_class": ["Cash", "Equity"],
            "isin": ["random", "US123"],
            "name": ["Dollar", "Apple"]
        })
        result = normalize_special_assets(df)
        self.assertEqual(result.iloc[0]["isin"], "CASH_USD")
        self.assertEqual(result.iloc[0]["name"], "Cash & Equivalents")
        self.assertEqual(result.iloc[1]["isin"], "US123")  # Unchanged


class TestIntegration(unittest.TestCase):
    """Integration test comparing v2 to original."""
    
    def test_same_output_as_original(self):
        """New package should produce same results as original."""
        from src.core.aggregation import run_aggregation as run_original
        from src.core.aggregation_v2 import run_aggregation as run_v2
        
        # Same inputs as existing test
        direct = pd.DataFrame({
            "isin": ["AAPL"],
            "name": ["Apple Inc."],
            "market_value": [100.0]
        })
        etfs = pd.DataFrame({
            "isin": ["ETF1", "ETF2"],
            "name": ["Tech 1", "Tech 2"],
            "market_value": [1000.0, 2000.0]
        })
        holdings1 = pd.DataFrame({
            "isin": ["AAPL", "MSFT"],
            "name": ["Apple", "Microsoft"],
            "weight_percentage": [10.0, 20.0]
        })
        holdings2 = pd.DataFrame({
            "isin": ["AAPL", "GOOG"],
            "name": ["Apple", "Google"],
            "weight_percentage": [5.0, 15.0]
        })
        holdings_map = {"ETF1": holdings1, "ETF2": holdings2}
        
        # Run both
        result_original = run_original(direct.copy(), etfs.copy(), holdings_map)
        result_v2 = run_v2(direct.copy(), etfs.copy(), holdings_map)
        
        # Compare AAPL row
        aapl_orig = result_original[result_original["isin"] == "AAPL"].iloc[0]
        aapl_v2 = result_v2[result_v2["isin"] == "AAPL"].iloc[0]
        
        self.assertAlmostEqual(aapl_orig["direct"], aapl_v2["direct"], places=2)
        self.assertAlmostEqual(aapl_orig["indirect"], aapl_v2["indirect"], places=2)
        self.assertAlmostEqual(aapl_orig["total_exposure"], aapl_v2["total_exposure"], places=2)


if __name__ == "__main__":
    unittest.main()
```

**Verification:**
```bash
pytest tests/test_aggregation_v2.py -v
```

---

### Step 2.2: Run All Tests
**Time:** 5 min | **Risk:** None

```bash
# Run new tests
pytest tests/test_aggregation_v2.py -v

# Run original tests (should still pass - old code unchanged)
pytest tests/test_aggregation.py -v

# Run full suite
pytest tests/ -v
```

---

## Phase 3: Migrate Callers (Atomic Switch)

### Step 3.1: Update Imports
**Time:** 10 min | **Risk:** Medium

**Files to update:**

1. `scripts/run_pipeline.py` (line 11):
```python
# OLD:
from src.core.aggregation import run_aggregation

# NEW:
from src.core.aggregation_v2 import run_aggregation
```

2. `tests/test_aggregation.py` (line 7):
```python
# OLD:
from src.core.aggregation import run_aggregation

# NEW:
from src.core.aggregation_v2 import run_aggregation
```

**Verification:**
```bash
pytest tests/ -v
python -m scripts.run_pipeline  # If data available
```

---

### Step 3.2: Rename Packages
**Time:** 10 min | **Risk:** Low

```bash
# 1. Remove old file
rm src/core/aggregation.py

# 2. Rename new package to final name
mv src/core/aggregation_v2 src/core/aggregation

# 3. Update imports back to original path
# (In run_pipeline.py and test_aggregation.py)
# Change: from src.core.aggregation_v2 import run_aggregation
# To:     from src.core.aggregation import run_aggregation
```

**Verification:**
```bash
pytest tests/ -v
ruff check src/core/aggregation/
ruff format src/core/aggregation/
```

---

### Step 3.3: Cleanup
**Time:** 5 min | **Risk:** None

1. Delete `tests/test_aggregation_v2.py` (merge useful tests into `test_aggregation.py`)
2. Run full test suite
3. Run ruff lint/format
4. Commit

---

## Verification Checklist

### After Phase 1 (each step):
- [ ] `python -c "from src.core.aggregation_v2.MODULE import FUNC"` works
- [ ] Old `aggregation.py` still works
- [ ] `pytest tests/test_aggregation.py` still passes

### After Phase 2:
- [ ] `pytest tests/test_aggregation_v2.py` passes
- [ ] Integration test confirms same output

### After Phase 3:
- [ ] All 9+ tests pass
- [ ] `ruff check .` clean
- [ ] Pipeline runs successfully
- [ ] Old file deleted
- [ ] Package renamed to `aggregation/`

---

## Rollback Plan

**If Phase 1 fails:** Just delete `src/core/aggregation_v2/`. No harm done.

**If Phase 2 fails:** Fix the bugs in v2. Old code still works.

**If Phase 3 fails:** 
```bash
git checkout -- scripts/run_pipeline.py tests/test_aggregation.py
```
Old imports restored, old code still works.

---

## Summary

| Phase | Steps | Time | Risk | Rollback |
|-------|-------|------|------|----------|
| 1 | Build new package (1.1-1.7) | 1h 45m | None | Delete folder |
| 2 | Test new package (2.1-2.2) | 35m | None | Fix bugs |
| 3 | Migrate & rename (3.1-3.3) | 25m | Medium | Git checkout |

**Total: ~2.5 hours**

**Key Safety Features:**
1. Old code never touched until Phase 3
2. New code fully tested before migration
3. Integration test confirms identical output
4. Easy rollback at every phase
