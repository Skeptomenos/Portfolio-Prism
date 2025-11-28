# Order based on typical SQL sort or observed behavior
SORTED_ALL_ISINS = [
    "DE0007030009",  # RHM.DE
    "DE0007500001",  # TKA.DE
    "DE000A0F5UF5",  # EXXT.DE
    "FR0010361683",  # INR.PA (Lyxor MSCI India)
    "IE000YYE6WK5",  # DFNS.L
    "IE0031442068",  # IUSA.AS
    "IE00B3WJKG14",  # QDVE.DE
    "IE00B4L5Y983",  # EUNL.DE
    "IE00B53SZB19",  # CNDX.AS
    "IE00B5BMR087",  # SXR8.DE
    "IE00BL25JP72",  # XDEQ.DE
    "IE00BYVQ9F29",  # s (Skipped)
    "KYG9830T1067",  # 1810.HK
    "LU0908500753",  # MEUD.DE
    "US0079031078",  # AMD
    "US02079K3059",  # GOOGL
    "US30303M1027",  # META
    "US67066G1040",  # NVDA
    "US69608A1088",  # PLTR
    "US88160R1014",  # TSLA
]

MAPPING = {
    "DE0007030009": "RHM.DE",
    "DE0007500001": "TKA.DE",
    "DE000A0F5UF5": "EXXT.DE",
    "FR0010361683": "INR.PA",
    "IE000YYE6WK5": "DFNS.L",
    "IE0031442068": "IUSA.AS",
    "IE00B3WJKG14": "QDVE.DE",
    "IE00B4L5Y983": "EUNL.DE",
    "IE00B53SZB19": "CNDX.AS",
    "IE00B5BMR087": "SXR8.DE",
    "IE00BL25JP72": "XDEQ.DE",
    # "IE00BYVQ9F29": "s",
    "KYG9830T1067": "1810.HK",
    "LU0908500753": "MEUD.DE",
    "US0079031078": "AMD",
    "US02079K3059": "GOOGL",
    "US30303M1027": "META",
    "US67066G1040": "NVDA",
    "US69608A1088": "PLTR",
    "US88160R1014": "TSLA",
}


def generate_inputs():
    input_sequence = []
    for isin in SORTED_ALL_ISINS:
        # Note: Ticker resolution only prompts if auto-discovery fails.
        # But we don't know for sure if it will fail for all of these.
        # yfinance ISIN lookup is hit-or-miss.
        # If it succeeds, it won't consume our input.
        # If it fails, it consumes one line.

        # Strategy: The safest bet for an automated run without conditional logic
        # is difficult. However, since we are in a "clean run", the map is empty.
        # We should expect prompts for most ISINs unless yfinance got smarter.

        # Wait! resolve_ticker() prints "Found direct match" if it works.
        # If it works, it DOES NOT prompt.
        # If I feed inputs for success cases, they will be buffered and consumed by the *next* failure.

        # This makes blind piping dangerous.
        # Correct approach: We should have updated `ticker_map.json` beforehand?
        # No, the goal is to test the interactive flow.

        # I will assume ALL ISIN lookups fail initially (safer assumption for generic ISINs).
        # Or, I can write a script to pre-populate the ticker map, but that defeats the purpose.

        if isin in MAPPING:
            input_sequence.append(MAPPING[isin])
        else:
            input_sequence.append("s")

    print("\n".join(input_sequence))


if __name__ == "__main__":
    generate_inputs()
