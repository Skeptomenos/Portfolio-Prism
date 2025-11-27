#!/usr/bin/env python3
"""
API Testing Script: ISIN Resolution Comparison
Tests OpenFIGI, Wikidata, and Finnhub APIs for reliability in resolving ISINs.
"""

import sys
import os
import time
import requests
from typing import Optional
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

# Test Dataset: 15 securities that failed in recent pipeline run
TEST_SECURITIES = [
    {"ticker": "AVGO", "name": "Broadcom Inc", "exchange": "US", "expected_isin": None},
    {
        "ticker": "GOOG",
        "name": "Alphabet Inc",
        "exchange": "US",
        "expected_isin": "US02079K3059",
    },
    {
        "ticker": "BRKB",
        "name": "Berkshire Hathaway Inc",
        "exchange": "US",
        "expected_isin": "US0846707026",
    },
    {
        "ticker": "NFLX",
        "name": "Netflix Inc",
        "exchange": "US",
        "expected_isin": "US64110L1061",
    },
    {
        "ticker": "HD",
        "name": "Home Depot Inc",
        "exchange": "US",
        "expected_isin": "US4370761029",
    },
    {
        "ticker": "MRK",
        "name": "Merck & Co Inc",
        "exchange": "US",
        "expected_isin": "US58933Y1055",
    },
    {
        "ticker": "ASML",
        "name": "ASML Holding NV",
        "exchange": "AS",
        "expected_isin": "NL0010273215",
    },
    {
        "ticker": "AZN",
        "name": "AstraZeneca PLC",
        "exchange": "L",
        "expected_isin": "GB0009895292",
    },
    {
        "ticker": "ROG",
        "name": "Roche Holding AG",
        "exchange": "SW",
        "expected_isin": "CH0012032048",
    },
    {
        "ticker": "NESN",
        "name": "Nestle SA",
        "exchange": "SW",
        "expected_isin": "CH0038863350",
    },
    {
        "ticker": "NOVN",
        "name": "Novartis AG",
        "exchange": "SW",
        "expected_isin": "CH0012005267",
    },
    {
        "ticker": "SAP",
        "name": "SAP SE",
        "exchange": "DE",
        "expected_isin": "DE0007164600",
    },
]

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Results storage
results = []


