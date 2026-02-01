"""Prototype RG flow analysis: integrate toy beta-functions and check FFT for dominant period.

This is a lightweight prototype that numerically integrates a simple toy ODE
dg/dt = -a * g + b * sin(2*pi*t/period) for demonstration and computes FFT on g(t).
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import os


def integrate_toy_beta(t_grid, g0=1.0, a=0.1, b=0.2, period=24.0):
    dt = t_grid[1] - t_grid[0]
    g = np.zeros_like(t_grid)
    g[0] = g0
    for k in range(1, len(t_grid)):
        t = t_grid[k-1]
        beta = -a * g[k-1] + b * np.sin(2 * np.pi * t / period)
        g[k] = g[k-1] + beta * dt
    return g


def analyze_fft(t_grid, g):
    # remove mean, compute FFT magnitude vs frequency in cycles per unit t
    y = g - np.mean(g)
    N = len(y)
    yf = np.fft.rfft(y)
    xf = np.fft.rfftfreq(N, d=(t_grid[1]-t_grid[0]))
    mag = np.abs(yf)
    # find dominant frequency
    idx = np.argmax(mag[1:]) + 1
    freq = xf[idx]
    period = 1.0 / freq if freq != 0 else np.inf
    return xf, mag, freq, period


def main():
    t_min, t_max = -35.0, 27.0
    dt = 0.05
    t_grid = np.arange(t_min, t_max, dt)
    g = integrate_toy_beta(t_grid, g0=1.0, a=0.05, b=0.5, period=24.0)

    xf, mag, freq, dom_period = analyze_fft(t_grid, g)

    save_dir = Path(__file__).resolve().parents[1] / 'figures'
    os.makedirs(save_dir, exist_ok=True)

    plt.figure(figsize=(10,4))
    plt.plot(t_grid, g)
    plt.xlabel('log10(length)')
    plt.ylabel('toy coupling g(t)')
    plt.title('Toy RG Flow Integration')
    plt.tight_layout()
    out1 = save_dir / 'rg_flow_g_t.png'
    plt.savefig(out1, dpi=200)
    plt.close()

    plt.figure(figsize=(8,4))
    plt.plot(xf, mag)
    plt.xlabel('Frequency (cycles per log10 unit)')
    plt.ylabel('FFT Magnitude')
    plt.title('FFT of g(t)')
    plt.tight_layout()
    out2 = save_dir / 'rg_flow_fft.png'
    plt.savefig(out2, dpi=200)
    plt.close()

    print('Dominant period (log10 units):', dom_period)
    print('Saved plots to:', out1, out2)


if __name__ == '__main__':
    main()
