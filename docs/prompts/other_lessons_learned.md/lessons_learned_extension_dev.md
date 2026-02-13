# Lessons Learned: Gemini Extension Development (Windows & MCP)

This document catalogs critical bugs, configuration errors, and platform-specific quirks encountered during the development and debugging of the `Pro-Rick-GPro` and `gemini-ralph-loop` extensions. 

**Target Audience:** AI Developer / Extension Maintainer
**Context:** Windows 10/11 Environment, Gemini CLI, MCP (Model Context Protocol)

---

## 1. MCP Server Isolation (The "Startup Loop" Bug)

### Problem
The Gemini CLI failed to start with `Cannot start phase 'load_builtin_commands': phase is already active` and `MaxListenersExceededWarning`.

### Root Cause
The `gemini-ralph-loop` extension was configured without an `mcpServers` definition in `gemini-extension.json`. This caused the CLI to load the extension's code **in-process**. The extension's `mcp-server.ts` initialized an `McpServer` and connected it to `process.stdin` / `process.stdout` globally, hijacking the CLI's own communication channels and creating a feedback loop.

### Solution
**Always** run MCP servers as separate processes. Configure them explicitly in `gemini-extension.json`.

**Correct `gemini-extension.json`:**
```json
{
  "name": "gemini-ralph-loop",
  // ...
  "mcpServers": {
    "ralph-loop": {
      "command": "node",
      "args": [
        "${extensionPath}/dist/mcp-server.js"
      ]
    }
  }
}
```

---

## 2. Windows Path Handling in TOML & Prompts

### Problem A: The Double Drive Letter (`C:\C:\Users\...`)
The agent was instructed to run scripts using `${extensionPath}`. On Windows, `${extensionPath}` **already includes** the drive letter (e.g., `C:\Users\...`). The prompt or agent logic was prepending *another* `C:`, resulting in invalid paths like `C:\C:\Users\ukchim01\...`.

### Solution A: The "Single Quote" Strategy (Verified)
In `architect.toml` command definitions for Windows, strict usage of **single quotes** around path variables prevents PowerShell from misinterpreting the drive letter or attempting double-resolution.

**Correct TOML Pattern:**
```toml
# Use single quotes for the script path to handle Windows paths safely
node '${extensionPath}/extension/bin/session-setup.js' $ARGUMENTS
```

*Note: Previous attempts using double quotes (`"${extensionPath}..."`) caused `C:\C:\` errors because the variable expansion combined with PowerShell's path parsing rules created an invalid absolute path.*

### Problem B: TOML Parsing Errors
Configuration files (TOML) failed to parse with `Failed to parse TOML file`. This was caused by using single backslashes in Windows paths within TOML strings (e.g., `'C:\Users'`).

### Solution B: Escape Backslashes
In TOML files, strictly escape all backslashes in path strings.

**Bad:**
```toml
message = "Path: C:\Users\name"
```
**Good:**
```toml
message = "Path: C:\\Users\\name"
```

---

## 3. Persistent State vs. Temporary execution

### Problem
The extension scripts (`update-state.js`) failed with `state.json not found`. The Agent was executing commands in its current working directory, which often defaults to a temporary sandbox (`.gemini/tmp/...`) rather than the persistent session directory created by the setup script.

### Solution
1. **Output the Session Path**: Modify the setup script (`session-setup.js`) to print a recognizable, parseable path to stdout.
   ```javascript
   console.log(`\nDETECTED_SESSION_PATH: ${fullSessionPath}\n`);
   ```
2. **Bind Agent to Path**: In the system prompt/TOML, instruct the Agent to **scrape** this path and use it for all subsequent commands.
   ```toml
   prompt = """
   After setup, **LOOK FOR THE LINE**: `DETECTED_SESSION_PATH: ...`
   **THAT IS YOUR session root**. Use it for `${SESSION_ROOT}`.
   **DO NOT** use `cwd`.
   """
   ```

---

## 4. Missing Scripts & Hallucinated Tools

### Problem
The Agent attempted to run `create-ticket.js`, which did not exist. The error `Cannot find module ...` occurred. This happened because the `SKILL.md` or prompt loosely implied a script existed, or the Agent hallucinated a standard tool pattern.

### Solution
**Verify capabilities before referencing them.**
- If a script doesn't exist, update the **Skill Definition** (`SKILL.md`) to instruct the Agent to use primitive tools instead (e.g., `write_file` to create a markdown ticket manually).
- **Audit `extension/bin`**: Ensure every script referenced in `architect.toml` or `SKILL.md` actually exists in the build output.

---

## 5. Non-Standard Extension Installation URLs

### Problem
Attempting to install extensions using branch or tree URLs (e.g., `https://github.com/owner/repo/tree/branch`) fails with invalid repository source errors or metadata issues.

### Root Cause
The Gemini CLI extension installer expects a standard repository root URL, a GitHub formatted `owner/repo` string, or a specific release tag/zip. Non-standard path structures within the URL are not natively parsed as valid sources.

