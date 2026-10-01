"""
Handlebar Demo Enclosure - builds directly into the active Rhino document.

Run this INSIDE Rhino (ScriptEditor or _EditPythonScript), not as a
standalone .py - it uses RhinoCommon (Rhino.Geometry) and scriptcontext,
which only exist inside Rhino's own Python. No pip installs needed.

What it does:
  1. Lofts a faceted hex cross-section along the length into the outer hull
  2. Builds a smaller inset copy and mesh-booleans it out to hollow the
     midsection to a ~3mm wall
  3. Cuts the rear cable port and side USB port
  4. Builds a separate chamfered top plate for the bar clamps
  5. Adds both to the document on their own colored layers

Edit the STATIONS table near the top to change the taper / facet shape,
then re-run (it clears its own layers first so re-running is safe).
"""
import Rhino.Geometry as rg
import scriptcontext as sc
import System.Drawing as sd

# ---- envelope ------------------------------------------------------------
L = 190.0        # length, X: 0 (nose) -> L (tail)
PAD_Z = 59.0     # top mounting pad height
PAD_X0, PAD_X1 = 45.0, 145.0   # pad runs 100mm long (80mm wide via ridge_hw=40)
WALL_T = 3.0     # nominal wall thickness (spec: 2.4-3.0mm)

# columns: x, bottom_hw, shoulder_hw, shoulder_z, ridge_hw, apex_z
STATIONS = [
    (0.0,    9, 11,  8,  4, 14),   # nose tip
    (15.0,  26, 34, 14, 12, 30),   # nose rises
    (40.0,  44, 56, 22, 36, 52),   # front shoulder approaching the pad
    (45.0,  46, 58, 23, 40, 59),   # pad front edge - flat deck begins
    (145.0, 44, 56, 23, 40, 59),   # pad back edge - flat deck ends
    (158.0, 36, 46, 20, 28, 46),   # rear shoulder narrows
    (178.0, 24, 30, 16, 12, 30),   # tail taper, kept thick enough to hollow cleanly
    (190.0, 20, 24, 15,  9, 24),   # blunt tail transom (flat rear face, not a point)
]

INNER_X_RANGE = (40.0, 158.0)   # only hollow the midsection; nose/tail stay solid
PORT_W, PORT_H, PORT_D = 16.0, 11.0, 14.0   # rear cable port
USB_W, USB_H, USB_D = 14.0, 10.0, 20.0       # side USB cutout (placeholder position)
PLATE_L, PLATE_W, PLATE_T, PLATE_CHAMFER = 210.0, 110.0, 6.0, 18.0

# ---- geometry helpers ------------------------------------------------------
def hex_pts(bw, sw, sz, rw, az, floor_z=0.0):
    return [(-bw, floor_z), (bw, floor_z), (sw, sz), (rw, az), (-rw, az), (-sw, sz)]

def build_hull_mesh(stations, floor_z=0.0):
    pps = 6
    mesh = rg.Mesh()
    for (x, bw, sw, sz, rw, az) in stations:
        for (y, z) in hex_pts(bw, sw, sz, rw, az, floor_z):
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
    """Capped solid extrusion of a convex XY polygon from z0 to z1."""
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
    bottom_c = mesh.Vertices.Count
    mesh.Vertices.Add(cx_ + ox, cy_ + oy, z0 + oz)
    for k in range(n):
        k2 = (k + 1) % n
        mesh.Faces.AddFace(bottom_c, k2, k)
    top_c = mesh.Vertices.Count
    mesh.Vertices.Add(cx_ + ox, cy_ + oy, z1 + oz)
    for k in range(n):
        k2 = (k + 1) % n
        mesh.Faces.AddFace(top_c, n + k, n + k2)
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

def boolean_diff(mesh_a, mesh_b, fallback_label):
    result = rg.Mesh.CreateBooleanDifference([mesh_a], [mesh_b])
    if not result or len(result) == 0:
        print("WARNING: boolean difference failed for " + fallback_label + " - keeping previous mesh")
        return mesh_a
    merged = result[0]
    for extra in result[1:]:
        merged.Append(extra)
    return merged

# ---- build outer hull + hollow it -----------------------------------------
hull = build_hull_mesh(STATIONS)

inner_stations = [
    (x, inset(bw, WALL_T), inset(sw, WALL_T), max(sz - WALL_T, 2.0),
     inset(rw, WALL_T), az - WALL_T)
    for (x, bw, sw, sz, rw, az) in STATIONS
    if INNER_X_RANGE[0] <= x <= INNER_X_RANGE[1]
]
inner_hull = build_hull_mesh(inner_stations, floor_z=-3.0)

shell = boolean_diff(hull, inner_hull, "hollow midsection")

cable_port = box_mesh(L - PORT_D / 2 + 2, 0, 1.0 + PORT_H / 2, PORT_D, PORT_W, PORT_H)
shell = boolean_diff(shell, cable_port, "rear cable port")

usb_port = box_mesh(62, 50, 20, USB_D, USB_W, USB_H)
shell = boolean_diff(shell, usb_port, "USB cutout")

# ---- top plate --------------------------------------------------------------
plate_pts = chamfered_rect_pts(PLATE_L, PLATE_W, PLATE_CHAMFER)
plate_cx = (PAD_X0 + PAD_X1) / 2.0
plate = extrude_xy_polygon(plate_pts, PAD_Z, PAD_Z + PLATE_T, offset=(plate_cx, 0.0, 0.0))

# ---- push into the Rhino document ------------------------------------------
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

import Rhino

body_layer = ensure_layer("Enclosure Body", sd.Color.FromArgb(176, 138, 92))   # tan/bronze
plate_layer = ensure_layer("Top Plate", sd.Color.FromArgb(28, 28, 28))         # black

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
print("Top plate: valid=%s  volume=%.1f cm^3" % (plate.IsValid, plate.Volume() / 1000.0))
print("Done - look on layers 'Enclosure Body' and 'Top Plate'.")
