"""
Handlebar Demo Enclosure v3 - merge of the two design-pass candidates that
actually read as intended (dragonhead snout + spine fins), dropping the two
that didn't (scaled flanks had a wall-perforation bug, haunches was broken
geometry).

Head end: slim snout tube -> one dramatic brow flare (two angled facets
with a centerline groove) -> a sharp narrow horn peak -> flat pad.
Tail end: flat pad -> twin spine fins -> tail taper -> blunt transom.
"""
import numpy as np
import trimesh
import shapely.geometry as sg

OUT = "/tmp/claude-0/-home-user-clauderep/d797779c-0f4d-5939-9a1d-ef5adbf7c278/scratchpad/enclosure_v3"

L = 190.0
PAD_Z = 59.0
PAD_X0, PAD_X1 = 45.0, 145.0
WALL_T = 3.0

# (x, bw, sw, sz, rw, az, groove)
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

def hex_cross_section(bw, sw, sz, rw, az, groove, floor_z=0.0):
    return [(-bw, floor_z), (bw, floor_z), (sw, sz), (rw, az), (0.0, az - groove), (-rw, az), (-sw, sz)]

def build_hull(stations, floor_z=0.0):
    n = len(stations); pps = 7; verts = []
    for (x, bw, sw, sz, rw, az, groove) in stations:
        for (y, z) in hex_cross_section(bw, sw, sz, rw, az, groove, floor_z):
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

def check_overhangs(mesh, label):
    down = np.array([0, 0, -1.0])
    dots = mesh.face_normals @ down
    bad = dots > 0.70710678
    bad_area = mesh.area_faces[bad].sum()
    total_down_area = mesh.area_faces[dots > 0].sum()
    pct = 100.0 * bad_area / total_down_area if total_down_area > 0 else 0.0
    print(f"[{label}] overhang-violation area pct of downward-facing area: {pct:.1f}%  ({bad.sum()} faces)")
    return pct

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
            a = np.array(STATIONS[i][1:6])
            b = np.array(STATIONS[i + 1][1:6])
            return tuple(a + t * (b - a))
    return STATIONS[-1][1:6]

def build_dorsal_fin(x_center, proud_height, base_half=6.0, apex_back_offset=2.5,
                      thick_half=3.0, embed=1.5):
    bw, sw, sz, rw, az = interp_station(x_center)
    base_z = az - embed
    apex_z = az + proud_height
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

hull = build_hull(STATIONS)

INNER_X_RANGE = (35.0, 170.0)
inner_stations = [
    (x, inset(bw, WALL_T), inset(sw, WALL_T), max(sz - WALL_T, 2.0), inset(rw, WALL_T), az - WALL_T, 0.0)
    for (x, bw, sw, sz, rw, az, groove) in STATIONS if INNER_X_RANGE[0] <= x <= INNER_X_RANGE[1]
]
inner_hull = build_hull(inner_stations, floor_z=-3.0)

cav_len = INNER_X_RANGE[1] - INNER_X_RANGE[0]
pad_bw, pad_sw, pad_sz, pad_rw, pad_az = interp_station(95.0)
in_bw, in_sw, in_sz, in_az = inset(pad_bw, WALL_T), inset(pad_sw, WALL_T), max(pad_sz - WALL_T, 2.0), pad_az - WALL_T
z_check = 40.0
hw_at_40 = in_bw + (z_check + 3.0) / (in_sz + 3.0) * (in_sw - in_bw) if z_check <= in_sz else \
           in_sw + (z_check - in_sz) / (in_az - in_sz) * (inset(pad_rw, WALL_T) - in_sw)
print(f"[cavity] {cav_len:.0f}mm long x {2*hw_at_40:.0f}mm wide x {in_az:.0f}mm ceiling "
      f"-> target 130x85x40 {'OK' if cav_len>=130 and 2*hw_at_40>=85 and in_az>=40 else 'FAIL'}")

cable_port = trimesh.creation.box(extents=[14.0, 16.0, 11.0])
cable_port.apply_translation([L - 5.0, 0, 1.0 + 5.5])

usb_x, usb_z = 62.0, 20.0
bw_u, sw_u, sz_u, rw_u, az_u = interp_station(usb_x)
surf_hw = bw_u + (usb_z / sz_u) * (sw_u - bw_u) if usb_z <= sz_u else sw_u + (usb_z - sz_u) / (az_u - sz_u) * (rw_u - sw_u)
proud = 2.0
bezel_outer_face = -(surf_hw + proud)
bezel_inner_face = -(surf_hw - 2.5)
bezel_center_y = (bezel_outer_face + bezel_inner_face) / 2.0
bezel_depth = abs(bezel_inner_face - bezel_outer_face)
bezel_outer = trimesh.creation.box(extents=[20.0, bezel_depth, 16.0])
bezel_outer.apply_translation([usb_x, bezel_center_y, usb_z])
cut_outer = bezel_outer_face - 1.0
cut_inner = -(surf_hw - 10.0)
cut_center_y = (cut_outer + cut_inner) / 2.0
cut_depth = abs(cut_inner - cut_outer)
usb_cut = trimesh.creation.box(extents=[14.0, cut_depth, 10.0])
usb_cut.apply_translation([usb_x, cut_center_y, usb_z])

shell = hull.difference(inner_hull, engine="manifold")
shell = shell.difference(cable_port, engine="manifold")
shell = shell.union(bezel_outer, engine="manifold")
shell = shell.difference(usb_cut, engine="manifold")

print("dorsal fins (rear flank only - front already carries the brow/horn):")
fin_specs = [(150.0, 12.0), (162.0, 15.0)]
for x, h in fin_specs:
    shell = shell.union(build_dorsal_fin(x, h), engine="manifold")

shell.merge_vertices()
trimesh.repair.fix_normals(shell)

mass_g = shell.volume / 1000.0 * 1.24
cost_usd = mass_g / 1000.0 * 22.0
overhang_pct = check_overhangs(shell, "body")
bbox = (shell.bounds[1] - shell.bounds[0]).tolist()
print(f"watertight={shell.is_watertight} mass_g={mass_g:.0f} cost_usd={cost_usd:.2f} bbox={bbox}")
shell.export(f"{OUT}/body.stl")

def chamfered_rect(w, h, chamfer):
    hw, hh = w / 2.0, h / 2.0
    pts = [(-hw + chamfer, -hh), (hw - chamfer, -hh), (hw, -hh + chamfer), (hw, hh - chamfer),
           (hw - chamfer, hh), (-hw + chamfer, hh), (-hw, hh - chamfer), (-hw, -hh + chamfer)]
    return pts

# 110mm along X (sits on the 100mm pad, clear of the fins), 210mm along Y
# (spans across the bar for two clamps ~190mm apart - this is the dimension
# that actually needs to be "wider than the enclosure", per spec section 7).
plate_poly = sg.Polygon(chamfered_rect(110.0, 210.0, 10.0))
plate = trimesh.creation.extrude_polygon(plate_poly, height=6.0)
plate.apply_translation([(PAD_X0 + PAD_X1) / 2.0, 0, PAD_Z])
plate.export(f"{OUT}/plate.stl")
plate_mass_g = plate.volume / 1000.0 * 1.24
print(f"plate watertight={plate.is_watertight} mass_g={plate_mass_g:.0f} (if printed - plywood/acrylic recommended instead)")
