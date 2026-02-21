#!/usr/bin/env python3
"""
RC1 Invariant Validator

Ensures no arithmetic drift across sample texts.
Run as part of CI on every push.
"""

import sys
import os

# Ensure repo root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rc1_lite.engine import evaluate_output

SAMPLE_TEXTS = [
    # Clean technical prose -> should PASS
    "This function computes a parameter under defined conditions.",

    # Self-referential capability -> should trigger SELF
    "This system guarantees perfect safety.",

    # Abstraction escalation + intent -> should trigger ESC/INTENT
    "We deploy intelligence into humanity.",

    # Clean with grounded absolute -> should PASS
    (
        "This function always returns exactly 32 bytes because the SHA3-256 "
        "specification mandates a fixed 256-bit output."
    ),

    # Empty edge case
    "",
]

errors = 0

for i, text in enumerate(SAMPLE_TEXTS):
    result = evaluate_output(text)

    V = result["V"]
    score = result["score"]
    violations = result["violations"]

    # 1. Severity sum must equal V
    severity_sum = sum(v["severity"] for v in violations)
    if V != severity_sum:
        print(f"FAIL sample {i}: V={V} != sum(severity)={severity_sum}")
        errors += 1

    # 2. Score must match formula
    expected_score = round(1 - V / 14, 4)
    if score != expected_score:
        print(f"FAIL sample {i}: score={score} != expected={expected_score}")
        errors += 1

    # 3. Gate must match thresholds
    gate = result["gate"]
    if score >= 0.70:
        expected_gate = "PASS"
    elif score >= 0.50:
        expected_gate = "WARN"
    else:
        expected_gate = "FAIL"

    if gate != expected_gate:
        print(f"FAIL sample {i}: gate={gate} != expected={expected_gate}")
        errors += 1

    # 4. Idempotence
    result2 = evaluate_output(text)
    if result != result2:
        print(f"FAIL sample {i}: idempotence violation")
        errors += 1

    # 5. V_max must be 14
    if result["V_max"] != 14:
        print(f"FAIL sample {i}: V_max={result['V_max']} != 14")
        errors += 1

if errors == 0:
    print(f"All invariants validated across {len(SAMPLE_TEXTS)} samples.")
    sys.exit(0)
else:
    print(f"{errors} invariant failures detected.")
    sys.exit(1)
