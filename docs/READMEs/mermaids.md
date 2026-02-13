## Chart Descriptions

### 1. High-Level Principles Chart
This chart visualizes the **5 core architectural pillars** of Hybrid Orchestrator and their direct outcomes:
- Shows how each principle maps to specific technical decisions
- Demonstrates the cause-and-effect relationship between design choices and system capabilities
- Highlights the Windows-native focus throughout all layers

### 2. Comprehensive Swimlane Diagram
This detailed sequence diagram shows:
- **All major components** and their interactions
- **Three distinct phases**: Initialization, Planning, Building
- **Async mid-flight steering** via inbox polling
- **Error handling paths** and loop detection
- **Context retrieval flow** with Openground fallback
- **MCP Git operations** for safe version control
- **Database logging** for audit trail

### 3. Code Block Level Steps
This flowchart provides:
- **Granular execution path** from user input to completion
- **Decision points** with specific conditions
- **Function-level operations** (e.g., `generate_codebase_map()`, `_run_bist()`)
- **Temperature escalation logic** (0.7 → 1.0 → 1.3)
- **Loop detection mechanism** with hash normalization
- **Async inbox polling** for mid-flight commands
- **Cleanup and logging** finalization steps

Each chart serves a different audience:
- **Principles chart** for architects and stakeholders
- **Swimlane diagram** for developers and system designers  
- **Code-level flowchart** for implementers and debuggers