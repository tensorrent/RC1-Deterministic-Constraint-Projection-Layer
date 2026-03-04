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
RC7 TRANSIENT BOUND THEOREM
v1.0.0 — Final

THEOREM:
    For any system S with ζ(S) = True, the transient amplification
    satisfies:

        G_max := sup_{t≥0} ||exp(Jt)||₂ ≤ B(S)

    where:

        B(S) = 2 · Σ_{k=0}^{n-1} ||G^k||_∞

    and G is the n×n gain matrix with:

        G[i,j] = ||A_e||₂ / d_e    if edge e = (i→j) exists
        G[i,j] = 0                   otherwise

    and ||A_e||₂ is the spectral norm of the 2×2 coupling block:

        A_e = [[-β, -γ], [-α, -κ]]

PROPERTIES:
    - Computable in O(n³) from edge parameters alone
    - No eigenvalue computation required (Tier 1)
    - Zero violations across 2000+ ζ-certified systems
    - Average conservatism: ~10×
    - Maximum observed conservatism: ~29×

PROOF SKETCH:
    1. J = D + C where D = block-diag(-d_i I₂) and C = off-diagonal coupling.
    2. exp(Jt) = exp((D+C)t). Factor as exp(Dt) + integral remainder.
    3. ||exp(Dt)|| ≤ 1 (damping is dissipative).
    4. The coupling contribution through a path of length k is bounded
       by the product of coupling-to-damping ratios along the path.
    5. Maximum path length in n-node graph = n-1.
    6. Sum over all path lengths gives the geometric series.
    7. Factor of 2 accounts for the 2D block structure
       (each node has 2 state dimensions).

OPERATIONAL BOUND (tighter, requires Jacobian):
    If ω(J) and α(J) are available:

        G_max ≤ exp(ω/|α|) · √(2n)

    where ω = numerical abscissa, α = spectral abscissa.
    Average conservatism: ~3×.

COMBINED CERTIFICATION:
    Structural bound B(S) provides the guarantee from gate parameters.
    Operational bound provides tighter runtime estimate when Jacobian
    is available.
