"""
reason_writer.py — the ONE visible-AI moment.

Everything else the reviewer does is deterministic. This is the single place an
AI does what only an AI can: turn a flagged finding + its exact cited evidence
into a plain-language reason a busy finance approver reads in seconds — grounded
strictly in the facts given, never inventing.

Reads the flagged items from output/review_results.json, asks Claude for one
reason per item (from ONLY the provided evidence), writes output/reasons.json.

Key: ANTHROPIC_API_KEY in env, or a line `ANTHROPIC_API_KEY=sk-...` in .env
(git-ignored). No key -> exits cleanly; the approval view falls back to the raw
citation and marks the AI reason as pending. Zero third-party deps (urllib only).
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

MODEL = os.environ.get("KFC_REASON_MODEL", "claude-sonnet-4-6")

SYSTEM = (
    "You are the AI reviewer inside a human-gated finance approval flow. You are "
    "given ONE flagged payment finding with its exact evidence. Produce the three "
    "things the human approver needs, as a JSON object with exactly these keys:\n"
    '  "reason"        - 1-2 plain-language sentences explaining the flag, naming '
    "the concrete evidence (payment id, account numbers, vendor) so it is traceable.\n"
    '  "recommendation" - one of "REJECT", "HOLD FOR VERIFICATION", or '
    '"APPROVE WITH CAUTION", followed by a short clause saying why. This is '
    "advisory only — the human signs, never you.\n"
    '  "escalation_note" - 1-2 sentences, ready to paste, addressed to the '
    "escalation level named in the finding, telling them exactly what to verify "
    "before signing.\n"
    "HARD RULES: use ONLY the facts given — never invent a number, name, date, or "
    "claim not present. If the evidence says the vendor is unknown, do not guess "
    "who they are. Attribute rules correctly: the rule id in the finding is the "
    "rule that fired; the escalation level comes from the threshold rule (R-003). "
    "Reply with ONLY the JSON object, no fences, no preamble."
)


def load_key():
    k = os.environ.get("ANTHROPIC_API_KEY")
    if k:
        return k
    env = Path(".env")
    if env.exists():
        for line in env.read_text().splitlines():
            if line.strip().startswith("ANTHROPIC_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def reason_for(item, key):
    facts = (
        f"Finding: {item['status']}\n"
        f"Vendor: {item['vendor']}\n"
        f"Invoice: {item['invoice_number']}\n"
        f"Amount: {item['amount_vnd']:,} VND\n"
        f"Rule: {item['cited_from']['rule']}\n"
        f"Evidence (verbatim): {item['cited_from']['evidence']}\n"
        f"Escalation required: {item['escalation_required']}"
    )
    body = json.dumps({
        "model": MODEL, "max_tokens": 500, "system": SYSTEM,
        "messages": [{"role": "user", "content": facts}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages", data=body,
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    text = "".join(b.get("text", "") for b in data.get("content", [])).strip()
    # Parse the structured reply; tolerate stray fences.
    clean = text.replace("```json", "").replace("```", "").strip()
    try:
        out = json.loads(clean)
    except json.JSONDecodeError:
        # Degrade gracefully: keep the raw text as the reason, no rec/note.
        return {"reason": text, "recommendation": None, "escalation_note": None}
    return {
        "reason": out.get("reason", "").strip(),
        "recommendation": (out.get("recommendation") or "").strip() or None,
        "escalation_note": (out.get("escalation_note") or "").strip() or None,
    }


def main():
    key = load_key()
    results = json.load(open("output/review_results.json"))
    flagged = [r for r in results if r["status"] != "CLEAN"]
    if not key:
        print("No ANTHROPIC_API_KEY (env or .env) — skipping AI reasons.")
        print(f"{len(flagged)} flagged items will use committed public-demo reasons if "
              "present; otherwise they fall back to deterministic citations. "
              "Add .env with ANTHROPIC_API_KEY= then rerun to regenerate.")
        return
    reasons = {}
    for item in flagged:
        try:
            reasons[item["line_id"]] = reason_for(item, key)
            print(f"  {item['line_id']} [{item['status']}] -> reason written")
        except urllib.error.HTTPError as e:
            print(f"  {item['line_id']} ERROR {e.code}: {e.read().decode()[:200]}")
            sys.exit(1)
    json.dump(reasons, open("output/reasons.json", "w"), indent=2, ensure_ascii=False)
    print(f"\nWrote {len(reasons)} AI reasons -> output/reasons.json")


if __name__ == "__main__":
    main()
