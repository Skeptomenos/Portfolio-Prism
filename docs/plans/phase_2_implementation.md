# Phase 2 Implementation Plan: Pydantic Schemas, Aggregation Refactor & Integration Tests

> **Objective:** Increase production readiness from 78% to 90% by implementing type-safe data models, modular aggregation logic, and comprehensive integration tests.

---

## Executive Summary

This plan addresses three interconnected improvements:

| Task | Goal | Impact |
|------|------|--------|
| **TASK-005** | Pydantic Schemas | Type safety, validation at boundaries, IDE support |
| **TASK-006** | Aggregation Refactor | Testable units, maintainable code, reduced complexity |
| **Integration Tests** | End-to-end validation | Regression prevention, confidence in changes |

**Estimated Time:** 4-6 hours total
**Risk Level:** Medium (touching core pipeline logic)

---

## TASK-005: Pydantic Schemas for Core Data Structures

### 5.1 Problem Statement

Currently, data flows through the pipeline as ad-hoc dictionaries and DataFrames without formal type contracts:

```python
# Current: No type safety
aggregated_exposures[isin] = {
    'name': row['name'],
    'direct': row['market_value'],
    'indirect': 0.0,
    'sector': 'Direct Holding',
    'geography': 'Global'
}
```

**Issues:**
- No IDE autocomplete or type checking
- Runtime errors from typos (e.g., `'diect'` vs `'direct'`)
- Pandera only validates DataFrames, not intermediate dicts
- Hard to understand data shape at a glance

### 5.2 Proposed Schema Architecture

```
src/utils/schemas.py (Current: Pandera only)
       │
       ▼
src/models/           (NEW: Pydantic models)
├── __init__.py
├── portfolio.py      # Position, ETFPosition, DirectHolding
├── holdings.py       # ETFHolding, EnrichedHolding
├── exposure.py       # ExposureRecord, AggregatedExposure
└── reports.py        # TrueExposureReport, SectorExposure
```

### 5.3 Schema Definitions

#### 5.3.1 Portfolio Models (`src/models/portfolio.py`)

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal

class Position(BaseModel):
    """Base position loaded from state manager."""
    isin: str = Field(..., min_length=12, max_length=12)
    name: str
    quantity: float = Field(..., ge=0)
    asset_type: Literal["Stock", "ETF"]
    ticker_src: Optional[str] = None  # Yahoo ticker
    provider: Optional[str] = None
    current_price: Optional[float] = None
    market_value: float = Field(default=0.0, ge=0)

    @field_validator('isin')
    @classmethod
    def validate_isin(cls, v: str) -> str:
        # Basic ISIN format check (2 letters + 10 alphanumeric)
        if not v[:2].isalpha() or not v[2:].isalnum():
            raise ValueError(f"Invalid ISIN format: {v}")
        return v.upper()

class DirectPosition(Position):
    """Stock position (direct holding)."""
    asset_type: Literal["Stock"] = "Stock"

class ETFPosition(Position):
    """ETF position (to be decomposed)."""
    asset_type: Literal["ETF"] = "ETF"
```

#### 5.3.2 Holdings Models (`src/models/holdings.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, Literal

class ETFHolding(BaseModel):
    """Single holding within an ETF (from adapter)."""
    name: str
    ticker: Optional[str] = None
    raw_ticker: Optional[str] = None  # Preserved from provider
    weight_percentage: float = Field(..., ge=0, le=100)
    isin: Optional[str] = None
    location: Optional[str] = None
    exchange: Optional[str] = None

class ClassifiedHolding(ETFHolding):
    """Holding with asset classification applied."""
    asset_class: Literal["Equity", "Cash", "Derivative"] = "Equity"

class EnrichedHolding(ClassifiedHolding):
    """Holding with ISIN resolution and metadata."""
    sector: str = "Unknown"
    geography: str = "Unknown"
    enrichment_tier: Literal["tier1", "tier2"] = "tier1"
```

#### 5.3.3 Exposure Models (`src/models/exposure.py`)

```python
from pydantic import BaseModel, Field, computed_field
from typing import Optional, Literal