### Solution
- **Use standard URLs**: Always use `https://github.com/owner/repo` or the shorthand `owner/repo`.
- **Versioning**: Rely on git tags (e.g., `v1.0.0`) and pushes (`git push --tags`) for the installer to recognize stable versions.

---

## 6. Windows-Specific Child Process Spawning (`gemini.cmd`)

### Problem
The extension fails to spawn worker agents on Windows with `spawn ENOENT` or `EINVAL`, despite the `gemini` command being available in the path.

### Root Cause
On Windows, `gemini` is often a shell script (`gemini.cmd`). Node.js's `child_process.spawn` does not automatically resolve `.cmd` or `.ps1` files unless `shell: true` is used, which can have security and performance implications.

### Solution
Detect the platform and explicitly target the `.cmd` wrapper when running on Windows.

**Correct Spawning Logic:**
```javascript
const command = process.platform === 'win32' ? 'gemini.cmd' : 'gemini';
const proc = spawn(command, cmdArgs, {
    cwd: process.cwd(),
    env,
    stdio: ['inherit', 'pipe', 'pipe'],
});
```

---

## 7. Extension Script Integrity & Syntax Errors

### Problem
Agent orchestration fails with `SyntaxError: Unexpected token '}'` in extension scripts (e.g., `spawn-worker.js`), even when the local source looks correct.

### Root Cause
- **Script Corruption**: Duplicate code blocks or broken merge markers during manual edits or high-iteration development.
- **Active Extension Drift**: Updates made in the local workspace directory are not automatically reflected in the active extension directory used by Gemini CLI.

### Solution
1. **Pre-flight Check**: Run `node --check <script>` before committing or reinstalling.
2. **Propagate Changes**: Always uninstall and reinstall the extension locally to ensure the active version is synchronized with your workspace.
   ```bash
   gemini extensions uninstall <ext-name>
   gemini extensions install .
   ```

---

## 8. Extension Name Collisions & Command Hijacking

### Problem
Executing an extension command (e.g., `/architect`) results in `MODULE_NOT_FOUND` errors or attempts to run scripts from an unexpected extension directory (e.g., the agent looks for `extension-A` while the user is working on `extension-B`).

### Root Cause
- **Command Overlap**: Multiple extensions defined with the same command name. The Gemini CLI uses a precedence system where the last installed or lexicographically first extension may "hijack" the command.
- **Shadowing**: If you have two versions of a similar project installed under different names (e.g., `Pro-Rick-GPro` vs `gemini-ralph-loop`), one will overshadow the other. The agent might activate using the manifest of Extension A but try to absolute-path into Extension B, leading to permission or path failures.

### Solution
1. **Audit Extensions**: Run `gemini extensions list` and check for duplicates or "zombie" extensions from previous branches/projects that use the same slash commands.
2. **Standardize Naming**: Ensure your `gemini-extension.json` has a unique and consistent `name`.
3. **Clean Environment**: Uninstall any conflicting extensions before installing the current project.
   ```bash
   gemini extensions uninstall <conflicting-name>
   gemini extensions install .
   ```

---

## 9. Workspace Trust & Path Restrictions (`trustedFolders.json`)

### Problem
Extension-based agents (e.g., AI Architect) fail to write session files, tickets, or state updates with the error: `Path not in workspace: Attempted path "..." resolves outside the allowed workspace directories`.

### Root Cause
Gemini CLI enforces strict security boundaries. If an extension attempts to write to its own internal directories (like `.../.gemini/extensions/<ext-name>/sessions/`), and that path is not explicitly "trusted" or part of the current project workspace, the tool execution is blocked.

### Solution
Manually add the extensions root directory to the `.gemini/trustedFolders.json` file.

**Correct `trustedFolders.json` update:**
```json
{
  "C:\\Users\\ukchim01\\.gemini\\extensions": "TRUST_FOLDER"
}
```

---

## 10. Prefer Workspace-Local Storage for Session Persistence

### Problem
Even with `trustedFolders.json` configured, agents may struggle with path resolution when mapping between their global installation directory (where scripts live) and their global session directory (where state lives). This often manifests as hallucinated paths or the agent getting "lost" between `${extensionPath}` and `${process.cwd()}`.

### Root Cause
Session data is project-specific, but the default storage model was extension-global. This creates a disconnect where the agent is forced to constantly context-switch between two disparate root directories, increasing the risk of path resolution errors and permission blocks.

### Solution
Pivot the extension's architecture to store all session, ticket, and temporary data within the project's own `.gemini/` folder.

**Benefits:**
1. **Automatic Trust**: Gemini CLI automatically trusts paths within the current workspace, removing the need for `trustedFolders.json` hacks.
2. **Simplified Prompts**: `${SESSION_ROOT}` becomes a simple subdirectory of the current workspace (`cwd`), making it much easier for the agent to navigate.
3. **Project Portability**: Sessions are naturally grouped with the codebase they belong to.

