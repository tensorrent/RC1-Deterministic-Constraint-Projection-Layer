"""
RC1-Lite Test Suite

Tests all 7 constraint operators independently.
Tests scoring arithmetic.
Tests gate thresholds.
Tests taxonomy aggregation.
Tests full engine integration.
Tests idempotence.

Deterministic. No shared state. No external dependencies.
"""

import sys
import os

# Ensure rc1_lite is importable (repo root = parent of tests/)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rc1_lite.engine import evaluate_output
from rc1_lite.scoring import compute_score, compute_gate, compute_taxonomy, V_MAX
from rc1_lite.version import VERSION
from rc1_lite.constraints.h2_metaphor import h2_metaphor
from rc1_lite.constraints.absolute_claim import absolute_claim
from rc1_lite.constraints.intent_execution import intent_execution
from rc1_lite.constraints.abstraction_escalation import abstraction_escalation
from rc1_lite.constraints.rephrasing_loop import rephrasing_loop
from rc1_lite.constraints.ungrounded_prescriptive import ungrounded_prescriptive
from rc1_lite.constraints.self_reference import self_reference


passed = 0
failed = 0


def check(name, condition, msg=""):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}: {msg}")
        failed += 1


# ═══════════════════════════════════════════
# SCORING ARITHMETIC
# ═══════════════════════════════════════════
print("\n── Scoring ──")

check("v_max_is_14", V_MAX == 14, f"got {V_MAX}")
check("score_v0", compute_score(0) == 1.0, f"got {compute_score(0)}")
check("score_v14", compute_score(14) == 0.0, f"got {compute_score(14)}")
check("score_v7", abs(compute_score(7) - 0.5) < 1e-9, f"got {compute_score(7)}")
check("score_v10", abs(compute_score(10) - (1 - 10/14)) < 1e-9, f"got {compute_score(10)}")
check("gate_pass", compute_gate(0.70) == "PASS", f"got {compute_gate(0.70)}")
check("gate_pass_high", compute_gate(1.0) == "PASS", f"got {compute_gate(1.0)}")
check("gate_warn", compute_gate(0.50) == "WARN", f"got {compute_gate(0.50)}")
check("gate_warn_mid", compute_gate(0.60) == "WARN", f"got {compute_gate(0.60)}")
check("gate_fail", compute_gate(0.49) == "FAIL", f"got {compute_gate(0.49)}")
check("gate_fail_zero", compute_gate(0.0) == "FAIL", f"got {compute_gate(0.0)}")

# Taxonomy aggregation
violations_example = [
    {"type": "H2", "severity": 2},
    {"type": "ABS", "severity": 1},
    {"type": "ABS", "severity": 2},
    {"type": "PRESC", "severity": 1},
]
tax = compute_taxonomy(violations_example)
check("tax_h2", tax["H2"] == 1, f"got {tax['H2']}")
check("tax_abs", tax["ABS"] == 2, f"got {tax['ABS']}")
check("tax_presc", tax["PRESC"] == 1, f"got {tax['PRESC']}")
check("tax_intent_zero", tax["INTENT"] == 0, f"got {tax['INTENT']}")


# ═══════════════════════════════════════════
# H2 — UNDISSOLVED METAPHOR
# ═══════════════════════════════════════════
print("\n── H2 Metaphor ──")

r = h2_metaphor("The function returns 256 bytes at O(1) cost.")
check("h2_clean", r["severity"] == 0, f"sev={r['severity']}")

r = h2_metaphor("The code breathes fire into the void.")
check("h2_undissolved", r["severity"] == 2, f"sev={r['severity']}")

r = h2_metaphor("The system is the heart of the architecture. That is, it means the central dispatch loop.")
check("h2_dissolved", r["severity"] == 0, f"sev={r['severity']}")

r = h2_metaphor("The ghost inhabits the machine, meaning the background daemon process.")
check("h2_dissolved_meaning", r["severity"] == 0, f"sev={r['severity']}")


