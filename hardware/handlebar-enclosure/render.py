import trimesh
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = "/tmp/claude-0/-home-user-clauderep/d797779c-0f4d-5939-9a1d-ef5adbf7c278/scratchpad/enclosure_v3"
body = trimesh.load(f"{OUT}/body.stl")
plate = trimesh.load(f"{OUT}/plate.stl")

BODY_COLOR = np.array([176, 138, 92]) / 255
PLATE_COLOR = np.array([28, 28, 28]) / 255

def shade(tris, base_rgb, light=np.array([-0.4, -0.5, 0.85])):
    light = light / np.linalg.norm(light)
    v0, v1, v2 = tris[:, 0], tris[:, 1], tris[:, 2]
    normals = np.cross(v1 - v0, v2 - v0)
    norms = np.linalg.norm(normals, axis=1, keepdims=True); norms[norms == 0] = 1
    normals = normals / norms
    ndotl = np.clip(normals @ light, 0, 1)
    brightness = 0.45 + 0.55 * ndotl
    return np.clip(base_rgb[None, :] * brightness[:, None], 0, 1)

def draw(ax, mesh, base_rgb, alpha=1.0):
    tris = mesh.vertices[mesh.faces]
    colors = shade(tris, base_rgb)
    ax.add_collection3d(Poly3DCollection(tris, facecolors=colors, edgecolor="#2a2015", linewidths=0.2, alpha=alpha))

def setup_axes(ax, elev, azim):
    # scale to the BODY's bounds, not body+plate - the plate's 210mm clamp
    # span is much wider than the body and would otherwise dominate the
    # frame and shrink the body/snout/fins down to near-invisibility.
    mins, maxs = body.bounds
    center = (mins + maxs) / 2
    span = (maxs - mins).max() / 2 * 1.35
    ax.set_xlim(center[0]-span, center[0]+span); ax.set_ylim(center[1]-span, center[1]+span)
    ax.set_zlim(-10, center[2]-span+2*span)
    ax.set_box_aspect([1,1,1]); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()

views = [("iso_front", 22, -50), ("iso_rear", 22, 130), ("profile", 8, -90), ("front_nose", 8, 0)]
fig = plt.figure(figsize=(16, 14)); fig.patch.set_facecolor("#eeeae2")
for i, (name, elev, azim) in enumerate(views):
    ax = fig.add_subplot(2, 2, i+1, projection="3d"); ax.set_facecolor("#eeeae2")
    draw(ax, body, BODY_COLOR); draw(ax, plate, PLATE_COLOR, 0.97)
    setup_axes(ax, elev, azim); ax.set_title(name, fontsize=13, color="#333")
plt.tight_layout()
plt.savefig(f"{OUT}/v3_4view.png", dpi=170, facecolor=fig.get_facecolor())

fig2 = plt.figure(figsize=(10,9)); fig2.patch.set_facecolor("#eeeae2")
ax2 = fig2.add_subplot(111, projection="3d"); ax2.set_facecolor("#eeeae2")
draw(ax2, body, BODY_COLOR); draw(ax2, plate, PLATE_COLOR, 0.97)
setup_axes(ax2, 22, -50)
plt.tight_layout(); plt.savefig(f"{OUT}/v3_iso.png", dpi=200, facecolor=fig2.get_facecolor())
print("done")
