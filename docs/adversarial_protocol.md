# RC1 Adversarial Testing Protocol

**Version: 1.0**

---

## Objective

Stress-test RC1 under controlled adversarial input generation to validate operator correctness, boundary behavior, and determinism guarantees.

---

## Phase 1: Operator Isolation

For each of the 7 operators:

1. Construct **minimal trigger** sentence (activates operator at severity 2)
2. Construct **near-boundary** sentence (just below/above activation threshold)
3. Construct **dissolved/grounded** variant (same content, properly scoped)
4. Confirm severity delta is correct
5. Confirm no unintended cross-operator activation

**Example (ABS):**

| Input | Expected |
|-------|----------|
| `"This system guarantees safety."` | ABS severity 2 |
| `"This system guarantees safety under defined conditions."` | ABS severity 0 |

---

## Phase 2: Compound Violations

Construct texts triggering:

- 2 operators simultaneously
- 3 operators simultaneously
- 5+ operators simultaneously

Verify: `V == Σ severity` holds exactly.

Check score arithmetic matches formula in all compound cases.

---

## Phase 3: Inflation Attacks

Test:

- Long text padding (>1000 tokens of clean prose + 1 violation)
- Redundant phrase insertion
- Segment duplication (exact and near-exact)
- Whitespace manipulation

Ensure LOOP detection activates correctly and other operators remain unaffected.

---

## Phase 4: Cross-Model Sampling

Feed RC1 outputs from:

- GPT-4
- Claude 3.5
- Gemini 1.5
- Grok
- DeepSeek

Measure taxonomy distribution differences per model.

Not to judge models — to study structural constraint patterns.

---

## Phase 5: Edge Case Fuzzing

Automate:

- Random insertion of marker tokens at boundary positions
- Mixed-case token variations
- Punctuation edge cases (em-dash, semicolon, ellipsis)
- Unicode edge cases
- Empty input, single-word input, single-sentence input

Ensure deterministic behavior in all cases.

---

## Phase 6: Version Stability Audit

After freeze:

1. Hash `engine.py` and all operator modules
2. Record hashes in release tag
3. Re-run full test suite
4. Compare results byte-for-byte with prior run

Any deviation invalidates freeze.

---

## Reporting

All adversarial test results should include:

- Input text (verbatim)
- Expected gate and score
- Actual gate and score
- Violation list with severities
- RC1 version
- Python version and OS

---

## Long-Term Scaling

Once stable:

- Expand adversarial corpus to 500+ samples
- Publish adversarial dataset publicly
- Invite external break attempts
- Document all discovered edge cases

Trust increases when you invite attack.

---

*Adversarial testing is not opposition. It is calibration.*