class ExposureRecord(BaseModel):
    """Single security exposure (direct + indirect)."""
    isin: str
    name: str
    direct: float = Field(default=0.0, ge=0)
    indirect: float = Field(default=0.0, ge=0)
    asset_class: Literal["Equity", "Cash", "Derivative"] = "Equity"
    sector: Optional[str] = None
    geography: Optional[str] = None

    @computed_field
    @property
    def total_exposure(self) -> float:
        return self.direct + self.indirect

class AggregatedExposure(BaseModel):
    """Complete aggregated exposure with portfolio percentage."""
    records: list[ExposureRecord]
    total_portfolio_value: float = Field(..., ge=0)

    def get_record(self, isin: str) -> Optional[ExposureRecord]:
        for r in self.records:
            if r.isin == isin:
                return r
        return None

    def to_dataframe(self) -> "pd.DataFrame":
        import pandas as pd
        data = [r.model_dump() for r in self.records]
        df = pd.DataFrame(data)
        if self.total_portfolio_value > 0:
            df['portfolio_percentage'] = (df['total_exposure'] / self.total_portfolio_value) * 100
        else:
            df['portfolio_percentage'] = 0.0
        return df
```

### 5.4 Migration Strategy

**Phase 1: Add Models (Non-Breaking)**
1. Create `src/models/` directory with all schema files
2. Add `from src.models import *` to relevant modules
3. No changes to existing logic

**Phase 2: Gradual Adoption**
1. Update `state_manager.py` to return `list[Position]`
2. Update `aggregation.py` to use `ExposureRecord` internally
3. Update `reporting.py` to consume `AggregatedExposure`

**Phase 3: Validation at Boundaries**
1. Add `@validate_call` decorators to critical functions
2. Convert adapter outputs to Pydantic models before processing

### 5.5 Files to Modify

| File | Change |
|------|--------|
| `src/models/__init__.py` | NEW: Export all models |
| `src/models/portfolio.py` | NEW: Position models |
| `src/models/holdings.py` | NEW: Holding models |
| `src/models/exposure.py` | NEW: Exposure models |
| `src/data/state_manager.py` | Return typed positions |
| `src/core/aggregation.py` | Use ExposureRecord internally |
| `requirements.txt` | Ensure `pydantic>=2.0` |

---

## TASK-006: Aggregation Module Refactor

### 6.1 Problem Statement

`run_aggregation()` is a 300-line monolithic function doing 7 distinct operations:

```
Line 16-49:   Process Direct Holdings
Line 51-201:  Process ETF Holdings (contains nested loops)
  - Classification (73-79)
  - Tiered Enrichment (86-176)
  - Value Calculation (185-192)
Line 206-261: Aggregate by ISIN/Fallback
Line 262-298: Finalize and Save
```

**Issues:**
- Single function = untestable units
- Deeply nested loops = hard to debug
- Mixed concerns (I/O + logic)
- No separation of "process ETF" vs "aggregate results"

### 6.2 Proposed Module Structure

```
src/core/aggregation/
├── __init__.py           # Public API: run_aggregation()
├── direct.py             # process_direct_holdings()
├── indirect.py           # process_etf_holdings()
├── classification.py     # classify_holdings()
├── enrichment.py         # tier_and_enrich_holdings()
├── grouping.py           # aggregate_by_identifier()
└── output.py             # format_and_save_report()
```

### 6.3 Function Decomposition

#### 6.3.1 `direct.py` - Process Direct Holdings

```python
from typing import Dict
from src.models.exposure import ExposureRecord

def process_direct_holdings(
    direct_positions: list[Position]
) -> Dict[str, ExposureRecord]:
    """
    Convert direct stock positions to exposure records.
    
    Args:
        direct_positions: List of direct stock holdings
        
    Returns:
        Dict mapping ISIN -> ExposureRecord with direct value set
    """
    exposures = {}
    for pos in direct_positions:
        exposures[pos.isin] = ExposureRecord(
            isin=pos.isin,
            name=pos.name,
            direct=pos.market_value,
            indirect=0.0,
            asset_class="Equity"
        )
    return exposures
```

#### 6.3.2 `indirect.py` - Process ETF Holdings

```python
from typing import Dict, Tuple
import pandas as pd
from src.models.holdings import ClassifiedHolding

