![The reviewer loop](https://peuarchukiati-rgb.github.io/kfc-p1-finance-reviewer/reviewer-loop.gif)

## Inspiration

KFC Vietnam's finance team pushes ~300 recurring payment requests a month, across 250+ stores, through a fully manual 5-level paper chain — five signatures, two days, every month. Their own brief says it plainly: Excel, email, no workflow tool. The moment that hooked me: a duplicate payment isn't a UX problem — it's real money leaving the building. I wanted the catch to happen *before* the money moves, not in next month's reconciliation.

And a personal one: I'm not a developer. This project tests a thesis — if a non-dev can build an enterprise-grade agentic reviewer by orchestrating AI agents, anyone can build.

## What it does

For the finance user it's one window and one click: **"This month's batch is in."** Press Run review, and the agent works through the batch stage by stage — with each step reported live as it actually executes, not a spinner.

- **Deterministic triage of all 761 line-items** through three editable rule templates: duplicate detection anchored to the paid-payments ledger AND the current batch; bank-account-change fraud signals against vendor master data; threshold-based escalation routing (HOD → F&A → CA → Cashier). The demo reviews payment line-items because that is where duplicate and bank-account risk is visible; flagged exceptions roll back up into the payment-request approval flow for human sign-off.
- **The risk picture first** — before any detail, the approver sees what a CFO asks first: **133.3M VND held back in the baseline model run**, broken down by category and sorted by money at stake. The resubmit test adds a fresh duplicate catch on top.
- **The AI writes the case** for every flag: a plain-language reason, an advisory recommendation (REJECT / HOLD FOR VERIFICATION / APPROVE WITH CAUTION), and a ready-to-send escalation note — every claim grounded in cited evidence (the exact ledger entry, the exact mismatched account numbers).
- **Signing produces a real handoff.** Approve an item and a `handoff-*.md` downloads instantly — the complete decision state in one file: prose for the next human, the verbatim payment record as JSON for the next system. Generated deterministically from the same record that rendered the card: nothing added, nothing dropped, nothing invented. Reject and a `return-*.md` travels back to the requesting store with the reason attached.
- **Nothing is ever auto-approved.** The agent prepares, flags, recommends, and drafts. A person signs.
- **The AI is not the detector and never the signer.** Its role is the case-building layer: it turns raw cited findings into the human-readable finance case — reason, advisory disposition, escalation instruction, and handoff note — so approvers act faster without losing auditability.

Demo run: 757 cleared clean · 1 duplicate caught before double-payment · 1 bank-account substitution flagged · 2 unknown-vendor items gated to a human — because when the agent has nothing to compare against, it says "unknown" instead of guessing.

And the question every finance director asks — *what if someone resubmits an invoice we already paid?* There's a button for that. It openly resubmits a random already-settled invoice and re-runs the review. A different vendor and amount is caught on every click, cited back to its original payment id. Ask it to run again; it catches a different one.

## How we built it

**Deterministic where money moves, AI where the reason is written.** Payment release can't run on probability — so the checks that move money are deterministic, auditable rule templates. The AI (claude-sonnet-4-6, called with zero dependencies via stdlib) sits where judgment and language actually help: reading each finding's evidence, explaining, recommending, drafting.

![User / AI journey — who does what](https://peuarchukiati-rgb.github.io/kfc-p1-finance-reviewer/user-ai-journey.png)

Run it four times and you can see the architecture: **every number, citation, and recommendation is identical across runs — that's the rules. Every sentence is written fresh — that's the AI.** If you can tell where one ends and the other begins, the design is working.

Three disciplines are enforced in code, not slides: **never invent** (no anchor → UNKNOWN → human), **human-gate always** (no code path approves; maps directly to KFC's Digital Signature integration requirement), **always citeable** (every flag carries rule id + exact source into a timestamped audit trail).

The reasoning layer is a single-file, zero-dependency adapter — Claude today, any approved LLM endpoint tomorrow (Bedrock, Azure, a local model). The engine's disciplines — never invent, always cite, a human signs — live in code, not in the model: the model is swappable, the money rules are not.

Built solo, by a non-developer, orchestrating AI agents end-to-end — the build itself ran on persistent state handoffs between AI sessions, the same discipline the product ships.

## Challenges we ran into

- **Making "agentic" mean something in finance.** A rules engine with an AI caption fails the bar. I answered with substance: the AI differentiates its recommendations by evidence strength on its own — the ledger-confirmed duplicate gets REJECT; the unverifiable vendor gets HOLD with specific verification steps. Remove the API key and the pipeline honestly degrades: cards mark the AI reason as pending. The AI is load-bearing, not decorative.
- **Trust design over feature count.** The brief lists five build areas plus three enterprise integrations. Solo, in days, building all of it means five half-things. I built the slice where money actually leaks — validation, duplicates, audit — to pilot depth, and put extraction, full routing UI, and accounting integration on the architecture as spoken design. One stage at pilot depth beats four at demo depth.
- **The last mile of a handoff.** An approval that ends at a button click still loses information. I made every decision produce a portable artifact — intent and task in one file — so what the approver decided travels whole to accounting or back to the requester.

## Accomplishments that we're proud of

- The full pipeline runs end-to-end with every hard constraint verifiable in the output: 0 auto-approved, 0 uncited flags, unknowns gated instead of guessed.
- The live resubmit button — judges can test the system's honesty themselves, repeatedly, and it catches a different invoice every time.
- Every signed or rejected item emits a complete, machine-and-human-readable handoff file — the approval chain's memory, generated verbatim, no GL codes assumed (mapping stays in KFC's chart of accounts).
- A non-developer shipped this — engine, dataset, audit trail, web UI, approval flow — in days.

## What we learned

The expensive problem in enterprise finance AI isn't reading documents — KFC's brief says the bulk of the data is already structured. It's trust. And trust comes from knowing where NOT to use AI: deterministic rules where money moves, AI judgment where humans need language. The human never left the loop — they moved to the gates: confirm at the entry, sign at the exit, and the machine in the middle cites every line.

And the quiet one: if someone who can't code can build this, the barrier was never the code — it's knowing exactly what must never be guessed.

## What's next for Agentic Finance Reviewer

- **Extraction junction live** — vision-based document reading into typed, human-verified records ("read only what's printed, null if not shown" — a pattern I've built and tested in other projects), so PDF/scanned invoices enter the same disciplined pipeline.
- **Plain-language rule authoring** — deliberately not built now (money rules need determinism first): finance users describing a control in Thai/Vietnamese/English, compiled into a deterministic template with human sign-off.
- **Pilot integration** — Entra ID sign-in, Digital Signature at the human gate, journal mapping into the existing ledger flow.

## Built with

`python` `anthropic` `claude-sonnet-4-6` `json-rule-templates` `stdlib-http` `html` `zero-dependencies`

## Optional Links

- **Live demo:** https://peuarchukiati-rgb.github.io/kfc-p1-finance-reviewer/
- **Source:** https://github.com/peuarchukiati-rgb/kfc-p1-finance-reviewer
- **AI documentation:** https://github.com/peuarchukiati-rgb/kfc-p1-finance-reviewer/blob/main/submission/AI_DOCUMENTATION.md
