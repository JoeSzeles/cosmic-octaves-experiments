"""
Prototype RG flow analysis: integrate toy beta-functions and check FFT for dominant period.

Usage examples:
  python rg_flow_analysis.py --period 24.0 --pert_amp 0.5 --window
  python rg_flow_analysis.py --t-min -40 --t-max 30 --dt 0.02
"""

import argparse
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os
from scipy.signal import find_peaks

# Hard-coded canonical structure log10 scales (from your original ladder)
CANONICAL_LOGS = np.array([
    -15.08, -10.28, -7.96, -6.00, -3.30, -0.046, 3.00,
    6.80, 8.84, 12.65, 16.67, 18.665, 20.70, 23.84, 26.64
])

def integrate_toy_beta(t_grid, g0=1.0, decay=0.05, pert_amp=0.5, period=24.0):
    """
    Toy ODE: dg/dt = -decay * g + pert_amp * sin(2π t / period)
    Simple Euler integration.
    """
    dt = t_grid[1] - t_grid[0]
    g = np.zeros_like(t_grid)
    g[0] = g0
    for k in range(1, len(t_grid)):
        t_prev = t_grid[k-1]
        beta = -decay * g[k-1] + pert_amp * np.sin(2 * np.pi * t_prev / period)
        g[k] = g[k-1] + beta * dt
    return g


def analyze_fft(t_grid, g, use_window=False):
    """Compute real FFT, remove mean, return freqs, magnitudes, dominant period."""
    y = g - np.mean(g)
    N = len(y)
    if use_window:
        from scipy.signal import hann
        window = hann(N)
        y *= window
    
    yf = np.fft.rfft(y)
    xf = np.fft.rfftfreq(N, d=(t_grid[1] - t_grid[0]))
    mag = np.abs(yf)
    
    # Find peaks (ignore DC component at index 0)
    peaks, _ = find_peaks(mag[1:], height=0.1 * mag.max())
    peaks += 1  # shift back to original indices
    
    if len(peaks) == 0:
        dom_freq = 0.0
        dom_period = np.inf
    else:
        # Sort peaks by magnitude descending
        peak_mags = mag[peaks]
        sorted_idx = np.argsort(peak_mags)[::-1]
        top_peaks = peaks[sorted_idx][:3]
        dom_freq = xf[top_peaks[0]]
        dom_period = 1.0 / dom_freq if dom_freq > 0 else np.inf
    
    return xf, mag, dom_freq, dom_period, top_peaks


def plot_results(t_grid, g, xf, mag, dom_period, save_dir, top_peaks=None):
    # Plot 1: g(t) with canonical lines
    fig1, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(t_grid, g, label='Toy coupling g(t)', color='blue')
    for log_val in CANONICAL_LOGS:
        if t_grid.min() <= log_val <= t_grid.max():
            ax1.axvline(log_val, color='gray', linestyle='--', alpha=0.4, linewidth=0.8)
    ax1.set_xlabel('log₁₀(length)')
    ax1.set_ylabel('Toy coupling g(t)')
    ax1.set_title(f'Toy RG Flow Integration (period={dom_period:.2f})')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    out1 = save_dir / 'rg_flow_g_t.png'
    fig1.savefig(out1, dpi=200, bbox_inches='tight')
    plt.close(fig1)

    # Plot 2: FFT
    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.plot(xf, mag, color='darkblue')
    ax2.set_xlabel('Frequency (cycles per log₁₀ unit)')
    ax2.set_ylabel('Magnitude')
    ax2.set_title('FFT of g(t)')
    ax2.grid(True, alpha=0.3)
    if top_peaks is not None and len(top_peaks) > 0:
        for pk in top_peaks[:3]:
            ax2.axvline(xf[pk], color='red', linestyle='--', alpha=0.6, linewidth=1.2,
                        label=f'Peak freq={xf[pk]:.4f} (period={1/xf[pk]:.2f})' if pk == top_peaks[0] else "")
    ax2.legend()
    out2 = save_dir / 'rg_flow_fft.png'
    fig2.savefig(out2, dpi=200, bbox_inches='tight')
    plt.close(fig2)

    print(f"Saved plots to:\n  {out1}\n  {out2}")


def main():
    parser = argparse.ArgumentParser(description="Toy RG flow + FFT analysis")
    parser.add_argument('--period', type=float, default=24.0, help='Target modulation period (log10 units)')
    parser.add_argument('--pert_amp', type=float, default=0.5, help='Amplitude of sinusoidal perturbation')
    parser.add_argument('--decay', type=float, default=0.05, help='Linear decay coefficient (-decay * g)')
    parser.add_argument('--g0', type=float, default=1.0, help='Initial coupling value')
    parser.add_argument('--t-min', type=float, default=-35.0, help='Min log10(length)')
    parser.add_argument('--t-max', type=float, default=27.0, help='Max log10(length)')
    parser.add_argument('--dt', type=float, default=0.05, help='Time step for integration')
    parser.add_argument('--window', action='store_true', help='Apply Hann window to FFT')
    
    args = parser.parse_args()

    t_grid = np.arange(args.t_min, args.t_max, args.dt)
    print(f"Grid: {len(t_grid)} points, dt={args.dt:.4f}, range={t_grid.min():.1f} to {t_grid.max():.1f}")

    g = integrate_toy_beta(t_grid, g0=args.g0, decay=args.decay,
                           pert_amp=args.pert_amp, period=args.period)

    xf, mag, dom_freq, dom_period, top_peaks = analyze_fft(t_grid, g, use_window=args.window)

    print(f"Dominant frequency: {dom_freq:.6f} cycles/log10 unit")
    print(f"Dominant period:    {dom_period:.3f} log10 units")
    if len(top_peaks) > 0:
        print("Top 3 peak frequencies / periods:")
        for pk in top_peaks[:3]:
            f = xf[pk]
            p = 1/f if f > 0 else np.inf
            print(f"  freq={f:.6f}, period={p:.3f}")

    save_dir = Path(__file__).resolve().parents[1] / 'figures'
    os.makedirs(save_dir, exist_ok=True)
    
    plot_results(t_grid, g, xf, mag, dom_period, save_dir, top_peaks)


if __name__ == '__main__':
    main()