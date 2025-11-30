# The "True Exposure" Engine: A Developer's Comprehensive Guide to Problems, Solutions, and Technical Challenges

## 1. Project Goal: The "True Exposure" Look-Through Engine

The objective of this project is to build a tool that calculates a portfolio's "true company exposure." This is a "look-through" analysis that aggregates the underlying constituents of all Exchange-Traded Funds (ETFs) in a portfolio to reveal the precise, aggregated exposure to individual stocks.

This document serves as a comprehensive summary of the project's core problems, failed paths, viable solution designs, and specific technical challenges.

---

## 2. Part 1: The Core Problem – Data Sourcing

The project's primary and most significant bottleneck is sourcing **complete, accurate, and machine-readable ETF holdings data** for free. The project must acquire the _entire_ list of constituents and their weights for any given ETF, for both U.S. and European-domiciled funds.

### 2.1. Known Limitations, Failures, and Traps

A preliminary analysis reveals several common approaches that will result in project failure.

#### 2.1.1. The "Free API Fallacy"

This is the assumption that a free-tier API exists for this specific high-value data. This is incorrect.

- **Problem:** Freemium data providers (Alpha Vantage, Finnhub, EODHistoricalData) attract developers with free-tier access for basic data (e.g., stock prices).
    
- **Known Failure:** These providers consistently and deliberately place complete, high-value datasets—such as "ETF Holdings"—behind premium paywalls.1
    
- **Limitation:** The free tiers are fundamentally insufficient.
    
    - **Alpha Vantage:** Free tier is limited to 25 API requests per day.4 This is not viable for a tool that must query holdings for multiple ETFs.
        
    - **Finnhub:** The "ETFs Holdings" endpoint is explicitly a **Premium** feature.1
        
    - **EODHistoricalData:** The free plan is limited to 20 calls/day 7 and the "ETFs Fundamentals Data API" only provides the **Top 10 Holdings**, not the complete list.8
        

#### 2.1.2. The "Top 10 Holdings" Trap (Yahoo Finance & `yfinance`)

This is the most common trap for developers and open-source projects.

- **Problem:** Many developers default to using the `yfinance` 10 or `yahooquery` 13 Python libraries, or scrape Yahoo Finance directly.14
    
- **Known Failure:** Yahoo Finance _only_ displays the **Top 10 Holdings** for an ETF on its public web pages.17 The `yfinance` library's `top_holdings` attribute reflects this limitation.11
    
- **Limitation:** A tool built on this data will fail its core mission. It will calculate exposure based on a small fraction of an ETF's actual constituents, giving a dangerously misleading result.
    

#### 2.1.3. The European "Missing Database" Problem

For European (UCITS) ETFs, the challenge is regulatory and structural fragmentation.

- **Problem:** There is no single, centralized, public-access database equivalent to the U.S. SEC EDGAR for all European fund filings.24
    
- **Known Failure:** The regulatory framework is fragmented. Supervision is delegated to **National Competent Authorities (NCAs)** in the fund's country of domicile, which for most ETFs is either Ireland's **Central Bank of Ireland (CBI)** 25 or Luxembourg's **CSSF**.35 These national bodies' websites are primarily statistical portals 40 or registers of _authorized_ firms 27, not public-facing document _archives_ for individual fund reports.47
    

#### 2.1.4. The OAM (Officially Appointed Mechanism) Failure

The country-specific databases that _do_ exist are practically unusable for this project.

- **Problem:** Each EU member state has a national OAM for storing regulated information.50
    
- **Known Failure (Ireland):** The Irish OAM, operated by **Euronext Dublin**, has no public search database for historical filings.54 It is an issuer-facing _filing_ portal (`Euronext Direct`) 57 and a public _live news_ feed.58
    
- **Known Failure (All OAMs):** The OAMs (Luxembourg, Germany, France) 65 are structured around _legal issuing entities_ (e.g., "iShares VII plc" 83), not _financial products_ (e.g., "iShares Core S&P 500 ETF"). An analyst's search for the product by its name or ISIN will fail.69
    

