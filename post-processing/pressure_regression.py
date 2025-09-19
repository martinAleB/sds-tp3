import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from pressure_analysis import (
    read_static,
    read_collision_events,
    compute_pressures_from_events,
    ENC,
)
from pressure_area import area_total

def steady_stats(t, P_left, P_right, tmin: float = 60.0):
    """Promedio y std en régimen (descarta t < tmin)."""
    if len(t) == 0:
        return np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, 0

    mask = (t >= tmin)
    if not np.any(mask):
        mask = slice(None)

    Pc = 0.5 * (P_left[mask] + P_right[mask])
    Pl = P_left[mask]
    Pr = P_right[mask]

    n = int(np.size(Pc))
    if n >= 2:
        P_mean      = float(np.mean(Pc))
        P_std       = float(np.std(Pc, ddof=1))
        P_mean_left = float(np.mean(Pl))
        P_std_left  = float(np.std(Pl, ddof=1))
        P_mean_right= float(np.mean(Pr))
        P_std_right = float(np.std(Pr, ddof=1))
    elif n == 1:
        P_mean      = float(Pc[0]); P_std = 0.0
        P_mean_left = float(Pl[0]); P_std_left = 0.0
        P_mean_right= float(Pr[0]); P_std_right = 0.0
    else:
        P_mean=P_std=P_mean_left=P_std_left=P_mean_right=P_std_right=np.nan

    return P_mean, P_std, P_mean_left, P_std_left, P_mean_right, P_std_right, n


def analytic_c_hat(x, y):
    """Mínimos cuadrados por el origen (no ponderado): c* = sum(xy)/sum(x^2)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    Sxx = np.sum(x * x)
    Sxy = np.sum(x * y)
    c_hat = Sxy / Sxx
    sigma_c = np.sqrt(1.0 / Sxx) 
    return c_hat, sigma_c


def build_error_curve(x, y, cmin=None, cmax=None, num=400):
    """Devuelve grid de c y E(c) = sum (y - c x)^2."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    c_auto = np.sum(x * y) / np.sum(x * x)
    if cmin is None or cmax is None:
        span = 3.0 * abs(c_auto) if abs(c_auto) > 0 else 1.0
        cmin = c_auto - span
        cmax = c_auto + span
        if cmin == cmax:
            cmin, cmax = c_auto - 1.0, c_auto + 1.0
    cs = np.linspace(cmin, cmax, num)
    E = np.array([np.sum((y - c * x) ** 2) for c in cs])
    idx = int(np.argmin(E))
    return cs, E, cs[idx], E[idx]


def r2_score(y, y_pred):
    y = np.asarray(y, float)
    y_pred = np.asarray(y_pred, float)
    ss_res = np.sum((y - y_pred)**2)
    ss_tot = np.sum((y - np.mean(y))**2)
    return 1.0 - ss_res/ss_tot if ss_tot > 0 else np.nan

def main(folders, tmin: float, cmin: float|None, cmax: float|None, ngrid: int):
    results = []  # (L, A, Ainv, Pavg, Pstd, PavgL, PstdL, PavgR, PstdR, Pavg*A, n, N, M, V)

    for folder in folders:
        folder = Path(folder)
        static_path = folder / "static.txt"
        dynamic_path = folder / "dynamic.txt"
        if not static_path.exists() or not dynamic_path.exists():
            raise FileNotFoundError(f"Faltan archivos en {folder}")

        N, L, R, M, V, T = read_static(static_path)
        times_ev, idx_ev, X, Y, VX, VY = read_collision_events(dynamic_path, N)
        t, P_L, P_R = compute_pressures_from_events(times_ev, X, Y, VX, VY, N, L, R, M)

        Pavg, Pstd, PavgL, PstdL, PavgR, PstdR, n = steady_stats(t, P_L, P_R, tmin=tmin)

        A = area_total(L, R)
        Ainv = 1.0 / A

        results.append((L, A, Ainv, Pavg, Pstd, PavgL, PstdL, PavgR, PstdR, Pavg*A, n, N, M, V))

    results.sort(key=lambda x: x[0])

    Ainv_vals = np.array([r[2] for r in results], dtype=float)
    Pavg_vals = np.array([r[3] for r in results], dtype=float)
    Pstd_vals = np.array([r[4] for r in results], dtype=float)

    cs, Ecs, c_min_grid, Emin = build_error_curve(Ainv_vals, Pavg_vals, cmin=cmin, cmax=cmax, num=ngrid)

    c_hat, sigma_c = analytic_c_hat(Ainv_vals, Pavg_vals)

    delta_abs = abs(c_min_grid - c_hat)
    delta_rel = delta_abs / (abs(c_hat) if c_hat != 0 else 1.0)

    y_fit = c_hat * Ainv_vals
    R2 = r2_score(Pavg_vals, y_fit)

    # Gráfico 1: Curva de error E(c) y mínimo (solo analítico)
    plt.figure(figsize=(7.2, 4.6))
    plt.plot(cs, Ecs, '-', lw=2)
    plt.axvline(c_hat, ls='--', color='C1', label=f'c*={c_hat:.6f}')
    plt.plot(c_hat, np.min(Ecs), 'o', color='C1', markersize=8)

    plt.xlabel('c', fontsize=14)
    plt.ylabel('Error', fontsize=14)
    plt.tick_params(axis="both", labelsize=12)
    plt.grid(True, ls=':', alpha=0.5)
    plt.legend(fontsize=14)
    plt.tight_layout()
    plt.show()

    # Gráfico 2: datos + barras + recta ajustada (sin “teoría”)
    plt.figure(figsize=(7.6, 5.2))
    plt.errorbar(Ainv_vals, Pavg_vals, yerr=Pstd_vals, fmt='o', capsize=5,
                 label='Datos')
    xs = np.linspace(Ainv_vals.min(), Ainv_vals.max(), 200)
    plt.plot(xs, c_hat*xs, '-', label=f"Ajuste: c*={c_hat:.6f}")
    plt.xlabel(r"$Area^{-1}$  (m$^{-2}$)", fontsize=14)
    plt.ylabel(r"Presión Promedio  (Pa$\cdot$m)", fontsize=14)
    plt.tick_params(axis="both", labelsize=12)
    plt.grid(True, ls=':', alpha=0.5)
    plt.legend(fontsize=14)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs=4, help="Cuatro carpetas de simulación (una por L)")
    ap.add_argument("--tmin", type=float, default=60.0,
                    help="Descarta datos con t < tmin para promediar (default 40 s)")
    ap.add_argument("--cmin", type=float, default=None,
                    help="Límite inferior del barrido de c para la curva E(c)")
    ap.add_argument("--cmax", type=float, default=None,
                    help="Límite superior del barrido de c para la curva E(c)")
    ap.add_argument("--ngrid", type=int, default=400,
                    help="Cantidad de puntos en la grilla para E(c) (default 400)")
    args = ap.parse_args()
    main(args.folders, args.tmin, args.cmin, args.cmax, args.ngrid)
