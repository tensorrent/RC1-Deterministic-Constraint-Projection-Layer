# RC1 — Deterministic Constraint Projection Layer

**Version: RC1-2026-03-25 (Frozen)**

RC1 is a deterministic, rule-based framework for evaluating structural discipline in language model outputs and technical prose.

It does not measure truth, intelligence, or correctness.

It measures **structural constraint compliance** under a fixed operator set.

---

## What RC1 Does

RC1 evaluates text and produces:

- **Structural compliance score** (0–1): `S = 1 - V/14`
- **Total violation severity** (V)
- **Gate classification**: PASS (≥0.70) · WARN (≥0.50) · FAIL (<0.50)
- **Structured taxonomy** breakdown by operator
- **Deterministic, idempotent** output

---

## What RC1 Does NOT Do

RC1 does not:

- ❌ Detect hallucinations
- ❌ Evaluate factual correctness
- ❌ Measure intelligence
- ❌ Guarantee safety
- ❌ Replace peer review

RC1 is a structural projection instrument only.

---

## Installation

**Python 3.8+** · No external dependencies.

```bash
git clone https://github.com/tensorrent/RC1-Deterministic-Constraint-Projection-Layer.git
cd RC1-Deterministic-Constraint-Projection-Layer
```

---

## Quick Start

```python
from rc1_lite.engine import evaluate_output

result = evaluate_output("Your text here.")
print(result)
```

Output:

```json
{
  "score": 0.857,
  "V": 2,
  "V_max": 14,
  "gate": "PASS",
  "taxonomy": {"H2":0,"ABS":1,"INTENT":0,"ESC":0,"LOOP":0,"PRESC":1,"SELF":0},
  "violations": [],
  "version": "RC1-2026-03-25"
}
```

---

## Running Tests

```bash
# RC1-Lite core (56 tests)
python3 tests/test_rc1_lite.py

# Teaching Loop (22 tests)
python3 tests/test_loop.py
```

All tests must pass. If any fail, file a bug.

---

## Constraint Operators

RC1-2026-03-25 includes seven frozen operators:

| Code | Operator | Detects |
|------|----------|---------|
| H2 | Undissolved Metaphor | Figurative language without literal dissolution |
| ABS | Absolute Claim | Universal quantifiers without scoping qualifiers |
| INTENT | Intent Without Mechanism | Intent verbs without concrete execution artifacts |
| ESC | Abstraction Escalation | Domain shift (technical → abstract) without bridge |
| LOOP | Rephrasing Loop | Adjacent segments with Jaccard similarity > 0.7 |
| PRESC | Ungrounded Prescriptive | Prescriptive markers without justification |
| SELF | Self-Referential Capability | Capability claims without qualification |

Full formal definitions: [docs/rc1_spec.md](docs/rc1_spec.md)

---

## False Positive Study

| Property | Value |
|----------|-------|
| Corpus | 200 purely technical documents |
| FP rate | 0.00% (0/200 WARN or FAIL) |
| Wilson 95% CI | < 1.8% |
| Mean V | 0.16 |

Full methodology: [docs/fp_study.md](docs/fp_study.md)

---

## Determinism Guarantees

- No ML components
- No model calls
- No external APIs
- Pure Python stdlib (`re`, `string`, `typing`)
- Version-locked thresholds
- Idempotent evaluation

---

## Governance

- **Frozen spec**: RC1-2026-03-25
- **New operators** require new version (RC2+)
- **No silent threshold changes**
- **All changes logged**
- **Observer ≠ Optimizer**: RC1 never provides training signals

Full governance policy: [docs/GOVERNANCE.md](docs/GOVERNANCE.md)

---

## Teaching Loop Extension

Optional iterative refinement module. Halting conditions:

1. PASS reached
2. No score improvement (Δ = 0)
3. Score decrease
4. MAX_ITERATIONS reached
5. Inflation detected (output exceeds input length)

Full delta trace recorded. Module remains deterministic.

---

## Project Structure

```
rc1/
├── README.md
├── LICENSE
├── VERSION
├── rc1_lite/
│   ├── engine.py          # Core evaluation
│   ├── scoring.py         # S = 1 - V/14, gates, taxonomy
│   ├── version.py         # RC1-2026-03-25
│   └── constraints/       # 7 frozen operators
├── teaching_loop/
│   └── loop.py            # Iterative refinement
├── tests/
│   ├── test_rc1_lite.py   # 56 invariant tests
│   └── test_loop.py       # 22 teaching loop tests
├── samples/
│   └── batch.jsonl        # 8 evaluation samples
├── docs/
│   ├── rc1_spec.md        # Full specification
│   ├── fp_study.md        # False positive methodology
│   └── GOVERNANCE.md      # Versioning & change policy
└── ci/
    └── rc1_tests.yml      # GitHub Actions
```

---

## License

MIT — see [LICENSE](LICENSE)

---

*Constraint compliance is not equivalent to truth.*