---

### 2.2. Viable Solution Designs for Data Sourcing

A robust tool must be built on a hybrid strategy that targets primary sources.

#### 2.2.1. Solution Design 1: The "Bespoke Adapter" Model (Direct Issuer Scraping)

This is the most effective method for timely, complete data. It is validated by open-source projects like `etf4u` 84 and `baskets`.85

- **Solution:** Build custom web scrapers ("adapters") for each ETF provider's website.86
    
- **Targets & Formats:**
    
    - **iShares (BlackRock):** Provides direct, persistent AJAX URLs that serve complete holdings as a **CSV file**. This is the most reliable target.87
        
    - **State Street (SPDR):** Provides direct, daily-updated **.xlsx (Excel)** file download links for its funds.93
        
    - **Vanguard (U.S.):** Provides a "Portfolio composition file" or **HTML table** on its product pages that contains the complete holdings.100
        
    - **Vanguard (Europe) & Xtrackers (DWS):** These UCITS providers make their **Annual and Semi-Annual Reports (PDFs)** available in their "Literature" or "Reports" sections.105 These PDFs contain the complete "Schedule of Investments," which is the full holdings list.35
        
- **Technical Challenges:**
    
    - Requires a new, bespoke scraper for every provider.
        
    - Scrapers are fragile and will break when provider websites are redesigned.
        
    - Some sites may require advanced libraries like Selenium/Playwright to handle dynamic JavaScript-loaded content.85
        

#### 2.2.2. Solution Design 2: The "Regulatory Database" Model

This method targets public, mandatory regulatory filings for a more standardized, robust (though less timely) data source.

- **Solution (U.S.):** Scrape the **SEC EDGAR** database.
    
    - **Target File:** **Form NPORT-P**, a public, quarterly report containing the fund's complete portfolio holdings.134
        
    - **Methodology:** This is a proven solution, as demonstrated by the `ETFConstituentExtractor` project.138 The tool uses the ETF's CIK (Central Index Key) to query the EDGAR API, finds all NPORT-P filings, and then scrapes/parses the holdings data from those files.139
        
- **Solution (Europe):** The **European Single Access Point (ESAP)**.
    
    - **Status:** ESAP is the official "EU EDGAR" and is _in development_.142
        
    - **Known Limitation:** This is a _future_ solution. The platform is expected to be operational by mid-2027.50 Critically, data from the **UCITS Directive** (which governs ETFs) is not scheduled for inclusion until **Phase 2, beginning 10 January 2028**.144 This solution is not viable for the project today.
        

#### 2.2.3. Solution Design 3: The "Concealed API" (Advanced)

This is a high-skill/high-reward method for scraping aggregator portals that appear to be protected.

- **Solution:** Scrape data-rich portals like **Morningstar**.155
    
- **Methodology:** Simple scraping fails because data is loaded dynamically.133 The solution is to:
    
    1. Use browser developer tools ("Inspect" $\rightarrow$ "Network") to "sniff" the internal API calls the website's front-end uses to populate its own tables.156
        
    2. Identify the API call returning the holdings data as clean JSON.156
        
    3. Automate this process using a headless browser (like Playwright) to load the page, intercept the request, and extract the dynamic **"Bearer Token"** from the `Authorization` header.157
        
    4. Use this token to make direct, authenticated calls to the concealed API from a Python script.157
        

---

## 3. Part 2: The Data Engineering & Aggregation Problem

Sourcing the data is only the first half of the project. The raw data will be heterogeneous, dirty, and require significant processing to become usable.

### 3.1. Problem: Identifier Mapping (Symbology)

- **Challenge:** The scraped data will contain a mix of identifiers for the same asset: CUSIPs (from U.S. filings) 161, ISINs (from European filings), and Tickers (from various sources). The tool will incorrectly treat `037833100` (Apple CUSIP) and `AAPL` (Apple Ticker) as two different companies, making aggregation impossible.161
    
