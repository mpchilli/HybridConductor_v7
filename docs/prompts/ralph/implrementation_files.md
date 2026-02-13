# Hybrid Orchestrator v7.2.9 Implementation Guide
## Using Gemini Antigravity IDE

---

## 🎯 **YOUR GOAL**
Build a **complete, production-ready** Hybrid Orchestrator v7.2 system that actually works—not just a skeleton.

---

## 📋 **WHAT YOU NEED TO DO**

### **Step 1: Prepare Your Workspace**
1. Create a new folder: `hybrid_orchestrator_v7.2`
2. Save my critical analysis feedback as `implementation_guide.md` in that folder
3. Open Gemini Antigravity IDE
4. Load the `implementation_guide.md` file into the chat

### **Step 2: Set Up the Implementation Workflow**
**IMPORTANT**: You will implement **ONE FILE AT A TIME**, not the whole system at once.

**Why?** Gemini's "planning mode" creates skeletons. We want **complete, tested files**.

---

## 🤖 **WHAT THE AI WILL DO**

### **For Each File:**
1. **Read** the implementation guide section for that file
2. **Write** complete, production-ready code with:
   - All functions fully implemented (no placeholders)
   - Type hints and docstrings
   - Error handling
   - Test suite at the bottom
3. **Test** the code before moving to the next file
4. **Verify** all requirements are met

---

## 📝 **YOUR INPUTS (What You Type)**

### **PHASE 1: Core Infrastructure (Do These First)**

#### **File 1: `loop_guardian.py`**
**Your Input:**
```
@file loop_guardian.py

IMPLEMENT COMPLETE FILE:

Requirements:
1. All functions from feedback must be fully implemented
2. Include test suite with 5+ test cases at bottom
3. Must pass all tests before proceeding

Test Requirements:
✅ normalize_output() strips timestamps, hex addresses, paths
✅ compute_normalized_hash() produces identical output for identical logic  
✅ LoopGuardian.should_terminate() enforces iteration/time limits
✅ get_escalated_temperature() follows [0.7, 1.0, 1.3] progression
✅ Test suite runs and passes 100%

DO NOT proceed until tests pass. Run: python loop_guardian.py
```

**Wait for AI to output complete file → Save it → Run tests → Confirm all pass → Then continue**

---

#### **File 2: `cartographer.py`**
**Your Input:**
```
@file cartographer.py

IMPLEMENT COMPLETE FILE:

Requirements:
1. codesum integration with proper error handling
2. Fallback to custom walker if codesum unavailable
3. Test suite at bottom

Test Requirements:
✅ Generates codebase_map.md in state/ directory
✅ Falls back to basic map if codesum fails
✅ Handles Windows paths correctly
✅ Test suite passes

DO NOT proceed until tests pass.
```

---

#### **File 3: `context_fetcher.py`**
**Your Input:**
```
@file context_fetcher.py

IMPLEMENT COMPLETE FILE:

Requirements:
1. Openground semantic search as PRIMARY method
2. Regex fallback as SECONDARY method
3. Proper error handling and timeouts
4. Test suite at bottom

CRITICAL: Must include Openground indexing step in setup
Test Requirements:
✅ fetch_context() returns results from Openground
✅ Falls back to regex if Openground fails
✅ Handles Windows file paths
✅ Test suite passes

DO NOT proceed until tests pass.
```

---

### **PHASE 2: Main Components**

#### **File 4: `worker.py`**
**Your Input:**
```
@file worker.py

IMPLEMENT COMPLETE FILE:

Requirements:
1. MCP Git client fully implemented (not stubbed)
2. BIST (Built-In Self-Test) actually runs tests
3. Loop detection uses actual hash tracking
4. Test suite at bottom

CRITICAL FIXES from feedback:
✅ Replace MCP stubs with actual HTTP client OR safe subprocess Git
✅ _run_bist() must actually execute tests, not return True
✅ _detect_loop() must compute actual normalized hash
✅ Test suite passes

DO NOT proceed until tests pass.
```

---

