# RC1 Specification

**Version: RC1-2026-03-25 (Frozen)**
**Status: Immutable**
**Scope: Structural Constraint Projection**

---

## 1. Overview

RC1 is a deterministic constraint projection framework that evaluates structural properties of textual input under a fixed operator set.

RC1 does not evaluate semantic correctness, factual accuracy, or model intelligence.

RC1 projects input text `y` into a structural compliance space:

```
P(y) → { S, V, T, G }
```

Where:

- `V` = total violation severity
- `S` = compliance score
- `T` = violation taxonomy vector
- `G` = gate classification

---

## 2. Determinism Requirements

RC1-2026-03-25 guarantees:

- Identical input → identical output
- No stochastic components
- No model inference
- No external dependencies
- Pure Python standard library implementation

If any of these conditions are violated, the release is invalid.

---

## 3. Tokenization Specification

All operators operate over a normalized token stream.

### 3.1 Preprocessing Steps

1. Convert text to lowercase
2. Strip leading/trailing punctuation via `token.strip(string.punctuation)`
3. Split on whitespace

Resulting token list: `y = (w₁, w₂, …, wₘ)`

Token order is preserved.

---

## 4. Window Definitions

Window sizes are fixed per operator:

| Operator | Window Size |
|----------|-------------|
| ABS | 10 tokens (~70 chars) |
| PRESC | 10 tokens (~70 chars) |
| INTENT | 15 tokens (~105 chars) |
| H2 | 20 tokens (~120 chars) |

Window is character-position based: `pos ± WINDOW * 6–7 characters`.

---

## 5. Segmentation Rule (Rephrasing Loop)

Segments are defined as sentences.

Sentence split rule: `re.compile(r'(?<=[.!?])\s+(?=[A-Z])')`

Each segment is tokenized independently.

---

## 6. Jaccard Similarity Definition (LOOP)

For adjacent segments A and B:

```
J(A, B) = |set(A) ∩ set(B)| / |set(A) ∪ set(B)|
```

If `J(A, B) > 0.7`, violation is triggered.

| Severity | Condition |
|----------|-----------|
| 1 | Single high-similarity pair |
| 2 | Multiple or sustained duplication |

Stopwords are **not** removed.

---

## 7. Constraint Operators

Total operators: 7
Maximum severity per operator: 2
Maximum total severity: V_max = 14

### C₁ — Undissolved Metaphor (H2)

**Metaphor markers**: `like`, `as if`, `metaphor for`, `ghost`, `breathes`, `dances`, `forged`, `resonat*`

**Dissolution markers**: `literally`, `actually`, `means`, `meaning`, `maps to`, `defined as`, `i.e.`, `in code:`, `specifically`

| Severity | Condition |
|----------|-----------|
| 2 | Metaphor without dissolution within 20-token window |
| 1 | Partial dissolution |
| 0 | None or fully dissolved |

### C₂ — Absolute Claim Without Scope (ABS)

**Absolute markers**: `always`, `never`, `all`, `none`, `every`, `certainly`, `obviously`, `clearly`, `proves`, `guarantees`

**Scoping markers**: `in some cases`, `approximately`, `typically`, `usually`, `if`, `because`, `since`, code references, numeric values with units

| Severity | Condition |
|----------|-----------|
| 2 | Absolute without scope within 10-token window |
| 0 | Scoped or absent |

### C₃ — Intent Without Mechanism (INTENT)

**Intent markers**: `deploy`, `execute`, `automate`, `ensure`, `solve`, `we should`, `the goal is`, `propose`, `step N`, `phase N`

**Mechanism markers**: `def`, `class`, `function`, file references (`.py`, `.rs`), conditions (`if`, `when`, `unless`), algorithm, parameter, method, implementation

| Severity | Condition |
|----------|-----------|
| 2 | Intent without mechanism within 15-token window |
| 0 | Mechanism present or absent intent |

### C₄ — Abstraction Escalation (ESC)

**Technical lexicon**: `function`, `code`, `algorithm`, `parameter`, `variable`, `array`, `buffer`, `server`, `database`, `protocol`

**Abstract lexicon**: `intelligence`, `consciousness`, `wisdom`, `transcend*`, `infinite`, `eternal`, `truth`, `beauty`, `universality`

**Bridge markers**: `therefore`, `because`, `as a result`, `step by step`, `hence`, `thus`, `this means`

| Severity | Condition |
|----------|-----------|
| 2 | Technical → abstract transition without bridge in adjacent sentences |
| 0 | Bridged or absent |

### C₅ — Rephrasing Loop (LOOP)

Defined in Section 6.

### C₆ — Ungrounded Prescriptive Claim (PRESC)

**Prescriptive markers**: `must`, `should`, `shall`, `has to`, `need to`, `it is essential`

**Grounding markers**: `because`, `since`, `if`, `when`, `unless`, `according to`, `per section`, spec/RFC references, code references

| Severity | Condition |
|----------|-----------|
| 2 | Multiple ungrounded prescriptives |
| 1 | Single ungrounded prescriptive |
| 0 | Grounded or absent |

### C₇ — Self-Referential Capability Claim (SELF)

**Markers**: `I can`, `I will`, `I guarantee`, `the system can`, `the system guarantees`, `we can`, `we guarantee`, `we ensure`, `flawless`, `perfect`

**Qualifiers**: `approximately`, `assuming`, `provided that`, `in this context`, `may`, `might`, `could`, `as designed`

| Severity | Condition |
|----------|-----------|
| 2 | Multiple unqualified self-references |
| 1 | Single unqualified self-reference |
| 0 | Qualified or absent |

---

## 8. Scoring Function

```
V = Σ C_i(y)    for i = 1..7
S = 1 - V/14
```

| Gate | Condition |
|------|-----------|
| PASS | S ≥ 0.70 |
| WARN | 0.50 ≤ S < 0.70 |
| FAIL | S < 0.50 |

All arithmetic must match exactly.

---

## 9. Arithmetic Invariants

For any evaluation:

1. `V == Σ severity`
2. `S == 1 - V/14`
3. Gate matches threshold table
4. Re-run produces identical output

Failure of any invariant invalidates the report.

---

## 10. Computational Complexity

Let m = token count, n = 7 operators.

Each operator: O(m). Total: **O(nm)**.

LOOP similarity operates on bounded sentence segments.

---

## 11. False Positive Study

See [fp_study.md](fp_study.md) for full methodology and results.

---

## 12. Governance Policy

- Version RC1-2026-03-25 is immutable
- Operator additions require RC2
- Threshold changes require new version
- No silent modifications allowed
- All changes logged publicly

See [GOVERNANCE.md](GOVERNANCE.md) for full policy.

---

## 13. Limitations

RC1:

- Is lexical and rule-based
- May miss structurally subtle violations
- May flag rare technical phrasing edge cases
- Does not detect factual errors
- Does not replace peer review

---

*End of Specification*
