"""Start the next change from an older version: "try X from #3".

  py tools/start_from.py 3
Puts the scripts of #3 back in scripts/ and makes #3 the parent of the next version,
so it branches from #3. Rhino updates when that version is saved.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import combine  # noqa: E402

ROOT = combine.ROOT


def checkout(n):
    h = combine.commit_of(n)
    keep = set(combine.git("ls-tree", "--name-only", h, "scripts/").split())
    for f in os.listdir(os.path.join(ROOT, "scripts")):
        if "scripts/" + f not in keep and f.endswith(".py"):
            os.remove(os.path.join(ROOT, "scripts", f))
    combine.git("checkout", h, "--", "scripts")


if __name__ == "__main__":
    n = int(sys.argv[1])
    checkout(n)
    os.makedirs(os.path.join(ROOT, ".history", "tmp"), exist_ok=True)
    with open(os.path.join(ROOT, ".history", "tmp", "start_from.json"), "w") as f:
        json.dump({"version": n}, f)
    print("next version branches from #%d" % n)
