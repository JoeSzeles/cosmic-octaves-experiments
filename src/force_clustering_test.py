"""Force clustering / expanded permutation test

Usage: run as a script. Supports smoke runs with --n_trials.
"""

import argparse
import os
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

import importlib.util
from pathlib import Path as _Path

# Import octave_analysis by file path to avoid package import issues
_ROOT = _Path(__file__).resolve().parents[1]
_oa_path = _ROOT / 'src' / 'octave_analysis.py'
spec = importlib.util.spec_from_file_location('octave_analysis', str(_oa_path))
_oa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_oa)
get_deviations = _oa.get_deviations
count_strong_matches = _oa.count_strong_matches
DEFAULT_LOGS = _oa.DEFAULT_LOGS

import csv


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
        return [], []
    return np.array(logs), names


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--n_trials', type=int, default=200000)
    parser.add_argument('--delta', type=float, default=24.0)
    parser.add_argument('--threshold', type=float, default=0.2)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--smoke', action='store_true', help='Use smaller n_trials for quick runs')
    parser.add_argument('--append-dmde', action='store_true', help='Append speculative DM/DE scales')
    args = parser.parse_args()

    if args.smoke:
        args.n_trials = min(args.n_trials, 2000)

    print('='*70)
    print('FORCE CLUSTERING TEST')
    print(f'Configuration: n_trials={args.n_trials}, delta={args.delta}, threshold={args.threshold}, seed={args.seed}')
    print('='*70)

    # Load base logs from src.octave_analysis.DEFAULT_LOGS
    base_logs = np.array(DEFAULT_LOGS)

    # Load force scales
    force_csv = Path(__file__).resolve().parents[1] / 'data' / 'force_scales.csv'
    force_logs, force_names = load_force_scales(str(force_csv))
    if force_logs.size == 0:
        print('No force scales found at', force_csv)
    else:
        print(f'Loaded {len(force_logs)} force scales from {force_csv.name}')

    logs = np.concatenate([base_logs, force_logs]) if force_logs.size else base_logs.copy()

    # Optional DM/DE placeholders
    if args.append_dmde:
        dmde = np.array([21.0, 26.5])  # placeholder DM (~21), DE (~26.5)
        logs = np.concatenate([logs, dmde])
        print('Appended DM/DE placeholder scales')

    rng = np.random.default_rng(args.seed)

    observed_dev = get_deviations(logs, delta=args.delta)
    # For extended logs we don't have canonical pairs; count strong matches across sliding pairs (first 7 pairs)
    # Use the first 7 canonical pairs mapped into the extended logs by indices from DEFAULT_LOGS
    # For simplicity, count strong matches by computing all pairwise differences and finding matches where difference ~ delta
    def count_strong_for_array(arr):
        # create all pair differences j>i
        n = len(arr)
        strong = 0
        for i in range(n):
            for j in range(i+1, n):
                if abs((arr[j] - arr[i]) - args.delta) <= args.threshold:
                    strong += 1
        return strong

    observed_strong = count_strong_for_array(logs)
    print('\nObserved strong matches (<=threshold):', observed_strong)
    print('\nRunning permutation test...')

    n_trials = args.n_trials
    count = 0
    random_counts = []
    for i in range(n_trials):
        perm = rng.permutation(logs)
        s = count_strong_for_array(perm)
        random_counts.append(s)
        if s >= observed_strong:
            count += 1
        if (i+1) % max(1, n_trials//10) == 0:
            print(f'  Progress: {i+1:,} / {n_trials:,} trials ({(i+1)/n_trials*100:.0f}%)')

    p = count / n_trials
    p_upper = (count + 1) / (n_trials + 1)

    print('\n' + '='*70)
    print('RESULTS')
    print('='*70)
    print(f'Permutations with strong >= {observed_strong}: {count:,} out of {n_trials:,}')
    print(f'Empirical p-value: {p:.6f} ({p*100:.5f}%)')
    print(f'Conservative upper bound (add-one): {p_upper:.6f} ({p_upper*100:.5f}%)')
    print('='*70)

    # Save histogram
    save_dir = Path(__file__).resolve().parents[1] / 'figures'
    os.makedirs(save_dir, exist_ok=True)
    plt.figure(figsize=(8,5))
    plt.hist(random_counts, bins=range(min(random_counts), max(random_counts)+2), color='purple', alpha=0.7, edgecolor='black')
    plt.axvline(observed_strong, color='red', linestyle='--', linewidth=2, label=f'Observed: {observed_strong}')
    plt.xlabel('Number of Strong Matches (pairwise)')
    plt.ylabel('Frequency')
    plt.title('Force Clustering: Expanded Permutation Test')
    plt.legend()
    plt.tight_layout()
    out_path = save_dir / 'force_clustering_hist.png'
    plt.savefig(out_path, dpi=200)
    plt.close()
    print('Histogram saved to', out_path)


if __name__ == '__main__':
    main()
