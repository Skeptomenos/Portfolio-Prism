# The Developer's Blueprint for True Exposure: A Guide to Sourcing ETF Holdings and Building a Look-Through Analysis Engine

## Part 1: The Data Sourcing Landscape: A Strategic Assessment

### Section 1.1: Introduction: Defining the Core Problem and the "Free API Fallacy"

The objective of this report is to provide a technical blueprint for a tool that calculates the "true company exposure" within an investment portfolio. This "look-through" analysis involves aggregating the underlying constituents of all Exchange-Traded Funds (ETFs) held in a portfolio to reveal the precise, aggregated exposure to individual stocks, bonds, and other assets. This is a non-trivial data engineering and quantitative task, distinct from simple portfolio tracking. The primary and most significant bottleneck for this project is the sourcing of complete, accurate, and timely ETF holdings data.   

The logical starting point for such a project is the search for a free Application Programming Interface (API) that provides this complete holdings data. However, a systematic analysis of the financial data market reveals this to be a "Free API Fallacy." Data providers that offer free-tier access for basic financial data (e.g., end-of-day stock prices) consistently and deliberately place high-value, aggregated datasets—such as complete ETF constituents—behind premium paywalls.

This report will first provide definitive evidence of this "fallacy" to prevent wasted development time. It will then pivot to the only practical and free solution: a multi-pronged, strategic web scraping approach. This analysis will provide a technical blueprint for targeting the three most viable data sources: primary ETF issuers, third-party aggregator portals, and public regulatory databases.

### Section 1.2: The "Free API Fallacy": An Analysis of Freemium Provider Limits

To build a resilient tool, it is critical to first understand the limitations of common freemium data providers. An examination of their service tiers demonstrates a clear business model: attract developers with free, commoditized data (like stock prices) but monetize the complex, high-value data (like complete ETF holdings) that this project requires.

- **Alpha Vantage**: A common entry point for developers, Alpha Vantage offers a free API for stock data. While its API documentation lists an endpoint for "ETF Profile & Holdings" , the free tier is severely restricted to 25 API requests per day. This daily limit is fundamentally insufficient for a tool that would need to query holdings for multiple ETFs, especially if those holdings require periodic updates. The 25-request-per-day limit makes this provider non-viable for the project's core function.   
    
- **Finnhub**: Finnhub offers a more generous free tier for general market data, with up to 60 API calls per minute. However, its pricing and API documentation are explicit. The endpoints required for this project, such as "ETFs Holdings," "ETFs Industry Exposure," and "ETFs Country Exposure," are clearly marked as **Premium**. The free tier does not include access to the complete constituent data.   
    
- **EODHistoricalData (EODHD)**: This provider follows a similar model. Its free plan is highly restrictive, with a limit of 20 API calls per day and a limited 1-year data range. While the platform offers an "ETFs Fundamentals Data API," this endpoint provides only the "Top 10 Holdings," not the _complete_ list required for a true exposure calculation.   
    

The pattern is clear and consistent. Complete, machine-readable ETF constituent data is a high-value product. Providers invest significant resources in aggregating, cleaning, and standardizing this data from disparate sources. Consequently, they reserve this data for their paying subscribers. The project, which depends entirely on this specific dataset, cannot be built on these free-tier APIs. The quest for a "free API" for this data is futile; the project _must_ be built on a different data sourcing strategy.

This conclusion is summarized in the table below.

**Table 1: Freemium API Tier Limitation Analysis for Complete ETF Holdings**

|Provider|Free Tier Call Limit|Endpoint for Complete ETF Holdings|Available on Free Tier?|
|---|---|---|---|
|Alpha Vantage|25 requests/day|`ETF Profile & Holdings`|No (Insufficient limits)|
|Finnhub|60 calls/minute|`ETFs Holdings`|**No (Premium Endpoint)**|
|EODHistoricalData|20 requests/day|`ETFs Fundamentals Data API`|No (Provides Top 10 only)|

  

### Section 1.3: The Viable Path: A 3-Pronged Scraping Strategy

