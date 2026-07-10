"""
generate_dataset.py  —  KFC-P1 MODEL dataset builder

Produces THREE corpora the Finance Reviewer needs:
  1. data/vendor_master.json   -> vendor + bank master data (source of truth)
  2. data/paid_ledger.json     -> historical PAID payments (duplicate anchors)
  3. data/incoming_batch.json  -> this month's requests, down to line-item level

EVERYTHING here is MODEL data. The FORMAT is real; the vendors are invented.
Nothing is presented as a real KFC transaction or a real e-invoice.

Deterministic: a fixed random seed means the same dataset every run.
That is on purpose — the demo is frozen at D3 and must not drift.

Kill-switch (from the blueprint): default 300 requests. Pass a smaller N on the
command line (e.g. `python generate_dataset.py 60`) — 60 tells the same story.
"""

import json, random, sys

SEED = 20260712          # freeze seed — never change after D3
random.seed(SEED)

N_REQUESTS = int(sys.argv[1]) if len(sys.argv) > 1 else 300

# ---- MODEL vendor pool (format real, names invented) -----------------------
VENDORS = [
    # vendor_id, name, expense_type, bank_name
    ("V-LEASE-01", "Sao Mai Property Co.",        "rental",       "Vietcombank"),
    ("V-LEASE-02", "Nam Long Retail Spaces",      "rental",       "BIDV"),
    ("V-LEASE-03", "An Phu Mall Management",       "rental",       "ACB"),
    ("V-LEASE-04", "Hoa Binh Commercial JSC",      "rental",       "Techcombank"),
    ("V-ELEC-01",  "EVN HCMC Power (model)",       "electricity",  "Vietcombank"),
    ("V-ELEC-02",  "EVN Hanoi Power (model)",      "electricity",  "BIDV"),
    ("V-ELEC-03",  "EVN Central Power (model)",    "electricity",  "Agribank"),
    ("V-WATER-01", "SAWACO Water (model)",         "water",        "Vietcombank"),
    ("V-WATER-02", "Hanoi Water Ltd (model)",      "water",        "BIDV"),
    ("V-SVC-01",   "CleanPro Facility Services",   "service_fee",  "ACB"),
    ("V-SVC-02",   "SecureGuard Vietnam",          "service_fee",  "Techcombank"),
    ("V-SVC-03",   "GreenScape Maintenance",       "service_fee",  "MB Bank"),
]

def bank_acct(vendor_id):
    # stable fake account per vendor
    random.seed(vendor_id)
    acct = "".join(str(random.randint(0, 9)) for _ in range(11))
    random.seed(SEED + len(vendor_id))  # re-jitter but stay reproducible
    return acct

# rebuild master with stable accounts, then restore main seed
vendor_master = []
for vid, name, etype, bank in VENDORS:
    vendor_master.append({
        "vendor_id": vid,
        "vendor_name": name + " [MODEL]",
        "expense_type": etype,
        "bank_name": bank,
        "bank_account_number": bank_acct(vid),
        "status": "active",
    })
random.seed(SEED)
MASTER = {v["vendor_id"]: v for v in vendor_master}

STORES = [f"KFC-{c}-{i:03d}" for c in ("HCM", "HN", "DN", "CT") for i in range(1, 41)]

AMOUNT_RANGES = {   # realistic-ish monthly VND ranges per expense type
    "rental":      (30_000_000, 80_000_000),
    "electricity": (8_000_000, 25_000_000),
    "water":       (1_000_000, 4_000_000),
    "service_fee": (3_000_000, 10_000_000),
}

def rnd_amount(etype):
    lo, hi = AMOUNT_RANGES[etype]
    return round(random.randint(lo, hi), -3)  # round to nearest 1,000 VND

inv_counter = 1000
def next_invoice(prefix):
    global inv_counter
    inv_counter += 1
    return f"{prefix}-{inv_counter}"

# ---- 1. PAID LEDGER (anchors) : prior months already paid -------------------
paid_ledger = []
# every store has PAID rent+electricity for 2026-05 (prior period history).
for store in STORES:
    for vid in random.sample([v[0] for v in VENDORS], k=3):
        etype = MASTER[vid]["expense_type"]
        paid_ledger.append({
            "payment_id": f"PAID-{len(paid_ledger)+1:05d}",
            "vendor_id": vid,
            "store_id": store,
            "expense_type": etype,
            "invoice_number": next_invoice("INV-2605"),
            "billing_period": "2026-05",
            "amount": rnd_amount(etype),
            "bank_account_number": MASTER[vid]["bank_account_number"],
            "paid_date": "2026-06-03",
            "status": "PAID",
            "source": "MODEL",
        })

