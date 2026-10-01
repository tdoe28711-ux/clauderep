"""
Handlebar Demo Enclosure v3 - builds directly into the active Rhino document.

Run this INSIDE Rhino (ScriptEditor / EditPythonScript), not as a standalone
.py - it uses RhinoCommon (Rhino.Geometry) and scriptcontext, which only
exist inside Rhino's own Python. No pip installs needed.

Matches generate_enclosure.py exactly: slim snout -> brow flare (two angled
facets with a centerline groove) -> sharp horn -> flat pad -> twin dorsal
fins -> tail taper -> blunt transom. Rear cable port, bezeled USB port on
the left wall, separate chamfered top plate (110mm along the body, 210mm
across it for the bar clamps).

Edit STATIONS to change the taper/facet shape, then re-run (it clears its
own layers first so re-running is safe).
"""
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System.Drawing as sd
import math

# ---- envelope ---------------------------------------------------------
L = 190.0
PAD_Z = 59.0
PAD_X0, PAD_X1 = 45.0, 145.0
WALL_T = 3.0

# (x, bottom_hw, shoulder_hw, shoulder_z, ridge_hw, apex_z, groove)
STATIONS = [
    (0.0,    8, 11,  7,  4, 14, 0.0),
    (14.0,  11, 15,  9,  6, 18, 1.5),
    (25.0,  13, 18, 10,  7, 22, 3.0),
    (35.0,  44, 58, 23, 18, 58, 12.0),
    (40.0,  45, 58, 23,  4, 68,  2.0),
    (45.0,  46, 58, 23, 40, 59,  0.0),
    (145.0, 46, 58, 23, 40, 59,  0.0),
    (170.0, 46, 58, 23, 40, 59,  0.0),
    (182.0, 28, 36, 18, 14, 34,  0.0),
    (190.0, 20, 24, 15,  9, 24,  0.0),
]

INNER_X_RANGE = (35.0, 170.0)
FIN_SPECS = [(150.0, 12.0), (162.0, 15.0)]   # (x_center, proud_height) - rear flank only
PORT_W, PORT_H, PORT_D = 16.0, 11.0, 14.0
USB_W, USB_H = 14.0, 10.0
USB_X, USB_Z = 62.0, 20.0
PLATE_X, PLATE_Y, PLATE_T, PLATE_CHAMFER = 110.0, 210.0, 6.0, 10.0

# ---- geometry helpers ---------------------------------------------------
def hept_pts(bw, sw, sz, rw, az, groove, floor_z=0.0):
    """7-pt profile: bottom-L, bottom-R, shoulder-R, ridge-R, groove-center, ridge-L, shoulder-L."""
    return [(-bw, floor_z), (bw, floor_z), (sw, sz), (rw, az), (0.0, az - groove), (-rw, az), (-sw, sz)]

def build_hull_mesh(stations, floor_z=0.0):
    pps = 7
    mesh = rg.Mesh()
    for (x, bw, sw, sz, rw, az, groove) in stations:
        for (y, z) in hept_pts(bw, sw, sz, rw, az, groove, floor_z):
            mesh.Vertices.Add(x, y, z)
    n = len(stations)
    for i in range(n - 1):
        a0, a1 = i * pps, (i + 1) * pps
        for k in range(pps):
            k2 = (k + 1) % pps
            v0, v1, v2, v3 = a0 + k, a0 + k2, a1 + k2, a1 + k
            mesh.Faces.AddFace(v0, v1, v2)
            mesh.Faces.AddFace(v0, v2, v3)
    nose0 = 0
    for k in range(1, pps - 1):
        mesh.Faces.AddFace(nose0, nose0 + k + 1, nose0 + k)
    tail0 = (n - 1) * pps
    for k in range(1, pps - 1):
        mesh.Faces.AddFace(tail0, tail0 + k, tail0 + k + 1)
    mesh.UnifyNormals()
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh

def box_mesh(cx, cy, cz, dx, dy, dz):
    plane = rg.Plane(rg.Point3d(cx, cy, cz), rg.Vector3d.ZAxis)
    box = rg.Box(plane, rg.Interval(-dx / 2, dx / 2), rg.Interval(-dy / 2, dy / 2), rg.Interval(-dz / 2, dz / 2))
    return rg.Mesh.CreateFromBox(box, 1, 1, 1)

