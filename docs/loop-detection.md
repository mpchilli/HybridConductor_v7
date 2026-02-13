# Loop Detection & Cycle Management Review
**Framework Version**: Hybrid Conductor v7.2.8
**Module**: `loop_guardian.py`

## 0. Context: Why This Was Asked
This review was initiated to verify the robustness of the **autonomous cycle management** in Hybrid Conductor v7. The goal is to ensure that the system can reliably detect logical ruts (infinite loops) in LLM-generated code without being fooled by volatile data. Specifically, we audited the SHA-256 logic hashing as a high-value, low-cost alternative to expensive LLM-based self-correction.

---

## 1. Governance Overview
The system implements a **Multi-Layer Defense** strategy designed to prevent infinite execution cycles. It prioritizes deterministic logic over fuzzy approximations to ensure stability on Windows and Linux platforms.

---

## 2. Technical Implementation: SHA-256 Normalized Hashing
The system uses the NIST FIPS 180-4 compliant SHA-256 algorithm to hash normalized output.

### Recent Improvements & Rationale (v7.2.9)

| Improvement | Rationale |
| :--- | :--- |
| **Comment Stripping** | Strips all Python/shell comments (`#`). This ensures that an LLM cannot bypass loop detection by simply adding or changing a comment while keeping the same buggy logic. |
| **Logic-Only Normalization** | Strips timestamps, hex addresses, paths, and process IDs. Focuses the "signature" on the code's functional structure. |
| **Whitespace Normalization** | Strips leading/trailing spaces and removes empty lines. Prevents minor formatting changes from generating a unique hash for identical logic. |
| **Floating Point Stability** | Added `round(..., 1)` to the temperature escalation logic. Prevents non-deterministic behavior caused by floating-point arithmetic (e.g., `0.7 + 0.6` resulting in `1.2999999...`), which formerly caused test failures and inconsistent retry behavior. |

---

## 3. Analysis Table: Value vs. Alternatives

| Method | Value / Effectiveness | Complexity | Speed / Cost | Robustness |
| :--- | :--- | :--- | :--- | :--- |
| **SHA-256 (Current)** | **High**. Catches exact logic loops with 100% precision. | **Medium**. Requires Regex maintenance for normalization. | **Instant / $0**. Local compute only. | **High**. Deterministic and predictable. |
| **Simple Counter** | **Low**. Only stops runaway processes; doesn't detect "stuck" states early. | **Very Low**. Simple integer increment. | **Instant / $0** | **Low**. Wastes tokens on repetitive failures. |
| **Semantic Embeddings** | **Very High**. Can detect "meaningfully similar" loops even if wording changes. | **High**. Requires Vector DB (Chroma/FAISS) and embedding model. | **Fast / Low-Med**. Small inference cost. | **Medium**. Can suffer from false positives. |
| **LLM Evaluator** | **Highest**. Can understand context and identify subtle logical ruts. | **Low (Dev) / High (Ops)**. Simple prompt but adds dependency. | **Slow / High**. Adds latency and token cost per iteration. | **Medium**. Dependent on model reliability. |

---

## 4. Current State Gaps (Internal Audit)
*   **Worker Synchronization**: While `loop_guardian.py` provides the hashing logic, the `worker.py` implementation currently utilizes a simplified "keyword search" (e.g., looking for `while True`) and does not fully integrate the SHA-256 history check available in the Guardian class.
*   **Temperature Escalation**: Integration is successful; the orchestrator correctly escalates temperature (0.7 -> 1.0 -> 1.3) upon detecting a failure or logic loop to "jiggle" the model out of the rut.
