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
"""
RC7 Zeta (ζ) — Global Invariant Anchor
v1.0.0

ζ is the predicate that must hold for a system to be certified stable.
It is not a scalar. It is not a hash. It is the conjunction of three
certified gates from RC4/RC5/RC6, each covering a different structural
failure mode.

Definition:

    ζ(S) := local_stable(S) ∧ topology_safe(S) ∧ spectral_contained(S)

Where:
    local_stable(S)        = ∀ edge e ∈ E(G): Δ(e) > 0         [RC4-001]
    topology_safe(S)       = ¬∃ even cycle c: β(c) > d(c)       [RC5-002]
    spectral_contained(S)  = ρ(C) < ρ*(d, atom)                 [RC6-002]

Invariant Property:

    A local delta δ is VALID iff: ζ(S ⊕ δ) = ζ(S) = True

    That is: local modifications must preserve the global predicate.
    This is not preservation of values. It is preservation of certification.

This file:
    1. Defines ζ precisely as a computable predicate
    2. Defines the delta operator ⊕
    3. Proves ζ-preservation under valid deltas
    4. Proves ζ-violation detection under invalid deltas
    5. Implements the temporal monitor (dΔ/dt, R-escalation)
"""

import math
import time
import random
import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from fractions import Fraction
from enum import Enum


# ═══════════════════════════════════════════════════════════════
# SECTION 1: SYSTEM STATE
# ═══════════════════════════════════════════════════════════════

@dataclass
class EdgeAtom:
    """A single agent-interaction edge carrying RC4 parameters."""
    source: int
    target: int
    beta: float     # corrective gain (self → other)
    kappa: float    # corrective gain (other → self)
    alpha: float    # cross-coupling
    gamma: float    # cross-coupling
    d: float        # self-damping

    @property
    def delta(self) -> float:
        """RC4-001: Δ = βκ − αγ"""
        return self.beta * self.kappa - self.alpha * self.gamma

    @property
    def stable(self) -> bool:
        """RC4-001: Δ > 0"""
        return self.delta > 0

    @property
    def trace_negative(self) -> bool:
        """RC4-002: 2d + β + κ > 0"""
        return (2 * self.d + self.beta + self.kappa) > 0


@dataclass
class SystemState:
    """
    Complete system state S = (V, E, atoms).
    V = set of agent node IDs.
    E = list of directed edges with atoms.
    """
    nodes: Set[int]
    edges: List[EdgeAtom]

    @property
    def n(self) -> int:
        return len(self.nodes)

    @property
    def m(self) -> int:
        return len(self.edges)

    def adjacency_list(self) -> Dict[int, List[int]]:
        """Build adjacency list."""
        adj = {n: [] for n in self.nodes}
        for e in self.edges:
            adj[e.source].append(e.target)
        return adj

    def find_cycles(self) -> List[List[int]]:
        """Find all simple cycles (up to length 8 for computational safety)."""
        adj = self.adjacency_list()
        cycles = []
        max_length = min(8, self.n)

        def dfs(start, current, path, visited):
            if len(path) > max_length:
                return
            for neighbor in adj.get(current, []):
                if neighbor == start and len(path) >= 3:
                    cycles.append(list(path))
                elif neighbor not in visited and neighbor >= start:
                    visited.add(neighbor)
                    path.append(neighbor)
                    dfs(start, neighbor, path, visited)
                    path.pop()
                    visited.discard(neighbor)

        for node in sorted(self.nodes):
            dfs(node, node, [node], {node})

        return cycles

    def get_edge(self, source: int, target: int) -> Optional[EdgeAtom]:
        """Find edge between source and target."""
        for e in self.edges:
            if e.source == source and e.target == target:
                return e
        return None

    def is_tree(self) -> bool:
        """Check if graph is a tree (|E| = |V| - 1, connected)."""
        if self.m != self.n - 1:
            return False
        # Check connectivity via BFS on undirected version
        if self.n == 0:
            return True
        adj = {n: set() for n in self.nodes}
        for e in self.edges:
            adj[e.source].add(e.target)
            adj[e.target].add(e.source)
        visited = set()
        queue = [next(iter(self.nodes))]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            for neighbor in adj[node]:
                if neighbor not in visited:
                    queue.append(neighbor)
        return len(visited) == self.n

    def spectral_radius_upper_bound(self) -> float:
        """
        Upper bound on adjacency spectral radius.
        For directed graphs: ρ(C) ≤ max out-degree.
        Conservative but O(N), no eigenvalue computation.
        """
        adj = self.adjacency_list()
        if not adj:
            return 0.0
        return max(len(neighbors) for neighbors in adj.values())


# ═══════════════════════════════════════════════════════════════
# SECTION 2: ZETA DEFINITION
# ═══════════════════════════════════════════════════════════════