# ---- 2. INCOMING BATCH : current period 2026-06 -----------------------------
incoming = []
for r in range(1, N_REQUESTS + 1):
    store = random.choice(STORES)
    n_lines = random.randint(1, 4)
    line_items = []
    for L in range(n_lines):
        vid = random.choice([v[0] for v in VENDORS])
        etype = MASTER[vid]["expense_type"]
        line_items.append({
            "line_id": f"R{r:04d}-L{L+1}",
            "vendor_id": vid,
            "vendor_name": MASTER[vid]["vendor_name"],
            "expense_type": etype,
            "invoice_number": next_invoice("INV-2606"),
            "billing_period": "2026-06",
            "amount": rnd_amount(etype),
            "bank_account_number": MASTER[vid]["bank_account_number"],
            "source": "MODEL",
        })
    incoming.append({
        "request_id": f"REQ-2606-{r:04d}",
        "store_id": store,
        "requester": f"{store}-manager",
        "submitted_date": "2026-07-05",
        "line_items": line_items,
    })

# ---- SEED THE TEST CATCHES --------------------------------------------------
# Seeded test items get normal in-sequence line_ids like every other row, so
# the dataset stays uniform end to end. Their locations are written to
# demo/catch_map.json (git-ignored) so demo rehearsal can find them without
# hardcoding line ids anywhere.
def append_seeded(req, fields):
    r = int(req["request_id"].split("-")[-1])
    line_id = f"R{r:04d}-L{len(req['line_items']) + 1}"
    req["line_items"].append({"line_id": line_id, **fields})
    return line_id

catch_map = {}

# HERO: a duplicate — an invoice already PAID in the ledger, resubmitted now.
already_paid = random.choice(paid_ledger)
hero_req = random.choice(incoming)
catch_map["duplicate_hero"] = {
    "line_id": append_seeded(hero_req, {
        "vendor_id": already_paid["vendor_id"],
        "vendor_name": MASTER[already_paid["vendor_id"]]["vendor_name"],
        "expense_type": already_paid["expense_type"],
        "invoice_number": already_paid["invoice_number"],   # same invoice, already paid
        "billing_period": already_paid["billing_period"],
        "amount": already_paid["amount"],
        "bank_account_number": already_paid["bank_account_number"],
        "source": "MODEL",
    }),
    "request_id": hero_req["request_id"],
    "anchor": already_paid["payment_id"],
}

# EXTENSION: a bank-account-change — real vendor, wrong (changed) payee account.
bank_vid = "V-LEASE-01"
bank_req = random.choice(incoming)
catch_map["bank_change"] = {
    "line_id": append_seeded(bank_req, {
        "vendor_id": bank_vid,
        "vendor_name": MASTER[bank_vid]["vendor_name"],
        "expense_type": "rental",
        "invoice_number": next_invoice("INV-2606"),
        "billing_period": "2026-06",
        "amount": rnd_amount("rental"),
        "bank_account_number": "99988877766",   # does NOT match master
        "source": "MODEL",
    }),
    "request_id": bank_req["request_id"],
}

# NEVER-INVENT GATE: line-items from vendors NOT in master data. The agent must
# say "unknown", not guess. Plausible vendor names/ids that simply aren't
# onboarded to master yet — exactly the real-world "unknown" case, not a giveaway.
UNKNOWN_VENDORS = [("V-SVC-07", "Thanh Cong Cleaning Co. [MODEL]"),
                   ("V-LEASE-09", "Phu My Hung Lease [MODEL]")]
catch_map["unknown"] = []
for uvid, uname in UNKNOWN_VENDORS:
    unk_req = random.choice(incoming)
    catch_map["unknown"].append({
        "line_id": append_seeded(unk_req, {
            "vendor_id": uvid,                     # not in vendor_master
            "vendor_name": uname,
            "expense_type": "service_fee",
            "invoice_number": next_invoice("INV-2606"),
            "billing_period": "2026-06",
            "amount": rnd_amount("service_fee"),
            "bank_account_number": "".join(str(random.randint(0, 9)) for _ in range(11)),
            "source": "MODEL",
        }),
        "request_id": unk_req["request_id"],
    })

# ---- write -----------------------------------------------------------------
import os
json.dump(vendor_master, open("data/vendor_master.json", "w"), indent=2, ensure_ascii=False)
json.dump(paid_ledger,   open("data/paid_ledger.json", "w"), indent=2, ensure_ascii=False)
json.dump(incoming,      open("data/incoming_batch.json", "w"), indent=2, ensure_ascii=False)

# presenter-only rehearsal map — where the seeded catches live (git-ignored).
os.makedirs("demo", exist_ok=True)
json.dump(catch_map, open("demo/catch_map.json", "w"), indent=2, ensure_ascii=False)

line_count = sum(len(r["line_items"]) for r in incoming)
print(f"MODEL dataset built (seed {SEED}):")
print(f"  vendor_master : {len(vendor_master)} vendors")
print(f"  paid_ledger   : {len(paid_ledger)} historical PAID payments (anchors)")
print(f"  incoming_batch: {len(incoming)} requests / {line_count} line-items")
print(f"  seeded catches: 1 duplicate (hero), 1 bank-change, 2 unknown")
print(f"  hero duplicate hidden in : {hero_req['request_id']}")
print(f"  bank-change hidden in    : {bank_req['request_id']}")
