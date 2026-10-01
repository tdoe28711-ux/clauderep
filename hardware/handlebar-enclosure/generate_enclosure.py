"""
Handlebar Demo Enclosure - parametric concept generator
Team Hero / UXDG 340

Builds a faceted, tank-inspired shell per Build Spec section 5-7:
  - External envelope ~190 x 135 x 70 mm (L x W x H)
  - Angular/faceted cross-sections (low-poly "tank" language, no supports)
  - Spine ridge running front-to-back, flattening into a 100x80mm top pad at 59mm
  - Cavity opens downward (no floor), sized to the spec's literal mm values
  - Rear cable port + side USB cutout
  - Separate flat top plate (210x110x6) for the 31.8mm bar clamps, two-tone

This is a concept massing study for visual review (per section 9: "developed
with visual feedback rather than written blind into a script"), not a
manufacturing-ready file. Wall margins here run thicker than the 2.4-3mm
nominal spec in a few spots so the cavity never breaches the shell -- dial
that back to the true minimum once the form is approved.

Output: STL meshes + render images.
Requires: trimesh, manifold3d (boolean engine), numpy, matplotlib
"""
import numpy as np
import trimesh

OUT = "/tmp/claude-0/-home-user-clauderep/d797779c-0f4d-5939-9a1d-ef5adbf7c278/scratchpad/enclosure"

# ---- envelope ----------------------------------------------------------
L = 190.0   # length, X: 0 (nose) -> L (tail)
W = 135.0   # width,  Y: -W/2 .. +W/2 (envelope ceiling, not fully used)
H = 70.0    # height ceiling, Z

PAD_Z = 59.0    # top mounting pad height
PAD_X0, PAD_X1 = 45.0, 145.0   # pad runs 100mm long
PAD_HALF_W = 40.0               # pad is 80mm wide

WALL_T = 3.0   # nominal wall thickness (spec: 2.4-3.0mm)

# ---- faceted hull station table ----------------------------------------
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

def hex_cross_section(bw, sw, sz, rw, az, floor_z=0.0):
    """6-pt faceted profile: bottom-L, bottom-R, shoulder-R, ridge-R, ridge-L, shoulder-L."""
    return [(-bw, floor_z), (bw, floor_z), (sw, sz), (rw, az), (-rw, az), (-sw, sz)]

def build_hull(stations, floor_z=0.0):
    n = len(stations)
    pps = 6  # points per station
    verts = []
    for (x, bw, sw, sz, rw, az) in stations:
        for (y, z) in hex_cross_section(bw, sw, sz, rw, az, floor_z):
            verts.append((x, y, z))
    verts = np.array(verts)

    faces = []
    for i in range(n - 1):
        a0, a1 = i * pps, (i + 1) * pps
        for k in range(pps):
            k2 = (k + 1) % pps
            v0, v1, v2, v3 = a0 + k, a0 + k2, a1 + k2, a1 + k
            faces += [[v0, v1, v2], [v0, v2, v3]]
            # NOTE: edge k=0 (bottom-L -> bottom-R) is swept here too, and
            # that quad strip doubles as the hull's floor - no separate
            # bottom cap needed (one would overlap this and break manifoldness).

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

hull = build_hull(STATIONS)
print(f"[hull]  watertight={hull.is_watertight}  volume={hull.volume/1000:.1f} cm^3  "
      f"bbox={hull.bounds[1]-hull.bounds[0]}")

# ---- hollow the whole hull to a uniform wall thickness -------------------
# Build an inset copy of the same faceted profile, offset inward by WALL_T,
# dropped below the bed plane so it punches clean through the open bottom
# (no floor, per spec). This hollows nose/tail/ridge uniformly instead of
# only the literal interior-cavity box, which is what actually gets the
# part under the ~300g filament budget. Tips are clamped so they don't
# collapse to zero thickness.
def inset(v, t, min_v=6.0):
    return max(v - t, min_v)

INNER_FLOOR_Z = -3.0
# Only hollow the main midsection (front shoulder through rear shoulder).
# The nose and tail tips stay solid: they're a small fraction of the mass,
# and letting the inner hull taper all the way to those points is what was
# producing a thin self-intersecting shard out of the boolean op. Capping
# the inner tool with its own flat ends here keeps it a clean, well-inside
# offset of the outer shell everywhere it's used.
INNER_X_RANGE = (40.0, 158.0)
inner_stations = [
    (x, inset(bw, WALL_T), inset(sw, WALL_T), max(sz - WALL_T, 2.0),
     inset(rw, WALL_T), az - WALL_T)
    for (x, bw, sw, sz, rw, az) in STATIONS
    if INNER_X_RANGE[0] <= x <= INNER_X_RANGE[1]
]
inner_hull = build_hull(inner_stations, floor_z=INNER_FLOOR_Z)
print(f"[inner] watertight={inner_hull.is_watertight}  volume={inner_hull.volume/1000:.1f} cm^3")

# ---- rear cable port (centered on the tail transom) ---------------------
port_w, port_h, port_d = 16.0, 11.0, 14.0  # width, height, cut depth
cable_port = trimesh.creation.box(extents=[port_d, port_w, port_h])
cable_port.apply_translation([L - port_d / 2 + 2, 0, 1.0 + port_h / 2])

# ---- USB access cutout (+Y side wall, over the Uno's assumed position) --
usb_w, usb_h, usb_d = 14.0, 10.0, 20.0
usb_port = trimesh.creation.box(extents=[usb_w, usb_d, usb_h])
usb_port.apply_translation([62, 50, 20])

shell = hull.difference(inner_hull, engine="manifold")
shell = shell.difference(cable_port, engine="manifold")
shell = shell.difference(usb_port, engine="manifold")
shell.merge_vertices()
trimesh.repair.fix_normals(shell)

mass_pla_g = shell.volume / 1000.0 * 1.24  # PLA density ~1.24 g/cm^3, solid walls
print(f"[shell] watertight={shell.is_watertight}  volume={shell.volume/1000:.1f} cm^3  "
      f"est. mass (solid PLA walls) = {mass_pla_g:.0f} g")

shell.export(f"{OUT}/body.stl")

# ---- separate top plate (bolts to the pad, carries the bar clamps) ------
from shapely.geometry import Polygon

PLATE_L, PLATE_W, PLATE_T = 210.0, 110.0, 6.0
CHAMFER = 18.0

def chamfered_rect(length, width, chamfer):
    hl, hw = length / 2, width / 2
    pts = [
        (-hl + chamfer, -hw), (hl - chamfer, -hw), (hl, -hw + chamfer),
        (hl, hw - chamfer), (hl - chamfer, hw), (-hl + chamfer, hw),
        (-hl, hw - chamfer), (-hl, -hw + chamfer),
    ]
    return Polygon(pts)

plate2d = chamfered_rect(PLATE_L, PLATE_W, CHAMFER)
plate = trimesh.creation.extrude_polygon(plate2d, height=PLATE_T)
plate.apply_translation([(PAD_X0 + PAD_X1) / 2, 0, PAD_Z])
plate.merge_vertices()
trimesh.repair.fix_normals(plate)
plate.export(f"{OUT}/top_plate.stl")
print(f"[plate] watertight={plate.is_watertight}  volume={plate.volume/1000:.1f} cm^3")

print("\nDone. STLs written to:", OUT)