Given that commercial APIs do not provide the necessary data for free, the project's foundation must be web scraping. This approach is not without its own challenges (e.g., scraper maintenance), but it is the only path that meets the project's constraints. An analysis of available free data sources reveals three distinct and viable target categories:

1. **Primary Sources (Issuer Websites):** Scraping data directly from the ETF issuers (e.g., BlackRock/iShares, Vanguard, State Street/SPDR). This is the _most reliable_ source for timely, accurate, and complete data, as the issuers themselves publish it.   
    
2. **Aggregator Portals:** Scraping third-party financial data portals (e.g., Morningstar). This is a potential fallback, but as will be shown, most portals only provide partial data, though some offer advanced "hidden" methods.
    
3. **Regulatory Databases:** Scraping data from public regulatory filings, specifically the SEC EDGAR database. This is a highly robust, standardized, and comprehensive method, though the data is less timely (typically quarterly).   
    

The remainder of this report provides a detailed technical guide for implementing all three strategies.

## Part 2: A Developer's Guide to Scraping ETF Holdings Data

### Section 2.1: Strategy 1: Scraping Primary Sources (The Gold Standard)

This is the recommended primary strategy. The data is direct from the source, complete, and often available in machine-readable formats (CSV/XLSX), which are ideal for programmatic ingestion. The primary challenge is that each issuer's website is different, requiring a bespoke scraper (or "adapter") for each ETF family (e.g., iShares, Vanguard) the tool intends to support.   

#### iShares (BlackRock)

- **Methodology:** iShares provides a direct, persistent AJAX URL for many of its funds that serves the complete holdings as a CSV file. This is the simplest and most robust scraping target.
    
- **Evidence and Guide:** An analysis of network traffic on iShares product pages reveals these download links. For example,  provides a direct Python `pandas.read_csv(url,...)` example for the SOXX ETF. The URL structure is generally: `https://www.ishares.com/us/products/[...]/[fund-name]/1467271812596.ajax?fileType=csv&fileName=_holdings&dataType=fund` A Python function can be written to format this URL string with the user's desired iShares ticker. This method is so reliable that open-source projects like `ishares` on GitHub exist solely to automate this exact process.   
    

#### Vanguard

- **Methodology:** Vanguard product pages display complete holdings in an HTML table or provide a "Portfolio composition file" link.   
    
- **Evidence and Guide:** The product page for VTI (Vanguard Total Stock Market ETF) , for example, lists "Holding details"  and the page for VT (Vanguard Total World Stock ETF) shows a "Portfolio composition file" with columns for Ticker, Holdings (company name), CUSIP, SEDOL, % of fund, Shares, and Market value. This is confirmed by community analysis, which notes that while Yahoo Finance fails to provide complete data for Vanguard funds, the Vanguard website itself has the complete composition. This source cannot be scraped with a simple `read_csv`. It requires a tool like Python's `requests` library to fetch the page, followed by `BeautifulSoup` or `pandas.read_html` to parse the specific HTML table containing the holdings data.   
    

#### State Street (SPDR)

- **Methodology:** SSGA provides direct, daily-updated `.xlsx` (Excel) file downloads for its funds, particularly the popular Sector SPDRs.   
    
- **Evidence and Guide:** The direct download link `.../holdings-daily-us-en-spy.xlsx` exists for SPY. More importantly,  provides a full Python script that successfully scrapes this data. It iterates a list of SPDR sector tickers (XLC, XLY, XLF, etc.) and programmatically downloads the holdings Excel file for each one from a persistent base URL: `http://www.sectorspdr.com/sectorspdr/IDCO.Client.Spdrs.Holdings/Export/ExportExcel?symbol=`. This is another highly reliable, machine-readable source that can be ingested directly with Python's `pandas.read_excel(url)`.   
    

#### DWS (Xtrackers)

- **Methodology:** DWS product pages offer multiple download links for fund literature.   
    