**Correct path initialization in `session-setup.js`:**
```javascript
const SESSIONS_ROOT = path.join(process.cwd(), '.gemini', 'sessions');
```

---

---

## 11. Hardened Workspace Discovery (Anti-Sandbox Logic)

### Problem
When agents run in temporary sandboxes (e.g., `.../.gemini/tmp/`), they may incorrectly identify the workspace root if a `.gemini` folder is found inside the `tmp` directory. This leads to session data being stored in non-persistent locations.

### Solution
Harden the `findWorkspaceRoot` logic to explicitly ignore `.gemini` folders located in `tmp`, `temp`, or the user's home directory.

**Corrected Logic (session-setup.ts):**
```typescript
const isTmp = curr.toLowerCase().includes('tmp') || curr.toLowerCase().includes('temp');
if (fs.existsSync(potential) && 
    potential.toLowerCase() !== globalGemini.toLowerCase() &&
    !isTmp) {
  return curr;
}
```

---

## 12. Path Discipline & Absolute Script Execution

### Problem
Agents often attempt to `cd` into the `${extensionPath}` to run scripts, which triggers workspace restriction errors ("Path not in workspace").

### Solution
1. **Persona Injection**: Integrate "Path Discipline" into the core persona. Forbid `cd` or `dir_path` into the extension root.
2. **Absolute Calls**: Mandate the use of absolute paths for all extension script calls (e.g., `node "${EXTENSION_ROOT}/extension/bin/update-state.js" ...`).
3. **Workspace Anchoring**: Ensure the agent remains in the project workspace while executing remote scripts.

---

## 13. Platform-Specific Fallbacks (Windows ID Generation)

### Problem
The `openssl` command is often missing on vanilla Windows installations, causing ticket generation to fail during breakdown.

### Solution
Provide a Node.js-based fallback for random ID generation that works on any machine where the extension (Node.js) is running.

**Reliable ID Generation:**
```bash
node -e "console.log(require('crypto').randomBytes(4).toString('hex'))"
```

---

## 14. Advanced State & Ticket Management

### Problem
Simple key-value state updates were insufficient for complex lifecycle tasks like updating ticket statuses across nested directories.

### Solution
Refactor `update-state.js` into a multi-action utility that can handle:
- **`ticket-status`**: Locates ticket files (recursive search if necessary) and updates frontmatter.
- **`step`**: Updates the global lifecycle phase.
- **`current_ticket`**: Tracks the active task.

---

## 15. The "No-Stop" Loop (Continuous Execution)

### Problem
Forcing the agent to yield (`[STOP_TURN]`) after every phase (PRD -> Breakdown -> Research) introduces friction and requires the user to manually trigger the next command repeatedly.

### Solution
Remove mandated `[STOP_TURN]` blocks from the `prd-drafter` and `ticket-manager` skills. Instruct the agent to proceed to the next skill automatically unless it reaches its iteration/time limit.

---

## Summary Checklist for Pro-Architect Extensions

1.  [x] **Hardened Roots**: Does `session-setup` ignore `tmp` folders?
2.  [x] **Path Discipline**: Is `cd` forbidden in `architect.toml`?
3.  [x] **Windows Fallbacks**: Are random IDs generated using `crypto`?
4.  [x] **Absolute Paths**: Are all script calls in skills hard-coded with `"${EXTENSION_ROOT}"`?
5.  [x] **Continuous Loop**: Are unnecessary `[STOP_TURN]` yields removed?
6.  [x] **ESM Consistency**: Do ALL `.js` files under `extension/` use `import` (not `require`)? See Lesson 15.
7.  [x] **Two-Step Sync**: After editing source files, are they ALSO copied to `.gemini/extensions/<NAME>/`? (Lesson 16)
8.  [x] **Workspace Registry**: Does `dispatch.js` record `cwd` to `last_workspace.txt` and do binary scripts use it? (Lesson 17)
9.  [x] **Hierarchical Discovery**: Do scripts support `--workspace` overrides? (Lesson 18)
10. [x] **Double-Trust (C/c)**: Are both drive letter case variations in `trustedFolders.json`? (Lesson 23)
11. [x] **No-Exploration Persona**: Is the agent forbidden from listing extension folders? (Lesson 24)
12. [x] **Utility Upgrade**: Are auxiliary scripts modernized (ESM/Prefix)? (Lesson 25)
13. [x] **Phase Guarding**: Does `BuiltinCommandLoader` protect against duplicate phases? (Lesson 19)
14. [x] **Listener Limit**: Are `maxListeners` increased for scaled extension sets? (Lesson 20/22)
15. [x] **Platform Patching**: Are core platform bugfixes applied to global `node_modules`? (Lesson 21)

---

## 15. ESM/CJS Module Conflict (The `require is not defined` Bug)

