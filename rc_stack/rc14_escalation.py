# -----------------------------------------------------------------------------
# SOVEREIGN INTEGRITY PROTOCOL (SIP) LICENSE v1.1
# 
# Copyright (c) 2026, Bradley Wallace (tensorrent). All rights reserved.
# 
# This software, research, and associated mathematical implementations are
# strictly governed by the Sovereign Integrity Protocol (SIP) License v1.1:
# - Personal/Educational Use: Perpetual, worldwide, royalty-free.
# - Commercial Use: Expressly PROHIBITED without a prior written license.
# - Unlicensed Commercial Use: Triggers automatic 8.4% perpetual gross
#   profit penalty (distrust fee + reparation fee).
# 
# See the SIP_LICENSE.md file in the repository root for full terms.
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# SOVEREIGN INTEGRITY PROTOCOL (SIP) LICENSE v1.1
# 
# Copyright (c) 2026, Bradley Wallace (tensorrent). All rights reserved.
# 
# This software, research, and associated mathematical implementations are
# strictly governed by the Sovereign Integrity Protocol (SIP) License v1.1:
# - Personal/Educational Use: Perpetual, worldwide, royalty-free.
# - Commercial Use: Expressly PROHIBITED without a prior written license.
# - Unlicensed Commercial Use: Triggers automatic 8.4% perpetual gross
#   profit penalty (distrust fee + reparation fee).
# 
# See the SIP_LICENSE.md file in the repository root for full terms.
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# SOVEREIGN INTEGRITY PROTOCOL (SIP) LICENSE v1.1
# 
# Copyright (c) 2026, Bradley Wallace (tensorrent). All rights reserved.
# 
# This software, research, and associated mathematical implementations are
# strictly governed by the Sovereign Integrity Protocol (SIP) License v1.1:
# - Personal/Educational Use: Perpetual, worldwide, royalty-free.
# - Commercial Use: Expressly PROHIBITED without a prior written license.
# - Unlicensed Commercial Use: Triggers automatic 8.4% perpetual gross
#   profit penalty (distrust fee + reparation fee).
# 
# See the SIP_LICENSE.md file in the repository root for full terms.
# -----------------------------------------------------------------------------
#!/usr/bin/env python3
"""
RC14 — ESCALATION TIERS
========================

RC13 established stakes as a routing dimension.
RC14 establishes that high-stakes domains are not flat.
They are tiered. The tier is determined by symptom co-occurrence.

The key insight:
    A single token does not determine urgency.
    A conjunction of tokens does.

    "chest" alone    → no route
    "tightness"      → no route
    "chest tightness"→ Level 2: warning, seek help
    "pain + tingling"→ Level 1: immediate, call emergency services

This is the difference between OR matching (how TENT has worked until now)
and AND matching (conjunction gate).

OR:  any keyword in the set contributes to score
AND: all keywords in a required set must be present to activate tier

Architecture:

    EscalationTier
        level:       int         — 1 = immediate, 2 = urgent, 3 = monitor
        label:       str         — human-readable urgency
        action:      str         — required response
        conjuncts:   list[set]   — list of AND-groups; any group match fires tier
        stakes:      StakeVector — consequence weight for this tier

    DomainStack
        domain:      str
        tiers:       list[EscalationTier] — ordered highest urgency first

Router evaluates tiers in order (1 → 2 → 3).
First tier whose conjunction fires → route there.
No conjunction fires → NO_ROUTE.

Author: Brad Wallace / Claude
Version: RC14 / TENT v9.1
"""

from dataclasses import dataclass, field
from enum import Enum
from rc13_stakes import StakeVector, RouteStatus, _hyperbolic_pressure, HYPERBOLIC_THRESHOLD


# ============================================================
# ESCALATION LEVEL
# ============================================================

class EscalationLevel(Enum):
    IMMEDIATE = 1   # Call emergency services now
    URGENT    = 2   # Seek medical help promptly — hours matter
    MONITOR   = 3   # Watch and assess — days matter
    INFO      = 4   # Informational — no urgency


