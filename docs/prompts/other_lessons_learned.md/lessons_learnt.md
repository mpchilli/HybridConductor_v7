# Lessons Learnt & Integration Logs

## Debugging Log: LoopsManager & Ralph CLI Bridge Integration
**Date:** 2026-02-10
**Component:** Ralph Orchestrator (Backend)
**Issue:** LoopsManager failing to spawn `ralph` process (ENOENT, EINVAL, unrecognized command)

### Synopsis
The backend server's `LoopsManager` and `PlanningService` were configured to spawn a `ralph` command, expecting a Rust-compiled binary on the system PATH. However, the project had transitioned to a Python-based coordinator (`bridge.py`) invoked via `ralph.cmd` in the repository root. This mismatch caused repeated process crashes.

We iteratively debugged and fixed the integration to allow the Node.js backend to successfully control the Python coordinator on Windows.

### Trial & Error Log

#### 1. Initial Error Investigation
- **Trial:** Analyzed terminal output showing `Error: spawn ralph ENOENT`.
- **Finding:** The server was trying to execute `ralph` directly, but no such binary existed in the PATH. The repository uses `ralph.cmd` as a wrapper.
- **Lesson:** Always verify the existence and location of external binaries when migrating between project structures (Rust -> Python).

#### 2. Bridge Implementation
- **Trial:** Updated `coordinator/bridge.py` to handle CLI arguments.
- **Action:** Expanded the script from a simple file-trigger loop to a full CLI entrypoint supporting `loops`, `run`, `list`, etc.
- **Result:** The Python script can now accept the subcommands that `LoopsManager` sends (e.g., `ralph loops process`), acting as a drop-in replacement.
- **Lesson:** When replacing a component, the new implementation must satisfy the existing interface (CLI arguments) to avoid breaking dependent services.

#### 3. Path Configuration
- **Trial:** Updated `backend/.../serve.ts` to point to the absolute path of `ralph.cmd` instead of assuming "ralph" is on the PATH.
- **Action:** Defined `RALPH_CLI_PATH` resolving to the repo root's `ralph.cmd`.
- **Result:** `ENOENT` error resolved, but replaced by `EINVAL` on Windows.
- **Lesson:** Hardcoded command strings ("ralph") are fragile. Always use absolute paths for project-local executables.

#### 4. Windows Process Spawning Fixes
- **Trial:** Attempted to fix `EINVAL` by adding `{ shell: true }` to the `spawn` options in `LoopsManager.ts`.
- **Finding:** This fixed `EINVAL`, but caused a new error: `'C:\Users\...\Ai' is not recognized`. The path contained spaces ("Ai Tools"), and the shell was splitting the command incorrectly.
- **Lesson:** On Windows, `shell: true` is often required for `.cmd/.bat` files, but it introduces argument parsing hazards.

#### 5. Final Fix - Quoting Paths
- **Trial:** Modified `LoopsManager.ts` and `PlanningService.ts` to wrap the command path in quotes when on Windows.
- **Code Change:** `const command = process.platform === "win32" ? "\"${this.ralphPath}\"" : this.ralphPath;`
- **Result:** success! The server now successfully spawns the Python coordinator, and "Merge queue processed successfully" logs confirm stability.
- **Lesson:** Always quote file paths when executing shell commands, especially on Windows where spaces in directory names (e.g., "Program Files", "Ai Tools") are common.

### Summary of Changes

| File | Change |
|---|---|
| `coordinator/bridge.py` | Implemented CLI command handling to mock the original Rust binary. |
| `serve.ts` | Configured `LoopsManager` and `PlanningService` to use the local `ralph.cmd`. |
| `LoopsManager.ts` | Added Windows-specific spawn logic (shell: true + path quoting). |
| `PlanningService.ts` | Added Windows-specific spawn logic (shell: true + path quoting). |

---

## Issue Log

### [ISSUE]: spawn ralph ENOENT on Windows
**Date:** 2026-02-10
**Description:** The Ralph Orchestrator backend (Node.js) failed to launch the Python Coordinator bridge. It attempted to spawn `ralph` without a file extension and without a shell on Windows, resulting in an `ENOENT` error.