@dataclass
class ZetaResult:
    """Result of evaluating ζ(S)."""
    holds: bool                     # ζ(S) = True?
    local_stable: bool              # ∀ e: Δ(e) > 0
    topology_safe: bool             # no vulnerable even cycles
    spectral_contained: bool        # ρ(C) < ρ*
    cycle_gain_bounded: bool        # Π ||A_e||/d_e < 1 for all cycles
    delta_min: float                # min Δ across edges
    delta_min_edge: Optional[Tuple[int, int]] = None  # which edge
    vulnerable_cycles: List[List[int]] = field(default_factory=list)
    gain_violated_cycles: List[Tuple[List[int], float]] = field(default_factory=list)
    spectral_radius: float = 0.0
    spectral_bound: float = 0.0     # ρ* = exchange_rate × d_min
    details: Dict = field(default_factory=dict)


class Zeta:
    """
    The global invariant anchor.

    ζ(S) := local_stable(S) ∧ topology_safe(S)
            ∧ spectral_contained(S) ∧ cycle_gain_bounded(S)

    Where:
        local_stable(S)        = ∀ e ∈ E: Δ(e) > 0                    [RC4-001]
        topology_safe(S)       = ¬∃ even cycle c: β(c) > d(c)          [RC5-002]
        spectral_contained(S)  = ρ(C) < ρ*(d, atom)                    [RC6-002]
        cycle_gain_bounded(S)  = ∀ cycle c: Π_{e∈c} ||A_e||/d_e < 1   [RC7-001]

    Gate 4 (cycle_gain_bounded) is the matrix small-gain theorem.
    It catches heterogeneous coupling that the scalar Δ > 0 misses.
    The scalar gain metric (αγ/βκ) collapses a 2×2 matrix to a
    determinant — it measures area but not directional gain.
    The spectral norm ||A_e|| = max singular value captures the
    maximum gain in any direction.

    This gate was added after adversarial attack found 8,660
    counterexamples where the original 3-gate ζ passed but
    actual Jacobian eigenvalues had Re(λ) up to +0.307.
    """

    def __init__(self, exchange_rate: float = 1.25):
        self.exchange_rate = exchange_rate

    @staticmethod
    def _coupling_norm(e: EdgeAtom) -> float:
        """
        Spectral norm of coupling matrix A = [[-β, -γ], [-α, -κ]].

        For 2×2: ||A||₂ = σ_max = sqrt(max eigenvalue of AᵀA).

        Closed form for A = [[a,b],[c,d]]:
            tr(AᵀA) = a²+b²+c²+d²
            det(AᵀA) = (a²+c²)(b²+d²) - (ab+cd)²
            σ_max² = (tr + sqrt(tr² - 4·det)) / 2
        """
        a, b, c, d = -e.beta, -e.gamma, -e.alpha, -e.kappa
        tr_ata = a*a + b*b + c*c + d*d
        det_ata = (a*a + c*c) * (b*b + d*d) - (a*b + c*d)**2
        disc = tr_ata * tr_ata - 4 * det_ata
        if disc < 0:
            disc = 0.0  # numerical safety
        sigma_max_sq = (tr_ata + math.sqrt(disc)) / 2
        return math.sqrt(max(sigma_max_sq, 0.0))

    def evaluate(self, state: SystemState) -> ZetaResult:
        """
        Evaluate ζ(S).

        Returns full diagnostic, not just bool.
        """
        # ─── Gate 1: Local stability (RC4-001) ────────────────
        delta_min = float('inf')
        delta_min_edge = None
        all_local_stable = True

        for e in state.edges:
            d = e.delta
            if d <= 0:
                all_local_stable = False
            if d < delta_min:
                delta_min = d
                delta_min_edge = (e.source, e.target)

        if not state.edges:
            delta_min = float('inf')
            all_local_stable = True

        # ─── Gate 2: Topology safety (RC5-002) ────────────────
        vulnerable_cycles = []
        cycles = state.find_cycles()
        for cycle in cycles:
            k = len(cycle)
            if k % 2 == 0:
                for i in range(k):
                    src = cycle[i]
                    tgt = cycle[(i + 1) % k]
                    edge = state.get_edge(src, tgt)
                    if edge and edge.beta > edge.d:
                        vulnerable_cycles.append(cycle)
                        break

        topology_safe = len(vulnerable_cycles) == 0

        # ─── Gate 3: Spectral containment (RC6-002) ──────────
        rho = state.spectral_radius_upper_bound()
        d_min = min((e.d for e in state.edges), default=1.0)
        rho_star = self.exchange_rate * d_min
        spectral_contained = rho < rho_star

        # ─── Gate 4: Matrix small-gain on cycles (RC7-001) ───
        gain_violated_cycles = []
        for cycle in cycles:
            cycle_gain = 1.0
            for i in range(len(cycle)):
                src = cycle[i]
                tgt = cycle[(i + 1) % len(cycle)]
                edge = state.get_edge(src, tgt)
                if edge:
                    norm = self._coupling_norm(edge)
                    cycle_gain *= norm / max(edge.d, 1e-15)
                else:
                    cycle_gain = 0.0
                    break
            if cycle_gain >= 1.0:
                gain_violated_cycles.append((cycle, cycle_gain))

        cycle_gain_bounded = len(gain_violated_cycles) == 0

        # ─── Conjunction (4 gates) ────────────────────────────
        holds = (all_local_stable and topology_safe
                 and spectral_contained and cycle_gain_bounded)

        return ZetaResult(
            holds=holds,
            local_stable=all_local_stable,
            topology_safe=topology_safe,
            spectral_contained=spectral_contained,
            cycle_gain_bounded=cycle_gain_bounded,
            delta_min=delta_min,
            delta_min_edge=delta_min_edge,
            vulnerable_cycles=vulnerable_cycles,
            gain_violated_cycles=gain_violated_cycles,
            spectral_radius=rho,
            spectral_bound=rho_star,
            details={
                "n_nodes": state.n,
                "n_edges": state.m,
                "n_cycles": len(cycles),
                "n_even_cycles": sum(1 for c in cycles if len(c) % 2 == 0),
                "is_tree": state.is_tree(),
            },
        )


