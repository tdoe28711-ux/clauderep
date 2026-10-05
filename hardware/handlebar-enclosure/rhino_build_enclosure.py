"""
Handlebar Demo Enclosure v6 - builds directly into the active Rhino document.

Run this INSIDE Rhino (ScriptEditor / EditPythonScript), not as a standalone
.py - it uses RhinoCommon (Rhino.Geometry) and scriptcontext, which only
exist inside Rhino's own Python. No pip installs needed.

Three objects come out, on three layers:
  Enclosure Body - the printed shell (open bottom, bolts down to the base)
  Top Plate      - flat mount the bar clamps bolt to (plywood/acrylic)
  Base Plate     - flat board the shell bolts down onto (plywood/acrylic)

What changed from v5:
  * SYMMETRY. v5 read lopsided because the USB bezel stuck out on the -Y
    side only. Both flanks now get an identical bezel; the +Y one is a
    blind recess with no through-hole, so the part is mirror-symmetric
    anywhere a viewer can see.
  * EVEN FACETS. v5's stations were spaced 4/10/90mm apart with parameters
    jumping around, so facet sizes were all over the place. v6 uses evenly
    spaced stations (~31mm) with a smooth monotonic progression.
  * A BOTTOM. The shell itself is still open-bottomed (spec section 6), but
    it now bolts down to a base plate through four INTERNAL bosses. An
    external bolt flange was tried first and rejected: it pushed width to
    142mm (spec caps 135mm) and mass to 323g (budget 300g). Internal bosses
    add neither.

Color it in Rhino's material/render panel: dark gunmetal body
(~RGB 60,62,67), near-black top plate, and give the faces right along the
centerline groove an emissive red/orange material for the glowing-seam look
from the renders.

Re-running is safe - it deletes the objects it made last time first.
"""
import Rhino
import Rhino.Geometry as rg
import scriptcontext as sc
import System.Drawing as sd
import math

# ---- envelope ---------------------------------------------------------
L = 190.0
PAD_Z = 58.0
PAD_X0, PAD_X1 = 56.0, 134.0
WALL_T = 3.0

# Evenly spaced stations, smooth monotonic progression, mirror-symmetric
# fore/aft apart from the nose being lower and sharper than the tail.
# The two shoulder stations (x=30/160) are the hollow-region boundaries;
# their shoulder_hw/ridge_hw are sized so the interior clears 85mm of width
# at the 40mm height the components need, not just at mid-length.
# (x, bottom_hw, shoulder_hw, shoulder_z, ridge_hw, apex_z, groove)
STATIONS = [
    (0.0,    10, 13,  8,  5, 16,  0.0),   # nose tip
    (30.0,   46, 60, 22, 36, 58, 20.0),   # shoulder, V open
    (64.0,   60, 66, 26, 40, 58,  0.0),   # pad front
    (95.0,   61, 66, 26, 40, 58,  0.0),   # pad mid
    (126.0,  60, 66, 26, 40, 58,  0.0),   # pad back
    (160.0,  46, 60, 22, 36, 58, 20.0),   # shoulder, V open (mirrors x=30)
    (190.0,  16, 20, 12,  8, 22,  0.0),   # blunt tail transom (cable port)
]

INNER_X_RANGE = (30.0, 160.0)   # 130mm, matching the spec minimum exactly

# (x_center, proud_height). proud_height is measured from the TRUE y=0
# surface (az - groove, see build_dorsal_fin), not from az, so it has to be
# large enough to clear the groove depth before the fin pokes up past the
# surrounding ridge.
FIN_SPECS = [(26.0, 24.0), (38.0, 26.0)]

PORT_W, PORT_H, PORT_D = 16.0, 11.0, 14.0
USB_W, USB_H = 14.0, 10.0
USB_X, USB_Z = 70.0, 20.0

BOLT_D = 4.5                       # M4 clearance
BOSS_OD, BOSS_H = 11.0, 14.0       # internal bolt bosses
BOSS_XS = [46.0, 144.0]