- **Evidence and Guide:** The "Prospectuses & Reports" section for a fund like XAIX (Artificial Intelligence and Big Data ETF) lists "First Fiscal Quarter Holdings" and "Third Fiscal Quarter Holdings". Another page includes a "Download data (XLSX)" link. This target will require a multi-step scraper: (1) Use `requests` to get the main product page. (2) Use `BeautifulSoup` to find the `href` (link) that matches a text pattern like "Holdings" or "Download data (XLSX)". (3) Pass this extracted URL to `pandas` to ingest the data.   
    

**Table 2: Issuer Scraping Target Guide**

|Issuer|ETF Family (Ticker)|Data Source Example|Data Format|Scraping Method|
|---|---|---|---|---|
|BlackRock|iShares (IVV, SOXX)|AJAX URL|CSV|`pandas.read_csv(formatted_url)`|
|Vanguard|Vanguard (VTI, VOO)|HTML Page|HTML Table|`requests` + `pandas.read_html()`|
|State Street|SPDR (SPY, XLF)|Direct URL|XLSX|`pandas.read_excel(formatted_url)`|
|DWS|Xtrackers (XAIX)|Product Page Links|XLSX / PDF|`requests` + `BeautifulSoup` (to find link)|

  

### Section 2.2: Strategy 2: Scraping Aggregator Portals

This strategy involves scraping third-party aggregators. While this can centralize scraping efforts, it comes with significant limitations, as most aggregators only display partial data to non-paying users.

#### The Yahoo Finance / yfinance Trap

A Python developer building a financial tool will almost certainly turn to the `yfinance` library first. For this specific project, this is a critical mistake. The `yfinance` library is an excellent tool for price data, but it is **unsuitable for complete holdings analysis.**   

The library's Ticker object provides access to fund data via attributes like `funds_data.top_holdings`. However, as the name implies and as multiple developer discussions confirm, this _only_ returns the **Top 10 Holdings**. This is not a limitation of the library, but of its data source: the Yahoo Finance website _itself_ only displays the top 10 holdings on its public "holdings" page. Using `yfinance` or `yahooquery`  will cause the tool to _fail_ its core mission of calculating "true" exposure, as it will be based on only a small fraction of an ETF's actual constituents.   

#### The Morningstar "Concealed API" Technique (Advanced)

Morningstar is an extremely data-rich source , but it is notoriously difficult to scrape. Simple `requests` or `BeautifulSoup` approaches will fail because the data is loaded dynamically via JavaScript.   

- **Methodology:** The solution is to use browser developer tools to "sniff" the internal, concealed API calls the website's frontend uses to populate its own data tables.   
    
- **Evidence and Guide:**  provides a complete Python code example that demonstrates this advanced technique. A developer, failing to scrape the page with `lxml`, used their browser's "Inspect → Network" tab to find that the Morningstar page calls a URL like `https://api-global.morningstar.com/sal-service/v1/fund/portfolio/holding/v2/.../data`. The script then replicates this call using the `requests` library, passing the exact `headers` (including an `apikey`) and `payload` (query parameters) it sniffed from the browser. This call returns a clean JSON response containing the _complete_ holdings data.   
    
- This method can be taken further. Some of these internal APIs are protected by a "bearer token" that is generated dynamically. As described in  and , a headless browser library like `Playwright` can be used to programmatically load the page, intercept the network requests, extract the `Authorization` header containing the bearer token, and then use that token to make authenticated calls to the concealed API. This is a powerful but technically complex fallback strategy.   
    

### Section 2.3: Strategy 3: Scraping SEC EDGAR (The "Standardized" Method)

#### Methodology

This is a non-traditional, highly effective "quant" approach that targets public, mandatory regulatory filings. In the U.S., all registered investment funds (including ETFs) must file their complete holdings with the Securities and Exchange Commission (SEC) on a quarterly basis. This filing is known as "Form NPORT-P". This data is public, standardized, and machine-readable (typically XML or HTML-formatted XML).   

#### Evidence and Guide

The open-source project `ETFConstituentExtractor` (found on GitHub) is purpose-built for this exact task. Its methodology, as summarized in , is as follows:   

1. **Input:** The tool takes an ETF's CIK (Central Index Key), which is the SEC's unique identifier for a filer.
    
