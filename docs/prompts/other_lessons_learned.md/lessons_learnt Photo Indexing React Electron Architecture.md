# Lessons Learnt: Photo Indexing & React/Electron Architecture

## 1. State Management: The Perils of Legacy Globals
**Issue:** `useSearch` relied on `window.STATE.settings` (a legacy hybrid bridge) to get the `photoPath`. However, React components often mount before this global is populated, resulting in empty paths and data leakage (showing all photos).
**Lesson:** Never rely on `window` globals for critical state in React. Always use **React Context** (`useSettings`) which guarantees reactive updates and proper initialization.
**Rule:** `const { settings } = useSettings();` > `window.STATE`.

## 2. Data Integrity: Upsert is Not Sync
**Issue:** Exploring a folder added photos to the SQLite DB. Changing folders stopped *adding* old photos, but didn't *remove* them, leaving "orphaned" rows in the view.
**Lesson:** `Upsert` (Insert/Update) only handles presence. You MUST implement **Pruning** (Delete missing) to reflect the true state of the filesystem.
**Mechanism:** 
1. Mark scan start time.
2. Upsert checks.
3. `DELETE FROM photos WHERE last_seen_at < start_time` (Pruning).

## 3. Strict Filtering: Trust No Cache
**Issue:** relyng solely on the indexer to keep the DB clean is risky (race conditions, crashes).
**Lesson:** implement **Strict Filtering** at the Query level.
**Implementation:** `SELECT * FROM photos WHERE path LIKE 'C:\Current\Path%'`. This ensures that even if garbage exists in the DB, the UI *never* shows it.

## 4. The IPC Chain of Responsibility
**Issue:** We updated the Repository and the Main Handler to accept `rootPath`, but forgot the **Preload Script** (`contextBridge`).
**Result:** The argument was dropped silently in the bridge, causing the Main process to receive `undefined`.
**Checklist for IPC Changes:**
1. **React Hook**: Pass arg.
2. **Repository**: Pass arg.
3. **Preload info (Bridge)**: **FORWARD ARG**. (`(a,b,c) => ipcRenderer.invoke(ch, a,b,c)`)
4. **Main (Handler)**: Receive arg.

## 5. Worker Safety
**Issue:** If the indexing worker crashed, `finally` block triggered a "Scan Complete" event, which triggered Pruning.
**Risk:** partial scans could wipe the database.
**Lesson:** Only trigger destructive cleanup (Pruning) on **verified success**. If an error occurs, abort the cleanup.

---
*Generated: 2026-01-23*