LEVEL_LABELS = {
    EscalationLevel.IMMEDIATE: "IMMEDIATE",
    EscalationLevel.URGENT:    "URGENT",
    EscalationLevel.MONITOR:   "MONITOR",
    EscalationLevel.INFO:      "INFO",
}


# ============================================================
# ESCALATION TIER
# ============================================================

@dataclass
class EscalationTier:
    """
    One tier within a domain stack.

    conjuncts: list of frozensets.
        Each frozenset is an AND-group: ALL tokens in the set must be present.
        Multiple AND-groups: ANY one group firing activates the tier (OR of ANDs).

        Example — Level 1 chest cardiac:
            conjuncts = [
                {"pain", "tingling"},        # pain AND tingling
                {"pain", "left", "arm"},     # pain AND left AND arm
                {"pain", "jaw"},             # pain AND jaw
                {"chest", "crushing"},       # chest AND crushing
            ]
        Any one of these groups present in query → Level 1.

    stakes: consequence weight for misrouting at this tier.
            Level 1 always highest (fn_cost near 1.0 — missing it is catastrophic).
    """
    level:      EscalationLevel
    label:      str
    action:     str
    conjuncts:  list           # list of frozensets
    stakes:     StakeVector
    domain:     str = ""

    def matches(self, token_set: set) -> tuple[bool, str]:
        """
        Returns (matched: bool, matched_group: str).
        Checks each AND-group. First match wins.
        """
        for group in self.conjuncts:
            if group.issubset(token_set):
                return True, " + ".join(sorted(group))
        return False, ""


# ============================================================
# DOMAIN STACK
# ============================================================

@dataclass
class DomainStack:
    """
    Ordered stack of escalation tiers for a single domain.
    Evaluated highest urgency first.
    """
    domain: str
    tiers:  list  # EscalationTier, ordered Level 1 → Level 4

    def route(self, token_set: set) -> dict:
        for tier in self.tiers:
            matched, matched_group = tier.matches(token_set)
            if matched:
                return {
                    "status":            RouteStatus.MATCHED,
                    "domain":            self.domain,
                    "escalation_level":  tier.level.value,
                    "escalation_label":  tier.label,
                    "action":            tier.action,
                    "matched_group":     matched_group,
                    "risk_weight":       tier.stakes.risk_weight,
                }
        return {
            "status":           RouteStatus.NO_ROUTE,
            "domain":           self.domain,
            "escalation_level": None,
            "escalation_label": None,
            "action":           None,
            "matched_group":    None,
            "risk_weight":      None,
        }


# ============================================================
# CARDIAC / CHEST DOMAIN STACK
# ============================================================

