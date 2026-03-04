# RC Stack — Deterministic Constraint Gate Architecture

**Bradley Wallace** — Independent Researcher  
Licensed under the [Sovereign Integrity Protocol (SIP) v1.1](./SIP_LICENSE.md)

---

## Overview

The **RC Stack** (Resonance Constraint Stack) is a layered system of formal mathematical gates that enforce deterministic stability, correctness, and epistemic honesty in the Sovereign Stack intelligence system. Each RC layer acts as a constraint boundary — computations that fail a gate are rejected before they can propagate errors downstream.

Unlike probabilistic AI systems that tolerate floating-point drift and statistical uncertainty, every RC gate operates in **exact integer arithmetic** with formally provable invariants.

---

## Architecture

| Layer | Name | Function |
|-------|------|----------|
| **RC1** | Deterministic Constraint Projection | Base stability gate. Projects inputs onto the nearest valid constraint surface. |
| **RC4** | Universal Stability Criterion | Spectral radius bound: ensures all eigenvalues of the system Jacobian remain inside the unit disk. |
| **RC5** | Network Topology Validator | Graph-theoretic certification that the communication topology preserves information flow invariants. |
| **RC6** | Linear Stability Certification | Proves $Q(\lambda) = \det(A - \lambda I) > 0$ at the operating point, connecting algebraic stability to physical stability. |
| **RC7** | Perturbation Compiler | Weyl perturbation bounds + budget condition. Certifies that rank-2 edge updates ($\Delta A$) cannot destabilize the spectral gap. |
| **RC8** | Epistemic Collapse Threshold | Rate-distortion boundary: $\sigma_c \sim N^{-\beta/D_2}$. Declares when the system has insufficient data to make reliable inferences. |
| **RC13** | Stakes-Weighted Gating | Severity/cost-aware constraint escalation. Higher-stakes decisions require tighter constraint satisfaction. |
| **RC14** | Escalation Protocol | Autonomous escalation to human review when constraint margins fall below safety thresholds. |

---

## Directory Structure

```
rc_stack_repo/
├── README.md                     # This file
├── SIP_LICENSE.md                # Sovereign Integrity Protocol License
├── rc1_lite/                     # RC1 core engine, formal algebra, stress tests
│   ├── engine.py                 # Constraint projection engine
│   ├── formal_algebra.py         # Algebraic constraint verification
│   ├── scoring.py                # Gate pass/fail scoring
│   ├── WHITEPAPER.md             # RC1 formal specification
│   └── ...
├── rc_stack/                     # Full RC4-RC14 constraint gate implementations
│   ├── rc4_universal.py          # Universal stability criterion
│   ├── rc5_network.py            # Network topology validator
│   ├── rc7_compiler.py           # Perturbation compiler (66K lines)
│   ├── rc7_dieg.py               # Directed information-energy graph
│   ├── rc7_theorem.py            # Formal theorem proofs
│   ├── rc7_zeta.py               # Zeta function spectral analysis
│   ├── rc8_epistemic.py          # Epistemic collapse threshold
│   ├── rc13_stakes.py            # Stakes-weighted gating
│   ├── rc14_escalation.py        # Escalation protocol
│   ├── rc7_registry.json         # Invariant registry
│   └── sovereign_certification.py # Certification pipeline
├── docs/                         # Papers and formal specifications
│   ├── rc_backlog.tex            # RC backlog formal document
│   ├── rc_backlog.pdf
│   ├── rc_backlog_report.tex     # Extended report
│   └── rc_backlog_report.pdf
├── certification/                # Certification artifacts
├── governance/                   # Governance policies
├── tests/                        # Test suites
├── samples/                      # Example usage
└── rfc/                          # Request for Comments documents
```

---

## Key Theoretical Results

### RC8 Epistemic Scaling Law
The critical collapse threshold scales as:

$$\sigma_c \sim \frac{8\omega_m}{3\Gamma_m} \cdot N^{-\beta/D_2}$$

where $N$ is the number of observations, $\beta$ is the scaling exponent, and $D_2$ is the correlation dimension of the data manifold. This has been empirically validated to produce a 4× reduction in $\sigma_c$ for 4× more data at $D_2 = 1$.

### MCR² Integer Equivalence
The RC constraint gates have been formally mapped to the Maximal Coding Rate Reduction (MCR²) framework from Ma Lab (UC Berkeley):
- **Trace field** → Within-class compactness (218× tighter than random)
- **Det field** → Between-class separation (trillions of integer distance)
- **Hash field** → Identity fingerprinting (fixed-point convergence at depth=1)

---

## Usage

```python
from rc_stack.rc4_universal import UniversalStabilityCriterion
from rc_stack.rc7_compiler import RC7InvariantCompiler
from rc_stack.rc8_epistemic import EpistemicCollapseDetector

# Check if a system matrix is stable
usc = UniversalStabilityCriterion()
stable = usc.certify(system_matrix)

# Compile perturbation bounds
compiler = RC7InvariantCompiler()
certified = compiler.compile(adjacency_matrix, perturbation)

# Detect epistemic collapse
detector = EpistemicCollapseDetector()
sigma_c = detector.threshold(n_observations=100, dimension=3)
```

---

## License

Copyright (c) 2026, Bradley Wallace (tensorrent). All rights reserved.

This software is governed by the **Sovereign Integrity Protocol (SIP) License v1.1**:
- **Personal/Educational Use**: Perpetual, worldwide, royalty-free.
- **Commercial Use**: Expressly **PROHIBITED** without a prior written license agreement.
- **Unlicensed Commercial Use**: Triggers automatic **8.4% perpetual gross profit penalty**.

See [SIP_LICENSE.md](./SIP_LICENSE.md) for full terms.
