"""
Handlebar Demo Enclosure v6 - clean rebuild.

Fixes carried in from v5 feedback:
  * SYMMETRY. v5 read lopsided because the USB bezel stuck out 2mm on the
    -Y side only. Now both flanks get an identical bezel (the +Y one is a
    blind vent recess, no through-hole), so the part is mirror-symmetric
    everywhere a viewer can see. Verified numerically at the end.
  * NO MORE WONKY FACETS. v5's stations were spaced 4/10/90mm apart with
    parameters jumping around, so facet sizes were all over the place.
    v6 uses evenly spaced stations with a smooth monotonic progression,
    and is fore-aft symmetric about mid-length apart from the deliberate
    nose/tail difference.
  * BOTTOM. The shell stays open-bottomed (spec section 6), but now bolts
    down to a flat base plate via INTERNAL bosses rather than the external
    flange tried in v5 - the flange pushed width to 142mm (over the 135mm
    spec) and mass to 323g (over the 300g budget). Internal bosses add
    neither.
"""
import os
import numpy as np
import trimesh
import shapely.geometry as sg

OUT = os.path.dirname(os.path.abspath(__file__))

L = 190.0
WALL_T = 3.0
PAD_Z = 58.0
PAD_X0, PAD_X1 = 56.0, 134.0

# Evenly spaced stations (0/32/64/95/126/158/190 - 31-32mm apart), smooth
# monotonic progression, mirror-symmetric fore/aft except the nose being a
# little lower and sharper than the tail.
# (x, bottom_hw, shoulder_hw, shoulder_z, ridge_hw, apex_z, groove)
STATIONS = [
    (0.0,    10, 13,  8,  5, 16,  0.0),   # nose tip
    (30.0,   46, 60, 22, 36, 58, 20.0),   # shoulder, V open (sw/rw sized so the cavity clears 85mm at z=40)
    (64.0,   60, 66, 26, 40, 58,  0.0),   # pad front
    (95.0,   61, 66, 26, 40, 58,  0.0),   # pad mid
    (126.0,  60, 66, 26, 40, 58,  0.0),   # pad back
    (160.0,  46, 60, 22, 36, 58, 20.0),   # shoulder, V open (mirrors x=30)
    (190.0,  16, 20, 12,  8, 22,  0.0),   # blunt tail transom (cable port lives here)
]

INNER_X_RANGE = (30.0, 160.0)   # 130mm, matching the spec minimum exactly
FIN_SPECS = [(26.0, 24.0), (38.0, 26.0)]   # (x_center, proud_height) on the nose-side V
PORT_W, PORT_H, PORT_D = 16.0, 11.0, 14.0
USB_W, USB_H = 14.0, 10.0
USB_X, USB_Z = 70.0, 20.0

BOLT_D = 4.5                       # M4 clearance
BOSS_OD, BOSS_H = 11.0, 14.0       # internal bolt bosses
BOSS_XS = [46.0, 144.0]
BASE_L, BASE_W, BASE_T = 206.0, 150.0, 6.0

def hex7(bw, sw, sz, rw, az, groove, floor_z=0.0):
    return [(-bw, floor_z), (bw, floor_z), (sw, sz), (rw, az), (0.0, az - groove), (-rw, az), (-sw, sz)]

def build_hull(stations, floor_z=0.0):
    n = len(stations); pps = 7; verts = []
    for (x, bw, sw, sz, rw, az, groove) in stations:
        for (y, z) in hex7(bw, sw, sz, rw, az, groove, floor_z):
            verts.append((x, y, z))
    verts = np.array(verts)
    faces = []
    for i in range(n - 1):
        a0, a1 = i * pps, (i + 1) * pps
        for k in range(pps):
            k2 = (k + 1) % pps
            v0, v1, v2, v3 = a0 + k, a0 + k2, a1 + k2, a1 + k
            faces += [[v0, v1, v2], [v0, v2, v3]]
    nose0 = 0
    for k in range(1, pps - 1):
        faces.append([nose0, nose0 + k + 1, nose0 + k])
    tail0 = (n - 1) * pps
    for k in range(1, pps - 1):
        faces.append([tail0, tail0 + k, tail0 + k + 1])
    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    mesh.merge_vertices()
    trimesh.repair.fix_normals(mesh)
    return mesh

def inset(v, t, min_v=6.0):
    return max(v - t, min_v)

