# Handlebar Demo Enclosure — Concept Pass v1

Team Hero · UXDG 340 · generated from `handlebar-enclosure-spec.md`'s build spec.

This is a **massing study**, not a manufacturing-ready file. Per the spec's
own section 9 — "what's needed is a better-resolved form... developed with
visual feedback rather than written blind into a script" — the goal here was
to get a faceted, tank-leaning shape in front of the team to react to,
quickly, rather than guess blind at facet geometry in prose.

![Isometric render](renders/enclosure_iso.png)
![Four-view render](renders/enclosure_4view.png)

## What this is

A parametric Python generator (`generate_enclosure.py`, using `trimesh` +
`manifold3d` for the boolean ops) that lofts a low-poly, hex-faceted hull
along the enclosure's length, hollows the midsection to a ~3mm wall, and
cuts the rear cable port + side USB port called out in spec section 6. A
separate chamfered top plate stands in for the bar-clamp mounting plate
from section 7. `render.py` produces the shaded preview images above.

Regenerate with:
```
pip install trimesh manifold3d numpy matplotlib shapely
python3 generate_enclosure.py   # writes body.stl + top_plate.stl
python3 render.py               # writes renders/*.png
```

## Design decisions made here

- **Faceted hex-loft body**, angular throughout, no rounded surfaces — reads
  closer to "tank" than "router," per section 2's steer.
- **Spine/ridge that flattens into the mounting pad**: the top edge narrows
  from the shoulders into a flat 100 × 80mm deck at 59mm, matching section 6's
  "top mounting pad" spec exactly (`PAD_X0=45, PAD_X1=145` → 100mm long;
  `PAD_HALF_W=40` → 80mm wide).
- **Two-tone split**: tan/bronze body, black top plate — echoes the Team
  Bravo reference photo's finish without copying its canister silhouette.
- **Blunt tail transom** instead of tapering to a point, so the rear cable
  port (16 × 11mm) has an actual near-vertical face to sit in, as the spec
  calls for ("rear face, centered").
- **Hollowed midsection only.** The nose and tail tips are left solid — the
  inner-hull boolean produced a thin self-intersecting shard when it was
  asked to taper all the way to a point at both ends. Since those tips are
  a small fraction of the volume, capping the hollow at `INNER_X_RANGE =
  (40, 158)` was the pragmatic fix rather than fighting the boolean kernel
  further for a concept pass.
- **Top plate is a stand-in**, not final geometry: 210 × 110 × 6mm with
  chamfered corners, no clamp bolt holes (per spec — drill those after the
  clamps are in hand).

## Spec compliance check

| Spec item | Target | This model | Status |
|---|---|---|---|
| External envelope | 190 × 135 × 70mm | 190 × 116 × 59mm (body); plate adds 210 × 110mm footprint at 59-65mm | Under envelope on W/H — room to grow if the facet language wants more shoulder |
| Wall thickness | 2.4-3.0mm | 3.0mm nominal in the midsection hollow; nose/tail solid | Midsection on-spec; nose/tail intentionally thicker |
| Supports / overhangs | ≤45° from vertical, no supports | Not yet verified | **Open — check in slicer before printing** |
| Filament budget | Under ~300g | Body: **275g** (PLA, @1.24 g/cm³). Plate: 167g *if* printed — spec suggests plywood/acrylic instead, which is assumed here | Body alone is in budget |
| Top mounting pad | ~100 × 80mm, ~59mm height | 100 × 80mm at 59mm, exact | Match |
| Cable port | Rear, 16 × 11mm | Cut at X≈190, Z 1-12mm | Present, not dimension-verified in slicer |
| USB access | Side, ~14 × 10mm | Cut at X=62, +Y side, Z 15-25mm | Placeholder position — depends on final Uno orientation (spec says decide that first) |
| Separate top plate for clamps | 210 × 110 × 6mm | Modeled at those exact dims | Match |

## Honest gaps / next steps

1. **Not print-verified.** This hasn't been sliced or overhang-checked. The
   nose rise and shoulder flare are the likeliest spots to exceed 45°; worth
   a slicer pass before anyone commits filament.
2. **USB cutout position is a guess.** Spec explicitly says "decide the
   Uno's orientation first, then cut this to match" — this model picked a
   plausible spot so there's *something* to react to, not a verified one.
3. **Facet count/sharpness is a first guess**, not a converged answer.
   Section 8 lists "exact facet language" as still open — this gives the
   team a concrete shape to critique (more facets? sharper shoulder? taller
   ridge?) rather than iterating blind.
4. **Bar clamp bolt pattern, spine fins, and display mount** are untouched —
   all still open per section 8.
5. This is a trimesh/Python concept model, not Rhino/Fusion native. Once the
   form is approved, it should get rebuilt (or at minimum re-verified) in
   whatever tool the team is actually printing from.

## Files

- `generate_enclosure.py` — the parametric model (edit the `STATIONS` table
  to change the taper/facet shape)
- `render.py` — shaded preview renderer
- `body.stl`, `top_plate.stl` — current output meshes
- `renders/` — preview images
