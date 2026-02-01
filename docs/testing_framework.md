# Testing Framework for Cosmic Octaves

## Purpose
This document outlines a set of mathematical and statistical tests to evaluate and extend the "Cosmic Octaves" hypothesis. The goal is to provide reproducible experiment sketches, rationale, expected outcomes, and implementation notes for three prioritized tests: (1) Force Range Clustering, (2) Renormalization Group (RG) Flow & Periodicity, and (3) Toy Universe Simulation with a Fractal Force.

---

## Summary of Context
- The core observation: characteristic lengths of many structures appear to align in octave-like pairs with log10 ratio near 24.
- Primary repo scripts: `code/permutation_test.py` and `code/delta_scan.py` perform permutation testing and delta scanning.
- Default configuration: 15 structures, 7 canonical pairs; permutation tests use `n_trials=200000` and RNG seed `42`.

---

## Test 1 — Force Range Clustering

Rationale
- Add characteristic ranges of fundamental forces and interaction types (Planck, nuclear, atomic, biochemical, dust/grain, galactic, etc.) to the scale list and re-run permutation-style alignment tests to see if force scales preferentially align into octave pairings.

Mathematical setup
- Let L_i be log10(length) for each structure i. Maintain canonical `pairs` as the candidate ladder.
- Deviation for pair (i,j): d_{ij}(Δ) = |(L_j - L_i) - Δ|. For a fixed Δ (default 24), define a strong match when d_{ij} <= threshold (default 0.2).
- Permutation test: random permutations of L across labels produce null distribution of count of strong matches.

Code sketch
- `src/force_clustering_test.py` will:
  - Load `logs` from base `scale_table.csv` and append the new `data/force_scales.csv` rows.
  - Allow command-line options: `--n_trials`, `--delta`, `--threshold`, `--seed`, and `--append-dmde`.
  - Reuse functions from `src/octave_analysis.py` (`get_deviations`, `count_strong_matches`, `max_strong_matches_in_scan`).
  - Output histogram to `/figures/force_clustering_hist.png` and print p-values (empirical + add-one conservative bound).

Expected outcomes
- If forces add structure, we may see increased counts of strong matches and lower empirical p-values compared to baseline.

Extensions
- Weight matches by physical relevance (e.g., coupling-strength-weighted scoring) and test for significance.

---

## Test 2 — Renormalization Group Flow & Periodicity

Rationale
- The RG viewpoint treats physics at different length scales via flow of coupling constants; if octave periodicity exists, RG flows or effective couplings may show periodic/oscillatory signatures on a log-length axis.

Mathematical setup
- Define toy β-functions for one or more coupling parameters: d g / d t = β(g, t), where t = log10(length).
- Add sinusoidal/fractal modulation terms, or consider simple polynomial β(g) choices producing scale-dependent oscillations.

Code sketch
- `src/rg_flow_analysis.py` or `src/rg_flow_analysis.ipynb` will:
  - Integrate toy β-functions over a grid in t ∈ [t_min, t_max] (e.g., -35 → +27).
  - Record g(t) for each toy coupling and compute FFT on g(t) vs t.
  - Identify dominant frequency f_dom and convert to period P = 1/f_dom in log10-length units; compare to Δ≈24.

Expected outcomes
- Detection of a dominant period near ~24 (log10) would be suggestive; absence would constrain the toy-model parameterization.

Extensions
- Sweep β-function parameters and produce a heatmap of dominant periods as function of model parameters.

---

## Test 3 — Toy Universe Simulation with Fractal Force

Rationale
- Build an N-body / clustering toy with a modified radial force law that includes a log-periodic (sinusoidal-in-log) perturbation so that F(r) ~ 1/r^2 * (1 + ε * sin(2π * log10(r)/Δ + φ)).

Mathematical setup
- Simulate many particles with periodic boundary conditions and perform clustering analysis (e.g., hierarchical clustering or DBSCAN) to extract characteristic inter-clump scales.

Code sketch
- `src/fractal_force_sim.py` (stretch goal) outlines:
  - Initial random particle distribution in 3D box.
  - Time-stepping with simple velocity Verlet integrator and pairwise forces approximated with cutoff.
  - After relaxation, run clustering and extract cluster size distribution; compare modes to octave spacing.

Expected outcomes
- A toy model that reproduces preferred cluster scales spaced near Δ would support the fractal-force hypothesis.

---

## Holographic & DM/DE Speculative Notes
- Consider DM/DE as inter-scale leakage in projection: DM as lower-boundary small-scale structure projected upward; DE as boundary tension from larger scales projecting down.
- Add optional DM/DE placeholder scales to tests and re-run.

---

## Implementation Notes & Conventions
- Use RNG seed `42` for reproducibility.
- Default `n_trials = 200_000` for permutation tests; provide `--n_trials` to override for smoke runs.
- Save all figures into the repository `/figures/` directory with descriptive filenames.
- All new scripts must include a short header print (title, configuration) and docstring.

---

## Next Actions (development roadmap)
1. Implement modular core functions (`src/octave_analysis.py`).
2. Add `data/force_scales.csv` and validate code paths.
3. Implement `src/force_clustering_test.py` and provide a smoke-run mode (`--n_trials 2000`).
4. Prototype RG flow analysis in a notebook and produce a report of dominant periods.

---

_This document is intended as a living plan. Update as prototypes and results become available._
