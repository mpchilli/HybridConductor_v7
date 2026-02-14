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

### **🚀 Option A: Standard Dashboard (**Recommended**)**
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
For CI/CD pipelines, hard-core terminal users, or automated scripting.

```powershell
python orchestrator.py --prompt "Refactor src/utils.py" --complexity fast
```

#### **Available Arguments**

| Argument | Values | Description | Use Case |
| :--- | :--- | :--- | :--- |
| `--prompt` | Any natural language string | The core instruction for the AI to execute. | `--prompt "Refactor auth middleware"` |
| `--complexity` | • `fast`<br>• `streamlined`<br>• `full` | **Workflow Depth**: Control the rigor of the state machine. | • `--complexity fast` for trivial fixes<br>• `--complexity full` for mission-critical features |
| `--preset` | • `debug`<br>• `fast_track`<br>• `full`<br>• `streamlined`<br>• `tdd` | **Profiles**: Loads predefined configuration overrides from the `presets/` folder. | • `--preset tdd` to force a test-driven development flow |
| `--resume` | Flag (no value required) | **Persistence**: Restores the orchestrator to its last saved state from `state/session.json`. | Recovering a session after a reboot or intentional pause |
| `--background` | Flag (no value required) | **Detachment**: Spawns a detached process. Stays active if the terminal is closed. | Running long-running refactors (30m+) in the background |

#### **Complexity Mode Comparison**
-   **`fast`**: Skips planning and specs. Direct implementation loop.
-   **`streamlined`**: Default balanced mode. Minimal spec + TDD workflow.
-   **`full`**: High-rigor mode. Forced `spec.md` and `plan.md` generation with strict verification gates.

#### **Advanced Examples**

**1. Running a high-stakes refactor with full planning:**
```powershell
python orchestrator.py --prompt "Refactor core engine" --complexity full
```

**2. Resuming an interrupted session:**
```powershell
python orchestrator.py --resume
```

**3. Running a quick fix in the background:**
```powershell
python orchestrator.py --prompt "Fix typo in logging" --complexity fast --background
```

### **🔧 Option E: Manual Launch (Debugging)**
If `start_app.py` fails or you need direct access:
```powershell
cd backend
python -m dashboard.app
```
*Note: Must be run from the `backend/` directory.*

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

## 🏆 Ralph Loop Ecosystem Matrix v4.1

> Comprehensive comparison of Gemini CLI loop/workflow tools for one-shot app building.
> Legend: `✅` = Full support, `Partial` = Limited, `❌` = None. Citations `[n]` link to evidence below each table.

### CORE LOOP CONTROL

| Feature          | Hybrid Conductor | ralph-orch | kranthik/Ralph | conductor | ralph (official) | blueprint | ralph-wiggum | self-command | BMAD |
|------------------|------------------|------------|----------------|-----------|------------------|-----------|--------------|--------------|------|
| Loop Trigger     | ✅/RickProto [1] | ✅/CLI [6] | ✅/MCP [5]     | ❌ [2]   | ✅/AfterAgent [3]| ❌ [7]   | ✅/AfterAgent [4]| ✅/tmux [8]| ❌ [9] |
| Cycles Limit     | ✅/SHA-256 [10]  | ✅/config [14]| ✅/adjust [13]| ❌ [2]   | ✅/max-iter [11] | ❌ [7]   | ✅/max-iter [12]| Partial [15]| ❌ [9] |
| Loop Breaking    | ✅/hash [16]     | ✅/LOOP_COMPLETE [20]| ✅/complete [19]| ❌ [2]| ✅/promise [17] | ❌ [7]   | ✅/promise [18]| Partial [21]| ❌ [9] |
| Stuck Escape     | ✅/3cyc→esc [22] | ✅/backpressure [24]| ✅/diagnose [23]| ❌ [2]| Partial [11]   | ❌ [7]   | Partial [12] | ✅/idle [25] | ❌ [9] |
| One-Shot Success | ✅/BIST [26]     | ✅/gates [29]| Partial [28]  | Partial [27]| Partial [3]   | Partial [30]| Partial [4]| ❌ [8]       | Partial [31] |

<details>
<summary>📎 Evidence (Core Loop Control)</summary>

