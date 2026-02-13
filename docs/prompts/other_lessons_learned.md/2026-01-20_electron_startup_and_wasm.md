# Post-Mortem: Electron Native Modules & The Startup Loop
**Date:** 2026-01-20
**Context:** PoC Carton Info v7 (Electron/Node/SQLite)

## 1. Executive Summary
The application was prevented from starting by two compounding critical failures:
1.  **Environment Incompatibility:** The requirement for native C++ modules (`better-sqlite3`) clashed with a restricted corporate environment (paths with spaces, no Visual Studio build tools).
2.  **The "Electron Loop":** An attempt to fix the environment led to a broken dependency state where `require('electron')` returned a file path string instead of the API object, causing a crash at `app.disableHardwareAcceleration()`.

**Final Resolution:**
- **Database:** Migrated to `sql.js` (WASM), removing all native compilation requirements.
- **Runtime:** Restored strict npm-based execution (`electron .`) to resolve internal module shadowing.

---

## 2. Root Cause Analysis

### A. The Native Module Block
The original database driver, `better-sqlite3`, is a native Node.js module. It requires `node-gyp` and a C++ compiler (Visual Studio Build Tools) to link against the specific Electron ABI (Application Binary Interface).
*   **Constraint 1:** The project path `.../Ai Tools/...` contained spaces. `node-gyp` historically struggles with unescaped spaces in paths.
*   **Constraint 2:** The host machine lacked the necessary C++ build chain.
*   **Result:** `npm install` and `electron-rebuild` failed repeatedly.

### B. The "Electron Loop" (Module Shadowing)
To run Electron, the `electron` npm package must be listed in `devDependencies`. This package contains a binary (`electron.exe`) and a small Node.js wrapper.
*   **The Trap:** When running a script via `node electron-main.js`, Node's module resolution finds the `electron` folder in `node_modules`. The `package.json` of that folder points to `index.js`, which exports the *path* to the executable (a string).
*   **The Expectation:** When running inside the *Electron Runtime*, `require('electron')` is supposed to trigger a special internal loader that returns the API object (`{ app, BrowserWindow, ... }`).
*   **The Failure:** By interacting with the package in unusual ways (custom runners, direct execution queries), we inadvertently created a scenario where the "External Pkg" shadowed the "Internal API".
*   **Symptom:** `TypeError: Cannot read properties of undefined (reading 'disableHardwareAcceleration')`.

---

## 3. Explored Avenues & Results

### ❌ Attempt 1: Native Rebuilds
*   **Action:** Tried `electron-rebuild`, `npm rebuild`, and isolated builds in temp folders.
*   **Result:** FAIL. Windows permission errors (`EPERM`) and path parsing errors persisted.
*   **Lesson:** Fighting the environment in a restricted corporate setting is a losing battle. "Portable" means "Pure JS/WASM".

### ❌ Attempt 2: Custom "Shadow" Runner
*   **Action:** Renamed the `electron` package to `electron_shadow` and wrote a custom `child_process.spawn` script to launch it.
*   **Intent:** To force Node to ignore the package lookup while still having the binary.
*   **Result:** FAIL. Extremely brittle. Caused `ICU` data errors (crashes) because the binary expects resources at specific relative paths which were broken by the rename.

### ❌ Attempt 3: Direct Binary Invocation
*   **Action:** Ran `.\node_modules\electron\dist\electron.exe .` directly.
*   **Result:** FAIL (initially). It still picked up the wrong module scope because of residual `package.json` config settings (`main` pointing to the wrong place) or environment variables `ELECTRON_RUN_AS_NODE`.

### ✅ Attempt 4: The Clean Slate (WASM + Standard CLI)
*   **Action (DB):** Replaced `better-sqlite3` with `sql.js`. This is a pure WebAssembly compilation of SQLite. It runs anywhere Node.js runs.
    *   *Trade-off:* It's in-memory only.
    *   *Fix:* Added a `persist()` method to flush the memory buffer to disk asynchronously.
*   **Action (Runtime):** Wiped `node_modules`, cleanly reinstalled `electron`, and reverted to the standard `npm start` script (`"start": "electron ."`).
*   **Result:** SUCCESS. The standard CLI wrapper correctly configures the environment variables to ensure `require('electron')` hits the internal API.

---

## 4. Retrospective: The "Golden Path" Diagnosis

If this happens again, here is the optimal troubleshooting route:

1.  **The "Type Check" First:**
    Instead of guessing why `app` is undefined, immediately log this at the top of `main.js`:
    ```javascript
    const electron = require('electron');
    console.log('TYPE:', typeof electron); // If 'string' -> YOU ARE SHADOWED.
    ```

2.  **Environment Check:**
    Check `process.env.ELECTRON_RUN_AS_NODE`. If this is set, Electron ignores its internal API and acts like standard Node. This is often the culprit when tools spawn Electron subprocesses.

3.  **The Architecture Rule:**
    *   **Rule:** **NEVER** import `electron` in a Worker thread (`worker_threads` or `child_process`).
    *   **Why:** Workers run in a standard Node context (usually). Importing `electron` there will almost always resolve to the npm package (the string path), causing confusing errors or spawning unwanted child windows.
    *   **Fix:** Use "Pure Node" workers that communicate purely via IPC (messages).

4.  **The "Portable" Mandate:**
    For warehouse/corporate tools where you cannot control the OS image:
    *   **Avoid:** Native Modules (`.node`, `better-sqlite3`, `sharp`).
    *   **Prefer:** WASM replacements (`sql.js`, `@surma/png`).
    *   *Why:* It eliminates an entire class of "it works on my machine" build errors.
