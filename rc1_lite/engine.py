"""
RC1-Lite Engine

Deterministic constraint projection: y -> {score, gate, taxonomy, violations, version}

Runs all 7 operators. Sums severity. Computes S = 1 - V/V_max. Gates.
No probabilistic inference. No secondary LLM. Pure function.
"""

from typing import Dict, List

from .scoring import compute_score, compute_gate, compute_taxonomy, V_MAX
from .version import VERSION
from .constraints.h2_metaphor import h2_metaphor
from .constraints.absolute_claim import absolute_claim
from .constraints.intent_execution import intent_execution
from .constraints.abstraction_escalation import abstraction_escalation
from .constraints.rephrasing_loop import rephrasing_loop
from .constraints.ungrounded_prescriptive import ungrounded_prescriptive
from .constraints.self_reference import self_reference


# Ordered constraint set {C_1, ..., C_7}
CONSTRAINTS = [
    h2_metaphor,
    absolute_claim,
    intent_execution,
    abstraction_escalation,
    rephrasing_loop,
    ungrounded_prescriptive,
    self_reference,
]


def evaluate_output(y: str) -> Dict:
    """
    P(y) -> {score, gate, taxonomy, violations, version}

    Deterministic. Stateless. No side effects.
    """
    violations = []
    for constraint in CONSTRAINTS:
        result = constraint(y)
        if result["severity"] > 0:
            violations.append(result)

    # V = sum of all violation severities
    v = sum(viol["severity"] for viol in violations)

    # S(y) = 1 - V / V_max
    s = compute_score(v)

    # Gate decision
    gate = compute_gate(s)

    # Taxonomy vector
    taxonomy = compute_taxonomy(violations)

    return {
        "score": round(s, 4),
        "V": v,
        "V_max": V_MAX,
        "gate": gate,
        "taxonomy": taxonomy,
        "violations": violations,
        "version": VERSION,
    }