**[FIX]:**
1. Updated `backend/ralph-web-server/src/serve.ts` to use the absolute path to `ralph.cmd` (`RALPH_CLI_PATH`).
2. Updated `backend/ralph-web-server/src/runner/ProcessSupervisor.ts` to include `{ shell: true }` when spawning processes on Windows. This is required for executing `.cmd` files.
3. Verified the fix using a standalone test script `scripts/test-ralph-spawn.js`.

**[LESSON]:**
On Windows, `child_process.spawn` cannot execute `.cmd` or `.bat` files directly unless they are in the PATH and `shell: true` is specified. Always use absolute paths for critical system binaries and ensure shell execution is enabled for batch script wrappers on Windows.

---

## Audit Remediation [2026-02-10]

**Context:** An external audit (critic_analysis_v2.md) compared the codebase against the original spec (project_goals.md) and found significant deviations introduced during V2 refactoring.

### Corrections Applied

| File | Issue | Fix |
|:---|:---|:---|
| `coordinator/llm.py` | Signature drift: `generate(prompt, model_name, system_instruction)` | Reverted to spec's `generate(prompt, role="executor")` |
| `coordinator/llm.py` | Feature creep: budget tracking, `generate_with_planner`, `see_and_critique` | Removed — not in spec |
| `coordinator/llm.py` | Vision used `genai.upload_file()` | Replaced with inline `{'mime_type', 'data'}` per spec |
| `coordinator/safety.py` | `update_badge(status, **kwargs)` | Reverted to spec's `update_badge(task_id, status, message)` |
| `coordinator/safety.py` | Feature creep: `validate_path()`, datetime, project_root | Removed — not in spec |
| `coordinator/loop.py` | Architecture: TDD phases, Ambiguity Traps, Captain Consultation, `run_all()` | Replaced with spec's `run_cycle(task_id)` single-entry flow |
| `coordinator/loop.py` | Feature creep: `select_hat`, `consult_captain`, `AmbiguityException` | Removed — not in spec |

**[LESSON]:**
When implementing production logic, always cross-reference against the original spec before adding features. V2 innovations (TDD, Ambiguity Traps) were valuable but introduced signature drift that broke spec-compliance. Features should be added as documented extension layers, not as modifications to spec-mandated interfaces.

---

## Deployment Log: Ralph-Coordinator Integration
**Date:** 2026-02-10
**Component:** Ralph Coordinator (Frontend/Backend)
**Issue:** Usage of `WebSocket` in Vite and environment variable loading in Python

### Issues & Fixes

#### 1. Vite & Node.js Version Compatibility
- **Issue:** `npm run dev:web` failed with `ReferenceError: WebSocket is not defined`.
- **Cause:** The project is running on Node.js v20.20.0, but the installed version of Vite expects `WebSocket` to be available in the global scope (Standard in Node v22+, but not v20 without flag).
- **Fix:** Installed `ws` package and created `frontend/ralph-web/shims.js` to polyfill `global.WebSocket`. Updated `package.json` to load this shim using `node --import`.

#### 2. Vite Binary Hoisting
- **Issue:** `npm run dev` failed with `ERR_MODULE_NOT_FOUND` for `vite.js`.
- **Cause:** `npm` hoisted `vite` to the root `node_modules`, but the script in `frontend/ralph-web/package.json` hardcoded the path to `./node_modules`.
- **Fix:** Updated the dev script to point to `../../node_modules/vite/bin/vite.js`.

#### 3. Python Backend Environment Variables
- **Issue:** Backend API endpoints returned 500 errors; logs showed `CRITICAL: GEMINI_API_KEY is missing from environment`.
- **Cause:** The `coordinator/llm.py` script relied on `os.environ`, but the executing environment (spawned by Node.js or `cmd`) did not automatically propagate the `.env` file values from the root.
- **Fix:** Updated `coordinator/llm.py` to manually parse and load the `.env` file from the project root if the API key is missing.

#### 4. Backend Process Stale State
- **Issue:** Retrying the UI test after the Python fix still resulted in 500 errors.
- **Cause:** The Node.js backend (`npm run start:server`) spawns the Python process. Changing the Python source code does not automatically restart the *already running* process if it was loaded into memory or if the Node server holds a persistent reference.
- **Action:** Terminated and restarted `npm run start:server` to force a fresh spawn of the Python coordinator with the new code.

