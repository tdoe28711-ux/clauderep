# Handlebar Demo Enclosure — v5 "dragon shield"

Team Hero · UXDG 340

Concept massing study, not manufacturing-ready. Third major direction after
the faceted dragonhead/spinefin merge (v3) and a fully smooth sculpted pass
(v4). This version comes from a specific reference image: dark gunmetal,
angular faceted shield shape, a glowing red V-seam down the centerline,
small dragon-fin accents near the nose.

![3/4 view](renders/enclosure_corner.png)
![Front view](renders/enclosure_front.png)
![Side view](renders/enclosure_side.png)
![Top view](renders/enclosure_top.png)

## What's in this version

- **Angular faceted shield body** — back to hard facets (not v4's smooth
  curves), reusing the proven 7-point groove cross-section from v3.
- **Sharp V-ridge down the centerline**, deepest right before the mounting
  pad, giving the aggressive "face" read from the reference. Rendered with
  a glowing red/orange seam along the groove.
- **Two small fins near the nose**, echoing the reference's "ridge detail:
  small fins for a dragon-like silhouette."
- **Dark gunmetal body / near-black plate**, matching the reference's
  material instead of the earlier tan/bronze PLA look.
- **Generic flat mounting plate for the actual bars** — not the specific
  riser/clamp hardware shown in the reference image, which was unrelated
  stock photography. Plate is 100 × 190mm, bolt holes left undrilled per
  spec (mark and drill once the real clamps are in hand).

## A bug I found and fixed while building the Rhino version

The first pass had the top plate rotated 90° by mistake (copied from an
earlier version where that rotation dodged a different set of fins). That
put the plate's long 190mm dimension along the body's length — hanging off
both the nose and tail — instead of across the body for the bar clamps.
Fixed before handing off the Rhino script; `generate_enclosure.py` and
`rhino_build_enclosure.py` both have the corrected orientation.

## Numbers

| | Value |
|---|---|
| Body mass (PLA) | 259g |
| Body cost @ $22/kg | $5.69 |
| Body bbox | 190 × 133 × 67mm |
| Plate mass if printed | 140g — recommend plywood/acrylic instead |
| Overhang checker | 41.5% of downward-facing area flagged |
| Fin overhang angles | 35.5°/18.4° and 31.0°/15.6° (both under the 45° limit) |

Body alone is well under the 300g budget.

## Honest gaps

1. **Scale texture from the reference isn't modeled.** Real 3D scales at
   that density would mean hundreds of tiny raised bumps — print-prohibitive
   at this scale and not worth the wall-thickness/print-time cost. A
   textured spray paint or vinyl wrap would get the same visual effect
   physically. Spec itself says scales aren't required.
2. **The red glow is a render effect, not geometry** — it's just how the
   groove faces are colored in the preview. In Rhino, assign those
   centerline faces a separate emissive/red material if you want the same
   look (see the print statement at the end of `rhino_build_enclosure.py`).
3. **Not slicer-checked.** The 41.5% overhang number is a simple
   face-angle heuristic, not a real slice — check actual bridging before
   printing.
4. **USB port position (x=60mm, left wall) is still a placeholder** — spec
   says decide the Uno's orientation first.
5. Bar overall width is unconfirmed for the actual 7/8" clamp set (see
   spec.md's correction note), so the plate's 190mm span is a reasonable
   guess, not a measured fit.

## Files

- `generate_enclosure.py` — Python/trimesh generator
- `rhino_build_enclosure.py` — same geometry, pure RhinoCommon, builds
  directly into an open Rhino document (no pip installs needed)
- `render.py` — gunmetal/red-glow preview renderer
- `body.stl`, `top_plate.stl` — current output meshes
- `renders/` — preview images
- `spec.md` — the team's build spec (one correction applied: section 7 bar
  diameter, see git history)
- `PROJECT.md` — team/project context