2. **API Call:** It uses the SEC's EDGAR API to find all NPORT-P filings associated with that CIK.
    
3. **Scraping:** It then web-scrapes the specific filing (which is a public web page) to find the holdings data.
    
4. **Parsing:** The tool parses the file to extract the complete holdings table, including company name, CUSIP, shares held, market value, and percentage of the portfolio.   
    
5. **Output:** The data is saved to a clean CSV file.
    

#### The Hybrid Source Solution

These three strategies present a classic engineering trade-off.

- **Strategy 1 (Issuer Scraping)** is the most _timely_. State Street, for example, provides daily holdings files. However, this strategy is _fragile_. A simple website redesign by Vanguard could break the scraper, requiring constant maintenance. It is also _high-effort_, as it requires a new, bespoke scraper for every single ETF issuer.   
    
- **Strategy 3 (SEC EDGAR Scraping)** is the most _robust_. The NPORT-P format is standardized by law, not by a web design team. One well-written scraper can, in theory, get data for _all_ U.S. ETFs. However, this strategy is _slow_. The data is filed quarterly and may be published with a lag.   
    

Therefore, the optimal architecture for a resilient and professional-grade tool is a _hybrid_ one. The tool's data logic should first attempt to fetch data using the _Primary Source (Issuer) Scraper_ for the most timely (e.g., daily or monthly) data. If that scraper fails (due to a website change) or if the tool encounters an ETF from an issuer for which no bespoke adapter exists, it should _automatically fall back_ to the _SEC EDGAR NPORT-P Scraper_. This provides the (slightly stale-but-complete) quarterly data, ensuring the tool always returns a result instead of failing. This hybrid, fallback-driven design is a professional, resilient architecture that provides the best of both worlds.

## Part 3: Core Architectural Challenges and Solutions for an Exposure Engine

Sourcing the data is only the first half of the problem. The "challenges and solutions" for a project like this lie in the data engineering and quantitative logic required to aggregate the heterogeneous data into a single, correct answer.

### Section 3.1: Challenge: The Identifier Mapping Problem

#### The Problem: Heterogeneous Identifiers

The scrapers will _not_ return clean, common tickers like `AAPL` or `MSFT`. An examination of the source data shows the problem clearly:

- Vanguard's data provides "Ticker," "CUSIP," and "SEDOL".   
    
- The `ETFConstituentExtractor` (from SEC filings) is built around "CUSIP".   
    
- Other international funds may provide "ISIN"s.
    

The tool's database will quickly fill with a mix of identifiers: `037833100` (Apple's CUSIP), `US0378331005` (Apple's ISIN), and `AAPL` (Apple's Ticker). The tool will be unable to aggregate them; it will incorrectly treat them as three different companies. This "identifier mapping" or "symbology" problem is a central challenge in all of financial technology.   

#### The Solution: A Centralized Mapping Service

The solution is to "normalize" all identifiers. After scraping a holdings file, every holding's identifier must be mapped to one _single, global, persistent identifier_.

The primary solution for this is the **OpenFIGI API**. This is a free, open, and MIT-licensed service specifically designed to solve this problem. Its entire purpose is to map between various financial identifiers, such as CUSIP → FIGI, ISIN → FIGI, or Ticker → FIGI. The API is free to use with an API key, provides a generous rate limit (25 requests per 6 seconds, far exceeding the 25/day of Alpha Vantage), and is built for this exact high-volume, programmatic use case.   

The tool will require a "normalization" module. This module will iterate through every scraped holding, call the OpenFIGI API with the identifier it has (e.g., `idType: CUSIP`, `idValue: 037833100`), and receive a JSON response mapping it to a common ticker and a composite FIGI. This normalized identifier becomes the new primary key in the database, allowing for correct aggregation.   

While OpenFIGI is the recommended choice, other services exist. EODHD  and `sec-api.io`  also offer free mapping endpoints, but their free tiers are far more restrictive and not suitable for the potential volume of this project.   

**Table 3: Identifier Mapping API Comparison**

