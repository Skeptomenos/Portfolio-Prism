# Architectural Decision Log

This log records significant architectural decisions and trade-offs.

## 2025-11-20: Parallel PDF Parsing & Incremental SQLite Loading

### Context
Parsing large Trade Republic PDF exports (200+ pages) was CPU-bound and prohibitively slow (>10 mins). Additionally, the lack of deduplication meant re-running the pipeline required deleting the DB or processing everything from scratch.

### Decision
1.  **Multiprocessing:** We utilized Python's `multiprocessing.Pool` to parallelize page parsing.
    *   **Trade-off:** Increased memory usage (one process per core).
    *   **Constraint:** Used `spawn` safe arguments (file path + page index) instead of passing complex objects.
2.  **Incremental Loading:** We leveraged SQLite as the state store.
    *   `processed_files` table tracks file hashes.
    *   `trades` table uses `UNIQUE` constraints and `INSERT OR IGNORE` to handle overlapping data.
    *   **Trade-off:** Requires database schema management (migrations/init scripts), but significantly improves UX and robustness.

### Consequences
*   **Performance:** 5x-10x speedup on multi-core machines.
*   **UX:** Subsequent runs are instant.
*   **Complexity:** `parser.py` is more complex due to process management, but `setup_db.py` logic is simplified (just call parser).

## 2025-11-20: Adoption of Rust-based Excel Parsing (Calamine)

### Context
Amundi exports malformed `.xlsx` files (invalid XML/styles) that cause the standard `openpyxl` engine to crash. Users were forced to manually convert files to CSV, violating the "Radical Simplicity" principle.

### Decision
We integrated `python-calamine` (a Python binding for the Rust `calamine` library) as a fallback engine in the `AmundiAdapter`.

### Consequences
*   **Robustness:** The system can now read corrupted/non-compliant Excel files that `pandas`/`openpyxl` reject.
*   **Dependencies:** Added `python-calamine` to `requirements.txt`.
*   **UX:** Users can simply download files (even if broken) and the system handles them transparently.