- **Solution Design:** Implement a central "normalization" service that maps all identifiers to one single, global, persistent ID.
    
- **Recommended Tool:** The **OpenFIGI API**.
    
    - **Why:** It is free, open-source (MIT license), and built for this exact high-volume, programmatic use case.161
        
    - **Generous Free Tier:** The rate limit is 25 requests per _6 seconds_, which is vastly superior to the 25 _per day_ limits of freemium data APIs.169
        
- **Alternatives (Not Recommended):** Other mapping APIs exist (e.g., EODHD 172, sec-api.io 173, FactSet 174, CUSIP 175) but are either paywalled or have highly restrictive free tiers.
    

### 3.2. Problem: Recursive "Look-Through" (ETFs of ETFs)

- **Challenge:** The tool cannot assume a "one-level-deep" look-through. A user may hold an "Asset Allocation ETF" that holds _no stocks_ directly, but is composed of 60% `ETF_B` and 40% `ETF_C`. The tool must be able to recursively "un-nest" these holdings.176
    
- **Solution Design:** A **recursive bisection algorithm**.183 The core aggregation logic must:
    
    1. Iterate through a portfolio's holdings.
        
    2. For each holding, check if it is a base security (e.g., a stock) or another ETF.
        
    3. If it is a base security, add its weight to the final list.
        
    4. If it is an ETF, the function must **call itself** on that ETF's holdings, passing down the new proportional weight to be multiplied.
        

### 3.3. Problem: Final Calculation & Data Aggregation

- **Challenge:** Calculating the final "true exposure" for a single stock across the entire portfolio.
    
- **Solution Design:** A **sum of weighted products**. The core calculation, as demonstrated by the `baskets` project 85 and Intrinio's methodology 140, is:
    
    - `True_Exposure_Stock_X = (Portfolio_Weight_ETF_A * ETF_A_Weight_Stock_X) + (Portfolio_Weight_ETF_B * ETF_B_Weight_Stock_X) +...`
        
- **Technical Implementation:**
    
    1. For each ETF in the portfolio, retrieve its holdings and create a DataFrame.
        
    2. Create a new column `final_weight` by multiplying the holding's weight (`ETF_A_Weight_Stock_X`) by the portfolio's allocation to that ETF (`Portfolio_Weight_ETF_A`).140
        
    3. Concatenate all these individual DataFrames into one large master DataFrame.
        
    4. Use a `groupby()` on the _normalized stock identifier_ (from OpenFIGI) and `sum()` the `final_weight` column.140 This final summed value is the "true exposure."
        

### 3.4. Problem: System Architecture & Data Heterogeneity

- **Challenge:** The tool must ingest CSVs 87, XLSXs 95, HTML tables 101, and parsed PDFs 118 from dozens of sources. This creates a high risk of disjointed, unmanageable code.186
    
- **Solution Design:** The **"Adapter" Design Pattern**, as demonstrated by the `etf4u` project.84
    
    - **Architecture:** The core aggregation logic (Part 3.3) must be decoupled from the data sourcing logic (Part 2.2).
        
    - **Implementation:** The main logic calls a single function (e.g., `data.get_holdings('SPY')`). This function acts as a "router," consulting an internal map to determine which **bespoke adapter** (e.g., `spdr_scraper.py`) to call.
        
    - **Normalization:** Each adapter (e.g., `ishares_adapter.py`, `sec_edgar_adapter.py`) is responsible for its own scraping _and_ for normalizing its unique output into a **standard internal data format** (e.g., `{'identifier': '037833100', 'id_type': 'CUSIP', 'weight': 0.0704}`) before returning it. This makes the system modular, maintainable, and extensible.
        

---

## 4. Summary & Recommended Project Blueprint

The analysis of all known problems and solutions reveals a clear, resilient, and free architecture.

