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
import numpy as np
from typing import List, Dict, Optional
from rc_stack.rc7_zeta import SystemState, EdgeAtom, Zeta
from rc_stack.rc8_epistemic import EpistemicHorizonEngine, RC8Invariants

class SovereignCertification:
    """
    Bridges Sovereign PrimeLattice4D to RC7/RC8 Invariant Engines.
    """
    def __init__(self, lattice_stats: Dict):
        self.lattice_stats = lattice_stats
        self.zeta_engine = Zeta()
        self.rc8_engine = EpistemicHorizonEngine()

    def map_lattice_to_state(self, points: List[Dict]) -> SystemState:
        """
        Maps lattice points to an RC7 SystemState.
        Each point is a node. Edges are sequential transitions.
        """
        nodes = set(range(len(points)))
        edges = []
        
        # Build sequential edges from the mixdown order
        for i in range(len(points) - 1):
            p1 = points[i]["coord"]
            p2 = points[i+1]["coord"]
            
            # Distance-based parameter derivation
            dist = np.linalg.norm(np.array(p1) - np.array(p2))
            
            # Logic: 
            # - Stable edges (beta, kappa) derived from prime hits in metadata
            # - Cross-coupling (alpha, gamma) derived from proximity
            # - Damping (d) is constant 1.0 baseline
            
            h1 = points[i]["meta"].get("prime_hit", False)
            h2 = points[i+1]["meta"].get("prime_hit", False)
            
            beta = 0.8 + (0.2 if h1 else 0)
            kappa = 0.8 + (0.2 if h2 else 0)
            alpha = min(0.4, 1.0 / (dist + 1e-5))
            gamma = min(0.4, 1.0 / (dist + 1e-5))
            
            edges.append(EdgeAtom(
                source=i,
                target=i+1,
                beta=beta,
                kappa=kappa,
                alpha=alpha,
                gamma=gamma,
                d=1.0
            ))
            
        return SystemState(nodes=nodes, edges=edges)

    def compute_epistemic_horizon(self, points: List[Dict]) -> Dict:
        """
        Computes RC8 Horizon for the point set.
        """
        coords = np.array([p["coord"] for p in points])
        if len(coords) < 2:
            return {"verdict": "INSUFFICIENT_DATA"}
            
        # 1. Estimate Amplitude (A)
        A = np.std(coords)
        
        # 2. Estimate Lyapunov (λ) via mean drift
        drifts = np.linalg.norm(np.diff(coords, axis=0), axis=1)
        lyapunov = np.mean(drifts) / (A + 1e-10)
        
        # 3. Estimate D2 (Correlation Dimension proxy)
        # Using a simplified variance-scaling proxy
        D2 = min(4.0, 1.0 + np.var(coords) / (A**2 + 1e-10))
        
        inv = RC8Invariants(
            lyapunov=max(0.151, lyapunov), # Hard-floor for chaos detection
            D2=D2,
            A=A,
            N=len(points)
        )
        
        # Standard noise estimate: 1 - purity
        stored = self.lattice_stats.get("stored", 1)
        total = self.lattice_stats.get("total", 1)
        sigma_hat = 1.0 - (stored / total)
        
        res = self.rc8_engine.evaluate(inv, sigma_hat=sigma_hat)
        return vars(res)

    def certify_mixdown(self, points: List[Dict]) -> Dict:
        """
        Full RC Stack certification for a mixdown state.
        """
        # RC7 Check
        state = self.map_lattice_to_state(points)
        zeta_res = self.zeta_engine.evaluate(state)
        
        # RC8 Check
        rc8_res = self.compute_epistemic_horizon(points)
        
        return {
            "zeta": {
                "holds": zeta_res.holds,
                "local_stable": zeta_res.local_stable,
                "topology_safe": zeta_res.topology_safe,
                "spectral_radius": zeta_res.spectral_radius
            },
            "rc8": rc8_res
        }
