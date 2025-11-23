# Phase 4 Plan: Roadmap Automation & Feedback Loop [COMPLETE]

**Objective:** Automatically capture user intent for unsupported features (e.g., missing adapters) and convert them into structured backlog items, ensuring the user knows the system "heard" them.

## 1. Architecture: The "Feature Gap" Detector

We will enhance the `AdapterRegistry` to distinguish between "Unknown Provider" (configuration error) and "Unimplemented Provider" (feature gap).

### Components:
1.  **`docs/BACKLOG.md`**: A persistent file to store automated feature requests.
2.  **`src/adapters/registry.py`**: Refactor `get_adapter` to handle missing classes gracefully.
3.  **`scripts/run_pipeline.py`**: Update quality reporting to categorize these skips correctly.

## 2. Implementation Steps

### Step 1: Initialize the Backlog
- Create `docs/BACKLOG.md` with a standard header if it doesn't exist.

### Step 2: Enhance Adapter Registry (`src/adapters/registry.py`)
- **Task:** Modify `get_adapter(isin)`.
- **Logic:**
    - Look up `provider_key` for the ISIN.
    - If `provider_key` exists in config but NOT in `_key_to_class`:
        - This is a **Missing Implementation**.
        - Log a warning.
        - Call `log_feature_request(provider_key)` to append to `BACKLOG.md`.
        - Return `None` (or a special `NotImplementedAdapter` stub?). Returning `None` is simpler for now, but we need to signal *why*.
    - **Refinement:** Return a tuple `(adapter, error_reason)` or throw a specific exception `AdapterNotImplementedError` to let the caller handle it specifically. Let's use a custom Exception.

### Step 3: Handle the "Missing Implementation" Signal
- **Task:** Update `scripts/run_pipeline.py`.
- **Logic:**
    - Catch `AdapterNotImplementedError`.
    - Log it as a "Known Limitation".
    - Add to `failed_etfs` list with reason: "Provider 'Vanguard' not yet implemented. Added to Backlog."

## 3. Verification
- **Test:** Manually map a dummy ISIN to "vanguard" in `adapter_registry.json`.
- **Run:** Execute the pipeline.
- **Check:**
    - Pipeline should not crash.
    - Console should say: "Support for 'vanguard' is not yet implemented."
    - `docs/BACKLOG.md` should have a new entry: "- [ ] Create adapter for provider: 'vanguard' (Requested via ISIN: ...)"
    - `outputs/data_quality_report.txt` should list it as a limitation.