### Problem
The `extension/package.json` contains `"type": "module"`, which tells Node.js to treat ALL `.js` files under the `extension/` directory as ES Modules. Any file using CommonJS `require()` syntax will fail with:

```
ReferenceError: require is not defined in ES module scope
```

This is especially insidious because:
- **Hand-written scripts** (like `update-state.js`) may use `require()` by default.
- **Compiled TypeScript output** uses ESM `import` syntax (matching the `"type": "module"` setting).
- There is **no warning at compile time** — the error only appears at runtime.

### Root Cause
Node.js resolves the module type by walking up the directory tree to find the nearest `package.json` with a `"type"` field. Files under `extension/bin/` and `extension/hooks/` inherit `"type": "module"` from `extension/package.json`. Therefore, ALL `.js` files in these directories MUST use `import`/`export` syntax.

### Solution
**Rule**: Every `.js` file under `extension/` MUST use ESM `import` syntax:
```javascript
// ❌ WRONG — will crash under "type": "module"
const fs = require('fs');
const path = require('path');

// ✅ CORRECT — works with "type": "module"
import fs from 'node:fs';
import path from 'node:path';
```

### Prevention Checklist
- Before committing any `.js` file under `extension/`, verify it uses `import` not `require`.
- Run `node --check <file>` to validate syntax.
- After editing source files, ALWAYS sync to the installed extension directory:
  ```powershell
  Copy-Item -Path "source/file.js" -Destination "$HOME/.gemini/extensions/Pro-Rick-GPro/path/file.js" -Force
  ```

---

## 16. Two-Step Sync Rule (Source vs. Installed Extension)

### Problem
The Gemini CLI runs scripts from the **installed** extension directory (`~/.gemini/extensions/<NAME>/`), not the source workspace. Editing source files without copying them to the installed directory has no effect.

### Solution
After ANY edit to a file under the extension's `extension/` directory:
1. Edit the **source** copy (in your workspace).
2. **Copy** the edited file to the installed extension directory.
3.  **Verify** with `node --check` on the installed copy.

---

## 17. Sandbox Isolation & Workspace Registry Bridge

### Problem
Gemini CLI workers and hooks often run in temporary sandboxes with no direct parent-child relationship to the project's workspace. Standard `findWorkspaceRoot` logic (which traverses `path.dirname`) fails because it hits the system root before finding a `.gemini` folder, leading to session data being stored in incorrect directories.

### Solution
Implement a **Workspace Registry** to bridge the sandbox-to-workspace gap.

1. **Registry Creation**: The hook dispatcher (which knows the true `cwd`) records the project path in a persistent `last_workspace.txt` file within the extension's root directory.
2. **Lookup Fallback**: The setup and state scripts are modified to read this registry when standard discovery fails, ensuring they always target the project-local workspace.

**Registry Logic (dispatch.js):**
```javascript
if (data.cwd) {
    const registryPath = join(EXTENSION_DIR, 'last_workspace.txt');
    writeFileSync(registryPath, data.cwd);
}
```

---

## 18. Multi-Layered Workspace Discovery

### Problem
Relying on a single discovery method (like `process.cwd()` or a hardcoded fallback) is fragile in complex environments where agents might be isolated from the filesystem structure.

### Solution
Use a hierarchical, fail-safe discovery strategy (ordered by precedence):

1. **Explicit Argument**: Check for `--workspace <PATH>` or `--wd <PATH>` command-line arguments.
2. **Environment Variable**: Check for `ANTIGRAVITY_WORKSPACE_ROOT`.
3. **Traversal Discovery**: Perform `findWorkspaceRoot` traversal from `process.cwd()` (ignoring `tmp`).
4. **Local Registry**: Fall back to the "Workspace Registry" (`last_workspace.txt`) recorded by the dispatcher.
5. **Safe Baseline**: Finally fall back to `process.cwd()`.

This multi-layered approach ensures the project root is correctly identified regardless of whether the agent is running "naked" on the OS or inside a restrictive sandbox.

---

## 19. Startup Stabilization & Listener Leaks

### Problem
Gemini CLI starts with warnings: `Cannot start phase 'load_builtin_commands': phase is already active` and `MaxListenersExceededWarning: Possible EventTarget memory leak detected`.

### Root Cause
1. **Duplicate Phases**: Rapid React effect re-runs (or concurrent initialization triggers) can cause the `BuiltinCommandLoader` to attempt starting the `load_builtin_commands` profiling phase while it is already active.
2. **Listener Accumulation**: Each extension and MCP server setup adds an `abort` listener to a shared `AbortSignal`. When the number of active extensions exceeds the default Node.js limit (usually 10), it triggers a memory leak warning.

### Solution
1. **Phase Guarding**: Implement a `loaded` flag in `BuiltinCommandLoader` to ensure the profiling phase is only started once.
2. **Listener limit**: Increase the max listeners for the `AbortSignal` using `setMaxListeners(N, signal)` in `slashCommandProcessor.js`.

