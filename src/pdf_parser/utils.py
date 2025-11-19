import re
from typing import Dict, Optional


def parse_description(description: str) -> Dict[str, Optional[str]]:
    """
    Parses a Trade Republic transaction description to extract trade details.
    """
    result = {
        "trade_type": "BUY",  # Default to BUY
        "isin": None,
        "name": None,
        "quantity": None,
        "price": None,
    }

    # Determine trade type
    if "sell" in description.lower():
        result["trade_type"] = "SELL"

    # Extract ISIN
    isin_pattern = r"[A-Z]{2}[A-Z0-9]{10}"
    isin_match = re.search(isin_pattern, description)
    if isin_match:
        result["isin"] = isin_match.group(0)
        # Extract name: text after ISIN until comma or quantity
        after_isin = description[isin_match.end() :].strip()
        name_match = re.match(r"(.+?)(?:, quantity|$)", after_isin)
        if name_match:
            result["name"] = name_match.group(1).strip()
        else:
            # If no comma, take until quantity or end
            qty_match = re.search(r", quantity", after_isin)
            if qty_match:
                result["name"] = after_isin[: qty_match.start()].strip()
            else:
                result["name"] = after_isin.strip()
    else:
        # No ISIN, extract name from start until quantity
        qty_match = re.search(r", quantity", description)
        if qty_match:
            result["name"] = description[: qty_match.start()].strip()

    # Extract quantity
    qty_match = re.search(r"quantity:\s*([\d.,]+)", description)
    if qty_match:
        result["quantity"] = float(qty_match.group(1).replace(",", "."))

    # Extract price
    price_match = re.search(r"price:\s*([\d.,]+)", description)
    if price_match:
        result["price"] = float(price_match.group(1).replace(",", "."))

    return result
