# Handlebar Demo Enclosure — Build Spec

Team Hero · UXDG 340 · Interactive Product Design
Last updated 2026-10-01

---

## 1. What this is

A 3D-printed enclosure that sits on a pedestal in a hallway. Handlebars
clamp to the top of it. Inside it hides an Arduino and wiring. A monitor
behind it plays a first-person riding video.

People walk up, grip the bars, twist the throttle, and feel directional
haptic feedback in the grips while matching lights fire in the top
corners of the screen.

The enclosure is the only part of the rig anyone sees, so it carries the
whole visual impression of the project.

**Reference:** a previous year's SCAD project ("Honda HMI Redesign,"
Team Bravo) did a compact two-tone box — tan printed base, black top
plate, bars clamped on, round display in the middle. That's the right
scale and the right level of finish to aim at.

---

## 2. Aesthetic direction

- Should read as a **motorcycle tank**, not a project box
- Angular / faceted is preferred over smooth organic curves — it prints
  without supports and looks deliberate
- A ridge or spine running front to back ties it to the project's story
  (the bikes in the script are named Whispering Torque and Screaming
  Pistons; a dragon-adjacent read is welcome, scales are not required)
- Two-tone finish is worth copying from the reference. Printing the body
  and the top plate in different colors makes the parting line look
  intentional
- **Do not** make it a plain rounded rectangle. Already tried, looks like
  a router
- **Do not** make it a full-size sculpted tank. Already tried at
  418 × 252 × 173mm, which is roughly 2kg of filament and four days of
  printing

---

## 3. Hard constraints

### Print
| Constraint | Value |
|---|---|
| Max bed (Ender 3) | 220 × 220 × 250 mm |
| Max bed (Bambu P1S / X1) | 256 × 256 × 256 mm |
| Max bed (Prusa MK4) | 250 × 210 × 220 mm |
| Wall thickness | 2.4–3.0 mm (3–4 perimeters at 0.4 nozzle) |
| Supports | None. All overhangs ≤ 45° from vertical |
| Filament budget | Under ~300 g total |
| Print time budget | Under ~20 h total |

Confirm which printer is actually available before finalizing size. If
SCAD has large-format, the bed constraint relaxes.

### Orientation
Design so the largest flat face is the bed face. The cavity opening
should face down, which makes the natural print orientation also the
natural assembly orientation.

---

## 4. What has to fit inside

| Component | Footprint | Height | Notes |
|---|---|---|---|
| Arduino Uno R3 | 68.6 × 53.4 mm | 15 mm bare | Allow **30 mm** with jumper wires standing up |
| Half-size breadboard | 83 × 55 mm | 10 mm | Verify against the one you actually have |
| Wiring, connectors, slack | — | — | Allow generous room, this is what always overflows |

**Minimum usable internal volume: 130 × 85 × 40 mm.**

That fits the Uno and breadboard side by side with wire room. Going
smaller means stacking components, which makes debugging miserable at
2am before a critique.

Not inside the enclosure:
- Vibration motor modules — these live in or against the **grips**
- LEDs — these mount at the **monitor's** top corners
- Throttle — mounts on the **bar** at 22.2 mm diameter
- Power supply — external wall plug, only the barrel jack comes in

---

## 5. Recommended external envelope

**190 × 135 × 70 mm** (length × width × height)

Derived from: 130 × 85 × 40 internal, plus 3 mm walls, plus the taper
needed for a faceted form that narrows toward the nose and tail.

This fits every bed listed above in one piece, should land around
200–280 g of PLA, and is close to the reference photo's proportions.

If it needs to shrink, cut height before length. A low wide tank looks
better than a tall narrow one and the Uno sets the floor on footprint,
not on height.

---

## 6. Feature placement

Origin at the **front-bottom-center**. X runs back along the length,
Y runs side to side, Z runs up.

