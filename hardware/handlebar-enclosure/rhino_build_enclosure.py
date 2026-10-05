"""
Handlebar Demo Enclosure v5 "dragon shield" - builds directly into the
active Rhino document.

Run this INSIDE Rhino (ScriptEditor / EditPythonScript), not as a standalone
.py - it uses RhinoCommon (Rhino.Geometry) and scriptcontext, which only
exist inside Rhino's own Python. No pip installs needed.

Angular/faceted shield shape: low tapered nose -> deep V-ridge (sharp
groove down the centerline, reads as the glowing seam in the renders) ->
two small front fins -> flat mounting pad -> V-ridge resumes behind the
pad -> tail taper -> blunt transom. Rear cable port, bezeled USB port on
the left wall, flat mounting plate sized generically for your actual bar
clamps (not the specific hardware in the reference image - that was
unrelated stock photography).

Color it in Rhino's material/render panel: dark gunmetal body
(~RGB 60,62,67), near-black top plate, and give the faces right along the
centerline groove an emissive red/orange material for the glowing-seam
look from the renders (select those faces with Rhino's "SelSubCrv" or by
hand along the ridge, then assign a separate sub-object material).

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
PAD_Z = 58.0
PAD_X0, PAD_X1 = 50.0, 140.0
WALL_T = 3.0

# NOTE on x=36/150/166: these are the INNER_X_RANGE hollow boundaries.
# Originally (x=38 rw=10, x=150 rw=11, x=164 rw=8) they were narrow enough
# that the interior didn't clear 85mm width at the 40mm height the spec
# needs - checked numerically (half-width at z=40 came out to 31/28/12mm,
# all failing the 42.5mm-half-width bar). Widened rw/az at these three
# stations so the actual usable interior - not just the gross
# INNER_X_RANGE span - clears 130x85x40 (every station in range now
# individually passes, not just the two endpoints). The V-notch (groove)
# is unchanged, so the dragon-seam look is the same, just the ridge the
# groove cuts into is a bit wider/taller at these specific stations.
# (x, bottom_hw, shoulder_hw, shoulder_z, ridge_hw, apex_z, groove)
STATIONS = [
    (0.0,    7,  9,  6,  3, 12,  0.0),   # nose tip - low, narrow, sharp
    (14.0,  18, 24, 12,  7, 26,  7.0),   # nose rises, V starting to open
    (28.0,  40, 54, 21, 13, 46, 16.0),   # shoulder widens, deep V
    (36.0,  56, 64, 25, 32, 60, 24.0),   # tall ridge peak before the pad - widened for cavity clearance
    (46.0,  60, 66, 26, 36, 60,  6.0),   # ridge closes fast into the flat deck
    (50.0,  62, 66, 26, 40, 58,  0.0),   # pad front edge (flat)
    (140.0, 60, 65, 26, 40, 58,  0.0),   # pad back edge (flat)
    (150.0, 58, 64, 25, 32, 59, 18.0),   # ridge resumes behind the pad - widened for cavity clearance
    (166.0, 54, 62, 23, 34, 58, 16.0),   # rear ridge peak - widened for cavity clearance
    (178.0, 28, 36, 16, 10, 28,  8.0),   # tail taper
    (190.0, 18, 22, 13,  7, 18,  0.0),   # blunt tail transom
]

INNER_X_RANGE = (36.0, 166.0)   # 130mm, now genuinely wide/tall enough end to end
# (x_center, proud_height) - front, nose side. proud_height is measured
# from the TRUE y=0 surface (az - groove, see build_dorsal_fin below), not
# from az, so it needs to be large enough to clear the groove depth
# (~18-22mm here) before the fin pokes up past the surrounding ridge.
FIN_SPECS = [(31.0, 26.0), (36.0, 26.0)]
PORT_W, PORT_H, PORT_D = 16.0, 11.0, 14.0
USB_W, USB_H = 14.0, 10.0
USB_X, USB_Z = 60.0, 20.0
# generic flat mounting plate for the actual bars - not the specific
# clamp/riser hardware in the reference image, which was unrelated stock
# hardware. Bolt holes stay undrilled per spec - mark/drill after the
# real clamps are in hand. w maps to body-X (sits on the ~90mm pad),
# h maps to body-Y (spans side-to-side for the clamps).
PLATE_X, PLATE_Y, PLATE_T, PLATE_CHAMFER = 100.0, 190.0, 6.0, 10.0

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
    """Returns (bw, sw, sz, rw, az) - NOT groove; use interp_groove(x) too
    if you need the true y=0 surface height (az - groove), since az alone
    is the RIDGE height at y=+-rw, not the (lower, V-notched) centerline."""
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

def interp_groove(x):
    xs = [s[0] for s in STATIONS]
    if x <= xs[0]:
        return STATIONS[0][6]
    if x >= xs[-1]:
        return STATIONS[-1][6]
    for i in range(len(STATIONS) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            return STATIONS[i][6] + t * (STATIONS[i + 1][6] - STATIONS[i][6])
    return STATIONS[-1][6]

def build_dorsal_fin(x_center, proud_height, base_half=5.5, apex_back_offset=2.0,
                      thick_half=2.5, embed=1.5):
    # BUG (found via Rhino screenshots - fins floating with a visible gap
    # underneath): this used to anchor to `az`, the RIDGE height at
    # y=+-rw. But the fin is centered at y=0, which sits in the bottom of
    # the V-notch, not on the ridge - the real surface there is lower by
    # the groove depth. Anchor to that instead so the fin's base actually
    # touches solid material.
    bw, sw, sz, rw, az = interp_station(x_center)
    groove = interp_groove(x_center)
    surface_z = az - groove
    base_z = surface_z - embed
    apex_z = surface_z + proud_height
    x_front, x_back = x_center - base_half, x_center + base_half
    x_apex = x_center + apex_back_offset
    pts = [
        rg.Point3d(x_front, -thick_half, base_z), rg.Point3d(x_back, -thick_half, base_z), rg.Point3d(x_apex, -thick_half, apex_z),
        rg.Point3d(x_front,  thick_half, base_z), rg.Point3d(x_back,  thick_half, base_z), rg.Point3d(x_apex,  thick_half, apex_z),
    ]
    mesh = rg.Mesh()
    for p in pts:
        mesh.Vertices.Add(p)
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

# ---- top plate: no rotation - w(100) maps to body-X (sits on the pad),
# h(190) maps to body-Y (spans side-to-side for the bar clamps) ------------
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

body_layer = ensure_layer("Enclosure Body", sd.Color.FromArgb(60, 62, 67))    # gunmetal
plate_layer = ensure_layer("Top Plate", sd.Color.FromArgb(18, 18, 20))        # near-black

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
print("Tip: select the faces straight down the centerline V and give them a")
print("separate emissive red material (Rhino's sub-object material assign)")
print("for the glowing-seam look from the renders.")
