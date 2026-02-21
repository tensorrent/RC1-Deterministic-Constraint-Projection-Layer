# RC1 Public Review — 2026 Q2

**Specification:** RC1-2026-03-25
**Review Window:** 60 days from publication date
**Status:** Open for comment

---

## Purpose

This document opens a public review period for the RC1 specification (RFC-RC1-0001). The goal is to identify defects, edge cases, and operator blind spots through community scrutiny before reaffirming the freeze.

---

## Scope of Review

Comments MUST reference a specific section of RFC-RC1-0001.

Accepted categories:

| Category | Requires |
|----------|----------|
| False positive report | Input text + expected gate + actual gate |
| False negative report | Input text + expected violations + actual result |
| Determinism violation | Input text + two differing outputs + environment details |
| Spec ambiguity | RFC section reference + proposed clarification |
| Operator boundary issue | Input text near detection threshold + analysis |

---

## Out of Scope

The following are NOT accepted during this review:

- Philosophical objections to structural evaluation
- Requests to add new operators (requires RC2 proposal process)
- Requests to change thresholds (requires RC2)
- Comparisons to semantic evaluation frameworks
- Marketing or positioning feedback

---

## How to Submit

1. Open a GitHub Issue on the repository
2. Title format: `[REVIEW] Section X.Y — Brief description`
3. Include all required evidence per category above
4. Include: RC1 version, Python version, OS

---

## Response Policy

- All submissions will receive acknowledgment within 7 days
- Confirmed defects will be documented in `governance/known_issues.md`
- No spec changes will be made during the review window
- At the close of the 60-day window, a summary report will be published

---

## Review Outcomes

| Finding | Action |
|---------|--------|
| No critical defects | Reaffirm freeze |
| Minor edge cases | Document in known issues |
| Systemic operator failure | Begin formal RC2 proposal |
| Determinism violation | Issue patch + regression test |

---

## Timeline

| Date | Milestone |
|------|-----------|
| Publication date | Review window opens |
| +30 days | Mid-review summary |
| +60 days | Review window closes |
| +75 days | Final summary report published |

---

*Standards mature through friction. Critique is welcome.*
