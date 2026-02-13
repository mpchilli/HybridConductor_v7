# Bug Fix Report & Lessons Learnt (Phase 8 Refinements)
**Date**: 2026-01-21
**Version**: v7.1.x -> v7.1.2

## 1. Sidebar Transparency
- **Issue**: Settings and Filter sidebars remained semi-transparent despite adding `background: #0f172a`.
- **Root Cause**: Later CSS overrides (Phase 3 block) were using `background-color: var(--surface-panel)`, which in some legacy themes was semi-transparent. High CSS specificity and `!important` on the wrong properties prevented earlier fixes from working.
- **Solution**: Centralized sidebar overrides in the final CSS block. Forced `#0f172a !important` background and fixed `z-index` to ensure opaque layering above the grid.

## 2. System Log Failure to Expand
- **Issue**: Clicking the status bar footer did not reveal the log panel.
- **Root Cause**: The parent container `#status-bar` had `overflow: hidden`. Since the expansion panel was positioned at `bottom: 100%` (outside the container), it was being clipped.
- **Solution**: Set `#status-bar { overflow: visible !important; }`. This allows children positioned outside the 42px bar to be visible while maintaining the footer's fixed position.

## 3. "Stuck Loading" Metadata Indicator
- **Issue**: Individual cards stayed on "⏳ Metadata importing..." even after worker finished.
- **Root Cause**: 
    1. `metadata-syncer.js` was sending a final `complete` message via a `finally` block that lacked the `worker: 'metadata'` property.
    2. `data-loader.js` logic was failing to clear the `isLoading.metadata = true` flag because of this property mismatch.
    3. Errors in the worker were not clearing the loading state.
- **Solution**: Refactored `metadata-syncer.js` to always send a tagged completion message. Updated `data-loader.js` to clear flags on both `complete` and `error` events.

## 4. Full SSCC Search Failure (20 Digits)
- **Issue**: Searching for full 20-digit SSCCs (including `00` prefix) yielded 0 matches, but partial searches worked.
- **Root Cause**: The SQLite search logic in `db-sqlite.js` had a restricted suffix-matching condition. For queries >= 18 digits, it was only checking the 18-digit suffix against the `filename`, but not against the indexed `sscc_ref` field.
- **Solution**: Broadened the SQL generator in `db-sqlite.js` to check suffix matches against both `filename` and `sscc_ref`. This ensures that even if filenames and metadata vary (18 vs 20 digits), the search remains robust.

---
**Learning**: Always verify `overflow` properties on fixed footer parents when using absolute-positioned fly-outs. Always ensure background workers tag every message with their `worker` identifier to avoid state desync in orchestrator modules.
