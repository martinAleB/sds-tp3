import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

def read_static(static_path: Path) -> Tuple[int, float, float, float, float, float]:
    with static_path.open("r") as f:
        N = int(f.readline().strip())
        L = float(f.readline().strip())
        R = float(f.readline().strip())
        M = float(f.readline().strip())
        V = float(f.readline().strip())
        T = float(f.readline().strip())
    return N, L, R, M, V, T


def read_dynamic_positions(dynamic_path: Path, N: int) -> Tuple[np.ndarray, np.ndarray]:
    with dynamic_path.open("r") as f:
        lines = f.readlines()

    times: List[float] = []
    positions: List[np.ndarray] = []

    i = 0
    while i < len(lines):
        head = lines[i].strip()
        if not head:
            i += 1
            continue
        toks = head.split()
        t = float(toks[0])
        i += 1

        frame_pos = np.zeros((N, 2), dtype=float)
        for p in range(N):
            parts = lines[i].split()
            if len(parts) == 4:
                x, y, vx, vy = map(float, parts)
            elif len(parts) == 5:
                _, x, y, vx, vy = parts
                x, y, vx, vy = map(float, (x, y, vx, vy))
            frame_pos[p, 0] = x
            frame_pos[p, 1] = y
            i += 1

        times.append(t)
        positions.append(frame_pos)

    return np.array(times, dtype=float), np.stack(positions)

def compute_msd(positions: np.ndarray, ref_index: int = 0) -> np.ndarray:
    r0 = positions[ref_index]
    disp = positions - r0
    sq = np.sum(disp * disp, axis=2)
    msd = np.mean(sq, axis=1)
    return msd


def error_curve_for_slope_origin(x: np.ndarray, y: np.ndarray, a_grid: np.ndarray) -> np.ndarray:
    Syy = float(np.sum(y * y))
    Sxy = float(np.sum(x * y))
    Sxx = float(np.sum(x * x))
    return Syy - 2.0 * a_grid * Sxy + (a_grid * a_grid) * Sxx


def analytic_slope_origin(x: np.ndarray, y: np.ndarray) -> float:
    Sxx = float(np.sum(x * x))
    Sxy = float(np.sum(x * y))
    return 0.0 if Sxx == 0.0 else Sxy / Sxx


def r2_score(y: np.ndarray, y_hat: np.ndarray) -> float:
    ss_res = float(np.sum((y - y_hat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else np.nan


def sci_formatter():
    fmt = ScalarFormatter(useMathText=True)
    fmt.set_scientific(True)
    fmt.set_powerlimits((0, 0))
    return fmt

def format_sci_base10(val: float, prec: int = 2) -> str:
    s = f"{val:.{prec}e}"          # ej "3.45e-04"
    base, exp = s.split("e")
    exp = int(exp)
    return f"${base} \\times 10^{{{exp}}}$"

def main(folder: Path, t0_abs: float, tmin: float, tmax: float, dim: int,
         a_min: float | None, a_max: float | None, ngrid: int):
    static_path = folder / "static.txt"
    dynamic_path = folder / "dynamic.txt"
    N, L, R, M, V, T = read_static(static_path)
    times_abs, positions = read_dynamic_positions(dynamic_path, N)

    i0 = int(np.where(times_abs >= float(t0_abs))[0][0])
    times = times_abs - times_abs[i0]
    msd = compute_msd(positions, ref_index=i0)

    mask = (times >= tmin) & (times <= tmax)
    x = times[mask].astype(float)
    y = msd[mask].astype(float)

    a_hat = analytic_slope_origin(x, y)
    if a_min is None or a_max is None:
        span = 3.0 * abs(a_hat) if abs(a_hat) > 0 else 1.0
        a_min, a_max = a_hat - span, a_hat + span

    a_grid = np.linspace(float(a_min), float(a_max), int(ngrid))
    E_grid = error_curve_for_slope_origin(x, y, a_grid)
    idx_min = int(np.argmin(E_grid))
    a_min_grid = float(a_grid[idx_min])

    y_hat = a_hat * x
    D = a_hat / (2.0 * float(dim))

    # Gráfico 1: Curva de error 
    plt.figure(figsize=(7.4, 4.8))
    plt.plot(a_grid, E_grid, '-', lw=2)
    plt.axvline(a_hat, ls='--', color='C1', label=f'a* = {format_sci_base10(a_hat, prec=2)}')
    plt.plot(a_min_grid, E_grid[idx_min], 'o', color='C1', markersize=8)

    ax_err = plt.gca()
    ax_err.xaxis.set_major_formatter(sci_formatter())
    ax_err.yaxis.set_major_formatter(sci_formatter())
    ax_err.xaxis.get_offset_text().set_fontsize(14)
    ax_err.yaxis.get_offset_text().set_fontsize(14)

    plt.xlabel('a', fontsize=16)
    plt.ylabel('E(a)', fontsize=16)
    plt.tick_params(axis="both", labelsize=13)
    plt.grid(True, ls=':', alpha=0.5)
    plt.legend(fontsize=14)
    plt.tight_layout()
    plt.show()

    # Gráfico 2: MSD
    plt.figure(figsize=(7.8, 5.4))
    plt.plot(x, y, '-', lw=1.2, label='MSD (datos)')
    xs = np.linspace(x.min(), x.max(), 200)
    plt.plot(xs, a_hat * xs, '--', lw=1.4,
         label=f"a = {format_sci_base10(a_hat, prec=2)}")

    ax_msd = plt.gca()
    ax_msd.yaxis.set_major_formatter(sci_formatter())
    ax_msd.yaxis.get_offset_text().set_fontsize(14)

    plt.xlabel("t[s]", fontsize=16)
    plt.ylabel("MSD[m$^2$]", fontsize=16)
    plt.tick_params(axis="both", labelsize=13)
    plt.grid(True, ls=':', alpha=0.5)
    plt.legend(fontsize=14)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path)
    ap.add_argument("--t0", type=float, default=51.0)
    ap.add_argument("--tmin", type=float, default=1.0)
    ap.add_argument("--tmax", type=float, default=20.0)
    ap.add_argument("--dim", type=int, default=2)
    ap.add_argument("--amin", type=float, default=None)
    ap.add_argument("--amax", type=float, default=None)
    ap.add_argument("--ngrid", type=int, default=400)
    args = ap.parse_args()
    main(args.folder, args.t0, args.tmin, args.tmax, args.dim, args.amin, args.amax, args.ngrid)
