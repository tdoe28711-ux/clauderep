import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = "/tmp/claude-0/-home-user-clauderep/d797779c-0f4d-5939-9a1d-ef5adbf7c278/scratchpad/enclosure"

body = trimesh.load(f"{OUT}/body.stl")
plate = trimesh.load(f"{OUT}/top_plate.stl")

BODY_COLOR = "#b08a5c"   # tan/bronze, echoing the reference photo's base
PLATE_COLOR = "#1c1c1c"  # black top plate

def shade(tris, base_rgb, light=np.array([-0.4, -0.5, 0.85])):
    light = light / np.linalg.norm(light)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    normals = np.cross(v1 - v0, v2 - v0)
    norms = np.linalg.norm(normals, axis=1, keepdims=True)
    norms[norms == 0] = 1
    normals = normals / norms
    ndotl = np.clip(normals @ light, 0, 1)
    brightness = 0.45 + 0.55 * ndotl  # ambient floor + diffuse
    base = np.array(base_rgb)
    colors = np.clip(base[None, :] * brightness[:, None], 0, 1)
    return colors

def draw(ax, mesh, hexcolor, alpha=1.0, edge="#2a2015", lw=0.2):
    tris = mesh.vertices[mesh.faces]
    base_rgb = np.array([int(hexcolor[i:i+2], 16) / 255 for i in (1, 3, 5)])
    colors = shade(tris, base_rgb)
    coll = Poly3DCollection(tris, facecolors=colors, edgecolor=edge, linewidths=lw, alpha=alpha)
    ax.add_collection3d(coll)

def setup_axes(ax, elev, azim):
    all_v = np.vstack([body.vertices, plate.vertices])
    mins, maxs = all_v.min(axis=0), all_v.max(axis=0)
    center = (mins + maxs) / 2
    span = (maxs - mins).max() / 2 * 1.1
    ax.set_xlim(center[0] - span, center[0] + span)
    ax.set_ylim(center[1] - span, center[1] + span)
    ax.set_zlim(-10, center[2] - span + 2*span)
    ax.set_box_aspect([1, 1, 1])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()

views = [
    ("iso", 24, -35),
    ("front (nose-on)", 10, 0),
    ("side profile", 10, -90),
    ("top", 88, -90),
]

fig = plt.figure(figsize=(16, 14))
fig.patch.set_facecolor("#eeeae2")
for i, (name, elev, azim) in enumerate(views):
    ax = fig.add_subplot(2, 2, i + 1, projection="3d")
    ax.set_facecolor("#eeeae2")
    draw(ax, body, BODY_COLOR)
    draw(ax, plate, PLATE_COLOR, alpha=0.97)
    setup_axes(ax, elev, azim)
    ax.set_title(name, fontsize=13, color="#333")

plt.tight_layout()
plt.savefig(f"{OUT}/enclosure_4view.png", dpi=170, facecolor=fig.get_facecolor())
print("saved 4-view render")

# a bigger standalone iso shot
fig2 = plt.figure(figsize=(10, 9))
fig2.patch.set_facecolor("#eeeae2")
ax2 = fig2.add_subplot(111, projection="3d")
ax2.set_facecolor("#eeeae2")
draw(ax2, body, BODY_COLOR)
draw(ax2, plate, PLATE_COLOR, alpha=0.97)
setup_axes(ax2, 24, -35)
plt.tight_layout()
plt.savefig(f"{OUT}/enclosure_iso.png", dpi=200, facecolor=fig2.get_facecolor())
print("saved iso render")
