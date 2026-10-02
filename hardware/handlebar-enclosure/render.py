import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Ellipse
import mpl_toolkits.mplot3d.art3d as art3d

OUT = "/tmp/claude-0/-home-user-clauderep/d797779c-0f4d-5939-9a1d-ef5adbf7c278/scratchpad/enclosure_v3"
body = trimesh.load(f"{OUT}/body.stl")
plate = trimesh.load(f"{OUT}/plate.stl")

BODY_COLOR = np.array([201, 156, 99]) / 255
PLATE_COLOR = np.array([32, 32, 35]) / 255
BG = "#e9e4da"

def quad_pair_shade(mesh, base_rgb, light1, light2):
    """Shade by averaging each pair of triangles that make up one loft quad
    (faces are emitted in (v0,v1,v2),(v0,v2,v3) pairs by build_hull) so a
    nominally-flat quad never shows a visible seam between its two tris.
    Falls back to per-triangle shading for any leftover odd face out."""
    tris = mesh.vertices[mesh.faces]
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    n = np.cross(v1 - v0, v2 - v0)
    nn = np.linalg.norm(n, axis=1, keepdims=True); nn[nn == 0] = 1
    n = n / nn
    key = np.clip(n @ light1, 0, 1)
    fill = np.clip(n @ light2, 0, 1)
    brightness = 0.42 + 0.70 * key + 0.18 * fill
    nfaces = len(mesh.faces)
    pairs = nfaces // 2 * 2
    avg = (brightness[0:pairs:2] + brightness[1:pairs:2]) / 2.0
    brightness[0:pairs:2] = avg
    brightness[1:pairs:2] = avg
    brightness = np.clip(brightness, 0.28, 1.1)
    return np.clip(base_rgb[None, :] * brightness[:, None], 0, 1)

def draw(ax, mesh, base_rgb, flat=False, alpha=1.0):
    tris = mesh.vertices[mesh.faces]
    light1 = np.array([-0.35, -0.55, 0.85]); light1 /= np.linalg.norm(light1)
    light2 = np.array([0.6, 0.3, 0.35]); light2 /= np.linalg.norm(light2)
    if flat:
        # plate: uniform matte color, no per-triangle lighting at all -
        # it's a flat slab, shading it just invites seam artifacts.
        colors = np.tile(base_rgb, (len(tris), 1))
    else:
        colors = quad_pair_shade(mesh, base_rgb, light1, light2)
    coll = Poly3DCollection(tris, facecolors=colors, edgecolor=None, linewidths=0,
                             alpha=alpha, antialiased=False)
    ax.add_collection3d(coll)

def draw_ground_shadow(ax, mesh, z0, center, span):
    """A simple soft drop shadow: the mesh's own footprint, flattened and
    blurred via several overlapping translucent ellipses, sitting just
    below the model so it reads as resting on a surface."""
    mins, maxs = mesh.bounds
    cx, cy = (mins[0] + maxs[0]) / 2, (mins[1] + maxs[1]) / 2
    rx, ry = (maxs[0] - mins[0]) / 2 * 1.08, (maxs[1] - mins[1]) / 2 * 1.08
    for k, a in [(1.25, 0.05), (1.1, 0.07), (1.0, 0.10)]:
        p = Ellipse((cx, cy), 2 * rx * k, 2 * ry * k, facecolor="#2a2015", alpha=a, edgecolor=None)
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
    return center, span, floor_z

def hero(name, elev, azim, label):
    fig = plt.figure(figsize=(10, 9.4)); fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111, projection="3d"); ax.set_facecolor(BG)
    center, span, floor_z = setup_axes(ax, elev, azim)
    draw_ground_shadow(ax, body, floor_z, center, span)
    draw(ax, body, BODY_COLOR)
    draw(ax, plate, PLATE_COLOR, flat=True, alpha=0.99)
    fig.text(0.5, 0.035, label, ha="center", fontsize=15, color="#3a3a3a")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0.07)
    plt.savefig(f"{OUT}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    print("saved", name)

hero("v2_corner", 20, -40, "3/4 view")
hero("v2_side",   10, -90, "Side view  -  nose (snout) on the left, tail + fins on the right")
hero("v2_front",   8,   0, "Front view  -  looking at the nose, clamp plate overhead")
hero("v2_rear",    14, 100, "Rear 3/4 view  -  showing the two dorsal fins and cable port")
print("done")
