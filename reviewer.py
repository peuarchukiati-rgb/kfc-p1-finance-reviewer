"""
reviewer.py  —  KFC-P1 AI Finance Reviewer engine

Reads structured MODEL data (the demo begins AFTER the extraction junction —
no PDF is parsed here) and runs three deterministic, editable rules:

  R-001  Duplicate payment   -> anchored to paid ledger + current batch
  R-002  Bank-account-change -> compared to vendor master data
  R-003  Threshold routing    -> assigns the approval level each amount needs

Three principles are enforced in code, not in slides:
  * NEVER INVENT — if there is nothing to compare against, the item is 'unknown'
                   and gated to a human. It is never guessed clean or duplicate.
  * HUMAN-GATE   — this engine flags, cites, and STAGES. It never approves.
  * ALWAYS CITE  — every flag names the rule and the exact source it came from.

Output:  output/audit_log.txt   (timestamped plain log)
         output/review_results.json (structured, per line-item, with citations)
"""

import json
from datetime import datetime, timezone

# ---- load corpora + rules ---------------------------------------------------
master  = {v["vendor_id"]: v for v in json.load(open("data/vendor_master.json"))}
ledger  = json.load(open("data/paid_ledger.json"))
batch   = json.load(open("data/incoming_batch.json"))
rules   = json.load(open("rules/rules.json"))

# ---- build duplicate anchors from the ledger (historical PAID payments) ------
ledger_by_invoice   = {}   # (vendor_id, invoice_number) -> payment_id
ledger_by_recurring = {}   # (vendor_id, store_id, expense_type, billing_period) -> payment_id
for p in ledger:
    ledger_by_invoice[(p["vendor_id"], p["invoice_number"])] = p["payment_id"]
    ledger_by_recurring[(p["vendor_id"], p["store_id"], p["expense_type"], p["billing_period"])] = p["payment_id"]

# ---- build in-batch anchors (same invoice submitted twice in one batch) ------
batch_invoice_seen = {}
for req in batch:
    for li in req["line_items"]:
        key = (li["vendor_id"], li["invoice_number"])
        batch_invoice_seen.setdefault(key, []).append(li["line_id"])

# ---- audit log --------------------------------------------------------------
log_lines = []
def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
    log_lines.append(f"[{ts}] {msg}")

log("=== KFC-P1 AI FINANCE REVIEWER — RUN START ===")
log(f"corpora: {len(master)} vendors | {len(ledger)} ledger anchors | {len(batch)} requests")
log("mode: structured MODEL data (post-extraction junction). No payment will be released — human-gate active.")

# ---- rule checks (per line-item) --------------------------------------------
def check_duplicate(li, store_id):
    """R-001. Returns (status, citation). status in DUPLICATE / CLEAN / UNKNOWN."""
    strong = (li["vendor_id"], li["invoice_number"])
    rec    = (li["vendor_id"], store_id, li["expense_type"], li["billing_period"])

    if strong in ledger_by_invoice:
        return "DUPLICATE", f"invoice already PAID in ledger ({ledger_by_invoice[strong]})"
    if len(batch_invoice_seen.get(strong, [])) > 1:
        others = [x for x in batch_invoice_seen[strong] if x != li["line_id"]]
        return "DUPLICATE", f"same invoice submitted twice in this batch ({', '.join(others)})"
    if rec in ledger_by_recurring:
        return "DUPLICATE", f"this period already PAID in ledger ({ledger_by_recurring[rec]})"

    # not a duplicate on any anchor. Is there any basis to call it clean?
    if li["vendor_id"] not in master:
        return "UNKNOWN", "vendor not in master data — no basis to compare, needs human"
    return "CLEAN", "no matching anchor in ledger or batch (new period, known vendor)"

def check_bank_change(li):
    """R-002. Returns (status, citation)."""
    if li["vendor_id"] not in master:
        return "UNKNOWN", "vendor not in master data — cannot verify bank account, needs human"
    on_file = master[li["vendor_id"]]["bank_account_number"]
    if li["bank_account_number"] != on_file:
        return "BANK_CHANGE", f"payee account {li['bank_account_number']} != master {on_file}"
    return "CLEAN", "bank account matches master data"

def check_threshold(li):
    """R-003. Returns escalation level for the amount."""
    for tier in rules["R-003"]["tiers"]:
        if tier["up_to"] is None or li["amount"] <= tier["up_to"]:
            return tier["escalation"]
    return "CA + Cashier"

# ---- run --------------------------------------------------------------------
PRIORITY = {"DUPLICATE": 3, "BANK_CHANGE": 2, "UNKNOWN": 1, "CLEAN": 0}
results = []
for req in batch:
    for li in req["line_items"]:
        dup_status, dup_cite   = check_duplicate(li, req["store_id"])
        bank_status, bank_cite = check_bank_change(li)
        escalation             = check_threshold(li)

        # overall = the most serious finding across dimensions
        candidates = [(dup_status, "R-001", dup_cite), (bank_status, "R-002", bank_cite)]
        overall, rule_id, citation = max(candidates, key=lambda c: PRIORITY[c[0]])

        record = {
            "line_id": li["line_id"],
            "request_id": req["request_id"],
            "store_id": req["store_id"],
            "vendor": li["vendor_name"],
            "invoice_number": li["invoice_number"],
            "amount_vnd": li["amount"],
            "status": overall,
            "cited_from": {"rule": rule_id, "input_row": li["line_id"], "evidence": citation},
            "escalation_required": escalation,
            "decision": "STAGED FOR HUMAN APPROVAL",   # never auto-approved
        }
        results.append(record)
        if overall != "CLEAN":
            log(f"FLAG {overall} | {li['line_id']} | {li['vendor_name']} | "
                f"{li['amount']:,} VND | rule {rule_id} | {citation} | escalate: {escalation}")

# ---- summary (precision context) --------------------------------------------
from collections import Counter
counts = Counter(r["status"] for r in results)
total = len(results)
log("=== RUN COMPLETE ===")
log(f"reviewed {total} line-items | CLEAN {counts['CLEAN']} | "
    f"DUPLICATE {counts['DUPLICATE']} | BANK_CHANGE {counts['BANK_CHANGE']} | UNKNOWN {counts['UNKNOWN']}")
log("NO PAYMENT RELEASED. All items staged for human signature.")

# ---- write outputs ----------------------------------------------------------
open("output/audit_log.txt", "w").write("\n".join(log_lines) + "\n")
json.dump(results, open("output/review_results.json", "w"), indent=2, ensure_ascii=False)

# ---- console readout --------------------------------------------------------
print("\n----- PRECISION CONTEXT -----")
print(f"  {total} line-items reviewed")
print(f"  CLEAN        : {counts['CLEAN']}")
print(f"  DUPLICATE    : {counts['DUPLICATE']}   <- hero catch")
print(f"  BANK_CHANGE  : {counts['BANK_CHANGE']}   <- engine goes further")
print(f"  UNKNOWN      : {counts['UNKNOWN']}   <- 'I don't know' -> human (never invented)")
print("\n----- FLAGGED ITEMS (what a human sees) -----")
for r in results:
    if r["status"] != "CLEAN":
        print(f"  [{r['status']}] {r['line_id']} | {r['vendor']} | {r['amount_vnd']:,} VND")
        print(f"      cited: {r['cited_from']['rule']} — {r['cited_from']['evidence']}")
        print(f"      escalation: {r['escalation_required']} | {r['decision']}")
print("\nHuman-gate active: nothing approved. See output/audit_log.txt for the full trail.")
