"""What Claude gets when the user asks to combine two versions.

  py tools/combine.py 7 12      prints the brief (also printed by the prompt hook)
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, ".history")


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True, encoding="utf-8").stdout


def commit_of(n):
    for line in git("log", "--format=%H %s").splitlines():
        h, subject = line.split(" ", 1)
        if subject.split(" ", 1)[0] == "#%d" % n:
            return h
    raise ValueError("no version #%d" % n)


def load(n):
    with open(os.path.join(HIST, str(n), "version.json"), encoding="utf-8") as f:
        return json.load(f)


def by_category(va, vb):
    """Per category: elements only in A, only in B, and in both but different."""
    ea, eb = va["elements"], vb["elements"]
    out = {}
    for name in set(ea) | set(eb):
        cat = (ea.get(name) or eb.get(name))["category"]
        row = out.setdefault(cat, {"only_a": 0, "only_b": 0, "differ": 0, "same": 0})
        if name not in eb:
            row["only_a"] += 1
        elif name not in ea:
            row["only_b"] += 1
        elif ea[name]["box"] != eb[name]["box"] or ea[name]["size"] != eb[name]["size"]:
            row["differ"] += 1
        else:
            row["same"] += 1
    return out


def brief(a, b):
    a, b = int(a), int(b)
    va, vb = load(a), load(b)
    ha, hb = commit_of(a), commit_of(b)
    lines = [
        "COMBINE REQUEST from the history app: the user picked #%d and #%d to combine." % (a, b),
        "Do not merge mechanically. Look at both, then talk it through with the user before building:",
        "ask what they want from each, and push back where they don't fit (different buildings? does the",
        "MEP of one fit the massing of the other? MEP must never sit outside the building).",
        "When you agree, build it, then write .history/pending.json with title, summary and \"parents\": [%d, %d]." % (a, b),
        "",
    ]
    for n, v in ((a, va), (b, vb)):
        lines.append("#%d %s, by %s, %s. %s" % (n, v["title"], v["author"], v["time"][:16], v["summary"]))
        lines.append("  numbers: %s" % json.dumps(v["numbers"]))
        for pic in ("picture", "inside"):
            if v.get(pic):
                lines.append("  %s: %s" % (pic, os.path.join(HIST, str(n), v[pic])))
    lines += ["", "Elements by category (only in #%d / only in #%d / in both but different / same):" % (a, b)]
    for cat, r in sorted(by_category(va, vb).items()):
        lines.append("  %-10s %d / %d / %d / %d" % (cat, r["only_a"], r["only_b"], r["differ"], r["same"]))
    lines += ["", "Script differences, #%d -> #%d:" % (a, b), git("diff", ha, hb, "--", "scripts")[:20000] or "(none)"]
    lines += ["", "Full scripts: git show %s:scripts/<name>.py and git show %s:scripts/<name>.py" % (ha[:9], hb[:9])]
    return "\n".join(lines)


if __name__ == "__main__":
    print(brief(sys.argv[1], sys.argv[2]))