|Provider|Cost|Identifiers Handled|Free Tier Limit|Recommendation|
|---|---|---|---|---|
|OpenFIGI|Free|CUSIP, ISIN, SEDOL, Ticker, etc.|25 requests/6 seconds|**Primary Choice.**|
|EODHD|Free Plan|CUSIP, ISIN, FIGI, Ticker|20 requests/day|Good, but too limited.|
|sec-api.io|Freemium|CIK, Ticker, CUSIP, Name|100 API calls (total)|Viable alternative for CIK mapping.|

  

### Section 3.2: Challenge: The Recursive "Look-Through" (ETFs of ETFs)

#### The Problem: "ETFs of ETFs"

A simple "one-level-deep" look-through is insufficient for calculating "true" exposure. Many portfolio strategies use "ETFs of ETFs". For example, a user may hold a single "Asset Allocation ETF" (e.g., `ETF_A`). But `ETF_A` itself holds no stocks; its holdings are 60% `ETF_B` (a U.S. stock ETF) and 40% `ETF_C` (a bond ETF). The tool _must_ be able to recursively "un-nest" `ETF_B` and `ETF_C` and multiply the weights. The true exposure to Apple in this portfolio is `Weight_of_A_in_Portfolio * Weight_of_B_in_A * Weight_of_AAPL_in_B`.   

#### The Solution: A Recursive Aggregation Algorithm

The core logic of the tool must be a recursive function. This function's job is to resolve a dictionary of holdings into a final list of _base securities_ (stocks, bonds) and their aggregated weights. This process is a form of recursive bisection applied to portfolio composition.   

To do this, the tool must maintain a `master_etf_list` (or be able to check if a given holding is itself an ETF). When processing a portfolio, if a holding is identified as an ETF, the function must call _itself_ on that holding, passing down the new proportional weight to be multiplied.

The following pseudo-code outlines this core recursive logic:

Python

```
# Pseudo-code for recursive look-through
def get_true_exposure(portfolio_dict, master_etf_list):
    final_holdings = defaultdict(float)
    
    # Iterate over assets in the current portfolio level
    for (asset_id, weight) in portfolio_dict.items():
        
        # Normalize the asset_id using the OpenFIGI mapper
        normalized_id = normalize_identifier(asset_id)
        
        if normalized_id in master_etf_list:
            # 1. This holding is an ETF. Recurse.
            # Get this ETF's holdings from the hybrid adapter
            etf_holdings_data = get_holdings_from_adapter(normalized_id) 
            
            # 2. Call the function on itself with the new holdings
            recursive_holdings = get_true_exposure(etf_holdings_data, master_etf_list)
            
            # 3. Add recursive holdings, multiplying by the parent weight
            for (security, recursive_weight) in recursive_holdings.items():
                final_holdings[security] += weight * recursive_weight
        else:
            # 4. This is a base security (stock, bond). Add its weight.
            final_holdings[normalized_id] += weight
            
    return final_holdings
```

### Section 3.3: Challenge: Data Aggregation & Normalization

#### The Problem: Heterogeneous Data Formats

As established in Part 2, the data sources are fundamentally heterogeneous. The tool's core logic cannot be built to simultaneously parse iShares CSVs , Vanguard HTML tables , SPDR XLSX files , and SEC NPORT-P XML files. This would create an unmaintainable, tightly-coupled system. This problem of disjointed data and connectivity is a common challenge in FinTech systems.   

#### The Solution: The "Adapter" Design Pattern

The open-source project `etf4u` provides an elegant solution to this exact problem. Its architecture is built on "bespoke adapters" for specific funds and a "generic adapter" (which scrapes `etfdb.com`) as a fallback.   

This "Adapter" pattern should be adopted. The tool's architecture should feature a main `Data` module that is decoupled from the core aggregation logic. The main logic will simply call `data.get_holdings('SPY')`. This adapter module will act as a router, consulting an internal mapping to determine which _sub-scraper_ to call (e.g., `spdr_scraper.get_spy()`).

