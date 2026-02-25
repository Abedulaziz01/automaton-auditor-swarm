# Week 2 Interim Architecture Report

## The Automaton Auditor – Digital Courtroom

---

# 1️⃣ Architecture Decision Rationale

_(Master Thinker Level – Trade-offs, Failure Modes, Alternatives Considered)_

This section explains not just what was chosen, but why, what alternatives were considered, and which failure modes each decision prevents.

## 1.1 Why Pydantic / TypedDict Over Plain dict for State

**Decision**
Use:

- `BaseModel` (Pydantic) for structured artifacts (`Evidence`, `JudicialOpinion`, `AuditReport`)
- `TypedDict` + `Annotated` reducers (`operator.add`, `operator.ior`) for `AgentState`

**Core Rationale**
The Digital Courtroom is parallel by design. Detectives and Judges run concurrently. Without strict typing and reducers:

- Parallel agents overwrite each other's outputs.
- Freeform LLM text contaminates structured reasoning.
- Silent key mismatches occur (`opinion` vs `opinions`).

**Failure Modes Prevented**

| Failure Mode            | Why Dict Fails                | Why Pydantic + Reducers Prevent It               |
| ----------------------- | ----------------------------- | ------------------------------------------------ |
| Parallel data overwrite | Last write wins               | `operator.add` and `operator.ior` merge safely   |
| LLM hallucinated fields | No validation                 | Schema enforcement rejects invalid output        |
| Silent structural drift | Typos not caught              | Strict field validation                          |
| Debugging opacity       | Unstructured nested dict soup | Typed artifacts are introspectable and traceable |

**Why Not Plain Dict?**
A plain dict is:

- Flexible but unsafe
- Implicitly mutable
- Not self-documenting
- Not reducer-aware

In a fan-out/fan-in architecture, dict-based state becomes brittle and unmaintainable — the exact "Dict Soup" technical debt warned about in the Statute of Engineering.

**Alternatives Considered**

| Alternative                         | Why Rejected                             |
| ----------------------------------- | ---------------------------------------- |
| Dataclasses                         | No built-in validation for LLM outputs   |
| Marshmallow                         | More boilerplate, less LangChain-native  |
| Pure BaseModel state (no TypedDict) | Harder to use LangGraph reducers cleanly |

**Conclusion**
Typed state is not stylistic preference. It is a concurrency control mechanism and a hallucination firewall.

## 1.2 AST Parsing vs Regex for Repository Analysis

**Decision**
Use Python's `ast` module for structural verification of:

- `StateGraph` instantiation
- `add_edge()` fan-out logic
- Class inheritance from `BaseModel`
- Presence of reducers

**Why Not Regex?**
Regex works on text patterns, not syntax trees.

| Scenario                                         | Regex Fails Because               | AST Handles                    |
| ------------------------------------------------ | --------------------------------- | ------------------------------ |
| Multiline class definitions                      | Pattern breaks on newlines        | AST normalizes structure       |
| Nested function calls                            | Regex can't understand tree depth | AST captures call graph        |
| Alias imports (`from x import StateGraph as SG`) | Regex misses alias                | AST resolves actual usage      |
| Conditional graph wiring                         | Regex sees string, not logic      | AST sees real call expressions |

Regex proves that a word exists. AST proves that a construct is syntactically valid and instantiated.

**Architectural Importance**
The challenge is to detect Orchestration Fraud. Only AST parsing can confirm actual fan-out architecture.

- Regex = superficial verification
- AST = structural forensic analysis

## 1.3 Sandboxing Strategy for Cloning Unknown Repositories

**Decision**
Use:

- `tempfile.TemporaryDirectory()`
- `subprocess.run()` with:
  - `capture_output=True`
  - `check=True`
  - error handling
- Never clone into working directory

**Why This Matters**
The Auditor clones arbitrary GitHub repositories. Without sandboxing:

- Malicious post-clone scripts may execute.
- Repo contents may overwrite local files.
- Path traversal vulnerabilities may occur.
- Shell injection possible via repo URL.

**Failure Modes Prevented**

| Risk                 | Unsafe Method                   | Sandboxed Method Prevents             |
| -------------------- | ------------------------------- | ------------------------------------- |
| Shell Injection      | `os.system(f"git clone {url}")` | `subprocess.run([...])` without shell |
| Code pollution       | Cloning to live directory       | Temporary isolation                   |
| Silent clone failure | No return code check            | Explicit error handling               |
| Credential leak      | Hardcoded tokens                | Environment-managed keys              |

**Alternatives Considered**

