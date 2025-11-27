
# Order based on typical SQL sort or observed behavior
SORTED_ALL_ISINS = [
    "DE0007030009", # RHM.DE
    "DE0007500001", # TKA.DE
    "DE000A0F5UF5", # EXXT.DE
    "FR0010361683", # INR.PA
    "IE000YYE6WK5", # DFNS.L
    "IE0031442068", # IUSA.AS
    "IE00B3WJKG14", # QDVE.DE
    "IE00B4L5Y983", # EUNL.DE
    "IE00B53SZB19", # CNDX.AS
    "IE00B5BMR087", # SXR8.DE
    "IE00BL25JP72", # XDEQ.DE
    "IE00BYVQ9F29", # s
    "KYG9830T1067", # 1810.HK
    "LU0908500753", # MEUD.DE
    "US0079031078", # AMD
    "US02079K3059", # GOOGL
    "US30303M1027", # META
    "US67066G1040", # NVDA
    "US69608A1088", # PLTR
    "US88160R1014"  # TSLA
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
    "US88160R1014": "TSLA"
}

def generate_inputs():
    input_sequence = []
    
    # 1. Ticker Resolution Inputs
    for isin in SORTED_ALL_ISINS:
        if isin in MAPPING:
            input_sequence.append(MAPPING[isin])
        else:
            input_sequence.append("s")
            
    # 2. Product ID Input (for DE000A0F5UF5)
    # This is requested later in the pipeline
    input_sequence.append("251795")
            
    print("\n".join(input_sequence))

if __name__ == "__main__":
    generate_inputs()
