import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Ellipse
import mpl_toolkits.mplot3d.art3d as art3d

OUT = "/tmp/claude-0/-home-user-clauderep/d797779c-0f4d-5939-9a1d-ef5adbf7c278/scratchpad/enclosure_v5"
body = trimesh.load(f"{OUT}/body.stl")
plate = trimesh.load(f"{OUT}/plate.stl")

GUNMETAL = np.array([120, 124, 132]) / 255
GUNMETAL_DARK = np.array([22, 23, 26]) / 255
RED_GLOW = np.array([235, 60, 30]) / 255
BG = "#1c1c20"

def seam_weight(tris):
    """How close each triangle is to the Y=0 centerline AND near the top of
    the body (the V-ridge groove) - used to blend in the red emissive seam.
    Centered groove vertices sit at y=0 by construction; faces touching
    them span from y=0 out a few mm, so weight by how small the face's
    average |y| is relative to its average z (only near the top, not the
    flat bottom edge which also touches y=0 at the equator seam)."""
    centroids = tris.mean(axis=1)
    y = np.abs(centroids[:, 1])
    z = centroids[:, 2]
    near_center = np.clip(1.0 - y / 11.0, 0.0, 1.0)   # 1 right at y=0, 0 by y=11mm
    high_enough = np.clip((z - 10.0) / 10.0, 0.0, 1.0)  # most of the ridge, not the floor seam
    return near_center * high_enough

def shade(mesh, base_rgb, light1, light2, glow=False):
    tris = mesh.vertices[mesh.faces]
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    n = np.cross(v1 - v0, v2 - v0)
    nn = np.linalg.norm(n, axis=1, keepdims=True); nn[nn == 0] = 1
    n = n / nn
    key = np.clip(n @ light1, 0, 1)
    fill = np.clip(n @ light2, 0, 1)
    brightness = 0.38 + 0.55 * key + 0.20 * fill
    brightness = np.clip(brightness, 0.30, 1.15)
    colors = np.clip(base_rgb[None, :] * brightness[:, None], 0, 1)
    if glow:
        w = seam_weight(tris)
        emissive = RED_GLOW[None, :] * (0.75 + 0.5 * brightness[:, None])
        colors = colors * (1 - w[:, None]) + emissive * w[:, None]
    colors = np.clip(colors, 0, 1)
    return colors

def draw(ax, mesh, base_rgb, flat=False, alpha=1.0, glow=False):
    tris = mesh.vertices[mesh.faces]
    light1 = np.array([-0.4, -0.5, 0.85]); light1 /= np.linalg.norm(light1)
    light2 = np.array([0.55, 0.35, 0.3]); light2 /= np.linalg.norm(light2)
    if flat:
        colors = np.tile(base_rgb, (len(tris), 1))
    else:
        colors = shade(mesh, base_rgb, light1, light2, glow=glow)
    coll = Poly3DCollection(tris, facecolors=colors, edgecolor=None, linewidths=0,
                             alpha=alpha, antialiased=False)
    ax.add_collection3d(coll)

def draw_ground_shadow(ax, mesh, z0):
    mins, maxs = mesh.bounds
    cx, cy = (mins[0] + maxs[0]) / 2, (mins[1] + maxs[1]) / 2
    rx, ry = (maxs[0] - mins[0]) / 2 * 1.08, (maxs[1] - mins[1]) / 2 * 1.08
    for k, a in [(1.25, 0.25), (1.1, 0.32), (1.0, 0.4)]:
        p = Ellipse((cx, cy), 2 * rx * k, 2 * ry * k, facecolor="#000000", alpha=a, edgecolor=None)
        ax.add_patch(p)
        art3d.pathpatch_2d_to_3d(p, z=z0, zdir="z")

def setup_axes(ax, elev, azim):
    mins, maxs = body.bounds
    center = (mins + maxs) / 2
    span = (maxs - mins).max() / 2 * 1.25
    ax.set_xlim(center[0]-span, center[0]+span)
    ax.set_ylim(center[1]-span, center[1]+span)
    floor_z = mins[2] - 1.5
    ax.set_zlim(floor_z, floor_z + 2*span)
    ax.set_box_aspect([1,1,1]); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()
    return floor_z

def hero(name, elev, azim, label):
    fig = plt.figure(figsize=(10, 9.4)); fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111, projection="3d"); ax.set_facecolor(BG)
    floor_z = setup_axes(ax, elev, azim)
    draw_ground_shadow(ax, body, floor_z)
    draw(ax, body, GUNMETAL, glow=True)
    draw(ax, plate, GUNMETAL_DARK, flat=True, alpha=0.99)
    fig.text(0.5, 0.035, label, ha="center", fontsize=15, color="#ccc")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0.07)
    plt.savefig(f"{OUT}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("saved", name)

hero("v5_corner", 24, -42, "3/4 view")
hero("v5_front",  10,   0, "Front view")
hero("v5_side",   8,  -90, "Side view - nose left, tail right")
hero("v5_top",    85, -90, "Top view")
print("done")