1. **Data Sourcing Layer (Hybrid "Adapter" Model):**
    
    - **Primary Strategy:** Build **Bespoke Issuer Scrapers** (Solution 2.2.1) to get the most timely (daily/monthly) data from iShares, SPDR, Vanguard, and Xtrackers websites.
        
    - **U.S. Fallback:** Build a **SEC EDGAR NPORT-P Scraper** (Solution 2.2.2) for robust, standardized (but quarterly) data for any U.S. ETF.
        
    - **EU Fallback:** Build **PDF Scrapers** for the Annual/Semi-Annual reports (Solution 2.2.1) from provider websites. This is the only reliable method for UCITS funds today.
        
    - **Advanced Fallback:** Implement the **Morningstar "Concealed API" Scraper** (Solution 2.2.3) as a non-issuer-specific alternative.
        
    - **DO NOT USE:** Free-tier APIs or `yfinance`.
        
2. **Normalization Layer (Centralized Mapping):**
    
    - Integrate the **OpenFIGI API** (Problem 3.1) as a core, centralized service.
        
    - All scraped holdings, regardless of source, must be passed through this layer to map CUSIPs, ISINs, etc., to a single common identifier (e.g., Ticker or FIGI) before aggregation.
        
3. **Aggregation Layer (Recursive Logic):**
    
    - Implement a **recursive bisection algorithm** (Problem 3.2) to correctly handle the "ETFs of ETFs" nested look-through.
        
    - Implement the final **sum-of-weighted-products** calculation (Problem 3.3) to aggregate all exposures and deliver the final "true" portfolio weights for each base security.


# Chat response

Yes, this is a well-defined problem that several open-source projects and developers have attempted to solve. Analyzing their work provides a clear blueprint of the common challenges and the most effective solutions.

Based on my research, here is what we can learn from similar projects and technical analyses.

### The "Top 10" vs. "Complete" Data Trap

The most common mistake, and the most important lesson from existing projects, is the "Top 10" holdings trap.

- **The Problem:** Many popular financial data libraries, most notably `yfinance` and `yahooquery`, are used by default in open-source portfolio trackers like `Ghostfolio` 1 and `Portfolio Performance`.2 However, these libraries are pulling from Yahoo Finance's public web pages, which _only_ list the top 10 holdings for any given ETF.3
    
- **The Lesson:** A tool built to calculate "true exposure" _cannot_ use these sources, as it would be basing its entire analysis on a tiny, incomplete fraction of the fund's data. Developer discussions repeatedly confirm this limitation.3
    

Successful projects have learned this and instead employ more robust, direct-sourcing methods.

### Solution 1: The "Bespoke Adapter" Model (Direct Issuer Scraping)

This is the most common and effective strategy for gathering timely, complete data. The solution is to build "adapters"—scrapers custom-built for each ETF issuer's website.

- **`etf4u` Project** 10: This Python tool is designed to scrape ETF information and "proportionally distribute their assets' allocation".10 Its key architectural lesson is the use of "bespoke adapters." It maintains a folder of small scripts, each one designed to parse the specific holdings page of a particular fund provider.10
    
- **`baskets` Project** 11: This project's goal is identical to yours: "reconstruct the dollar amount exposure to each constituent stock".11 Its methodology explicitly relies on scraping the ETF issuer's web pages directly and requires libraries like `selenium` to handle modern, JavaScript-heavy sites.11
    
- **`ETF-Scraper` Project** 12: This library queries provider websites directly for holdings data, noting the differences between them (e.g., iShares provides historical data, while SSGA and Invesco only provide the latest holdings).12
    
- **Technical Blogs (How-To):** Developer forums are filled with examples of this. One Stack Overflow post provides a complete Python script for programmatically downloading the daily `.xlsx` (Excel) file for all SPDR Sector ETFs from State Street's website.13 Another shows how to get the complete iShares CSV holdings file with a single line of code.14
    

