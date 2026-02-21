"""
Teaching Loop — Möbius Reiteration Engine (Phase 2)

The correction architecture:

    LLM Output (v0)
        ↓
    Validator (deterministic audit)
        ↓
    ┌──────────┬──────────┬──────────┐
    │ PASS     │ WARN     │ FAIL     │
    │ (ship)   │ (log)    │ (correct)│
    └──────────┴──────────┴──────────┘
                               ↓
                    CorrectionVector
                               ↓
                    Structured Rewrite Prompt
                               ↓
                    rewrite_fn (caller-provided)
                               ↓
                    LLM Output (v1)
                               ↓
                    Validator (re-audit)
                               ↓
                         ... max 2 iterations

HARD CONSTRAINTS:
    1. MAX_ITERATIONS = 2 (halting constraint — no negotiation)
    2. Validators are stateless — same input always same output
    3. Feedback is structured — correction vectors, not prose
    4. Expansion forbidden — rewrite must not add new abstractions
    5. Every iteration is logged — full delta trace

The caller provides a `rewrite_fn(text, corrections) -> text`.
This module does NOT invoke any LLM. It orchestrates the loop.

If the caller doesn't provide a rewrite_fn, the loop returns
the rewrite prompt and the caller handles it externally.
"""

import sys
import os
from typing import Callable, Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.schema import Report, Violation, CorrectionVector
from harness.runner import LLMHarness
from harness.teacher.correction import generate_corrections, build_rewrite_prompt


MAX_ITERATIONS = 2  # Halting constraint. Hardcoded. Not configurable.


@dataclass
class IterationRecord:
    """One pass through the loop."""
    iteration: int
    gate: str
    score: float
    violations: List[dict]
    corrections: List[dict]
    rewrite_prompt: str
    text_length: int          # Track if text is expanding (forbidden)

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "gate": self.gate,
            "score": self.score,
            "violation_count": len(self.violations),
            "correction_count": len(self.corrections),
            "text_length": self.text_length,
            "violations": self.violations,
            "corrections": self.corrections,
            "rewrite_prompt": self.rewrite_prompt,
        }


@dataclass
class LoopResult:
    """Full trace of the teaching loop."""
    sample_id: str
    initial_gate: str
    initial_score: float
    final_gate: str
    final_score: float
    iterations_used: int
    halted: bool                          # True if hit MAX_ITERATIONS
    expansion_blocked: bool               # True if rewrite tried to expand
    delta_score: float                    # final - initial
    delta_violations: int                 # final - initial (negative = improvement)
    iterations: List[IterationRecord] = field(default_factory=list)
    final_text: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "sample_id": self.sample_id,
            "initial_gate": self.initial_gate,
            "initial_score": self.initial_score,
            "final_gate": self.final_gate,
            "final_score": self.final_score,
            "iterations_used": self.iterations_used,
            "halted": self.halted,
            "expansion_blocked": self.expansion_blocked,
            "delta_score": round(self.delta_score, 3),
            "delta_violations": self.delta_violations,
            "iterations": [it.to_dict() for it in self.iterations],
            "timestamp": self.timestamp,
        }

    def summary_line(self) -> str:
        arrow = "→"
        return (f"{self.sample_id} | "
                f"{self.initial_gate}({self.initial_score:.2f}) "
                f"{arrow} {self.final_gate}({self.final_score:.2f}) | "
                f"Δ={self.delta_score:+.3f} | "
                f"iters={self.iterations_used} | "
                f"halted={self.halted}")


# Expansion threshold: rewrite must not grow text by more than 20%
# Minimum floor: 500 chars. Short inputs naturally grow during correction.
EXPANSION_LIMIT = 1.20
EXPANSION_FLOOR = 500  # Don't trigger expansion block below this length