Each sub-scraper (e.g., `ishares_scraper`, `vanguard_scraper`, `sec_edgar_scraper`) is responsible for its own unique extraction logic. Critically, each adapter must _normalize_ its output to a standard internal data format (e.g., a dictionary of `{'identifier': '037833100', 'id_type': 'CUSIP', 'weight': 0.0704}`) before returning it. This modular, "hub-and-spoke" design  makes the tool highly maintainable and extensible. Adding support for a new ETF issuer (e.g., Invesco) only requires adding a new "adapter" file, not refactoring the entire application.   

### Section 3.4: Challenge: The Final Calculation (Aggregating Exposures)

#### The Problem: The Final Calculation

Once the data is scraped, normalized by the adapters, mapped by OpenFIGI, and resolved by the recursive function, how is the final "true exposure" for a single company calculated?

#### The Solution: Sum of Weighted Products

The open-source `baskets` project  and an Intrinio technical blog  describe this final step. The goal is to "reconstruct the dollar amount exposure to each constituent stock" by aggregating the allocations across multiple ETFs. The `baskets` project specifically collects "fractional constituents of each ETF" to achieve this. Similarly, the Intrinio guide explains the process of using an ETF's holdings data, multiplying the `allocation` (the investor's dollars in the ETF) by the holding's `weight`, and then grouping and summing these values across the entire portfolio.   

After the recursive function `get_true_exposure` runs on the user's top-level portfolio, it will return a single, flat dictionary where the keys are normalized base securities (e.g., `AAPL_FIGI`) and the values are their final, aggregated portfolio weights.

For any given stock (e.g., `AAPL`), this final weight represents the sum of all its exposures, calculated as: `True_Exposure_AAPL = (Portfolio_Weight_ETF1 * ETF1_Weight_AAPL) + (Portfolio_Weight_ETF2 * ETF2_Weight_AAPL) +...`

This final number is the core deliverable. It allows an investor to see beyond their high-level allocation (e.g., "30% U.S. Equities") and understand their "true factor biases"  or "risk factor decomposition". For example, an investor who holds three different "Tech" ETFs and a "Growth" ETF may be shocked to find their "true" portfolio exposure to a single company like NVIDIA is over 20%, a level of concentrated risk they would be unaware of without this look-through tool.   

## Part 4: Case Studies: Deconstructing Open-Source Look-Through Tools

The request for "reports about similar projects" can be best answered by deconstructing existing open-source projects. These case studies validate the architecture proposed in Part 3.

### Case Study 1: `ETFConstituentExtractor`

- **Methodology:** This tool is a pure implementation of Strategy 3 (SEC Scraping). It takes an ETF's CIK, uses the SEC EDGAR API to find its quarterly NPORT-P filings, and scrapes those filings to extract the complete holdings list, including CUSIPs, shares, and market values.   
    
- **Key Takeaway:** This project is a powerful validation that scraping SEC filings is a robust and viable method for obtaining _complete, standardized_ holdings data for _all_ U.S. ETFs with a single parser. Its primary weakness, which necessitates the hybrid approach, is the data's low frequency (quarterly).
    

### Case Study 2: `baskets`

- **Methodology:** This Python library is a direct parallel to the project's goal. It is designed to "download the compositions of those ETFs" and "reconstruct the dollar amount exposure to each constituent stock". It explicitly scrapes issuer web pages and requires dependencies like `selenium` (for dynamic JavaScript-heavy sites), `xlrd`, and `openpyxl` (for Excel files).   
    
