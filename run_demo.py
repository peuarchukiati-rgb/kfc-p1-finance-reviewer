"""
run_demo.py — one command, full pipeline, live.

Rebuilds the frozen MODEL dataset, reviews every line-item, writes the AI
reasons for whatever got flagged, renders the approval view, opens it.
This is the Beat-1 demo command — and the reset button after demo_resubmit.py.

    python3 run_demo.py         # full 300-request batch
    python3 run_demo.py 60      # kill-switch size
"""

import os
import subprocess
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).parent


def step(title, cmd):
    print(f"\n\033[1m── {title} ──\033[0m")
    r = subprocess.run(cmd, cwd=HERE)
    if r.returncode != 0:
        sys.exit(r.returncode)


size = sys.argv[1:2] or []
step("1/4  Build MODEL dataset (deterministic, frozen seed)",
     ["python3", "generate_dataset.py", *size])
step("2/4  Review every line-item (deterministic rules, cited)",
     ["python3", "reviewer.py"])
step("3/4  AI reviewer writes reason + recommendation + escalation note",
     ["python3", "reason_writer.py"])
step("4/4  Render the human approval view",
     ["python3", "build_report.py"])

view = HERE / "output" / "approve_view.html"
if not os.environ.get("KFC_NO_BROWSER"):
    webbrowser.open(view.as_uri())
print(f"\nOpened {view.name} — nothing was paid. Every flag waits for a human signature.")
