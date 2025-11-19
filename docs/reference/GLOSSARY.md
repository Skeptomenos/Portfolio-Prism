# Glossary

Key terms for the Portfolio Look-Through Analyzer POC.

- **ISIN**: International Securities Identification Number (e.g., IE00B3RBWM25) – unique identifier for securities.
- **Ticker**: Stock symbol (e.g., GOOGL) for trading; mapped from ISIN.
- **Exposure**: Total portfolio value or risk from holdings, including ETF breakdowns.
- **Trade Republic**: Broker platform; PDFs are account statements with transaction tables.
- **PDF Parsing**: Extracting text/data from PDFs using libraries like pdfplumber.
- **ETL**: Extract, Transform, Load – data pipeline process.
- **Validation**: Automated checks for data accuracy (e.g., count matches, field integrity).
- **Reusables**: Patterns/learnings applicable to other projects (e.g., multi-page cropping).
- **OpenFIGI**: API for mapping ISINs to tickers/providers.
- **yfinance**: Library for fetching stock prices (Yahoo Finance data).
- **Selenium**: Library for browser automation; used for JS-heavy scraping (e.g., ETF.com popups).
- **ETF.com**: Aggregator site for ETF holdings data across providers.
- **Phase 1**: Ingestion & Positions – PDF parsing to holdings calculation.
- **Phase 2**: Mapping & Pricing – ISIN to ticker, live prices via APIs.
- **Phase 3**: Holdings Ingestion – ETF composition data.
- **Phase 4**: Aggregation – Combine all for true exposure report.
- **Phase 5**: Final POC Script – Executable console output.