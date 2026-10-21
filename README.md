# Grasshopper History

A history tree for a Grasshopper model that you design by chatting with Claude Code.
Every change Claude makes becomes a version: a short title, the level it touched
(massing, structure, envelope, interior, MEP), who made it, its measurements, a code diff,
and a picture with the changed elements marked in red. You can restore any version,
branch from it, or pick two and work out with Claude how to combine them.

The rules Claude follows when it models are in [CLAUDE.md](CLAUDE.md).

## What you need

- Rhino 8 (Windows), with Grasshopper
- Claude Code
- Git
- Node 20 or newer
- Python 3 with Pillow (`py -m pip install pillow`)

## Setup

1. Clone this repo.
2. In Rhino, run `StartScriptServer` once per Rhino session. It lets the tools run
   scripts inside Rhino through `RhinoCode.exe`.
3. Install the app: `cd app && npm install`, and the server: `cd server && npm install`.

## Start

1. Open Claude Code in this folder (the hooks in `.claude/settings.json` only load here).
2. Start the history: `cd server && npm start`, then open http://localhost:5174.
3. Ask Claude for a change. When it finishes the turn, the model rebuilds in Rhino and
   the new version appears in the tree.

## How it works

- `scripts/` holds the model, one Python 3 component per building category.
- The Stop hook runs `tools/autosave.py`: rebuild `model.gh` in Rhino, measure, compare
  every named element with the parent version, take a picture with the changed elements
  in red, and commit the scripts and `.history/<n>/` as one version.
- `server/` reads the versions from git and `.history/`; `app/` is the tree.
- Rhino always shows the current model. Looking at an old version never changes it;
  only a confirmed Restore does.
- A version's parents are recorded in `.history/<n>/version.json`. The git history itself
  is linear (one commit per version); branches and combines exist in the version tree.

## Measurements and their limits

- Height: from ±0.00 to the highest point of the model.
- Gross floor area: the floor plates the scripts output, at their outer edge, openings
  included. Footprint: the plan projection of those plates, overlaps counted once.
- Volume per material: the sum of the closed elements of the scripts with that material.
  Where elements overlap (a post through a beam), the overlap is counted twice.
- Changed elements are found by comparing each named element's bounding box and volume
  with the parent version (2 mm / 0.1 % tolerance). A change that keeps both, such as a
  rotation in place or an opening moved within a slab, is not detected.

## Demo

`py demo/run.py` builds the demo history from an empty `.history/`, through the real
pipeline: about 90 versions of a football stadium by three fictional authors (Liam, Maya,
Jonas). It starts with rough massing studies, one branch per person, then runs in parallel
phases where each person owns one branch (bowl, structure and site; envelope, roof and rooms;
services and lighting), combined at the end of each phase, through to the 2014 capacity
expansion and the 2015 LED facade. A step on a colleague's branch is titled as a handoff.

It is a reconstruction in the manner of the Allianz Arena, Munich (Herzog & de Meuron with
ArupSport, 2002-2005), not the architects' design process. What it follows from the published
record, what is estimated and what is invented is listed in [demo/SOURCES.md](demo/SOURCES.md).
It is a design and coordination model: no connections, no structural analysis, no code checks.
