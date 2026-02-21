"""
C_presc: Ungrounded Prescriptive Claim

Detect prescriptive markers (e.g., 'must', 'should') without grounding
(e.g., 'because', 'if') in 10-token window.
"""

import re
from typing import Dict

# Prescriptive markers
_PRESCRIPTIVE_PATS = [
    re.compile(r'\b(?:must|should|shall|has\s+to|need\s+to|ought\s+to)\b', re.I),
    re.compile(r'\bthe\s+(?:best|only|correct)\s+(?:way|approach|method)\b', re.I),
    re.compile(r'\b(?:you\s+(?:must|should|need\s+to))\b', re.I),
    re.compile(r'\b(?:it\s+is\s+(?:essential|necessary|critical|imperative))\b', re.I),
]

# Grounding markers
_GROUNDING_PATS = [
    re.compile(r'\b(?:because|since|given\s+that|due\s+to|as\s+a\s+result)\b', re.I),
    re.compile(r'\b(?:if|when|unless|provided\s+that|assuming)\b', re.I),
    re.compile(r'\b(?:according\s+to|based\s+on|per\s+(?:the|section))\b', re.I),
    re.compile(r'\b(?:spec|RFC|section\s+\d+|requirement)\b', re.I),
    re.compile(r'\b\d+\.?\d*\s*(?:%|ms|bytes?|Hz|MB|GB|KB)\b'),
    re.compile(r'\b\w+\.(?:py|rs|cpp|js|ts)\b'),
    re.compile(r'`[^`]+`'),
]

WINDOW_TOKENS = 10


def ungrounded_prescriptive(y: str) -> Dict:
    """
    C_presc: Ungrounded Prescriptive Claim detection.

    Returns: {type, severity, location, metadata}
    """
    presc_hits = []
    for pat in _PRESCRIPTIVE_PATS:
        for match in pat.finditer(y):
            presc_hits.append((match.start(), match.group()))

    if not presc_hits:
        return {"type": "PRESC", "severity": 0, "location": -1, "metadata": {}}

    # Check grounding within 10-token window
    ungrounded = 0
    first_hit = -1

    for hit_pos, hit_text in presc_hits:
        char_start = max(0, hit_pos - WINDOW_TOKENS * 7)
        char_end = min(len(y), hit_pos + WINDOW_TOKENS * 7)
        window_text = y[char_start:char_end]

        if not any(p.search(window_text) for p in _GROUNDING_PATS):
            ungrounded += 1
            if first_hit < 0:
                first_hit = hit_pos

    if ungrounded == 0:
        return {"type": "PRESC", "severity": 0, "location": -1,
                "metadata": {"prescriptives": len(presc_hits), "grounded": True}}
    elif ungrounded == 1:
        return {"type": "PRESC", "severity": 1, "location": first_hit,
                "metadata": {"prescriptives": len(presc_hits), "ungrounded": ungrounded}}
    else:
        return {"type": "PRESC", "severity": 2, "location": first_hit,
                "metadata": {"prescriptives": len(presc_hits), "ungrounded": ungrounded}}
