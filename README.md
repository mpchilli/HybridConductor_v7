# Hybrid Conductor v7.2.8
**Windows-Native AI Coding Agent**

[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🚀 Executive Summary

Hybrid Conductor is a **Windows-native AI coding framework** designed for reliability over autonomy. 

Most agents fail because they get stuck in loops or hallucinate libraries that don't exist. We fixed that by stripping away the "magic" and replacing it with hard engineering: **SHA-256 state tracking**, **isolated Git branches**, and **deterministic state machines**.

If you're tired of agents that write broken code and then delete it when they panic, this is for you. It requires **zero WSL, Docker, or Linux subsystems**. It runs where you work: on native Windows.

---

## 🛠️ The Tech Stack (Why It Works)

We don't use buzzwords. Here is exactly how the system guarantees reliability.

### 1. The Rick Protocol (Infinite Loop Killing)
Most agents get stuck trying to fix the same error forever. We use cryptographic hashing to stop that.

- **Mechanism**: The `LoopGuardian` class normalizes code output (strips timestamps/pointers) and computes a **SHA-256 hash**. It maintains a sliding window of the last 3 iterations.
- **Example**: If the agent writes the exact same `utils.py` content three times in a row to fix a `SyntaxError`, the hashes match.
- **Outcome**: The system immediately terminates the loop and escalates the LLM temperature (0.7 → 1.0 → 1.3) to force a new approach.

### 2. Hallucination-Proof Context via Openground
Agents fail when they guess what your code looks like. We give them the actual code.

- **Mechanism**: A tiered retrieval system (`ContextFetcher`).
    1.  **L1 (Vector)**: Queries local **LanceDB** via **Openground** for semantic matches (e.g., "auth logic").
    2.  **L2 (RegexFallback)**: If Openground fails, it scans `.py` files using rigid regex patterns.
- **Example**: When you ask for "user login", it pulls `backend/auth.py` vectors instead of hallucinating a generic `User` class.
- **Outcome**: < 10% hallucinated imports/functions compared to raw GPT-4.

### 3. Isolated Build Environments
We never touch your `main` branch until the code works.

- **Mechanism**: The `Worker` process uses an internal **MCP (Model Context Protocol) Server** to drive Git. It creates a temporary branch `task-{uuid}` for every single request.
- **Example**: A request to "refactor the API" happens in `task-a1b9`. If the BIST (Built-In Self-Test) fails, the branch is discarded. 
- **Outcome**: Your `main` branch is **always** deployable. No broken commits.

### 4. Deterministic State Machine
Event buses are brittle. We use a linear, single-threaded brain.

- **Mechanism**: `Orchestrator.py` implements a rigid Finite State Machine: `PLANNING` → `BUILDING` → `VERIFYING`. Transitions are atomic.
- **Example**: The system *cannot* build code until the user approves the `plan.md` artifact in the `PLANNING` phase (unless in FAST mode).
- **Outcome**: Zero "orphaned" agent processes or race conditions.

---

## ⚡ Launching the System

You have 4 ways to run this, depending on your vibe.

### **🚀 Option A: Standard Dashboard (Recommended)**
The best daily driver. Native window, system tray integration, high performance.
```powershell
python start_gui.py
```

### **🌐 Option B: Web Dashboard**
For remote access or if you prefer Chrome/Edge.
```powershell
python start_app.py
```
*Access at: `http://127.0.0.1:5000`*

### **💻 Option C: Standalone Executable**
No Python installed? No problem.
- **File**: `dist\HybridConductor.exe`
- **Build It**: `python scripts/build/build_exe.py`

### **🦍 Option D: CLI Headless Mode**
For CI/CD pipelines or hard-core terminal users.
```powershell
python orchestrator.py --prompt "Refactor src/utils.py" --complexity fast
```

---

## 🧪 Developer Workflow

Want to mod the engine? Here is how you build and test.

### Making Changes
1.  **Modify Source**: Edit `backend/` (React/Flask) or `orchestrator.py` (Python).
2.  **Test Locally**: Run `python start_gui.py`.
3.  **Rebuild UI**: `cd backend && npm run build`.
4.  **Rebuild Exe**: `python scripts/build/build_exe.py`.

### Testing with Playwright
We don't guess if the UI works. We prove it.

```powershell
cd backend
npx playwright install  # First run only
npm test                # Runs all specs
```

| Spec File | Coverage |
| :--- | :--- |
| `console.spec.js` | Terminal input/output, keybindings (`Ctrl+K`) |
| `entry.spec.js` | Task submission flow |
| `progress.spec.js` | Recursive tree rendering |

---

## 🧬 Genealogy & Influences

This project didn't appear in a vacuum. It stands on the shoulders of:

### 1. **[Ralph Orchestrator](https://github.com/gemini-cli-extensions/ralph-orchestrator)**
*The "Hat" Philosophy.*
- **Influence**: Ralph's concept of "wearing different hats" (Planner vs. Builder) directly inspired our `State` class. We hardened it by forcing those hats to be distinct, irreversible states.

### 2. **[BMAD-METHOD](https://github.com/bmad-code-org/BMAD-METHOD)**
*The Complexity Heuristic.*
- **Influence**: BMAD's research into "Dynamic Complexity" taught us that AI needs to know *how hard* a task is. We simplified their continuous scale into our 3 discrete modes: **FAST** (Direct), **STREAMLINED** (TDD), and **FULL** (Spec-First).

### 3. **[Google Conductor](https://github.com/gemini-cli-extensions/conductor)**
*Context-Driven Development.*
- **Influence**: The idea that "Context is King." We adopted their pattern of fetching context *before* planning, but swapped their cloud API for our local **Openground** vector store to keep it offline-friendly.

---

## 📂 Project Structure

```text
hybrid_conductor/
├── orchestrator.py      # The Brain (State Machine)
├── worker.py            # The Hands (Git + Subprocess)
├── loop_guardian.py     # The Referee (SHA-256 Hashing)
├── context_fetcher.py   # The Memory (Openground + Regex)
├── setup.py             # The Installer (Windows Native)
├── backend/             # The Body (Flask + React)
└── scripts/
    └── build/           # Packaging Logic (PyInstaller)
```

---

## 📜 License
Distributed under the **MIT License**.
*Built for engineers who want tools, not toys.*
