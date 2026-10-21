"""Restore an older version: its scripts come back, Rhino rebuilds, and it is saved as a
new version branching from the one restored.

  py tools/restore.py 3 [--author "Name"]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import autosave  # noqa: E402
import start_from  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("n", type=int)
ap.add_argument("--author")
a = ap.parse_args()
start_from.checkout(a.n)
old = autosave.load(a.n)
rec = autosave.save("Restore #%d" % a.n, "Scripts restored from #%d (%s)." % (a.n, old["title"]), a.author, [a.n])
print(json.dumps({k: v for k, v in rec.items() if k != "elements"}, indent=2))
