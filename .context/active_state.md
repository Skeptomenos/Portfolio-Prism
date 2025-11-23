# 🔴 Active Session State
**Objective:** Phase 6: Reliability & Gap Closure
**Status:** Pending

## 🛡️ Applied Constraints
- [Constraint: Automation] - The solution for iShares ID discovery must not rely on manual JSON editing by the user.
- [Constraint: Data Integrity] - Ticker mapping must be validated by a successful price fetch before being saved.

## 📝 Plan & Progress
- [ ] 1. **iShares Fix:** Implement automated scraping or a better search strategy to find the `product_id` for `DE000A0F5UF5` (and others) without user intervention if possible.
- [ ] 2. **Ticker Map:** Implement the interactive prompt in `market.py` to ask the user for a valid Yahoo ticker when `yfinance` returns 404.
- [ ] 3. **Verify:** Run the full pipeline and ensure the "Value Conservation" loss drops from 2.6% to near 0%.

## 🧠 Context & Learnings
*   **Dashboard Insights:** The new dashboard clearly shows the "Data Funnel" drops. This visibility makes it easier to track the impact of our fixes.
*   **iShares Complexity:** The `product_id` is a hidden internal identifier. We might need to parse the search results page from the iShares website to find it dynamically.