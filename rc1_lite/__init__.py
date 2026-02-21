"""
RC1-Lite: Deterministic Constraint Projection Layer for LLM Output Evaluation.

Standalone engine matching the frozen RC1-2026-03-25 paper specification.
7 constraint operators, V/Vmax scoring, structured taxonomy.
Pure Python (stdlib only). No external dependencies. Deterministic.
"""

from .engine import evaluate_output
from .version import VERSION

__all__ = ["evaluate_output", "VERSION"]