def extrude_xy_polygon(pts_xy, z0, z1, offset=(0.0, 0.0, 0.0)):
    n = len(pts_xy)
    ox, oy, oz = offset
    mesh = rg.Mesh()
    for (x, y) in pts_xy:
        mesh.Vertices.Add(x + ox, y + oy, z0 + oz)
    for (x, y) in pts_xy:
        mesh.Vertices.Add(x + ox, y + oy, z1 + oz)
    for k in range(n):
        k2 = (k + 1) % n
        b0, b1, t1, t0 = k, k2, k2 + n, k + n
        mesh.Faces.AddFace(b0, b1, t1)
        mesh.Faces.AddFace(b0, t1, t0)
    cx_ = sum(p[0] for p in pts_xy) / n
    cy_ = sum(p[1] for p in pts_xy) / n
    bc = mesh.Vertices.Count
    mesh.Vertices.Add(cx_ + ox, cy_ + oy, z0 + oz)
    for k in range(n):
        k2 = (k + 1) % n
        mesh.Faces.AddFace(bc, k2, k)
    tc = mesh.Vertices.Count
    mesh.Vertices.Add(cx_ + ox, cy_ + oy, z1 + oz)
    for k in range(n):
        k2 = (k + 1) % n
        mesh.Faces.AddFace(tc, n + k, n + k2)
    mesh.UnifyNormals()
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh

def chamfered_rect_pts(length, width, chamfer):
    hl, hw = length / 2.0, width / 2.0
    return [
        (-hl + chamfer, -hw), (hl - chamfer, -hw), (hl, -hw + chamfer),
        (hl, hw - chamfer), (hl - chamfer, hw), (-hl + chamfer, hw),
        (-hl, hw - chamfer), (-hl, -hw + chamfer),
    ]

def inset(v, t, min_v=6.0):
    return max(v - t, min_v)

