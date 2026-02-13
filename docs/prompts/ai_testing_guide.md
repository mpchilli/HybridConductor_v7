# AI Testing & Organization Guide

## Purpose
This document provides instructions for AI agents on how to perform validation tests within the Hybrid Orchestrator v7.2.8 framework and how to organize the resulting artifacts.

## 1. Test Execution Protocol

### Simple Tests
For basic verification (e.g., "Hello World"), use the `FAST` complexity mode.
```bash
python orchestrator.py --prompt "Create a simple hello.py script" --complexity fast
```

### Complex/Multi-File Tests
For multi-module systems, use `STREAMLINED` or `FULL` mode. Ensure your prompt explicitly lists the desired files if specific structure is needed.
```bash
python orchestrator.py --prompt "Create a library with data_utils.py and a main.py consumer" --complexity streamlined
```

## 2. Output Organization
The system is configured to enforce structured persistence. Do **not** save test files to the root directory.

### Standard Path Structure
All test outputs must be saved to:
`tests/<YYYYMMMdd>/<HHMMSS>_<TaskID>/`

**Example:**
`tests/2026Feb13/174522_task8a/`

### File Persistence Logic
When writing logic to save files (e.g., in `worker.py` or custom scripts):
1.  **Generate Timestamp**: Get current date/time.
2.  **Create Directory**: Ensure the target folder exists (`mkdir -p`).
3.  **Write File**: Save the verified content to this structured path.
4.  **Clean Root**: If files were generated in root, move them to the structured folder immediately.

## 3. Verification Criteria (BIST)
- **Exit Code**: Must be `0`.
- **Content Check**: Verify file existence in the specific test folder.
- **Execution**: The script must run without error (`python <file>`).

## 4. Git Workflow for Successful Tests
If a test passes:
1.  **Commit**: The worker automatically commits to `task-<id>` branch.
2.  **Merge**: Merge `task-<id>` into `main` to preserve the verified test artifact.
3.  **Cleanup**: Delete the `task-<id>` branch after merging.
