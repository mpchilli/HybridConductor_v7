# 📂 HYBRID CONDUCTOR

**Windows-Native LLM Orchestration Framework**
*From Messy Prompt to QA'd Application*

[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🚀 Executive Summary

Hybrid Conductor is a **self-correcting, Windows-native AI coding agent** that transforms ambiguous prompts into fully tested applications. It operates on a hybrid control model that prioritizes reliability over "black box" autonomy:

1.  **Strict Planning**: Generates Specs and Plans before a single line of code is written.
2.  **Isolated Building**: Executes tasks in dedicated Git branches to protect your codebase.
3.  **Deterministic Verification**: Runs Built-In Self-Tests (BIST) with multi-layer loop breaking (SHA-256 hash detection).
4.  **Glassmorphic Control**: A modern v8.0 React dashboard for monitoring and mid-flight steering.

Designed specifically for **Windows environments**, it requires **zero WSL, Docker, or Linux subsystems**.

---

## ✨ Key Features

- **🤖 Autonomous Implementation**: Converts natural language into functional, tested code.
- **🛡️ The Rick Protocol**: Prevents infinite loops by hashing file outputs and escalating temperature.
- **🔍 Openground RAG**: Semantic context retrieval using embedded LanceDB for Windows-native speed.
- **📊 Glassmorphism Dashboard v8.0**: Real-time SSE streaming, interactive progress trees, and system metrics.
- **🎹 Power-User UX**: Full keyboard shortcut support (`Ctrl+Enter`, `Ctrl+K`) and resizable console.
- **🧪 BIST Framework**: Automatic unit testing and syntax validation before every commit.
- **🔒 Security-First**: Localhost binding, user-space installation (no admin), and path sanitization.

---

## ⚡ Quick Start Guide

### 1. Prerequisites
- **OS**: Windows 10/11 (Native)
- **Python**: 3.11+
- **Node.js**: 18+ (for Dashboard)
- **Git**: Installed and in System PATH

### 2. Physical Installation
Run the native installer to set up the environment and dependencies:
```powershell
python setup.py
```

### 3. Launching the System

**Option A: The Modern Dashboard (Recommended)**
Best for interactive steering and visual progress.
```powershell
# Start both Backend and Frontend Dev Server
# (See backend/README.md for detailed Node setup)
python -m dashboard.app
```
Access at: `http://localhost:5173` (Dev) or `http://127.0.0.1:5000` (Prod)

**Option B: CLI Headless Mode**
Best for quick fixes or CI integration.
```powershell
python orchestrator.py --prompt "Clean up unused imports in src/" --complexity fast
```

---

## 🕹️ Interaction & Usage

### Complexity Modes
| Mode | Best For | Behavior |
| :--- | :--- | :--- |
| **FAST** 🐇 | Minor tweaks, typos | Skips Planning. Direct BIST loop code generation. |
| **STREAMLINED** 🚄 | Features, Refactors | **(Default)** Minimal Spec + TDD. Balanced rigor. |
| **FULL** 🦍 | New projects, architecture | Heavy Spec phase. Strict Verification gates. |

### Dashboard Shortcuts
- `Ctrl + Enter`: Submit Task
- `Ctrl + K`: Clear Console
- `Ctrl + /`: Focus Input
- `Ctrl + Shift + P`: Toggle Settings

---

## 🏗️ Architecture

Hybrid Conductor uses a **Deterministic State Machine** rather than a fragile event bus.

### Detailed Process Flow (ASCII)
```text
START
  |
  +---[ USER ] Input: Prompt & Complexity Mode (FAST/STREAMLINED/FULL)
  |      |
  |      v
  +-> ORCHESTRATOR (orchestrator.py) - State Machine Init
         |
         +-> State: PLANNING
         |      |
         +-------> Generate spec.md & plan.md
         |      |
         +-------> [ DISPLAY ] Show Plan to User
         +-------> [ USER ]    Approve Plan? (y/n)
         |             |
         |             v
         +-> State: BUILDING <---------------------------------------+
         |      |                                                    |
         |      +--- worker.py (Isolated Subprocess)                 |
         |      |      |                                             |
         |      |      +-> Git Branch Creation (task-xyz)            |
         |      |      +-> Context Retrieval (Openground/L3)         |
         |      |      +-> LLM Generation (Code Write)               |
         |      |      +-> Atomic File Save                          |
         |      |                                                    |
         |      |      +-> BIST (Built-In Self-Test)                 |
         |      |             |                                      |
         |      |             +---[ FAIL ] ---> LoopGuardian Check --+
         |      |             |                    |                 |
         |      |             |                    +---[ LOOP ] ---> Escalate Temp
         |      |             |                                      |
         |      |             +---[ DISPLAY ] Stream Logs (SSE)      |
         |      |                                                    |
         |      |             +---[ PASS ] ---> Commit to Branch     |
         |      |
         |      +--- Check Inbox (state/inbox.md)
         |             |
         |             +---[ USER ] Command Injection (/pause, /checkpoint)
         |             |
         |             +---[ DISPLAY ] Update Dashboard Status
         |
         +-> State: VERIFYING
         |      |
         |      +-> Run Integration Tests
         |      +---[ DISPLAY ] Show Test Results
         |
         +-> State: COMPLETE / FAILED
                |
                v
         [ DISPLAY ] Final Report & Artifacts
```

*(For visual diagrams, see [docs/architecture/system_flow.mermaid](docs/architecture/system_flow.mermaid))*

---

## 🔬 Methodological Comparison

Hybrid Conductor is optimized for reliability in Windows environments where administrative or container restrictions exist.

### Strategic Comparison
| Framework | Primary Strategy | Key Differentiator |
| :--- | :--- | :--- |
| **Hybrid Conductor** | **Deterministic State Machine** | Windows-native & SHA256 Loop Breaking |
| **Conductor (Google)** | Context-Driven Development | Deep Cloud Ecosystem Integration |
| **Ralph-Orchestrator**| Hat-Based Multi-Agent | Pub/Sub Event Bus Flexibility |
| **BMAD-METHOD** | Agentic Planning | scale-Adaptive Complexity Heuristics |

### Feature Matrix: Sub-Methods
| Sub-Method / Feature | Hybrid Conductor | Conductor (Google) | Ralph-Orchestrator | BMAD-METHOD |
| :--- | :---: | :---: | :---: | :---: |
| **OS Requirement** | **Windows Native** 🪟 | Linux / Cloud ☁️ | Linux / Docker 🐳 | Linux / Docker 🐳 |
| **Loop Breaking** | **SHA-256 Hash Pattern** ✅ | N/A | Timeout / Limit | Interaction Limit |
| **Context Engine** | **Openground (Local)** | Cloud API | Regex / Basic | Vector DB |
| **Complexity Control**| **Explicit Toggle** 🎚️ | Manual | Configurable | Heuristic (Auto) |
| **Installation** | **User-Space (No Admin)** | Toolchain Setup | Containerized | Containerized |

---

## 📂 Project Structure

```text
hybrid_conductor/
├── orchestrator.py      # Main state machine & brain
├── worker.py            # Task executor (subprocess)
├── loop_guardian.py     # Loop detection logic (SHA-256)
├── setup.py             # Windows-native installer
├── backend/             # Dashboard Server (Flask + SSE)
├── frontend/            # Dashboard UI (React + Tailwind)
├── state/               # Runtime state (spec.md, plan.md, inbox.md)
├── logs/                # Activity history (activity.db)
└── docs/                # Extended documentation & guides
```

---

## 🛠️ Troubleshooting

**Q: Git error on Windows?**
Ensure Git is in your PATH. The orchestrator depends on standard Git for isolated branch management.

**Q: Dashboard blank or connection refused?**
Verify `backend/dashboard/app.py` is running and port 5000/5173 are not blocked by firewall. Note: Dashboard binds only to `127.0.0.1`.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.

---
*Built for developers who want precision AI coding on Windows.*
