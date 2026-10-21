"""UserPromptSubmit hook: keep the prompt for the version, and hand over a combine request.

When the history app's Combine button has written .history/combine-request.json, this
prints both versions to Claude (what a hook prints is added to Claude's context) and
marks the request as handed over.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import combine  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIST = os.path.join(ROOT, ".history")
try:
    data = json.load(sys.stdin)
    os.makedirs(HIST, exist_ok=True)
    with open(os.path.join(HIST, "prompt.json"), "w", encoding="utf-8") as f:
        json.dump({"prompt": data.get("prompt", "")}, f)
    req = os.path.join(HIST, "combine-request.json")
    if os.path.exists(req):
        with open(req, encoding="utf-8") as f:
            a, b = json.load(f)["versions"]
        print(combine.brief(a, b))
        os.replace(req, os.path.join(HIST, "combine-request-sent.json"))
except Exception:
    pass