**Corrective Implementation (BuiltinCommandLoader):**
```javascript
async loadCommands(_signal) {
    if (this.loaded) return [];
    const handle = startupProfiler.start('load_builtin_commands');
    // ... load commands ...
    handle?.end();
    this.loaded = true;
}
```

**Corrective Implementation (slashCommandProcessor):**
```javascript
import { setMaxListeners } from 'node:events';
// ...
useEffect(() => {
    const controller = new AbortController();
    setMaxListeners(20, controller.signal);
    // ...
}, [config, ...]);
```

---

## 20. Extension Update 403s (GitHub Rate Limiting)

### Problem
Update checks for extensions fail with `Request failed with status code 403`.

### Root Cause
GitHub's REST API is strictly rate-limited for unauthenticated requests. When many extensions are checked for updates in a short period, the IP-based limit is easily hit.

### Solution
- **Authentication**: Users should set a `GITHUB_TOKEN` environment variable to increase their rate limit.
- **Improved Diagnostics**: Update `github_fetch.js` to provide clearer guidance when a 403 occurs.

**Improved Error Message:**
```javascript
if (res.statusCode === 403) {
    errorMessage += '. This is likely due to GitHub rate limiting. Consider setting a GITHUB_TOKEN environment variable.';
}
```

---

## 21. Debugging Core Platform Bugs (Global node_modules)

### Problem
Problems like duplicate startup phases or global listener leaks often appear to be extension-related but are actually bugs in the Gemini CLI platform itself.

### Root Cause
The core CLI logic resides in the global `node_modules` directory (e.g., `...\AppData\Roaming\npm\node_modules\@google\gemini-cli`). When the platform's own state management or React hooks (like `slashCommandProcessor.js`) have race conditions or lacks guards, extensions merely trigger the bug rather than containing it.

### Solution
- **Locate Core**: Use `npm root -g` to find the global installation path.
- **Trace via UI Hooks**: Look into `dist/src/ui/hooks/` and `dist/src/services/` for the actual logic.
- **Apply Platform Patches**: Modify the core files directly in the global `node_modules` for immediate stabilization.
- **Verify with `node --check`**: Always validate syntax after editing compiled `.js` files in the global path.

---

## 22. The "Scale Paradox" (Concurrent Init Leaks)

### Problem
A CLI configuration that works perfectly with 2-3 extensions suddenly starts throwing memory leak warnings or timing out when 10+ extensions are installed.

### Root Cause
Many asynchronous operations (like extension loading or update checks) share a single `AbortSignal` for lifecycle management. Each operation adds a listener. Node.js's default `MaxListeners` limit is 10. Once the number of extensions + concurrent tasks exceeds this threshold, the "Scale Paradox" triggers a warning, even if there is no actual memory leak.

### Solution
- **Proactive Limit Heightening**: If a platform supports many extensions, the core must explicitly increase the listener limit on shared signals.
- **Code**: `setMaxListeners(20, signal);`.
- **Diagnostic**: Always check the number of active extensions (`gemini extensions list`) when troubleshooting "intermittent" startup warnings.

---

## 23. Drive Letter Case Sensitivity in `trustedFolders.json`

### Problem
Agents are still blocked with "Path not in workspace" errors even after the extension root is added to `trustedFolders.json`.

### Root Cause
Windows drive letters are case-insensitive for the OS but can be case-sensitive for string matching in security filters. If the Gemini CLI resolves a path as `c:\Users\...` but `trustedFolders.json` only contains `C:\Users\...`, the trust check may fail depending on the internal resolver's implementation.

### Solution
**Double-Trust**: Add both drive letter case variations to `trustedFolders.json`.

```json
{
  "C:\\Users\\name\\.gemini\\extensions\\ext-name": "TRUST_FOLDER",
  "c:\\Users\\name\\.gemini\\extensions\\ext-name": "TRUST_FOLDER"
}
```

---

## 24. Mandatory Path Discipline: The "No Exploration" Rule

### Problem
Agents attempt to use `list_directory` or `ReadFolder` on the `${EXTENSION_ROOT}` to "find" scripts, which often triggers workspace restrictions even if the root is trusted, or causes the agent to get lost in internal extension logic.

### Solution
Implement a **Persona-Level Mandate** that forbids exploration of extension paths.

1. **Trust the Prompt**: Instruct the agent to trust that any script referenced in its command definition exists.
2. **Absolute Execution**: Force the agent to execute scripts via absolute paths using `${EXTENSION_ROOT}` without listing the directory first.
3. **Recovery Protocol**: If a tool fails with "Path not in workspace", the agent's first instinct MUST be to check if it used a relative path or an exploratory tool, and correct it by using a project-local or absolute extension path.

---

## 25. Utility Script Modernization (ESM & Command Prefixes)

### Problem
Auxiliary scripts like `artifact-runner.js` fail during orchestration because they use outdated CommonJS syntax (conflicting with ESM "type": "module" settings) or trigger incorrect extension commands (e.g., using `/architect` instead of the renamed `/rick-architect`).

