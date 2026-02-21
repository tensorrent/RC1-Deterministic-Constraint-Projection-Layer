# RC1 Compliance Checklist

**Version:** RC1-2026-03-25

---

## Requirements

An implementation is RC1-compliant if and only if ALL of the following hold:

### Operators

- [ ] All 7 operators implemented: H2, ABS, INTENT, ESC, LOOP, PRESC, SELF
- [ ] Each operator returns severity in {0, 1, 2}
- [ ] No additional operators present under RC1 version

### Tokenization

- [ ] Lowercase conversion applied
- [ ] Punctuation stripped via `token.strip(string.punctuation)`
- [ ] Split on whitespace
- [ ] Token order preserved

### Windows

- [ ] H2: 20-token window
- [ ] ABS: 10-token window
- [ ] INTENT: 15-token window
- [ ] PRESC: 10-token window

### Similarity

- [ ] LOOP: Jaccard similarity over token sets (not multisets)
- [ ] Threshold: λ = 0.7
- [ ] No stopword removal

### Scoring

- [ ] V_max = 14
- [ ] S = 1 - V/14
- [ ] PASS: S ≥ 0.70
- [ ] WARN: 0.50 ≤ S < 0.70
- [ ] FAIL: S < 0.50

### Invariants

- [ ] V == sum of all violation severities
- [ ] Score matches formula exactly
- [ ] Gate matches threshold table exactly
- [ ] Identical input → identical output (idempotence)

### Prohibitions

- [ ] No external dependencies
- [ ] No ML or probabilistic inference
- [ ] No external API calls
- [ ] No training signal output

---

## Certification Submission

To claim RC1 compliance, submit:

1. **Engine hash** (SHA-256 of core evaluation module)
2. **Test vector results** (output for all entries in `test-vectors.jsonl`)
3. **Language and runtime** (e.g., Python 3.11, Rust 1.75, Go 1.22)
4. **Diff from reference** (any intentional deviations — should be none)

All test vector outputs must match the reference implementation exactly.

---

*Compliance is binary. Partial compliance is non-compliance.*