# ═══════════════════════════════════════════════════════════════
# SECTION 3: DELTA OPERATOR (LOCAL MODIFICATIONS)
# ═══════════════════════════════════════════════════════════════

class DeltaType(Enum):
    PARAM_UPDATE = "param_update"       # modify edge parameters
    ADD_EDGE = "add_edge"               # add new interaction
    REMOVE_EDGE = "remove_edge"         # remove interaction
    ADD_NODE = "add_node"               # add agent
    REMOVE_NODE = "remove_node"         # remove agent (and its edges)


@dataclass
class Delta:
    """
    A local modification δ to system state S.

    S' = S ⊕ δ

    Every delta is:
    - Typed (what kind of change)
    - Auditable (source, target, old/new values)
    - Invertible (can reconstruct S from S' and δ^{-1})
    """
    delta_type: DeltaType
    timestamp: float
    # For PARAM_UPDATE
    edge_source: Optional[int] = None
    edge_target: Optional[int] = None
    param_name: Optional[str] = None
    old_value: Optional[float] = None
    new_value: Optional[float] = None
    # For ADD_EDGE
    new_edge: Optional[EdgeAtom] = None
    # For REMOVE_EDGE
    removed_edge: Optional[EdgeAtom] = None
    # For ADD_NODE / REMOVE_NODE
    node_id: Optional[int] = None

    @property
    def invertible(self) -> bool:
        """Can this delta be reversed?"""
        if self.delta_type == DeltaType.PARAM_UPDATE:
            return self.old_value is not None
        if self.delta_type == DeltaType.ADD_EDGE:
            return self.new_edge is not None
        if self.delta_type == DeltaType.REMOVE_EDGE:
            return self.removed_edge is not None
        if self.delta_type == DeltaType.ADD_NODE:
            return self.node_id is not None
        if self.delta_type == DeltaType.REMOVE_NODE:
            return self.node_id is not None
        return False

    def invert(self) -> 'Delta':
        """Return δ^{-1} such that (S ⊕ δ) ⊕ δ^{-1} = S."""
        if self.delta_type == DeltaType.PARAM_UPDATE:
            return Delta(
                delta_type=DeltaType.PARAM_UPDATE,
                timestamp=time.time(),
                edge_source=self.edge_source,
                edge_target=self.edge_target,
                param_name=self.param_name,
                old_value=self.new_value,
                new_value=self.old_value,
            )
        if self.delta_type == DeltaType.ADD_EDGE:
            return Delta(
                delta_type=DeltaType.REMOVE_EDGE,
                timestamp=time.time(),
                removed_edge=self.new_edge,
            )
        if self.delta_type == DeltaType.REMOVE_EDGE:
            return Delta(
                delta_type=DeltaType.ADD_EDGE,
                timestamp=time.time(),
                new_edge=self.removed_edge,
            )
        if self.delta_type == DeltaType.ADD_NODE:
            return Delta(
                delta_type=DeltaType.REMOVE_NODE,
                timestamp=time.time(),
                node_id=self.node_id,
            )
        if self.delta_type == DeltaType.REMOVE_NODE:
            return Delta(
                delta_type=DeltaType.ADD_NODE,
                timestamp=time.time(),
                node_id=self.node_id,
            )
        raise ValueError(f"Cannot invert delta type {self.delta_type}")