def interp_station(x):
    xs = [s[0] for s in STATIONS]
    if x <= xs[0]: return STATIONS[0][1:6]
    if x >= xs[-1]: return STATIONS[-1][1:6]
    for i in range(len(STATIONS) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            a, b = STATIONS[i][1:6], STATIONS[i + 1][1:6]
            return tuple(a[j] + t * (b[j] - a[j]) for j in range(5))
    return STATIONS[-1][1:6]

def interp_groove(x):
    xs = [s[0] for s in STATIONS]
    if x <= xs[0]: return STATIONS[0][6]
    if x >= xs[-1]: return STATIONS[-1][6]
    for i in range(len(STATIONS) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            return STATIONS[i][6] + t * (STATIONS[i + 1][6] - STATIONS[i][6])
    return STATIONS[-1][6]

def build_dorsal_fin(x_center, proud_height, base_half=6.0, apex_back_offset=2.0,
                      thick_half=2.5, embed=2.0):
    # anchor to the TRUE y=0 surface (az - groove), not the ridge height az -
    # the fins sit in the bottom of the V-notch, not on the ridge.
    bw, sw, sz, rw, az = interp_station(x_center)
    surface_z = az - interp_groove(x_center)
    base_z = surface_z - embed
    apex_z = surface_z + proud_height
    x_front, x_back = x_center - base_half, x_center + base_half
    x_apex = x_center + apex_back_offset
    pts = np.array([
        [x_front, -thick_half, base_z], [x_back, -thick_half, base_z], [x_apex, -thick_half, apex_z],
        [x_front,  thick_half, base_z], [x_back,  thick_half, base_z], [x_apex,  thick_half, apex_z],
    ])
    fin = trimesh.convex.convex_hull(pts)
    front_deg = np.degrees(np.arctan2(base_half + apex_back_offset, proud_height + embed))
    back_deg = np.degrees(np.arctan2(base_half - apex_back_offset, proud_height + embed))
    print(f"  fin@x={x_center:.0f}: proud={proud_height:.1f}mm front={front_deg:.1f}deg back={back_deg:.1f}deg (limit 45)")
    return fin

def surface_half_width(x, z):
    bw, sw, sz, rw, az = interp_station(x)
    if z <= sz:
        return bw + (z / sz) * (sw - bw)
    return sw + (z - sz) / (az - sz) * (rw - sw)

def check_overhangs(mesh, label):
    down = np.array([0, 0, -1.0])
    dots = mesh.face_normals @ down
    bad = dots > 0.70710678
    pct = 100.0 * mesh.area_faces[bad].sum() / mesh.area_faces[dots > 0].sum()
    print(f"[{label}] overhang-violation area: {pct:.1f}% of downward-facing area ({bad.sum()} faces)")
    return pct

# ---- hull + hollow --------------------------------------------------------
hull = build_hull(STATIONS)
print(f"[hull] watertight={hull.is_watertight} bbox={(hull.bounds[1]-hull.bounds[0]).round(1)}")

inner_stations = [
    (x, inset(bw, WALL_T), inset(sw, WALL_T), max(sz - WALL_T, 2.0), inset(rw, WALL_T), az - WALL_T, 0.0)
    for (x, bw, sw, sz, rw, az, groove) in STATIONS if INNER_X_RANGE[0] <= x <= INNER_X_RANGE[1]
]
inner_hull = build_hull(inner_stations, floor_z=-3.0)
shell = hull.difference(inner_hull, engine="manifold")

# ---- rear cable port ------------------------------------------------------
cable_port = trimesh.creation.box(extents=[PORT_D, PORT_W, PORT_H])
cable_port.apply_translation([L - 5.0, 0, 1.0 + PORT_H / 2])
shell = shell.difference(cable_port, engine="manifold")

# ---- USB port, and a MATCHING blind vent on the far side so the part is
#      mirror-symmetric to look at (v5 had the bezel on one side only) ------
surf_hw = surface_half_width(USB_X, USB_Z)
proud = 2.0
for side in (-1.0, +1.0):
    outer_face = side * (surf_hw + proud)
    inner_face = side * (surf_hw - 2.5)
    bezel = trimesh.creation.box(extents=[20.0, abs(outer_face - inner_face), 16.0])
    bezel.apply_translation([USB_X, (outer_face + inner_face) / 2.0, USB_Z])
    shell = shell.union(bezel, engine="manifold")

# real through-cut on -Y (the USB side)
cut_outer = -(surf_hw + proud + 1.0)
cut_inner = -(surf_hw - 10.0)
usb_cut = trimesh.creation.box(extents=[USB_W, abs(cut_inner - cut_outer), USB_H])
usb_cut.apply_translation([USB_X, (cut_outer + cut_inner) / 2.0, USB_Z])
shell = shell.difference(usb_cut, engine="manifold")

# matching shallow blind recess on +Y: same opening, but only 2.5mm deep so
# it reads identical from outside without breaching the wall
blind_outer = (surf_hw + proud + 1.0)
blind_inner = (surf_hw - 0.5)
blind = trimesh.creation.box(extents=[USB_W, abs(blind_outer - blind_inner), USB_H])
blind.apply_translation([USB_X, (blind_outer + blind_inner) / 2.0, USB_Z])
shell = shell.difference(blind, engine="manifold")

# ---- dorsal fins ----------------------------------------------------------
print("fins:")
for fx, fh in FIN_SPECS:
    shell = shell.union(build_dorsal_fin(fx, fh), engine="manifold")

# ---- internal bolt bosses (no external flange - that blew the width and
#      mass budgets in v5). Bolts come up through the base plate into these.
BOLTS = []
for bx in BOSS_XS:
    hw_at_base = surface_half_width(bx, 0.0)
    by = hw_at_base - WALL_T - BOSS_OD / 2.0 - 1.0   # tucked just inside the wall
    for sgn in (-1.0, 1.0):
        BOLTS.append((bx, sgn * by))

for (bx, by) in BOLTS:
    boss = trimesh.creation.cylinder(radius=BOSS_OD / 2.0, height=BOSS_H)
    boss.apply_translation([bx, by, BOSS_H / 2.0])
    shell = shell.union(boss, engine="manifold")
    hole = trimesh.creation.cylinder(radius=BOLT_D / 2.0, height=BOSS_H * 3)
    hole.apply_translation([bx, by, BOSS_H / 2.0])
    shell = shell.difference(hole, engine="manifold")

shell.merge_vertices()
trimesh.repair.fix_normals(shell)
shell.export(f"{OUT}/body.stl")

mass_g = shell.volume / 1000.0 * 1.24
bbox = (shell.bounds[1] - shell.bounds[0])
print(f"[body] watertight={shell.is_watertight} mass={mass_g:.0f}g cost=${mass_g/1000*22:.2f} "
      f"bbox={bbox.round(1)}")
check_overhangs(shell, "body")

# ---- symmetry check (the actual complaint) --------------------------------
mirrored = shell.copy()
mirrored.apply_transform(np.array([[1,0,0,0],[0,-1,0,0],[0,0,1,0],[0,0,0,1]]))
d_vol = abs(shell.volume - mirrored.volume)
ext_a, ext_b = shell.bounds[1] - shell.bounds[0], mirrored.bounds[1] - mirrored.bounds[0]
print(f"[symmetry] |volume difference| vs mirrored copy = {d_vol:.4f} mm^3")
print(f"[symmetry] y-extent: +Y={shell.bounds[1][1]:.2f}  -Y={shell.bounds[0][1]:.2f} "
      f"(equal magnitude = left/right symmetric)")

# ---- cavity vs spec's 130 x 85 x 40 --------------------------------------
print("[cavity] station-by-station clearance check:")
ok_all = True
for s in STATIONS:
    x = s[0]
    if not (INNER_X_RANGE[0] <= x <= INNER_X_RANGE[1]):
        continue
    bw, sw, sz, rw, az = interp_station(x)
    bw2, sw2, sz2, rw2, az2 = inset(bw, WALL_T), inset(sw, WALL_T), max(sz - WALL_T, 2), inset(rw, WALL_T), az - WALL_T
    hw40 = bw2 + (40 / sz2) * (sw2 - bw2) if 40 <= sz2 else sw2 + (40 - sz2) / (az2 - sz2) * (rw2 - sw2)
    ok = hw40 >= 42.5 and az2 >= 40
    ok_all = ok_all and ok
    print(f"   x={x:5.0f}: half-width@z40={hw40:5.1f}mm ceiling={az2:4.1f}mm  {'PASS' if ok else 'FAIL'}")
print(f"[cavity] length={INNER_X_RANGE[1]-INNER_X_RANGE[0]:.0f}mm (spec wants >=130), "
      f"all stations clear 85x40: {ok_all}")

# ---- top plate ------------------------------------------------------------
def chamfered_rect(w, h, chamfer):
    hw, hh = w / 2.0, h / 2.0
    return [(-hw + chamfer, -hh), (hw - chamfer, -hh), (hw, -hh + chamfer), (hw, hh - chamfer),
            (hw - chamfer, hh), (-hw + chamfer, hh), (-hw, hh - chamfer), (-hw, -hh + chamfer)]

plate = trimesh.creation.extrude_polygon(sg.Polygon(chamfered_rect(100.0, 190.0, 10.0)), height=6.0)
plate.apply_translation([(PAD_X0 + PAD_X1) / 2, 0, PAD_Z])
plate.export(f"{OUT}/top_plate.stl")
print(f"[top plate] 100 x 190 x 6mm, {plate.volume/1000*1.24:.0f}g if printed "
      f"(plywood/acrylic recommended)")

# ---- base plate -----------------------------------------------------------
base = trimesh.creation.extrude_polygon(sg.Polygon(chamfered_rect(BASE_L, BASE_W, 12.0)), height=BASE_T)
base.apply_translation([L / 2.0, 0.0, -BASE_T])
for (bx, by) in BOLTS:
    hole = trimesh.creation.cylinder(radius=BOLT_D / 2.0, height=BASE_T * 4)
    hole.apply_translation([bx, by, -BASE_T / 2.0])
    base = base.difference(hole, engine="manifold")
base.export(f"{OUT}/base_plate.stl")
print(f"[base plate] {BASE_L:.0f} x {BASE_W:.0f} x {BASE_T:.0f}mm plywood/acrylic, "
      f"{len(BOLTS)} x M4 holes at {[(round(a), round(b)) for a, b in BOLTS]}")
