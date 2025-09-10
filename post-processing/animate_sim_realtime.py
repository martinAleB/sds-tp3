import argparse
from pathlib import Path
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, FFMpegWriter


ENCLOSURE = 0.09  # meters (box width/height)


def read_static(static_path: Path):
    with static_path.open("r") as f:
        N = int(f.readline().strip())
        L = float(f.readline().strip())
        R = float(f.readline().strip())
        M = float(f.readline().strip())
        V = float(f.readline().strip())
        T = float(f.readline().strip())
    return N, L, R, M, V, T


def read_dynamic(dynamic_path: Path, N: int):
    """Return times (F,), pos (F,N,2), vel (F,N,2).

    Tolerant parser:
    - Time line: "t", or "t count", or "t count id1 id2 ..." (IDs ignored here)
    - Particle line: "x y vx vy" or "id x y vx vy" (ID ignored)
    """
    times: List[float] = []
    positions: List[np.ndarray] = []
    velocities: List[np.ndarray] = []
    with dynamic_path.open("r") as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        t_line = lines[i].strip()
        if t_line == "":
            i += 1
            continue
        parts_time = t_line.split()
        t = float(parts_time[0])
        i += 1
        frame_pos = np.zeros((N, 2), dtype=float)
        frame_vel = np.zeros((N, 2), dtype=float)
        for p in range(N):
            if i >= len(lines):
                raise ValueError("Unexpected EOF while parsing dynamic.txt")
            parts = lines[i].split()
            if len(parts) == 4:
                x, y, vx, vy = map(float, parts)
            elif len(parts) == 5:
                _, x, y, vx, vy = parts
                x, y, vx, vy = map(float, (x, y, vx, vy))
            else:
                raise ValueError(f"Expected 4 or 5 numbers at line {i+1}, got: {lines[i]!r}")
            frame_pos[p, 0] = x
            frame_pos[p, 1] = y
            frame_vel[p, 0] = vx
            frame_vel[p, 1] = vy
            i += 1
        times.append(t)
        positions.append(frame_pos)
        velocities.append(frame_vel)

    return np.array(times), np.stack(positions), np.stack(velocities)


def create_axes(ax, L: float):
    y0 = (ENCLOSURE - L) / 2.0
    y1 = y0 + L

    # vértices del perímetro en sentido horario
    verts = [
        (0.0, 0.0),
        (ENCLOSURE, 0.0),
        (ENCLOSURE, y0),
        (2 * ENCLOSURE, y0),
        (2 * ENCLOSURE, y1),
        (ENCLOSURE, y1),
        (ENCLOSURE, ENCLOSURE),
        (0.0, ENCLOSURE),
        (0.0, 0.0),
    ]

    domain = patches.Polygon(
        verts, closed=True,
        facecolor="white", edgecolor="black",
        linewidth=1, joinstyle="miter"
    )
    ax.add_patch(domain)

    # límites y proporción
    ax.set_xlim(-0.002, 2 * ENCLOSURE + 0.002)
    ax.set_ylim(-0.002, ENCLOSURE + 0.002)
    ax.set_aspect("equal", adjustable="box")

    # eliminar ejes y etiquetas
    ax.axis("off")


def animate_realtime(folder: Path, out_name: str = "animation_rt.mp4", fps: int = 60, speed: float = 1.0):
    static_path = folder / "static.txt"
    dynamic_path = folder / "dynamic.txt"
    if not static_path.exists() or not dynamic_path.exists():
        raise FileNotFoundError(f"Expected static.txt and dynamic.txt in {folder}")

    N, L, R, M, V, T = read_static(static_path)
    times, pos, vel = read_dynamic(dynamic_path, N)

    fig, ax = plt.subplots(figsize=(8, 4))
    create_axes(ax, L)

    # Escalado del largo proporcional a |v|, mapeando la mediana a ~5% del recinto
    speeds_all = np.linalg.norm(vel.reshape(-1, 2), axis=1)
    s_med = float(np.median(speeds_all)) if speeds_all.size > 0 else 0.0
    target_len = 0.05 * ENCLOSURE
    q_scale = (s_med / target_len) if s_med > 0 else 1.0

    quiv = ax.quiver(
        pos[0, :, 0], pos[0, :, 1],
        vel[0, :, 0], vel[0, :, 1],
        angles="xy", scale_units="xy", scale=q_scale, width=0.002, pivot="tail",
        color="C0"
    )

    time_text = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top")

    # Timeline de reproducción (1 s sim ~ 1 s anim si speed=1)
    dt_play = 1.0 / float(fps)
    t_start, t_end = float(times[0]), float(times[-1])
    t_play = np.arange(t_start, t_end + 1e-12, dt_play / float(speed))

    def state_at_time(t: float):
        # Encuentra intervalo (t_{k-1}, t_k] tal que t <= t_k
        k = int(np.searchsorted(times, t, side="right"))
        if k <= 0:
            return pos[0], vel[0]
        if k >= len(times):
            return pos[-1], vel[-1]
        dt = t - times[k - 1]
        # Movimiento rectilíneo uniforme entre eventos con vel del frame anterior
        pos_t = pos[k - 1] + vel[k - 1] * dt
        vel_t = vel[k - 1]
        return pos_t, vel_t

    def init():
        p0, v0 = state_at_time(t_play[0])
        quiv.set_offsets(p0)
        quiv.set_UVC(v0[:, 0], v0[:, 1])
        time_text.set_text(f"t = {t_play[0]:.4f} s   N = {N}")
        return quiv, time_text

    def update(tcur):
        p, v = state_at_time(float(tcur))
        quiv.set_offsets(p)
        quiv.set_UVC(v[:, 0], v[:, 1])
        time_text.set_text(f"t = {tcur:.6f} s   N = {N}")
        return quiv, time_text

    anim = FuncAnimation(
        fig, update, frames=t_play, init_func=init, blit=True,
        interval=int(1000 / float(fps)), repeat=False
    )

    plt.tight_layout()
    out_path = folder / out_name
    try:
        writer = FFMpegWriter(fps=int(fps), bitrate=2400)
        anim.save(out_path, writer=writer)
    except Exception as e:
        print("Warning: Could not export MP4 (ffmpeg missing?). Showing animation instead.", e)
        plt.show()
        return
    print(f"Saved: {out_path}")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path, help="Folder containing static.txt and dynamic.txt")
    parser.add_argument("--out", type=str, default="animation_rt.mp4")
    parser.add_argument("--fps", type=int, default=60)
    parser.add_argument("--speed", type=float, default=1.0, help="1.0 = real time, >1 faster, <1 slower")
    args = parser.parse_args()
    animate_realtime(args.folder, args.out, fps=args.fps, speed=args.speed)

