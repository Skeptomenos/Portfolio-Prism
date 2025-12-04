# Trade Republic API Refactor Plan

> **Created:** 2024-12-04  
> **Status:** Backlog (Future Work)  
> **Priority:** Medium (Post-MVP)

## Executive Summary

This document captures the analysis and future refactoring plan for how we interact with Trade Republic's API. The goal is to eventually have **full control over data acquisition and calculation**, removing dependency on pytr's internal transformations.

**Current Decision:** Stick with pytr + Yahoo Finance for MVP. Revisit after core features are stable.

---

## Part 1: Current Architecture

### Data Flow (As-Is)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Trade Republic │────▶│      pytr       │────▶│  Our Pipeline   │
│       API       │     │ (fetch+calculate)│     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌─────────────────┐             │
                        │  Yahoo Finance  │◀────────────┘
                        │ (prices, history)│
                        └─────────────────┘
```

### What pytr Does Internally

| Step | pytr Action | Data Retrieved |
|------|-------------|----------------|
| 1 | `compact_portfolio()` | ISIN, quantity, avgCost (averageBuyIn) |
| 2 | `instrument_details()` | Security name, exchange IDs |
| 3 | `ticker()` | Real-time price from TR |
| 4 | **Calculates** | `netValue = price × quantity` |

**Problem:** pytr bundles fetch + calculation. We get `netValue` but not the raw `price`.

### pytr CSV Output Format (v0.4.2)

```
Name;ISIN;quantity;avgCost;netValue
NVIDIA;US67066G1040;10.376354;120.50;1607.25
```

- 5 columns, semicolon-separated
- `netValue` is calculated by pytr, not raw from TR
- Current price can be derived: `price = netValue / quantity`

---

## Part 2: Problem Analysis

### Why This Matters

| Issue | Impact |
|-------|--------|
| No control over price source | Can't choose TR vs Yahoo |
| Calculation opacity | Can't audit how values are derived |
| Format dependency | pytr format changes break our parser |
| Vendor lock-in | Tied to pytr's implementation decisions |

### First Principles Analysis

**Core Entities:**
- **Position**: ISIN, quantity, avgCost (can ONLY come from TR)
- **Price**: current market price (can come from TR ticker OR Yahoo)
- **Value**: calculated (price × quantity) - should be OUR calculation

**Invariants:**
1. Position data (quantity, avgCost) can ONLY come from Trade Republic
2. Look-through holdings can ONLY come from ETF providers (iShares, Amundi)
3. All calculations should be explicit and auditable in our code

**Trade-offs:**

| Dimension | TR Ticker | Yahoo Finance |
|-----------|-----------|---------------|
| Freshness | Real-time | 15-20 min delayed |
| Accuracy to TR app | Exact match | Close approximation |
| Historical data | None | Full history |
| Availability | Requires TR auth | Public API |
| Rate limits | Unknown | Known (2000/hr) |

---

## Part 3: Future Architecture (Target State)

### Data Flow (To-Be)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Trade Republic │────▶│   TR Client     │────▶│  Our Pipeline   │
│       API       │     │  (thin wrapper) │     │ (all calculation)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │ Real-time prices                              │
        └──────────────────────────────────────────────▶│
                                                        │
                        ┌─────────────────┐             │
                        │  Yahoo Finance  │◀────────────┘
                        │ (history only)  │     (fallback/history)
                        └─────────────────┘
```

### Proposed TR Client Interface

```python
class TRClient:
    """Thin wrapper around pytr for raw data access."""
    
    def get_positions(self) -> list[Position]:
        """
        Returns raw position data from TR.
        
        Returns:
            list of Position(isin, quantity, avg_cost)
        """
        pass
    
    def get_current_price(self, isin: str) -> Price:
        """
        Returns real-time price from TR ticker.
        
        Returns:
            Price(value, currency, timestamp, source="TR")
        """
        pass
    
    def get_price_history(self, isin: str, range: str) -> list[Price]:
        """
        Returns historical prices from TR.
        
        Note: TR has performance_history() but unclear coverage.
        May still need Yahoo as fallback.
        """
        pass
```

### Calculation Layer (Our Code)

```python
# All calculations explicit and auditable
def calculate_position_value(quantity: float, price: float) -> float:
    return quantity * price

def calculate_unrealized_pl(current_value: float, cost_basis: float) -> float:
    return current_value - cost_basis

def calculate_pl_percentage(current_value: float, cost_basis: float) -> float:
    if cost_basis == 0:
        return 0.0
    return ((current_value / cost_basis) - 1) * 100
```

---

## Part 4: Implementation Options

### Option A: Minimal Fix (Current Choice)

**Description:** Fix parser to handle pytr's 5-column format correctly.