# Top plate: PLATE_X maps to body-X (sits on the ~78mm pad), PLATE_Y maps to
# body-Y (spans side-to-side for the bar clamps). Bolt holes stay undrilled
# per spec - mark and drill once the real clamps are in hand.
PLATE_X, PLATE_Y, PLATE_T, PLATE_CHAMFER = 100.0, 190.0, 6.0, 10.0
BASE_L, BASE_W, BASE_T, BASE_CHAMFER = 206.0, 150.0, 6.0, 12.0

OBJ_NAME_PREFIX = "handlebar_enclosure_v6"

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

def cylinder_mesh(cx, cy, z0, radius, height, sides=24):
    base_plane = rg.Plane(rg.Point3d(cx, cy, z0), rg.Vector3d.ZAxis)
    cyl = rg.Cylinder(rg.Circle(base_plane, radius), height)
    mesh = rg.Mesh.CreateFromCylinder(cyl, 1, sides)
    mesh.UnifyNormals()
    mesh.Normals.ComputeNormals()
    mesh.Compact()
    return mesh

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
    if you need the true y=0 surface height (az - groove), since az alone is
    the RIDGE height at y=+-rw, not the (lower, V-notched) centerline."""
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

def surface_half_width(x, z):
    bw, sw, sz, rw, az = interp_station(x)
    if z <= sz:
        return bw + (z / sz) * (sw - bw)
    return sw + (z - sz) / (az - sz) * (rw - sw)

def build_dorsal_fin(x_center, proud_height, base_half=6.0, apex_back_offset=2.0,
                      thick_half=2.5, embed=2.0):
    # Anchor to the TRUE y=0 surface (az - groove), not the RIDGE height az
    # at y=+-rw. The fin is centered at y=0, which sits in the bottom of the
    # V-notch; anchoring to az left it floating by the groove depth.
    bw, sw, sz, rw, az = interp_station(x_center)
    surface_z = az - interp_groove(x_center)
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
    # CreateBooleanDifference returns a .NET array - list() it before any
    # Python indexing or slicing, or you get "array index has type slice".
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

cable_port = box_mesh(L - 5.0, 0, 1.0 + PORT_H / 2, PORT_D, PORT_W, PORT_H)
shell = boolean_diff(shell, cable_port, "rear cable port")

# ---- USB port, plus a MATCHING blind recess on the far side so the part is
#      mirror-symmetric to look at (v5 had the bezel on one side only) -----
surf_hw = surface_half_width(USB_X, USB_Z)
proud = 2.0
for side in (-1.0, 1.0):
    outer_face = side * (surf_hw + proud)
    inner_face = side * (surf_hw - 2.5)
    bezel = box_mesh(USB_X, (outer_face + inner_face) / 2.0, USB_Z,
                     20.0, abs(outer_face - inner_face), 16.0)
    shell = boolean_union(shell, bezel, "usb bezel side %.0f" % side)

# real through-cut on -Y (the USB side)
cut_outer = -(surf_hw + proud + 1.0)
cut_inner = -(surf_hw - 10.0)
usb_cut = box_mesh(USB_X, (cut_outer + cut_inner) / 2.0, USB_Z,
                   USB_W, abs(cut_inner - cut_outer), USB_H)
shell = boolean_diff(shell, usb_cut, "usb cutout")

# matching shallow blind recess on +Y: same opening, 2.5mm deep, so it reads
# identical from outside without breaching the wall
blind_outer = surf_hw + proud + 1.0
blind_inner = surf_hw - 0.5
blind = box_mesh(USB_X, (blind_outer + blind_inner) / 2.0, USB_Z,
                 USB_W, abs(blind_outer - blind_inner), USB_H)
shell = boolean_diff(shell, blind, "blind recess (symmetry)")

# ---- dorsal fins ---------------------------------------------------------
for (fx, fh) in FIN_SPECS:
    shell = boolean_union(shell, build_dorsal_fin(fx, fh), "dorsal fin @ x=%.0f" % fx)

# ---- internal bolt bosses -----------------------------------------------
BOLTS = []
for bx in BOSS_XS:
    by = surface_half_width(bx, 0.0) - WALL_T - BOSS_OD / 2.0 - 1.0  # tucked just inside the wall
    BOLTS.append((bx, -by))
    BOLTS.append((bx, by))

for (bx, by) in BOLTS:
    boss = cylinder_mesh(bx, by, 0.0, BOSS_OD / 2.0, BOSS_H)
    shell = boolean_union(shell, boss, "bolt boss @ (%.0f, %.0f)" % (bx, by))
    hole = cylinder_mesh(bx, by, -BOSS_H, BOLT_D / 2.0, BOSS_H * 3)
    shell = boolean_diff(shell, hole, "bolt hole @ (%.0f, %.0f)" % (bx, by))

# ---- top plate -----------------------------------------------------------
plate = extrude_xy_polygon(chamfered_rect_pts(PLATE_X, PLATE_Y, PLATE_CHAMFER),
                           PAD_Z, PAD_Z + PLATE_T,
                           offset=((PAD_X0 + PAD_X1) / 2.0, 0.0, 0.0))

# ---- base plate (shell bolts down onto this) -----------------------------
base = extrude_xy_polygon(chamfered_rect_pts(BASE_L, BASE_W, BASE_CHAMFER),
                          -BASE_T, 0.0, offset=(L / 2.0, 0.0, 0.0))
for (bx, by) in BOLTS:
    hole = cylinder_mesh(bx, by, -BASE_T * 2, BOLT_D / 2.0, BASE_T * 4)
    base = boolean_diff(base, hole, "base bolt hole @ (%.0f, %.0f)" % (bx, by))

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

def clear_previous():
    """So re-running doesn't stack a second copy on top of the first."""
    removed = 0
    for obj in list(sc.doc.Objects):
        if obj.Attributes.Name and obj.Attributes.Name.startswith(OBJ_NAME_PREFIX):
            sc.doc.Objects.Delete(obj, True)
            removed += 1
    if removed:
        print("cleared %d object(s) from a previous run" % removed)

