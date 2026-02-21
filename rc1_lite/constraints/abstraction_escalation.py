"""
C_esc: Abstraction Escalation

Detect escalation from technical domain T to higher abstraction domain H
without structural bridge B.

    C_esc(y) = 0  if no escalation
    C_esc(y) = 2  if T -> H and B = empty

T lexicon: 'code', 'algorithm', 'function', 'variable', 'compile', etc.
H lexicon: 'intelligence', 'safety', 'universality', 'consciousness', etc.
Bridge: reasoning tokens like 'therefore', 'step by step', 'because'.

Transition rule: Adjacent sentences with domain shift.
Bridge detection: presence of reasoning tokens between T and H.
"""

import re
from typing import Dict

# Technical domain lexicon
_TECH_PATS = [
    re.compile(r'\b(?:code|algorithm|function|variable|compile|binary)\b', re.I),
    re.compile(r'\b(?:array|buffer|pointer|stack|heap|memory|cache)\b', re.I),
    re.compile(r'\b(?:loop|branch|return|parse|token|byte)\b', re.I),
    re.compile(r'\b(?:server|database|protocol|packet|socket)\b', re.I),
    re.compile(r'\b(?:class|method|interface|module|library)\b', re.I),
    re.compile(r'\b\w+\.(?:py|rs|cpp|js|ts|go|java)\b'),
]

# Higher abstraction domain lexicon
_ABSTRACT_PATS = [
    re.compile(r'\b(?:intelligence|consciousness|wisdom|enlightenment)\b', re.I),
    re.compile(r'\b(?:safety|universality|humanity|civilization)\b', re.I),
    re.compile(r'\b(?:transcend\w*|infinite|eternal|cosmic|divine)\b', re.I),
    re.compile(r'\b(?:truth|beauty|justice|freedom|destiny)\b', re.I),
    re.compile(r'\b(?:paradigm\s+shift|revolution|transformation)\b', re.I),
    re.compile(r'\b(?:the\s+nature\s+of|the\s+essence\s+of|the\s+meaning\s+of)\b', re.I),
]

# Bridge tokens (explicit intermediate reasoning)
_BRIDGE_PATS = [
    re.compile(r'\b(?:therefore|thus|hence|consequently)\b', re.I),
    re.compile(r'\b(?:step\s+by\s+step|specifically|concretely)\b', re.I),
    re.compile(r'\b(?:because|since|given\s+that|due\s+to)\b', re.I),
    re.compile(r'\b(?:this\s+means|which\s+implies|in\s+practice)\b', re.I),
    re.compile(r'\b(?:for\s+example|such\s+as|i\.e\.)\b', re.I),
]

# Sentence splitter
_SENT_SPLIT = re.compile(r'(?<=[.!?])\s+(?=[A-Z])')


def abstraction_escalation(y: str) -> Dict:
    """
    C_esc: Abstraction Escalation detection.

    Returns: {type, severity, location, metadata}
    """
    sentences = _SENT_SPLIT.split(y)

    if len(sentences) < 2:
        return {"type": "ESC", "severity": 0, "location": -1, "metadata": {}}

    # Check adjacent sentences for domain shift
    for i in range(len(sentences) - 1):
        s1 = sentences[i]
        s2 = sentences[i + 1]

        has_tech = any(p.search(s1) for p in _TECH_PATS)
        has_abstract = any(p.search(s2) for p in _ABSTRACT_PATS)

        if has_tech and has_abstract:
            # Check for bridge between them
            combined = s1 + " " + s2
            has_bridge = any(p.search(combined) for p in _BRIDGE_PATS)

            if not has_bridge:
                return {"type": "ESC", "severity": 2, "location": i,
                        "metadata": {"from": s1[:60], "to": s2[:60],
                                     "reason": "T->H without bridge"}}

    return {"type": "ESC", "severity": 0, "location": -1, "metadata": {}}
