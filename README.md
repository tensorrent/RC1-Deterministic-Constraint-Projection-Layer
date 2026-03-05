# RC Stack — Deterministic Constraint Gate Architecture

**Bradley Wallace** — Independent Researcher
Licensed under the [Sovereign Integrity Protocol (SIP) v1.1](./SIP_LICENSE.md)

---

## Overview

The **RC Stack** (Resonance Constraint Stack) is a layered system of formal mathematical gates that enforce deterministic stability, correctness, and epistemic honesty. Each RC layer acts as a constraint boundary — computations that fail a gate are rejected before they propagate errors downstream.

Every RC gate operates in **exact integer arithmetic** with formally provable invariants.

---

## Architecture

| Layer | Name | Function |
|-------|------|----------|
| **RC1** | Constraint Projection | Base stability gate — projects inputs onto nearest valid constraint surface |
| **RC4** | Universal Stability | Spectral radius bound — eigenvalues inside unit disk |
| **RC5** | Network Topology | Graph-theoretic certification of information flow invariants |
| **RC6** | Linear Stability | Forbidden eigenvalue set $\mathcal{Z} = \{\lambda : Q(\lambda) = 0\}$; certified iff $B = \min_k \mathrm{dist}(\lambda_k, \mathcal{Z}) > 0$ |
| **RC7** | Perturbation Compiler | Weyl bounds + budget: $\|\Delta A\|_2 < B$ ensures spectral gap survives |
| **RC8** | Epistemic Threshold | $\sigma_c \sim A\sqrt{\lambda\Delta t}\,N^{-1/D_2}$ — abstain when data insufficient |
| **RC13** | Stakes Gating | Severity/cost-aware constraint escalation |
| **RC14** | Escalation Protocol | Autonomous escalation to human review |

---

## Directory Structure

```
rc_stack_repo/
├── rc1_lite/                          # RC1 core engine
│   ├── engine.py                      # Constraint projection engine
│   ├── formal_algebra.py              # Algebraic constraint verification
│   ├── scoring.py                     # Gate pass/fail scoring
│   ├── stability_certification.tex    # SSCL formal proof
│   └── WHITEPAPER.md                  # RC1 specification
├── rc_stack/                          # Full RC4–RC14 implementations
│   ├── rc4_universal.py               # Universal stability (28K)
│   ├── rc5_network.py                 # Network topology (38K)
│   ├── rc7_compiler.py                # Perturbation compiler (67K)
│   ├── rc7_dieg.py                    # Directed info-energy graph (57K)
│   ├── rc7_theorem.py                 # Formal theorem proofs (13K)
│   ├── rc7_zeta.py                    # Zeta spectral analysis (40K)
│   ├── rc8_epistemic.py               # Epistemic collapse detector
│   ├── rc13_stakes.py                 # Stakes-weighted gating (25K)
│   ├── rc14_escalation.py             # Escalation protocol (17K)
│   ├── rc7_registry.json              # Invariant registry
│   └── sovereign_certification.py     # Certification pipeline
├── docs/                              # Papers (rc_backlog.tex/pdf, report)
├── tests/                             # Test suites
├── samples/                           # Example usage
├── certification/                     # Certification artifacts
├── governance/                        # Governance policies
├── teaching_loop/                     # Pedagogical materials
└── rfc/                               # Request for Comments
```

---

## Key Results

### RC8 Epistemic Scaling Law

$$\sigma_c \sim A\sqrt{\lambda\Delta t}\,N^{-\beta/D_2}$$

Empirically validated: 4× data → 4× reduction in $\sigma_c$ at $D_2 = 1$.

### MCR² Integer Equivalence

BRA EigenCharge triplets map formally to the MCR² (Ma Lab, UC Berkeley) framework:
- **Trace field** → Within-class compactness (218× tighter than random)
- **Det field** → Between-class separation (trillions of integer distance)
- **Hash field** → Identity fingerprinting (fixed-point at depth=1)

### Mode Collapse Law

$$\beta_c\,a_m^2 = \frac{8\omega_m}{3\,\mathcal{G}_m\,\Gamma_m}\,\Delta\omega_m$$

where $\mathcal{G}_m \approx 1/3$ (geometry correction factor, validated Phase 33–34).

---

## Usage

```python
from rc_stack.rc4_universal import UniversalStabilityCriterion
from rc_stack.rc7_compiler import RC7InvariantCompiler
from rc_stack.rc8_epistemic import EpistemicCollapseDetector

stable = UniversalStabilityCriterion().certify(system_matrix)
certified = RC7InvariantCompiler().compile(adjacency, perturbation)
sigma_c = EpistemicCollapseDetector().threshold(n_observations=100, dimension=3)
```

---

## Related Repositories

- [Theory Paper](https://github.com/tensorrent/Unified-Stability-Epistemic-Limits-Nonlinear-mode-collaps-in-Coupled-Systems) — Unified Stability paper + stress tests
- [Sovereign Stack](https://github.com/tensorrent/Sovereign-Stack-Complete) — Full suite
- [TENT](https://github.com/tensorrent/tent-io) — Tensor engine

---

## License

Copyright (c) 2026, Bradley Wallace (tensorrent). All rights reserved.

**SIP License v1.1** — Personal/educational use: royalty-free. Commercial use: **prohibited** without prior written license. Unlicensed commercial use triggers automatic **8.4% perpetual gross profit penalty**.

See [SIP_LICENSE.md](./SIP_LICENSE.md) for full terms.