- **Key Takeaway:** This project validates Strategy 1 (Issuer Scraping). Its existence proves the demand for this type of tool, and its required libraries confirm the technical challenges and solutions (like targeting SPDR's `.xlsx` files) outlined in Part 2.
    

### Case Study 3: `etf4u`

- **Methodology:** This Python tool scrapes ETF information and performs "proportional asset allocation". Its architecture is its most important feature. It uses "bespoke adapters" for specific funds where the full holdings are available, and a "generic adapter" (which scrapes `etfdb.com` for top holdings) as a fallback.   
    
- **Key Takeaway:** This project provides the _best architectural model_ for the tool. The "adapter" pattern it employs is the explicit, modular solution to the data normalization challenge (Section 3.3). Its "blending" algorithm is the same aggregation logic required for the final calculation (Section 3.4).
    

### Case Study 4: `Ghostfolio`

`Portfolio Performance`

- **Methodology:** These are two of the most popular, full-featured, open-source portfolio tracking applications. An examination of their documentation reveals their primary data sources for stock and fund data. `Ghostfolio` explicitly lists `YAHOO` and `COINGECKO`. `Portfolio Performance` also lists Yahoo Finance as a primary price provider.   
    
- **The "True Exposure" Gap:** This reveals a critical gap in the existing open-source landscape. As established in Section 2.2, any tool relying on Yahoo Finance for fund data is almost certainly _only_ accessing the **Top 10 Holdings**. This means that these popular, sophisticated tools are likely _incapable_ of performing the deep, recursive, "true company exposure" calculation that this project is designed for. They are excellent portfolio trackers, but they do not solve this specific look-through problem. This is not a criticism, but a _major validation of the project's value_. The tool to be built is not "rebuilding the wheel"; it is building a tool with a specific, advanced feature (deep, recursive, _complete_ look-through) that appears to be missing from the current open-source ecosystem.   
    

## Part 5: Concluding Recommendations and Strategic Blueprint

  

Based on the preceding analysis, a clear, actionable blueprint emerges for successfully building the "true company exposure" engine while adhering to the "free" constraint.

1. **Reject Freemium APIs for Holdings Data:** Do not attempt to build the tool's core function on the free tiers of Alpha Vantage, Finnhub, or EODHD. The analysis confirms they are a "dead end," as they all paywall the _complete_ constituent data required for the project.   
    
2. **Adopt a Hybrid Scraping Strategy:** The tool's data layer must be hybrid to ensure both timeliness and robustness.
    
    - **Primary Source:** Implement **Bespoke Issuer Scrapers** (Strategy 1). This provides the most timely (daily/monthly) data. The first priorities should be scrapers for iShares (targets CSVs), SPDR (targets XLSXs), and Vanguard (targets HTML tables).   
        
    - **Fallback Source:** Implement the **SEC EDGAR NPORT-P Scraper** (Strategy 3). This provides a robust, standardized (but quarterly) fallback for any ETF for which a bespoke scraper has not been written. The tool's logic should automatically use this source if the primary scraper fails.   
        
    - **Advanced Fallback:** For further robustness, implement the **Morningstar "Concealed API" Scraper** (Strategy 2) as a powerful, non-issuer-specific alternative.   
        
3. **Build a Modular "Adapter" Architecture:** Do not mix scraping logic with business logic. Adopt the "adapter" pattern from the `etf4u` project. The core logic should call a single function (e.g., `data.get_holdings(ticker)`), and the adapter module should be responsible for routing to the correct scraper and, most importantly, _normalizing the data_ into a standard internal format.   
    
4. **Solve the Identifier Problem Centrally:** This is non-negotiable. The tool _must_ integrate the **OpenFIGI API**  as a core, centralized service. All scraped data (CUSIPs, ISINs, etc.) must be passed through a normalization function that calls this API to map all holdings to a single, common identifier (e.g., Ticker or FIGI). This is the only way to ensure `037833100` from a Vanguard file is correctly aggregated with `AAPL` from an iShares file.   
    
5. **Implement the Core Quantitative Logic:** The tool's unique value will be two functions:
    
    - A **recursive look-through function** to handle "ETFs of ETFs" and correctly multiply nested weights (as outlined in Section 3.2).
        
    - An **aggregation function** to calculate the final "true exposure" for each base security by summing the weighted products of all its occurrences across the entire portfolio (as outlined in Section 3.4).
        

This blueprint provides a complete, resilient, and—most importantly—**free** path to building the exact tool envisioned. It navigates the "Free API Fallacy" and provides a robust architectural plan that leverages the proven techniques of other open-source projects, while ultimately creating a tool that fills a significant gap in the current FinTech ecosystem.