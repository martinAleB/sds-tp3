import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import csv

ENC = 0.09      # lado del recinto izquierdo (m)
EPS = 2e-5      # tolerancia espacial para "estar tocando pared" (m)
DT_BIN = 0.01   # respaldo si hubiera Δt no positivos

def read_static(static_path: Path):
    with static_path.open("r") as f:
        N = int(f.readline().strip())
        L = float(f.readline().strip())
        R = float(f.readline().strip())
        M = float(f.readline().strip())
        V = float(f.readline().strip())
        T = float(f.readline().strip())
    return N, L, R, M, V, T

def map_particle_id(pid: int, N: int) -> int | None:
    if 1 <= pid <= N:
        return pid - 1
    return None


def read_collision_events(dynamic_path: Path, N: int):
    times_ev = []
    idx_ev = []
    X = []; Y = []; VX = []; VY = []

    with dynamic_path.open("r") as f:
        lines = f.readlines()

    i = 0
    frame_idx = 0
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
        # IDs listados en este frame
        raw_ids = []
        for tok in toks[1:]:
            try:
                raw_ids.append(int(tok))
            except ValueError:
                pass
        i += 1

        # Leer N partículas
        frame_pos = []
        frame_vel = []
        for p in range(N):
            if i >= len(lines):
                raise ValueError(f"EOF inesperado leyendo partícula {p} en frame {frame_idx}")
            parts = lines[i].split()
            if len(parts) == 4:
                x, y, vx, vy = map(float, parts)
            elif len(parts) == 5:  # tolera "id x y vx vy"
                _, x, y, vx, vy = parts
                x, y, vx, vy = map(float, (x, y, vx, vy))
            else:
                raise ValueError(f"Línea {i+1}: esperaba 4 o 5 números, leí: {lines[i]!r}")
            frame_pos.append((x, y))
            frame_vel.append((vx, vy))
            i += 1

        # Para cada ID listado, agregar un evento con el estado de esa partícula
        for pid in raw_ids:
            idx = map_particle_id(pid, N)
            if idx is None:
                continue
            x, y = frame_pos[idx]
            vx, vy = frame_vel[idx]
            times_ev.append(t)
            idx_ev.append(idx)
            X.append(x); Y.append(y); VX.append(vx); VY.append(vy)
        frame_idx += 1

    return (np.array(times_ev, float),
            np.array(idx_ev, int),
            np.array(X, float),
            np.array(Y, float),
            np.array(VX, float),
            np.array(VY, float))

def compute_pressures_from_events(times_ev, X, Y, VX, VY, N, L, R, M, out_csv: Path | None = None):
    # Longitudes efectivas de paredes (2D)
    len_left  = 4*ENC - L
    len_right = 2*ENC + L

    # Agrupar por tiempo
    unique_t, sumL, sumR = [], [], []
    i, E = 0, len(times_ev)
    while i < E:
        t = times_ev[i]
        accL, accR = 0.0, 0.0
        while i < E and np.isclose(times_ev[i], t):
            x, y, vx, vy = X[i], Y[i], VX[i], VY[i]
            # Detectar paredes tocadas
            hits = classify_wall_and_recinto(x, y, vx, vy, L, R)
            for orient, rec in hits:
                delta_p = 2.0 * M * (abs(vx) if orient == 'V' else abs(vy))
                if rec == 'L':
                    accL += delta_p
                else:
                    accR += delta_p
            i += 1
        unique_t.append(t)
        sumL.append(accL)
        sumR.append(accR)

    unique_t = np.array(unique_t)
    sumL = np.array(sumL)
    sumR = np.array(sumR)

    # Calcular presiones en cada intervalo [t_i, t_{i+1})
    dts = np.diff(unique_t)
    P_left  = sumL[:-1] / (dts * len_left)
    P_right = sumR[:-1] / (dts * len_right)
    t_mid   = 0.5 * (unique_t[:-1] + unique_t[1:])

    # Guardar CSV si se pide
    if out_csv is not None:
        with out_csv.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t", "P_left", "P_right"])
            for i in range(len(t_mid)):
                w.writerow([f"{t_mid[i]:.6f}", f"{P_left[i]:.8e}", f"{P_right[i]:.8e}"])

    return t_mid, P_left, P_right

def classify_wall_and_recinto(x, y, vx, vy, L, R):
    y0 = (ENC - L) / 2.0
    y1 = y0 + L
    hits = []

    # --- VERTICALES ---
    # x=0 (pared izquierda de la caja)
    if abs(x - R) <= EPS and vx > 0:
        hits.append(('V', 'L'))

    # x=ENC (pared interna del cuadrado, fuera de la abertura)
    if abs(x - (ENC - R)) <= EPS:
        if y <= (y0 - R + EPS) or y >= (y1 + R - EPS):
            if vx < 0:
                hits.append(('V', 'L'))

    # x=2*ENC (pared derecha del canal)
    if abs(x - (2*ENC - R)) <= EPS and vx < 0:
        hits.append(('V', 'R'))

    # --- HORIZONTALES ---
    # y=0 (piso global)
    if abs(y - R) <= EPS and vy > 0:
        hits.append(('H', 'L' if x < ENC else 'R'))

    # y=ENC (techo global)
    if abs(y - (ENC - R)) <= EPS and vy < 0:
        hits.append(('H', 'L' if x < ENC else 'R'))

    # piso canal
    if x >= ENC and abs(y - (y0 + R)) <= EPS and vy > 0:
        hits.append(('H', 'R'))

    # techo canal
    if x >= ENC and abs(y - (y1 - R)) <= EPS and vy < 0:
        hits.append(('H', 'R'))

    return hits


def main(folder: Path):
    static_path = folder / "static.txt"
    dynamic_path = folder / "dynamic.txt"

    if not static_path.exists() or not dynamic_path.exists():
        raise FileNotFoundError(f"Faltan static.txt o dynamic.txt en {folder}")

    # Cargar parámetros y eventos
    N, L, R, M, V, T = read_static(static_path)
    times_ev, idx_ev, X, Y, VX, VY = read_collision_events(dynamic_path, N)

    # Calcular presiones
    t, P_L, P_R = compute_pressures_from_events(times_ev, X, Y, VX, VY, N, L, R, M, folder / "pressures.csv")

    # Graficar ambas presiones en un solo plot
    plt.figure(figsize=(10, 5))
    plt.plot(t, P_L, label="Recinto izquierdo", lw=1.4)
    plt.plot(t, P_R, label="Recinto derecho (pasillo)", lw=1.4)
    plt.xlabel("t [s]")
    plt.ylabel("P [N/m]")
    #plt.title("Presión vs tiempo en ambos recintos")
    plt.legend()
    plt.grid(True, ls=":", alpha=0.5)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder", type=Path, help="Carpeta con static.txt y dynamic.txt")
    args = ap.parse_args()
    main(args.folder)