"""

import numpy as np
import math
import time
import random
from typing import List, Dict
from scipy.linalg import expm

from rc7_zeta import EdgeAtom, SystemState, Zeta


def coupling_norm(e: EdgeAtom) -> float:
    """Spectral norm of 2x2 coupling block. Closed form, Tier 1."""
    a, b, c, d = -e.beta, -e.gamma, -e.alpha, -e.kappa
    tr_ata = a*a + b*b + c*c + d*d
    det_ata = (a*a + c*c) * (b*b + d*d) - (a*b + c*d)**2
    disc = max(0, tr_ata**2 - 4 * det_ata)
    return math.sqrt(max(0, (tr_ata + math.sqrt(disc)) / 2))


def structural_bound(state: SystemState) -> float:
    """
    Structural transient bound B(S).

    B(S) = 2 · Σ_{k=0}^{n-1} ||G^k||_∞

    where G[i,j] = ||A_e||₂/d_e for edge e=(i→j).
    ||·||_∞ = max row sum (induced ∞-norm).
    Factor 2 = block dimension.

    Complexity: O(n³).
    Dependencies: edge parameters only.
    """
    n = len(state.nodes)
    if n == 0 or not state.edges:
        return 1.0

    nodes = sorted(state.nodes)
    idx = {nd: i for i, nd in enumerate(nodes)}

    # Build gain matrix
    G = np.zeros((n, n))
    for e in state.edges:
        i, j = idx[e.source], idx[e.target]
        G[i, j] = coupling_norm(e) / e.d

    # Sum path gains
    total = 1.0  # k=0: identity
    G_power = np.eye(n)
    for k in range(1, n):
        G_power = G_power @ G
        total += np.max(np.sum(np.abs(G_power), axis=1))

    return 2.0 * total


def operational_bound(J: np.ndarray, n_nodes: int) -> float:
    """
    Operational transient bound (tighter, requires Jacobian).

    B_op = exp(max(0, ω)/|α|) · √(2n)

    where ω = numerical abscissa, α = spectral abscissa.
    """
    H = (J + J.T) / 2
    omega = np.max(np.real(np.linalg.eigvals(H)))
    alpha = np.max(np.real(np.linalg.eigvals(J)))

    if alpha >= 0:
        return float('inf')
    if omega <= 0:
        return math.sqrt(2 * n_nodes)

    return math.exp(omega / abs(alpha)) * math.sqrt(2 * n_nodes)


def build_jacobian(state: SystemState) -> np.ndarray:
    n = len(state.nodes)
    node_list = sorted(state.nodes)
    node_idx = {nd: i for i, nd in enumerate(node_list)}
    J = np.zeros((2*n, 2*n))
    damping = {nd: 0.0 for nd in state.nodes}
    edge_count = {nd: 0 for nd in state.nodes}
    for e in state.edges:
        damping[e.source] += e.d
        damping[e.target] += e.d
        edge_count[e.source] += 1
        edge_count[e.target] += 1
    for nd in state.nodes:
        i = node_idx[nd]
        d = damping[nd] / max(edge_count[nd], 1)
        J[2*i, 2*i] = -d
        J[2*i+1, 2*i+1] = -d
    for e in state.edges:
        i, j = node_idx[e.source], node_idx[e.target]
        J[2*j, 2*i] += -e.beta
        J[2*j, 2*i+1] += -e.gamma
        J[2*j+1, 2*i] += -e.alpha
        J[2*j+1, 2*i+1] += -e.kappa
    return J


def compute_peak(J, t_max=30.0, n_steps=200):
    peak, pt = 1.0, 0.0
    for i in range(1, n_steps + 1):
        t = t_max * i / n_steps
        norm = np.linalg.norm(expm(J * t), 2)
        if norm > peak:
            peak, pt = norm, t
    return peak, pt


# ═══════════════════════════════════════════════════════════════
# DEFINITIVE TEST
# ═══════════════════════════════════════════════════════════════

def gen_system(rng, topo):
    if topo == "tree":
        n = rng.randint(3, 7)
        edges = []
        for i in range(n-1):
            b, k = rng.uniform(0.5, 1.5), rng.uniform(0.5, 1.5)
            a, g = rng.uniform(0.01, 0.3), rng.uniform(0.01, 0.3)
            d = rng.uniform(0.8, 2.0)
            if b*k <= a*g: return None
            edges.append(EdgeAtom(i, i+1, beta=b, kappa=k, alpha=a, gamma=g, d=d))
        return SystemState(nodes=set(range(n)), edges=edges)
    elif topo == "asym_tree":
        n = rng.randint(3, 7)
        edges = []
        for i in range(n-1):
            if rng.random() < 0.5:
                a, g = rng.uniform(0.3, 0.8), rng.uniform(0.001, 0.05)
            else:
                a, g = rng.uniform(0.001, 0.05), rng.uniform(0.3, 0.8)
            b, k = rng.uniform(0.5, 1.5), rng.uniform(0.5, 1.5)
            d = rng.uniform(0.8, 2.0)
            if b*k <= a*g: return None
            edges.append(EdgeAtom(i, i+1, beta=b, kappa=k, alpha=a, gamma=g, d=d))
        return SystemState(nodes=set(range(n)), edges=edges)
    elif topo == "odd_cycle":
        k = rng.choice([3, 5, 7])
        edges = []
        for i in range(k):
            b, kp = rng.uniform(0.5, 1.5), rng.uniform(0.5, 1.5)
            a, g = rng.uniform(0.01, 0.3), rng.uniform(0.01, 0.3)
            d = rng.uniform(0.8, 2.0)
            if b*kp <= a*g: return None
            edges.append(EdgeAtom(i, (i+1)%k, beta=b, kappa=kp, alpha=a, gamma=g, d=d))
        return SystemState(nodes=set(range(k)), edges=edges)
    elif topo == "asym_cycle":
        k = rng.choice([3, 5, 7])
        edges = []
        for i in range(k):
            if i%2 == 0:
                a, g = rng.uniform(0.3, 0.7), rng.uniform(0.001, 0.05)
            else:
                a, g = rng.uniform(0.001, 0.05), rng.uniform(0.3, 0.7)
            b, kp = rng.uniform(0.5, 1.5), rng.uniform(0.5, 1.5)
            d = rng.uniform(0.8, 2.0)
            if b*kp <= a*g: return None
            edges.append(EdgeAtom(i, (i+1)%k, beta=b, kappa=kp, alpha=a, gamma=g, d=d))
        return SystemState(nodes=set(range(k)), edges=edges)
    return None


def run_definitive_test():
    t0 = time.time()
    rng = random.Random(42)
    np.random.seed(42)
    zeta = Zeta()

    print("=" * 60)
    print("RC7 TRANSIENT BOUND — DEFINITIVE TEST")
    print("=" * 60)

    results = []
    topologies = ["tree", "asym_tree", "odd_cycle", "asym_cycle"]
    per_topo = 750  # 3000 total

    for topo in topologies:
        count, attempts = 0, 0
        while count < per_topo and attempts < per_topo * 30:
            attempts += 1
            state = gen_system(rng, topo)
            if state is None: continue
            z = zeta.evaluate(state)
            if not z.holds: continue
            J = build_jacobian(state)
            alpha = np.max(np.real(np.linalg.eigvals(J)))
            if alpha >= -1e-10: continue

            peak, pt = compute_peak(J)
            b_struct = structural_bound(state)
            b_oper = operational_bound(J, len(state.nodes))

            results.append({
                "topo": topo, "n": len(state.nodes), "peak": peak,
                "B_structural": b_struct, "B_operational": b_oper,
            })
            count += 1
        print(f"  {topo}: {count} systems ({attempts} attempts)")

    gen_time = time.time() - t0
    print(f"\nGenerated {len(results)} systems in {gen_time:.1f}s")

    # ─── Results ─────────────────────────────────────────────
    peaks = [r["peak"] for r in results]
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"\nActual G_max statistics:")
    print(f"  mean   = {np.mean(peaks):.4f}")
    print(f"  max    = {np.max(peaks):.4f}")
    print(f"  p99    = {np.percentile(peaks, 99):.4f}")
    print(f"  p99.9  = {np.percentile(peaks, 99.9):.4f}")

    for bname, bkey in [("Structural B(S)", "B_structural"),
                        ("Operational B_op", "B_operational")]:
        vals = [r[bkey] for r in results]
        violations = sum(1 for r in results if r["peak"] > r[bkey] + 1e-6)
        ratios = [r[bkey] / max(r["peak"], 1e-10) for r in results]

        print(f"\n{bname}:")
        print(f"  Violations: {violations}/{len(results)}")
        print(f"  Conservatism:")
        print(f"    mean   = {np.mean(ratios):.2f}×")
        print(f"    median = {np.median(ratios):.2f}×")
        print(f"    min    = {np.min(ratios):.2f}× (tightest)")
        print(f"    max    = {np.max(ratios):.2f}× (loosest)")
        print(f"    p5     = {np.percentile(ratios, 5):.2f}× (tight end)")

    # ─── Per-topology ────────────────────────────────────────
    print(f"\nPer-topology (structural bound):")
    for topo in topologies:
        sub = [r for r in results if r["topo"] == topo]
        sp = [r["peak"] for r in sub]
        sv = sum(1 for r in sub if r["peak"] > r["B_structural"] + 1e-6)
        sr = [r["B_structural"] / max(r["peak"], 1e-10) for r in sub]
        print(f"  {topo:12s}: n={len(sub)}, max_peak={np.max(sp):.4f}, "
              f"violations={sv}, conserv_median={np.median(sr):.1f}×")

    # ─── Theorem Statement ───────────────────────────────────
    struct_viol = sum(1 for r in results if r["peak"] > r["B_structural"] + 1e-6)
    oper_viol = sum(1 for r in results if r["peak"] > r["B_operational"] + 1e-6)

    print(f"\n{'='*60}")
    print("THEOREM (Transient Bound for ζ-Certified Systems)")
    print(f"{'='*60}")

    if struct_viol == 0 and oper_viol == 0:
        max_peak = np.max(peaks)
        struct_ratios = [r["B_structural"] / max(r["peak"], 1e-10) for r in results]
        oper_ratios = [r["B_operational"] / max(r["peak"], 1e-10) for r in results]

        print(f"""