#### **File 5: `orchestrator.py`**
**Your Input:**
```
@file orchestrator.py

IMPLEMENT COMPLETE FILE:

Requirements:
1. State persistence to disk (not memory-only)
2. LLM integration (not placeholder)
3. Proper error handling throughout
4. Test suite at bottom

CRITICAL FIXES from feedback:
✅ Save state to state/orchestrator_state.json after each transition
✅ Implement actual LLM API call (OpenAI/Anthropic/local)
✅ Fix hardcoded tmp_dir path (use tempfile.gettempdir())
✅ Test suite passes

DO NOT proceed until tests pass.
```

---

### **PHASE 3: Supporting Files**

#### **File 6: `setup.py`**
**Your Input:**
```
@file setup.py

IMPLEMENT COMPLETE FILE:

Requirements:
1. Install Openground with indexing step
2. Create all necessary directories
3. Initialize Git repository
4. Set up SQLite databases
5. Test suite at bottom

CRITICAL ADDITION:
✅ Add: subprocess.run(["openground", "index", "."], ...) after installation
✅ This ensures Openground is ready to search on first run

Test Requirements:
✅ Creates all directories
✅ Initializes Git repo
✅ Installs Openground and indexes codebase
✅ Test suite passes

DO NOT proceed until tests pass.
```

---

#### **File 7: `dashboard/app.py`**
**Your Input:**
```
@file dashboard/app.py

IMPLEMENT COMPLETE FILE:

Requirements:
1. SSE streaming reads actual activity.db (not static loop)
2. Proper error handling for client disconnects
3. Security: binds ONLY to 127.0.0.1
4. Test suite at bottom

CRITICAL FIXES from feedback:
✅ SSE endpoint polls activity.db in real-time
✅ No blocking time.sleep() in event loop
✅ Handles client disconnects gracefully
✅ Test suite passes

DO NOT proceed until tests pass.
```

---

## ✅ **VERIFICATION CHECKLIST (After All Files)**

After implementing all 7 files, run this final check:

**Your Input:**
```
/verify complete_system

CHECKLIST:
- [ ] loop_guardian.py - All tests pass
- [ ] cartographer.py - Generates codebase_map.md
- [ ] context_fetcher.py - Openground search works
- [ ] worker.py - MCP Git operations work, BIST runs
- [ ] orchestrator.py - State persists, LLM integrates
- [ ] setup.py - Installs and indexes Openground
- [ ] dashboard/app.py - SSE streams real logs

Run end-to-end test:
python orchestrator.py --prompt "create test file" --complexity fast

Expected: System completes task successfully, creates file, logs show in dashboard
```

---

## 🚨 **CRITICAL RULES**

1. **ONE FILE AT A TIME** - Don't implement multiple files in one go
2. **TEST BEFORE PROCEEDING** - Each file must pass its test suite before moving on
3. **NO PLACEHOLDERS** - Every function must be fully implemented
4. **SAVE AND TEST** - After AI outputs file, save it, run tests, confirm pass
5. **IF TESTS FAIL** - Don't proceed. Fix the file first.

---

## 📊 **IMPLEMENTATION ORDER (Follow Exactly)**

1. ✅ `loop_guardian.py` (Foundation - loop detection)
2. ✅ `cartographer.py` (Codebase mapping)
3. ✅ `context_fetcher.py` (Context retrieval)
4. ✅ `worker.py` (Task execution)
5. ✅ `orchestrator.py` (Main control)
6. ✅ `setup.py` (Installation)
7. ✅ `dashboard/app.py` (UI)

---

## 💡 **PRO TIPS**

- **If AI creates placeholders**: Respond with `/rollback` and re-request with emphasis on "NO PLACEHOLDERS"
- **If tests fail**: Ask AI to `/fix` the specific failing test
- **If file is incomplete**: Ask AI to `/complete` the missing sections
- **Always verify**: Manually check that the output file has no `TODO`, `pass`, or placeholder comments

---

**Ready to start? Begin with Phase 1, File 1 (`loop_guardian.py`).**