# analyze_P_vs_Ainv.py
# Uso:
#   python3 analyze_P_vs_Ainv.py sim_L003 sim_L005 sim_L007 sim_L009 --steady-frac 0.5
#
# Requiere pressure_analysis.py en el PYTHONPATH (mismo directorio o paquete).
# Importa funciones existentes y no reimplementa nada de presión/choques.

import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

from pressure_analysis import (
    read_static,
    read_collision_events,
    compute_pressures_from_events,
    ENC,   # para calcular A(L)
)

def area_total(L: float) -> float:
    # A = A_cuadrado + A_canal = 0.09*0.09 + 0.09*L
    return ENC*ENC + ENC*L

def steady_mean(t, P_left, P_right, frac: float = 0.5):
    """
    Promedio en régimen: toma la fracción final 'frac' del tiempo y promedia
    (izq y der) -> devuelve P_prom = mean( (P_left + P_right)/2 ) en esa ventana.
    También devuelve por separado las medias de cada recinto.
    """
    if len(t) == 0:
        return np.nan, np.nan, np.nan
    t0, t1 = t[0], t[-1]
    cut = t0 + frac*(t1 - t0)
    mask = t >= cut
    if not np.any(mask):
        mask = slice(None)
    P_avg_left  = float(np.mean(P_left[mask]))   if np.any(mask) else float(np.mean(P_left))
    P_avg_right = float(np.mean(P_right[mask]))  if np.any(mask) else float(np.mean(P_right))
    P_avg = 0.5*(P_avg_left + P_avg_right)
    return P_avg, P_avg_left, P_avg_right

def main(folders, steady_frac: float):
    results = []  # (L, A, Ainv, Pavg, PavgL, PavgR, PA)

    for folder in folders:
        folder = Path(folder)
        static_path = folder / "static.txt"
        dynamic_path = folder / "dynamic.txt"
        if not static_path.exists() or not dynamic_path.exists():
            raise FileNotFoundError(f"Faltan archivos en {folder}")

        N, L, R, M, V, T = read_static(static_path)
        times_ev, idx_ev, X, Y, VX, VY = read_collision_events(dynamic_path, N)
        t, P_L, P_R = compute_pressures_from_events(times_ev, X, Y, VX, VY, N, L, R, M)

        Pavg, PavgL, PavgR = steady_mean(t, P_L, P_R, steady_frac)
        A = area_total(L)
        Ainv = 1.0 / A
        results.append((L, A, Ainv, Pavg, PavgL, PavgR, Pavg*A))

    # Ordenar por L para prolijidad
    results.sort(key=lambda x: x[0])

    # Tabla resumen
    print("\nResumen: presión promedio en régimen (fracción final = {:.2f})".format(steady_frac))
    print("L [m]   A [m^2]     1/A [1/m^2]   P_avg [N/m]   P_left  P_right  (P·A)")
    for L, A, Ainv, Pavg, PavgL, PavgR, PA in results:
        print(f"{L:0.3f}  {A:0.6f}  {Ainv:0.3f}      {Pavg:0.6e}  {PavgL:0.6e}  {PavgR:0.6e}  {PA:0.6e}")

    # Gráfico P_prom vs A^{-1}
    Ainv_vals = [r[2] for r in results]
    Pavg_vals = [r[3] for r in results]

    plt.figure(figsize=(7.5, 5))
    plt.plot(Ainv_vals, Pavg_vals, "o-", lw=1.6, ms=6)
    plt.xlabel(r"$A^{-1}$  [m$^{-2}$]")
    plt.ylabel(r"$\overline{P}$  [N/m]")
    #plt.title(r"Presión promedio en régimen vs $A^{-1}$")
    plt.grid(True, ls=":", alpha=0.5)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs=4, help="Cuatro carpetas de simulación (una por L)")
    ap.add_argument("--steady-frac", type=float, default=0.5,
                    help="Fracción final del tiempo usada como régimen (default 0.5)")
    args = ap.parse_args()
    main(args.folders, args.steady_frac)