def process_single_etf(
    etf_isin: str,
    etf_market_value: float,
    holdings_df: pd.DataFrame
) -> Tuple[list[ClassifiedHolding], dict]:
    """
    Process a single ETF's holdings through classification and enrichment.
    
    Returns:
        Tuple of (enriched_holdings, stats_dict)
    """
    # 1. Classification
    classified = classify_holdings(holdings_df)
    
    # 2. Tiered Enrichment (Equity only)
    enriched = tier_and_enrich(classified)
    
    # 3. Calculate indirect values
    for h in enriched:
        h.indirect_value = (h.weight_percentage / 100) * etf_market_value
    
    return enriched, {"count": len(enriched)}
```

#### 6.3.3 `classification.py` - Holding Classification

```python
from src.utils.classification import classify_holding
from src.models.holdings import ETFHolding, ClassifiedHolding

def classify_holdings(holdings: list[ETFHolding]) -> list[ClassifiedHolding]:
    """
    Apply asset class classification (Equity/Cash/Derivative) to holdings.
    """
    classified = []
    for h in holdings:
        asset_class = classify_holding(h.ticker or "", h.name)
        classified.append(ClassifiedHolding(
            **h.model_dump(),
            asset_class=asset_class
        ))
    return classified
```

#### 6.3.4 `enrichment.py` - Tiered Enrichment

```python
from typing import Tuple
from src.models.holdings import ClassifiedHolding, EnrichedHolding

ENRICHMENT_THRESHOLD = 1.0  # Only enrich if weight > 1%

def tier_and_enrich(
    holdings: list[ClassifiedHolding]
) -> Tuple[list[EnrichedHolding], dict]:
    """
    Split holdings into Tier 1 (>1%) and Tier 2 (≤1%).
    Enrich only Tier 1 with ISIN resolution.
    
    Returns:
        Tuple of (all_enriched_holdings, tier_stats)
    """
    equity_holdings = [h for h in holdings if h.asset_class == "Equity"]
    
    tier1 = [h for h in equity_holdings if h.weight_percentage > ENRICHMENT_THRESHOLD]
    tier2 = [h for h in equity_holdings if h.weight_percentage <= ENRICHMENT_THRESHOLD]
    
    # Enrich Tier 1
    enriched_tier1 = enrich_tier1_holdings(tier1)
    
    # Fallback for Tier 2
    enriched_tier2 = [
        EnrichedHolding(**h.model_dump(), isin="N/A", enrichment_tier="tier2")
        for h in tier2
    ]
    
    stats = {
        "tier1_count": len(tier1),
        "tier2_count": len(tier2),
        "tier1_weight": sum(h.weight_percentage for h in tier1),
        "tier2_weight": sum(h.weight_percentage for h in tier2)
    }
    
    return enriched_tier1 + enriched_tier2, stats
```

#### 6.3.5 `grouping.py` - Aggregation Logic

```python
from typing import Dict
from src.models.exposure import ExposureRecord

def aggregate_by_identifier(
    direct_exposures: Dict[str, ExposureRecord],
    indirect_holdings: list[EnrichedHolding]
) -> Dict[str, ExposureRecord]:
    """
    Merge direct and indirect exposures, grouping by ISIN or fallback key.
    """
    result = dict(direct_exposures)  # Start with direct
    
    for h in indirect_holdings:
        key = generate_group_id(h)
        
        if key in result:
            result[key].indirect += h.indirect_value
        else:
            result[key] = ExposureRecord(
                isin=h.isin or "N/A",
                name=h.name,
                direct=0.0,
                indirect=h.indirect_value,
                asset_class=h.asset_class
            )
    
    return result

def generate_group_id(holding: EnrichedHolding) -> str:
    """Generate unique grouping key (ISIN or fallback)."""
    isin = holding.isin
    if isin and isin not in ('N/A', 'nan', None) and not isin.startswith('UNKNOWN'):
        return isin
    return f"FALLBACK|{holding.ticker}|{holding.name}"
```

#### 6.3.6 `__init__.py` - Public API

```python
from typing import Dict
import pandas as pd
from src.models.portfolio import Position
from src.models.exposure import AggregatedExposure

from .direct import process_direct_holdings
from .indirect import process_single_etf
from .grouping import aggregate_by_identifier
from .output import save_exposure_report

