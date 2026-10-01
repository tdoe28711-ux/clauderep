# UXDG 340 — Bike UI Bench Demo

Project context for Claude Code. Read this before helping with anything
in this folder.

## The project

SCAD, UXDG 340 Interactive Product Design, Fall 2026. Team Hero.

We're designing a futuristic motorcycle interface tied to "Contronym," a
film script from the Dramatic Writing department. Two bikes in the story:
Whispering Torque and Screaming Pistons. Our deliverable is a working
bench demo displayed in a hallway at the end of the quarter.

**Team:** Ben Stefanik (UI simulation and software), Grant Leslie,
Tyson Doering, Yu Dian Dong (rig, budget, docs). I'm Tyson, goes by Ty.

**Dates:**
- Oct 13 — midterm, physical prototypes required
- Nov 3 — progress check
- Nov 17 — final presentation
- Nov 19 — final deliverables

## The concept

Three features we designed, these names are ours, don't rename them:
- **Smart Grips + HUD**
- **Team Link**
- **Scout Drone**

The core idea for the demo is **multimodal directional feedback**. When a
hazard appears on one side, the rider gets it on two channels at once:
vibration in that grip, and a light in that corner of their peripheral
vision. Both say the same thing. The redundancy is the point, grounded in
aviation research on multi-channel alerting (the stick-shaker precedent).

## The bench demo

Someone walks up to a pedestal, grips real handlebars, twists a throttle,
and rides through a simulation on a monitor while feeling haptics in the
grips.

**Hardware:**
- Arduino Uno, driving both the vibration motors and the LEDs from one
  board so they stay in sync with each other
- Vibration motor modules (driver + flyback diode already on the board,
  so no separate MOSFETs needed)
- E-bike thumb throttle, hall effect, 3-wire, reads into an analog pin
- MTB riser handlebar, 31.8mm clamp, 720mm wide, with lock-on grips
- LEDs at the monitor's top corners
- Ben's simulation built in Reality Composer / Xcode

**Sync:** throttle position goes Uno → USB serial → sim. Hazard events
come back sim → Uno, which fires the motor and LED on that side.

**Fallback if the budget doesn't land:** PS5 controller + monitor, which
Ben already owns. Costs $0 and still proves directional haptics, since the
DualSense has independent left/right rumble.

## Critical unresolved issue

**The slides contradict themselves about whether the rider drives or
watches.** One slide says people "ride through" the UI and that buttons
and throttle "trigger real screen changes." Another says you press one key
and the demo plays itself while you watch.

These are different projects. The first justifies the throttle and
buttons; the second makes them props. This needs a team decision and it
affects the parts list. Don't write copy or build hardware that assumes
one without flagging it.

## Current task: the enclosure

See @tank-spec.md for the full build spec.

Short version: a compact 3D-printed tank-shaped enclosure, roughly
190 × 135 × 70mm, that hides the Arduino and has the handlebars clamped
to the top. Needs to look like a motorcycle tank, not a project box, and
print for under ~300g of filament.

**Three attempts have already failed:**
1. Sculpted full-size tank at 418 × 252 × 173mm — correct proportions,
   but 2kg of filament. Too big, too expensive.
2. Plain rounded box — right size, no character. Ugly.
3. Faceted shell at 185 × 130 × 66mm — right size, right idea, bad
   execution.

The size envelope is right. The form inside it isn't resolved.

**The reason those failed:** geometry was written blind into Rhino scripts
with no visual feedback, then relayed through me by eye, one round trip at
a time. If you work on this, render previews before asking me to run
anything.

## Environment

- Windows, Rhino 8
- Scripts must run **inside** Rhino, not from PowerShell. `rhinoscriptsyntax`
  only exists in Rhino's own Python. Use `EditPythonScript` from Rhino's
  command box
- `rs.AddBox` is reliable. `rs.ExtrudeCurve` + `rs.CapPlanarHoles` produced
  objects Rhino wouldn't accept as solids for booleans, so avoid that
  pattern
- Figma Slides for the deck

## How I want you to work

- **No em dashes.** Nobody types like that.
- Don't rewrite or restructure my team's content. The slide copy, feature
  names, and concepts are ours. Fix typos and errors, propose changes, but
  don't silently replace our writing with yours.
- Check arithmetic. Two totals on our budget slides were wrong and nobody
  caught it.
- Short answers. Bullets over paragraphs. I'll ask if I want depth.
- If you're guessing, say so. I'd rather hear "untested" than find out by
  running it.
