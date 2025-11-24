import sys
import time
import os
import pandas as pd
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

logger = get_logger(__name__)

class AmundiAdapter:
    def fetch_holdings(self, isin: str) -> pd.DataFrame:
        """
        Navigates the Amundi website to download the holdings XLSX file.
        Implements a 'Manual Escape Hatch' to look for local files first.
        """
        logger.info(f"--- Running Amundi holdings acquisition for {isin} ---")
        
        # --- Manual Escape Hatch ---
        manual_dir = "data/inputs/manual_holdings"
        xlsx_path = os.path.join(manual_dir, f"{isin}.xlsx")
        csv_path = os.path.join(manual_dir, f"{isin}.csv")
        
        df = None
        
        # Try to load the file
        # Strategy: Try XLSX first (default -> calamine). If missing or broken, try CSV.
        
        if os.path.exists(xlsx_path):
            logger.info(f"  - ✅ Found manual file: {xlsx_path}")
            try:
                # "Header Hunting" Strategy
                temp_df = None
                try:
                    temp_df = pd.read_excel(xlsx_path, header=None, nrows=30)
                except Exception as e_default:
                    if CALAMINE_AVAILABLE:
                        logger.warning(f"    - Default engine failed ({e_default}). Retrying with 'calamine'...")
                        temp_df = pd.read_excel(xlsx_path, header=None, nrows=30, engine="calamine")
                    else:
                        raise e_default

                header_row_idx = None
                
                for i, row in temp_df.iterrows():
                    row_str = row.astype(str).str.lower().tolist()
                    if 'isin' in row_str and 'name' in row_str:
                        header_row_idx = i
                        break
                
                read_engine = "calamine" if CALAMINE_AVAILABLE else None # Prefer default if calamine not strictly needed/available, but we already loaded temp_df so likely need it. 
                # Actually, if temp_df succeeded, we know which engine works.
                # But 'read_excel' with engine=None defaults to openpyxl/xlrd.
                # If we are here, temp_df worked.
                
                if header_row_idx is not None:
                    logger.info(f"    - Detected header at row {header_row_idx}")
                    try:
                        df = pd.read_excel(xlsx_path, header=header_row_idx)
                    except:
                        if CALAMINE_AVAILABLE:
                             df = pd.read_excel(xlsx_path, header=header_row_idx, engine="calamine")
                        else: raise
                else:
                    logger.warning("    - Could not detect header row. Trying header=0.")
                    try:
                        df = pd.read_excel(xlsx_path, header=0)
                    except:
                        if CALAMINE_AVAILABLE:
                            df = pd.read_excel(xlsx_path, header=0, engine="calamine")
                        else: raise

            except Exception as e:
                logger.error(f"    - Failed to read manual XLSX: {e}")
                df = None # Ensure None so we fall through to CSV

        # Fallback to CSV if XLSX failed or didn't exist
        if df is None and os.path.exists(csv_path):
            logger.info(f"  - ✅ Found manual file: {csv_path}")
            try:
                # Try reading with different separators
                try:
                    df = pd.read_csv(csv_path, sep=';') # Common in Europe
                    if len(df.columns) < 2: raise ValueError("Not enough columns with ';'")
                except:
                    df = pd.read_csv(csv_path, sep=',')
            except Exception as e:
                 logger.error(f"    - Failed to read manual CSV: {e}")

        # Process the loaded dataframe
        if df is not None:
             # 1. Normalize Columns
             # Map German/Raw headers to Internal Schema
             # We lower-case the file's columns first to make matching case-insensitive
             df.columns = df.columns.str.strip().str.lower()
             
             col_map = {
                 'isin': 'isin',
                 'name': 'name',
                 'gewichtung': 'weight_percentage',
                 'gewichtung (%)': 'weight_percentage',
                 'weight': 'weight_percentage',
                 'sektor': 'sector',
                 'land': 'country',
                 'währung': 'currency',
                 'currency': 'currency'
             }
             
             df = df.rename(columns=col_map)
             
             # Check if required columns exist
             if 'isin' in df.columns and 'weight_percentage' in df.columns:
                 # 2. Clean Data
                 
                 # Drop rows with missing critical data (e.g. footers/disclaimers)
                 # Amundi exports often have trailing disclaimer text that pandas reads as rows
                 initial_len = len(df)
                 
                 # Robust NaN/Empty check
                 df = df.dropna(subset=['name', 'weight_percentage'])
                 
                 # Ensure ISIN is a string and looks valid (length > 5), drop if missing
                 df = df[df['isin'].astype(str).str.len() > 5]
                 
                 # Explicitly drop "Total" or "Assets" rows that might be misread
                 df = df[~df['name'].astype(str).str.contains('Total', case=False, na=False)]
                 df = df[~df['name'].astype(str).str.contains('Assets', case=False, na=False)]

                 if len(df) < initial_len:
                     logger.info(f"    - Dropped {initial_len - len(df)} footer/invalid rows.")

                 # Clean Weight Percentage (Handle '5,40%', '5.40', etc.)
                 if df['weight_percentage'].dtype == object:
                     df['weight_percentage'] = (
                         df['weight_percentage']
                         .astype(str)
                         .str.replace('%', '')
                         .str.replace(',', '.')
                         .str.strip()
                     )
                 
                 df['weight_percentage'] = pd.to_numeric(df['weight_percentage'], errors='coerce')
                 
                 # Auto-Scale Weights (Decimal vs Percentage)
                 # Some files use 0.01 for 1%, others use 1.0 for 1%
                 total_weight = df['weight_percentage'].sum()
                 if 0.0 < total_weight <= 1.5:
                     logger.info(f"    - Detected decimal weights (Sum={total_weight:.4f}). Scaling by 100.")
                     df['weight_percentage'] = df['weight_percentage'] * 100
                 
                 # Clip negative weights to 0.0 to satisfy schema (and handle floating point noise)
                 df['weight_percentage'] = df['weight_percentage'].clip(lower=0.0)
                 
                 # Ensure all schema columns exist (ticker, sector, country, currency)
                 if 'ticker' not in df.columns:
                     df['ticker'] = None
                 if 'sector' not in df.columns:
                     df['sector'] = None
                 if 'country' not in df.columns:
                     df['country'] = None
                 if 'currency' not in df.columns:
                     df['currency'] = None

                 # Debug AstraZeneca
                 astra_row = df[df['name'].astype(str).str.contains("ASTRA", case=False, na=False)]
                 if not astra_row.empty:
                     logger.info(f"    - DEBUG: AstraZeneca found in Amundi file. Weight: {astra_row['weight_percentage'].values}")

                 # Return standard schema
                 cols_to_return = ['ticker', 'isin', 'name', 'weight_percentage', 'sector', 'country', 'currency']
                 logger.info(f"    - Successfully parsed manual file with {len(df)} rows.")
                 return df[cols_to_return]
             else:
                 logger.error(f"    - Manual file loaded but missing required columns (need 'isin' and 'weight/gewichtung'). Found: {df.columns.tolist()}")
                 # Fall through to automation if manual file is invalid
        
        else:
             logger.info("  - ℹ️ No manual file found. Proceeding to automated download...")


        # --- Selenium Automation (Fallback) ---
        driver = None
        downloaded_file_path = None
        
        OUTPUT_DIR = "data/working/raw_downloads"
        DOWNLOAD_KEYWORD = ".xlsx"
        target_url = f"https://www.amundietf.de/de/privatanleger/products/equity/amundi-msci-india-swap-ucits-etf-eur-acc/{isin}"

        try:
            # --- Configure auto-download options ---
            download_dir = os.path.abspath(OUTPUT_DIR)
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=options)

            driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
            params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
            driver.execute("send_command", params)

            logger.info(f"1. Navigating to: {target_url}")
            driver.get(target_url)
            time.sleep(5)

            # --- Handle Modals ---
            logger.info("2. Handling profile selection modal...")
            profile_button_xpath = "//button[@data-profile='RETAIL']"
            profile_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, profile_button_xpath))
            )
            driver.execute_script("arguments[0].click();", profile_button)
            time.sleep(1)
            confirm_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "confirmDisclaimer"))
            )
            driver.execute_script("arguments[0].click();", confirm_button)
            logger.info("   - Profile selection complete.")
            time.sleep(5)

            logger.info("3. Handling cookie consent modal...")
            cookie_button_xpath = "//button[contains(., 'Alle annehmen')]"
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
            )
            driver.execute_script("arguments[0].click();", cookie_button)
            logger.info("   - Cookie consent complete.")
            time.sleep(5)
            
            # --- Find and Click Download Link ---
            logger.info("4. Opening the 'Zusammensetzung' tab...")
            zusammensetzung_tab_xpath = "//button[contains(., 'ZUSAMMENSETZUNG')]"
            zusammensetzung_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, zusammensetzung_tab_xpath))
            )
            driver.execute_script("arguments[0].click();", zusammensetzung_tab)
            logger.info("   - Clicked 'Zusammensetzung' tab.")
            time.sleep(2)

            logger.info("5. Finding and clicking the download link...")
            download_link_xpath = "//a[contains(., 'KOMPONENTEN DES ETFS HERUNTERLADEN')]"
            download_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, download_link_xpath))
            )
            driver.execute_script("arguments[0].click();", download_link)
            logger.info("   - Clicked download link.")
            
            # --- Verify Download ---
            logger.info(f"6. Waiting for download to complete in '{OUTPUT_DIR}'...")
            time.sleep(10)

            for filename in os.listdir(OUTPUT_DIR):
                if DOWNLOAD_KEYWORD in filename and not filename.endswith('.crdownload'):
                    downloaded_file_path = os.path.abspath(os.path.join(OUTPUT_DIR, filename))
                    
                    # --- Parse the downloaded file ---
                    df = pd.read_excel(downloaded_file_path, header=9)
                    df = df[['Name', 'ISIN', 'Gewichtung (%)']]
                    df.columns = ['name', 'isin', 'weight_percentage']
                    return df

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

if __name__ == '__main__':
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