# ═══════════════════════════════════════════
# ABS — ABSOLUTE CLAIM WITHOUT SCOPE
# ═══════════════════════════════════════════
print("\n── ABS Absolute Claim ──")

r = absolute_claim("The latency is approximately 12ms under normal load.")
check("abs_clean", r["severity"] == 0, f"sev={r['severity']}")

r = absolute_claim("This always works and never fails.")
check("abs_unscoped", r["severity"] == 2, f"sev={r['severity']}")

r = absolute_claim("This always returns 256 bits because the SHA3 spec requires it.")
check("abs_scoped_because", r["severity"] == 0, f"sev={r['severity']}")

r = absolute_claim("Under these conditions, it is guaranteed to converge.")
check("abs_scoped_conditions", r["severity"] == 0, f"sev={r['severity']}")


# ═══════════════════════════════════════════
# INTENT — INTENT WITHOUT MECHANISM
# ═══════════════════════════════════════════
print("\n── INTENT ──")

r = intent_execution("def compute(x): return x * 2")
check("intent_clean_code", r["severity"] == 0, f"sev={r['severity']}")

r = intent_execution("We should build a framework for processing data. The plan is to create a pipeline architecture.")
check("intent_no_mechanism", r["severity"] == 2, f"sev={r['severity']}")

r = intent_execution("We should implement parser in parser.py. Step 1: def parse(input_str): return tokenize(input_str)")
check("intent_with_mechanism", r["severity"] == 0, f"sev={r['severity']}")


# ═══════════════════════════════════════════
# ESC — ABSTRACTION ESCALATION
# ═══════════════════════════════════════════
print("\n── ESC Escalation ──")

r = abstraction_escalation("The function parses tokens. It returns a list of strings.")
check("esc_clean", r["severity"] == 0, f"sev={r['severity']}")

r = abstraction_escalation("The code compiles to binary. This represents the transcendence of consciousness.")
check("esc_unbridged", r["severity"] == 2, f"sev={r['severity']}")

r = abstraction_escalation("The algorithm processes the array. Therefore, this demonstrates the universality of the approach.")
check("esc_bridged", r["severity"] == 0, f"sev={r['severity']}")


# ═══════════════════════════════════════════
# LOOP — REPHRASING LOOP
# ═══════════════════════════════════════════
print("\n── LOOP Rephrasing ──")

r = rephrasing_loop("Step 1: parse input. Step 2: validate output. Step 3: return result.")
check("loop_clean", r["severity"] == 0, f"sev={r['severity']}")

r = rephrasing_loop("The system processes the input data and returns the output result. The system processes the input data and returns the output.")
check("loop_single_rephrase", r["severity"] >= 1, f"sev={r['severity']}")


# ═══════════════════════════════════════════
# PRESC — UNGROUNDED PRESCRIPTIVE
# ═══════════════════════════════════════════
print("\n── PRESC Prescriptive ──")

r = ungrounded_prescriptive("The function accepts two arguments and returns an integer.")
check("presc_clean", r["severity"] == 0, f"sev={r['severity']}")

r = ungrounded_prescriptive("You must always validate inputs.")
check("presc_ungrounded", r["severity"] >= 1, f"sev={r['severity']}")

r = ungrounded_prescriptive("You must validate inputs because RFC 793 requires it per section 3.2.")
check("presc_grounded", r["severity"] == 0, f"sev={r['severity']}")


# ═══════════════════════════════════════════
# SELF — SELF-REFERENTIAL CAPABILITY
# ═══════════════════════════════════════════
print("\n── SELF Reference ──")

r = self_reference("The algorithm uses divide and conquer.")
check("self_clean", r["severity"] == 0, f"sev={r['severity']}")

r = self_reference("I can guarantee perfect results every time.")
check("self_unqualified", r["severity"] >= 1, f"sev={r['severity']}")

r = self_reference("I can process this request, assuming the input is valid.")
check("self_qualified", r["severity"] == 0, f"sev={r['severity']}")


