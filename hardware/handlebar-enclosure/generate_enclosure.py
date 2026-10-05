"""
Handlebar Demo Enclosure v5 - "dragon shield": dark gunmetal, angular
faceted shield shape, sharp V-ridge spine (glowing red seam in the
render), small front fins, flat mounting pad for the actual bars (not
the reference image's specific clamp/riser hardware - that was generic
stock hardware, not ours).

Reuses the proven 7-point groove cross-section + hollow-midsection +
convex-hull fin techniques from v3/the design-pass candidates.
"""
import numpy as np
import trimesh
import shapely.geometry as sg

OUT = "/tmp/claude-0/-home-user-clauderep/d797779c-0f4d-5939-9a1d-ef5adbf7c278/scratchpad/enclosure_v5"

L = 190.0
PAD_Z = 58.0
PAD_X0, PAD_X1 = 50.0, 140.0
WALL_T = 3.0

# (x, bw, sw, sz, rw, az, groove)
STATIONS = [
    (0.0,    7,  9,  6,  3, 12,  0.0),   # nose tip - low, narrow, sharp
    (14.0,  18, 24, 12,  7, 26,  7.0),   # nose rises, V starting to open
    (28.0,  40, 54, 21, 13, 46, 16.0),   # shoulder widens, deep V
    (38.0,  56, 64, 25, 10, 58, 24.0),   # tall sharp ridge peak before the pad - deepest V
    (46.0,  60, 66, 26, 36, 60,  6.0),   # ridge closes fast into the flat deck
    (50.0,  62, 66, 26, 40, 58,  0.0),   # pad front edge (flat)
    (140.0, 60, 65, 26, 40, 58,  0.0),   # pad back edge (flat)
    (150.0, 58, 64, 25, 11, 54, 18.0),   # ridge resumes behind the pad
    (164.0, 48, 58, 23,  8, 46, 16.0),   # rear ridge peak
    (178.0, 28, 36, 16, 10, 28,  8.0),   # tail taper
    (190.0, 18, 22, 13,  7, 18,  0.0),   # blunt tail transom
]

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
    return mesh, verts, faces, pps, n

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
    if x <= xs[0]: return STATIONS[0][1:6]
    if x >= xs[-1]: return STATIONS[-1][1:6]
    for i in range(len(STATIONS) - 1):
        x0, x1 = xs[i], xs[i + 1]
        if x0 <= x <= x1:
            t = 0.0 if x1 == x0 else (x - x0) / (x1 - x0)
            a, b = STATIONS[i][1:6], STATIONS[i + 1][1:6]
            return tuple(a[j] + t * (b[j] - a[j]) for j in range(5))
    return STATIONS[-1][1:6]

def build_dorsal_fin(x_center, proud_height, base_half=5.5, apex_back_offset=2.0,
                      thick_half=2.5, embed=1.5):
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

hull, _, _, _, _ = build_hull(STATIONS)
print(f"[hull] watertight={hull.is_watertight} volume={hull.volume/1000:.1f}cm^3 "
      f"bbox={(hull.bounds[1]-hull.bounds[0]).round(1)}")

INNER_X_RANGE = (38.0, 164.0)
inner_stations = [
    (x, inset(bw, WALL_T), inset(sw, WALL_T), max(sz - WALL_T, 2.0), inset(rw, WALL_T), az - WALL_T, 0.0)
    for (x, bw, sw, sz, rw, az, groove) in STATIONS if INNER_X_RANGE[0] <= x <= INNER_X_RANGE[1]
]
inner_hull, _, _, _, _ = build_hull(inner_stations, floor_z=-3.0)
print(f"[inner] watertight={inner_hull.is_watertight} volume={inner_hull.volume/1000:.1f}cm^3")

shell = hull.difference(inner_hull, engine="manifold")

cable_port = trimesh.creation.box(extents=[14.0, 16.0, 11.0])
cable_port.apply_translation([L - 5.0, 0, 1.0 + 5.5])
shell = shell.difference(cable_port, engine="manifold")

usb_x, usb_z = 60.0, 20.0
bw_u, sw_u, sz_u, rw_u, az_u = interp_station(usb_x)
surf_hw = bw_u + (usb_z / sz_u) * (sw_u - bw_u) if usb_z <= sz_u else sw_u + (usb_z - sz_u) / (az_u - sz_u) * (rw_u - sw_u)
proud = 2.0
bezel_outer_face = -(surf_hw + proud)
bezel_inner_face = -(surf_hw - 2.5)
bezel_cy = (bezel_outer_face + bezel_inner_face) / 2.0
bezel_depth = abs(bezel_inner_face - bezel_outer_face)
bezel = trimesh.creation.box(extents=[20.0, bezel_depth, 16.0])
bezel.apply_translation([usb_x, bezel_cy, usb_z])
shell = shell.union(bezel, engine="manifold")
cut_outer = bezel_outer_face - 1.0
cut_inner = -(surf_hw - 10.0)
cut_cy = (cut_outer + cut_inner) / 2.0
cut_depth = abs(cut_inner - cut_outer)
usb_cut = trimesh.creation.box(extents=[14.0, cut_depth, 10.0])
usb_cut.apply_translation([usb_x, cut_cy, usb_z])
shell = shell.difference(usb_cut, engine="manifold")

print("front fins:")
for fx, fh in [(31.0, 9.0), (36.0, 11.0)]:
    shell = shell.union(build_dorsal_fin(fx, fh), engine="manifold")

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

# generic flat mounting plate for OUR bars - 7/8" clamps are compact, so this
# is sized conservatively generous (not the specific riser/clamp hardware in
# the reference image, which was unrelated stock hardware). Bolt holes stay
# undrilled per spec - mark/drill after the real clamps are in hand.
# NOTE: no rotation here (earlier versions rotated 90deg to dodge dorsal
# fins near the pad, but v5's fins are up at the nose, nowhere near the
# pad, so that rotation was copied over by mistake and had it backwards:
# it put the 190mm dimension along body-X (hanging off both the nose and
# tail) and the 100mm dimension along body-Y (too narrow to span bar
# clamps). Unrotated, chamfered_rect(w=100, h=190) already maps w->X
# (matches the ~90mm pad length) and h->Y (spans side-to-side for the
# clamps), which is what's actually wanted.
plate_poly = sg.Polygon(chamfered_rect(100.0, 190.0, 10.0))
plate = trimesh.creation.extrude_polygon(plate_poly, height=6.0)
plate.apply_translation([(PAD_X0 + PAD_X1) / 2, 0, PAD_Z])
plate.export(f"{OUT}/plate.stl")
plate_mass_g = plate.volume / 1000.0 * 1.24
print(f"plate watertight={plate.is_watertight} mass_g={plate_mass_g:.0f} (if printed)")
