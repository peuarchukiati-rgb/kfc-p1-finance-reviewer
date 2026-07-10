# DECK.md — AABW Demo Day · 3-Minute Pitch + 2-Minute Q&A

**KFC-P1 · Agentic Finance Reviewer · KFC F&B Track (Problem 1: recurring payment processing)**

Format: 8 slides, ~3:00 total including the live browser demo (slide 3 hands off to the
running app at `http://127.0.0.1:8123`; fallback is the pre-generated
`output/approve_view.html`, offline-safe). Every claim on every slide traces to
`submission/SUBMISSION.md`, `submission/AI_DOCUMENTATION.md`, or the frozen demo run.

Timing is cumulative. Demo budget inside slide 3: ~40 seconds, pre-staged.

---

## SLIDE 1 — "Your current dashboard" · 0:00–0:12

**TITLE:** Your current dashboard

**VISUAL:** Frame 1 of `submission/reviewer-loop.gif` — the plain frame titled
"Your current dashboard:" showing paper, Excel, email. Nothing else on the slide.

**SPOKEN LINE:**
> "This is KFC Vietnam's payment approval system today. Five signatures. Two days.
> Every month. I'm not making that up — it's in your own brief: Excel, email,
> no workflow tool."

**TIME:** 12 seconds. Land the gag, smile, move — the brief is the joke, not the team.

---

## SLIDE 2 — The problem in one number · 0:12–0:30

**TITLE:** ~300 requests. 250+ stores. Every month. No net underneath.

**VISUAL:** Text slide, three lines large:
`~300 payment requests / month` · `250+ stores` · `duplicate payments + thin audit trail`.

**SPOKEN LINE:**
> "Three hundred recurring payment requests a month, across more than two hundred fifty
> stores, moving through that paper chain. Two things fall through it: duplicate payments,
> and the audit trail to catch them. And a duplicate payment isn't a UX problem — it's
> money leaving the building."

**TIME:** 18 seconds.

---

## SLIDE 3 — The reviewer (LIVE DEMO HANDOFF) · 0:30–1:18

**TITLE:** The reviewer

**VISUAL:** One line of text — "Live: this month's batch, one click." — then switch to
the browser. Demo sequence (pre-staged): home view → **Run review** → approval view →
scroll to the duplicate card (AI reason, REJECT recommendation, escalation note,
citation `paid_ledger / PAID-00418`). If time allows, flash **Resubmit & watch**.
Fallback: `output/approve_view.html` renders offline.

**SPOKEN LINE (handoff):**
> "So instead of telling you about it, let me just run this month's batch. Three hundred
> requests, seven hundred sixty-one line items — watch what one click does."

**SPOKEN (over the demo):**
> "Seven hundred fifty-seven clear themselves. Four wait for a human. This one — a
> duplicate. The AI writes the reason, recommends reject, drafts the escalation note,
> and cites the exact ledger entry it found: PAID-00418. Nothing is paid until a
> person signs."

**TIME:** 8 seconds handoff + ~40 seconds demo = 48 seconds.

---

## SLIDE 4 — Architecture · 1:18–1:46

**TITLE:** Deterministic where money moves, AI where the reason is written

**VISUAL:** `submission/user-ai-journey.png` — the four-stage journey
(sweep → extraction junction → review → human gate).

**SPOKEN LINE (verbatim positioning — do not paraphrase):**
> "Here's the design position: deterministic where money moves, AI where the reason is
> written. The judgment layer that touches money is rules — because real money can't run
> on probability. In production, invoices enter through an extraction junction — the
> agent extracts, a human confirms the structured data before any check runs. Today's
> demo begins after that junction. And that's deliberate: reading documents is the intake
> problem. Where the money leaks is validation — so that's the stage we built to
> pilot depth."

**TIME:** 28 seconds.

---

## SLIDE 5 — Trust by design · 1:46–2:08

**TITLE:** Three disciplines, enforced in code

**VISUAL:** `submission/screenshot-approve-view.png` — the approval screen showing a
flagged card with reason, recommendation, escalation note, and citation. Overlay three
short labels: NEVER INVENT · HUMAN-GATE ALWAYS · ALWAYS CITEABLE.

**SPOKEN LINE:**
> "Three disciplines are in the code, not the slides. Never invent — an item with
> nothing to compare against returns unknown and goes to a human; it's never guessed
> clean. Human-gate always — the agent stages and recommends, it never approves; that
> maps directly to your Digital Signature integration. And always citeable — every flag
> names the rule and the exact source, feeding a timestamped audit trail. In a pilot,
> this is where Microsoft Entra ID, Digital Signature, and your data-protection
> controls would plug in."

**TIME:** 22 seconds.

---

## SLIDE 6 — The proof the AI is real · 2:08–2:26

**TITLE:** Same numbers. Fresh reasoning. Every run.

**VISUAL:** `submission/screenshot-run-log.png` — the run log showing 761 line-items
triaged with precision context. Optionally two reason-line excerpts from separate runs
side by side, same citation, different sentences.

**SPOKEN LINE:**
> "How do you know the AI isn't a template string? Run it four times: every number
> identical, every sentence different. The rules don't move; the AI writes fresh
> reasoning every run, grounded in the same cited evidence. That's the division of
> labor working."

**TIME:** 18 seconds.

---

## SLIDE 7 — The 80% · 2:26–2:40

**TITLE:** 5 hand-offs + re-keying → 1 review + 1 signature