### Solution
1. **Modernize Imports**: Use `node:` prefixed imports and ensure `import`/`export` is used.
2. **Prefix Sync**: Ensure all internal command triggers match the latest manifest (e.g., `gemini /rick-architect`).
3. **Shebang Protection**: Ensure scripts designed for direct execution maintain a valid shebang (`#!/usr/bin/env node`).

**Correct internal trigger:**
```javascript
const cmd = ['gemini', '/rick-architect', '--resume', sessionDir];
```

---

## 26. User-Friendly Session Resume (Path vs. Name)

### Problem
Users find it cumbersome to copy-paste full relative paths (e.g., `.gemini/sessions/2024-02-11-abcd`) to resume a specific session. They prefer using just the session ID or a short name.

### Solution
Implement a **Smart Path Resolver** in the session setup script.

1.  **Check Path Match**: First, treat the input as a file system path.
2.  **Check ID Match**: If the path doesn't exist, check if it exists as a subdirectory within `${SESSIONS_ROOT}`.

**Implementation:**
```javascript
if (resumePath) {
    let potentialPath = resolvePath(resumePath);
    if (fs.existsSync(potentialPath)) {
         fullSessionPath = potentialPath;
    } else {
         const sessionInRoot = path.join(SESSIONS_ROOT, resumePath);
         if (fs.existsSync(sessionInRoot)) {
             fullSessionPath = sessionInRoot;
         }
    }
}
```

This allows both `/architect --resume .gemini/sessions/sess-1` and `/architect --resume sess-1` to work seamlessly.

---

## 27. New Commands Require Re-Installation

### Problem
Adding a new `.toml` file to the `commands/` directory does not automatically register the command in the Gemini CLI, even after a restart. The command remains "missing" until the extension is updated or re-installed.

### Solution
The CLI caches the command list at installation time. When adding new commands:
1.  **Bump Version**: Increment `version` in `gemini-extension.json`.
2.  **Re-Install**: Run `gemini extensions install .` (or the source path) to force a refresh of the command registry.
3.  **Restart**: Restart the CLI to load the new configuration.

---

## 28. Cross-Instance Startup Guards (Static Caching)

### Problem
Even with local guards (e.g., `this.loaded = true`), the Gemini CLI may instantiate multiple copies of a `CommandLoader` (common during React hot-reloading or UI state transitions). If these instances run concurrently, they will each attempt to start the same `startupProfiler` phase, causing "phase is already active" errors.

### Solution
Use **Static Class Properties** for lifecycle state and caching.
1. **Static Promise**: Ensures that if multiple instances call `loadCommands` simultaneously, they all wait for the exact same initialization task.
2. **Static Cache**: Ensures that subsequent calls (after the first load) return the full set of results immediately from memory, rather than returning `[]` or re-running the load logic.

**Hardened Pattern:**
```javascript
export class HardenedLoader {
    static globalLoaded = false;
    static cachedResults = [];
    async loadCommands() {
        if (HardenedLoader.globalLoaded) return HardenedLoader.cachedResults;
        // ... (use a static promise to guard the actual loading)
    }
}
```
This ensures built-in commands are never "lost" and the profiler is only touched once per CLI lifecycle.

---

## 29. Silent Execution Mode for Utilities

### Problem
When utility commands (like listing sessions) are triggered via the Markdown prompt pattern, the LLM often attempts to "help" by re-summarizing the tool output or commenting on it. This can lead to repetitive output, "malformed function call" errors if the model tries to call more tools, or unnecessary loop detections.

### Solution
Harden the command prompt to enforce **Silent Execution**.
1. **Explicit Role**: Tell the model it is in "Silent Execution Mode".
2. **Mandatory Token**: Use `completionPromise` in TOML and require the model to output the token *immediately* after the tool call.
3. **No Summarization**: Explicitly forbid any explanation or follow-up text.

**Example Prompt:**
```markdown
# Silent Execution Mode
1. Execute script: `node ...`
2. Do NOT summarize or explain.
3. Output <promise>TOKEN</promise> immediately.
```
This keeps the UI clean and prevents the "AI chatter" from cluttering utility command output.

---

## 30. Windows Spawning Pitfalls (`shell: true`)

### Problem
When using Node.js `child_process.spawn()` to execute a command on Windows that is actually a shell script or batch file (e.g., `gemini.cmd`), the call will fail with `spawn EINVAL` if the `shell` option is not set. This is because Windows requires a command processor to handle `.cmd` files and correctly parse arguments containing spaces (like `Ai Tools`).

### Solution
Always set `shell: true` when spawning commands on Windows, especially for `.cmd` or `.bat` files.

**Correct Pattern:**
```javascript
const command = process.platform === 'win32' ? 'gemini.cmd' : 'gemini';
const proc = spawn(command, args, {
    shell: process.platform === 'win32',
    // ...
});
```
This ensures the underlying shell (typically `cmd.exe` or `powershell.exe`) handles the execution bridge correctly.

