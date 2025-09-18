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

def area_total(L: float, r) -> float:
    #return ENC*ENC + ENC*L
    return (ENC - 2*r)**2 + (ENC - 2*r)*L

def steady_stats(t, P_left, P_right, tmin: float = 60.0):
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


def main(folders):
    results = []
    for folder in folders:
        folder = Path(folder)
        static_path = folder / "static.txt"
        dynamic_path = folder / "dynamic.txt"
        if not static_path.exists() or not dynamic_path.exists():
            raise FileNotFoundError(f"Faltan archivos en {folder}")

        N, L, R, M, V, T = read_static(static_path)
        times_ev, idx_ev, X, Y, VX, VY = read_collision_events(dynamic_path, N)
        t, P_L, P_R = compute_pressures_from_events(times_ev, X, Y, VX, VY, N, L, R, M)

        Pavg, Pstd, PavgL, PstdL, PavgR, PstdR, n = steady_stats(t, P_L, P_R, tmin=60.0)
        A = area_total(L, R)
        Ainv = 1.0 / A
        results.append((L, A, Ainv, Pavg, Pstd, PavgL, PstdL, PavgR, PstdR, Pavg*A, n))

    results.sort(key=lambda x: x[0])

    Ainv_vals = [r[2] for r in results]
    Pavg_vals = [r[3] for r in results]
    Pstd_vals = [r[4] for r in results]

    plt.figure(figsize=(7.5, 5))
    plt.errorbar(Ainv_vals, Pavg_vals, yerr=Pstd_vals, fmt='o', lw=1.2, capsize=4)
    plt.xlabel(r"$A^{-1}$  [m$^{-2}$]", fontsize=14)
    plt.ylabel(r"$\overline{P}$  [N/m]", fontsize=14)
    #plt.title(r"Presión promedio en régimen vs $A^{-1}$")
    plt.tick_params(axis="both", labelsize=12)
    plt.grid(True, ls=":", alpha=0.5)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs=4, help="Cuatro carpetas de simulación (una por L)")
    args = ap.parse_args()
    main(args.folders)
