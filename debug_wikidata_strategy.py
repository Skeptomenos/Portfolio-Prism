import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sophisticated_wikidata_lookup(name, raw_ticker, yahoo_ticker):
    """
    Implements a multi-step lookup strategy using Wikidata.
    """
    headers = {"User-Agent": "PortfolioAnalyzer/1.0 (Educational Python Project)"}

    def search_wikidata(query):
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": "en",
            "format": "json",
            "limit": 5,
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("search", [])
        except Exception as e:
            logger.error(f"Search failed for {query}: {e}")
        return []

    def get_entity_details(entity_id):
        url = "https://www.wikidata.org/w/api.php"
        params = {
            "action": "wbgetentities",
            "ids": entity_id,
            "props": "claims|labels|aliases",
            "format": "json",
        }
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("entities", {}).get(entity_id, {})
        except Exception as e:
            logger.error(f"Details failed for {entity_id}: {e}")
        return {}

    def extract_isin(entity_data):
        claims = entity_data.get("claims", {})
        # P946 is ISIN
        isin_claims = claims.get("P946", [])
        if isin_claims:
            return isin_claims[0]["mainsnak"]["datavalue"]["value"]
        return None

    def extract_tickers(entity_data):
        claims = entity_data.get("claims", {})
        # P249 is Ticker Symbol
        ticker_claims = claims.get("P249", [])
        tickers = []
        for claim in ticker_claims:
            if "datavalue" in claim["mainsnak"]:
                tickers.append(claim["mainsnak"]["datavalue"]["value"])
        return tickers

    logger.info(
        f"--- Resolving: {name} | Raw: {raw_ticker} | Yahoo: {yahoo_ticker} ---"
    )

    # Strategy 1: Search by Name
    logger.info(f"1. Searching by Name: {name}")
    results = search_wikidata(name)

    for result in results:
        entity_id = result["id"]
        details = get_entity_details(entity_id)

        # Check ISIN
        isin = extract_isin(details)

        # Check Tickers for validation
        found_tickers = extract_tickers(details)

        logger.info(f"   - Found: {result['label']} ({entity_id})")
        logger.info(f"     ISIN: {isin}")
        logger.info(f"     Tickers: {found_tickers}")

        # Validation Logic
        match_score = 0
        if isin:
            match_score += 1

        if raw_ticker in found_tickers:
            logger.info("     ✅ Raw Ticker Match!")
            match_score += 2

        # Yahoo ticker often has suffix, so check if any found ticker is a prefix
        if yahoo_ticker:
            base_yahoo = yahoo_ticker.split(".")[0]
            if base_yahoo in found_tickers:
                logger.info("     ✅ Yahoo Ticker Base Match!")
                match_score += 1

        if match_score >= 2 or (isin and match_score >= 1):
            logger.info(f"   >>> MATCH CONFIRMED: {isin}")
            return isin

    # Strategy 2: Search by Raw Ticker (if name failed)
    if raw_ticker:
        logger.info(f"2. Searching by Raw Ticker: {raw_ticker}")
        # This is harder because ticker search in Wikidata isn't direct via wbsearchentities usually
        # But we can try searching the ticker string
        results = search_wikidata(raw_ticker)
        for result in results:
            # Similar validation logic...
            pass

    return None


# Test Cases
print("\n=== TEST 1: Apple ===")
sophisticated_wikidata_lookup("APPLE INC", "AAPL", "AAPL")

print("\n=== TEST 2: Microsoft ===")
sophisticated_wikidata_lookup("MICROSOFT CORP", "MSFT", "MSFT")

print("\n=== TEST 3: German Stock (Allianz) ===")
# iShares might give "ALV" as raw, "ALV.DE" as Yahoo
sophisticated_wikidata_lookup("ALLIANZ SE", "ALV", "ALV.DE")