| Alternative                | Why Rejected                      |
| -------------------------- | --------------------------------- |
| Direct GitHub API download | Harder to preserve commit history |
| `os.system()`              | Security negligence               |
| Persistent clone directory | Risk of contamination across runs |

**Conclusion**
Sandboxing is not optional. It enforces the Rule of Security in synthesis.

## 1.4 RAG-Lite Approach for PDF Ingestion

**Decision**
Chunk PDF into semantic segments rather than loading full document into context.

**Why**
PDF reports may exceed context window. Naively injecting entire PDF causes:

- Context truncation
- Irrelevant noise
- Increased hallucination risk

| Failure                    | Naive Approach           | RAG-lite Prevents              |
| -------------------------- | ------------------------ | ------------------------------ |
| Buzzword misclassification | Term seen out of context | Query-specific chunk retrieval |
| Context overflow           | Full PDF injected        | Selective retrieval            |
| Shallow evaluation         | Keyword match only       | Semantic passage verification  |

**Alternative Considered**
Full-document injection → rejected due to:

- Context inefficiency
- Loss of precision
- Higher hallucination risk

## 1.5 LLM Provider Strategy for Judges

**Decision**
Use structured output binding (`.with_structured_output()`) rather than parsing free text.

**Failure Modes Prevented**

- Freeform moralizing instead of scoring
- Missing score field
- Persona convergence (identical outputs)

Structured enforcement forces judges into a constitutional contract.

## 1.6 LLM Provider Strategy for Multi-Judge System

**Decision:** Use GPT-4 for Prosecutor and Tech Lead, Claude 3.5 Sonnet for Defense, GPT-4o-mini for RepoInvestigator.

**Rationale:**

- **GPT-4 (Prosecutor/Tech Lead):** Stronger adversarial reasoning and critical scrutiny capabilities. Better at identifying security flaws and architectural debt.
- **Claude 3.5 Sonnet (Defense):** Superior nuanced language understanding for recognizing effort, intent, and creative workarounds even in imperfect code.
- **GPT-4o-mini (RepoInvestigator):** Tool-calling optimized, lower cost for high-volume forensic tasks where creative reasoning is less critical.

**Alternatives Considered:**

| Alternative                    | Why Rejected                                            |
| ------------------------------ | ------------------------------------------------------- |
| Single provider for all judges | Risk of persona collapse (same model repeats itself)    |
| Gemini Pro for all roles       | Less reliable structured output enforcement             |
| Local open-source models       | Inconsistent JSON formatting, higher hallucination rate |

**Failure Modes Prevented:**

| Failure Mode              | How Provider Strategy Prevents It                                      |
| ------------------------- | ---------------------------------------------------------------------- |
| Persona convergence       | Different base models maintain distinct reasoning patterns             |
| Single provider outage    | Fallback to secondary provider if primary fails                        |
| Cost overrun              | Tiered pricing: expensive models only for reasoning-heavy roles        |
| Structured output failure | All chosen providers have reliable `.with_structured_output()` support |

**Fallback Strategy:**

- If GPT-4 fails → fallback to Claude 3.5 Sonnet for Prosecutor/Tech Lead
- If Claude fails → fallback to GPT-4 for Defense
- If all fail → cached response with explicit error flag in report

---

# 2️⃣ Gap Analysis & Forward Plan

_(Granular, Sequenced, Risk-Aware, Actionable)_

This section evaluates what is NOT yet implemented and how it will be built.

## 2.1 Judicial Layer Implementation Plan

**Step 1 – Persona Separation**

- Create three distinct system prompts.
- Ensure >50% textual divergence.
- Embed rubric `judicial_logic` dynamically.

**Risk Identified:**
LLM may converge despite prompt differences.

**Mitigation:**

- Inject adversarial framing.
- Add explicit "disagree if possible" instruction.
- Compare lexical similarity between outputs and retry if too similar.

**Step 2 – Structured Output Enforcement**

- Bind `JudicialOpinion` Pydantic schema.
- Add retry loop if parsing fails.

**Risk:**
LLM returns partial JSON.

**Mitigation:**

- Use strict schema validation.
- Re-prompt with validation error message.

**Step 3 – Parallel Fan-Out for Judges**

- Judges run concurrently on identical Evidence input.

**Risk:**
State mutation conflict.

**Mitigation:**
Use `operator.add` reducer on `opinions`.

## 2.2 Chief Justice Synthesis Plan

**Deterministic Rule Engine (Hardcoded)**
Implement:

1. Security Override Rule
2. Fact Supremacy Rule
3. Functionality Weight Rule
4. Variance Re-evaluation Trigger