def run_aggregation(
    direct_positions: pd.DataFrame,
    etf_positions: pd.DataFrame,
    etf_holdings_map: Dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """
    Main aggregation entry point (backward-compatible signature).
    
    Orchestrates:
    1. Direct holdings processing
    2. ETF decomposition and enrichment
    3. Aggregation by identifier
    4. Report generation
    """
    # 1. Process Direct
    direct_exposures = process_direct_holdings(
        direct_positions.to_dict('records')
    )
    
    # 2. Process Each ETF
    all_indirect = []
    for _, etf in etf_positions.iterrows():
        holdings_df = etf_holdings_map.get(etf['isin'])
        if holdings_df is None or holdings_df.empty:
            continue
        enriched, _ = process_single_etf(
            etf['isin'], etf['market_value'], holdings_df
        )
        all_indirect.extend(enriched)
    
    # 3. Aggregate
    final_exposures = aggregate_by_identifier(direct_exposures, all_indirect)
    
    # 4. Output
    result = AggregatedExposure(
        records=list(final_exposures.values()),
        total_portfolio_value=sum(r.total_exposure for r in final_exposures.values())
    )
    
    return save_exposure_report(result)
```

### 6.4 Testing Strategy

Each module gets its own test file:

```
tests/
├── test_aggregation/
│   ├── test_direct.py        # Unit tests for direct processing
│   ├── test_classification.py # Unit tests for classification
│   ├── test_enrichment.py    # Unit tests for tiered enrichment
│   ├── test_grouping.py      # Unit tests for aggregation logic
│   └── test_integration.py   # End-to-end pipeline test
```

---

## Integration Tests

### 7.1 Test Fixtures

Create comprehensive test fixtures in `tests/fixtures/`:

```
tests/fixtures/
├── portfolio/
│   ├── asset_universe_test.csv    # 10 assets (5 stocks, 5 ETFs)
│   └── portfolio_holdings_test.csv # Matching holdings
├── adapters/
│   ├── ishares_msci_world.csv     # Real iShares output sample
│   └── vaneck_defense.xlsx        # Real VanEck output sample
└── expected/
    └── true_exposure_expected.csv  # Expected pipeline output
```

### 7.2 Integration Test Implementation

```python
# tests/test_integration.py
import pytest
import pandas as pd
from pathlib import Path

from scripts.run_pipeline import run_pipeline

FIXTURES = Path(__file__).parent / "fixtures"

class TestPipelineIntegration:
    """End-to-end pipeline tests with fixture data."""
    
    @pytest.fixture
    def setup_test_environment(self, tmp_path, monkeypatch):
        """Configure pipeline to use test fixtures."""
        # Copy fixtures to temp location
        # Monkeypatch config paths
        pass
    
    def test_pipeline_produces_valid_output(self, setup_test_environment):
        """Verify pipeline runs without errors."""
        run_pipeline()
        
        output = pd.read_csv("outputs/true_exposure_report.csv")
        assert not output.empty
        assert "total_exposure" in output.columns
    
    def test_value_conservation(self, setup_test_environment):
        """Verify total value is preserved (±2%)."""
        # Load input holdings
        holdings = pd.read_csv(FIXTURES / "portfolio/portfolio_holdings_test.csv")
        
        # Run pipeline
        run_pipeline()
        
        # Check output
        output = pd.read_csv("outputs/true_exposure_report.csv")
        
        # Assert within tolerance
        input_total = holdings['Quantity'].sum() * 100  # Simplified
        output_total = output['total_exposure'].sum()
        
        assert abs(input_total - output_total) / input_total < 0.02
    
    def test_direct_holdings_preserved(self, setup_test_environment):
        """Verify direct holdings appear in output."""
        run_pipeline()
        
        output = pd.read_csv("outputs/true_exposure_report.csv")
        
        # NVDA should be in output (direct holding)
        nvda = output[output['isin'] == 'US67066G1040']
        assert not nvda.empty
        assert nvda['direct'].iloc[0] > 0
    
    def test_etf_decomposition_works(self, setup_test_environment):
        """Verify ETFs are decomposed into constituents."""
        run_pipeline()
        
        output = pd.read_csv("outputs/true_exposure_report.csv")
        
        # Apple should appear as indirect (via MSCI World ETF)
        aapl = output[output['isin'] == 'US0378331005']
        assert not aapl.empty
        assert aapl['indirect'].iloc[0] > 0
```

### 7.3 Test Data Generation

Create a script to generate test fixtures:

```python
# scripts/generate_test_fixtures.py
"""Generate minimal test fixtures for integration tests."""

import pandas as pd
from pathlib import Path

FIXTURES = Path("tests/fixtures")

def generate_asset_universe():
    """Create minimal asset universe."""
    data = [
        # Stocks
        ("US67066G1040", "NVDA", "NVDA", "Nvidia", "", "Stock"),
        ("US0378331005", "AAPL", "AAPL", "Apple Inc", "", "Stock"),
        ("US5949181045", "MSFT", "MSFT", "Microsoft", "", "Stock"),
        # ETFs
        ("IE00B4L5Y983", "IWDA", "IWDA.AS", "iShares Core MSCI World ETF", "iShares", "ETF"),
        ("IE00B5BMR087", "CSPX", "SXR8.DE", "iShares Core S&P 500 ETF", "iShares", "ETF"),
    ]
    df = pd.DataFrame(data, columns=["ISIN", "TR_Ticker", "Yahoo_Ticker", "Name", "Provider", "Asset_Class"])
    df.to_csv(FIXTURES / "portfolio/asset_universe_test.csv", index=False)

def generate_portfolio_holdings():
    """Create test portfolio."""
    data = [
        ("US67066G1040", 10),   # 10 shares NVDA
        ("IE00B4L5Y983", 50),   # 50 shares MSCI World
        ("IE00B5BMR087", 25),   # 25 shares S&P 500
    ]
    df = pd.DataFrame(data, columns=["ISIN", "Quantity"])
    df.to_csv(FIXTURES / "portfolio/portfolio_holdings_test.csv", index=False)

if __name__ == "__main__":
    FIXTURES.mkdir(parents=True, exist_ok=True)
    (FIXTURES / "portfolio").mkdir(exist_ok=True)
    generate_asset_universe()
    generate_portfolio_holdings()
    print("Test fixtures generated.")
```

---

## Implementation Order

```
Week 1: Foundation
├── Day 1: TASK-005 Phase 1 (Create Pydantic models)
├── Day 2: TASK-005 Phase 2 (Integrate into state_manager)
└── Day 3: Create test fixtures

Week 2: Refactor
├── Day 4: TASK-006 (Extract direct.py, classification.py)
├── Day 5: TASK-006 (Extract enrichment.py, grouping.py)
└── Day 6: TASK-006 (Refactor run_aggregation, update __init__.py)

Week 3: Testing
├── Day 7: Unit tests for each module
├── Day 8: Integration tests
└── Day 9: Verification & documentation
```

---

## Risk Mitigation

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Breaking existing pipeline | Medium | Keep backward-compatible signatures, incremental changes |
| Performance regression | Low | Profile before/after, Pydantic v2 is fast |
| Test flakiness | Medium | Use deterministic fixtures, mock external APIs |
| Scope creep | Medium | Strict phase boundaries, don't refactor reporting.py yet |

---

## Success Criteria

1. **TASK-005 Complete:**
   - [ ] All core data structures have Pydantic models
   - [ ] Type checker shows no new errors
   - [ ] IDE autocomplete works for Position, ExposureRecord

2. **TASK-006 Complete:**
   - [ ] `run_aggregation()` is <50 lines
   - [ ] Each submodule has unit tests
   - [ ] Existing `test_aggregation.py` still passes

3. **Integration Tests Complete:**
   - [ ] `test_pipeline_integration.py` exists with 4+ tests
   - [ ] Tests run in <30 seconds
   - [ ] CI-friendly (no external API calls)

---

## Next Steps

1. **Confirm Plan:** Review this document for any concerns
2. **Execute TASK-005:** Create `src/models/` with Pydantic schemas
3. **Execute TASK-006:** Refactor aggregation into submodules
4. **Add Integration Tests:** Create fixture-based end-to-end tests
5. **Update Documentation:** Mark tasks complete in `tasks.md`

---

*Plan created: 2025-11-28*
*Author: AI Agent (Phase 2 Planning)*
