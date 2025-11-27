"""
ETF holdings models.

Defines the structure for holdings data returned by ETF adapters,
through classification and enrichment stages.
"""

from pydantic import BaseModel, Field, computed_field
from typing import Optional, Literal


class ETFHolding(BaseModel):
    """
    Single holding within an ETF (raw data from adapter).

    Represents one constituent of an ETF as returned by provider
    adapters (iShares, VanEck, etc.).

    Attributes:
        name: Security name from provider
        ticker: Ticker symbol (may be Yahoo-compatible or raw)
        raw_ticker: Original ticker from provider before transformation
        weight_percentage: Weight in ETF (0-100 scale)
        isin: ISIN if provided by adapter, else None
        location: Country/region from provider
        exchange: Exchange name from provider
    """

    name: str
    ticker: Optional[str] = None
    raw_ticker: Optional[str] = None
    weight_percentage: float = Field(..., ge=0.0, le=100.0)
    isin: Optional[str] = None
    location: Optional[str] = None
    exchange: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow extra fields from adapters


class ClassifiedHolding(ETFHolding):
    """
    Holding with asset classification applied.

    After classification, each holding is tagged as Equity, Cash,
    or Derivative based on ticker/name patterns.

    Attributes:
        asset_class: Classification result
    """

    asset_class: Literal["Equity", "Cash", "Derivative"] = "Equity"


class EnrichedHolding(ClassifiedHolding):
    """
    Holding with ISIN resolution and metadata.

    After enrichment, holdings have resolved ISINs and
    sector/geography metadata from external APIs.

    Attributes:
        sector: Industry sector (e.g., "Technology")
        geography: Country of domicile (e.g., "United States")
        enrichment_tier: Whether resolved via Tier 1 (>1%) or Tier 2 (fallback)
        indirect_value: Calculated EUR value (weight% * ETF market value)
    """

    sector: str = "Unknown"
    geography: str = "Unknown"
    enrichment_tier: Literal["tier1", "tier2"] = "tier1"
    indirect_value: float = Field(default=0.0, ge=0.0)

    @computed_field
    @property
    def group_id(self) -> str:
        """
        Generate unique grouping key for aggregation.

        Uses ISIN if available and valid, otherwise falls back
        to a composite key of ticker + name.

        Returns:
            Unique identifier for grouping this holding
        """
        isin = self.isin
        if (
            isin
            and isin not in ("N/A", "nan", None, "")
            and not isin.startswith("UNKNOWN")
            and not isin.startswith("NON_EQUITY")
        ):
            return isin

        # Fallback: Ticker + Name
        ticker = self.ticker or ""
        name = self.name or ""
        return f"FALLBACK|{ticker}|{name}"

    def calculate_indirect_value(self, etf_market_value: float) -> None:
        """
        Calculate the EUR value of this holding based on ETF value.

        Args:
            etf_market_value: Total market value of the parent ETF in EUR
        """
        self.indirect_value = (self.weight_percentage / 100.0) * etf_market_value