def interp_station(x):
    xs = [s[0] for s in STATIONS]
    if x <= xs[0]:
        return STATIONS[0][1:6]
    if x >= xs[-1]:
        return STATIONS[-1][1:6]
    for i in range(len(STATIONS) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            a, b = STATIONS[i][1:6], STATIONS[i + 1][1:6]
            return tuple(a[j] + t * (b[j] - a[j]) for j in range(5))
    return STATIONS[-1][1:6]

def build_dorsal_fin(x_center, proud_height, base_half=6.0, apex_back_offset=2.5,
                      thick_half=3.0, embed=1.5):
    bw, sw, sz, rw, az = interp_station(x_center)
    base_z = az - embed
    apex_z = az + proud_height
    x_front, x_back = x_center - base_half, x_center + base_half
    x_apex = x_center + apex_back_offset
    pts = [
        rg.Point3d(x_front, -thick_half, base_z), rg.Point3d(x_back, -thick_half, base_z), rg.Point3d(x_apex, -thick_half, apex_z),
        rg.Point3d(x_front,  thick_half, base_z), rg.Point3d(x_back,  thick_half, base_z), rg.Point3d(x_apex,  thick_half, apex_z),
    ]
    mesh = rg.Mesh()
    for p in pts:
        mesh.Vertices.Add(p)
    # two triangular end caps + three side quads (triangular prism, 6 verts: 0,1,2 front face / 3,4,5 back face)
    mesh.Faces.AddFace(0, 1, 2)
    mesh.Faces.AddFace(3, 5, 4)
    mesh.Faces.AddFace(0, 3, 4); mesh.Faces.AddFace(0, 4, 1)
    mesh.Faces.AddFace(1, 4, 5); mesh.Faces.AddFace(1, 5, 2)
    mesh.Faces.AddFace(2, 5, 3); mesh.Faces.AddFace(2, 3, 0)
    mesh.UnifyNormals()
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    front_deg = math.degrees(math.atan2(base_half + apex_back_offset, proud_height + embed))
    back_deg = math.degrees(math.atan2(base_half - apex_back_offset, proud_height + embed))
    print("fin@x=%.0f: proud=%.1fmm front=%.1fdeg back=%.1fdeg (limit 45)" % (x_center, proud_height, front_deg, back_deg))
    return mesh

def boolean_diff(mesh_a, mesh_b, label):
    result = list(rg.Mesh.CreateBooleanDifference([mesh_a], [mesh_b]))
    if len(result) == 0:
        print("WARNING: boolean difference failed for " + label + " - keeping previous mesh")
        return mesh_a
    merged = result[0]
    for extra in result[1:]:
        merged.Append(extra)
    return merged

def boolean_union(mesh_a, mesh_b, label):
    result = list(rg.Mesh.CreateBooleanUnion([mesh_a, mesh_b]))
    if len(result) == 0:
        print("WARNING: boolean union failed for " + label + " - keeping previous mesh")
        return mesh_a
    merged = result[0]
    for extra in result[1:]:
        merged.Append(extra)
    return merged

# ---- build outer hull + hollow it ---------------------------------------
hull = build_hull_mesh(STATIONS)

inner_stations = [
    (x, inset(bw, WALL_T), inset(sw, WALL_T), max(sz - WALL_T, 2.0), inset(rw, WALL_T), az - WALL_T, 0.0)
    for (x, bw, sw, sz, rw, az, groove) in STATIONS
    if INNER_X_RANGE[0] <= x <= INNER_X_RANGE[1]
]
inner_hull = build_hull_mesh(inner_stations, floor_z=-3.0)
shell = boolean_diff(hull, inner_hull, "hollow midsection")

cable_port = box_mesh(L - PORT_D / 2 + 2, 0, 1.0 + PORT_H / 2, PORT_D, PORT_W, PORT_H)
shell = boolean_diff(shell, cable_port, "rear cable port")

# USB bezel: compute the real outer-hull half-width at (USB_X, USB_Z) so the
# bezel genuinely stands proud and the cut fully penetrates the wall.
bw_u, sw_u, sz_u, rw_u, az_u = interp_station(USB_X)
if USB_Z <= sz_u:
    surf_hw = bw_u + (USB_Z / sz_u) * (sw_u - bw_u)
else:
    surf_hw = sw_u + (USB_Z - sz_u) / (az_u - sz_u) * (rw_u - sw_u)
proud = 2.0
bezel_outer_face = -(surf_hw + proud)
bezel_inner_face = -(surf_hw - 2.5)
bezel_cy = (bezel_outer_face + bezel_inner_face) / 2.0
bezel_depth = abs(bezel_inner_face - bezel_outer_face)
bezel = box_mesh(USB_X, bezel_cy, USB_Z, 20.0, bezel_depth, 16.0)
shell = boolean_union(shell, bezel, "usb bezel")

cut_outer = bezel_outer_face - 1.0
cut_inner = -(surf_hw - 10.0)
cut_cy = (cut_outer + cut_inner) / 2.0
cut_depth = abs(cut_inner - cut_outer)
usb_cut = box_mesh(USB_X, cut_cy, USB_Z, USB_W, cut_depth, USB_H)
shell = boolean_diff(shell, usb_cut, "usb cutout")

for (fx, fh) in FIN_SPECS:
    fin = build_dorsal_fin(fx, fh)
    shell = boolean_union(shell, fin, "dorsal fin @ x=%.0f" % fx)

# ---- top plate: 110mm along body-X (sits on the 100mm pad), 210mm along Y
# (spans across the bar for two clamps ~190mm apart) ----------------------
plate_pts = chamfered_rect_pts(PLATE_X, PLATE_Y, PLATE_CHAMFER)
plate_cx = (PAD_X0 + PAD_X1) / 2.0
plate = extrude_xy_polygon(plate_pts, PAD_Z, PAD_Z + PLATE_T, offset=(plate_cx, 0.0, 0.0))

# ---- push into the Rhino document ----------------------------------------
def ensure_layer(name, color):
    idx = sc.doc.Layers.FindByFullPath(name, True)
    if idx < 0:
        layer = Rhino.DocObjects.Layer()
        layer.Name = name
        layer.Color = color
        idx = sc.doc.Layers.Add(layer)
    else:
        sc.doc.Layers[idx].Color = color
    return idx

body_layer = ensure_layer("Enclosure Body", sd.Color.FromArgb(176, 138, 92))
plate_layer = ensure_layer("Top Plate", sd.Color.FromArgb(28, 28, 28))

body_attr = Rhino.DocObjects.ObjectAttributes()
body_attr.LayerIndex = body_layer
body_attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer

plate_attr = Rhino.DocObjects.ObjectAttributes()
plate_attr.LayerIndex = plate_layer
plate_attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer

sc.doc.Objects.AddMesh(shell, body_attr)
sc.doc.Objects.AddMesh(plate, plate_attr)
sc.doc.Views.Redraw()

print("Body mesh: valid=%s  volume=%.1f cm^3  (~%.0fg PLA)" %
      (shell.IsValid, shell.Volume() / 1000.0, shell.Volume() / 1000.0 * 1.24))
print("Top plate: valid=%s  volume=%.1f cm^3  (~%.0fg if printed - plywood/acrylic recommended instead)" %
      (plate.IsValid, plate.Volume() / 1000.0, plate.Volume() / 1000.0 * 1.24))
print("Done - look on layers 'Enclosure Body' and 'Top Plate'.")
