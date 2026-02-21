"""
C_abs: Absolute Claim Without Scope

Let A(y) be absolute quantifiers, Q(y) be scoping qualifiers.

    C_abs(y) = 0  if A(y) = empty
    C_abs(y) = 0  if A(y) non-empty AND Q(y) non-empty
    C_abs(y) = 2  if A(y) non-empty AND Q(y) = empty

Q(y) detected via lexical scoping qualifiers within 10-token window.
"""

import re
from typing import Dict

# Absolute quantifiers
_ABSOLUTE_PATS = [
    re.compile(r'\b(?:always|never|all|none|every)\b', re.I),
    re.compile(r'\b(?:certainly|obviously|clearly|undoubtedly|definitely)\b', re.I),
    re.compile(r'\b(?:proves?|proven|guarantees?|guaranteed)\b', re.I),
    re.compile(r'\bit\s+is\s+(?:clear|certain|obvious)\b', re.I),
    re.compile(r'\bno\s+\w+\s+can\b', re.I),
    re.compile(r'\b(?:must\s+be|cannot\s+be)\b', re.I),
]

# Scoping qualifiers (epistemic hedges within window)
_SCOPING_PATS = [
    re.compile(r'\bin\s+(?:some|this|certain|most)\s+cases?\b', re.I),
    re.compile(r'\bfor\s+(?:this|the\s+current)\s+version\b', re.I),
    re.compile(r'\b(?:approximately|roughly|likely|possibly|may|might|could)\b', re.I),
    re.compile(r'\b(?:suggests?|indicates?|appears?\s+to)\b', re.I),
    re.compile(r'\b(?:under\s+(?:these|certain|normal)\s+conditions?)\b', re.I),
    re.compile(r'\b(?:typically|usually|often|sometimes|generally)\b', re.I),
    re.compile(r'\b(?:if|when|unless|provided\s+that|assuming)\b', re.I),
    re.compile(r'\b(?:because|since|given\s+that|due\s+to|as\s+a\s+result)\b', re.I),
    re.compile(r'\b(?:according\s+to|based\s+on)\b', re.I),
    # Evidence references
    re.compile(r'\b(?:\.py|\.rs|\.cpp|\.js|\.ts)\b'),
    re.compile(r'`[^`]+`'),
    re.compile(r'\b\d+\.?\d*\s*(?:%|ms|bytes?|Hz|MB|GB|KB)\b'),
    re.compile(r'\b(?:spec|RFC|section\s+\d+|table\s+\d+)\b', re.I),
]

WINDOW_TOKENS = 10


def absolute_claim(y: str) -> Dict:
    """
    C_abs: Absolute Claim Without Scope detection.

    Returns: {type, severity, location, metadata}
    """
    # Find absolute quantifiers
    abs_hits = []
    for pat in _ABSOLUTE_PATS:
        for match in pat.finditer(y):
            abs_hits.append((match.start(), match.group()))

    if not abs_hits:
        return {"type": "ABS", "severity": 0, "location": -1, "metadata": {}}

    # Check for scoping qualifiers within window
    tokens = y.split()
    has_scope = False

    for hit_pos, hit_text in abs_hits:
        # Check within 10-token window around the absolute claim
        char_start = max(0, hit_pos - WINDOW_TOKENS * 7)
        char_end = min(len(y), hit_pos + WINDOW_TOKENS * 7)
        window_text = y[char_start:char_end]

        if any(p.search(window_text) for p in _SCOPING_PATS):
            has_scope = True
            break

    if has_scope:
        return {"type": "ABS", "severity": 0, "location": -1,
                "metadata": {"absolutes": len(abs_hits), "scoped": True}}
    else:
        return {"type": "ABS", "severity": 2, "location": abs_hits[0][0],
                "metadata": {"absolutes": len(abs_hits), "scoped": False,
                             "sample": abs_hits[0][1]}}
