"""
demo_resubmit.py — the live catch, performed in front of the audience.

The question a Finance director actually asks: "what happens if someone
resubmits an invoice we already paid?" This script does exactly that, openly:
it takes a real entry from the paid-payments ledger, submits it again as a
brand-new incoming request, and re-runs the reviewer. Watch it get caught,
cited back to the original payment id, with the AI's reason and a REJECT
recommendation — in seconds.

    python3 demo_resubmit.py          # resubmit a rental invoice (biggest amount)
    python3 demo_resubmit.py 42       # or pick ledger entry #42

Reset to the frozen baseline afterwards with:  python3 run_demo.py
"""

import json
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).parent

ledger = json.load(open(HERE / "data" / "paid_ledger.json"))
batch = json.load(open(HERE / "data" / "incoming_batch.json"))

# Pick the entry to resubmit: by index arg for a rehearsed fixed run, else a
# RANDOM paid invoice — every click catches a different vendor/amount/citation.
# Safe to randomize: any already-paid invoice resubmitted IS a duplicate by
# construction, so the catch is guaranteed regardless of the pick.
import random
if len(sys.argv) > 1:
    entry = ledger[int(sys.argv[1]) % len(ledger)]
else:
    entry = random.choice(ledger)

print("\033[1m── LIVE: resubmitting an already-paid invoice ──\033[0m")
print(f"  ledger says : {entry['invoice_number']} · {entry['amount']:,} VND · "
      f"vendor {entry['vendor_id']} · PAID on {entry['paid_date']} ({entry['payment_id']})")
print(f"  now entering: the SAME invoice, as a fresh payment request\n")

n = len(batch) + 1
batch.append({
    "request_id": f"REQ-LIVE-{n:04d}",
    "store_id": entry["store_id"],
    "requester": f"{entry['store_id']}-manager",
    "submitted_date": "2026-07-12",
    "line_items": [{
        "line_id": f"R{n:04d}-L1",
        "vendor_id": entry["vendor_id"],
        "vendor_name": next((v["vendor_name"] for v in
                             json.load(open(HERE / "data" / "vendor_master.json"))
                             if v["vendor_id"] == entry["vendor_id"]), entry["vendor_id"]),
        "expense_type": entry["expense_type"],
        "invoice_number": entry["invoice_number"],   # the same invoice
        "billing_period": entry["billing_period"],
        "amount": entry["amount"],
        "bank_account_number": entry["bank_account_number"],
        "source": "MODEL",
    }],
})
json.dump(batch, open(HERE / "data" / "incoming_batch.json", "w"),
          indent=2, ensure_ascii=False)

# Inject-only mode: serve.py drives the rest of the pipeline itself so it can
# report real per-step progress to the browser.
if os.environ.get("KFC_INJECT_ONLY"):
    print("injected — batch now has the resubmitted invoice")
    sys.exit(0)


def step(title, cmd):
    print(f"\033[1m── {title} ──\033[0m")
    r = subprocess.run(cmd, cwd=HERE)
    if r.returncode != 0:
        sys.exit(r.returncode)


step("Reviewing the batch again (now 301 requests)", ["python3", "reviewer.py"])
step("AI reviewer writes the reasons", ["python3", "reason_writer.py"])
step("Rendering the approval view", ["python3", "build_report.py"])

view = HERE / "output" / "approve_view.html"
if not os.environ.get("KFC_NO_BROWSER"):
    webbrowser.open(view.as_uri())
print(f"\nCaught. The resubmitted invoice is flagged DUPLICATE, cited to "
      f"{entry['payment_id']} — staged for a human, not paid.")
print("Reset to the frozen baseline:  python3 run_demo.py")
