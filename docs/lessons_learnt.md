# Hybrid Orchestrator - Lessons Learned

## 1. Windows-Native Environment Challenges

### Unicode encoding (CP1252)

- **Issue**: Standard Windows consoles (using CP1252 encoding) throw `UnicodeEncodeError` when trying to print emoji characters (e.g., 🧪, ✅, 🎉).
- **Why**: The default `sys.stdout` encoding on Windows often lacks support for supplementary plane characters used in emojis.
- **Fix**: Replaced all emojis with ASCII text equivalents (e.g., `PASS:`, `ERROR:`, `RUNNING:`) to ensure cross-platform compatibility and stability.

### Subprocess Create No Window

- **Issue**: Background processes (like the MCP server) can cause flickering console windows on Windows.
- **Fix**: Used `creationflags=subprocess.CREATE_NO_WINDOW` in `subprocess.Popen` calls to ensure silent background execution.

## 2. Worker & Persistence Logic

### Temp Directory vs. Project Root

- **Issue**: `worker.py` successfully ran Built-In Self-Tests (BIST) in a temporary directory but failed to "persist" the results to the repository.
- **Why**: The code was verified in isolation for safety, but the logic to copy the verified code back to the project root before `git add .` was missing.
- **Fix**: Added explicit logic to copy BIST-passed files from the temporary directory to the current working directory before committing.

### Multi-File Task Support

- **Issue**: The initial implementation assumed a single task would result in a single file (`task_{id}.py`).
- **Fix**: Enhanced `worker.py` and `orchestrator.py` to support multi-file output by parsing `# filename: <name>` headers in the LLM response. This allows the system to generate complex utility libraries or multi-module features in a single pass.

### Restrictive BIST Success Criteria

- **Issue**: `_run_bist` check for "Task completed" in stdout caused valid tasks to fail if they didn't match that exact string.
- **Why**: The original simulation template included this string, but subsequent "LLM" simulations (like "Hello World") used more realistic project-specific output.
- **Fix**: Broadened BIST success to depend primarily on `returncode == 0` (script executed without error).

### Nested F-String Escaping

- **Issue**: `SyntaxError` in `worker.py` when generating code with f-strings.
- **Why**: The outer simulation `f-string` was trying to interpolate `{variable}` blocks intended for the *inner* generated code.
- **Fix**: Escaped braces in simulation templates (e.g., `{{variable}}`) to ensure they are passed as literals to the generated file.

## 3. Python Development Pitfalls

### Missing Standard Imports

- **Issue**: Persistent `NameError` for `sys` and `re`.
- **Why**: Several utility functions relied on these modules but they were only imported in certain scopes or missing entirely from the top-level imports of `worker.py`.
- **Fix**: Standardized top-level imports in all project files.

### Import Aliasing and Namespacing

- **Issue**: `orchestrator.py` failed to load because it expected `generate_codebase_map` from `cartographer.py`, but the function was named `generate_map`.
- **Fix**: Used `from cartographer import generate_map as generate_codebase_map` to maintain backwards compatibility with the orchestrator's expectations without renaming core library functions.

### Docstring Closures

- **Issue**: File-level `SyntaxError` prevents any execution or tests.
- **Why**: `context_fetcher.py` had an unclosed triple-quoted docstring at the top of the file, which broke the entire Python module.
- **Fix**: Added rigorous `py_compile` checks to the validation workflow to catch these before running deeper logic.

## 4. Operational Insights

### CLI Entry Point Separation

- **Issue**: The orchestrator only ran its internal test suite when executed directly, ignoring CLI arguments like `--prompt`.
- **Fix**: Restructured `orchestrator.py` to use `argparse` and separate the "Verification Mode" (internal tests) from the "Execution Mode" (real tasks).

## 5. Algorithm Robustness & Determinism

### Floating-Point Drift in Retry Logic

- **Issue**: `LoopGuardian` test suite failed intermittently on temperature escalation checks (expected `1.3`, got `1.29999999`).
- **Why**: Python's floating-point arithmetic (IEEE 754) introduced micro-drift when adding `0.3` intervals to the base temperature.
- **Fix**: Implemented explicit `round(..., 1)` in `get_escalated_temperature()` to force deterministic 1-decimal precision, ensuring the "jiggle" mechanics are predictable.