---

## 31. Positional vs. Flag Prompt Conflict

### Problem
The Gemini CLI (and many other commander-based CLIs) distinguishes between a "positional prompt" (e.g., `gemini "hello"`) and a flagged prompt (e.g., `gemini -p "hello"`). Passing both simultaneously results in an error:
`Cannot use both a positional prompt and the --prompt (-p) flag together`

### Solution
When programmatically spawning the CLI, ensure that any "task description" or "instructions" are strictly integrated into the string passed to the `-p` flag. Do not pass them as positional arguments if you are also using `-p`.

---

## 32. Path Quoting with `shell: true` (Windows)

### Problem
Even when passing arguments as an array to `spawn(cmd, args, { shell: true })`, Windows shells (`cmd.exe`) can still misinterpret paths containing spaces if they aren't explicitly quoted. The shell may split `C:\Users\Name\Ai Tools` into `C:\Users\Name\Ai` and `Tools`, leading to "file not found" or "invalid argument" errors.

### Solution
Manually wrap paths containing spaces in double quotes when executing on Windows with `shell: true`.

**Pattern:**
```javascript
const quotedPath = p.includes(' ') && process.platform === 'win32' ? `"${p}"` : p;
cmdArgs.push('--include-directories', quotedPath);
```
This forces the Windows shell to treat the entire string as a single argument.

---

## 33. Windows log line endings (CRLF Compliance)

### Problem
Logs viewed in standard Windows text editors (Notepad, etc.) appeared as massive single lines, or displayed missing newline characters.

### Root Cause
Many Unix-flavored scripts use `\n` (LF) exclusively. Windows legacy and some modern tools specifically look for `\r\n` (CRLF) to recognize line breaks.

### Solution
Use `node:os` module's `EOL` constant to ensure platform-native line endings.

**Correct Logging Pattern:**
```javascript
import { EOL } from 'node:os';
// ...
fs.appendFileSync(logPath, `[${ts}] ${message}${EOL}`);
```

---

## 34. Local Development vs. Installed Synchronization

### Problem
Applying changes to the `Downloads/Ai Tools/...` source directory had no effect on the running extension, as the Gemini CLI executes code from `%USERPROFILE%/.gemini/extensions/...`.

### Root Cause
Extensions are "installed" via a deep copy. The active instance is detached from the source. Furthermore, hardcoded paths in `dispatch.js` often point to the home directory version, ignoring the developer's working copy.

### Solution
1. **Dynamic Rooting**: Support the `EXTENSION_DIR` environment variable in all hooks and dispatchers to allow redirecting the extension's internal lookups to the source folder.
2. **Re-install Ritual**: Treat `gemini extensions install .` as a mandatory step after any UI/TOML change, as the command registry is cached at install time.

---

## 35. Robust Session ID Resolution (Fuzzy Matching)

### Problem
The `--resume <ID>` flag was brittle, requiring either a full relative path or a perfectly typed folder name.

### Root Cause
Initial logic strictly used `path.resolve()`, which forced IDs to be treated as file paths relative to the current working directory.

### Solution
Implement a multi-stage search in the session setup script:
1. Treat as direct path.
2. Search for exact ID in the workspace's `./.gemini/sessions/` directory.
3. Perform fuzzy/partial match against existing session folders.

---

## 36. Context Noise Control (`.geminiignore`)

### Problem
The agent would enter a "self-referential loop" by reading its own `debug.log` or previous session data into the context during repo searches.

### Root Cause
Large log files clutter the prompt context and can mislead the agent into thinking past errors are current ones.

### Solution
Create a `.geminiignore` file in the project root. The Gemini CLI respects this file (similar to `.gitignore`) to exclude noise from its internal operations and tool results.

**Standard `.geminiignore` for Architect:**
```text
**/debug.log
**/hooks.log
**/logs/
.gemini/sessions/**
```

---

## 37. Markdown-Formatted Debug Logs

### Problem
Plain text logs (`.log`, `.txt`) are difficult to parse visually when debugging complex JSON objects or multi-line error stacks. They often lack syntax highlighting and structure in standard editors.

### Solution
Output debug logs as **Markdown** files (`.md`) and wrap entries in code blocks.

**Implementation**:
```javascript
const formatted = \`\`\`\${os.EOL}[\${ts}] [CheckLimitJS] \${msg}\${os.EOL}\`\`\`\${os.EOL};
fs.appendFileSync(logPath, formatted);
```
This allows VS Code and other editors to render the logs with distinct block separation and potential syntax highlighting.

---

## 38. Robust Session Setup Automation (TOML Command Strategy)

### Problem
Instructions to "Run the setup script" often fail because the agent constructs the command incorrectly for the specific OS shell (e.g., misquoting paths in PowerShell), or the user copies the command with slight errors.