def add(mesh, layer_name, color, suffix):
    attr = Rhino.DocObjects.ObjectAttributes()
    attr.LayerIndex = ensure_layer(layer_name, color)
    attr.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer
    attr.Name = OBJ_NAME_PREFIX + "_" + suffix
    sc.doc.Objects.AddMesh(mesh, attr)

clear_previous()
add(shell, "Enclosure Body", sd.Color.FromArgb(60, 62, 67), "body")
add(plate, "Top Plate", sd.Color.FromArgb(18, 18, 20), "top_plate")
add(base, "Base Plate", sd.Color.FromArgb(150, 120, 80), "base_plate")
sc.doc.Views.Redraw()

bb = shell.GetBoundingBox(True)
print("Body:  valid=%s  volume=%.1f cm^3  (~%.0fg PLA)  bbox=%.0f x %.0f x %.0f mm" %
      (shell.IsValid, shell.Volume() / 1000.0, shell.Volume() / 1000.0 * 1.24,
       bb.Max.X - bb.Min.X, bb.Max.Y - bb.Min.Y, bb.Max.Z - bb.Min.Z))
print("Top plate: %.0f x %.0f x %.0fmm - cut from plywood/acrylic, don't print it" %
      (PLATE_X, PLATE_Y, PLATE_T))
print("Base plate: %.0f x %.0f x %.0fmm with %d x M4 holes - plywood/acrylic" %
      (BASE_L, BASE_W, BASE_T, len(BOLTS)))
print("Bolt positions (x, y) in mm: %s" % ([(round(a), round(b)) for a, b in BOLTS],))
print("")
print("NOTE: select ONLY the body mesh before running BoundingBox - the")
print("plates are deliberately wider than the shell, so a cumulative")
print("bounding box over all three reports the plates' size, not the shell's.")
print("Tip: give the faces straight down the centerline V a separate")
print("emissive red material for the glowing-seam look from the renders.")
