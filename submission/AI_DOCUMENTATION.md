# AI Documentation — Agentic Finance Reviewer

> What the AI is, where it runs, what it does, and — just as deliberately — what it is not allowed to do. Written for judges who want to verify that Agentic AI is a core component, not decoration.

## The workflow: four stages, one click for the operator

From the KFC finance user's seat this is one window and one action: open the reviewer,
run the batch, read the report, sign. Under that click, four stages:

```
 STAGE 1 · SWEEP (production design)
   a collector agent gathers invoices/docs from where they live
   (e-invoice feeds, mailboxes, store folders) and lands them as files
                                     │
                                     ▼
 STAGE 2 · EXTRACTION JUNCTION (production design — human-verified)
   documents become TYPED, STRUCTURED RECORDS (JSON) — unclear fields
   flagged "unknown", a human confirms before any check runs
                                     │
                                     ▼
 STAGE 3 · REVIEW  ◀━━ BUILT TO PILOT DEPTH — this is where money leaks
                    ┌─ deterministic tools (money-critical) ─┐
 payment batch ───▶ │ R-001 duplicate  (ledger + batch)      │
 (line-item level)  │ R-002 bank-change (vendor master)      │
                    │ R-003 threshold   (approval routing)   │
                    └────────────────┬───────────────────────┘
                                     │ findings + cited evidence
                                     ▼
                    ┌─ AI reviewer (claude-sonnet-4-6) ──────┐
                    │ reads each finding + its evidence      │
                    │ • writes the plain-language reason     │
                    │ • recommends a disposition (advisory)  │
                    │ • drafts the escalation note           │
                    │ grounded: never invent, always cite    │
                    └────────────────┬───────────────────────┘
                                     ▼
 STAGE 4 · HUMAN GATE — approval view; a person signs.
           The agent never approves anything.
```

**Why stage 3 is the one built deep — a deliberate call, not a gap.** Stages 1–2 are
patterns we have already built and tested in other projects (a browser-automation
collector, and a vision→strict-JSON extractor whose rule is "read only what is visibly
printed, null if not shown"). We chose not to make them this project's center because
KFC's own brief says the bulk of the data is already structured and ready — reading
documents is not where the money leaks. Validation is. One stage built to pilot depth
beats four stages built to demo depth.

**Two planes, two substrates.** Machines match on JSON — the data plane is typed,
deterministic, exact (`vendor_id + invoice_number`, amounts as integers). Humans and
AI continue on language — the reasons, recommendations, and escalation notes the model
writes. Money moves on the first plane; understanding moves on the second.

## Where the AI is (and why there)

**1. The reviewer's judgment layer (`reason_writer.py`) — core.**
For every flagged line-item, the model receives the finding and its exact evidence (ledger payment id, the two mismatched account numbers, the missing master-data record) and produces three things a human approver needs:
- **Reason** — plain language, names the concrete evidence, traceable.
- **Recommendation** — REJECT / HOLD FOR VERIFICATION / APPROVE WITH CAUTION, advisory only.
- **Escalation note** — ready to send to the approval level the threshold rule assigned.

This is judgment work, not templating: in the frozen demo run the model differentiates by evidence strength on its own — the ledger-confirmed duplicate gets REJECT; the unverifiable vendor and the changed bank account get HOLD FOR VERIFICATION with different verification instructions each. A raw flag ("DUPLICATE R-001") is not something a Finance approver can act on in 30 seconds; the AI's output is.

**2. The extraction junction (production design; capability demonstrated separately).**
In production, PDF/scanned invoices enter through an extraction junction: a vision model reads the document into structured fields, unclear fields are flagged "unknown," and a human confirms before any check runs. We already operate this exact pattern in another production stack (`vision.py` — screenshot → Claude vision → strict JSON, "read ONLY what is visibly printed, null if not shown"). The demo deliberately begins after this junction because KFC's own brief states the bulk of the data is already structured and ready — the expensive problem is validation, not reading.

## Why the money-decision layer is deterministic — a design position, not a gap

Payment release cannot run on probability. The checks that move money (duplicate, bank-change, thresholds) are deterministic, editable rule templates — same input, same output, auditable line by line. The AI sits where language and judgment actually help: reading evidence, explaining, recommending, drafting. **Deterministic where money moves, AI where the reason is written.** Teams that let an LLM decide payments have built a demo; this is built like something a Finance team could pilot.

## Hard guardrails (enforced in code)

- **Never invent** — the model is instructed to use only the provided evidence; an item with no anchor to compare against returns UNKNOWN and gates to a human (see the two unknown-vendor items in the demo run — the agent refuses to guess).
- **Human-gate always** — no code path approves a payment. Every item is staged for signature. Maps to KFC's Digital Signature integration requirement.
- **Always citeable** — every flag carries rule id + exact source (e.g. `paid_ledger / PAID-00418`); every AI output is generated from that citation and displays it.

## The agent loop the operator actually runs

`serve.py` is the one-window experience: click **Run review** and the agent pipeline executes stage by stage — load the batch → deterministic triage of all 761 line-items → the AI writes the case for every flag → the approval view is staged — with each step reported live to the browser as it actually runs. The second button, **Resubmit an already-paid invoice**, openly injects a random already-settled invoice back into the batch and re-runs the loop: a different vendor and amount is caught on every click, cited to its original payment id. The AI layer is load-bearing, not decorative: remove the API key and the pipeline says so — flagged cards degrade to raw citations marked "AI reason pending," and the 30-second human decision is gone.

## Models & stack

- **AI:** claude-sonnet-4-6 (Anthropic API) for the judgment layer; same family via vision for the extraction junction pattern.
- **Engine:** Python 3 stdlib only — no installs to run the pipeline. (Asset tooling like the GIF generator uses Pillow; the engine itself has zero dependencies.)
- **Rules:** editable JSON templates a finance user can change without code (deliberately *not* a natural-language rule parser — for money-movement rules, determinism beats convenience; plain-language rule authoring is the roadmap).
- **Data:** MODEL dataset (deterministic seed) — the format is real (VN e-invoice fields, StoreID organization, vendor/bank master), the vendors are not. Labelled MODEL at every layer; no real KFC transaction is shown or claimed.