### Solution
Hardcode the exact, platform-specific command string in the `architect.toml` prompt definition, using the "Single Quote Strategy" (Lesson 2) to ensure reliability.

**TOML Definition**:
```toml
[command.windows]
command = "powershell.exe"
args = ["-NoProfile", "-Command", "node '${extensionPath}/extension/bin/session-setup.js' $ARGUMENTS"]
```
This removes the variability of LLM-generated command strings for critical infrastructure initialization.

---

## 39. Debouncing State Updates (The "Loop Increment by X" Bug)

### Problem
The agent's iteration counter would increment by 4 steps (or more) for every single logical turn, exhausting the `maxIterations` limit prematurely.

### Root Cause
The `BeforeModel` hook in `hooks.json` uses a wildcard matcher (`"matcher": "*"`). When the context includes multiple files (e.g., `task.md`, `implementation_plan.md`, `current_file.js`), the hook triggers once for *each file* in the context during a single prompt construction phase.

### Solution
Implement a **Debounce Mechanism** in the hook handler.
1.  **Timestamp Tracking**: Add a `last_increment_ts` field to `state.json`.
2.  **Time Gate**: Only allow the increment to proceed if a sufficient time (e.g., 2000ms) has passed since the last update.

**Correct Handler Logic (`increment-iteration.js`):**
```javascript
const now = Date.now();
const lastIncrement = state.last_increment_ts || 0;

if (now - lastIncrement > 2000) {
    state.iteration = (state.iteration || 0) + 1;
    state.last_increment_ts = now;
    // ... write state ...
}
```
This ensures that even if the hook fires 10 times in 100ms, the state only updates once.


---

## 40. Debounce Tuning for Fast Models (Flash-Lite Support)

### Problem
The iteration counter "skips" numbers (e.g., jumps from 5 to 7) when using extremely fast models like Gemini Flash-Lite.

### Root Cause
The initial 2000ms debounce in `increment-iteration.js` (Lesson 39) was too aggressive. Fast models can complete a tool call and return a new prompt within <1 second. If the next hook fires within the 2000ms window, the increment is ignored, but the agent still performs work, leading to a desync between actual turns and recorded iterations.

### Solution
**Reduce the debounce threshold**. A value of **500ms** is sufficient to prevent the "double-fire" bug (where one event triggers two hooks instantly) while still capturing legitimate rapid-fire turns.

**Refined Logic:**
```javascript
// Debounce: Only increment if 0.5 seconds have passed
if (now - lastIncrement > 500) {
    // ...
}
```

---

## 41. ANSI Colors in Tool Output (The "Malformed JSON" Bug)

### Problem
When an LLM executes a tool (e.g., `list-sessions`) and the output contains ANSI color codes (`\x1b[32m...`), the model may fail to parse it strictly or get confused, leading to "malformed function call" errors or hallucinatory follow-up calls.

### Root Cause
Models trained on clean text data often struggle with raw terminal escape sequences. They may interpret them as noise or try to "fix" the output in their next response.

### Solution
**Suppress ANSI colors** when the tool is called by an agent.
1.  **Support `NO_COLOR`**: Update utility scripts to check `process.env.NO_COLOR` and disable colors if present.
2.  **Enforce in Prompt**: In the TOML definition, set `NO_COLOR=1` when invoking the script.

**TOML Example:**
```toml
command = "bash"
args = ["-c", "NO_COLOR=1 node extension/bin/list-sessions.js"]
```

**Script Logic:**

---

## 42. Double Drive Letters in PowerShell Variables

### Problem
When passed a prompt variable like `${extensionPath}` which resolves to `C:\Users\...`, PowerShell scripts that assign it to a variable (e.g., `$ext = "${extensionPath}"`) sometimes result in a path like `C:\C:\Users\...` when used in subsequent commands.

### Root Cause
This is often due to a conflict between how the prompt engine interpolates the variable and how PowerShell interprets the string assignment, especially if the engine tries to "fix" paths for Windows automatically.

### Solution
**Use Inline Execution**. Avoid intermediate PowerShell variables for paths injected by the prompt template.

**Bad Pattern:**
```powershell
$ext = "${extensionPath}"
node "$ext/bin/script.js"
```

**Good Pattern:**
```powershell
node "${extensionPath}/bin/script.js"
```

---

## 43. Hallucinated HTML Entities in TOML Commands

### Problem
PowerShell commands defined in `.toml` prompts sometimes fail with `ParserError: Unexpected token '&'`.

### Root Cause
LLMs may hallucinate or "correct" special characters in the prompt into HTML entities (e.g., converting a newline or simple space into `&#x0A;` or `&nbsp;`). When this string is passed to PowerShell, the `&` is interpreted as the call operator or background operator, causing a syntax error.

### Solution
**Simplify Command Syntax**. Reduce the complexity of the command string to minimize the chance of the LLM introducing "helpful" formatting entities. Use standard, simple one-liners where possible.