### Solution 2: The "Regulatory Database" Model (SEC EDGAR)

This is the most robust and standardized solution, particularly for U.S.-domiciled funds. The methodology is to scrape the public regulatory database, which is the U.S. equivalent of the European national databases you are investigating.

- **`ETFConstituentExtractor` Project** 17: This is a purpose-built tool for exactly this task. Its methodology is a clear lesson:
    
    1. It takes an ETF's CIK (Central Index Key) as input.
        
    2. It uses the SEC's EDGAR API to find all **NPORT-P filings** for that fund. These are the mandatory, public, quarterly reports that contain the _complete_ list of portfolio holdings.18
        
    3. It then scrapes and parses the holdings data from those filings and saves it to a CSV.18
        
- **`sec-edgar-api` Project** 22: This is another open-source Python wrapper for the EDGAR API, demonstrating that this is a common foundation for this type of data retrieval.
    

### Solution 3: The "Concealed API" Technique (Advanced Scraping)

This is a more advanced technique for scraping data-rich aggregator portals (like Morningstar) that are designed to be difficult to scrape.

- **Blog Post: "Concealed APIs"** 23: This technical blog post provides a step-by-step guide. The author demonstrates that simple scraping tools fail on Morningstar's dynamic pages.24 The solution is:
    
    1. Use the browser's "Inspect -> Network" tab to "sniff" the internal, concealed API calls the website's own front-end uses to get its data.25
        
    2. Identify the API call (e.g., to `api-global.morningstar.com`) that returns the holdings data as clean JSON.25
        
    3. Automate the process of getting the "bearer token" (an authentication key) from the browser's request headers using a headless browser library like `Playwright`.23
        
    4. Use this token to make direct, authenticated calls to the concealed API from a Python script.23
        

### Core Challenge 1: The "Identifier Mapping" Problem

The research reveals a critical challenge _after_ scraping: you will have a mix of CUSIPs, ISINs, and Tickers, and you need to map them to a single common identifier to aggregate them correctly.26

- **The Solution: `OpenFIGI`**.26 This is the consensus solution. It is a free, open, and MIT-licensed API specifically designed to map between various financial identifiers.29 It has a generous free rate limit (25 requests per 6 seconds, far better than most free financial APIs) and is built for this exact "Rosetta Stone" mapping task.32 Other mapping APIs exist, but OpenFIGI is the most robust, free option.35
    

### Core Challenge 2: The "Look-Through" Aggregation Logic

Once you have the data, you need the logic to perform the "look-through" calculation, especially for "ETFs of ETFs".39

- **The Algorithm:** A technical blog from Intrinio clearly describes the algorithm 42:
    
    1. For each ETF in your portfolio, get its holdings and weights.
        
    2. Multiply each holding's weight by your portfolio's allocation to that ETF (e.g., if you have 10% in `ETF_A` and `ETF_A` is 5% Apple, your true exposure is 0.10 * 0.05 = 0.5% Apple).
        
    3. Concatenate all these calculated DataFrames into one large table.
        
    4. Use a `groupby()` on the constituent ticker (or CUSIP/FIGI) and `sum()` the weighted allocations. This gives you the final "true exposure" for each individual stock.42
        
- **The Projects:** The `baskets` 11 and `etf4u` 10 projects both implement this aggregation logic to blend the proportional allocations.
    
- **Recursive Logic:** For handling "ETFs of ETFs," several papers on quantitative portfolio allocation (like Hierarchical Risk Parity) describe using a "recursive algorithm" or "recursive bisection" to assign weights top-down 43, which is the correct approach for "un-nesting" a fund that holds other funds.
    

In summary, the open-source community provides a clear path: avoid the "Top 10" data sources, build "bespoke adapters" to scrape issuer sites directly, use a regulatory database (like the national OAMs) as a fallback, solve the identifier mapping problem with OpenFIGI, and then implement a sum-of-products aggregation algorithm.