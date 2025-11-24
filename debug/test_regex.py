import re

def parse_description(description: str):
    result = {"quantity": None}
    
    # New Regex
    qty_match = re.search(r"quantity:.*?([\d.,]+)$", description)
    
    if qty_match:
        raw = qty_match.group(1)
        print(f"Raw match: '{raw}'")
        qty_str = raw.replace(".", "").replace(",", ".")
        try:
            result["quantity"] = float(qty_str)
        except ValueError:
            pass
        
    return result

test_str = "Sell trade DE0007030009 RHEINMETALL AG, quantity: 391,46 € 18.513,57 0.291902"
print(f"Testing: {test_str}")
print(parse_description(test_str))