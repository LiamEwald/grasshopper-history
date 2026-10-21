"""Run a script inside Rhino through RhinoCode.exe and wait for its result file.

rhinocode returns before the script finishes, so we delete the result file,
start the script, then poll for the file to reappear.
"""
import json
import os
import subprocess
import sys
import time

RHINOCODE = r"C:\Program Files\Rhino 8\System\RhinoCode.exe"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(script, result, timeout=60):
    """Run tools/<script> in Rhino; return the parsed result JSON or None."""
    result = os.path.join(ROOT, ".history", "tmp", result)
    if os.path.exists(result):
        os.remove(result)
    try:
        subprocess.run([RHINOCODE, "script", os.path.join(ROOT, "tools", script)],
                       capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    end = time.time() + timeout
    while time.time() < end:
        if os.path.exists(result):
            try:
                with open(result, encoding="utf-8") as f:
                    return json.load(f)
            except ValueError:
                pass  # still being written
        time.sleep(0.25)
    return None


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1], sys.argv[2]), indent=2))
