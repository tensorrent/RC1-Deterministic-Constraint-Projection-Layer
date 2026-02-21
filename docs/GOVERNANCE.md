# RC1 Governance

**Version: RC1-2026-03-25**

---

## Core Principle

RC1 versions are **immutable once published**. No retroactive changes to thresholds, operator definitions, or scoring formulas.

---

## Versioning Policy

| Rule | Detail |
|------|--------|
| Format | `RC{N}-YYYY-MM-DD` |
| Immutability | Once frozen, a version never changes |
| New operators | Require new version (RC2, RC3, etc.) |
| Threshold changes | Require new version |
| Bug fixes | Allowed if FP/FN rates are preserved and documented |

---

## Operator Proposal Process

To propose a new constraint operator for RC2+:

1. **Define** the operator formally: input → {0, 1, 2} with explicit detection rules
2. **Implement** as pure Python (stdlib only), deterministic, no external calls
3. **Test** on the 200-prompt clean corpus: FP impact must be documented
4. **Document** tokenization, window size, and pattern lists
5. **Submit** with test cases showing true positives, true negatives, and edge cases

No operator is accepted without formal definition, FP measurement, idempotence proof, and version designation.

---

## Prohibited Changes

The following are **never** permitted within a frozen version:

- Silent threshold drift
- Adding operators without version bump
- Introducing probabilistic or ML-based detection
- Adding external dependencies
- Providing optimization feedback to evaluated models
- Retroactive FP rate recalculation

---

## Deprecation Policy

- Deprecated versions remain available and runnable indefinitely
- Deprecation announced with minimum 90-day notice
- Comparison reports must specify version used
- Cross-version comparisons must note operator differences

---

## Change Log

### RC1-2026-03-25 (frozen)

- 7 constraint operators: H2, ABS, INTENT, ESC, LOOP, PRESC, SELF
- Scoring: S = 1 - V/14, gates at 0.70/0.50
- FP rate: 0.00% on 200-prompt corpus (Wilson 95% CI < 1.8%)
- Pure Python, stdlib only, deterministic
- Observer ≠ Optimizer enforced

---

## Adversarial Testing

If you can:

- Construct clean technical prose that triggers WARN or FAIL → **false positive**. Report it.
- Construct inflated text that receives PASS → **false negative**. Report it.
- Demonstrate non-determinism → **bug**. Report it.

Include: input text, expected gate, actual gate, RC1 version, Python version, OS.

---

*Governance exists to prevent the system from becoming what it measures.*