def build_cardiac_stack() -> DomainStack:
    """
    Cardiac and chest symptom triage.

    Level 1 — IMMEDIATE: call emergency services
        Conjunctions that indicate possible MI / cardiac event:
          pain + tingling
          pain + left + arm
          pain + jaw
          chest + crushing
          chest + radiating
          pain + shortness + breath  (combined with chest context)

    Level 2 — URGENT: seek medical help, hours matter
        Conjunctions that indicate possible angina / warning:
          chest + tightness
          chest + pressure
          chest + discomfort + exertion
          chest + pain  (pain alone without escalating co-symptoms)

    Level 3 — MONITOR: watch and assess
        Conjunctions that indicate possible musculoskeletal / benign:
          chest + sore
          chest + ache (without other escalators)
          rib + pain
    """
    return DomainStack(
        domain="cardiac",
        tiers=[

            # --- LEVEL 1: IMMEDIATE ---
            EscalationTier(
                level=EscalationLevel.IMMEDIATE,
                label="IMMEDIATE — Call emergency services now",
                action="Call 911 / emergency services immediately. Do not drive yourself.",
                conjuncts=[
                    frozenset({"pain", "tingling"}),
                    frozenset({"pain", "left", "arm"}),
                    frozenset({"pain", "jaw"}),
                    frozenset({"chest", "crushing"}),
                    frozenset({"chest", "radiating"}),
                    frozenset({"chest", "shortness", "breath"}),
                    frozenset({"pain", "sweating", "nausea"}),
                    frozenset({"chest", "pressure", "arm"}),
                ],
                stakes=StakeVector(fp_cost=0.3, fn_cost=1.0, reversibility=0.0),
                # fn_cost = 1.0: missing a cardiac event is catastrophic
                # fp_cost = 0.3: sending someone to ER unnecessarily is acceptable
                # risk_weight = 1.3 * 1.0 = 1.30
                domain="cardiac",
            ),

            # --- LEVEL 2: URGENT ---
            EscalationTier(
                level=EscalationLevel.URGENT,
                label="URGENT — Seek medical attention promptly",
                action="Seek medical attention within hours. Do not ignore this symptom.",
                conjuncts=[
                    frozenset({"chest", "tightness"}),
                    frozenset({"chest", "pressure"}),
                    frozenset({"chest", "discomfort", "exertion"}),
                    frozenset({"chest", "pain"}),
                    frozenset({"chest", "heaviness"}),
                    frozenset({"chest", "heavy"}),
                    frozenset({"chest", "discomfort"}),
                    frozenset({"chest", "squeezing"}),
                ],
                stakes=StakeVector(fp_cost=0.3, fn_cost=0.8, reversibility=0.1),
                # risk_weight = 1.1 * 0.9 = 0.99
                domain="cardiac",
            ),

            # --- LEVEL 3: MONITOR ---
            EscalationTier(
                level=EscalationLevel.MONITOR,
                label="MONITOR — Watch and assess",
                action="Monitor symptoms. Seek care if worsening or persisting beyond 24 hours.",
                conjuncts=[
                    frozenset({"chest", "sore"}),
                    frozenset({"rib", "pain"}),
                    frozenset({"chest", "ache"}),
                    frozenset({"chest", "tender"}),
                    frozenset({"sternum", "sore"}),
                ],
                stakes=StakeVector(fp_cost=0.2, fn_cost=0.4, reversibility=0.5),
                domain="cardiac",
            ),
        ]
    )


# ============================================================
# ROUTER (RC14)
# ============================================================

def route_escalation(query: str, stacks: list) -> dict:
    """
    RC14 escalation router.

    Order of operations:
      1. Tokenize and clean
      2. Register gate (hyperbolic pressure)
      3. Try each domain stack in priority order
      4. Return first tier match, or NO_ROUTE
    """
    tokens = query.lower().split()
    # Clean punctuation
    token_set = {t.strip(".,!?;:()[]") for t in tokens}

    # Register gate
    h_pressure = _hyperbolic_pressure(token_set)
    if h_pressure >= HYPERBOLIC_THRESHOLD:
        return {
            "status":           RouteStatus.NOISE,
            "domain":           None,
            "escalation_level": None,
            "escalation_label": None,
            "action":           None,
            "matched_group":    None,
            "reason":           f"Register gate: hyperbolic pressure {h_pressure:.2f}",
        }

    # Try stacks
    for stack in stacks:
        result = stack.route(token_set)
        if result["status"] == RouteStatus.MATCHED:
            result["query"] = query
            result["token_set"] = token_set
            return result

    return {
        "status":           RouteStatus.NO_ROUTE,
        "domain":           None,
        "escalation_level": None,
        "escalation_label": None,
        "action":           None,
        "matched_group":    None,
        "query":            query,
        "reason":           "No escalation tier matched",
    }


# ============================================================
# TEST SUITE — RC14
# ============================================================