**VISUAL:** Text slide. Left: `5 hand-offs + re-keying`. Arrow. Right:
`1 review + 1 signature`. Below, small: `~80% cycle-time target — KFC's own number,
projected from the step collapse.`

**SPOKEN LINE:**
> "Five hand-offs plus re-keying collapses to one review and one signature. The
> roughly-eighty-percent cycle-time cut is KFC's own target, projected from that step
> collapse — not measured from live runs. I'd rather tell you that straight than
> dress up a demo number as a field result."

**TIME:** 14 seconds.

---

## SLIDE 8 — CLOSE · 2:40–3:00

**TITLE:** That's the real pilot

**VISUAL:** Text slide, one line: `Built solo. Non-developer. Five days.`

**SPOKEN LINE:**
> "The technology to catch a duplicate payment isn't new. What's new is who can build
> it and how fast. I'm not a developer — I built this in five days. If a non-dev can
> build an enterprise-grade agentic reviewer, anyone in your company can build.
> That's the real pilot."

**TIME:** 20 seconds. Stop talking. Hold the slide through applause into Q&A.

---
---

# Q&A PREP — full spoken answers

## Q1 · "Why didn't you handle the PDF/OCR side?"

> "It's designed in — it's the extraction junction on the architecture slide: a vision
> model reads the document into structured fields, unclear fields come back as unknown,
> and a human confirms before any check runs. We already operate that exact pattern in
> another production stack, so the capability is proven — I didn't need to prove it twice.
> And your own brief says the bulk of this data is already structured and ready for AI.
> Reading documents is not where the money leaks — validation is — so that's the stage
> I built to pilot depth."

## Q2 · "Isn't the AI just decorative? The rules do the catching."

> "The rules catch; the AI does the judgment work a human approver actually needs. Look
> at the frozen run: the model differentiates by evidence strength on its own — the
> ledger-confirmed duplicate gets REJECT, while the unverifiable vendor and the changed
> bank account each get HOLD FOR VERIFICATION with different verification instructions.
> A raw flag like 'DUPLICATE R-001' is not something Finance can act on in thirty
> seconds; the reason, recommendation, and escalation note are. And the proof it's real
> generation, not a template: run it four times — every number identical, every sentence
> different, all grounded in the same citation."

## Q3 · "How can you trust AI with payments?"

> "You can't — which is exactly why this system never asks you to. The human didn't
> leave the loop; the human moved to the gates. A person confirms the structured data
> at entry, and a person signs at exit — no code path in this build approves a payment.
> In the middle, the machine does what machines are good at: it checks every line
> deterministically and cites the exact source for every flag. So trust isn't a feeling
> here — it's an audit trail you can read line by line."

## Q4 · "Can a non-technical finance user write the rules?"

> "Today the rules are editable JSON templates — a finance user changes a threshold or
> a routing level without touching code, and the change is exact and auditable. What I
> deliberately did not build is natural-language rule authoring, because rules that move
> money need determinism — 'roughly what I meant' is fine for a draft email, not for a
> payment threshold. Plain-language rule authoring, compiled down to these same
> deterministic templates with a human confirming the compiled rule, is the roadmap.
> I've already prototyped that pattern separately; it's proof number two, not this pilot."

## Q5 · "What's your false-positive rate?"

> "On the demo batch: seven hundred sixty-one line items, seven hundred fifty-seven
> cleared, four surfaced — and every one of the four is something a finance team would
> genuinely want a human to see: one confirmed duplicate, one bank-account substitution,
> two vendors with no master-data anchor. The design choice that keeps noise down is
> unknown-gating: when the system has no anchor to reason from, it says 'unknown — needs
> human' instead of guessing in either direction. That's what keeps it selective — the
> reviewer earns trust by being quiet when things are clean, not by painting the screen
> red. Real-world rates get measured in the pilot, on real ledger data."

## Q6 · "What exactly is checked against what?"

> "Duplicates are anchored two ways: each line item is checked against the paid-payments
> ledger — has this vendor-plus-invoice already been paid — and against the current batch
> itself, so the same invoice submitted twice this month is caught even before it ever
> reaches the ledger. Bank-account changes are checked against the vendor master data —
> if the account on the request doesn't match the account on file, that's a fraud signal
> and it's flagged with both numbers cited. Thresholds route by amount to the approval
> level your policy defines. And if an item has no anchor in either the ledger or the
> master data, it isn't guessed — it gates to a human as unknown."

## Q7 · Governance (2 sentences)

> "A pilot would plug into Microsoft Entra ID and your data-protection controls, and the
> deterministic checks run entirely locally — the batch never leaves the environment.
> Only the flagged finding's fields are sent to the model API to write the reason;
> everything else stays local, and every AI output is logged with its citation in the
> audit trail."

---

## DELIVERY NOTES

- Slide 3 is the only moving part: pre-stage the browser tab before walking on; verify
  `output/approve_view.html` opens offline as fallback.
- Slide 4's positioning lines are verbatim — they are also the answers to Q1 and Q3.
  Saying them in the pitch makes the Q&A feel pre-answered.
- Slide 7's honesty ("projected, not measured") is a feature in front of a General
  Director — own it at full volume, don't mumble it.
- Numbers to hold in your head: 300 requests · 761 line items · 757 clean · 4 flagged ·
  1 duplicate (PAID-00418) · 1 bank change · 2 unknowns · 5 days · 250+ stores.
