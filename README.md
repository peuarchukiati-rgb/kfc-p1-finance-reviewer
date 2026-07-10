# KFC-P1 — Agentic Finance Reviewer

**AABW 2026 · KFC F&B Track · P1: recurring payment processing for a 250+ store QSR chain**

An AI agent that reviews every recurring payment before it goes out — catches duplicates and bank-account fraud signals, explains each catch in plain language with cited evidence, recommends a disposition, and stages everything for a human signature.

**Deterministic where money moves, AI where the reason is written.**

🔗 **Live demo (approval view):** https://peuarchukiati-rgb.github.io/kfc-p1-finance-reviewer/

## Run it

```bash
python3 serve.py          # one-click web UI at http://127.0.0.1:8123
```

Two buttons: **Run monthly review** (300 requests / 761 line-items, full pipeline with live step progress) and **Resubmit an already-paid invoice** — openly resubmit a random paid invoice and watch it get caught, cited back to the original payment id.

Terminal path (same pipeline, no UI):

```bash
python3 run_demo.py        # dataset -> review -> AI reasons -> approval view
python3 demo_resubmit.py   # the live duplicate catch
```

The AI reason layer needs `ANTHROPIC_API_KEY` (env or `.env`). Without a key everything else still runs — the reason-writing step is skipped and the approval view falls back to the reasons committed for the public demo (or, with none present, to the deterministic citation with the AI reason marked as pending).

## What it does

| Stage | What happens |
|---|---|
| Review | Every line-item runs through 3 **editable rule templates** (`rules/rules.json`): R-001 duplicate (vs paid ledger + current batch) · R-002 bank-account change (vs vendor master) · R-003 threshold escalation routing. Deterministic — same input, same answer. |
| AI case-writing | For each flagged item, Claude (claude-sonnet-4-6) writes the plain-language **reason**, an advisory **recommendation** (REJECT / HOLD FOR VERIFICATION / APPROVE WITH CAUTION), and a ready-to-send **escalation note** — grounded strictly in the cited evidence. |
| Human gate | `output/approve_view.html` — the screen an approver reads in 30 seconds and signs. **Nothing is ever auto-approved.** |

Demo run: **761 line-items → 757 clean · 1 duplicate (cited to the original payment) · 1 bank-change · 2 unknown** (no anchor to compare → gated to a human, never guessed).

## Three disciplines, enforced in code

- **Never invent** — an item with nothing to compare against returns `UNKNOWN` and goes to a human. The agent refuses to guess.
- **Human-gate always** — no code path approves a payment. Maps to KFC's Digital Signature integration requirement.
- **Always citeable** — every flag carries rule id + exact source (`paid_ledger / PAID-00418`), feeding a timestamped audit trail (`output/audit_log.txt`).

## The extraction junction (production design)

In production, invoices enter through an extraction junction: the agent extracts, shows a side-by-side verify view, flags unclear fields as *unknown*, and a **human confirms the structured data before any check runs**. This demo begins **after** that junction — KFC's own brief states the bulk of the data is already structured and ready. Reading documents is not where the money leaks; validation is.

## Data

Everything here is **MODEL data** — the format is real (VN e-invoice fields, StoreID organization, vendor/bank master), the vendors are invented and labelled `[MODEL]` throughout. Deterministic seed; `python3 generate_dataset.py 60` is the small-batch variant. No real KFC transaction is shown or claimed.

## Files

```
serve.py             one-click web UI (stdlib http server, thin wrapper)
run_demo.py          full pipeline, one command (also the reset button)
demo_resubmit.py     resubmit a paid invoice -> watch the catch
generate_dataset.py  MODEL dataset builder (deterministic)
reviewer.py          the deterministic review engine
reason_writer.py     the AI case-writer (reason / recommendation / note)
build_report.py      renders the human approval view
rules/rules.json     editable rule templates — parameters, not code
submission/          description, AI documentation, deck, video script, visuals
```

The engine is Python 3 stdlib only — zero installs to run the pipeline. (`make_loop_gif.py`, an asset-generation tool, additionally uses Pillow.)

## Submission

See [`submission/SUBMISSION.md`](submission/SUBMISSION.md) · [`submission/AI_DOCUMENTATION.md`](submission/AI_DOCUMENTATION.md) — where the AI is, what it does, and what it is deliberately not allowed to do.

---

*The rules never guess. The AI always cites. A human signs everything.
And it was built the way it works: intent stated clearly, agents doing
the rest — by one person who doesn't write code.*

*That used to be the barrier. It isn't anymore.
This is everyone's craft now — go build your version.*

*— Peak · Agentic AI Build Week 2026*
