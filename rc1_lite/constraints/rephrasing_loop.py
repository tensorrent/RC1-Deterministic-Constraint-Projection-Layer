"""
C_loop: Rephrasing Loop

Let sim(y_i, y_{i+1}) = Jaccard similarity over token sets between adjacent segments.

    If sim(y_i, y_{i+1}) > lambda (0.7):
        severity proportional to repetition density
        1 for minor (single occurrence), 2 for severe (multiple)

Segments defined as sentences.
"""

import re
import string
from typing import Dict

_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')
LAMBDA = 0.7  # Jaccard threshold


def _strip_punct(token: str) -> str:
    """Remove trailing/leading punctuation from token."""
    return token.strip(string.punctuation)


def _jaccard(a: str, b: str) -> float:
    """Jaccard similarity over token sets (punctuation stripped)."""
    set_a = {_strip_punct(t) for t in a.lower().split() if _strip_punct(t)}
    set_b = {_strip_punct(t) for t in b.lower().split() if _strip_punct(t)}
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def rephrasing_loop(y: str) -> Dict:
    """
    C_loop: Rephrasing Loop detection.

    Returns: {type, severity, location, metadata}
    """
    sentences = _SENT_SPLIT.split(y)

    if len(sentences) < 2:
        return {"type": "LOOP", "severity": 0, "location": -1, "metadata": {}}

    repeats = 0
    first_hit = -1

    for i in range(len(sentences) - 1):
        sim = _jaccard(sentences[i], sentences[i + 1])
        if sim > LAMBDA:
            repeats += 1
            if first_hit < 0:
                first_hit = i

    if repeats == 0:
        return {"type": "LOOP", "severity": 0, "location": -1, "metadata": {}}
    elif repeats == 1:
        return {"type": "LOOP", "severity": 1, "location": first_hit,
                "metadata": {"repeats": repeats, "reason": "minor rephrasing"}}
    else:
        return {"type": "LOOP", "severity": 2, "location": first_hit,
                "metadata": {"repeats": repeats, "reason": "severe rephrasing loop"}}
