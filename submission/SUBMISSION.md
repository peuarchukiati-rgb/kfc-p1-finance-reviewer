# Agentic Finance Reviewer — KFC F&B Track (P1)

**One line:** An AI agent that reviews every recurring payment before it goes out — catches duplicates and fraud signals, explains each catch in plain language with cited evidence, recommends a disposition, and stages everything for a human signature. Deterministic where money moves, AI where judgment is written.

## Project description (paste into portal)

KFC Vietnam processes ~300 recurring payment requests a month across 250+ stores through a fully manual 5-level paper chain — duplicate payments are hard to catch, audit trails are thin, and the monthly cycle burns ~2 days of manual work.

The Agentic Finance Reviewer is the AI reviewer that sits in front of that chain. A payment batch comes in at line-item level; the agent triages every item through three editable rule templates — duplicate detection anchored to the paid-payments ledger and the current batch, bank-account-change fraud signals against vendor master data, and threshold-based approval routing. For every flagged item, the AI then does what only an AI can: reads the finding and its evidence, writes the plain-language reason an approver actually needs, recommends a disposition (REJECT / HOLD FOR VERIFICATION / APPROVE WITH CAUTION), and drafts the escalation note ready to send to the right approval level — every claim traceable to a cited source (the exact ledger entry, the exact mismatched account numbers).

Three disciplines are enforced in code, not slides: **never invent** (an item with nothing to compare against returns "unknown — needs human," never a guess), **human-gate always** (the agent stages and recommends; it never approves — mapping directly to KFC's Digital Signature integration requirement), and **always citeable** (every flag names the rule and exact source, feeding a timestamped audit trail).

On the demo dataset (300 requests / 761 line-items, MODEL data — real format, modelled vendors): 757 cleared clean, 1 duplicate caught before double-payment, 1 bank-account substitution flagged, 2 unknown-vendor items gated to a human. Nothing auto-approved. The result: a 5-handoff paper chain collapses to 1 review + 1 signature — the step-collapse behind KFC's own ~80% cycle-time target.

For the finance user it is one window, one click: run the batch, read the report, sign. Under that click sit four stages — sweep (collect documents from where they live), extraction junction (documents → typed structured records, human-verified), review (this build), human gate. Stages 1–2 are patterns we have built and tested in other projects; here we deliberately built stage 3 to pilot depth instead, because KFC's brief says the data is already structured and ready — reading documents is not where the money leaks. Validation is.

Built solo, by a non-developer, orchestrating AI agents — because if a non-dev can build an enterprise-grade agentic reviewer, anyone can build.

## Submission checklist mapping
- **Project description** — above.
- **Live demo** — https://peuarchukiati-rgb.github.io/kfc-p1-finance-reviewer/ (the approval view a signer reads; full pipeline runs locally via `python3 serve.py`).
- **Demo video** — https://youtu.be/LO5VAOD2Vmg
- **Images** — `user-ai-journey.png` (the workflow: who does what, human lane vs agent lane), `reviewer-loop.gif` (the loop in 7 beats), `screenshot-approve-view.png` (the human approval screen: reason + recommendation + escalation note per catch), `screenshot-run-log.png` (761 line-items triaged, precision context).
- **AI documentation** — `AI_DOCUMENTATION.md` (where the AI is, what it does, what it is deliberately not allowed to do).
- **Pitch deck + Q&A prep** — `DECK.md`.
- **Source code** — https://github.com/peuarchukiati-rgb/kfc-p1-finance-reviewer
- **Project target** — KFC F&B Track, Problem 1 (recurring payment processing).
