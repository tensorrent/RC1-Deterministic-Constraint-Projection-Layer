# RC1 False Positive Study

**Version: RC1-2026-03-25**

---

## Definition

A **false positive** (FP) is defined as a document from a clean technical corpus that receives a gate of WARN or FAIL under RC1-Lite evaluation.

---

## Corpus Specification

| Property | Value |
|----------|-------|
| Size | 200 documents |
| Domain | Purely technical prose |
| Sources | Python math stdlib docs, RFC 793 (TCP), RFC 2616 (HTTP/1.1), Euclidean algorithm, NumPy ndarray reference |
| Sampling | Sequential extraction of complete paragraphs |
| Token range | 40–120 tokens per document |
| Exclusions | Zero rhetorical, policy, or motivational language |
| Modal verbs | Present in some (e.g., "must" in RFC context), grounded by spec reference |

---

## Results

| Metric | Value |
|--------|-------|
| Documents evaluated | 200 |
| PASS | 200 |
| WARN | 0 |
| FAIL | 0 |
| **FP rate** | **0.00%** |
| Wilson 95% CI | true FP < 1.8% |

---

## Corpus Statistics

| Metric | Value |
|--------|-------|
| Total severity sum | 32 |
| Mean V | 0.16 |
| StdDev V | 0.54 |
| Docs with V > 0 | 32 |
| Severity per affected doc | Exactly 1 (all minor) |
| Min S in corpus | 0.929 |

### Operator Activation Counts

| Operator | Activations | Severity |
|----------|-------------|----------|
| ABS | 12 | All severity 1 |
| PRESC | 20 | All severity 1 |
| H2 | 0 | — |
| INTENT | 0 | — |
| ESC | 0 | — |
| LOOP | 0 | — |
| SELF | 0 | — |
| **Total** | **32** | **32** |

Reconciliation: 12 + 20 = 32 total severity. Matches mean V × 200 = 32.

---

## Boundary Sensitivity

| PASS threshold | FP rate |
|----------------|---------|
| ≥ 0.70 (default) | 0.00% |
| ≥ 0.75 | 0.00% |
| ≥ 0.80 | 0.00% |

Max V per document in corpus = 1, so S ≥ 0.929 for all affected documents.

---

## Batch Determinism

Re-running the full 200-document corpus produces identical:

- Mean V
- FP rate
- Operator activation counts
- Total severity sum

---

## Methodology Notes

1. No documents were excluded post-evaluation
2. No threshold tuning was performed against this corpus
3. Corpus was assembled before evaluation, not selected for results
4. All documents are publicly available technical references

---

## Interpretation

RC1 shows zero false positives on purely technical prose. The 32 minor activations (all severity 1, all PASS) indicate the operators detect lexical patterns at expected rates without triggering false gate classifications.

The Wilson confidence interval provides statistical grounding: with 200 samples and 0 failures, the true FP rate is below 1.8% with 95% confidence.

---

*FP measurement is a frozen result. Any changes to operators or thresholds require re-evaluation under a new version designation.*
