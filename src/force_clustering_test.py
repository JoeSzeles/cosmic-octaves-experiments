"""
Force Clustering / Expanded Permutation Test - Cross-Domain Version
Usage: python force_clustering_test.py [--n_trials 200000] [--cross-only] [--append-dmde] [--smoke]

Counts octave matches (diff ≈ delta) only between structures and force scales (cross-domain).
This avoids combinatorial explosion and directly tests if force scales align with the cosmic ladder.
"""
import argparse
import csv
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import importlib.util

# Import DEFAULT_LOGS from octave_analysis
_ROOT = Path(__file__).resolve().parents[1]
_oa_path = _ROOT / 'src' / 'octave_analysis.py'
spec = importlib.util.spec_from_file_location('octave_analysis', str(_oa_path))
_oa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_oa)
DEFAULT_LOGS = _oa.DEFAULT_LOGS

def load_force_scales(csv_path: str):
    logs = []
    names = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as fo:
            reader = csv.DictReader(fo)
            for r in reader:
                try:
                    logs.append(float(r['log10_L']))
                    names.append(r['Structure'])
                except Exception:
                    continue
    except FileNotFoundError:
        return np.array([]), []
    return np.array(logs), names

def count_strong_cross_domain(arr, n_base, delta=24.0, thresh=0.2):
    """Count strong matches only between base structures (0..n_base-1) and added scales (n_base..end)"""
    strong = 0
    for i in range(n_base):
        for j in range(n_base, len(arr)):
            if abs((arr[j] - arr[i]) - delta) <= thresh:
                strong += 1
    return strong

def count_strong_all_pairs(arr, delta=24.0, thresh=0.2):
    """Original all-pairs count (for comparison only - noisy)"""
    n = len(arr)
    strong = 0
    for i in range(n):
        for j in range(i+1, n):
            if abs((arr[j] - arr[i]) - delta) <= thresh:
                strong += 1
    return strong

def main():
    parser = argparse.ArgumentParser(description="Force Clustering Permutation Test")
    parser.add_argument('--n_trials', type=int, default=200000, help="Number of permutations")
    parser.add_argument('--delta', type=float, default=24.0)
    parser.add_argument('--threshold', type=float, default=0.2)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--smoke', action='store_true', help="Quick run with fewer trials")
    parser.add_argument('--append-dmde', action='store_true', help="Append speculative DM/DE scales")
    parser.add_argument('--cross-only', action='store_true', default=True, 
                        help="Count only cross-domain pairs (structures vs force/DMDE) [recommended]")
    args = parser.parse_args()

    if args.smoke:
        args.n_trials = min(args.n_trials, 2000)

    print('='*70)
    print('FORCE CLUSTERING TEST (Cross-Domain Mode)' if args.cross_only else 'FORCE CLUSTERING TEST (All Pairs Mode)')
    print(f'Configuration: n_trials={args.n_trials}, delta={args.delta}, threshold={args.threshold}, seed={args.seed}')
    print('='*70)

    # Load base structure logs
    base_logs = np.array(DEFAULT_LOGS)
    n_base = len(base_logs)
    print(f"Base structures loaded: {n_base}")

    # Load force scales
    force_csv = Path(__file__).resolve().parents[1] / 'data' / 'force_scales.csv'
    force_logs, force_names = load_force_scales(str(force_csv))
    if len(force_logs) == 0:
        print('Warning: No force scales found at', force_csv)
    else:
        print(f'Loaded {len(force_logs)} force scales from {force_csv.name}')

    logs = np.concatenate([base_logs, force_logs]) if len(force_logs) else base_logs.copy()

    # Optional DM/DE
    if args.append_dmde:
        dmde = np.array([21.0, 26.5])  # DM halo ~21, DE horizon ~26.5
        logs = np.concatenate([logs, dmde])
        print('Appended DM/DE placeholder scales (21.0, 26.5)')

    n_total = len(logs)
    n_added = n_total - n_base
    print(f'Total scales in test: {n_total} (base: {n_base}, added: {n_added})')

    # Choose counting function
    if args.cross_only:
        count_func = lambda arr: count_strong_cross_domain(arr, n_base, args.delta, args.threshold)
        pairs_tested = n_base * n_added
        print(f"Counting cross-domain pairs only: {pairs_tested} possible pairs")
    else:
        count_func = lambda arr: count_strong_all_pairs(arr, args.delta, args.threshold)
        pairs_tested = n_total * (n_total - 1) // 2
        print(f"Counting ALL pairwise matches: {pairs_tested} possible pairs (noisy)")

    # Rough expected under uniform (very approximate)
    rough_p_single = 2 * args.threshold / 42.0  # ~42 orders of magnitude
    expected_rough = pairs_tested * rough_p_single
    print(f'Approximate expected strong matches under uniform random: ~{expected_rough:.1f}')

    rng = np.random.default_rng(args.seed)

    observed_strong = count_func(logs)
    print(f'\nObserved strong matches (<= {args.threshold}): {observed_strong}')

    print('\nRunning permutation test...')
    count_exceeds = 0
    random_counts = []
    for i in range(args.n_trials):
        perm = rng.permutation(logs)
        s = count_func(perm)
        random_counts.append(s)
        if s >= observed_strong:
            count_exceeds += 1
        if (i + 1) % max(1, args.n_trials // 10) == 0:
            print(f'  Progress: {i+1:,} / {args.n_trials:,} trials ({(i+1)/args.n_trials*100:.0f}%)')

    p = count_exceeds / args.n_trials
    p_upper = (count_exceeds + 1) / (args.n_trials + 1)

    print('\n' + '='*70)
    print('RESULTS')
    print('='*70)
    print(f'Permutations with strong >= {observed_strong}: {count_exceeds:,} out of {args.n_trials:,}')
    print(f'Empirical p-value: {p:.6f} ({p*100:.4f}%)')
    print(f'Conservative upper bound (add-one): {p_upper:.6f} ({p_upper*100:.4f}%)')
    print('='*70)

    # Histogram
    save_dir = Path(__file__).resolve().parents[1] / 'figures'
    os.makedirs(save_dir, exist_ok=True)
    plt.figure(figsize=(10, 6))
    plt.hist(random_counts, bins=range(min(random_counts), max(random_counts)+2), 
             color='purple', alpha=0.7, edgecolor='black')
    plt.axvline(observed_strong, color='red', linestyle='--', linewidth=2, 
                label=f'Observed: {observed_strong}')
    plt.xlabel('Number of Strong Matches')
    plt.ylabel('Frequency')
    plt.title('Force Clustering: Expanded Permutation Test\n(Cross-Domain Mode)' if args.cross_only else 'All Pairs Mode')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    out_path = save_dir / 'force_clustering_hist.png'
    plt.savefig(out_path, dpi=300)
    plt.close()
    print('Histogram saved to', out_path)

if __name__ == '__main__':
    main()