### Regex Greed & Masking

- **Issue**: Short hex tokens (e.g., commit hashes `a1b2c3d4`) were being stripped as generic `[HEX_ADDR]`, masking potentially relevant differences, or conversely, `[MEM_ADDR]` logic was dead code because the `[HEX_ADDR]` regex was too broad and ran first.
- **Fix**: Reordered normalization pipeline to handle specific patterns (Long Memory Addresses `9-16` chars) *before* generic ones, and tuned the regex boundaries (`\b`) to prevent overlapping matches.

### Semantic vs. Superficial Hashing

- **Issue**: Changing a code comment or adding a blank line caused the SHA-256 hash to change, allowing infinite logic loops to bypass detection.

## 6. Windows Process Spawning & Path Safety

### Argument Parsing Hazards

- **Issue**: Spawning subprocesses on Windows with paths containing spaces (e.g., `C:\Users\Name\Ai Tools`) often fails with `EINVAL` or "path not found".
- **Why**: Windows `cmd.exe` has complex quoting rules. `child_process.spawn` (in Node/Electron) or `subprocess.Popen` (in Python) can misinterpret spaces as argument delimiters.
- **Fix**:
  - **Quote Paths**: Always wrap paths in double quotes when constructing command strings (e.g., `cmd = f'"{path}"'`).
  - **Shell=True**: For `.cmd` or `.bat` files, use `shell=True`.
  - **Single Quotes**: In TOML or shell scripts, use single quotes (`'C:\Path'`) to prevent variable expansion issues with Windows backslashes.

### Hidden Environment Variables

- **Issue**: Child processes (like the Python bridge) failing specifically because they missed API keys or configuration.
- **Why**: `os.environ` isn't always fully propagated by default in some spawn configurations (especially when crossing from Node.js to Python).
- **Fix**: Explicitly pass the `env` dictionary to the subprocess call, merging `os.environ` with any required project-specific variables (`PYTHONPATH`, `GEMINI_API_KEY`).

## 7. External Tool Integration & Release Management

### Dockerless OpenHands Strategy
- **Issue**: Running full OpenHands agents usually requires Docker, which is heavy for simple Windows workflows and requires admin rights.
- **Fix**: Leveraged `openhands serve --runtime=process` via the `uv` tool. Constructed a dedicated `OpenHandsRunner` adapter that checks for `uv` presence and manages the subprocess lifecycle separately from the main loop.
- **Trade-off**: Process mode lacks sandboxing. Future work (v9) must implement a custom `Sandbox` wrapper to enforce safety limits (file access, network) that Docker usually handles.

### Version Referential Integrity
- **Issue**: Documentation rot caused by manual version updates. `grep` revealed multiple files (README, setup.py, matrix) still referencing "v4.1" or "v7.2.8" after a release.
- **Lessons**: 
    - **Grep is Mandatory**: Never trust a manual "search and replace". Always run `grep -r "old_version" .` before committing.
    - **Single Source of Truth**: Ideally, read version from `pyproject.toml` in `conf.py` or doc generators, rather than hardcoding it in Markdown headers.

### CLI Adapter Pattern
- **Issue**: Integrating third-party CLI tools (like `openhands` or `uv`) can lead to "command not found" crashes on user machines.
- **Fix**: Implemented the **Adapter Pattern** (`OpenHandsRunner`).
    - **Check Prerequisites**: Explicit method `check_prerequisites()` returns a dict of missing tools.
    - **Graceful Degradation**: The system detects missing tools *before* execution and offers fallback paths (e.g., "Install via uv" instructions) instead of crashing with a raw `FileNotFoundError`.

### "Start-Up Loop" with Recursive Process Spawning

- **Issue**: A parent process spawning a child that re-spawns the parent (infinite fork bomb).
- **Fix**: Implemented the `HC_BACKGROUND_CHILD` environment variable sentinal. The `orchestrator.py` checks for this variable at startup; if present, it behaves as a worker/child rather than spawning a new background task.
