"""Save one version: build in Rhino, measure, compare with the parent, picture, commit.

As the Stop hook (no arguments) it reads .history/pending.json, which Claude writes at
the end of a design turn: {"title", "summary", "parents"?}. From the command line:

  py tools/autosave.py --title "Gable roof" --summary "..." [--author "Name"] [--parent 3 ...]

Versions are numbered 1, 2, 3... Each is one git commit "#<n> <title>" holding scripts/
and .history/<n>/ (version.json, picture.webp, inside.webp). The parent is the newest
version, unless start_from.py picked another or parents are given (restore, combine).
No change in scripts/ and no parents given = no version. Never raises (it's a hook).
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rhino  # noqa: E402
import pictures  # noqa: E402

ROOT = rhino.ROOT
HIST = os.path.join(ROOT, ".history")
TMP = os.path.join(HIST, "tmp")
LEVELS = ["massing", "structure", "envelope", "interior", "mep"]  # most significant first: the tag is the first one touched
OUTER = ("structure", "envelope")  # their elements make up the building's overall extents
MOVE = 0.002  # metres an element's box must move to count as changed (small changes count too)
RESIZE = 0.001  # share its volume or area must change


def git(*args, check=True):
    r = subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode:
        raise RuntimeError("git %s: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def versions():
    return sorted(int(os.path.basename(os.path.dirname(p))) for p in glob.glob(os.path.join(HIST, "*", "version.json")))


def load(n):
    with open(os.path.join(HIST, str(n), "version.json"), encoding="utf-8") as f:
        return json.load(f)


def read_json(name):
    path = os.path.join(HIST, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def compare(old, new):
    """Element tables -> {added, removed, changed} lists of names."""
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = []
    for name in sorted(set(old) & set(new)):
        a, b = old[name], new[name]
        moved = max(abs(x - y) for x, y in zip(a["box"], b["box"])) > MOVE
        resized = abs(a["size"] - b["size"]) > RESIZE * max(abs(a["size"]), 1e-6)
        if moved or resized:
            changed.append(name)
    return {"added": added, "removed": removed, "changed": changed}


def extents(elements):
    """Overall bounding box of structure and envelope, rounded to 2 mm steps."""
    boxes = [e["box"] for e in elements.values() if e["level"] in OUTER]
    if not boxes:
        return None
    lo = [min(b[i] for b in boxes) for i in range(3)]
    hi = [max(b[i + 3] for b in boxes) for i in range(3)]
    return [round(v / MOVE) for v in lo + hi]


def script_levels():
    """Levels of the scripts whose text changed, for versions with no visible change."""
    out = git("status", "--porcelain", "--", "scripts").splitlines()
    files = [l[3:].strip() for l in out]
    levels = set()
    for f in files:
        path = os.path.join(ROOT, f)
        if os.path.exists(path):
            for line in open(path, encoding="utf-8"):
                if line.startswith("# level:"):
                    levels.add(line.split(":", 1)[1].strip())
    return levels


def save(title, summary, author=None, parents=None, prompt=""):
    os.makedirs(TMP, exist_ok=True)
    have = versions()
    n = (have[-1] + 1) if have else 1
    start = read_json("tmp/start_from.json").get("version")
    explicit = bool(parents)
    parents = [int(p) for p in parents] if parents else ([int(start)] if start else have[-1:])
    if not git("status", "--porcelain", "--", "scripts") and not explicit:
        return None  # nothing changed

    build = rhino.run("gh_build.py", "build.json")
    if build is None:  # no version without a model: keep the change for the next try
        raise RuntimeError("Rhino is not reachable. Start Rhino, run StartScriptServer, then save again.")
    meas = (rhino.run("measure.py", "measure.json") if build.get("ok") else None) or {"ok": False}
    elements = meas.get("elements", {})

    parent = load(parents[0]) if parents else None
    diff = compare(parent["elements"], elements) if parent else {"added": sorted(elements), "removed": [], "changed": []}
    touched = diff["added"] + diff["changed"]
    lv = {elements[e]["level"] for e in touched} | {parent["elements"][e]["level"] for e in diff["removed"]}
    if parent and extents(parent["elements"]) != extents(elements):
        lv.add("massing")  # the overall length, width or height changed
    if not lv:
        lv = script_levels()
    levels = [l for l in LEVELS if l in lv]

    folder = os.path.join(HIST, str(n))
    os.makedirs(folder, exist_ok=True)
    pics = {"picture": None, "inside": None, "side": None}
    if meas.get("ok"):  # every version gets a picture, even when the change looks small
        removed_boxes = [parent["elements"][e]["box"] for e in diff["removed"]]
        pics = pictures.take(rhino, TMP, folder, red=touched if parent else [], removed=removed_boxes,
                             inside=bool(parent) and bool(lv - {"envelope", "massing"}))

    record = {
        "n": n,
        "title": title,
        "summary": summary,
        "prompt": prompt,
        "author": author or git("config", "user.name", check=False) or "Unknown",
        "time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "parents": parents,
        "level": levels[0] if levels else None,
        "levels": levels,
        "changes": diff if parent else {"added": [], "removed": [], "changed": []},
        "numbers": meas.get("numbers"),
        "values": build.get("values", {}),
        "errors": build.get("errors", {}),
        "warnings": meas.get("warnings", []),
        "build_error": None if build.get("ok") else build.get("error"),
        "picture": pics["picture"],
        "inside": pics["inside"],
        "side": pics["side"],
        "elements": elements,
    }
    with open(os.path.join(folder, "version.json"), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=1)

    git("add", "-A", "--", "scripts", folder)
    msg = "#%d %s\n\n%s" % (n, title, summary)
    args = ["commit", "-q", "-m", msg]
    if author:
        args.append("--author=%s <%s@example.com>" % (author, author.lower().replace(" ", ".")))
    git(*args)
    for f in ("pending.json", "tmp/start_from.json"):
        if os.path.exists(os.path.join(HIST, f)):
            os.remove(os.path.join(HIST, f))
    return record


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title")
    ap.add_argument("--summary", default="")
    ap.add_argument("--author")
    ap.add_argument("--parent", action="append", default=[])
    a = ap.parse_args()
    try:
        pending = read_json("pending.json")
        prompt = read_json("prompt.json").get("prompt", "")
        title = a.title or pending.get("title") or " ".join(prompt.split()[:6]) or "Untitled change"
        summary = a.summary or pending.get("summary") or prompt
        rec = save(title, summary, a.author or pending.get("author"), a.parent or pending.get("parents"), prompt)
        if rec:
            rec = {k: v for k, v in rec.items() if k != "elements"}
        print(json.dumps(rec, indent=2) if rec else "no change")
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    main()