**Dissent Logic**
If score variance > 2:

- Re-evaluate cited evidence
- Summarize Prosecutor vs Defense conflict
- Explicitly justify final ruling

| Risk                      | Mitigation                       |
| ------------------------- | -------------------------------- |
| Judges cite weak evidence | Cross-reference evidence IDs     |
| Rule conflicts            | Priority hierarchy enforced      |
| Overreliance on LLM       | Deterministic if/else resolution |

Plan is sequenced and executable by another engineer.

## 2.3 Implementation Timeline & Validation

| Phase | Component         | Completion Target | Validation Method           | Success Criteria                      |
| ----- | ----------------- | ----------------- | --------------------------- | ------------------------------------- |
| 1     | Persona Prompts   | Day 1             | Lexical similarity analysis | <50% text overlap between prompts     |
| 2     | Structured Output | Day 2             | Parse rate on 10 trial runs | 100% valid JudicialOpinion JSON       |
| 3     | Parallel Judges   | Day 3             | State integrity check       | No data overwrite in opinions list    |
| 4     | Synthesis Rules   | Day 4             | Conflict resolution tests   | Rules fire correctly for 5 test cases |
| 5     | End-to-End Flow   | Day 5             | Full graph execution        | AuditReport generated without errors  |

**Dependencies:**

- Phase 2 depends on Phase 1 (prompts define schema usage)
- Phase 4 depends on Phase 3 (synthesis needs judge outputs)
- All phases depend on sandboxed tooling (already implemented)

## 2.4 Integration Test Cases

| Test Scenario         | Input                                                                  | Expected Behavior                                           | Pass/Fail Criteria                         |
| --------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------ |
| **High Variance**     | Evidence: "Code has bugs but shows deep understanding"                 | Variance >2 → re-evaluate, dissent required in final report | Dissent summary present for that criterion |
| **Security Override** | Evidence: `os.system()` call detected + Defense argues effort          | Final score capped at 3 regardless of Defense               | Score ≤ 3 on that criterion                |
| **Fact Supremacy**    | Report claims "parallel judges implemented" but code shows linear flow | Defense overruled, fact-based score applied                 | Final score matches Prosecutor/Tech Lead   |
| **Persona Collapse**  | All judges return identical scores and reasoning                       | Retry with stronger adversarial prompts                     | After retry, scores diverge                |
| **Missing Evidence**  | PDF mentions file that doesn't exist in repo                           | Hallucination flag in report                                | "Hallucinated Paths" section populated     |

**Risk Register:**

| Risk                                       | Likelihood | Impact | Mitigation                                            |
| ------------------------------------------ | ---------- | ------ | ----------------------------------------------------- |
| LLMs ignore persona constraints            | Medium     | High   | Lexical monitoring + retry with stronger framing      |
| API rate limits                            | Medium     | Medium | Exponential backoff, queueing                         |
| PDF exceeds context                        | Low        | Medium | RAG-lite already implemented                          |
| Rule conflicts (Security vs Functionality) | Low        | Medium | Priority hierarchy: Security > Functionality > Effort |

---

# 3️⃣ StateGraph Architecture Diagram Description

The architecture follows strict hierarchical orchestration.

## Flow Overview

## Diagram Requirements Satisfied

| Requirement             | Status | Evidence                                                                     |
| ----------------------- | ------ | ---------------------------------------------------------------------------- |
| ✔ Parallel Detectives   | ✅     | Fan-out from ContextBuilder to all three detectives                          |
| ✔ Synchronization Node  | ✅     | EvidenceAggregator clearly collects structured Evidence objects              |
| ✔ Parallel Judges       | ✅     | All three judges run concurrently on same evidence                           |
| ✔ State Types Indicated | ✅     | Detectives → Evidence, Judges → JudicialOpinion, Chief Justice → AuditReport |
| ✔ Conditional Edges     | ✅     | Error paths for failures, retry logic for parse failures                     |
| ✔ Hierarchical Flow     | ✅     | Detectives → Aggregation → Judges → Deterministic Synthesis                  |

## Conditional Edge Logic

| Condition                       | Action                                              |
| ------------------------------- | --------------------------------------------------- |
| RepoInvestigator fails →        | Error state branch with partial evidence flag       |
| PDF missing →                   | Skip DocAnalyst path, proceed with partial evidence |
| VisionInspector fails →         | Continue without diagram evidence (non-critical)    |
| Judge parse fails →             | Retry edge (max 3 attempts)                         |
| All judges fail for criterion → | Fallback to Tech Lead solo opinion                  |

---

_End of Report_
