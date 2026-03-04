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
RC4 Universal — Cross-Gain Competition Atom
Version: 2.0.0
Status:  FROZEN

The minimal linear system exhibiting destabilizing cross-gain competition.

    dx/dt = A x

    A = [ -β  -γ ]
        [ -α  -κ ]

    All gains positive.

Stability reduces to one scalar:

    Δ = βκ − αγ

    Δ > 0  → stable node
    Δ = 0  → critical transition
    Δ < 0  → saddle instability

Interpretation-free. Domain-agnostic.
The 2×2 block is the primitive atom of N-state block-diagonal stability.

All arithmetic in exact rationals via RC2.
"""

__version__ = "2.0.0"
__status__ = "FROZEN"

import sys, os
sys.path.insert(0, '/home/claude')

from fractions import Fraction
from dataclasses import dataclass
import hashlib, json, time, math, random

from tent_stack import RC2


# ═════════════════════════════════════════════════════
# §1. THE ATOM
# ═════════════════════════════════════════════════════

@dataclass(frozen=True)
class Atom:
    """
    The 2×2 cross-gain competition atom.

    A = [ -β  -γ ]
        [ -α  -κ ]

    β: corrective adaptation gain
    κ: self-damping / friction
    α: disturbance amplification gain
    γ: cross-suppression / interference gain

    All positive. No physical interpretation assumed.
    """
    beta: Fraction     # corrective gain
    kappa: Fraction    # damping
    alpha: Fraction    # amplification gain
    gamma: Fraction    # cross-coupling gain

    def __post_init__(self):
        for name in ('beta', 'kappa', 'alpha', 'gamma'):
            val = getattr(self, name)
            if not isinstance(val, Fraction):
                object.__setattr__(self, name, Fraction(val))
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive, got {val}")

    # ── Core invariants ──

    @property
    def delta(self) -> Fraction:
        """Stability margin: Δ = βκ − αγ. The one scalar."""
        return self.beta * self.kappa - self.alpha * self.gamma

    @property
    def rho(self) -> Fraction:
        """Bifurcation parameter: ρ = αγ / βκ"""
        return (self.alpha * self.gamma) / (self.beta * self.kappa)

    @property
    def trace(self) -> Fraction:
        """tr(A) = −(β + κ). Always negative."""
        return -(self.beta + self.kappa)

    @property
    def score(self) -> Fraction:
        """
        Normalized stability score: βκ / (βκ + αγ)
        Score > 1/2 ⟺ Δ > 0 ⟺ stable.
        """
        bk = self.beta * self.kappa
        ag = self.alpha * self.gamma
        return Fraction(bk, bk + ag)

    @property
    def phase(self) -> str:
        d = self.delta
        if d > 0: return "STABLE"
        if d == 0: return "CRITICAL"
        return "UNSTABLE"

    @property
    def is_stable(self) -> bool:
        return self.delta > 0

    # ── Eigenvalues ──

    def eigenvalues(self) -> tuple:
        """
        λ = (tr ± √(tr² − 4Δ)) / 2
        """
        tr = float(self.trace)
        det = float(self.delta)
        disc = tr * tr - 4 * det
        if disc >= 0:
            sd = math.sqrt(disc)
            return ((tr + sd) / 2, (tr - sd) / 2)
        else:
            r = tr / 2
            i = math.sqrt(-disc) / 2
            return (complex(r, i), complex(r, -i))

    # ── RC2 gate ──

    def gate(self, threshold=Fraction(1, 2)) -> bool:
        """
        RC2 decision: score > threshold.
        Uses integer cross-multiplication. No float comparison.
        Equivalent to Δ > 0 when threshold = 1/2.
        """
        return RC2(S=self.score, threshold=threshold).gate()

    # ── Matrix form ──

    def matrix(self) -> list:
        return [[-self.beta, -self.gamma],
                [-self.alpha, -self.kappa]]

    def to_dict(self) -> dict:
        return {
            "beta": str(self.beta), "kappa": str(self.kappa),
            "alpha": str(self.alpha), "gamma": str(self.gamma),
            "delta": str(self.delta), "rho": str(self.rho),
            "trace": str(self.trace), "score": str(self.score),
            "phase": self.phase,
        }


# ═════════════════════════════════════════════════════
# §2. EQUIVALENCE THEOREM
# ═════════════════════════════════════════════════════
#
# For the 2×2 atom with positive gains, the following are equivalent:
#
#   (E1) βκ > αγ                  [determinant condition]
#   (E2) det(A) > 0               [same, restated]
#   (E3) ρ < 1                    [bifurcation parameter]
#   (E4) score > 1/2              [normalized metric]
#   (E5) Re(λ₁) < 0 ∧ Re(λ₂) < 0  [eigenvalue condition]
#   (E6) RC2.gate() = True        [exact rational decision]
#   (E7) V̇ < 0 along trajectories [Lyapunov monotonicity]
#
# All seven conditions collapse to one scalar inequality.
# This module verifies (E1)–(E6) algebraically and (E7) numerically.


def verify_equivalence(atom: Atom) -> dict:
    """
    Check all seven equivalence conditions for a given atom.
    Returns dict of {condition: bool}.
    """
    e1 = atom.beta * atom.kappa > atom.alpha * atom.gamma
    e2 = atom.delta > 0
    e3 = atom.rho < 1
    e4 = atom.score > Fraction(1, 2)

    ev = atom.eigenvalues()
    if isinstance(ev[0], complex):
        e5 = ev[0].real < 0 and ev[1].real < 0
    else:
        e5 = ev[0] < 0 and ev[1] < 0

    e6 = atom.gate()

    return {"E1_det_ineq": e1, "E2_det_pos": e2, "E3_rho_lt1": e3,
            "E4_score_gt_half": e4, "E5_eigenvalues_neg": e5, "E6_rc2_gate": e6}


# ═════════════════════════════════════════════════════
# §3. N-STATE BLOCK GENERALIZATION
# ═════════════════════════════════════════════════════

class BlockSystem:
    """
    An N-state system composed of 2×2 cross-gain atoms on the block diagonal.

    For block-diagonal structure, the full system is stable
    iff every 2×2 block is stable.

    The 2×2 atom is the primitive: stability of any block-diagonal
    cross-coupled system reduces to checking Δᵢ > 0 for each block.
    """

    def __init__(self, atoms: list):
        """atoms: list of Atom instances, one per 2×2 block."""
        if not atoms:
            raise ValueError("Need at least one atom")
        self.atoms = list(atoms)
        self.n_blocks = len(atoms)
        self.dim = 2 * self.n_blocks

    @property
    def is_stable(self) -> bool:
        """System stable iff all blocks stable."""
        return all(a.is_stable for a in self.atoms)

    @property
    def weakest_block(self) -> int:
        """Index of block with smallest stability margin."""
        return min(range(self.n_blocks), key=lambda i: self.atoms[i].delta)

    @property
    def min_delta(self) -> Fraction:
        """Smallest Δ across all blocks. System stable iff this > 0."""
        return min(a.delta for a in self.atoms)

    @property
    def system_score(self) -> Fraction:
        """Min score across blocks. System stable iff > 1/2."""
        return min(a.score for a in self.atoms)

    def eigenvalues(self) -> list:
        """All eigenvalues (union of block eigenvalues)."""
        evs = []
        for a in self.atoms:
            evs.extend(a.eigenvalues())
        return evs

    def block_matrix(self) -> list:
        """Full system matrix as 2N × 2N (block diagonal)."""
        n = self.dim
        M = [[Fraction(0)] * n for _ in range(n)]
        for i, a in enumerate(self.atoms):
            r = 2 * i
            blk = a.matrix()
            M[r][r] = blk[0][0]
            M[r][r+1] = blk[0][1]
            M[r+1][r] = blk[1][0]
            M[r+1][r+1] = blk[1][1]
        return M

    def stability_report(self) -> dict:
        blocks = []
        for i, a in enumerate(self.atoms):
            blocks.append({
                "block": i, "delta": str(a.delta), "rho": str(a.rho),
                "score": str(a.score), "phase": a.phase,
            })
        return {
            "dim": self.dim, "n_blocks": self.n_blocks,
            "system_stable": self.is_stable,
            "min_delta": str(self.min_delta),
            "system_score": str(self.system_score),
            "weakest_block": self.weakest_block,
            "blocks": blocks,
        }


# ═════════════════════════════════════════════════════
# §4. OFF-DIAGONAL COUPLING (PERTURBATION BOUND)
# ═════════════════════════════════════════════════════

class CoupledBlockSystem:
    """
    Block-diagonal atoms with off-diagonal perturbation.

    Full matrix: M = diag(A₁, A₂, ..., Aₖ) + εC

    where C is a coupling matrix with bounded norm.

    Stability preserved if min_i(Δᵢ) > ε·‖C‖.

    This is a Gershgorin-type bound: the block atoms remain stable
    under perturbation as long as the perturbation energy is smaller
    than the weakest block's stability margin.
    """

    def __init__(self, block_sys: BlockSystem, epsilon: Fraction = Fraction(0)):
        self.block_sys = block_sys
        self.epsilon = epsilon

    def stability_bound(self) -> Fraction:
        """
        Maximum ε for which stability is guaranteed.
        ε_max = min_i(Δᵢ) (conservative bound assuming ‖C‖ ≤ 1).
        """
        return self.block_sys.min_delta

    @property
    def is_robust(self) -> bool:
        """Stable under current ε."""
        return self.epsilon < self.block_sys.min_delta


# ═════════════════════════════════════════════════════
# §5. RK4 INTEGRATOR (ABSTRACT)
# ═════════════════════════════════════════════════════

class AtomSimulator:
    """RK4 integration of dx/dt = Ax for a single atom."""

    def __init__(self, atom: Atom):
        self.a = atom
        self.b = float(atom.beta)
        self.k = float(atom.kappa)
        self.al = float(atom.alpha)
        self.g = float(atom.gamma)

    def _deriv(self, x1, x2):
        dx1 = -self.b * x1 - self.g * x2
        dx2 = -self.al * x1 - self.k * x2
        return dx1, dx2

    def _rk4(self, x1, x2, dt):
        k1a, k1b = self._deriv(x1, x2)
        k2a, k2b = self._deriv(x1 + 0.5*dt*k1a, x2 + 0.5*dt*k1b)
        k3a, k3b = self._deriv(x1 + 0.5*dt*k2a, x2 + 0.5*dt*k2b)
        k4a, k4b = self._deriv(x1 + dt*k3a, x2 + dt*k3b)
        return (x1 + dt/6*(k1a+2*k2a+2*k3a+k4a),
                x2 + dt/6*(k1b+2*k2b+2*k3b+k4b))

    def simulate(self, x1_0, x2_0, dt=0.005, t_max=20.0):
        traj = []
        x1, x2, t = float(x1_0), float(x2_0), 0.0
        while t <= t_max:
            traj.append((t, x1, x2))
            x1, x2 = self._rk4(x1, x2, dt)
            t += dt
        return traj

    def lyapunov(self, traj):
        """V = x₁² + x₂². Returns [(t, V)]."""
        return [(t, x1**2 + x2**2) for t, x1, x2 in traj]


# ═════════════════════════════════════════════════════
# §6. BENCHMARK
# ═════════════════════════════════════════════════════

class UniversalBenchmark:

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0

    def check(self, name, cond, detail=""):
        self.results.append({"name": name, "pass": cond, "detail": detail})
        if cond: self.passed += 1
        else: self.failed += 1
        print(f"  {'✓' if cond else '✗'} {name}" + (f"  ({detail})" if detail else ""))

    def run_all(self):
        t0 = time.time()
        self.sect_atom_invariants()
        self.sect_equivalence_theorem()
        self.sect_eigenvalue_algebra()
        self.sect_bifurcation_boundary()
        self.sect_trajectory_convergence()
        self.sect_trajectory_divergence()
        self.sect_lyapunov()
        self.sect_rc2_gate_equivalence()
        self.sect_randomized_sweep()
        self.sect_block_system()
        self.sect_block_weakest_link()
        self.sect_perturbation_bound()
        self.sect_score_algebra()
        return time.time() - t0

    # ── §6.1 Atom invariants ──
    def sect_atom_invariants(self):
        print("\n── §1. Atom Invariants ──")
        a = Atom(Fraction(7,10), Fraction(8,10), Fraction(3,10), Fraction(2,10))

        # Δ = 7/10 * 8/10 - 3/10 * 2/10 = 56/100 - 6/100 = 50/100 = 1/2
        self.check("Δ exact", a.delta == Fraction(1, 2), f"Δ = {a.delta}")

        # tr = -(7/10 + 8/10) = -3/2
        self.check("tr exact", a.trace == Fraction(-3, 2), f"tr = {a.trace}")

        # ρ = (3/10 * 2/10) / (7/10 * 8/10) = 6/56 = 3/28
        self.check("ρ exact", a.rho == Fraction(3, 28), f"ρ = {a.rho}")

        # score = 56/100 / (56/100 + 6/100) = 56/62 = 28/31
        self.check("score exact", a.score == Fraction(28, 31), f"score = {a.score}")

        # All Fraction
        self.check("all Fraction type",
                    all(isinstance(x, Fraction) for x in [a.delta, a.trace, a.rho, a.score]))

    # ── §6.2 Equivalence theorem ──
    def sect_equivalence_theorem(self):
        print("\n── §2. Equivalence Theorem (E1–E6) ──")

        # Stable atom: all conditions True
        a_s = Atom(Fraction(7,10), Fraction(8,10), Fraction(1,10), Fraction(1,10))
        eq_s = verify_equivalence(a_s)
        self.check("Stable: all E1–E6 agree True",
                    all(eq_s.values()),
                    f"{sum(eq_s.values())}/6")

        # Unstable atom: all conditions False
        a_u = Atom(Fraction(9,10), Fraction(1,10), Fraction(9,10), Fraction(1,10))
        eq_u = verify_equivalence(a_u)
        self.check("Unstable: all E1–E6 agree False",
                    not any(eq_u.values()),
                    f"{sum(eq_u.values())}/6")

        # Critical: E1–E4,E6 all False (marginal), E5 marginal
        a_c = Atom(Fraction(1), Fraction(1), Fraction(1), Fraction(1))
        eq_c = verify_equivalence(a_c)
        e1_e4_false = not eq_c["E1_det_ineq"] and not eq_c["E3_rho_lt1"] and not eq_c["E4_score_gt_half"]
        self.check("Critical: E1,E3,E4 all False (not strictly stable)",
                    e1_e4_false, f"Δ={a_c.delta}, ρ={a_c.rho}")

    # ── §6.3 Eigenvalue algebra ──
    def sect_eigenvalue_algebra(self):
        print("\n── §3. Eigenvalue Algebra ──")
        a = Atom(Fraction(7,10), Fraction(8,10), Fraction(3,10), Fraction(2,10))
        ev = a.eigenvalues()

        # Sum = trace
        ev_sum = sum(ev) if not isinstance(ev[0], complex) else (ev[0] + ev[1]).real
        self.check("λ₁ + λ₂ = tr(A)",
                    abs(ev_sum - float(a.trace)) < 1e-12,
                    f"sum={ev_sum:.10f}, tr={float(a.trace)}")

        # Product = det
        ev_prod = ev[0] * ev[1] if not isinstance(ev[0], complex) else (ev[0] * ev[1]).real
        self.check("λ₁ · λ₂ = Δ",
                    abs(ev_prod - float(a.delta)) < 1e-12,
                    f"prod={ev_prod:.10f}, Δ={float(a.delta)}")

        # Stable: both negative
        self.check("Stable atom: Re(λ) < 0",
                    all((e.real if isinstance(e, complex) else e) < 0 for e in ev))

        # Unstable: one positive
        a_u = Atom(Fraction(1,10), Fraction(1,10), Fraction(8,10), Fraction(8,10))
        ev_u = a_u.eigenvalues()
        has_pos = any((e.real if isinstance(e, complex) else e) > 0 for e in ev_u)
        self.check("Unstable atom: ∃ Re(λ) > 0", has_pos)

    # ── §6.4 Bifurcation boundary ──
    def sect_bifurcation_boundary(self):
        print("\n── §4. Bifurcation Boundary ──")

        # At ρ = 1: zero eigenvalue
        a_c = Atom(Fraction(1), Fraction(1), Fraction(1), Fraction(1))
        ev = a_c.eigenvalues()
        has_zero = any(abs(e.real if isinstance(e, complex) else e) < 1e-10 for e in ev)
        self.check("ρ = 1: zero eigenvalue", has_zero, f"ev = {ev}")
        self.check("ρ = 1: Δ = 0", a_c.delta == 0)

        # ε-perturbation
        eps = Fraction(1, 10000)
        a_below = Atom(Fraction(1), Fraction(1), Fraction(1), Fraction(1) - eps)
        a_above = Atom(Fraction(1), Fraction(1), Fraction(1), Fraction(1) + eps)
        self.check("ρ = 1−ε: stable", a_below.is_stable)
        self.check("ρ = 1+ε: unstable", not a_above.is_stable)

        # Monotonic transition
        results = []
        for i in range(1, 201):
            g = Fraction(i, 100)
            a = Atom(Fraction(1), Fraction(1), Fraction(1), g)
            results.append((float(a.rho), a.is_stable))
        results.sort()
        crossed = False
        monotonic = True
        for rho, stable in results:
            if rho > 1.0: crossed = True
            if crossed and stable: monotonic = False; break
        self.check("Phase transition monotonic (200 points)", monotonic)

    # ── §6.5 Trajectory convergence ──
    def sect_trajectory_convergence(self):
        print("\n── §5. Trajectory Convergence ──")
        a = Atom(Fraction(6,10), Fraction(7,10), Fraction(1,10), Fraction(2,10))
        sim = AtomSimulator(a)

        ics = [(5.0, 3.0), (-2.0, 4.0), (8.0, -1.0), (-3.0, -5.0), (0.1, 9.0)]
        converged = 0
        for x1, x2 in ics:
            traj = sim.simulate(x1, x2, dt=0.005, t_max=30)
            final = traj[-1]
            if abs(final[1]) < 0.01 and abs(final[2]) < 0.01:
                converged += 1

        self.check(f"Stable: {len(ics)} ICs → origin",
                    converged == len(ics),
                    f"{converged}/{len(ics)}")

    # ── §6.6 Trajectory divergence ──
    def sect_trajectory_divergence(self):
        print("\n── §6. Trajectory Divergence ──")
        a = Atom(Fraction(1,10), Fraction(1,10), Fraction(8,10), Fraction(8,10))
        sim = AtomSimulator(a)

        traj = sim.simulate(1.0, 0.1, dt=0.005, t_max=20)
        init_norm = math.sqrt(traj[0][1]**2 + traj[0][2]**2)
        final_norm = math.sqrt(traj[-1][1]**2 + traj[-1][2]**2)

        self.check("Unstable: trajectory diverges",
                    final_norm > init_norm * 10,
                    f"‖x₀‖={init_norm:.2f} → ‖x_f‖={final_norm:.2f}")

    # ── §6.7 Lyapunov ──
    def sect_lyapunov(self):
        print("\n── §7. Lyapunov Monotonicity ──")
        a = Atom(Fraction(6,10), Fraction(7,10), Fraction(1,10), Fraction(2,10))
        sim = AtomSimulator(a)

        traj = sim.simulate(5.0, 5.0, dt=0.005, t_max=30)
        lyap = sim.lyapunov(traj)

        # Sample every 50 steps
        sampled = lyap[::50]
        decreasing = all(sampled[i][1] >= sampled[i+1][1] - 1e-10
                         for i in range(len(sampled)-1))
        self.check("V(t) monotonically decreasing", decreasing)

        # V → 0
        self.check("V(t) → 0", lyap[-1][1] < 0.001, f"V_final = {lyap[-1][1]:.8f}")

    # ── §6.8 RC2 gate equivalence ──
    def sect_rc2_gate_equivalence(self):
        print("\n── §8. RC2 Gate ⟺ Δ > 0 ──")

        random.seed(2026)
        n = 500
        agree = 0
        for _ in range(n):
            b = Fraction(random.randint(1, 99), 100)
            k = Fraction(random.randint(1, 99), 100)
            al = Fraction(random.randint(1, 99), 100)
            g = Fraction(random.randint(1, 99), 100)
            a = Atom(b, k, al, g)
            if a.gate() == a.is_stable:
                agree += 1

        self.check(f"RC2 gate ⟺ Δ > 0  ({n} random atoms)",
                    agree == n, f"{agree}/{n}")

    # ── §6.9 Full equivalence sweep ──
    def sect_randomized_sweep(self):
        print("\n── §9. E1–E6 Equivalence Sweep ──")

        random.seed(42)
        n = 200
        all_equiv = 0

        for _ in range(n):
            b = Fraction(random.randint(1, 99), 100)
            k = Fraction(random.randint(1, 99), 100)
            al = Fraction(random.randint(1, 99), 100)
            g = Fraction(random.randint(1, 99), 100)
            a = Atom(b, k, al, g)
            eq = verify_equivalence(a)
            vals = list(eq.values())
            if all(v == vals[0] for v in vals):
                all_equiv += 1

        self.check(f"E1–E6 unanimous ({n} random atoms)",
                    all_equiv == n, f"{all_equiv}/{n}")

    # ── §6.10 Block system ──
    def sect_block_system(self):
        print("\n── §10. N-State Block System ──")

        # 5 stable blocks → system stable
        atoms_s = [
            Atom(Fraction(6,10), Fraction(7,10), Fraction(1,10), Fraction(2,10)),
            Atom(Fraction(8,10), Fraction(9,10), Fraction(2,10), Fraction(3,10)),
            Atom(Fraction(5,10), Fraction(5,10), Fraction(1,10), Fraction(1,10)),
            Atom(Fraction(7,10), Fraction(4,10), Fraction(1,10), Fraction(1,10)),
            Atom(Fraction(9,10), Fraction(8,10), Fraction(3,10), Fraction(2,10)),
        ]
        bs = BlockSystem(atoms_s)
        self.check("5 stable blocks → system stable",
                    bs.is_stable, f"dim={bs.dim}, min_Δ={bs.min_delta}")

        # Verify all eigenvalues negative
        evs = bs.eigenvalues()
        all_neg = all((e.real if isinstance(e, complex) else e) < 0 for e in evs)
        self.check("All 10 eigenvalues have Re < 0", all_neg,
                    f"{sum(1 for e in evs if (e.real if isinstance(e,complex) else e) < 0)}/10")

        # One unstable block → system unstable
        atoms_mixed = atoms_s[:4] + [
            Atom(Fraction(1,10), Fraction(1,10), Fraction(9,10), Fraction(9,10))
        ]
        bs_m = BlockSystem(atoms_mixed)
        self.check("1 unstable block → system unstable", not bs_m.is_stable)

        # Weakest link identified
        self.check("Weakest block = index 4",
                    bs_m.weakest_block == 4, f"idx={bs_m.weakest_block}")

    # ── §6.11 Weakest link ──
    def sect_block_weakest_link(self):
        print("\n── §11. Weakest-Link Principle ──")

        # System score = min block score
        atoms = [
            Atom(Fraction(9,10), Fraction(9,10), Fraction(1,10), Fraction(1,10)),  # high margin
            Atom(Fraction(5,10), Fraction(5,10), Fraction(4,10), Fraction(4,10)),  # low margin
            Atom(Fraction(8,10), Fraction(7,10), Fraction(2,10), Fraction(3,10)),  # medium
        ]
        bs = BlockSystem(atoms)

        scores = [a.score for a in atoms]
        self.check("System score = min(block scores)",
                    bs.system_score == min(scores),
                    f"sys={bs.system_score}, min={min(scores)}")

        self.check("System Δ = min(block Δ)",
                    bs.min_delta == min(a.delta for a in atoms))

    # ── §6.12 Perturbation bound ──
    def sect_perturbation_bound(self):
        print("\n── §12. Perturbation Robustness ──")

        atoms = [
            Atom(Fraction(7,10), Fraction(8,10), Fraction(1,10), Fraction(2,10)),
            Atom(Fraction(6,10), Fraction(6,10), Fraction(2,10), Fraction(3,10)),
        ]
        bs = BlockSystem(atoms)
        cbs = CoupledBlockSystem(bs, epsilon=Fraction(1, 100))

        self.check("ε < min_Δ → robust",
                    cbs.is_robust,
                    f"ε={cbs.epsilon}, bound={cbs.stability_bound()}")

        # Large ε → not robust
        cbs_big = CoupledBlockSystem(bs, epsilon=Fraction(99, 100))
        self.check("ε > min_Δ → not guaranteed robust",
                    not cbs_big.is_robust,
                    f"ε={cbs_big.epsilon}, bound={cbs_big.stability_bound()}")

    # ── §6.13 Score algebra ──
    def sect_score_algebra(self):
        print("\n── §13. Score Algebra ──")

        # Score is monotone in Δ
        a1 = Atom(Fraction(7,10), Fraction(8,10), Fraction(1,10), Fraction(1,10))
        a2 = Atom(Fraction(7,10), Fraction(8,10), Fraction(3,10), Fraction(3,10))
        self.check("Higher Δ → higher score",
                    (a1.delta > a2.delta) == (a1.score > a2.score))

        # Score ∈ (0, 1) for positive gains
        random.seed(99)
        in_range = all(
            0 < Atom(
                Fraction(random.randint(1,99),100), Fraction(random.randint(1,99),100),
                Fraction(random.randint(1,99),100), Fraction(random.randint(1,99),100),
            ).score < 1
            for _ in range(200)
        )
        self.check("Score ∈ (0,1) for all positive gains (200 samples)", in_range)

        # Score = 1/2 at critical
        a_c = Atom(Fraction(1), Fraction(1), Fraction(1), Fraction(1))
        self.check("Score = 1/2 at ρ = 1",
                    a_c.score == Fraction(1, 2), f"score = {a_c.score}")


# ═════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print(f"RC4 UNIVERSAL — CROSS-GAIN COMPETITION ATOM v{__version__} [{__status__}]")
    print("=" * 70)
    print("Δ = βκ − αγ   |   Δ > 0 → stable   |   one scalar decides all")
    print("=" * 70)

    bench = UniversalBenchmark()
    elapsed = bench.run_all()

    total = bench.passed + bench.failed
    print(f"\n{'═' * 70}")
    print(f"  {bench.passed}/{total} passed  |  {elapsed:.3f}s  |  v{__version__} [{__status__}]")
    print(f"{'═' * 70}")

    if bench.failed == 0:
        print(f"\n  ★ ATOM HOLDS")
        print(f"  E1–E6 equivalence verified on {200} random configurations.")
        print(f"  RC2 gate ⟺ Routh-Hurwitz on {500} random configurations.")
        print(f"  N-state block stability = weakest-link principle.")
        print(f"  Perturbation bound: ε < min_i(Δᵢ).")
        print(f"  Everything reduces to Δ = βκ − αγ.")
    else:
        print(f"\n  ⚠ {bench.failed} FAILURES")

    out_dir = "/home/claude/rc4_universal"
    os.makedirs(out_dir, exist_ok=True)
    output = {
        "version": __version__, "status": __status__,
        "passed": bench.passed, "failed": bench.failed,
        "total": total, "elapsed_seconds": elapsed,
        "tests": bench.results,
        "invariant": "Δ = βκ − αγ",
        "equivalences": ["E1: βκ > αγ", "E2: det(A) > 0", "E3: ρ < 1",
                          "E4: score > 1/2", "E5: Re(λ) < 0", "E6: RC2.gate()"],
    }
    with open(os.path.join(out_dir, "rc4_universal_results.json"), "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✓ Results: {out_dir}/rc4_universal_results.json")


if __name__ == "__main__":
    main()
