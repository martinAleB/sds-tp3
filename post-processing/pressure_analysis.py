import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import csv

ENC = 0.09      # lado del recinto izquierdo (m)
EPS = 2e-5      # tolerancia espacial para "estar tocando pared" (m)

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

# def compute_pressures_from_events(times_ev, X, Y, VX, VY, N, L, R, M, out_csv: Path | None = None):
#     # Longitudes efectivas de paredes (2D)
#     len_left  = 4*ENC - L
#     len_right = 2*ENC + L

#     # Agrupar por tiempo
#     unique_t, sumL, sumR = [], [], []
#     i, E = 0, len(times_ev)
#     while i < E:
#         t = times_ev[i]
#         accL, accR = 0.0, 0.0
#         while i < E and np.isclose(times_ev[i], t):
#             x, y, vx, vy = X[i], Y[i], VX[i], VY[i]
#             # Detectar paredes tocadas
#             hits = classify_wall_and_recinto(x, y, vx, vy, L, R)
#             for orient, rec in hits:
#                 delta_p = 2.0 * M * (abs(vx) if orient == 'V' else abs(vy))
#                 if rec == 'L':
#                     accL += delta_p
#                 else:
#                     accR += delta_p
#             i += 1
#         unique_t.append(t)
#         sumL.append(accL)
#         sumR.append(accR)

#     unique_t = np.array(unique_t)
#     sumL = np.array(sumL)
#     sumR = np.array(sumR)

#     # Calcular presiones en cada intervalo [t_i, t_{i+1})
#     #dts = np.diff(unique_t)
#     dts = 1
#     P_left  = sumL[:-1] / (dts * len_left)
#     P_right = sumR[:-1] / (dts * len_right)
#     t_mid   = 0.5 * (unique_t[:-1] + unique_t[1:])

#     # Guardar CSV si se pide
#     if out_csv is not None:
#         with out_csv.open("w", newline="") as f:
#             w = csv.writer(f)
#             w.writerow(["t", "P_left", "P_right"])
#             for i in range(len(t_mid)):
#                 w.writerow([f"{t_mid[i]:.6f}", f"{P_left[i]:.8e}", f"{P_right[i]:.8e}"])

#     return t_mid, P_left, P_right

def compute_pressures_from_events(times_ev, X, Y, VX, VY, N, L, R, M, out_csv: Path | None = None):
    """
    Binning temporal con ΔT fijo (estimado automáticamente):
      - Define bins uniformes en [t_min, t_max] con ancho dt_bin.
      - Suma impulsos de choques dentro de cada bin.
      - P_left/right = impulso_acum / (dt_bin * longitud_de_pared).
    """
    # Longitudes efectivas de paredes (2D)
    len_left  = 4*ENC - L
    len_right = 2*ENC + L

    if len(times_ev) == 0:
        raise ValueError("No hay eventos de pared.")

    # Elegir dt_bin a partir de la mediana de separaciones entre tiempos únicos
    # tu = np.unique(times_ev)
    # if len(tu) >= 3:
    #     med = float(np.median(np.diff(tu)))
    #     print(med)
    #     dt_bin = max(1e-4, min(1, 50.0 * med))  # 50×mediana, limitado a [1e-4, 1] s
    #     #dt_bin = 1
    # else:
    #     dt_bin = 0.1  # fallback razonable
    dt_bin = 2

    t0 = float(times_ev.min())
    t1 = float(times_ev.max())
    nbins = max(1, int(np.ceil((t1 - t0) / dt_bin)))
    edges = t0 + np.arange(nbins + 1) * dt_bin

    accL = np.zeros(nbins)
    accR = np.zeros(nbins)

    # Acumular impulsos por bin
    for x, y, vx, vy, te in zip(X, Y, VX, VY, times_ev):
        b = int((te - t0) // dt_bin)
        if b < 0 or b >= nbins:
            continue
        hits = classify_wall_and_recinto(x, y, vx, vy, L, R)
        for orient, rec in hits:
            delta_p = 2.0 * M * (abs(vx) if orient == 'V' else abs(vy))
            if rec == 'L':
                accL[b] += delta_p
            else:
                accR[b] += delta_p

    # Presiones promediadas por bin
    P_left  = accL / (dt_bin * len_left)
    P_right = accR / (dt_bin * len_right)
    t_mid   = 0.5 * (edges[:-1] + edges[1:])

    # Guardar CSV si se pide
    if out_csv is not None:
        with out_csv.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["t", "P_left", "P_right"])
            for tc, pl, pr in zip(t_mid, P_left, P_right):
                w.writerow([f"{tc:.6f}", f"{pl:.8e}", f"{pr:.8e}"])

    return t_mid, P_left, P_right


def classify_wall_and_recinto(x, y, vx, vy, L, R):
    y0 = (ENC - L) / 2.0
    y1 = y0 + L
    hits = []

    # --- VERTICALES (igual que antes) ---
    if abs(x - R) <= EPS and vx > 0:
        hits.append(('V', 'L'))
    if abs(x - (ENC - R)) <= EPS:
        if y <= (y0 - R + EPS) or y >= (y1 + R - EPS):
            if vx < 0:
                hits.append(('V', 'L'))
    if abs(x - (2*ENC - R)) <= EPS and vx < 0:
        hits.append(('V', 'R'))

    # --- HORIZONTALES ---
    if x < ENC:
        # Recinto izquierdo → solo piso/techo globales
        if abs(y - R) <= EPS and vy > 0:
            hits.append(('H', 'L'))
        if abs(y - (ENC - R)) <= EPS and vy < 0:
            hits.append(('H', 'L'))
    else:
        # Canal → solo piso/techo canal
        if abs(y - (y0 + R)) <= EPS and vy > 0:
            hits.append(('H', 'R'))
        if abs(y - (y1 - R)) <= EPS and vy < 0:
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

    # Descartar caso
    t, P_L, P_R = t[:-1], P_L[:-1], P_R[:-1]

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