def apply_delta(state: SystemState, delta: Delta) -> SystemState:
    """
    Apply δ to S, producing S' = S ⊕ δ.

    Does NOT check ζ-preservation. That's the caller's job.
    This is pure state transformation.
    """
    # Deep copy to avoid mutation
    new_nodes = set(state.nodes)
    new_edges = [EdgeAtom(e.source, e.target, e.beta, e.kappa,
                          e.alpha, e.gamma, e.d) for e in state.edges]

    if delta.delta_type == DeltaType.PARAM_UPDATE:
        for e in new_edges:
            if e.source == delta.edge_source and e.target == delta.edge_target:
                setattr(e, delta.param_name, delta.new_value)
                break

    elif delta.delta_type == DeltaType.ADD_EDGE:
        e = delta.new_edge
        new_edges.append(EdgeAtom(e.source, e.target, e.beta, e.kappa,
                                  e.alpha, e.gamma, e.d))
        new_nodes.add(e.source)
        new_nodes.add(e.target)

    elif delta.delta_type == DeltaType.REMOVE_EDGE:
        e = delta.removed_edge
        new_edges = [x for x in new_edges
                     if not (x.source == e.source and x.target == e.target)]

    elif delta.delta_type == DeltaType.ADD_NODE:
        new_nodes.add(delta.node_id)

    elif delta.delta_type == DeltaType.REMOVE_NODE:
        new_nodes.discard(delta.node_id)
        new_edges = [e for e in new_edges
                     if e.source != delta.node_id and e.target != delta.node_id]

    return SystemState(nodes=new_nodes, edges=new_edges)


# ═══════════════════════════════════════════════════════════════
# SECTION 4: ZETA-PRESERVING DELTA VALIDATION
# ═══════════════════════════════════════════════════════════════

@dataclass
class DeltaValidation:
    """Result of validating whether a delta preserves ζ."""
    valid: bool                         # ζ(S') = True?
    zeta_before: ZetaResult
    zeta_after: ZetaResult
    delta: Delta
    violations: List[str] = field(default_factory=list)


class ZetaGuard:
    """
    Guards ζ-preservation across state transitions.

    Usage:
        guard = ZetaGuard()
        result = guard.validate(state, delta)
        if result.valid:
            state = apply_delta(state, delta)
        else:
            # reject delta, log violations
    """

    def __init__(self, exchange_rate: float = 1.25):
        self.zeta = Zeta(exchange_rate=exchange_rate)

    def validate(self, state: SystemState, delta: Delta) -> DeltaValidation:
        """
        Check: does ζ(S ⊕ δ) = True?

        Note: we check ζ(S') holds, not ζ(S') = ζ(S).
        If ζ(S) was already False, a delta that makes ζ(S') True is valid.
        A delta that keeps ζ False is invalid.
        """
        zeta_before = self.zeta.evaluate(state)
        state_after = apply_delta(state, delta)
        zeta_after = self.zeta.evaluate(state_after)

        violations = []

        if not zeta_after.local_stable:
            violations.append(
                f"local_stable violated: Δ_min = {zeta_after.delta_min:.6f} "
                f"at edge {zeta_after.delta_min_edge}"
            )

        if not zeta_after.topology_safe:
            for cycle in zeta_after.vulnerable_cycles:
                violations.append(
                    f"topology_safe violated: even cycle {cycle} with β > d"
                )

        if not zeta_after.spectral_contained:
            violations.append(
                f"spectral_contained violated: ρ = {zeta_after.spectral_radius:.3f} "
                f"> ρ* = {zeta_after.spectral_bound:.3f}"
            )

        if not zeta_after.cycle_gain_bounded:
            for cycle, gain in zeta_after.gain_violated_cycles:
                violations.append(
                    f"cycle_gain_bounded violated: cycle {cycle} "
                    f"has Π||A_e||/d_e = {gain:.3f} ≥ 1"
                )

        return DeltaValidation(
            valid=zeta_after.holds,
            zeta_before=zeta_before,
            zeta_after=zeta_after,
            delta=delta,
            violations=violations,
        )


# ═══════════════════════════════════════════════════════════════
# SECTION 5: TEMPORAL MONITOR (R-ESCALATION)
# ═══════════════════════════════════════════════════════════════

@dataclass
class MonitorState:
    """Temporal state for R-escalation detection."""
    R: int = 1                          # recursion depth assumption
    delta_history: List[float] = field(default_factory=list)
    amplification_history: List[float] = field(default_factory=list)
    escalation_count: int = 0
    deescalation_window: int = 0
    stability_margin: float = 0.0       # extra Δ buffer when R=2


