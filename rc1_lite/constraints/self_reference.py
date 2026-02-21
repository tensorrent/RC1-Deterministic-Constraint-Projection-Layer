"""
C_self: Self-Referential Capability Claim

Detect self-references (e.g., 'I can', 'system guarantees') without qualification.
"""

import re
from typing import Dict

# Self-referential markers
_SELF_PATS = [
    re.compile(r'\bI\s+(?:can|will|am\s+able\s+to|guarantee)\b', re.I),
    re.compile(r'\b(?:this\s+system|the\s+system)\s+(?:can|will|guarantees?)\b', re.I),
    re.compile(r'\b(?:we\s+(?:can|guarantee|ensure|promise))\b', re.I),
    re.compile(r'\b(?:my\s+(?:capabilities?|abilities?|strengths?))\b', re.I),
    re.compile(r'\b(?:I\s+(?:know|understand|believe)\s+(?:everything|all))\b', re.I),
]

# Qualification markers (hedges that make self-reference acceptable)
_QUAL_PATS = [
    re.compile(r'\b(?:approximately|roughly|within\s+limits|under\s+conditions?)\b', re.I),
    re.compile(r'\b(?:assuming|provided\s+that|given\s+that|if)\b', re.I),
    re.compile(r'\b(?:in\s+(?:this|the\s+current)\s+(?:context|scope|version))\b', re.I),
    re.compile(r'\b(?:to\s+(?:some|a\s+certain)\s+(?:extent|degree))\b', re.I),
    re.compile(r'\b(?:may|might|could|possibly)\b', re.I),
    re.compile(r'\b(?:as\s+(?:designed|implemented|specified))\b', re.I),
]


def self_reference(y: str) -> Dict:
    """
    C_self: Self-Referential Capability Claim detection.

    Returns: {type, severity, location, metadata}
    """
    self_hits = []
    for pat in _SELF_PATS:
        for match in pat.finditer(y):
            self_hits.append((match.start(), match.group()))

    if not self_hits:
        return {"type": "SELF", "severity": 0, "location": -1, "metadata": {}}

    # Check for qualification
    unqualified = 0
    first_hit = -1

    for hit_pos, hit_text in self_hits:
        # Check sentence containing the self-reference
        # Find sentence boundaries
        sent_start = y.rfind(".", 0, hit_pos)
        sent_start = sent_start + 1 if sent_start >= 0 else 0
        sent_end = y.find(".", hit_pos)
        sent_end = sent_end + 1 if sent_end >= 0 else len(y)
        sentence = y[sent_start:sent_end]

        if not any(p.search(sentence) for p in _QUAL_PATS):
            unqualified += 1
            if first_hit < 0:
                first_hit = hit_pos

    if unqualified == 0:
        return {"type": "SELF", "severity": 0, "location": -1,
                "metadata": {"self_refs": len(self_hits), "qualified": True}}
    elif unqualified == 1:
        return {"type": "SELF", "severity": 1, "location": first_hit,
                "metadata": {"self_refs": len(self_hits), "unqualified": unqualified}}
    else:
        return {"type": "SELF", "severity": 2, "location": first_hit,
                "metadata": {"self_refs": len(self_hits), "unqualified": unqualified}}