| Aspect | Details |
|--------|---------|
| Effort | 1 hour |
| Risk | Low |
| Control | Limited (still uses pytr's netValue) |
| When | Now |

**Implementation:**
- Change `len(parts) >= 6` to `len(parts) >= 5`
- Derive `current_price = netValue / quantity`
- Keep Yahoo for ETF look-through and fallback

### Option B: Raw Data Wrapper

**Description:** Create thin wrapper around pytr to get raw data only.

| Aspect | Details |
|--------|---------|
| Effort | 3-4 hours |
| Risk | Medium |
| Control | Full |
| When | Post-MVP |

**Implementation:**
- Use pytr's `compact_portfolio()` for positions
- Use pytr's `ticker()` for real-time prices
- All calculations in our code

### Option C: Hybrid Price Sources

**Description:** Configurable price source (TR ticker OR Yahoo).

| Aspect | Details |
|--------|---------|
| Effort | 6-8 hours |
| Risk | Medium |
| Control | Maximum |
| When | Post-MVP |

**Implementation:**
- Everything from Option B
- Add configuration for price source
- Use TR for P/L, Yahoo for historical

### Option D: Custom TR Client (No pytr)

**Description:** Build our own TR API client.

| Aspect | Details |
|--------|---------|
| Effort | 20+ hours |
| Risk | High |
| Control | Complete |
| When | Only if pytr becomes unmaintained |

**Implementation:**
- Implement TR authentication (2FA, websocket)
- Handle cookie management
- Replicate pytr's API calls

**Not recommended** unless pytr is abandoned.

---

## Part 5: Decision

### Current Decision (2024-12-04)

**Chosen Option:** A (Minimal Fix)

**Rationale:**
1. MVP focus - don't add complexity before core features work
2. Yahoo prices are "exact enough" for portfolio analysis
3. pytr handles complex TR authentication well
4. Can revisit after MVP when architecture is stable

**Accepted Trade-offs:**
- Dashboard P/L may differ slightly from TR app (15-20 min delay)
- Less control over data transformations
- Dependency on pytr's format

### Future Trigger for Revisiting

Revisit this decision when:
- [ ] MVP is complete and stable
- [ ] Users report P/L accuracy issues
- [ ] pytr changes format or becomes unmaintained
- [ ] We need real-time price updates in dashboard

---

## Part 6: Technical Notes

### pytr API Reference (Relevant Methods)

```python
# From pytr/api.py

async def compact_portfolio(self):
    """Returns positions with ISIN, quantity, avgCost."""
    return await self.subscribe({"type": "compactPortfolio"})

async def ticker(self, isin, exchange="LSX"):
    """Returns real-time price for ISIN."""
    return await self.subscribe({"type": "ticker", "id": f"{isin}.{exchange}"})

async def performance_history(self, isin, timeframe, exchange="LSX"):
    """Returns historical prices (potential Yahoo replacement)."""
    return await self.subscribe({
        "type": "aggregateHistory",
        "id": f"{isin}.{exchange}",
        "range": timeframe,
    })
```

### TR API Response Structures

**compactPortfolio response:**
```json
{
  "positions": [
    {
      "instrumentId": "US67066G1040",
      "netSize": 10.376354,
      "averageBuyIn": 120.50
    }
  ]
}
```

**ticker response:**
```json
{
  "last": {
    "price": 154.81,
    "time": "2024-12-04T10:30:00Z"
  }
}
```

---

## Appendix: Assumption Validation

### Assumptions Challenged

| Assumption | Challenge | Verdict |
|------------|-----------|---------|
| "Can't get rid of Yahoo" | TR has `performance_history()` | Partially true - need Yahoo for now |
| "Yahoo is exact enough" | 15-20 min delay during market hours | True for directional accuracy |
| "Don't add complexity now" | Cost of fixing later vs now | True if we document clearly |
| "Stick with pytr until MVP" | Dependency risks | Acceptable - pytr handles auth well |

### Yahoo Finance Dependency Analysis

| Use Case | Yahoo Required? | Future Alternative |
|----------|-----------------|-------------------|
| Historical prices | Yes | TR `performance_history()` (untested) |
| PDF fallback pricing | Yes | TR ticker (if authenticated) |
| ETF look-through | No | We use iShares/Amundi directly |
| Fallback when TR fails | Yes | Keep as safety net |

**Conclusion:** Yahoo cannot be fully eliminated yet, but its role can be reduced to historical data and fallback only.

---

## References

- pytr source: `venv/lib/python3.9/site-packages/pytr/`
- Current fetch script: `scripts/fetch_tr_api.py`
- Pipeline entry: `scripts/run_pipeline.py`