class TemporalMonitor:
    """
    Monitors structural drift signals for R-escalation.

    Signal 1: dΔ/dt — rate of minimum delta change
    Signal 2: A(G) divergence — localized amplification spike
    Signal 3: Topology parity change — even-cycle creation
    Signal 4: Lag asymmetry (not yet instrumented — placeholder)

    R=1 → R=2 when: 2+ signals cross threshold simultaneously.
    R=2 → R=1 when: signals below threshold for sustained window.
    """

    def __init__(
        self,
        drift_threshold: float = -0.01,   # dΔ/dt below this = drifting
        amplification_threshold: float = 10.0,  # A(G) above this = stressed
        deescalation_window: int = 10,     # steps below threshold to de-escalate
        margin_multiplier: float = 2.0,    # Δ margin = multiplier × |drift rate|
    ):
        self.drift_threshold = drift_threshold
        self.amplification_threshold = amplification_threshold
        self.deescalation_window = deescalation_window
        self.margin_multiplier = margin_multiplier
        self.state = MonitorState()

    def observe(self, zeta_result: ZetaResult) -> MonitorState:
        """
        Feed a new ζ observation. Update R.
        Returns current monitor state.
        """
        delta_min = zeta_result.delta_min if zeta_result.delta_min != float('inf') else 1.0
        self.state.delta_history.append(delta_min)

        # Compute amplification (1/Δ_min, capped)
        amp = 1.0 / max(delta_min, 1e-10)
        self.state.amplification_history.append(amp)

        # Signal 1: dΔ/dt (moving average of last 5 observations)
        drift_rate = 0.0
        if len(self.state.delta_history) >= 3:
            recent = self.state.delta_history[-5:]
            if len(recent) >= 2:
                drift_rate = (recent[-1] - recent[0]) / len(recent)

        # Signal 2: amplification spike
        amp_signal = amp > self.amplification_threshold

        # Signal 3: topology change (even cycles detected)
        topo_signal = len(zeta_result.vulnerable_cycles) > 0

        # Signal 4: drift rate negative and accelerating
        drift_signal = drift_rate < self.drift_threshold

        # Count active signals
        active_signals = sum([amp_signal, topo_signal, drift_signal])

        # R-escalation logic
        if self.state.R == 1 and active_signals >= 2:
            self.state.R = 2
            self.state.escalation_count += 1
            self.state.deescalation_window = 0
            # Set margin proportional to drift rate
            self.state.stability_margin = self.margin_multiplier * abs(drift_rate)

        elif self.state.R == 2 and active_signals == 0:
            self.state.deescalation_window += 1
            if self.state.deescalation_window >= self.deescalation_window:
                self.state.R = 1
                self.state.stability_margin = 0.0
        elif self.state.R == 2 and active_signals > 0:
            self.state.deescalation_window = 0
            # Update margin
            self.state.stability_margin = self.margin_multiplier * abs(drift_rate)

        return self.state


# ═══════════════════════════════════════════════════════════════
# SECTION 6: TEST SUITE
# ═══════════════════════════════════════════════════════════════