def _check_openfigi(ticker: str, name: str, exchange: str) -> Optional[str]:
    """
    Test OpenFIGI API for ISIN resolution.

    Args:
        ticker: Stock ticker symbol
        name: Company name
        exchange: Exchange code (US, L, SW, DE, AS)

    Returns:
        ISIN if found, None otherwise
    """
    url = "https://api.openfigi.com/v3/mapping"

    # Try multiple query strategies
    queries = [
        {"idType": "TICKER", "idValue": ticker, "exchCode": exchange},
        {"query": name},
        {"idType": "TICKER", "idValue": ticker},
    ]

    headers = {"Content-Type": "application/json"}

    for query in queries:
        try:
            payload = [query]
            response = requests.post(url, json=payload, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0 and "data" in data[0]:
                    results_list = data[0]["data"]
                    if results_list:
                        # Check if ISIN is in response
                        first_result = results_list[0]

                        # OpenFIGI might return ISIN in different fields
                        # Common fields: isin, compositeFIGI, shareClassFIGI
                        isin = first_result.get("isin")
                        if isin:
                            return isin

            time.sleep(0.3)  # Rate limiting

        except Exception as e:
            print(f"    OpenFIGI error for {ticker}: {e}")
            continue

    return None


def _check_wikidata(ticker: str, name: str) -> Optional[str]:
    """
    Test Wikidata API for ISIN resolution.
    Uses existing implementation from enrichment.py

    Args:
        ticker: Stock ticker symbol
        name: Company name

    Returns:
        ISIN if found, None otherwise
    """
    from src.data.enrichment import fetch_isin_from_wikidata

    try:
        isin = fetch_isin_from_wikidata(
            company_name=name, raw_ticker=ticker, yahoo_ticker=ticker
        )
        return isin
    except Exception as e:
        print(f"    Wikidata error for {ticker}: {e}")
        return None


def _check_finnhub(ticker: str) -> Optional[str]:
    """
    Test Finnhub API for ISIN resolution.

    Args:
        ticker: Stock ticker symbol

    Returns:
        ISIN if found, None otherwise
    """
    if not FINNHUB_API_KEY:
        return None

    url = "https://finnhub.io/api/v1/stock/profile2"
    params = {"symbol": ticker, "token": FINNHUB_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return data.get("isin")
        time.sleep(1.1)  # Rate limiting
    except Exception as e:
        print(f"    Finnhub error for {ticker}: {e}")

    return None


def run_tests():
    """Run tests for all securities across all APIs."""
    print("=" * 80)
    print("ISIN Resolution API Testing")
    print("=" * 80)
    print(f"\nTesting {len(TEST_SECURITIES)} securities across 3 APIs...\n")

    for idx, security in enumerate(TEST_SECURITIES, 1):
        ticker = security["ticker"]
        name = security["name"]
        exchange = security["exchange"]
        expected = security["expected_isin"]

        print(f"[{idx}/{len(TEST_SECURITIES)}] Testing: {ticker} ({name})")

        # Test OpenFIGI
        print("  - OpenFIGI...", end=" ", flush=True)
        start = time.time()
        openfigi_isin = _check_openfigi(ticker, name, exchange)
        openfigi_time = time.time() - start
        print(
            f"{'✓ ' + openfigi_isin if openfigi_isin else '✗ Not Found'} ({openfigi_time:.2f}s)"
        )

        # Test Wikidata
        print("  - Wikidata...", end=" ", flush=True)
        start = time.time()
        wikidata_isin = _check_wikidata(ticker, name)
        wikidata_time = time.time() - start
        print(
            f"{'✓ ' + wikidata_isin if wikidata_isin else '✗ Not Found'} ({wikidata_time:.2f}s)"
        )

        # Test Finnhub
        print("  - Finnhub...", end=" ", flush=True)
        start = time.time()
        finnhub_isin = _check_finnhub(ticker)
        finnhub_time = time.time() - start
        print(
            f"{'✓ ' + finnhub_isin if finnhub_isin else '✗ Not Found'} ({finnhub_time:.2f}s)"
        )

        # Store result
        results.append(
            {
                "ticker": ticker,
                "name": name,
                "exchange": exchange,
                "expected_isin": expected,
                "openfigi_isin": openfigi_isin,
                "openfigi_time": openfigi_time,
                "wikidata_isin": wikidata_isin,
                "wikidata_time": wikidata_time,
                "finnhub_isin": finnhub_isin,
                "finnhub_time": finnhub_time,
            }
        )

        print()


def generate_report():
    """Generate comparison report from test results."""
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    # Calculate success rates
    openfigi_success = sum(1 for r in results if r["openfigi_isin"])
    wikidata_success = sum(1 for r in results if r["wikidata_isin"])
    finnhub_success = sum(1 for r in results if r["finnhub_isin"])

    total = len(results)

    print("\n📊 Success Rate (ISINs Found):")
    print(
        f"  - OpenFIGI:  {openfigi_success}/{total} ({openfigi_success / total * 100:.1f}%)"
    )
    print(
        f"  - Wikidata:  {wikidata_success}/{total} ({wikidata_success / total * 100:.1f}%)"
    )
    print(
        f"  - Finnhub:   {finnhub_success}/{total} ({finnhub_success / total * 100:.1f}%)"
    )

    # Calculate average response times
    openfigi_avg_time = sum(r["openfigi_time"] for r in results) / total
    wikidata_avg_time = sum(r["wikidata_time"] for r in results) / total
    finnhub_avg_time = sum(r["finnhub_time"] for r in results) / total

    print("\n⏱️  Average Response Time:")
    print(f"  - OpenFIGI:  {openfigi_avg_time:.2f}s")
    print(f"  - Wikidata:  {wikidata_avg_time:.2f}s")
    print(f"  - Finnhub:   {finnhub_avg_time:.2f}s")

    # Accuracy check (where we have expected ISINs)
    print("\n✅ Accuracy (vs Expected ISINs):")
    for api_name, field in [
        ("OpenFIGI", "openfigi_isin"),
        ("Wikidata", "wikidata_isin"),
        ("Finnhub", "finnhub_isin"),
    ]:
        correct = 0
        total_with_expected = 0
        for r in results:
            if r["expected_isin"]:
                total_with_expected += 1
                if r[field] == r["expected_isin"]:
                    correct += 1

        if total_with_expected > 0:
            print(
                f"  - {api_name}: {correct}/{total_with_expected} ({correct / total_with_expected * 100:.1f}%)"
            )

    # Save to CSV
    import csv

    output_file = "outputs/isin_api_test_results.csv"
    os.makedirs("outputs", exist_ok=True)

    with open(output_file, "w", newline="") as f:
        fieldnames = [
            "ticker",
            "name",
            "exchange",
            "expected_isin",
            "openfigi_isin",
            "openfigi_time",
            "wikidata_isin",
            "wikidata_time",
            "finnhub_isin",
            "finnhub_time",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n💾 Detailed results saved to: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
    generate_report()
