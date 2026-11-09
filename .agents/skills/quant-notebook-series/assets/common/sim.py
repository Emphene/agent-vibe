"""Simulation utilities. Seeded generators only; no global RNG state."""
from __future__ import annotations

import numpy as np


def rng(seed: int = 42) -> np.random.Generator:
    return np.random.default_rng(seed)


def gbm_paths(s0, r, q, vol, T, n_steps, n_paths, seed=42, antithetic=True) -> np.ndarray:
    """Exact-step GBM under the risk-neutral measure. Shape (n_paths, n_steps + 1)."""
    g = rng(seed)
    n_base = n_paths // 2 if antithetic else n_paths
    z = g.standard_normal((n_base, n_steps))
    if antithetic:
        z = np.vstack([z, -z])
    dt = T / n_steps
    incr = (r - q - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * z
    log_s = np.concatenate([np.zeros((z.shape[0], 1)), np.cumsum(incr, axis=1)], axis=1)
    return s0 * np.exp(log_s)


def correlated_normals(corr: np.ndarray, n_paths: int, n_steps: int, seed=42) -> np.ndarray:
    """Standard normals with correlation matrix `corr`. Shape (n_paths, n_steps, n_assets)."""
    g = rng(seed)
    L = np.linalg.cholesky(corr)
    z = g.standard_normal((n_paths, n_steps, corr.shape[0]))
    return z @ L.T