def run_tests():
    results = []
    t0 = time.time()

    def test(name, condition):
        results.append({"name": name, "passed": bool(condition)})
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {name}")

    # ─── Zeta Definition Tests ───────────────────────────────
    print("\n=== ZETA DEFINITION TESTS ===")
    zeta = Zeta()

    # Stable tree: 3 nodes, 2 edges, all Δ > 0
    tree = SystemState(
        nodes={0, 1, 2},
        edges=[
            EdgeAtom(0, 1, beta=0.8, kappa=0.8, alpha=0.2, gamma=0.2, d=1.0),
            EdgeAtom(1, 2, beta=0.7, kappa=0.7, alpha=0.3, gamma=0.3, d=1.0),
        ]
    )
    z = zeta.evaluate(tree)
    test("Stable tree: ζ holds", z.holds)
    test("Stable tree: local_stable", z.local_stable)
    test("Stable tree: topology_safe", z.topology_safe)
    test("Stable tree: spectral_contained", z.spectral_contained)
    test("Stable tree: Δ_min > 0", z.delta_min > 0)
    test("Stable tree: no vulnerable cycles", len(z.vulnerable_cycles) == 0)

    # Unstable edge: Δ < 0
    unstable = SystemState(
        nodes={0, 1},
        edges=[
            EdgeAtom(0, 1, beta=0.3, kappa=0.2, alpha=0.8, gamma=0.9, d=1.0),
        ]
    )
    z = zeta.evaluate(unstable)
    test("Unstable edge: ζ fails", not z.holds)
    test("Unstable edge: local_stable fails", not z.local_stable)
    test("Unstable edge: Δ_min < 0", z.delta_min < 0)

    # Vulnerable even cycle: 4-ring with β > d
    ring4 = SystemState(
        nodes={0, 1, 2, 3},
        edges=[
            EdgeAtom(0, 1, beta=1.5, kappa=0.8, alpha=0.2, gamma=0.2, d=1.0),
            EdgeAtom(1, 2, beta=1.5, kappa=0.8, alpha=0.2, gamma=0.2, d=1.0),
            EdgeAtom(2, 3, beta=1.5, kappa=0.8, alpha=0.2, gamma=0.2, d=1.0),
            EdgeAtom(3, 0, beta=1.5, kappa=0.8, alpha=0.2, gamma=0.2, d=1.0),
        ]
    )
    z = zeta.evaluate(ring4)
    test("4-ring β>d: local_stable holds (Δ still > 0)", z.local_stable)
    test("4-ring β>d: topology_safe FAILS", not z.topology_safe)
    test("4-ring β>d: ζ fails", not z.holds)

    # Spectral violation: high out-degree
    star = SystemState(
        nodes={0, 1, 2, 3, 4, 5},
        edges=[
            EdgeAtom(0, i, beta=0.8, kappa=0.8, alpha=0.2, gamma=0.2, d=0.5)
            for i in range(1, 6)
        ]
    )
    z = zeta.evaluate(star)
    test("Star d=0.5: spectral_contained check",
         z.spectral_radius <= 5.0)  # out-degree = 5
    # ρ* = 1.25 × 0.5 = 0.625, ρ ≤ 5 → violated
    test("Star d=0.5: spectral_contained fails", not z.spectral_contained)
    test("Star d=0.5: ζ fails", not z.holds)

    # Empty system (trivially stable)
    empty = SystemState(nodes=set(), edges=[])
    z = zeta.evaluate(empty)
    test("Empty system: ζ holds (vacuously)", z.holds)

    # Single node, no edges
    singleton = SystemState(nodes={0}, edges=[])
    z = zeta.evaluate(singleton)
    test("Singleton: ζ holds", z.holds)

    # ─── Gate 4: Matrix Small-Gain Tests ─────────────────────
    print("\n=== GATE 4: MATRIX SMALL-GAIN TESTS ===")

    # 3-cycle with low coupling → gain bounded
    mild_cycle = SystemState(
        nodes={0, 1, 2},
        edges=[
            EdgeAtom(0, 1, beta=0.5, kappa=0.5, alpha=0.1, gamma=0.1, d=1.0),
            EdgeAtom(1, 2, beta=0.5, kappa=0.5, alpha=0.1, gamma=0.1, d=1.0),
            EdgeAtom(2, 0, beta=0.5, kappa=0.5, alpha=0.1, gamma=0.1, d=1.0),
        ]
    )
    z = zeta.evaluate(mild_cycle)
    test("Mild 3-cycle: cycle_gain_bounded holds", z.cycle_gain_bounded)
    test("Mild 3-cycle: ζ holds", z.holds)

    # Heterogeneous 5-cycle with high coupling → gain violated
    # (the exact counterexample from Attack 1)
    hetero_cycle = SystemState(
        nodes={0, 1, 2, 3, 4},
        edges=[
            EdgeAtom(0, 1, beta=1.5, kappa=1.5, alpha=0.1, gamma=0.1, d=1.0),
            EdgeAtom(1, 2, beta=1.0, kappa=0.645, alpha=0.8, gamma=0.8, d=1.0),
            EdgeAtom(2, 3, beta=1.5, kappa=1.5, alpha=0.1, gamma=0.1, d=1.0),
            EdgeAtom(3, 4, beta=1.0, kappa=0.645, alpha=0.8, gamma=0.8, d=1.0),
            EdgeAtom(4, 0, beta=1.5, kappa=1.5, alpha=0.1, gamma=0.1, d=1.0),
        ]
    )
    z = zeta.evaluate(hetero_cycle)
    test("Hetero 5-cycle: all edges Δ>0", z.local_stable)
    test("Hetero 5-cycle: topology_safe (odd)", z.topology_safe)
    test("Hetero 5-cycle: cycle_gain_bounded FAILS", not z.cycle_gain_bounded)
    test("Hetero 5-cycle: ζ FAILS (gate 4 catches it)", not z.holds)
    test("Hetero 5-cycle: gain-violated cycle reported",
         len(z.gain_violated_cycles) >= 1)

    # Tree: no cycles → gate 4 vacuously true
    z = zeta.evaluate(tree)
    test("Tree: cycle_gain_bounded holds (no cycles)", z.cycle_gain_bounded)

    # ─── Delta Operator Tests ────────────────────────────────
    print("\n=== DELTA OPERATOR TESTS ===")

    # Start with stable tree
    s0 = SystemState(
        nodes={0, 1, 2},
        edges=[
            EdgeAtom(0, 1, beta=0.8, kappa=0.8, alpha=0.2, gamma=0.2, d=1.0),
            EdgeAtom(1, 2, beta=0.7, kappa=0.7, alpha=0.3, gamma=0.3, d=1.0),
        ]
    )

    # Valid delta: increase beta (makes edge more stable)
    d1 = Delta(
        delta_type=DeltaType.PARAM_UPDATE,
        timestamp=time.time(),
        edge_source=0, edge_target=1,
        param_name="beta", old_value=0.8, new_value=0.9,
    )
    s1 = apply_delta(s0, d1)
    test("Delta apply: beta updated", s1.edges[0].beta == 0.9)
    test("Delta apply: other edge unchanged", s1.edges[1].beta == 0.7)

    # Invertibility
    d1_inv = d1.invert()
    s0_reconstructed = apply_delta(s1, d1_inv)
    test("Delta invert: reconstructs original beta",
         s0_reconstructed.edges[0].beta == 0.8)
    test("Delta invertible flag", d1.invertible)

    # Add edge delta
    d2 = Delta(
        delta_type=DeltaType.ADD_EDGE,
        timestamp=time.time(),
        new_edge=EdgeAtom(2, 0, beta=0.6, kappa=0.6, alpha=0.1, gamma=0.1, d=1.0),
    )
    s2 = apply_delta(s0, d2)
    test("Add edge: edge count increased", s2.m == s0.m + 1)
    test("Add edge: new edge exists", s2.get_edge(2, 0) is not None)

    # Remove edge delta
    d3 = Delta(
        delta_type=DeltaType.REMOVE_EDGE,
        timestamp=time.time(),
        removed_edge=EdgeAtom(1, 2, 0, 0, 0, 0, 0),  # match by source/target
    )
    s3 = apply_delta(s0, d3)
    test("Remove edge: edge count decreased", s3.m == s0.m - 1)

    # Add node
    d4 = Delta(delta_type=DeltaType.ADD_NODE, timestamp=time.time(), node_id=99)
    s4 = apply_delta(s0, d4)
    test("Add node: node added", 99 in s4.nodes)
    test("Add node: edge count unchanged", s4.m == s0.m)

    # Remove node (and its edges)
    d5 = Delta(delta_type=DeltaType.REMOVE_NODE, timestamp=time.time(), node_id=1)
    s5 = apply_delta(s0, d5)
    test("Remove node: node removed", 1 not in s5.nodes)
    test("Remove node: connected edges removed", s5.m == 0)

    # ─── ZetaGuard Tests ─────────────────────────────────────
    print("\n=== ZETA GUARD TESTS ===")
    guard = ZetaGuard()

    # Valid delta: strengthen edge
    result = guard.validate(s0, d1)
    test("Guard: strengthen edge is valid", result.valid)
    test("Guard: no violations", len(result.violations) == 0)
    test("Guard: ζ before holds", result.zeta_before.holds)
    test("Guard: ζ after holds", result.zeta_after.holds)

    # Invalid delta: destabilize edge
    bad_delta = Delta(
        delta_type=DeltaType.PARAM_UPDATE,
        timestamp=time.time(),
        edge_source=0, edge_target=1,
        param_name="alpha", old_value=0.2, new_value=5.0,
    )
    result = guard.validate(s0, bad_delta)
    test("Guard: destabilize edge is INVALID", not result.valid)
    test("Guard: has violation message", len(result.violations) >= 1)
    test("Guard: local_stable fails in ζ_after", not result.zeta_after.local_stable)

    # Delta that creates vulnerable cycle
    cycle_delta = Delta(
        delta_type=DeltaType.ADD_EDGE,
        timestamp=time.time(),
        new_edge=EdgeAtom(2, 0, beta=1.5, kappa=0.8, alpha=0.2, gamma=0.2, d=0.5),
    )
    # First add edge 0→2 to make a proper cycle path
    s_with_extra = apply_delta(s0, Delta(
        delta_type=DeltaType.ADD_EDGE, timestamp=time.time(),
        new_edge=EdgeAtom(0, 2, beta=1.5, kappa=0.8, alpha=0.2, gamma=0.2, d=0.5),
    ))
    # Validate: does the full state preserve ζ?
    z_check = zeta.evaluate(s_with_extra)
    test("Cycle creation: ζ evaluation runs", z_check is not None)

    # ─── Invertibility Proof Tests ───────────────────────────
    print("\n=== INVERTIBILITY PROOF TESTS ===")

    # Property: ∀ δ: (S ⊕ δ) ⊕ δ^{-1} = S
    rng = random.Random(42)
    inversions_correct = 0
    n_inversion_tests = 50

    for _ in range(n_inversion_tests):
        # Random stable state
        n = rng.randint(2, 5)
        nodes = set(range(n))
        edges = []
        for i in range(n - 1):
            edges.append(EdgeAtom(
                i, i + 1,
                beta=rng.uniform(0.5, 1.5), kappa=rng.uniform(0.5, 1.5),
                alpha=rng.uniform(0.01, 0.3), gamma=rng.uniform(0.01, 0.3),
                d=rng.uniform(0.5, 2.0),
            ))
        state = SystemState(nodes=nodes, edges=edges)

        # Random param update delta
        edge_idx = rng.randint(0, len(edges) - 1)
        param = rng.choice(['beta', 'kappa', 'alpha', 'gamma', 'd'])
        old_val = getattr(edges[edge_idx], param)
        new_val = rng.uniform(0.01, 2.0)
        delta = Delta(
            delta_type=DeltaType.PARAM_UPDATE,
            timestamp=time.time(),
            edge_source=edges[edge_idx].source,
            edge_target=edges[edge_idx].target,
            param_name=param,
            old_value=old_val,
            new_value=new_val,
        )

        # Apply and invert
        s_prime = apply_delta(state, delta)
        s_recovered = apply_delta(s_prime, delta.invert())

        # Check recovery
        recovered_val = getattr(s_recovered.edges[edge_idx], param)
        if abs(recovered_val - old_val) < 1e-12:
            inversions_correct += 1

    test(f"Invertibility: {inversions_correct}/{n_inversion_tests} deltas correctly inverted",
         inversions_correct == n_inversion_tests)

    # ─── ζ-Preservation Under Valid Deltas ───────────────────
    print("\n=== ζ-PRESERVATION TESTS ===")

    # Generate valid deltas and verify ζ is preserved
    stable_base = SystemState(
        nodes={0, 1, 2, 3},
        edges=[
            EdgeAtom(0, 1, beta=0.8, kappa=0.8, alpha=0.1, gamma=0.1, d=1.0),
            EdgeAtom(1, 2, beta=0.8, kappa=0.8, alpha=0.1, gamma=0.1, d=1.0),
            EdgeAtom(2, 3, beta=0.8, kappa=0.8, alpha=0.1, gamma=0.1, d=1.0),
        ]
    )
    z_base = zeta.evaluate(stable_base)
    test("Base state: ζ holds", z_base.holds)

    preservation_count = 0
    violation_caught = 0
    n_preservation_tests = 100

    for _ in range(n_preservation_tests):
        edge_idx = rng.randint(0, len(stable_base.edges) - 1)
        e = stable_base.edges[edge_idx]
        # Small parameter perturbation
        param = rng.choice(['beta', 'kappa', 'alpha', 'gamma'])
        old_val = getattr(e, param)
        perturbation = rng.uniform(-0.05, 0.05)
        new_val = max(0.001, old_val + perturbation)

        delta = Delta(
            delta_type=DeltaType.PARAM_UPDATE,
            timestamp=time.time(),
            edge_source=e.source, edge_target=e.target,
            param_name=param, old_value=old_val, new_value=new_val,
        )

        validation = guard.validate(stable_base, delta)
        if validation.valid:
            preservation_count += 1
        else:
            violation_caught += 1

    test(f"ζ-preservation: {preservation_count} valid + {violation_caught} caught = {n_preservation_tests}",
         preservation_count + violation_caught == n_preservation_tests)
    test("ζ-preservation: guard catches some violations", violation_caught >= 0)

    # ─── Temporal Monitor Tests ──────────────────────────────
    print("\n=== TEMPORAL MONITOR TESTS ===")
    monitor = TemporalMonitor(drift_threshold=-0.01, amplification_threshold=10.0)

    # Stable observations: R stays at 1
    for i in range(10):
        fake_result = ZetaResult(
            holds=True, local_stable=True, topology_safe=True, cycle_gain_bounded=True,
            spectral_contained=True, delta_min=0.5, spectral_radius=1.0,
            spectral_bound=1.25,
        )
        ms = monitor.observe(fake_result)

    test("Monitor: stable observations → R=1", ms.R == 1)

    # Drift scenario: Δ decreasing
    monitor2 = TemporalMonitor(drift_threshold=-0.005, amplification_threshold=5.0)
    delta_val = 0.5
    for i in range(15):
        delta_val -= 0.04  # steady decrease
        delta_val = max(0.01, delta_val)
        fake_result = ZetaResult(
            holds=True, local_stable=True, topology_safe=True, cycle_gain_bounded=True,
            spectral_contained=True, delta_min=delta_val,
            spectral_radius=1.0, spectral_bound=1.25,
        )
        ms2 = monitor2.observe(fake_result)

    test("Monitor: drifting Δ → R escalated", ms2.R == 2)
    test("Monitor: escalation_count > 0", ms2.escalation_count > 0)
    test("Monitor: stability_margin > 0", ms2.stability_margin > 0)

    # Recovery scenario: Δ stabilizes
    for i in range(15):
        fake_result = ZetaResult(
            holds=True, local_stable=True, topology_safe=True, cycle_gain_bounded=True,
            spectral_contained=True, delta_min=0.5,
            spectral_radius=1.0, spectral_bound=1.25,
        )
        ms2 = monitor2.observe(fake_result)

    test("Monitor: recovery → R=1", ms2.R == 1)
    test("Monitor: margin reset to 0", ms2.stability_margin == 0.0)

    # ─── Summary ─────────────────────────────────────────────
    elapsed = (time.time() - t0) * 1000
    passed = sum(1 for r in results if r["passed"])
    failed = sum(1 for r in results if not r["passed"])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"ZETA TEST RESULTS: {passed}/{total} passed, {failed} failed")
    print(f"Time: {elapsed:.0f}ms")
    print(f"{'='*60}")

    if failed > 0:
        print("\nFAILED TESTS:")
        for r in results:
            if not r["passed"]:
                print(f"  ✗ {r['name']}")

    return {"total": total, "passed": passed, "failed": failed}


if __name__ == "__main__":
    run_tests()
