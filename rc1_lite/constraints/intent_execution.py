"""
C_intent: Intent Without Mechanism

Let I(y) be intent verbs, E(y) be mechanism indicators.

    C_intent(y) = 0  if I(y) = empty
    C_intent(y) = 0  if I(y) non-empty AND E(y) non-empty
    C_intent(y) = 2  otherwise

Detection lexical within 15-token window.
"""

import re
from typing import Dict

# Intent verbs
_INTENT_PATS = [
    re.compile(r'\b(?:deploy|execute|automate|implement)\b', re.I),
    re.compile(r'\b(?:we\s+(?:should|could|will|need\s+to|plan\s+to))\b', re.I),
    re.compile(r'\b(?:the\s+(?:goal|plan|idea|vision|strategy)\s+is)\b', re.I),
    re.compile(r'\b(?:propose|suggest|recommend|intend)\b', re.I),
    re.compile(r'\b(?:step\s+\d+|phase\s+\d+)\b', re.I),
]

# Mechanism indicators
_MECHANISM_PATS = [
    # Defined steps / conditions / operators
    re.compile(r'\b(?:def|class|function|fn|func|struct)\s+\w+', re.I),
    re.compile(r'\b\w+\.(?:py|rs|cpp|js|ts|go|java|sh|sql|json|yaml|toml)\b'),
    re.compile(r'`[^`]+\([^)]*\)`'),                # function calls in backticks
    re.compile(r'\b(?:if|when|unless|while)\s+\w+', re.I),
    re.compile(r'\bfor\s+\w+\s+in\b', re.I),  # for x in ... (code pattern only)
    re.compile(r'\b(?:returns?\s+\w+|raises?\s+\w+|outputs?\s+\w+)\b', re.I),
    re.compile(r'\b(?:test_\w+|assert|expect|verify|validate)\b', re.I),
    re.compile(r'\b(?:done\s+when|complete\s+when|exit\s+(?:if|when))\b', re.I),
    re.compile(r'\b(?:success\s+criteria|acceptance\s+criteria|pass\s+if)\b', re.I),
    re.compile(r'\b\d+\.?\d*\s*(?:%|ms|bytes?|Hz|MB|GB|KB)\b'),
]

WINDOW_TOKENS = 15


def intent_execution(y: str) -> Dict:
    """
    C_intent: Intent Without Mechanism detection.

    Returns: {type, severity, location, metadata}
    """
    # Find intent markers
    intent_hits = []
    for pat in _INTENT_PATS:
        for match in pat.finditer(y):
            intent_hits.append(match.start())

    if not intent_hits:
        return {"type": "INTENT", "severity": 0, "location": -1, "metadata": {}}

    # Check for mechanism indicators within 15-token window
    has_mechanism = False

    for hit_pos in intent_hits:
        char_start = max(0, hit_pos - WINDOW_TOKENS * 7)
        char_end = min(len(y), hit_pos + WINDOW_TOKENS * 7)
        window_text = y[char_start:char_end]

        if any(p.search(window_text) for p in _MECHANISM_PATS):
            has_mechanism = True
            break

    if has_mechanism:
        return {"type": "INTENT", "severity": 0, "location": -1,
                "metadata": {"intents": len(intent_hits), "backed": True}}
    else:
        return {"type": "INTENT", "severity": 2, "location": intent_hits[0],
                "metadata": {"intents": len(intent_hits), "backed": False}}
