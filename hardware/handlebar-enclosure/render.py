import os
import trimesh, numpy as np, matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from matplotlib.patches import Ellipse
import mpl_toolkits.mplot3d.art3d as art3d

OUT = os.path.dirname(os.path.abspath(__file__))
body = trimesh.load(f"{OUT}/body.stl")
plate = trimesh.load(f"{OUT}/top_plate.stl")
base = trimesh.load(f"{OUT}/base_plate.stl")

def tessellate(mesh, max_edge=8.0):
    """Painter's-algorithm depth sorting is per-triangle centroid, so a few
    huge plate triangles sort wrong against the many small shell ones."""
    m = mesh.copy()
    v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=max_edge)
    return trimesh.Trimesh(vertices=v, faces=f, process=False)

GUNMETAL = np.array([120, 124, 132]) / 255
PLATE_C  = np.array([22, 23, 26]) / 255
BASE_C   = np.array([150, 120, 80]) / 255     # plywood-ish
RED      = np.array([235, 60, 30]) / 255
BG = "#1c1c20"

def seam_w(tris):
    c = tris.mean(axis=1)
    near = np.clip(1.0 - np.abs(c[:,1]) / 11.0, 0, 1)
    high = np.clip((c[:,2] - 10.0) / 10.0, 0, 1)
    return near * high

def shade(mesh, base_rgb, glow=False, lights=None):
    tris = mesh.vertices[mesh.faces]
    l1, l2 = lights if lights else ([-0.4,-0.5,0.85], [0.55,0.35,0.3])
    l1 = np.array(l1,float); l1/=np.linalg.norm(l1)
    l2 = np.array(l2,float); l2/=np.linalg.norm(l2)
    v0,v1,v2 = tris[:,0],tris[:,1],tris[:,2]
    n = np.cross(v1-v0, v2-v0); nn=np.linalg.norm(n,axis=1,keepdims=True); nn[nn==0]=1; n=n/nn
    b = 0.38 + 0.55*np.clip(n@l1,0,1) + 0.20*np.clip(n@l2,0,1)
    b = np.clip(b, 0.30, 1.15)
    col = np.clip(base_rgb[None,:]*b[:,None], 0, 1)
    if glow:
        w = seam_w(tris)
        col = col*(1-w[:,None]) + (RED[None,:]*(0.75+0.5*b[:,None]))*w[:,None]
    return np.clip(col,0,1)

def tri_colors(mesh, rgb, flat=False, glow=False, lights=None):
    tris = mesh.vertices[mesh.faces]
    cols = np.tile(rgb,(len(tris),1)) if flat else shade(mesh, rgb, glow, lights)
    return tris, cols

def setup(ax, elev, azim, ref):
    mins, maxs = ref.bounds
    c = (mins+maxs)/2; span=(maxs-mins).max()/2*1.02
    ax.set_xlim(c[0]-span,c[0]+span); ax.set_ylim(c[1]-span,c[1]+span)
    ax.set_zlim(c[2]-span, c[2]+span)
    ax.set_box_aspect([1,1,1]); ax.view_init(elev=elev, azim=azim); ax.set_axis_off()

def hero(name, elev, azim, label, parts):
    fig = plt.figure(figsize=(10,9.4)); fig.patch.set_facecolor(BG)
    ax = fig.add_subplot(111, projection="3d"); ax.set_facecolor(BG)
    allv = np.vstack([p[0].vertices for p in parts])
    ref = trimesh.PointCloud(allv).bounding_box
    setup(ax, elev, azim, ref)
    T, C = [], []
    for mesh, rgb, kw in parts:
        t, c = tri_colors(mesh, rgb, **kw)
        T.append(t); C.append(c)
    T = np.vstack(T); C = np.vstack(C)
    ax.add_collection3d(Poly3DCollection(T, facecolors=C, edgecolor=None,
                                          linewidths=0, antialiased=False))
    fig.text(0.5,0.035,label,ha="center",fontsize=15,color="#ccc")
    plt.subplots_adjust(left=0,right=1,top=1,bottom=0.07)
    plt.savefig(f"{OUT}/renders/enclosure_{name}.png", dpi=210, facecolor=fig.get_facecolor()); plt.close(fig)
    print("saved", name)

base = tessellate(base); plate = tessellate(plate); body = tessellate(body, 10.0)
base.apply_translation([0, 0, -0.4])   # render-only: avoids z-fighting speckle at the shell rim
shell_only = [(base, BASE_C, dict(flat=True)), (body, GUNMETAL, dict(glow=True))]
hero("corner", 22, -42, "3/4 view - shell on base plate", shell_only)
hero("front",  10,   0, "Front view", shell_only)
hero("side",    8, -90, "Side view - nose left, tail right", shell_only)
hero("mounted", 34, -42, "With bar mount plate fitted on top",
     shell_only + [(plate, PLATE_C, dict(flat=True))])
UNDER_LIGHTS = ([-0.35,-0.45,-0.82], [0.5,0.3,-0.4])
hero("under", -38, -60, "UNDERSIDE - open shell, 4 internal M4 bolt bosses",
     [(body, GUNMETAL, dict(glow=False, lights=UNDER_LIGHTS))])

body_up = body.copy(); body_up.apply_translation([0, 0, 55])
plate_up = plate.copy(); plate_up.apply_translation([0, 0, 95])
hero("exploded", 16, -48, "Exploded - base plate / shell / bar mount plate",
     [(base, BASE_C, dict(flat=True)), (body_up, GUNMETAL, dict(glow=True)),
      (plate_up, PLATE_C, dict(flat=True))])
print("done")