### Cavity
- X: 17% to 83% of length (≈ 32 mm to 158 mm)
- Y: ±29% of width (≈ ±39 mm)
- Z: from −1 mm (open to the bench) up to 62% of height (≈ 43 mm)
- Opens downward. No floor

### Top mounting pad
- Flat, horizontal, centered on length
- Approximately 100 × 80 mm
- At roughly 84% of height (≈ 59 mm)
- Purpose: a flat landing for the bar clamp hardware

### Cable port
- Rear face, centered
- 16 mm wide × 11 mm tall
- Bottom edge ~1 mm above the bench so cables lie flat

### USB access
- Side face, positioned over wherever the Uno's USB jack lands
- ~14 × 10 mm
- Lets you reflash without lifting the whole rig off the pedestal
- Decide the Uno's orientation first, then cut this to match

---

## 7. Handlebar mounting

**Correction (2026-10-01):** the original 31.8mm / 720mm Wake MTB riser
below was a placeholder. The bar actually purchased is a VUOZIP 7/8"
(22mm) dirt bike handlebar set, aluminum, uniform 22mm diameter along its
whole length (not an oversized 31.8mm center section tapering to 22mm
grips). The throttle (FT76X half-twist) is confirmed 7/8"/22mm compatible.
Overall bar width for this specific part is not yet confirmed from the
listing - don't assume 720mm still holds.

| Spec | Value |
|---|---|
| Bar clamp diameter | 22 mm (7/8") - was 31.8mm, corrected above |
| Bar grip diameter | 22.2 mm (same tube, uniform diameter) |
| Bar overall width | Unconfirmed for the VUOZIP set - was 720mm for the old Wake riser, don't carry that number forward |

**Use a separate flat top plate for the clamps.** This still matters even
at 22mm - two clamps spaced for a wide bar span more than the enclosure is
long. A separate plate solves this and matches the reference photo.

Plate spec:
- 210 × 110 mm, 6 mm thick
- Printed flat, or cut from 6 mm plywood or acrylic
- Bolts down to the enclosure's top pad with 4 × M4
- **Leave the clamp bolt holes undrilled in CAD.** Buy the clamps, set
  them on the plate, mark through, drill. Guessing bolt spacing wastes a
  print

**Structural warning:** printed plastic alone should not be the only
thing holding a 720 mm bar that people lean on and twist. A printed post
will flex and eventually crack at a layer line. Either keep the bar
height low so leverage is small, or use a real bike stem bolted through
to a plywood base with the printed enclosure as a shell around it.

### Bar height
In the reference photo the pedestal does the work, not the enclosure.
Bars sit roughly 120 mm above the pedestal surface with the pedestal at
standing height. Don't try to make the enclosure raise the bars.

---

## 8. Decided vs. open

### Decided
- Faceted over smooth
- Cavity opens downward, no separate base plate needed
- Separate top plate for clamps
- Compact: under 200 mm in any dimension
- Two-tone finish

### Still open
- Whether a round display gets mounted on top (the reference had one; our
  concept currently relies on grip haptics and screen-corner lights, so a
  display may be redundant)
- Exact facet language — how many planes, how sharp
- Whether spine fins stand proud of the ridge (they'd need supports)
- Whether the demo is rider-driven or plays back automatically, which
  decides whether the throttle and buttons are functional or props

---

## 9. Context for whoever picks this up

Three attempts have already missed:

1. **Full sculpted tank, 418 × 252 × 173 mm.** Correct motorcycle
   proportions relative to a 720 mm bar, but roughly 2 kg of filament and
   days of print time. Rejected on cost and size.
2. **Plain rounded box, 200 × 170 × 70 mm.** Right size, no character.
   Rejected on looks.
3. **Faceted shell, 185 × 130 × 66 mm.** Right size, right idea, the
   execution looked bad in Rhino.

The gap is aesthetic, not dimensional. The size envelope in section 5 is
sound. What's needed is a better-resolved form inside that envelope,
developed with visual feedback rather than written blind into a script.