def run_teaching_loop(
    text: str,
    harness: LLMHarness,
    rewrite_fn: Optional[Callable[[str, List[CorrectionVector]], str]] = None,
    sample_id: str = "sample_0",
) -> LoopResult:
    """
    Run the Möbius reiteration loop.

    Args:
        text: Original LLM output to validate and correct
        harness: Configured LLMHarness instance
        rewrite_fn: Optional function (text, corrections) -> corrected_text
                    If None, loop runs once and returns rewrite prompt for external handling
        sample_id: Identifier for this sample

    Returns:
        LoopResult with full delta trace

    The loop:
        1. Validate text
        2. If PASS: return immediately
        3. If FAIL/WARN: generate corrections
        4. If rewrite_fn provided: apply correction, re-validate
        5. Repeat up to MAX_ITERATIONS
        6. Halt regardless after MAX_ITERATIONS
    """
    iterations = []
    current_text = text
    initial_length = len(text)
    expansion_blocked = False

    for i in range(MAX_ITERATIONS + 1):  # iteration 0 = initial eval
        report = harness.run(current_text, sample_id=f"{sample_id}_iter{i}")

        record = IterationRecord(
            iteration=i,
            gate=report.gate,
            score=report.overall_score,
            violations=[v.to_dict() for v in report.violations],
            corrections=[c.to_dict() for c in report.corrections],
            rewrite_prompt=report.rewrite_prompt,
            text_length=len(current_text),
        )
        iterations.append(record)

        # PASS → ship it
        if report.gate == "PASS":
            return LoopResult(
                sample_id=sample_id,
                initial_gate=iterations[0].gate,
                initial_score=iterations[0].score,
                final_gate=report.gate,
                final_score=report.overall_score,
                iterations_used=i,
                halted=False,
                expansion_blocked=expansion_blocked,
                delta_score=report.overall_score - iterations[0].score,
                delta_violations=len(report.violations) - len(iterations[0].violations),
                iterations=iterations,
                final_text=current_text,
            )

        # No rewrite function → return with rewrite prompt, caller handles it
        if rewrite_fn is None:
            return LoopResult(
                sample_id=sample_id,
                initial_gate=iterations[0].gate,
                initial_score=iterations[0].score,
                final_gate=report.gate,
                final_score=report.overall_score,
                iterations_used=i,
                halted=False,
                expansion_blocked=False,
                delta_score=0.0,
                delta_violations=0,
                iterations=iterations,
                final_text=current_text,
            )

        # HALTING CONSTRAINT: max iterations reached
        if i >= MAX_ITERATIONS:
            return LoopResult(
                sample_id=sample_id,
                initial_gate=iterations[0].gate,
                initial_score=iterations[0].score,
                final_gate=report.gate,
                final_score=report.overall_score,
                iterations_used=i,
                halted=True,  # HIT THE WALL
                expansion_blocked=expansion_blocked,
                delta_score=report.overall_score - iterations[0].score,
                delta_violations=len(report.violations) - len(iterations[0].violations),
                iterations=iterations,
                final_text=current_text,
            )

        # CORRECTION PASS
        corrections = generate_corrections(report.violations)
        rewritten = rewrite_fn(current_text, corrections)

        # EXPANSION CHECK: forbid scope creep during correction
        # Only applies to texts above floor — short texts naturally resize
        if (initial_length > EXPANSION_FLOOR
                and len(rewritten) > initial_length * EXPANSION_LIMIT):
            expansion_blocked = True
            # Reject the rewrite, keep current text, halt
            return LoopResult(
                sample_id=sample_id,
                initial_gate=iterations[0].gate,
                initial_score=iterations[0].score,
                final_gate=report.gate,
                final_score=report.overall_score,
                iterations_used=i,
                halted=True,
                expansion_blocked=True,
                delta_score=report.overall_score - iterations[0].score,
                delta_violations=len(report.violations) - len(iterations[0].violations),
                iterations=iterations,
                final_text=current_text,
            )

        current_text = rewritten

    # Should never reach here, but safety
    last = iterations[-1]
    return LoopResult(
        sample_id=sample_id,
        initial_gate=iterations[0].gate,
        initial_score=iterations[0].score,
        final_gate=last.gate,
        final_score=last.score,
        iterations_used=len(iterations) - 1,
        halted=True,
        expansion_blocked=expansion_blocked,
        delta_score=last.score - iterations[0].score,
        delta_violations=len(last.violations) - len(iterations[0].violations),
        iterations=iterations,
        final_text=current_text,
    )
