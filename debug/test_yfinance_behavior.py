import yfinance as yf

def test_lookup(identifier, label):
    print(f"--- Testing {label}: '{identifier}' ---")
    try:
        t = yf.Ticker(identifier)
        # Accessing .info triggers the API call
        info = t.info
        
        # Check for key metadata
        name = info.get('longName') or info.get('shortName')
        sector = info.get('sector')
        country = info.get('country')
        
        if sector and country:
            print(f"✅ SUCCESS: Name='{name}', Sector='{sector}', Country='{country}'")
        else:
            print(f"❌ FAILED: Data empty or missing keys. Keys found: {list(info.keys())[:5]}...")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
    print("")

if __name__ == "__main__":
    # 1. Test Raw European Ticker (as seen in logs)
    test_lookup("NESN", "Raw Ticker (Nestle)")
    test_lookup("NOVO B", "Raw Ticker (Novo Nordisk)")
    
    # 2. Test Suffixed Ticker (Yahoo format)
    test_lookup("NESN.SW", "Suffixed Ticker (Nestle)")
    test_lookup("NOVO-B.CO", "Suffixed Ticker (Novo Nordisk)")
    
    # 3. Test ISIN (as passed by reporting.py)
    test_lookup("CH0038863350", "ISIN (Nestle)")
    
    # 4. Test Garbage (as seen in logs)
    test_lookup("_CURRENCYUSD", "Garbage Ticker")
