# LLM Fallback Plan for Asset Normalization

**Objective:** Provide a robust fallback mechanism for cleaning asset names when deterministic methods (Yahoo Finance ISIN lookup) fail. This ensures that even obscure assets or those with missing ISINs have clean, readable names in the dashboard.

## 1. Architecture

The normalization pipeline will follow a "Waterfall" approach:

1.  **Cache Hit:** Check `config/asset_names.json`. If found, use it.
2.  **Primary (Yahoo):** Query Yahoo Finance by ISIN. If valid name returned, use it and cache.
3.  **Secondary (LLM):** If Yahoo fails or ISIN is missing, call an LLM with the raw polluted string.
4.  **Heuristic Fallback (Safety Net):** If LLM fails (no key/offline), use aggressive Regex cleaning.

## 2. The LLM Component

### 2.1. Integration Point
We will create a dedicated function `fetch_name_llm(raw_text)` in `src/data/normalization.py`.

### 2.2. Prompt Design
The prompt must be strictly defined to output *only* the name, minimizing hallucination.

**System Prompt:**
"You are a financial data cleaning assistant. Your job is to extract the official company or ETF name from a polluted transaction string. Remove price data, dates, transaction IDs, and currency symbols. Return ONLY the clean name."

**Examples:**
*   Input: `-38,94 ALPHABET INC.CL.A DL-,001 3411422620220916 KW`
    *   Output: `Alphabet Inc. Class A`
*   Input: `Buy trade DE0007030009 10,00 € 4.282,79 RHEINMETALL AG`
    *   Output: `Rheinmetall AG`
*   Input: `ISHSVII- 40,00 € 595,56 NASDAQ 100 EOHACC`
    *   Output: `iShares NASDAQ 100 UCITS ETF`

### 2.3. Client Selection
*   **Project Standard:** Use the same client structure as the rest of the project (e.g., OpenAI or Google Generative AI SDK).
*   **Configuration:** Read API key from environment variables (`OPENAI_API_KEY` or `GEMINI_API_KEY`).

## 3. Implementation Steps

### Step 1: Setup LLM Client
*   Verify if `src/utils/llm_client.py` exists. If not, create a simple wrapper for the API call.
*   Ensure `.env` loading is handled.

### Step 2: Implement `fetch_name_llm`
*   Construct the prompt.
*   Call the API.
*   Sanitize the output (strip quotes/newlines).

### Step 3: Integration Test
*   Create a script `debug/test_llm_normalization.py` to run sample strings through the LLM function and verify output quality.

## 4. Cost & Latency Management
*   **Batching:** Not necessary for this scale (<50 assets). Individual calls are fine.
*   **Caching:** CRITICAL. The LLM result *must* be saved to `config/asset_names.json` to avoid repeated costs/latency on every run.

## 5. Risks & Mitigation
*   **Hallucination:** The LLM might invent a name.
    *   *Mitigation:* The prompt examples will guide it. We can also cross-reference with the ISIN if available (fuzzy match).
*   **API Failure:**
    *   *Mitigation:* Fallback to Heuristic Regex cleaning if the API call errors out.
