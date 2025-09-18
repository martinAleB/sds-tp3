# DEPRECATED... USE REALTIME VERSION INSTEAD (animate_sim_realtime.py)
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation, FFMpegWriter
from typing import Tuple, List

ENCLOSURE = 0.09

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
    """Return times (F,), pos (F,N,2), vel (F,N,2)"""
    times: List[float] = []
    positions: List[np.ndarray] = []
    velocities: List[np.ndarray] = []
    with dynamic_path.open("r") as f:
        lines = f.readlines()

    i = 0
    F = 0
    while i < len(lines):
        line = lines[i].split(" ")
        t = float(line[0])
        i += 1
        frame_pos = np.zeros((N, 2), dtype=float)
        frame_vel = np.zeros((N, 2), dtype=float)
        for p in range(N):
            if i >= len(lines):
                raise ValueError("Unexpected EOF while parsing dynamic.txt")
            x, y, vx, vy = map(float, lines[i].split())
            frame_pos[p, 0] = x
            frame_pos[p, 1] = y
            frame_vel[p, 0] = vx
            frame_vel[p, 1] = vy
            i += 1
        times.append(t)
        positions.append(frame_pos)
        velocities.append(frame_vel)
        F += 1

    return np.array(times), np.stack(positions), np.stack(velocities)

def create_axes(ax, L: float):
    y0 = (ENCLOSURE - L) / 2.0
    y1 = y0 + L

    verts = [
        (0.0, 0.0),                 
        (ENCLOSURE, 0.0),           
        (ENCLOSURE, y0),            
        (2*ENCLOSURE, y0),          
        (2*ENCLOSURE, y1),      
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

    ax.set_xlim(-0.002, 2*ENCLOSURE + 0.002)
    ax.set_ylim(-0.002, ENCLOSURE + 0.002)
    ax.set_aspect("equal", adjustable="box")

    ax.axis("off")

def main(folder: Path, out_name: str = "animation.mp4"):
    static_path = folder / "static.txt"
    dynamic_path = folder / "dynamic.txt"
    if not static_path.exists() or not dynamic_path.exists():
        raise FileNotFoundError(f"Expected static.txt and dynamic.txt in {folder}")

    N, L, R, M, V, T = read_static(static_path)
    times, pos, vel = read_dynamic(dynamic_path, N)
    F = len(times)

    fig, ax = plt.subplots(figsize=(8, 4))
    create_axes(ax, L)

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

    def init():
        quiv.set_offsets(pos[0])
        quiv.set_UVC(vel[0, :, 0], vel[0, :, 1])
        time_text.set_text(f"t = {times[0]:.4f} s")
        return quiv, time_text

    def update(frame):
        quiv.set_offsets(pos[frame])
        quiv.set_UVC(vel[frame, :, 0], vel[frame, :, 1])
        time_text.set_text(f"t = {times[frame]:.6f} s")
        return quiv, time_text

    anim = FuncAnimation(fig, update, frames=F, init_func=init, blit=True, interval=16)
    plt.tight_layout()
    out_path = folder / out_name
    try:
        writer = FFMpegWriter(fps=60, bitrate=2400)
        anim.save(out_path, writer=writer)
    except Exception as e:
        print("Warning: Could not export MP4 (ffmpeg missing?). Showing animation instead.", e)
        plt.show()
        return
    print(f"Saved: {out_path}")
    plt.show()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", type=Path, help="Folder containing static.txt and dynamic.txt")
    parser.add_argument("--out", type=str, default="animation.mp4")
    args = parser.parse_args()
    main(args.folder, args.out)