# ═══════════════════════════════════════════
# ENGINE INTEGRATION
# ═══════════════════════════════════════════
print("\n── Engine Integration ──")

# Clean technical prose -> PASS
clean = (
    "The function compute_hash(data) returns a 256-bit SHA3 digest. "
    "If the input exceeds 4096 bytes, it chunks at 1024-byte boundaries. "
    "Benchmarks show approximately 12.5ms average latency."
)
r = evaluate_output(clean)
check("engine_clean_pass", r["gate"] == "PASS",
      f"gate={r['gate']}, V={r['V']}, S={r['score']}")
check("engine_clean_v_matches",
      r["V"] == sum(v["severity"] for v in r["violations"]),
      f"V={r['V']} but severity sum={sum(v['severity'] for v in r['violations'])}")

# Violation-heavy text -> FAIL
bad = (
    "The ghost breathes immortal fire into the dancing void. "
    "This obviously proves everything is certainly perfect forever. "
    "The code compiles to binary. This represents the transcendence of consciousness. "
    "I can guarantee perfect results. You must always do it this way."
)
r = evaluate_output(bad)
check("engine_bad_fail", r["gate"] == "FAIL",
      f"gate={r['gate']}, V={r['V']}, S={r['score']}")
check("engine_bad_v_matches",
      r["V"] == sum(v["severity"] for v in r["violations"]),
      f"V={r['V']} but severity sum={sum(v['severity'] for v in r['violations'])}")

# Arithmetic consistency: S = 1 - V/14
r = evaluate_output(bad)
expected_s = round(1 - r["V"] / 14, 4)
check("engine_arithmetic",
      r["score"] == expected_s,
      f"score={r['score']} but 1 - {r['V']}/14 = {expected_s}")

# Version
check("engine_version", r["version"] == "RC1-2026-03-25",
      f"got {r['version']}")

# V_max
check("engine_vmax", r["V_max"] == 14, f"got {r['V_max']}")


# ═══════════════════════════════════════════
# IDEMPOTENCE
# ═══════════════════════════════════════════
print("\n── Idempotence ──")

text = "The system must handle all edge cases. This always works without fail."
r1 = evaluate_output(text)
r2 = evaluate_output(text)
check("idempotent_score", r1["score"] == r2["score"],
      f"{r1['score']} != {r2['score']}")
check("idempotent_gate", r1["gate"] == r2["gate"],
      f"{r1['gate']} != {r2['gate']}")
check("idempotent_v", r1["V"] == r2["V"],
      f"{r1['V']} != {r2['V']}")
check("idempotent_taxonomy", r1["taxonomy"] == r2["taxonomy"],
      f"{r1['taxonomy']} != {r2['taxonomy']}")


# ═══════════════════════════════════════════
# ARITHMETIC INVARIANT (the hardening core)
# ═══════════════════════════════════════════
print("\n── Arithmetic Invariant ──")

# V must equal sum of listed severities in ALL cases
test_inputs = [
    "Pure technical text with no violations at all.",
    "The function returns 42.",
    "The ghost breathes fire. You must do it. I can guarantee everything.",
    "We should build a framework. The plan is transcendence of consciousness.",
]
for i, text in enumerate(test_inputs):
    r = evaluate_output(text)
    sev_sum = sum(v["severity"] for v in r["violations"])
    check(f"invariant_{i}_v_eq_sum", r["V"] == sev_sum,
          f"V={r['V']} != sum={sev_sum}")
    expected = round(1 - r["V"] / 14, 4)
    check(f"invariant_{i}_s_eq_formula", r["score"] == expected,
          f"S={r['score']} != 1-{r['V']}/14={expected}")


# ═══════════════════════════════════════════
print(f"\n{'='*40}")
print(f"Results: {passed}/{passed + failed} passed")
print(f"{'='*40}")
sys.exit(0 if failed == 0 else 1)