### Backend Process Management (Feb 10, 2026)
- **Problem**: `spawn ralph ENOENT` error persists even with absolute paths in `serve.ts`.
- **Root Cause**: The backend was running from `dist/serve.js` (compiled), while fixes were applied to `src/serve.ts`. The build step was required to propagate changes.
- **Fix**: Run `npm run build -w @ralph-web/server` AFTER modifying `src` files. 
- **Critical Note**: `path.resolve` behavior in `dist` vs `src` can differ if `REPO_ROOT` calculation relies on `__dirname`. Always verify `__dirname` depth in compiled output.

### TRPC & Bridge Communication (Feb 10, 2026)
- **Problem**: Backend crashed with `TRPC Error on loops.list: TypeError: loops.filter is not a function`.
- **Root Cause**: Mismatch in data structure. `bridge.py` returned `{ "loops": [...] }` (object), but the backend's TRPC handler expected a raw array `[...]` to map/filter over.
- **Fix**: Updated `bridge.py` to return the list directly: `print(json.dumps([...]))`.
- **Lesson**: Ensure the Python bridge output exactly matches the TypeScript interface expectations.

### TypeScript Build Errors (Feb 10, 2026)
- **Problem**: `TS2448: Block-scoped variable 'RALPH_CLI_PATH' used before its declaration`.
- **Cause**: Variable was defined after its usage in `serve.ts` due to reordering/editing.
- **Fix**: Moved constant definitions to the top of the file.

### E2E Verification
- **Success**: Confirmed `task.create` now works via UI.
- **Artifact**: `successful_task_submission` screenshot verifies the fix.



* v0.1.0-test (2026-02-10):
    - **[Test Coverage] Full Test Matrix for Offline Electron App**:
        - **Unit Testing Layer**: **Vitest** + **React Testing Library** configuration with **mock-fs** isolation patterns for all filesystem-dependent modules (settings, cache, user data). Include concrete example for **writeUserData()** service testing with virtual filesystem verification.
        - **E2E Testing Layer**: **Playwright** + **playwright-electron** configuration for visible-window testing (NO headless/Xvfb). Demonstrate safe filesystem write test using isolated **.test-data** directory with **path.join(process.cwd(), '.test-data')** pattern. Include cleanup hooks to prevent test pollution.
        - **Windows-Specific Safeguards**: Explicit handling of Windows path separators (**\\** vs **/**), **UAC** virtualization avoidance via **%LOCALAPPDATA%** fallback detection, and anti-ransomware folder exclusion patterns for test directories.
        - **[Configuration Warning]**: **NEVER** test against real user directories (**%APPDATA%**, **Documents**). Always isolate to project-local **.test-data/** with pre-test directory creation and post-test cleanup. Windows Defender may quarantine rapid FS writes without this isolation.
    - **[Test Fix] Resolve Windows Path Normalization Failures**:
        - **Path Consistency**: Implemented **path.win32.normalize()** wrapper for all filesystem operations in test harness to prevent **C:\\test\\file.json** vs **C:/test/file.json** mismatches that break snapshot testing on Windows.
        - **Case Sensitivity**: Added case-insensitive path assertions using **expect(path1.toLowerCase()).toBe(path2.toLowerCase())** to accommodate **NTFS** case preservation quirks.
    - **[Test Optimization] Zero-Dependency Test Execution**:
        - **Offline-First Setup**: All test dependencies (**playwright-electron** binaries, **Vitest**) must be pre-downloaded during **npm install --offline**. Include **npm config set offline true** in setup instructions.
        - **No Admin Rights Verification**: Test harness must validate write permissions to **.test-data** BEFORE execution using **fs.accessSync(path, fs.constants.W_OK)** with graceful fallback to user-chosen directory.

### Test Execution Report (2026-02-10)
- **Unit Tests**: Passed. Verified **mock-fs** isolation for virtual filesystem operations.
    - **Note**: Resolved `mock-fs` initialization error by using relative paths for directory mocking.
- **E2E Tests**: Passed. Verified isolated **.test-data/** creation, write operations, and post-test cleanup using **Playwright**.
    - **Note**: Confirmed **path.win32** compatibility on Windows 11.
- **Environment**: Node.js v20.20.0, Vitest v3.2.4, Playwright v1.58.0.
