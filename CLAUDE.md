# Rules for Claude

This folder is a Grasshopper model that the user changes only by chatting with you.
Every change you make becomes a version in the history tree (tools/, app/). Never ask
the user to wire, drag or click anything in Grasshopper; you write the scripts and the
tools rebuild the definition.

## How the model is split

One file in `scripts/` per building category, each becoming its own labelled Python 3
component in Grasshopper. The demo model (a stadium, `demo/stadium/`) uses:

| level | files (category) | element names |
|---|---|---|
| massing | `massing.py` (rough volumes, before the detailed scripts) | `M-RING`, `M-N` |
| structure | `site.py`, `bowl.py`, `rakers.py`, `concourses.py`, `roof_trusses.py`, `transoms.py` | `PL-012`, `TU2-R05-B023`, `RK2-B014`, `CS1-B007`, `RT-012`, `TR-04` |
| envelope | `envelope.py` | `EF04-117`, `ER12-033` |
| interior | `hospitality.py`, `team_rooms.py` | `BX-S012`, `TM-W2` |
| mep | `lighting.py`, `services.py` | `FL-012`, `LF-03`, `AHU-07`, `DP-07` |

The history adds a fifth level, massing, by itself whenever the building's overall extents
(length, width or height) change.

- Never merge two categories into one file. A new kind of thing (a lift, a canopy) gets
  its own file with its own level.
- Name every element, and keep names stable: name by grid position or role
  (`C-A1`, `B1-A1-B1`), never by loop index, so the same column has the same name in
  every version. The history compares versions element by element through these names.
- MEP and interior must fit inside the structure and envelope of the same version. Read the
  shared inputs (pitch, tiers, envelope and member sizes) instead of hard-coding them.
- Units are metres in the scripts. In titles and summaries give member sizes in mm
  (500 × 1,500 mm raker, Ø1,000 mm duct) and building dimensions in m.

## Script format

```python
# category: raker frames
# level: structure
# material: concrete
# gh-input: rows1 int 20 0 40           (name, int|float, default, min, max)
# gh-input: raker_d float 1.2 0.6 2.0
import Rhino.Geometry as rg

a = []       # Breps, closed where possible
names = []   # one name per item in a, same order
floors = []  # floor plates (slab scripts only), for floor area
stats = []   # optional: "label|unit|value" lines
```

- `material` sets which volume total the script's closed elements count towards
  (concrete, steel, ETFE...).
- A script can report its own figures as `stats`, lines of `label|unit|value`
  (seats, viewing distance); they appear with the measurements.
- `# inside-view: hide` keeps a script out of the inside picture (a roof structure, say),
  next to the envelope, which is always hidden there.
- Inputs with the same name in different scripts share one slider. Change a design value
  by editing its `gh-input` default.
- Sliders arrive as floats; cast counts with `int()`.

## After each design change

Before you end the turn, write `.history/pending.json`:

```json
{"title": "Gable roof over the bar", "summary": "One or two plain sentences on what changed in the building, not in the code."}
```

- `title`: 3-6 words, what changed in the building, in architectural terms.
- `summary`: state only what the model shows: sizes, positions, counts. Don't claim
  materials, performance or code compliance the model doesn't contain.
- The Stop hook then rebuilds the model in Rhino, takes the picture, measures, and commits
  the version. Don't commit yourself.
- To start from an older version ("try X from #3"): `py tools/start_from.py 3`, then edit.
  The new version branches from #3.

## Combine

When your prompt carries a combine request (two versions picked in the history app),
don't merge mechanically. Read both, then talk it through with the user first: ask what
they want from each, and push back when the two don't fit (are these two different
buildings? does the MEP of one still fit the massing of the other? MEP must never sit
outside the building). Only build once you agree. Then write `pending.json` with
`"parents": [a, b]` added, and the result is a version with two parents.
