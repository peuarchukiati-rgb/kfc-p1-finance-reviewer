# VIDEO_SCRIPT.md — 90-Second Demo

KFC-P1 · Agentic Finance Reviewer — demo video script.
One take, 1280x800 browser window, cuts noted below.

---

## 0:00–0:08 · THE GAG

**Screen:** A plain frame titled "Your current dashboard:" — paper, Excel, email. (Screenshot frame 1 of `submission/reviewer-loop.gif`.)

**Line:**
> "This is KFC Vietnam's payment approval system today. Five signatures. Two days. Every month. Their own brief says it: Excel, email, no workflow tool."

## 0:08–0:20 · THE BATCH

**Screen:** Open `http://127.0.0.1:8123` (serve.py UI). Home view shows "This month's batch is in."

**Line:**
> "Here's the same month — 300 requests, 761 line items. One click."

## 0:20–0:40 · THE RUN

**Screen:** Click **Run review**. Spinner runs (cut the wait). Land on the approval view.

**Line:**
> "The agent checks every line — duplicates against the paid ledger, bank accounts against master data. 757 clear themselves. Four wait for a human. Every flag cites its exact source."

## 0:40–1:05 · THE CARD

**Screen:** Scroll to one card — the DUPLICATE. Show the AI reason, the REJECT recommendation, and the escalation note.

**Line:**
> "For each catch, the AI writes the reason, a recommendation, and the escalation note — grounded in the evidence, never invented. This one: already paid, ledger entry PAID-00418. Recommendation: reject."

## 1:05–1:20 · THE RESUBMIT

**Screen:** Back to home. Click **Resubmit & watch**. The catch appears, cited to the original payment id.

**Line:**
> "The question every finance director asks — what if someone resubmits an invoice we already paid? Watch."

## 1:20–1:30 · THE CLOSE

**Screen:** End on the sign / reject buttons.

**Line:**
> "Nothing is paid until a person signs. Deterministic where money moves, AI where the reason is written. I'm not a developer — I built this in five days. That's the point."

---

## RECORDING NOTES

- Record in **one take** at a **1280x800 browser window**.
- **Cut the two ~25s waits** (the run-review spinner and the resubmit run) in the edit.
- **Fallback:** if wifi dies during the AI step, the pre-generated approval view at `output/approve_view.html` still renders — reasons are already on disk.
- Record **before** any rehearsal edits; keep an **offline copy** of this file.
