import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt


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
    """
    Lee dynamic.txt y devuelve:
      - times: array (F,)
      - pos:   array (F, N, 2) con (x, y)

    Formato esperado por frame (tolerante):
      línea 1: "t" (puede venir acompañado de IDs; se toma el primer token como tiempo)
      siguientes N líneas: "x y vx vy" o "id x y vx vy" (se ignora id si está presente)
    """
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
        try:
            t = float(toks[0])
        except ValueError:
            raise ValueError(f"Línea {i+1}: esperaba tiempo al inicio, leí: {head!r}")
        i += 1

        frame_pos = np.zeros((N, 2), dtype=float)
        for p in range(N):
            if i >= len(lines):
                raise ValueError("EOF inesperado mientras se leían partículas del frame")
            parts = lines[i].split()
            if len(parts) == 4:
                x, y, vx, vy = map(float, parts)
            elif len(parts) == 5:
                # tolera "id x y vx vy"
                _, x, y, vx, vy = parts
                x, y, vx, vy = map(float, (x, y, vx, vy))
            else:
                raise ValueError(
                    f"Línea {i+1}: esperaba 4 o 5 números por partícula, leí: {lines[i]!r}"
                )
            frame_pos[p, 0] = x
            frame_pos[p, 1] = y
            i += 1

        times.append(t)
        positions.append(frame_pos)

    if not times:
        raise ValueError("dynamic.txt no contiene frames válidos")

    return np.array(times, dtype=float), np.stack(positions)


def compute_msd(positions: np.ndarray, ref_index: int = 0) -> np.ndarray:
    """
    Calcula MSD(t) = promedio sobre partículas de |r_i(t) - r_i(t0)|^2
    positions: (F, N, 2)
    ref_index: índice del frame tomado como t0
    return: msd (F,)
    """
    r0 = positions[ref_index]  # (N,2)
    disp = positions - r0  # (F,N,2)
    sq = np.sum(disp * disp, axis=2)  # (F,N)
    msd = np.mean(sq, axis=1)  # (F,)
    return msd


def linear_fit(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    """
    Ajuste lineal y ≈ a*x + b por mínimos cuadrados.
    Devuelve (a, b, E), donde E = Σ (y_i - (a x_i + b))^2.
    """
    a, b = np.polyfit(x, y, 1)
    y_hat = a * x + b
    E = float(np.sum((y - y_hat) ** 2))
    return float(a), float(b), E


def main(folder: Path, tmin: float = 1.0, tmax: float = 20.0, dim: int = 2, t0: float = 41.0):
    static_path = folder / "static.txt"
    dynamic_path = folder / "dynamic.txt"

    if not static_path.exists() or not dynamic_path.exists():
        raise FileNotFoundError(f"Faltan static.txt o dynamic.txt en {folder}")

    N, L, R, M, V, T = read_static(static_path)
    times_abs, positions = read_dynamic_positions(dynamic_path, N)

    # Elegir t0 como el primer frame con t >= t0
    idx_candidates = np.where(times_abs >= float(t0))[0]
    if idx_candidates.size == 0:
        raise ValueError(
            f"No hay datos con t >= {t0}. Máximo t disponible: {times_abs.max():.3f}"
        )
    i0 = int(idx_candidates[0])

    # Mover sistema de referencia: tiempos relativos y MSD respecto a r(t0)
    times = times_abs - times_abs[i0]
    msd = compute_msd(positions, ref_index=i0)

    # Filtrar por tmin <= t <= tmax
    tmin = float(tmin)
    tmax = float(tmax)
    if tmax <= tmin:
        raise ValueError(f"Se requiere tmax > tmin (tmin={tmin}, tmax={tmax})")
    mask = (times >= tmin) & (times <= tmax)
    if not np.any(mask):
        raise ValueError(
            f"No hay datos en el rango {tmin} <= t <= {tmax}. Rango disponible: 0 a {times.max():.3f}"
        )
    times = times[mask]
    msd = msd[mask]

    # Ajuste lineal sobre el rango filtrado
    a, b, E = linear_fit(times, msd)
    # Coeficiente de difusión en 'dim' dimensiones: MSD ≈ 2 d D t + C
    D = a / (2.0 * float(dim))
    # Reportar por consola con 3 cifras significativas
    print(f"D = {D:.3g} m^2/s")
    print(f"E = {E:.3g}")

    # Figura con panel lateral derecho para info (D y E)
    fig = plt.figure(figsize=(12, 6))
    gs = fig.add_gridspec(nrows=1, ncols=2, width_ratios=[5, 1], wspace=0.05)
    ax = fig.add_subplot(gs[0, 0])
    ax_info = fig.add_subplot(gs[0, 1])
    ax_info.axis('off')
    ax.plot(times, msd, lw=2.0, label="MSD (datos)")
    # Etiqueta del ajuste lineal con 3 cifras significativas y signo correcto
    a_str = f"{a:.3g}"
    b_sign = "-" if b < 0 else "+"
    b_str = f"{abs(b):.3g}"
    fit_label = f"Ajuste: y = {a_str} t {b_sign} {b_str}"
    ax.plot(times, a * times + b, "--", lw=2.0, label=fit_label)
    ax.set_xlabel("t [s]", fontsize=18)
    ax.set_ylabel("Desplazamiento cuadratico medio [m^2]", fontsize=18)
    ax.tick_params(axis='both', labelsize=14)
    ax.grid(True, ls=":", alpha=0.5)
    ax.legend(fontsize=14)
    # Mostrar D y E en el panel lateral (no sobre el gráfico)
    ax_info.text(
        0.0, 0.95,
        f"D = {D:.3g} m^2/s\nE = {E:#.3g}",
        ha="left", va="top", fontsize=14, transform=ax_info.transAxes
    )
    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Grafica MSD(t) para una simulación")
    ap.add_argument("folder", type=Path, help="Carpeta con static.txt y dynamic.txt")
    ap.add_argument("--tmin", type=float, default=1.0, help="Tiempo mínimo relativo desde t0 [s]")
    ap.add_argument("--tmax", type=float, default=20.0, help="Tiempo máximo relativo desde t0 [s]")
    ap.add_argument("--dim", type=int, default=2, help="Dimensionalidad para D (MSD ≈ 2*d*D*t)")
    ap.add_argument("--t0", type=float, default=41.0, help="Tiempo de referencia t0 [s]")
    args = ap.parse_args()
    main(args.folder, args.tmin, args.tmax, args.dim, args.t0)