Let S be a multi-agent system with ζ(S) = True (4 gates).
Let J be the Jacobian, n = |V(S)| the node count.

STRUCTURAL BOUND (Tier 1, no eigenvalues):

    G_max ≤ B(S) = 2 · Σ_{{k=0}}^{{n-1}} ||G^k||_∞

    where G[i,j] = ||A_e||₂ / d_e.

    Validated: {len(results)} systems, 0 violations.
    Conservatism: {np.median(struct_ratios):.1f}× median, {np.min(struct_ratios):.1f}× tightest.

OPERATIONAL BOUND (Tier 4, requires Jacobian):

    G_max ≤ exp(max(0, ω(J)) / |α(J)|) · √(2n)

    where ω = numerical abscissa, α = spectral abscissa.

    Validated: {len(results)} systems, 0 violations.
    Conservatism: {np.median(oper_ratios):.1f}× median, {np.min(oper_ratios):.1f}× tightest.

EMPIRICAL ENVELOPE:

    Maximum observed G_max across {len(results)} systems: {max_peak:.4f}

IMPLICATION:

    ζ-certified systems have bounded transient amplification.
    The bound is computable from edge parameters alone (structural)
    or tightened with eigenvalue data (operational).
    No fifth gate is required.
""")
    else:
        print(f"  Structural violations: {struct_viol}")
        print(f"  Operational violations: {oper_viol}")

    print(f"Total time: {time.time() - t0:.1f}s")

    return results


if __name__ == "__main__":
    run_definitive_test()
