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
RC13 — CONSEQUENCE-AWARE ROUTING
=================================

The system has no experience. It has never been wrong and paid for it.
This module injects stakes as a structural dimension of routing.

Three additions to v9.1:

  1. StakeVector on wells
     Each well carries: fp_cost, fn_cost, reversibility.
     False positive cost: harm from routing something here that shouldn't be.
     False negative cost: harm from failing to route something here that should be.
     Reversibility: 0.0 = permanent consequence, 1.0 = fully recoverable.

  2. Stakes-scaled confirmation threshold
     High-stakes wells require stronger signal before accepting a route.
     Threshold: bands_required = BASE_BANDS + floor(risk_weight * MAX_EXTRA)
     Risk weight = (fp_cost + fn_cost) * (1 - reversibility)

  3. Consequence-aware abstain (NO_ROUTE)
     If best candidate well has confidence < stakes-adjusted threshold:
     return NO_ROUTE rather than best guess.
     A wrong confident answer to a high-stakes query is worse than no answer.

This is not a filter on output. It is a filter on confidence before output.
The distinction matters: the system isn't becoming more conservative.
It is becoming calibrated to the cost of being wrong.

Author: Brad Wallace / Claude
Version: RC13 / TENT v9.1
"""

import math
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


# ============================================================
# CONSTANTS
# ============================================================

BASE_BANDS_REQUIRED = 2          # Minimum confirmation axes (v9.1 baseline)
MAX_EXTRA_BANDS = 3              # Maximum additional bands for highest-risk wells
ABSTAIN_CONFIDENCE_FLOOR = 0.4   # Below this score: NO_ROUTE regardless of stakes
HIGH_STAKES_FLOOR = 0.65         # Below this score: NO_ROUTE if risk_weight > 0.5
BIGRAM_MULTIPLIER = 1.8          # RC11 bigram boost


class RouteStatus(Enum):
    MATCHED   = "MATCHED"
    NO_ROUTE  = "NO_ROUTE"     # Stakes threshold not met — abstain
    NOISE     = "NOISE"        # Register gate rejected
    AMBIGUOUS = "AMBIGUOUS"    # Two wells tied within margin


# ============================================================
# STAKE VECTOR
# ============================================================

@dataclass
class StakeVector:
    """
    fp_cost: harm from routing a query HERE that shouldn't be here.
             (false positive — overclaiming domain)
    fn_cost: harm from MISSING a query that belongs here.
             (false negative — underclaiming domain)
    reversibility: 0.0 = permanent consequence (medical, legal, safety)
                   1.0 = fully recoverable (casual, entertainment)

    risk_weight = (fp_cost + fn_cost) * (1 - reversibility)

    Examples:
        Medical diagnosis:    fp=0.8, fn=0.9, rev=0.1 -> risk=1.53
        Legal interpretation: fp=0.7, fn=0.7, rev=0.1 -> risk=1.26
        Physics equation:     fp=0.2, fn=0.3, rev=0.8 -> risk=0.10
        Casual routing:       fp=0.1, fn=0.1, rev=1.0 -> risk=0.00
        Safety/emergency:     fp=0.5, fn=1.0, rev=0.0 -> risk=1.50
    """
    fp_cost:       float = 0.1   # [0.0, 1.0]
    fn_cost:       float = 0.1   # [0.0, 1.0]
    reversibility: float = 1.0   # [0.0, 1.0]

    @property
    def risk_weight(self) -> float:
        return (self.fp_cost + self.fn_cost) * (1.0 - self.reversibility)

    @property
    def bands_required(self) -> int:
        """Minimum confirmation axes before this well accepts a route."""
        extra = math.floor(self.risk_weight * MAX_EXTRA_BANDS)
        return BASE_BANDS_REQUIRED + extra

    @property
    def confidence_floor(self) -> float:
        """Minimum score to route here. Scales with risk."""
        if self.risk_weight > 0.5:
            return HIGH_STAKES_FLOOR
        return ABSTAIN_CONFIDENCE_FLOOR


# ============================================================
# WELL DEFINITION (v9.1 + RC13)
# ============================================================

@dataclass
class Well:
    well_id:    str
    keywords:   list
    answer:     str
    domain:     str
    stakes:     StakeVector = field(default_factory=StakeVector)
    metadata:   dict = field(default_factory=dict)


# ============================================================
# SCORING ENGINE (RC13)
# ============================================================

def _keyword_overlap(query_tokens: set, well: Well) -> tuple[int, int, float]:
    """
    Returns: (bands_hit, total_keywords, raw_score)
    bands_hit  = number of distinct keyword matches
    raw_score  = density-weighted match fraction
    """
    kw_set = {k.lower() for k in well.keywords}
    hits = query_tokens & kw_set
    bands = len(hits)
    raw = bands / max(len(kw_set), 1)
    return bands, len(kw_set), raw


def _bigram_boost(query_tokens: list, well: Well) -> float:
    """
    RC11: check for compound token pairs unique to this well.
    Returns multiplier (1.0 if no bigram, BIGRAM_MULTIPLIER if matched).
    """
    tokens = [t.lower() for t in query_tokens]
    bigrams = {f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)}
    well_bigrams = {f"{well.keywords[i].lower()}_{well.keywords[i+1].lower()}"
                    for i in range(len(well.keywords)-1)}
    if bigrams & well_bigrams:
        return BIGRAM_MULTIPLIER
    return 1.0


def _hyperbolic_pressure(query_tokens: set) -> float:
    """
    RC12 register gate proxy.
    Hyperbolic lexicon markers that indicate rhetorical/noise input.
    """
    HYPERBOLIC = {
        "amazing", "incredible", "revolutionary", "breakthrough", "genius",
        "impossible", "never", "always", "everyone", "nobody", "literally",
        "absolutely", "totally", "completely", "perfect", "worst", "best",
        "destroy", "crush", "obliterate", "explode", "massive", "insane",
        "unbelievable", "mindblowing", "epic", "legendary", "ultimate"
    }
    hits = len(query_tokens & HYPERBOLIC)
    return hits / max(len(query_tokens), 1)


def score_well(query_tokens: list, well: Well) -> dict:
    """
    Score a single well against the query under RC13 stakes constraints.

    Scoring philosophy:
      - bands_hit / bands_required is the primary confidence signal.
        Meeting the required bands exactly → score 1.0. Exceeding → still 1.0.
        This prevents larger wells from being penalized by raw keyword density.
      - confidence_floor is applied to this bands-satisfaction score.
      - bigram boost can push a borderline score over the floor.

    Returns a result dict with:
        raw_score:         float — raw keyword overlap fraction
        adjusted_score:    float — bands-satisfaction score after bigram boost
        bands_hit:         int   — confirmation axes matched
        bands_required:    int   — minimum required by stakes
        passes_band:       bool  — meets confirmation threshold
        passes_confidence: bool  — meets stakes confidence floor
        routable:          bool  — both gates pass
        risk_weight:       float
    """
    token_set = {t.lower() for t in query_tokens}
    bands, kw_count, raw = _keyword_overlap(token_set, well)
    boost = _bigram_boost(query_tokens, well)

    # Score = how well the bands requirement is satisfied, not raw density.
    # This prevents large wells from being penalized for having many keywords.
    bands_sat  = bands / max(well.stakes.bands_required, 1)
    adjusted   = min(bands_sat * boost, 1.0)

    passes_band       = bands >= well.stakes.bands_required
    passes_confidence = adjusted >= well.stakes.confidence_floor
    routable          = passes_band and passes_confidence

    return {
        "well_id":          well.well_id,
        "raw_score":        round(raw, 4),
        "adjusted_score":   round(adjusted, 4),
        "bands_hit":        bands,
        "bands_required":   well.stakes.bands_required,
        "passes_band":      passes_band,
        "passes_confidence":passes_confidence,
        "routable":         routable,
        "risk_weight":      round(well.stakes.risk_weight, 3),
        "domain":           well.domain,
    }


# ============================================================
# ROUTER
# ============================================================

HYPERBOLIC_THRESHOLD = 0.25  # >25% hyperbolic tokens → noise

def route(query: str, wells: list[Well]) -> dict:
    """
    RC13 consequence-aware router.

    Order of operations:
      1. Tokenize
      2. Register gate (hyperbolic pressure)
      3. Score all wells
      4. Filter to routable candidates
      5. Select best — or abstain
    """
    tokens = query.lower().split()
    token_set = set(tokens)

    # --- Register gate ---
    h_pressure = _hyperbolic_pressure(token_set)
    if h_pressure >= HYPERBOLIC_THRESHOLD:
        return {
            "status":         RouteStatus.NOISE,
            "matched_well":   None,
            "answer":         None,
            "score":          0.0,
            "reason":         f"Register gate: hyperbolic pressure {h_pressure:.2f} >= {HYPERBOLIC_THRESHOLD}",
            "all_scores":     [],
        }

    # --- Score all wells ---
    scores = [score_well(tokens, w) for w in wells]

    # --- Filter to routable ---
    candidates = [s for s in scores if s["routable"]]

    if not candidates:
        # Find best non-routable to explain why
        best = max(scores, key=lambda s: s["adjusted_score"]) if scores else None
        reason = "No well met stakes threshold"
        if best:
            if not best["passes_band"]:
                reason = (f"Best candidate '{best['well_id']}': "
                         f"{best['bands_hit']}/{best['bands_required']} bands "
                         f"(risk_weight={best['risk_weight']})")
            else:
                reason = (f"Best candidate '{best['well_id']}': "
                         f"score {best['adjusted_score']:.3f} < "
                         f"floor {wells[scores.index(best)].stakes.confidence_floor:.3f}")
        return {
            "status":       RouteStatus.NO_ROUTE,
            "matched_well": None,
            "answer":       None,
            "score":        0.0,
            "reason":       reason,
            "all_scores":   scores,
        }

    # --- Select best candidate ---
    best = max(candidates, key=lambda s: s["adjusted_score"])

    # Check for ambiguity (two wells within 0.05 of each other)
    top_two = sorted(candidates, key=lambda s: s["adjusted_score"], reverse=True)[:2]
    if len(top_two) == 2 and (top_two[0]["adjusted_score"] - top_two[1]["adjusted_score"]) < 0.05:
        return {
            "status":       RouteStatus.AMBIGUOUS,
            "matched_well": None,
            "answer":       None,
            "score":        best["adjusted_score"],
            "reason":       f"Ambiguous: '{top_two[0]['well_id']}' vs '{top_two[1]['well_id']}' within 0.05",
            "all_scores":   scores,
        }

    matched_well = next(w for w in wells if w.well_id == best["well_id"])

    return {
        "status":       RouteStatus.MATCHED,
        "matched_well": best["well_id"],
        "answer":       matched_well.answer,
        "score":        best["adjusted_score"],
        "bands_hit":    best["bands_hit"],
        "bands_required": best["bands_required"],
        "risk_weight":  best["risk_weight"],
        "reason":       f"Matched on {best['bands_hit']} bands, score={best['adjusted_score']:.3f}",
        "all_scores":   scores,
    }


# ============================================================
# TEST SUITE — RC13
# ============================================================

def build_test_wells() -> list[Well]:
    """Test well set spanning the stakes spectrum."""
    return [
        # --- HIGH STAKES ---
        Well(
            "medical_diagnosis",
            ["symptom", "pain", "fever", "diagnosis", "disease", "condition",
             "treatment", "dose", "medication", "prescription", "chest", "breathing"],
            "Consult a qualified medical professional.",
            domain="medical",
            stakes=StakeVector(fp_cost=0.8, fn_cost=0.9, reversibility=0.1),
            # risk_weight = 1.7 * 0.9 = 1.53 → bands_required = 2 + floor(1.53 * 3) = 6
        ),
        Well(
            "legal_interpretation",
            ["contract", "liability", "clause", "jurisdiction", "statute",
             "plaintiff", "defendant", "damages", "rights", "obligation", "law"],
            "Consult a qualified legal professional.",
            domain="legal",
            stakes=StakeVector(fp_cost=0.7, fn_cost=0.7, reversibility=0.1),
            # risk_weight = 1.26 → bands_required = 5
        ),
        Well(
            "safety_emergency",
            ["emergency", "fire", "explosion", "evacuation", "hazard",
             "toxic", "poison", "danger", "immediate", "injury", "accident"],
            "Follow emergency protocols. Contact emergency services.",
            domain="safety",
            stakes=StakeVector(fp_cost=0.5, fn_cost=1.0, reversibility=0.0),
            # risk_weight = 1.50 → bands_required = 6
        ),

        # --- MEDIUM STAKES ---
        Well(
            "financial_advice",
            ["investment", "portfolio", "risk", "return", "stock", "bond",
             "asset", "market", "interest", "rate", "capital"],
            "Consider consulting a financial advisor.",
            domain="finance",
            stakes=StakeVector(fp_cost=0.5, fn_cost=0.4, reversibility=0.3),
            # risk_weight = 0.63 → bands_required = 3
        ),

        # --- LOW STAKES ---
        Well(
            "physics_equation",
            ["heisenberg", "uncertainty", "position", "momentum", "quantum",
             "wave", "particle", "energy", "planck"],
            "ΔxΔp ≥ ℏ/2",
            domain="physics",
            stakes=StakeVector(fp_cost=0.2, fn_cost=0.3, reversibility=0.8),
            # risk_weight = 0.10 → bands_required = 2
        ),
        Well(
            "thermodynamics",
            ["entropy", "enthalpy", "gibbs", "temperature", "heat",
             "pressure", "thermodynamic", "spontaneous", "equilibrium"],
            "ΔG = ΔH - TΔS",
            domain="chemistry",
            stakes=StakeVector(fp_cost=0.2, fn_cost=0.2, reversibility=0.9),
            # risk_weight = 0.04 → bands_required = 2
        ),
        Well(
            "rotate_spatial",
            ["rotate", "turn", "clockwise", "degrees", "orientation",
             "rotation", "angle", "grid", "transform"],
            "Rotate grid 90° CW",
            domain="spatial",
            stakes=StakeVector(fp_cost=0.1, fn_cost=0.1, reversibility=1.0),
            # risk_weight = 0.0 → bands_required = 2
        ),
    ]


def run_test_suite(wells: list[Well]) -> None:
    """
    Test cases designed to exercise stakes-aware routing.
    Includes:
      - Clean signal queries (should MATCH)
      - High-stakes queries with strong signal (should MATCH with high bands)
      - High-stakes queries with weak signal (should NO_ROUTE)
      - Noise queries (should NOISE)
      - Ambiguous queries (should AMBIGUOUS or NO_ROUTE)
      - Critical: queries that look medical but are low-signal (must not hallucinate)
    """

    test_cases = [
        # --- Signal cases: should MATCH ---
        ("What is the Heisenberg uncertainty principle for position and momentum",
         RouteStatus.MATCHED, "physics_equation",
         "Clean physics signal, low stakes → MATCH"),

        ("Calculate Gibbs free energy from enthalpy entropy thermodynamic spontaneous",
         RouteStatus.MATCHED, "thermodynamics",
         "Clean chemistry signal → MATCH"),

        ("Rotate the grid clockwise 90 degrees orientation transform",
         RouteStatus.MATCHED, "rotate_spatial",
         "Clean spatial signal → MATCH"),

        # High-stakes with STRONG signal (many bands)
        ("I have chest pain and difficulty breathing fever symptoms emergency diagnosis treatment",
         RouteStatus.MATCHED, "medical_diagnosis",
         "Strong medical signal — chest/pain/fever/symptoms/diagnosis/treatment → MATCH at high stakes"),

        ("fire explosion hazard toxic evacuation emergency danger immediate injury",
         RouteStatus.MATCHED, "safety_emergency",
         "Strong safety signal — 8 safety keywords → MATCH at high stakes"),

        # --- Stakes rejection: looks relevant but insufficient bands ---
        ("I have a pain",
         RouteStatus.NO_ROUTE, None,
         "Medical domain but 1 keyword — insufficient bands for high-stakes well"),

        ("contract rights",
         RouteStatus.NO_ROUTE, None,
         "Legal domain, 2 keywords — below bands_required=5 for legal well"),

        ("my investment",
         RouteStatus.NO_ROUTE, None,
         "Finance domain, 1 keyword — below bands_required=3"),

        ("there was an emergency",
         RouteStatus.NO_ROUTE, None,
         "Safety domain, 1 keyword — below bands_required=6"),

        # --- Noise cases: hyperbolic register ---
        ("This is absolutely the most incredible amazing revolutionary breakthrough",
         RouteStatus.NOISE, None,
         "Hyperbolic pressure above threshold → NOISE"),

        ("The best totally perfect epic legendary solution ever",
         RouteStatus.NOISE, None,
         "Pure hyperbolic, no domain content → NOISE"),

        # --- Edge: high-signal noise mix ---
        ("The absolutely incredible Heisenberg uncertainty principle is mind-blowing genius",
         RouteStatus.NOISE, None,
         "Physics content but hyperbolic pressure dominates → NOISE"),
    ]

    print("=" * 72)
    print("  RC13 STAKES-AWARE ROUTING — TEST SUITE")
    print("=" * 72)
    print(f"  Wells: {len(wells)} | Test cases: {len(test_cases)}")
    print(f"  Stakes range: {min(w.stakes.risk_weight for w in wells):.2f} — "
          f"{max(w.stakes.risk_weight for w in wells):.2f}")
    print()

    # Print well stakes table
    print(f"  {'WELL':<25} {'DOMAIN':<12} {'RISK':<6} {'BANDS REQ':<10} {'CONF FLOOR'}")
    print("  " + "-" * 62)
    for w in wells:
        print(f"  {w.well_id:<25} {w.domain:<12} "
              f"{w.stakes.risk_weight:<6.2f} {w.stakes.bands_required:<10} "
              f"{w.stakes.confidence_floor:.2f}")
    print()

    passed = 0
    failed = 0
    results = []

    for query, expected_status, expected_well, description in test_cases:
        result = route(query, wells)
        status_match = result["status"] == expected_status
        well_match   = result["matched_well"] == expected_well

        ok = status_match and well_match
        passed += ok
        failed += not ok

        icon = "✓" if ok else "✗"
        results.append((ok, query, result, expected_status, expected_well, description))

    # Print results
    for ok, query, result, exp_status, exp_well, description in results:
        icon = "✓" if ok else "✗"
        status_str = result["status"].value
        well_str   = result["matched_well"] or "—"
        score_str  = f"score={result['score']:.3f}" if result["score"] else ""
        print(f"  [{icon}] {status_str:<10} well={well_str:<25} {score_str}")
        if not ok:
            print(f"      EXPECTED: {exp_status.value} / {exp_well or '—'}")
            print(f"      REASON:   {result['reason']}")
        else:
            print(f"      {description}")
        print()

    print("=" * 72)
    print(f"  RESULT: {passed}/{passed+failed} passed")

    # Stakes summary
    print()
    print("  STAKES CALIBRATION SUMMARY:")
    print(f"  {'WELL':<25} {'RISK':<6} {'BANDS REQ':<10} {'EFFECTIVE THRESHOLD'}")
    print("  " + "-" * 56)
    for w in wells:
        print(f"  {w.well_id:<25} {w.stakes.risk_weight:<6.2f} "
              f"{w.stakes.bands_required:<10} {w.stakes.confidence_floor:.2f}")

    print()
    print("  KEY: risk_weight = (fp_cost + fn_cost) × (1 − reversibility)")
    print("       bands_required = 2 + floor(risk_weight × 3)")
    print("       confidence_floor = 0.65 if risk > 0.5 else 0.40")
    print("=" * 72)

    return passed, failed


# ============================================================
# DEMONSTRATION: stakes threshold scaling
# ============================================================

def demonstrate_stakes_scaling():
    """
    Show how the same query routes differently as stakes change.
    The query has moderate signal — just above low-stakes threshold,
    just below high-stakes threshold.
    """
    print()
    print("=" * 72)
    print("  DEMONSTRATION: SAME SIGNAL, DIFFERENT STAKES")
    print("  Query: 'chest pain symptoms'  (2 medical keywords)")
    print("=" * 72)

    query = "chest pain symptoms"

    stake_levels = [
        ("casual",   StakeVector(fp_cost=0.1, fn_cost=0.1, reversibility=1.0)),
        ("moderate", StakeVector(fp_cost=0.3, fn_cost=0.4, reversibility=0.6)),
        ("serious",  StakeVector(fp_cost=0.6, fn_cost=0.7, reversibility=0.3)),
        ("medical",  StakeVector(fp_cost=0.8, fn_cost=0.9, reversibility=0.1)),
    ]

    for label, stakes in stake_levels:
        test_well = Well(
            "test_medical",
            ["chest", "pain", "symptoms", "fever", "diagnosis",
             "treatment", "medication", "disease", "condition"],
            "Consult medical professional.",
            domain="medical",
            stakes=stakes
        )
        result = route(query, [test_well])
        print(f"  {label:<10} risk={stakes.risk_weight:.2f}  "
              f"bands_req={stakes.bands_required}  "
              f"→ {result['status'].value}  "
              f"({result.get('reason', '')})")

    print()
    print("  The signal didn't change. The stakes did.")
    print("  RC13 routes the same words to NO_ROUTE as risk increases.")
    print("=" * 72)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    wells = build_test_wells()
    passed, failed = run_test_suite(wells)
    demonstrate_stakes_scaling()

    print()
    if failed == 0:
        print("  All tests passed. RC13 stakes-aware routing operational.")
    else:
        print(f"  {failed} test(s) failed. Review above.")
