# src/adapters/vanguard.py
"""
Vanguard ETF Adapter

Fetches holdings data from Vanguard's German investor website.
Uses Playwright for scraping as Vanguard uses client-side rendering.

Supports manual file fallback similar to other adapters.
"""

import os
import sys
import json
import re
import pandas as pd
from typing import Optional, List, Dict, Any

from src.data.caching import cache_adapter_data
from src.utils.logging_config import get_logger
from src.config import MANUAL_INPUTS_DIR, RAW_DOWNLOADS_DIR

logger = get_logger(__name__)

# Known Vanguard ETF product IDs
# Format: ISIN -> (product_id, product_slug)
VANGUARD_PRODUCTS = {
    "IE00BK5BQT80": ("9679", "ftse-all-world-ucits-etf-usd-accumulating"),
}


class VanguardAdapter:
    """
    Adapter for fetching ETF holdings data from Vanguard.

    Strategy:
    1. Try manual file first (CSV/XLSX in manual_inputs directory)
    2. Try BeautifulSoup for quick scraping (gets top 10 holdings)
    3. Fallback to Playwright for full holdings with network interception
    """

    def __init__(self, isin: Optional[str] = None):
        """
        Initialize the adapter.

        Args:
            isin: Optional ISIN for validation. If provided, checks if supported.
        """
        self.isin = isin
        if isin and isin not in VANGUARD_PRODUCTS:
            logger.warning(
                f"ISIN {isin} not in known Vanguard products. "
                "Will attempt auto-discovery."
            )

    @cache_adapter_data(ttl_hours=24)
    def fetch_holdings(self, isin: str) -> pd.DataFrame:
        """
        Fetches holdings for a given Vanguard ETF ISIN.

        Args:
            isin: The ISIN of the ETF.

        Returns:
            A pandas DataFrame containing the ETF holdings,
            or an empty DataFrame if fetching fails.
        """
        logger.info(f"--- Running Vanguard holdings acquisition for {isin} ---")

        # 1. Try Manual File first
        df = self._fetch_from_manual_file(isin)
        if df is not None:
            return df

        # 2. Try Playwright with network interception for full holdings
        logger.info("  - No manual file found. Trying Playwright scraping...")
        df = self._fetch_via_playwright(isin)
        if df is not None and not df.empty:
            return df

        # 3. Fallback to BeautifulSoup (lightweight, gets top holdings only)
        logger.info("  - Playwright failed. Falling back to BeautifulSoup...")
        df = self._fetch_via_beautifulsoup(isin)
        if df is not None and not df.empty:
            return df

        return pd.DataFrame()

    def _fetch_via_playwright(self, isin: str) -> Optional[pd.DataFrame]:
        """
        Uses Playwright to scrape full holdings from Vanguard.

        Intercepts network requests to find any hidden API endpoints
        and extracts all holdings from the rendered page.
        """
        try:
            from src.utils.browser import (
                BrowserContext,
                handle_cookie_consent,
                save_debug_screenshot,
                PlaywrightNotInstalledError,
            )
        except ImportError as e:
            logger.error(f"Failed to import browser utilities: {e}")
            return None

        product_info = VANGUARD_PRODUCTS.get(isin)
        if not product_info:
            logger.error(f"ISIN {isin} not found in known Vanguard products.")
            return None

        product_id, product_slug = product_info
        target_url = f"https://www.de.vanguard/professionell/anlageprodukte/etf/aktien/{product_id}/{product_slug}"

        captured_apis: List[Dict[str, Any]] = []

        try:
            with BrowserContext(headless=True, timeout=60000) as ctx:
                page = ctx.new_page()

                # Set up network interception to capture API calls
                def capture_response(response):
                    url = response.url
                    content_type = response.headers.get("content-type", "")

                    # Look for JSON APIs that might contain holdings data
                    if "json" in content_type or "api" in url.lower():
                        try:
                            if response.ok:
                                body = response.text()
                                if (
                                    "holding" in body.lower()
                                    or "portfolio" in body.lower()
                                ):
                                    captured_apis.append(
                                        {"url": url, "body": body[:5000]}
                                    )
                        except Exception:
                            pass

                page.on("response", capture_response)

                # Navigate to page
                logger.info(f"1. Navigating to: {target_url}")
                page.goto(target_url)
                page.wait_for_load_state("networkidle")

                # Handle cookie consent
                logger.info("2. Handling cookie consent...")
                handle_cookie_consent(page)
                page.wait_for_timeout(2000)

                # Scroll to load any lazy content
                logger.info("3. Scrolling to load all content...")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(2000)

                # Check if we captured any API data
                if captured_apis:
                    logger.info(f"   Found {len(captured_apis)} potential API calls")
                    for api in captured_apis:
                        df = self._parse_api_response(api["body"])
                        if df is not None and not df.empty:
                            logger.info(f"   Extracted {len(df)} holdings from API")
                            return df

                # Extract from rendered page
                logger.info("4. Extracting holdings from rendered page...")
                holdings_df = self._extract_holdings_from_playwright(page)

                if holdings_df.empty:
                    logger.warning("   - Could not extract holdings from page.")
                    save_debug_screenshot(page, f"vanguard_{isin}_debug")

                return holdings_df

        except PlaywrightNotInstalledError as e:
            logger.error(str(e))
            return None
        except Exception as e:
            logger.error(f"Playwright scraping failed: {e}")
            return None

    def _extract_holdings_from_playwright(self, page) -> pd.DataFrame:
        """Extracts holdings data from the Playwright page."""
        try:
            # Find all tables on the page
            tables = page.locator("table").all()
            logger.info(f"   - Found {len(tables)} tables on page")

            for i, table in enumerate(tables):
                try:
                    # Get table headers
                    headers = table.locator("th").all()
                    header_texts = [h.text_content().strip() for h in headers]

                    # Look for holdings table
                    header_str = " ".join(header_texts).lower()
                    if "wertpapiere" in header_str or "% der assets" in header_str:
                        logger.info(f"   - Found holdings table (table {i})")
                        return self._parse_playwright_table(table)

                except Exception as e:
                    logger.debug(f"   - Table {i} parsing error: {e}")
                    continue

            logger.warning("   - No holdings table found")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"   - Failed to extract holdings: {e}")
            return pd.DataFrame()

    def _parse_playwright_table(self, table) -> pd.DataFrame:
        """Parses a Playwright table locator into a DataFrame."""
        try:
            rows = table.locator("tr").all()
            data = []

            # Get headers from first row
            if rows:
                header_cells = rows[0].locator("th").all()
                if not header_cells:
                    header_cells = rows[0].locator("td").all()
                headers = [cell.text_content().strip() for cell in header_cells]
            else:
                headers = []

            # Parse data rows
            for row in rows[1:]:
                cells = row.locator("td").all()
                if len(cells) >= 2:
                    row_data = [cell.text_content().strip() for cell in cells]
                    data.append(row_data)

            if not data:
                return pd.DataFrame()

            # Create DataFrame
            df = pd.DataFrame(data)
            if headers and len(headers) >= len(df.columns):
                df.columns = headers[: len(df.columns)]

            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()

            col_map = {
                "wertpapiere": "name",
                "securities": "name",
                "% der assets": "weight_percentage",
                "% of assets": "weight_percentage",
                "sektor": "sector",
                "sector": "sector",
                "region": "location",
                "marktwert": "market_value",
                "anteile": "shares",
            }
            df = df.rename(columns=col_map)

            # Clean weight column
            if "weight_percentage" in df.columns:
                df["weight_percentage"] = (
                    df["weight_percentage"]
                    .astype(str)
                    .str.replace("%", "")
                    .str.replace(",", ".")
                    .str.replace("\xa0", "")
                    .str.strip()
                )
                df["weight_percentage"] = pd.to_numeric(
                    df["weight_percentage"], errors="coerce"
                )

            # Filter valid rows
            if "name" in df.columns and "weight_percentage" in df.columns:
                df = pd.DataFrame(df.dropna(subset=["name", "weight_percentage"]))
                df = pd.DataFrame(df[df["weight_percentage"] > 0])

            # Ensure required columns
            for col in ["ticker", "isin", "sector", "location"]:
                if col not in df.columns:
                    df[col] = None

            logger.info(f"   - Parsed {len(df)} holdings from table")
            return pd.DataFrame(df)

        except Exception as e:
            logger.error(f"   - Table parsing error: {e}")
            return pd.DataFrame()

    def _parse_api_response(self, body: str) -> Optional[pd.DataFrame]:
        """Attempts to parse holdings from an API response body."""
        try:
            data = json.loads(body)

            # Look for holdings array in various locations
            holdings = None
            if isinstance(data, list):
                holdings = data
            elif isinstance(data, dict):
                for key in ["holdings", "positions", "constituents", "data"]:
                    if key in data and isinstance(data[key], list):
                        holdings = data[key]
                        break

            if not holdings:
                return None

            df = pd.DataFrame(holdings)

            # Try to identify and rename columns
            col_map = {
                "securityName": "name",
                "name": "name",
                "weight": "weight_percentage",
                "percentage": "weight_percentage",
                "ticker": "ticker",
                "isin": "isin",
            }
            df = df.rename(columns=col_map)

            if "name" in df.columns and "weight_percentage" in df.columns:
                return df

            return None

        except Exception:
            return None

    def _fetch_via_beautifulsoup(self, isin: str) -> Optional[pd.DataFrame]:
        """
        Lightweight scraping using requests + BeautifulSoup.

        Note: This method only gets the top 10 holdings displayed on the page.
        For complete holdings, use Playwright or provide a manual file.
        """
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error(
                "BeautifulSoup not available. Install with: pip install beautifulsoup4"
            )
            return None

        product_info = VANGUARD_PRODUCTS.get(isin)
        if not product_info:
            logger.error(f"ISIN {isin} not found in known Vanguard products.")
            return None

        product_id, product_slug = product_info
        url = f"https://www.de.vanguard/professionell/anlageprodukte/etf/aktien/{product_id}/{product_slug}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        }

        try:
            logger.info(f"   Fetching page: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")
            tables = soup.find_all("table")

            if len(tables) < 3:
                logger.warning(f"   Expected 4 tables, found {len(tables)}")
                return None

            # Holdings table is typically the 3rd table (index 2)
            holdings_table = tables[2]
            rows = holdings_table.find_all("tr")

            if len(rows) < 2:
                logger.warning("   Holdings table has no data rows")
                return None

            # Parse header
            header_row = rows[0]
            headers_list = [
                th.get_text(strip=True) for th in header_row.find_all(["th", "td"])
            ]

            # Parse data rows
            data = []
            for row in rows[1:]:
                cells = row.find_all("td")
                if len(cells) >= 2:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    data.append(row_data)

            if not data:
                logger.warning("   No holdings data found in table")
                return None

            # Create DataFrame
            col_count = len(data[0]) if data else len(headers_list)
            df = pd.DataFrame(data)
            df.columns = headers_list[:col_count]

            # Rename columns to standard names
            col_map = {
                "Wertpapiere": "name",
                "% der Assets": "weight_percentage",
                "Sektor": "sector",
                "Region": "location",
            }
            df = df.rename(columns=col_map)

            # Clean weight column
            if "weight_percentage" in df.columns:
                df["weight_percentage"] = (
                    df["weight_percentage"]
                    .str.replace("%", "")
                    .str.replace(",", ".")
                    .str.replace("\xa0", "")
                    .str.strip()
                )
                df["weight_percentage"] = pd.to_numeric(
                    df["weight_percentage"], errors="coerce"
                )

            # Filter valid rows
            df = pd.DataFrame(df.dropna(subset=["name", "weight_percentage"]))
            df = pd.DataFrame(df[df["weight_percentage"] > 0])

            # Add missing columns
            for col in ["ticker", "isin"]:
                if col not in df.columns:
                    df[col] = None

            logger.info(
                f"   Successfully scraped {len(df)} holdings (top holdings only)"
            )
            logger.warning(
                "   Note: BeautifulSoup only gets top 10 holdings. "
                "For complete data, provide a manual CSV file."
            )

            return pd.DataFrame(df)

        except Exception as e:
            logger.error(f"   BeautifulSoup scraping failed: {e}")
            return None

    def _fetch_from_manual_file(self, isin: str) -> Optional[pd.DataFrame]:
        """Attempts to load and parse a manually placed file."""
        manual_dir = MANUAL_INPUTS_DIR
        xlsx_path = os.path.join(manual_dir, f"{isin}.xlsx")
        csv_path = os.path.join(manual_dir, f"{isin}.csv")

        df = None

        # A. Try CSV
        if os.path.exists(csv_path):
            logger.info(f"  - Found manual file: {csv_path}")
            df = self._read_manual_csv(csv_path)

        # B. Try XLSX
        if df is None and os.path.exists(xlsx_path):
            logger.info(f"  - Found manual file: {xlsx_path}")
            df = self._read_manual_xlsx(xlsx_path)

        # C. Process DataFrame
        if df is not None:
            return self._process_manual_dataframe(df)

        return None

    def _read_manual_csv(self, path: str) -> Optional[pd.DataFrame]:
        """Reads CSV with separator detection."""
        try:
            try:
                df = pd.read_csv(path, sep=";")
                if len(df.columns) < 2:
                    raise ValueError("Not enough columns with ';'")
                return df
            except (ValueError, pd.errors.ParserError):
                return pd.read_csv(path, sep=",")
        except Exception as e:
            logger.error(f"    - Failed to read manual CSV: {e}")
            return None

    def _read_manual_xlsx(self, path: str) -> Optional[pd.DataFrame]:
        """Reads XLSX with header hunting."""
        try:
            temp_df = pd.read_excel(path, header=None, nrows=30)

            header_row_idx: int = 0
            for idx in range(len(temp_df)):
                row = temp_df.iloc[idx]
                row_str = row.astype(str).str.lower().tolist()
                if any(
                    kw in row_str
                    for kw in ["wertpapiere", "securities", "name", "ticker"]
                ):
                    header_row_idx = idx
                    break

            logger.info(f"    - Detected header at row {header_row_idx}")
            return pd.read_excel(path, header=header_row_idx)

        except Exception as e:
            logger.error(f"    - Failed to read manual XLSX: {e}")
            return None

    def _process_manual_dataframe(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Cleans and normalizes the manually loaded dataframe."""
        df.columns = df.columns.str.strip().str.lower()

        col_map = {
            "wertpapiere": "name",
            "securities": "name",
            "name": "name",
            "ticker": "ticker",
            "% der assets": "weight_percentage",
            "% of assets": "weight_percentage",
            "weight": "weight_percentage",
            "gewichtung": "weight_percentage",
            "sektor": "sector",
            "sector": "sector",
            "region": "location",
            "land": "location",
            "country": "location",
            "isin": "isin",
        }
        df = df.rename(columns=col_map)

        if "name" not in df.columns or "weight_percentage" not in df.columns:
            logger.error(
                f"    - Manual file missing required columns. Found: {df.columns.tolist()}"
            )
            return None

        # Clean weight column
        if df["weight_percentage"].dtype == object:
            df["weight_percentage"] = (
                df["weight_percentage"]
                .astype(str)
                .str.replace("%", "")
                .str.replace(",", ".")
                .str.replace("\xa0", "")
                .str.strip()
            )

        df["weight_percentage"] = pd.to_numeric(
            df["weight_percentage"], errors="coerce"
        )

        # Drop invalid rows
        df = pd.DataFrame(df.dropna(subset=["name", "weight_percentage"]))
        df = pd.DataFrame(df[df["weight_percentage"] > 0])

        # Ensure required columns exist
        for col in ["ticker", "isin", "sector", "location"]:
            if col not in df.columns:
                df[col] = None

        logger.info(f"    - Successfully parsed manual file with {len(df)} rows.")
        return pd.DataFrame(
            df[["ticker", "isin", "name", "weight_percentage", "sector", "location"]]
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        test_isin = sys.argv[1]
    else:
        test_isin = "IE00BK5BQT80"

    adapter = VanguardAdapter()
    holdings = adapter.fetch_holdings(test_isin)

    if not holdings.empty:
        print(f"\n--- Successfully fetched {len(holdings)} holdings ---")
        print(holdings.head(10))
        print(f"\nTotal weight: {holdings['weight_percentage'].sum():.2f}%")
    else:
        print("\n--- Failed to fetch holdings ---")