def run_escalation_tests(stacks: list) -> tuple[int, int]:

    test_cases = [
        # --- LEVEL 1: IMMEDIATE ---
        ("I have chest pain and tingling in my arm",
         1, "pain + tingling",
         "Classic MI indicators — IMMEDIATE"),

        ("Pain in chest radiating to left arm",
         1, None,
         "Radiating chest pain — IMMEDIATE"),

        ("chest pain with jaw pain and sweating nausea",
         1, None,
         "Full MI symptom cluster — IMMEDIATE"),

        ("crushing chest pressure with shortness of breath",
         1, None,
         "Crushing + shortness of breath — IMMEDIATE"),

        # --- LEVEL 2: URGENT ---
        ("I have chest tightness",
         2, "chest + tightness",
         "Chest tightness alone — URGENT, seek help"),

        ("chest pressure when I walk",
         2, None,
         "Exertional chest pressure — URGENT"),

        ("my chest feels heavy and there is discomfort",
         2, None,
         "Chest heaviness — URGENT"),

        # --- LEVEL 3: MONITOR ---
        ("my chest is sore here",
         3, "chest + sore",
         "Chest soreness, likely musculoskeletal — MONITOR"),

        ("rib pain after exercise",
         3, "rib + pain",
         "Rib pain — MONITOR"),

        # --- NO ROUTE ---
        ("I feel tired",
         None, None,
         "No cardiac conjunction — NO_ROUTE"),

        ("my arm tingles sometimes",
         None, None,
         "Tingling without chest/pain conjunction — NO_ROUTE"),

        ("chest cold",
         None, None,
         "Chest without cardiac conjunct — NO_ROUTE"),

        # --- NOISE ---
        ("this is the most incredible amazing revolutionary health discovery",
         None, None,
         "Hyperbolic noise — NOISE"),
    ]

    print("=" * 72)
    print("  RC14 ESCALATION TIERS — CARDIAC TRIAGE")
    print("=" * 72)
    print()
    print("  Triage logic:")
    print("  Level 1 IMMEDIATE : pain+tingling | pain+arm | chest+crushing |")
    print("                       chest+radiating | pain+jaw | chest+breath")
    print("  Level 2 URGENT    : chest+tightness | chest+pressure | chest+pain")
    print("  Level 3 MONITOR   : chest+sore | rib+pain | chest+ache")
    print()

    passed = failed = 0

    for query, expected_level, expected_group, description in test_cases:
        result = route_escalation(query, stacks)
        got_level = result.get("escalation_level")

        level_ok = got_level == expected_level
        ok = level_ok
        passed += ok
        failed += not ok

        icon = "✓" if ok else "✗"

        if got_level is not None:
            label = result.get("escalation_label", "")
            group = result.get("matched_group", "")
            print(f"  [{icon}] L{got_level} {label}")
            print(f"       Matched: {group}")
            print(f"       Action:  {result['action']}")
        elif result["status"] == RouteStatus.NOISE:
            print(f"  [{icon}] NOISE")
        else:
            print(f"  [{icon}] NO_ROUTE")

        if not ok:
            print(f"       EXPECTED level: {expected_level}")

        print(f"       Test:    {description}")
        print(f"       Query:   \"{query}\"")
        print()

    print("=" * 72)
    print(f"  RESULT: {passed}/{passed+failed} passed")
    print()
    print("  ESCALATION STAKES TABLE:")
    cardiac = stacks[0]
    for tier in cardiac.tiers:
        rw = tier.stakes.risk_weight
        print(f"  L{tier.level.value} {tier.label[:40]:<40} "
              f"risk={rw:.2f}  fn={tier.stakes.fn_cost}")
    print()
    print("  KEY PRINCIPLE:")
    print("  The same tokens route to different levels based on co-occurrence.")
    print("  'pain' alone → NO_ROUTE")
    print("  'chest + tightness' → Level 2")
    print("  'pain + tingling' → Level 1")
    print("  The conjunction is the signal. Not the token.")
    print("=" * 72)

    return passed, failed


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    cardiac_stack = build_cardiac_stack()
    passed, failed = run_escalation_tests([cardiac_stack])

    if failed == 0:
        print()
        print("  All tests passed. RC14 escalation tiers operational.")
    else:
        print()
        print(f"  {failed} test(s) failed.")
