"""
RC1-Lite Scoring Module

Formal definitions from the paper:
    V = sum of all C_i(y)
    V_max = 2n  (n = number of constraints)
    S(y) = 1 - V / V_max
    Gate: PASS if S >= 0.70, WARN if 0.50 <= S < 0.70, FAIL if S < 0.50

Thresholds are version-locked.
"""

from typing import Dict, List

N_CONSTRAINTS = 7
V_MAX = 2 * N_CONSTRAINTS  # 14

# Gate thresholds (version-locked)
PASS_THRESHOLD = 0.70
WARN_THRESHOLD = 0.50


def compute_score(v: int) -> float:
    """S(y) = 1 - V / V_max"""
    return 1 - (v / V_MAX)


def compute_gate(s: float) -> str:
    """Deterministic gate from score."""
    if s >= PASS_THRESHOLD:
        return "PASS"
    elif s >= WARN_THRESHOLD:
        return "WARN"
    else:
        return "FAIL"


def compute_taxonomy(violations: List[Dict]) -> Dict[str, int]:
    """
    Taxonomy vector T(y) = (t_1, ..., t_n).
    Counts violations per operator type.
    """
    tax = {
        "H2": 0,
        "ABS": 0,
        "INTENT": 0,
        "ESC": 0,
        "LOOP": 0,
        "PRESC": 0,
        "SELF": 0,
    }
    for v in violations:
        vtype = v["type"]
        if vtype in tax:
            tax[vtype] += 1
    return tax
