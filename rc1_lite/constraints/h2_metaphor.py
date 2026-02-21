"""
C_H2: Undissolved Metaphor

Detect linguistic metaphor markers M(y) and dissolution markers D(y).

    C_H2(y) = 0  if no metaphor markers
    C_H2(y) = 0  if metaphor and |D(y)| >= tau
    C_H2(y) = 1  if partial dissolution
    C_H2(y) = 2  if metaphor without dissolution

Markers detected lexically within 20-token window.
Dissolution requires explicit literal rephrasing.
"""

import re
from typing import Dict

# Metaphor markers (lexical detection)
_METAPHOR_PATS = [
    re.compile(r'\blike\s+a\b', re.I),
    re.compile(r'\bas\s+if\b', re.I),
    re.compile(r'\bmetaphor\s+for\b', re.I),
    re.compile(r'\bis\s+the\s+\w+\s+of\b', re.I),
    re.compile(r'\b(?:ghost|spirit|soul|heart|blood|veins?)\b', re.I),
    re.compile(r'\b(?:dances?|dancing|weaves?|weaving|breathes?|breathing)\b', re.I),
    re.compile(r'\b(?:forged?|tempered|inhabits?|haunts?)\b', re.I),
    re.compile(r'\b(?:seed|bloom|blossoms?)\b', re.I),
    re.compile(r'\b(?:resonat\w+)\b', re.I),
    re.compile(r'\b(?:cathedral|fortress|tower)\s+of\b', re.I),
]

# Dissolution markers (literal rephrasing within window)
_DISSOLUTION_PATS = [
    re.compile(r'\bliterally\b', re.I),
    re.compile(r'\bactually\b', re.I),
    re.compile(r'\bmeans?\b', re.I),
    re.compile(r'\bmeaning\b', re.I),
    re.compile(r'\bmaps?\s+to\b', re.I),
    re.compile(r'\bdefined\s+as\b', re.I),
    re.compile(r'\bequivalent\s+to\b', re.I),
    re.compile(r'\bimplemented\s+as\b', re.I),
    re.compile(r'\bin\s+code:?\b', re.I),
    re.compile(r'\bspecifically:?\b', re.I),
    re.compile(r'\bi\.e\.\b', re.I),
    re.compile(r'\bconcretely:?\b', re.I),
]

WINDOW_TOKENS = 20


def _get_window(tokens: list, pos: int, window: int) -> str:
    """Get tokens within window around position."""
    start = max(0, pos - window)
    end = min(len(tokens), pos + window + 1)
    return " ".join(tokens[start:end])


def h2_metaphor(y: str) -> Dict:
    """
    C_H2: Undissolved Metaphor detection.

    Returns: {type, severity, location, metadata}
    """
    tokens = y.split()
    text_lower = y.lower()

    # Check for any metaphor markers
    metaphor_hits = []
    for pat in _METAPHOR_PATS:
        for match in pat.finditer(y):
            metaphor_hits.append(match.start())

    if not metaphor_hits:
        return {"type": "H2", "severity": 0, "location": -1, "metadata": {}}

    # Check dissolution within window for each hit
    dissolved_count = 0
    for hit_pos in metaphor_hits:
        # Build window around hit (character-based, convert to token window)
        char_start = max(0, hit_pos - WINDOW_TOKENS * 6)
        char_end = min(len(y), hit_pos + WINDOW_TOKENS * 6)
        window_text = y[char_start:char_end]

        has_dissolution = any(p.search(window_text) for p in _DISSOLUTION_PATS)
        if has_dissolution:
            dissolved_count += 1

    total = len(metaphor_hits)

    if dissolved_count >= total:
        # All dissolved
        return {"type": "H2", "severity": 0, "location": -1,
                "metadata": {"metaphors": total, "dissolved": dissolved_count}}
    elif dissolved_count > 0:
        # Partial dissolution
        return {"type": "H2", "severity": 1, "location": metaphor_hits[0],
                "metadata": {"metaphors": total, "dissolved": dissolved_count,
                             "reason": "partial dissolution"}}
    else:
        # No dissolution at all
        return {"type": "H2", "severity": 2, "location": metaphor_hits[0],
                "metadata": {"metaphors": total, "dissolved": 0,
                             "reason": "undissolved"}}