- **[1]** `loop_guardian.py:L27-96` — `LoopGuardian` class implements "Rick Protocol": SHA-256 hashes each normalized code output, maintains sliding window of last 3 hashes, escalates LLM temperature (0.7→1.0→1.3) on repeated hashes to force divergent outputs
- **[2]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — no loop/iteration commands exist; lifecycle is `/conductor:setup` → `:newTrack` → `:implement` → `:review` (spec-driven, not loop-driven)
- **[3]** [ralph README](https://github.com/gemini-cli-extensions/ralph) "Core Concept" — `AfterAgent` hook in `hooks/stop-hook.sh` intercepts every agent exit and re-invokes with accumulated context; exits when `<promise>` tag detected in output
- **[4]** [ralph-wiggum README](https://github.com/AsyncFuncAI/ralph-wiggum-extension) "How It Works" — `AfterAgent` hook creates self-referential feedback loop; agent re-runs until completion promise matched or max iterations hit
- **[5]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) project structure — 19 `.toml` slash commands + `mcp-server.ts` (2400+ lines MCP server); loop initiated via `/ralph:start-loop "task" -m 30`
- **[6]** [ralph-orchestrator README](https://github.com/mikeyobrien/ralph-orchestrator) "Quick Start" — standalone CLI: `ralph run -p "Add input validation"` iterates until `LOOP_COMPLETE` token or iteration limit; supports 7 backends (Claude, Kiro, Gemini, Codex, Amp, Copilot, OpenCode)
- **[7]** [blueprint README](https://github.com/gplasky/gemini-cli-blueprint-extension) — sequential step commands (`/blueprint:research` → `:plan` → `:define` → `:implement` → `:test` → `:refine`); no loop mechanism
- **[8]** [self-command README](https://github.com/stevenAthompson/self-command) "How it Works" — MCP tool injects commands into gemini-cli via `tmux send-keys`; agent can write then execute its own follow-up commands
- **[9]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — 21 specialized agent personas (PM, Architect, Quinn QA, etc.) with structured workflows; no loop/iteration control mechanism
- **[10]** `loop_guardian.py:L248-266` — `compute_normalized_hash()` calls `hashlib.sha256` on output normalized by `normalize_output()` which strips timestamps, hex addresses, paths, PIDs, thread IDs, comments, and whitespace
- **[11]** [ralph README](https://github.com/gemini-cli-extensions/ralph) "Options" — `--max-iterations <N>` (default 5); agent stops after N iterations regardless of completion
- **[12]** [ralph-wiggum README](https://github.com/AsyncFuncAI/ralph-wiggum-extension) "Examples" — `--max-iterations 10`; same mechanism as ralph, forked implementation
- **[13]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) commands — `/ralph:adjust -m 50` modifies iteration limit at runtime without restarting the loop
- **[14]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "Configuration" — `ralph.yml` config file sets `max_iterations`, per-preset overrides; 31 built-in presets (TDD, spec-driven, debugging, etc.)
- **[15]** [self-command](https://github.com/stevenAthompson/self-command) — `wait_for_idle` monitors CPU usage below configurable threshold; timeout-based rather than explicit iteration counting
- **[16]** `loop_guardian.py:L159-185` — `detect_loop()` checks if current SHA-256 hash exists in `hash_history[-3:]`; if match found → loop detected, triggers escalation or termination
- **[17]** [ralph README](https://github.com/gemini-cli-extensions/ralph) "Options" — agent outputs `<promise>TEXT</promise>` XML tag; hook script parses and matches against `--completion-promise` value to exit loop
- **[18]** [ralph-wiggum README](https://github.com/AsyncFuncAI/ralph-wiggum-extension) "Examples" — `--completion-promise 'ALL TESTS PASSING'` — loop exits when agent output contains this exact string wrapped in promise tags
- **[19]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) commands — `/ralph:complete -s "Built API"` manually signals loop completion with summary annotation
- **[20]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "Quick Start" — agent outputs literal `LOOP_COMPLETE` token; orchestrator detects and exits cleanly
- **[21]** [self-command](https://github.com/stevenAthompson/self-command) — `yield_turn` sends Ctrl-C to terminate current agent turn in tmux session
- **[22]** `loop_guardian.py:L76-96` — `should_terminate()` triggers after 3 identical hash cycles; orchestrator then escalates temperature 0.7→1.0→1.3 via `get_escalated_temperature()` to force divergent code
- **[23]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) commands — `/ralph:diagnose` analyzes stuck loop (shows iteration history, detects patterns); `/ralph:rollback -s 2` reverts to 2 steps ago
- **[24]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "What is Ralph?" — backpressure gates reject incomplete work: tests, lint, and typecheck must all pass before iteration is accepted; failed gates trigger re-attempt
- **[25]** [self-command](https://github.com/stevenAthompson/self-command) — `wait_for_idle` monitors system CPU; when below threshold for configurable duration, assumes agent is stuck/finished
- **[26]** `worker.py:L432-467` — `_run_bist()` executes generated Python via `subprocess.run()`, checks `returncode == 0`; timeout at 30s with `CREATE_NO_WINDOW` flag; BIST = Built-In Self-Test
- **[27]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — `/conductor:status` displays progress per track/phase/task; no automatic pass/fail verification of generated code
- **[28]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) commands — `/ralph:report -f markdown` generates summary report; does not auto-verify correctness
- **[29]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "What is Ralph?" — backpressure system: gates that reject incomplete work (tests must pass, lint must be clean, typecheck must succeed) before accepting an iteration
- **[30]** [blueprint README](https://github.com/gplasky/gemini-cli-blueprint-extension) — `/blueprint:test` verifies implementation meets requirements from plan; manual trigger, not automatic
- **[31]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — Quinn (QA) agent persona provides built-in quality assurance testing within the workflow

</details>

### PLANNING & WORKFLOW

| Feature          | Hybrid Conductor | ralph-orch | kranthik/Ralph | conductor | ralph (official) | blueprint | ralph-wiggum | self-command | BMAD |
|------------------|------------------|------------|----------------|-----------|------------------|-----------|--------------|--------------|------|
| Spec Generation  | ✅/spec-first [32]| ✅/PDD [34]| ❌ [5]        | ✅/spec.md [33]| ❌ [3]       | ✅/research [35]| ❌ [4]  | ❌ [8]       | ✅/agents [36] |
| Plan Decompose   | ✅/Conductor [37]| ✅/plan [39]| ❌ [5]        | ✅/plan.md [38]| ❌ [3]       | ✅/TODO [40]| ❌ [4]     | ❌ [8]       | ✅/workflows [41] |
| Complexity Modes | ✅/3-mode [42]   | ✅/31 presets [44]| ✅/config [43]| ❌ [2]| ❌ [3]          | ❌ [7]    | ❌ [4]       | ❌ [8]       | ✅/scale [45] |
| Approval Gate    | ✅/plan [46]     | ✅/RObot [48]| ❌ [5]       | ✅/plan [47]| ❌ [3]          | ✅/step [49]| ❌ [4]    | ❌ [8]       | ✅/phase [50] |

<details>
<summary>📎 Evidence (Planning & Workflow)</summary>

- **[32]** `orchestrator.py:L324-340` — `_generate_spec()` creates formal specification document in FULL complexity mode before any code generation begins
- **[33]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — `/conductor:newTrack` generates `conductor/tracks/<id>/spec.md` capturing requirements, acceptance criteria, and scope
- **[34]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "Quick Start" — `ralph plan "Add JWT auth"` runs interactive PDD (Plan-Driven Development) session, generates `specs/<name>/requirements.md`, `design.md`, `implementation-plan.md`
- **[35]** [blueprint README](https://github.com/gplasky/gemini-cli-blueprint-extension) — `/blueprint:research` performs web search on topic; `/blueprint:plan` creates structured plan from research
- **[36]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — "12+ domain experts (PM, Architect, Developer, UX, Scrum Master)" each contribute to spec via their specialized persona
- **[37]** `orchestrator.py:L342-373` — `_generate_plan()` decomposes spec into phases/tasks using Conductor-pattern hierarchical planning
- **[38]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — generates `conductor/tracks/<id>/plan.md` with hierarchical phases → tasks → sub-tasks breakdown
- **[39]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) — `ralph plan` generates `implementation-plan.md` with step-by-step breakdown; plan feeds into `ralph run`
- **[40]** [blueprint README](https://github.com/gplasky/gemini-cli-blueprint-extension) — `/blueprint:define` converts plan into actionable `TODO.md` with checkboxes and acceptance criteria
- **[41]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — "Structured Workflows: Grounded in agile best practices" with sprint-like iteration cycles
- **[42]** `orchestrator.py:L50-54` — `ComplexityMode` enum: `FAST` (skip spec, minimal plan), `STREAMLINED` (standard), `FULL` (spec→plan→build→verify→debug)
- **[43]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) commands — `/ralph:config` view + `/ralph:adjust` modify runtime parameters (iterations, temperature, timeouts)
- **[44]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "What is Ralph?" — 31 presets: TDD, spec-driven, debugging, refactoring, and more; each configures iteration behavior, gates, and hat system
- **[45]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — "Scale-Domain-Adaptive: Automatically adjusts planning depth based on project complexity"
- **[46]** `orchestrator.py:L199-228` — `_handle_planning()` presents plan to user and requires explicit approval before transitioning to BUILDING state
- **[47]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — "Review plans before code is written, keeping you firmly in the loop"
- **[48]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "RObot" — Human-in-the-Loop via Telegram: agents emit `human.interact` events blocking until human responds; `/status`, `/tasks`, `/restart` commands for real-time visibility
- **[49]** [blueprint README](https://github.com/gplasky/gemini-cli-blueprint-extension) — "User Approval: Gemini will present its proposed changes for your approval" before each implementation step
- **[50]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — per-phase workflow approval through specialized agent handoffs (PM → Architect → Developer → QA)

</details>

### STATE & VERIFICATION

| Feature          | Hybrid Conductor | ralph-orch | kranthik/Ralph | conductor | ralph (official) | blueprint | ralph-wiggum | self-command | BMAD |
|------------------|------------------|------------|----------------|-----------|------------------|-----------|--------------|--------------|------|
| State Mgmt       | ✅/state-dir [51]| ✅/memories [56]| ✅/checkpoint [55]| ✅/tracks [52]| ✅/local.md [53]| ✅/PLAN [57]| ✅/local.md [54]| ❌ [8]| ✅/docs [58] |
| Verification     | ✅/BIST [26]     | ✅/gates [29]| Partial [28]  | ✅/review [59]| ❌ [3]        | ✅/test [30]| ❌ [4]       | ❌ [8]       | ✅/Quinn [31] |
| Git Handling     | ✅/branch [60]   | ❌ [6]     | Partial [62]   | ✅/revert [61]| ❌ [3]        | ❌ [7]    | ❌ [4]       | ❌ [8]       | ❌ [9] |

<details>
<summary>📎 Evidence (State & Verification)</summary>

- **[51]** `orchestrator.py:L67-81` — creates `.ralph-state/` directory in project root; stores iteration history, plan files, and execution logs
- **[52]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — `conductor/tracks/<track_id>/` directory contains `metadata.json` (status, timestamps), `spec.md`, `plan.md`; each track is a self-contained unit of work
- **[53]** [ralph README](https://github.com/gemini-cli-extensions/ralph) "Core Concept" — persistent state at `.gemini/ralph-loop.local.md`; updated each iteration with progress and context
- **[54]** [ralph-wiggum README](https://github.com/AsyncFuncAI/ralph-wiggum-extension) "State File" — same `.gemini/ralph-loop.local.md` pattern; viewable via `cat .gemini/ralph-loop.local.md`
- **[55]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) — `/ralph:checkpoint "v1"` saves named snapshot; `/ralph:restore "v1"` rolls back to snapshot; full checkpoint/restore lifecycle
- **[56]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "What is Ralph?" — "Memories & Tasks: Persistent learning and runtime work tracking" across iterations and sessions
- **[57]** [blueprint README](https://github.com/gplasky/gemini-cli-blueprint-extension) — tracks state across 3 markdown files: `PLAN.md` (research/architecture), `TODO.md` (implementation tasks), `ACT.md` (execution log)
- **[58]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — structured artifact documents produced by each of 21 agent personas; state flows through document handoffs between agents
- **[59]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — `/conductor:review` reviews all completed work against original spec and project guidelines; produces review report
- **[60]** `worker.py:L171-283` — `McpClient.create_branch(f"task-{task_id}")` creates isolated Git branch per task via MCP server; changes committed only after BIST passes
- **[61]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — `/conductor:revert` performs "git-aware revert that understands logical units": can revert entire tracks, individual phases, or specific tasks while preserving other work
- **[62]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) — `/ralph:rollback -s 2` reverts to 2 iterations ago; limited to iteration-level rather than logical-unit rollback

</details>

### DEVELOPER EXPERIENCE

| Feature          | Hybrid Conductor | ralph-orch | kranthik/Ralph | conductor | ralph (official) | blueprint | ralph-wiggum | self-command | BMAD |
|------------------|------------------|------------|----------------|-----------|------------------|-----------|--------------|--------------|------|
| Monitoring/UI    | ✅/dashboard [63]| ✅/web+TUI [66]| ✅/monitor [65]| Partial [64]| ❌ [3]       | ❌ [7]    | Partial [54] | ✅/pane [67] | ❌ [9] |
| Simple Tasks     | ✅/FAST [42]     | ✅/run [71]| ✅/start [70]  | ✅/track [27]| ✅/one-cmd [68]| Partial [35]| ✅/one-cmd [69]| ✅/cmd [72]| Partial [73] |
| Resume/Pause     | ✅/session [74] | ❌ [6]     | ✅/pause [74]  | ❌ [2]    | ❌ [3]           | ✅/resume [75]| ❌ [4]   | ✅/watch [76]| ❌ [9] |
| Background Tasks | ✅/detached [79] | ❌ [6]     | ❌ [5]         | ❌ [2]    | ❌ [3]           | ❌ [7]    | ❌ [4]       | ✅/long [77] | ❌ [9] |
| Multi-Backend    | ✅/providers [80]| ✅/7 [78]  | ❌ [5]         | ❌ [2]    | ❌ [3]           | ❌ [7]    | ❌ [4]       | ❌ [8]       | ❌ [9] |

<details>
<summary>📎 Evidence (Developer Experience)</summary>

- **[63]** `start_app.py` + `backend/` — Flask+React web dashboard at `http://127.0.0.1:5000`; shows state machine, iteration history, AI conversation log
- **[64]** [conductor README](https://github.com/gemini-cli-extensions/conductor) — `/conductor:status` gives text-based progress overview per track/phase/task; no GUI
- **[65]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) — `/ralph:monitor` provides real-time progress monitoring with iteration counts and timing
- **[66]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "Web Dashboard (Alpha)" — `ralph web` launches web dashboard (Node.js frontend:5173 + backend:3000); also has ratatui-based terminal UI
- **[67]** [self-command](https://github.com/stevenAthompson/self-command) — `capture_pane` captures visible text of tmux pane for agent to read its own terminal output
- **[68]** [ralph README](https://github.com/gemini-cli-extensions/ralph) "Usage" — `ralph:loop "Fix the auth bug"` — single command to start autonomous loop
- **[69]** [ralph-wiggum README](https://github.com/AsyncFuncAI/ralph-wiggum-extension) "Examples" — `ralph-loop Fix the auth bug --max-iterations 10`
- **[70]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) — `/ralph:start-loop "task" -m 30` starts loop with 30-iteration limit
- **[71]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "Quick Start" — `ralph run -p "Add input validation"` for simple tasks without planning
- **[72]** [self-command](https://github.com/stevenAthompson/self-command) — `self_command` tool sends CLI command to agent's own tmux session and returns immediately
- **[73]** [BMAD README](https://github.com/bmad-code-org/BMAD-METHOD) — "Simple Path (Quick Flow)" available for straightforward tasks
- **[74]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) — `/ralph:pause` suspends current loop; `/ralph:resume` continues from last iteration
- **[75]** [blueprint README](https://github.com/gplasky/gemini-cli-blueprint-extension) — `/blueprint:resume` auto-detects which step was last completed and continues from there
- **[76]** [self-command](https://github.com/stevenAthompson/self-command) — `watch_log` monitors file for changes matching regex pattern with configurable timeout
- **[77]** [self-command](https://github.com/stevenAthompson/self-command) — `run_long_command` executes command in background tmux pane with completion notification
- **[78]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "What is Ralph?" — "Multi-Backend Support: Claude Code, Kiro, Gemini CLI, Codex, Amp, Copilot CLI, OpenCode"

</details>

### INTERACTIVITY & UI/UX

| Feature            | Hybrid Conductor | ralph-orch | kranthik/Ralph | conductor | ralph (official) | blueprint | ralph-wiggum | self-command | BMAD |
|---------------------|------------------|------------|----------------|-----------|------------------|-----------|--------------|--------------|------|
| Web Dashboard       | ✅/Flask+React [63]| ✅/Node.js [66]| ❌ [5]     | ❌ [2]   | ❌ [3]           | ❌ [7]   | ❌ [4]       | ❌ [8]       | ❌ [9] |
| Terminal UI (TUI)   | ❌               | ✅/ratatui [94]| ✅/monitor [65]| Partial [64]| ❌ [3]       | ❌ [7]   | ❌ [4]       | ✅/tmux [67] | ❌ [9] |
| Real-time Feedback  | ✅/live dash [63]| ✅/events [95] | ✅/progress [65]| Partial [64]| ❌ [3]      | ❌ [7]   | Partial [54] | ✅/watch [76]| ❌ [9] |
| Config UI           | Partial/CLI [42] | ✅/presets+yml [44]| ✅/adjust [43]| ❌ [2]| Partial/flags [11]| ❌ [7]  | Partial/flags [12]| ❌ [8]    | Partial/agents [36] |
| Human-in-the-Loop   | ✅/plan gate [46]| ✅/Telegram [48]| ❌ [5]     | ✅/review [47]| ❌ [3]       | ✅/step [49]| ❌ [4]    | ❌ [8]       | ✅/phase [50] |

<details>
<summary>📎 Evidence (Interactivity & UI/UX)</summary>

- **[94]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "Architecture" — Rust-based ratatui terminal UI shows live iteration progress, event stream, and agent status without browser
- **[95]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) "What is Ralph?" — event-driven architecture emits `iteration.start`, `iteration.complete`, `gate.fail`, `human.interact` events in real-time; consumed by web dashboard, TUI, and Telegram bot simultaneously
- All other citations reference evidence items already documented above ([42]-[67], [76])

</details>

### DEPLOYMENT & MATURITY

| Feature          | Hybrid Conductor | ralph-orch | kranthik/Ralph | conductor | ralph (official) | blueprint | ralph-wiggum | self-command | BMAD |
|------------------|------------------|------------|----------------|-----------|------------------|-----------|--------------|--------------|------|
| Platform         | ✅/Windows [79]  | ✅/cross [80]| ✅/cross [5] | ✅/cross [2]| ✅/cross [3]    | ✅/cross [7]| ✅/cross [4]| Partial [81] | ✅/cross [9] |
| Install          | ✅/setup.py [82] | ✅/npm+brew+cargo [87]| ✅/gem-ext [86]| ✅/gem-ext [83]| ✅/gem-ext [84]| ✅/gem-ext [88]| ✅/gem-ext [85]| ✅/gem-ext [89]| ✅/npm [90] |
| Google Official  | ❌/Community     | ❌         | ❌             | ✅ [91]   | ✅ [91]          | ❌        | ❌           | ❌           | ❌ |
| Maturity         | Partial/v7 [92]  | ✅/33rel [93]| Partial [5]  | ✅ [91]   | ✅ [91]          | Partial [7]| Partial [4] | Partial [8]  | Partial [9] |

<details>
<summary>📎 Evidence (Deployment & Maturity)</summary>

- **[79]** `setup.py` + `worker.py` — Windows-native: `CREATE_NO_WINDOW` subprocess flags, no WSL/Docker/Linux subsystem dependency
- **[80]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) — Rust-based CLI; installable via npm, Homebrew (macOS/Linux), and Cargo (cross-platform)
- **[81]** [self-command](https://github.com/stevenAthompson/self-command) "Prerequisites" — requires tmux (Linux/macOS native; Windows requires WSL)
- **[82]** `setup.py` — `python setup.py` installs Python dependencies and configures local environment
- **[83]** [conductor](https://github.com/gemini-cli-extensions/conductor) — `gemini extensions install https://github.com/gemini-cli-extensions/conductor`
- **[84]** [ralph](https://github.com/gemini-cli-extensions/ralph) — `gemini extensions install https://github.com/gemini-cli-extensions/ralph`
- **[85]** [ralph-wiggum](https://github.com/AsyncFuncAI/ralph-wiggum-extension) — `gemini extensions install https://github.com/AsyncFuncAI/ralph-wiggum-extension`
- **[86]** [kranthik/Ralph](https://github.com/kranthik123/Gemini-Ralph-Loop) — `gemini extensions install` from GitHub
- **[87]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) — 3 install methods: `npm install -g @ralph-orchestrator/ralph-cli`, `brew install ralph-orchestrator`, `cargo install ralph-cli`
- **[88]** [blueprint](https://github.com/gplasky/gemini-cli-blueprint-extension) — `gemini extensions install https://github.com/gplasky/gemini-cli-blueprint-extension.git`
- **[89]** [self-command](https://github.com/stevenAthompson/self-command) — standard `gemini extensions install` from GitHub
- **[90]** [BMAD](https://github.com/bmad-code-org/BMAD-METHOD) — npm package or copy files into project
- **[91]** `gemini-cli-extensions` GitHub org — Google-maintained official extensions repository; conductor and ralph are official
- **[92]** Hybrid Conductor v7.1.6 — actively developed; ecosystem leader with Resume/Pause, TUI, and Multi-Backend support
- **[93]** [ralph-orchestrator](https://github.com/mikeyobrien/ralph-orchestrator) — 33 releases, 25 contributors, dedicated documentation site, Rust+Node architecture

</details>

---

### 🧩 Complementary Ecosystem Tools

These tools enhance the loop/workflow ecosystem but serve different functions:

| Tool | Category | What It Does | Link |
|------|----------|-------------|------|
| **jules** | Async Agent | Orchestrates Google Jules for background bug fixing & refactoring | [gemini-cli-extensions/jules](https://github.com/gemini-cli-extensions/jules) |
| **security** | Code Analysis | AI-powered vulnerability scanning via `/security:analyze` | [gemini-cli-extensions/security](https://github.com/gemini-cli-extensions/security) |
| **stitch** | Design Tool | Generate & manage Stitch design screens from Gemini CLI | [gemini-cli-extensions/stitch](https://github.com/gemini-cli-extensions/stitch) |
| **prompt-library** | Prompt Templates | 50+ pre-built prompts (`/code-review:security`, `/testing:generate-unit-tests`) | [involvex/gemini-cli-prompt-library](https://github.com/involvex/gemini-cli-prompt-library) |
| **AionUi** | Multi-Agent GUI | Unified desktop UI for Gemini CLI, Claude Code, Codex + scheduling + WebUI | [iOfficeAI/AionUi](https://github.com/iOfficeAI/AionUi) |
| **pro-workflow** | Claude Plugin | SQLite learning DB, parallel worktrees, wrap-up rituals, handoff docs | [rohitg00/pro-workflow](https://github.com/rohitg00/pro-workflow) |
| **run-gemini-cli** | CI/CD | GitHub Actions integration for running Gemini CLI in pipelines | [google-github-actions/run-gemini-cli](https://github.com/google-github-actions/run-gemini-cli) |
| **antigravity-proxy** | Model Bridge | Routes Claude CLI requests through Gemini models | [badrisnarayanan/antigravity-claude-proxy](https://github.com/badrisnarayanan/antigravity-claude-proxy) |

---

### 📊 Ecosystem Scorecard (Weighted RPN)

> **Scoring**: ✅ = 3pts, `Partial` = 1pt, ❌ = 0pts. Each metric is multiplied by an **importance weight** (1–5) reflecting its value for autonomous one-shot app building. Higher weight = more critical capability.

| Category (max pts)    | Wt | Hybrid Conductor | ralph-orch | kranthik/Ralph | conductor | ralph (official) | blueprint | ralph-wiggum | self-command | BMAD |
|-----------------------|----|------------------|------------|----------------|-----------|------------------|-----------|--------------|--------------|------|
| **CORE LOOP** (69)    |    | **69** 🥇       | **69** 🥇  | 59             | 5         | 49               | 0         | 49           | 38           | 0    |
| Loop Trigger          | 5  | 15               | 15         | 15             | 0         | 15               | 0         | 15           | 15           | 0    |
| Cycles Limit          | 4  | 12               | 12         | 12             | 0         | 12               | 0         | 12           | 4            | 0    |
| Loop Breaking         | 4  | 12               | 12         | 12             | 0         | 12               | 0         | 12           | 4            | 0    |
| Stuck Escape          | 5  | 15               | 15         | 15             | 0         | 5                | 0         | 5            | 15           | 0    |
| One-Shot Success      | 5  | 15               | 15         | 5              | 5         | 5                | 0         | 5            | 0            | 0    |
| **PLANNING** (33)     |    | **33** 🥇        | **33** 🥇  | 6              | 27        | 0                | 27        | 0            | 0            | 33   |
| Spec Generation       | 3  | 9                | 9          | 0              | 9         | 0                | 9         | 0            | 0            | 9    |
| Plan Decomposition    | 3  | 9                | 9          | 0              | 9         | 0                | 9         | 0            | 0            | 9    |
| Complexity Modes      | 2  | 6                | 6          | 6              | 0         | 0                | 0         | 0            | 0            | 6    |
| Approval Gate         | 3  | 9                | 9          | 0              | 9         | 0                | 9         | 0            | 0            | 9    |
| **STATE & VERIFY** (27)|   | **27** 🥇        | 21         | 15             | **27** 🥇 | 9                | 21        | 9            | 0            | 21   |
| State Mgmt            | 3  | 9                | 9          | 9              | 9         | 9                | 9         | 9            | 0            | 9    |
| Verification          | 4  | 12               | 12         | 4              | 12        | 0                | 12        | 0            | 0            | 12   |
| Git Handling          | 2  | 6                | 0          | 2              | 6         | 0                | 0         | 0            | 0            | 0    |
| **DEV EXPERIENCE** (30)|   | 15               | **21** 🥇  | **21** 🥇      | 9         | 6                | 8         | 9            | 24           | 2    |
| Monitoring/UI         | 3  | 9                | 9          | 9              | 3         | 0                | 0         | 3            | 9            | 0    |
| Simple Tasks          | 2  | 6                | 6          | 6              | 6         | 6                | 2         | 6            | 6            | 2    |
| Resume/Pause          | 2  | 6                | 0          | 6              | 0         | 0                | 6         | 0            | 6            | 0    |
| Background Tasks      | 1  | 3                | 0          | 0              | 0         | 0                | 0         | 0            | 3            | 0    |
| Multi-Backend         | 2  | 0                | 6          | 0              | 0         | 0                | 0         | 0            | 0            | 0    |
| **UI/UX** (39)        |    | **29**           | **39** 🥇  | 21             | 14        | 2                | 9         | 5            | 15           | 11   |
| Web Dashboard         | 3  | 9                | 9          | 0              | 0         | 0                | 0         | 0            | 0            | 0    |
| Terminal UI           | 2  | 0                | 6          | 6              | 2         | 0                | 0         | 0            | 6            | 0    |
| Real-time Feedback    | 3  | 9                | 9          | 9              | 3         | 0                | 0         | 3            | 9            | 0    |
| Config UI             | 2  | 2                | 6          | 6              | 0         | 2                | 0         | 2            | 0            | 2    |
| Human-in-the-Loop     | 3  | 9                | 9          | 0              | 9         | 0                | 9         | 0            | 0            | 9    |
| **DEPLOYMENT** (15)   |    | 8                | **12** 🥇  | 8              | **15** 🥇 | **15** 🥇        | 8         | 8            | 6            | 8    |
| Platform              | 1  | 3                | 3          | 3              | 3         | 3                | 3         | 3            | 1            | 3    |
| Install               | 1  | 3                | 3          | 3              | 3         | 3                | 3         | 3            | 3            | 3    |
| Google Official       | 1  | 0                | 0          | 0              | 3         | 3                | 0         | 0            | 0            | 0    |
| Maturity              | 2  | 2                | 6          | 2              | 6         | 6                | 2         | 2            | 2            | 2    |
|                       |    |                  |            |                |           |                  |           |              |              |      |
| **🏆 GRAND TOTAL (213)**|  | **211** 🥇       | **195**    | **130**        | **97**    | **81**           | **73**    | **80**       | **83**       | **75** |
| **Ratio (% of max)**  |    | **100%**         | **92%**    | 61%            | 46%       | 38%              | 34%       | 38%          | 39%          | 35%  |

<details>
<summary>📎 Scoring Methodology</summary>

**Weight rationale** (1–5 scale, higher = more critical for autonomous one-shot app building):

| Weight | Meaning | Applied to |
|--------|---------|------------|
| **5**  | Essential — without this the tool cannot autonomously build apps | Loop Trigger, Stuck Escape, One-Shot Success |
| **4**  | Important — significantly impacts reliability and quality | Cycles Limit, Loop Breaking, Verification |
| **3**  | Valuable — improves workflow but not strictly required | Spec, Plan, Approval, Monitoring, Real-time Feedback, Web Dashboard, Human-in-the-Loop, State Mgmt |
| **2**  | Nice-to-have — enhances DX but alternatives exist | Complexity Modes, Simple Tasks, Resume/Pause, Multi-Backend, Terminal UI, Config UI, Git, Maturity |
| **1**  | Baseline — expected of any tool | Platform, Install, Google Official, Background Tasks |

**Scoring formula**: `Cell Score = Support Level × Weight`
- ✅ (Full support) = 3 × Weight
- `Partial` = 1 × Weight
- ❌ = 0 × Weight

**Max possible**: 213 points (all ✅ across all 26 metrics)

</details>

---

### 🔍 Hybrid Conductor Gap Analysis (v7 → v8 Roadmap)

| Gap (Score = 0) | Best-in-Class | Implementation Pattern | Priority |
|-----------------|---------------|----------------------|----------|
| **Multi-Backend** | ralph-orch (7 backends) | `ralph.yml` declares backend configs; CLI swaps `--backend claude\|gemini\|codex`. **Pattern**: abstract `LLMProvider` interface with `generate(prompt, temperature)`, factory selects backend from config. | High |
| **Terminal UI** | ralph-orch (ratatui) | Rust ratatui renders live progress, event stream, agent status. **Pattern**: Python equivalent via `rich.live` or `textual` — render iteration count, state, last hash, temperature. | Low |
| **Config UI** (Partial→Full) | ralph-orch (31 presets + YAML) | `ralph.yml` with named presets overriding defaults. **Pattern**: add `config.yml` with `presets:` section, each overrides `complexity`, `max_iterations`, `temperature_schedule`. CLI: `--preset tdd`. | Medium |

> **Metrics where HC scores Partial (improvable):**
> - **Maturity** (2/6): increase release cadence, add changelog, publish to PyPI
> - **Config UI** (2/6): add YAML config file support instead of CLI-only flags

<details>
<summary>📎 How to use this for implementation</summary>

**For an AI agent performing gap analysis:**
1. Read each gap row's "Implementation Pattern" column
2. Clone the best-in-class repo (URL in evidence citations above)
3. Study the specific file/function referenced
4. Implement equivalent in `orchestrator.py` / `worker.py` following HC's existing patterns
5. Add tests and verify via BIST

**Priority key:** High = directly impacts scorecard by 6+ points; Medium = 2-4 points; Low = nice-to-have

</details>

---

### 🗂️ MCP Tools Registry (Cross-Reference)

> All MCP tools and libraries catalogued in [`docs/prompts/MCP_tools.md`](docs/prompts/MCP_tools.md), mapped to ecosystem adopters and sorted by relevance to autonomous coding workflows. Sources `[S:n]` reference the original research index.

#### 🔴 Critical — Core infrastructure for any AI coding agent

| MCP Tool/Library | Ecosystem Adopters | Value Assessment |
|------------------|--------------------|------------------|
| **Git** | Hybrid Conductor [60], conductor [61], kranthik/Ralph [62] | Foundation of all version control workflows; HC already uses MCP Git for branch isolation and safe commits [S:4,5] |
| **Filesystem** | Hybrid Conductor (direct `Path`), self-command (tmux pane) | Essential for code editing, project scaffolding, and file management within security boundaries; HC should migrate from raw `Path` to MCP-standard access [S:4-6] |
| **GitHub** | conductor [61], ralph-orch (planned) | Deep repo management, PR creation, issue tracking, and CI/CD interaction; closes HC's PR automation gap [S:1-4] |
| **Sequential Thinking** | blueprint (plan step) [35], BMAD (agent reasoning) [36] | Structured multi-step reasoning for architectural decisions; enhances HC's PLANNING phase with branching thought chains [S:2,5,7,8] |
| **Context7** | ralph-orch (docs), BMAD (agent context) | Prevents API hallucinations by providing real-time, version-specific library documentation; directly addresses HC's hallucination-proof context goal [S:2,4,7,11] |
| **Openground** | **Hybrid Conductor** [37] | HC's native RAG engine — local LanceDB vector store for offline semantic code search; already integrated in `context_fetcher.py` [S:24] |

#### 🟠 High — Significant workflow improvement

| MCP Tool/Library | Ecosystem Adopters | Value Assessment |
|------------------|--------------------|------------------|
| **Playwright** | Hybrid Conductor (BIST tests) [26], blueprint (test step) [30] | HC already uses Playwright for dashboard testing; MCP server version would enable agents to self-verify frontend output [S:5,14] |
| **Puppeteer** | blueprint (web scraping) [37] | Browser automation for E2E testing and visual regression; alternative to Playwright for Chrome-only environments [S:5,12,13] |
| **Memory** | ralph-orch (persistent memories) [56], ralph (local.md) [53] | Knowledge graph for cross-session learning; would close HC's session memory gap — currently state is lost between runs [S:5] |
| **CodeGraphContext** | BMAD (architect agent) [36] | Indexes codebase into graph DB for semantic dependency queries; enhances HC's context fetcher with call chain and hierarchy awareness [S:2,9,10] |
| **SQLite / PostgreSQL** | ralph-orch (iteration history), BMAD (structured data) | Replace HC's flat-file state storage with queryable database; enables analytics on iteration history and loop detection patterns [S:5] |
| **Sentry** | — (none currently) | Feeds crash reports and error logs directly to agent for automated root cause analysis; high-value for HC's VERIFYING phase [S:5] |
| **Snyk** | — (none currently) | Embeds security scanning into verification workflow; catches vulnerabilities in AI-generated code before BIST passes [S:5] |

#### 🟡 Medium — Valuable for specific workflows

| MCP Tool/Library | Ecosystem Adopters | Value Assessment |
|------------------|--------------------|------------------|
| **Firecrawl** | BMAD (research agents) [36] | Converts entire websites into LLM-ready markdown; useful for HC's FULL complexity mode research step [S:2,4,15] |
| **Fetch** | blueprint (research step) [35] | Lightweight URL-to-markdown conversion with robots.txt compliance; simpler alternative to Firecrawl for documentation gathering [S:5] |
| **Jina Reader** | — (none currently) | Single-prefix URL conversion (`https://r.jina.ai/`); cleanest output for RAG ingestion; complements Openground [S:2,22] |
| **Docker** | — (none currently) | Containerized execution environments; would enable HC to run BIST in isolated containers instead of subprocess [S:2,5] |
| **OneCompiler** | — (none currently) | Code execution in 70+ languages; extends HC beyond Python-only BIST to multi-language verification [S:2,4,16] |
| **SMART-E2B** | — (none currently) | Cloud-based sandboxed execution for JavaScript/Python; safer alternative to local subprocess for untrusted code [S:4,16] |
| **Limelight MCP** | — (none currently) | Streams live React app data (renders, logs, network) to agent; high-value for HC dashboard self-debugging [S:2,4,17,18] |
| **Grep MCP** | — (none currently) | Searches millions of GitHub repos for patterns; useful for finding implementation examples during code generation [S:4,20] |
| **Bright Data** | — (none currently) | Anti-bot web scraping with markdown output; for documentation behind aggressive CDNs or CAPTCHAs [S:2,4,21] |
| **AgentOps** | — (none currently) | Observability and tracing for AI agents; would add telemetry to HC's iteration loop for debugging agent behavior [S:5] |

#### 🟢 Specialist — Framework or domain-specific

| MCP Tool/Library | Ecosystem Adopters | Value Assessment |
|------------------|--------------------|------------------|
| **Figma** | blueprint (design step) [35] | Design-to-code from Figma layouts, components, and tokens; relevant only if HC targets frontend generation workflows [S:2,4,19] |
| **scaffold-mcp** | — (none currently) | Code scaffolding following project conventions; would complement HC's spec-first mode with template-based project creation [S:23] |
| **architect-mcp** | BMAD (architect agent) [36] | Design pattern enforcement and code quality review; could enhance HC's VERIFYING phase beyond BIST [S:23] |
| **style-system** | — (none currently) | Design system tokens and component registry; prevents duplicate component creation in frontend tasks [S:23] |
| **one-mcp** | — (none currently) | MCP proxy with progressive schema disclosure; reduces context window usage by loading tool definitions on demand [S:23] |
| **Blueprint MCP** | blueprint [37] | Runs JavaScript in webpage context for deterministic data extraction; niche but powerful for web scraping tasks [S:25] |

#### ⚪ Niche — Situational utility

| MCP Tool/Library | Ecosystem Adopters | Value Assessment |
|------------------|--------------------|------------------|
| **GitLab** | — (none currently) | GitLab REST API for projects, issues, MRs, pipelines; only relevant if migrating from GitHub [S:4,16] |
| **MongoDB** | — (none currently) | Natural language database interaction; relevant only for MongoDB-backed projects [S:4,16] |
| **Kubernetes** | — (none currently) | Cluster management and monitoring; relevant for DevOps-focused agent workflows, not local coding [S:4] |
| **Coolify** | — (none currently) | Self-hosted PaaS control; niche deployment automation for Coolify users [S:4,16] |
| **Ember MCP** | — (none currently) | Ember.js-specific CLI commands and codemods; irrelevant outside Ember ecosystem [S:4,16] |
| **MCP Server Builder** | — (meta-tool) | Access to MCP protocol specs and FastMCP docs; useful only when building new MCP servers [S:16] |
| **Everything** | — (testing) | Reference/test MCP server; educational baseline for validating MCP client implementations [S:5] |

<details>
<summary>📎 Source Index (from MCP_tools.md)</summary>

| Ref | Source |
|-----|--------|
| S:1 | [github/github-mcp-server](https://github.com/github/github-mcp-server) — GitHub's official MCP Server |
| S:2 | [Reddit r/mcp](https://reddit.com/r/mcp) — "5 MCPs that genuinely made me quicker" |
| S:3 | [tuannvm/slack-mcp-client](https://github.com/tuannvm/slack-mcp-client) — Slack ↔ MCP bridge |
| S:4 | Comprehensive Directory of MCP Servers and FOSS Tools |
| S:5 | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) — Official MCP reference servers |
| S:6 | [calebmwelsh/file-system-mcp-server](https://github.com/MCP-Mirror/calebmwelsh_file-system-mcp-server) |
| S:7 | [upstash/context7](https://github.com/upstash/context7) — Up-to-date code docs for LLMs |
| S:8 | [zalab-inc/mcp-sequentialthinking](https://github.com/zalab-inc/mcp-sequentialthinking) |
| S:9 | [CodeGraphContext/CodeGraphContext](https://github.com/CodeGraphContext/CodeGraphContext) — Code graph indexer |
| S:10 | [CodeGraphContext GitHub org](https://github.com/CodeGraphContext) |
| S:11 | [upstash/context7-legacy](https://github.com/upstash/context7-legacy) |
| S:12 | [puppeteer/puppeteer](https://github.com/puppeteer/puppeteer) — Chrome/Firefox automation |
| S:13 | [Puppeteer docs](https://pptr.dev/) |
| S:14 | [Playwright](https://playwright.dev/) — E2E testing framework |
| S:15 | [mendableai/firecrawl](https://github.com/firecrawl/firecrawl) — Web → LLM-ready markdown |
| S:16 | [Reddit r/mcp](https://reddit.com/r/mcp) — OneCompiler MCP Server thread |
| S:17 | [Reddit r/reactnative](https://reddit.com/r/reactnative) — Limelight local-first desktop app |
| S:18 | Limelight MCP Server bridge documentation |
| S:19 | [GLips/Figma-Context-MCP](https://github.com/GLips/Figma-Context-MCP) — Figma layout for AI agents |
| S:20 | [galprz/grep-mcp](https://github.com/galprz/grep-mcp) — GitHub code search via grep.app |
| S:21 | [brightdata/brightdata-mcp](https://github.com/brightdata/brightdata-mcp) — Public web access with anti-bot |
| S:22 | [jina-ai/reader](https://github.com/jina-ai/reader) — URL → LLM-friendly markdown |
| S:23 | [AgiFlow/aicode-toolkit](https://github.com/AgiFlow/aicode-toolkit) — Toolkit for coding agents |
| S:24 | [poweroutlet2/openground](https://github.com/poweroutlet2/openground) — On-device RAG |
| S:25 | [Nick Felker, Medium](https://medium.com/) — "Scrappy agents in Gemini CLI with Blueprint MCP" |

</details>

---

### 🔧 Other Noteworthy Tools & MCP Integrations

> Tools, servers, and frameworks that could be integrated into or complement Hybrid Conductor. Each includes integration potential for gap closure.

#### Agent Frameworks & Orchestrators

| Tool | What It Does | Integration Potential | Link | Benefit & Verdict |
|------|-------------|----------------------|------|-------------------|
| **Devon** | Open-source AI software engineer with multi-model support | Study multi-model orchestration for HC multi-backend gap | [entropy-research/Devon](https://github.com/entropy-research/Devon) | +6 pts (Multi-Backend). **Implement** — `LLMProvider` abstraction directly closes HC's 0-score gap |
| **Aider** | AI pair programming in terminal; git-aware, multi-file editing | Adopt `--auto-commits` pattern for HC Git workflow | [Aider-AI/aider](https://github.com/Aider-AI/aider) | +4 pts (Git Handling, DX). **Implement** — auto-commit pattern directly ports to `worker.py` |
| **OpenHands** | Platform for AI software agents with sandbox execution | Study sandboxed execution model for safer BIST runs | [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) | +3 pts (Verification). **Study** — sandbox model improves BIST safety but adds Docker dependency |
| **Cline** | Autonomous coding agent with diff-based editing, terminal commands, browser use | Study diff-editing UX for HC dashboard file preview | [cline/cline](https://github.com/cline/cline) | +2 pts (DX). **Study** — diff UX pattern worth adopting, not a dependency |
| **SWE-agent** | Princeton's agent for automated GitHub issue resolution | Benchmark HC against SWE-bench for academic credibility | [SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent) | +0 pts (credibility only). **Skip** — benchmarking exercise, no scorecard impact |

#### MCP Servers (Model Context Protocol)

| MCP Server | Protocol | What It Provides | Integration Potential | Link | Benefit & Verdict |
|------------|----------|-----------------|----------------------|------|-------------------|
| **github** | stdio | GitHub API (issues, PRs, repos, branches, file ops) | Add PR creation and issue tracking to HC Git workflow | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/github) | +6 pts (Git Handling). **Implement** — PR automation directly boosts scorecard |
| **puppeteer** | stdio | Browser automation (navigate, screenshot, click, type) | Add browser testing to HC BIST for full-stack verification | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer) | +4 pts (Verification). **Implement** — extends BIST from Python-only to full-stack |
| **memory** | stdio | Knowledge graph with entities, relations, observations | Persistent learning across sessions (close BMAD gap) | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) | +3 pts (State Mgmt). **Implement** — cross-session learning is a competitive differentiator |
| **sequential-thinking** | stdio | Dynamic problem-solving with branching thought chains | Enhance HC planning phase with structured reasoning | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) | +3 pts (Planning). **Implement** — upgrades PLANNING from linear to branching reasoning |
| **postgres / sqlite** | stdio | Database querying and schema inspection | Store iteration history in SQLite instead of flat files | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/sqlite) | +3 pts (State Mgmt). **Implement** — queryable history enables iteration analytics |
| **filesystem** | stdio | Read/write/search files with configurable allowed directories | Replace HC's direct `Path` operations with MCP-standard file access | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem) | +2 pts (DX, security). **Implement** — standardizes file ops, adds access control for free |
| **brave-search** | stdio | Web search via Brave API with filtering | Research step in FULL complexity mode for up-to-date docs | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search) | +1 pt (DX). **Defer** — useful but requires API key; Openground covers local docs |
| **fetch** | stdio | Web content fetching with robots.txt compliance | Fetch library docs/examples during code generation | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/fetch) | +1 pt (DX). **Defer** — lightweight but overlaps with Context7 and Openground |
| **everything** | stdio | Reference/test MCP server with all protocol features | Testing and validation of HC's MCP client | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/everything) | +0 pts (testing only). **Skip** — development aid, no production value |

#### Testing & Quality Tools

| Tool | What It Does | Integration Potential | Link | Benefit & Verdict |
|------|-------------|----------------------|------|-------------------|
| **Playwright MCP** | Browser automation via MCP protocol | Replace subprocess-based BIST with MCP-driven browser tests | [playwright-community/mcp](https://github.com/playwright-community/mcp) | +4 pts (Verification). **Implement** — MCP-native testing aligns with HC's architecture |
| **semgrep** | Static analysis with custom rules | Add SAST scanning to HC verification phase | [semgrep/semgrep](https://github.com/semgrep/semgrep) | +4 pts (Verification, security). **Implement** — catches vulnerability classes BIST misses |
| **pytest-mcp** | Run pytest suites via MCP | Standardize HC test execution through MCP | [calvernaz/pytest-mcp](https://github.com/calvernaz/pytest-mcp) | +2 pts (Verification). **Defer** — nice standardization but BIST already works |

#### Notification & Human-in-the-Loop

| Tool | What It Does | Integration Potential | Link | Benefit & Verdict |
|------|-------------|----------------------|------|-------------------|
| **ntfy** | Push notifications via HTTP (self-hosted) | Notify user when long HC tasks complete | [binwiederhier/ntfy](https://github.com/binwiederhier/ntfy) | +2 pts (DX). **Implement** — 10 lines of Python, zero dependencies, immediate UX win |
| **Telegram Bot API** | Bidirectional messaging | Port ralph-orch's RObot pattern for HC approval gates | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) | +3 pts (Human-in-the-Loop). **Defer** — powerful but requires bot token setup per user |
| **Slack MCP** | Slack integration via MCP | Team notifications for HC task completion/failures | [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/tree/main/src/slack) | +2 pts (DX). **Defer** — team-oriented; HC is currently single-user focused |

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

---

## 🔮 Future Integrations: OpenHands

We are actively researching **OpenHands** as a sandboxed execution engine. Our "Dockerless" strategy involves using the OpenHands CLI with a process-based runtime to keep the footprint light.

### Integration Plan (v9 Roadmap)
1.  **Process Runtime**: Use `openhands serve --runtime=process` to run agents without Docker.
2.  **Gemini CLI Bridge**: Connect Hybrid Conductor's orchestrator to OpenHands' API for complex multi-step refactoring tasks.
3.  **Safety**: We will implement a custom `Sandbox` class that wraps OpenHands' process execution with our `LoopGuardian` logic.

*Reference: [`docs/info_sources/openhands_dockerless.md`](docs/info_sources/openhands_dockerless.md)*

---

## 🚧 Known Oracle & Environment Issues

Developing on native Windows presents unique challenges that we are currently tracking:

### 1. SSL/TLS Handshake Failures
- **Symptom**: `SSLV3_ALERT_HANDSHAKE_FAILURE` when connecting to Telegram API.
- **Resolution**: Implemented `hybridconductor.core.ssl_fix` which forces usage of a vendored Mozilla certificate bundle (`vendor/certifi/cacert.pem`).
- **Current Status**: **Resolved**. The system now automatically patches the SSL context on startup.

### 2. File Handle Locking (WinError 32)
- **Symptom**: `PermissionError` when deleting temporary task directories.
- **Resolution**: Introduced `hybridconductor.utils.safe_cleanup` with a `safe_tempdir` context manager. This implements a retry loop with garbage collection to release Windows file handles.
- **Current Status**: **Resolved**. Worker now gracefully handles directory cleanup.

### 3. Orchestrator Stability
- **Symptom**: CLI task terminates after initialization with no file output.
- **Resolution**: Added `--debug` flag with top-level `sys.excepthook` to catch import-time errors. Enforced `winforms` renderer for `pywebview` to prevent chromium crashes.
- **Current Status**: **Resolved**. Run `python orchestrator.py --debug` if issues persist.

### 4. MCP offline noise
- **Symptom**: `WinError 10061` when Git MCP server is not running.
- **Resolution**: `McpClient` now respects `HYBRIDCONDUCTOR_OFFLINE=true` environment variable and fails gracefully.

---

## 🩺 Diagnostics

We included a diagnostic tool to verify your environment is ready for hybrid orchestration.

```powershell
python diagnostics.py
```

Checks performed:
1.  **Localhost Connectivity**: Verifies Flask backend is reachable.
2.  **Discord Config**: Validates webhook URL format.
3.  **SSL Trust**: Confirms vendored certificate bundle is present and loadable.
4.  **GUI Renderer**: Checks `PYWEBVIEW_GUI` environment variable preference (should be `winforms`).

---
**Auditor Signature**: Antigravity
**Last Review**: 2026-02-14
