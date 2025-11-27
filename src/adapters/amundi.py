import sys
import time
import os
import pandas as pd
from typing import Optional
from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    # Monkeypatch pandas to support 'calamine' engine if installed
    from python_calamine.pandas import pandas_monkeypatch

    pandas_monkeypatch()
    CALAMINE_AVAILABLE = True
except ImportError:
    CALAMINE_AVAILABLE = False

from src.utils.logging_config import get_logger
from src.config import MANUAL_INPUTS_DIR, RAW_DOWNLOADS_DIR

logger = get_logger(__name__)


class AmundiAdapter:
    def fetch_holdings(self, isin: str) -> pd.DataFrame:
        """
        Navigates the Amundi website to download the holdings XLSX file.
        Implements a 'Manual Escape Hatch' to look for local files first.
        """
        logger.info(f"--- Running Amundi holdings acquisition for {isin} ---")

        # 1. Try Manual File
        df = self._fetch_from_manual_file(isin)
        if df is not None:
            return df

        # 2. Fallback to Automation
        logger.info("  - ℹ️ No manual file found. Proceeding to automated download...")
        return self._fetch_via_selenium(isin)

    def _fetch_from_manual_file(self, isin: str) -> Optional[pd.DataFrame]:
        """Attempts to load and parse a manually placed file."""
        manual_dir = MANUAL_INPUTS_DIR
        xlsx_path = os.path.join(manual_dir, f"{isin}.xlsx")
        csv_path = os.path.join(manual_dir, f"{isin}.csv")

        df = None

        # A. Try XLSX
        if os.path.exists(xlsx_path):
            logger.info(f"  - ✅ Found manual file: {xlsx_path}")
            df = self._read_manual_xlsx(xlsx_path)

        # B. Try CSV
        if df is None and os.path.exists(csv_path):
            logger.info(f"  - ✅ Found manual file: {csv_path}")
            df = self._read_manual_csv(csv_path)

        # C. Process Dataframe
        if df is not None:
            return self._process_manual_dataframe(df)

        return None

    def _read_manual_xlsx(self, path: str) -> Optional[pd.DataFrame]:
        """Reads XLSX with header hunting and calamine fallback."""
        try:
            # Header Hunting
            temp_df = None
            try:
                temp_df = pd.read_excel(path, header=None, nrows=30)
            except Exception as e_default:
                if CALAMINE_AVAILABLE:
                    logger.warning(
                        f"    - Default engine failed ({e_default}). Retrying with 'calamine'..."
                    )
                    temp_df = pd.read_excel(
                        path, header=None, nrows=30, engine="calamine"
                    )
                else:
                    raise e_default

            header_row_idx = None
            for i, row in temp_df.iterrows():
                row_str = row.astype(str).str.lower().tolist()
                if "isin" in row_str and "name" in row_str:
                    header_row_idx = i
                    break

            engine = "calamine" if CALAMINE_AVAILABLE else None

            if header_row_idx is not None:
                logger.info(f"    - Detected header at row {header_row_idx}")
                return pd.read_excel(path, header=header_row_idx, engine=engine)
            else:
                logger.warning("    - Could not detect header row. Trying header=0.")
                return pd.read_excel(path, header=0, engine=engine)

        except Exception as e:
            logger.error(f"    - Failed to read manual XLSX: {e}")
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

    def _process_manual_dataframe(self, df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """Cleans and normalizes the manually loaded dataframe."""
        # 1. Normalize Columns
        df.columns = df.columns.str.strip().str.lower()

        col_map = {
            "isin": "isin",
            "name": "name",
            "gewichtung": "weight_percentage",
            "gewichtung (%)": "weight_percentage",
            "weight": "weight_percentage",
            "sektor": "sector",
            "land": "country",
            "währung": "currency",
            "currency": "currency",
        }
        df = df.rename(columns=col_map)

        if "isin" not in df.columns or "weight_percentage" not in df.columns:
            logger.error(
                f"    - Manual file missing required columns. Found: {df.columns.tolist()}"
            )
            return None

        # 2. Clean Data
        initial_len = len(df)
        df = df.dropna(subset=["name", "weight_percentage"])
        df = df[df["isin"].astype(str).str.len() > 5]
        df = df[~df["name"].astype(str).str.contains("Total", case=False, na=False)]
        df = df[~df["name"].astype(str).str.contains("Assets", case=False, na=False)]

        if len(df) < initial_len:
            logger.info(f"    - Dropped {initial_len - len(df)} footer/invalid rows.")

        # Clean Weight
        if df["weight_percentage"].dtype == object:
            df["weight_percentage"] = (
                df["weight_percentage"]
                .astype(str)
                .str.replace("%", "")
                .str.replace(",", ".")
                .str.strip()
            )

        df["weight_percentage"] = pd.to_numeric(
            df["weight_percentage"], errors="coerce"
        )

        # Auto-Scale
        total_weight = df["weight_percentage"].sum()
        if 0.0 < total_weight <= 1.5:
            logger.info(
                f"    - Detected decimal weights (Sum={total_weight:.4f}). Scaling by 100."
            )
            df["weight_percentage"] = df["weight_percentage"] * 100

        df["weight_percentage"] = df["weight_percentage"].clip(lower=0.0)

        # Ensure Schema
        for col in ["ticker", "sector", "country", "currency"]:
            if col not in df.columns:
                df[col] = None

        # Debug AstraZeneca
        astra_row = df[
            df["name"].astype(str).str.contains("ASTRA", case=False, na=False)
        ]
        if not astra_row.empty:
            logger.info(
                f"    - DEBUG: AstraZeneca found. Weight: {astra_row['weight_percentage'].values}"
            )

        cols_to_return = [
            "ticker",
            "isin",
            "name",
            "weight_percentage",
            "sector",
            "country",
            "currency",
        ]
        logger.info(f"    - Successfully parsed manual file with {len(df)} rows.")
        return df[cols_to_return]

    def _fetch_via_selenium(self, isin: str) -> pd.DataFrame:
        """Executes the Selenium automation to download the file."""
        driver = None
        OUTPUT_DIR = RAW_DOWNLOADS_DIR
        DOWNLOAD_KEYWORD = ".xlsx"
        target_url = f"https://www.amundietf.de/de/privatanleger/products/equity/amundi-msci-india-swap-ucits-etf-eur-acc/{isin}"

        try:
            # Configure Driver
            download_dir = os.path.abspath(OUTPUT_DIR)
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
            }
            options.add_experimental_option("prefs", prefs)

            driver = webdriver.Chrome(options=options)
            driver.command_executor._commands["send_command"] = (
                "POST",
                "/session/$sessionId/chromium/send_command",
            )
            params = {
                "cmd": "Page.setDownloadBehavior",
                "params": {"behavior": "allow", "downloadPath": download_dir},
            }
            driver.execute("send_command", params)

            # Navigate & Interact
            logger.info(f"1. Navigating to: {target_url}")
            driver.get(target_url)
            time.sleep(5)

            self._handle_modals(driver)
            self._click_download(driver)

            # Verify Download
            logger.info(f"6. Waiting for download to complete in '{OUTPUT_DIR}'...")
            time.sleep(10)

            for filename in os.listdir(OUTPUT_DIR):
                if DOWNLOAD_KEYWORD in filename and not filename.endswith(
                    ".crdownload"
                ):
                    file_path = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
                    return self._parse_downloaded_file(file_path)

            logger.error("   - Download failed.")
            driver.save_screenshot("data/working/temp/amundi_error.png")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"An unexpected error occurred in Amundi acquisition: {e}")
            if driver:
                driver.save_screenshot("data/working/temp/amundi_error.png")
            return pd.DataFrame()
        finally:
            if driver:
                driver.quit()

    def _handle_modals(self, driver):
        """Handles Profile and Cookie modals."""
        logger.info("2. Handling profile selection modal...")
        profile_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-profile='RETAIL']"))
        )
        driver.execute_script("arguments[0].click();", profile_button)
        time.sleep(1)

        confirm_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "confirmDisclaimer"))
        )
        driver.execute_script("arguments[0].click();", confirm_button)
        time.sleep(5)

        logger.info("3. Handling cookie consent modal...")
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Alle annehmen')]")
            )
        )
        driver.execute_script("arguments[0].click();", cookie_button)
        time.sleep(5)

    def _click_download(self, driver):
        """Navigates tabs and clicks download."""
        logger.info("4. Opening the 'Zusammensetzung' tab...")
        tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'ZUSAMMENSETZUNG')]")
            )
        )
        driver.execute_script("arguments[0].click();", tab)
        time.sleep(2)

        logger.info("5. Finding and clicking the download link...")
        link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(., 'KOMPONENTEN DES ETFS HERUNTERLADEN')]")
            )
        )
        driver.execute_script("arguments[0].click();", link)

    def _parse_downloaded_file(self, file_path: str) -> pd.DataFrame:
        """Parses the standard Amundi download format."""
        try:
            df = pd.read_excel(file_path, header=9)
            df = df[["Name", "ISIN", "Gewichtung (%)"]]
            df.columns = ["name", "isin", "weight_percentage"]
            return df
        except Exception as e:
            logger.error(f"Failed to parse downloaded file: {e}")
            return pd.DataFrame()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python amundi.py <isin>", file=sys.stderr)
        sys.exit(1)

    isin_arg = sys.argv[1]
    adapter = AmundiAdapter()
    holdings = adapter.fetch_holdings(isin_arg)
    if not holdings.empty:
        print(f"Successfully fetched {len(holdings)} holdings.")
        print(holdings.head())
    else:
        print("Failed to fetch holdings.")
