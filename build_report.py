"""
build_report.py — the human-approve view (a report, not an app).

Renders output/approve_view.html: the screen a finance approver sees. Only the
few items that need a human, each with the AI's plain-language reason, the cited
evidence, the escalation level, and a signature gate. Nothing here approves
anything — it stages for a human.

Reads output/review_results.json (+ output/reasons.json if reason_writer has run).
"""

import html
import json
from collections import Counter
from pathlib import Path

results = json.load(open("output/review_results.json"))
reasons = json.load(open("output/reasons.json")) if Path("output/reasons.json").exists() else {}

counts = Counter(r["status"] for r in results)
total = len(results)
flagged = [r for r in results if r["status"] != "CLEAN"]

# Risk picture — the executive read before the per-case cards.
risk_total = sum(r["amount_vnd"] for r in flagged)
by_status = {}
for r in flagged:
    s = by_status.setdefault(r["status"], {"n": 0, "vnd": 0})
    s["n"] += 1
    s["vnd"] += r["amount_vnd"]
RISK_MEANING = {
    "DUPLICATE":   ("#b3141c", "would have been paid twice"),
    "BANK_CHANGE": ("#b06a00", "headed to an unverified bank account"),
    "UNKNOWN":     ("#52525b", "payee cannot be verified against master data"),
}

BADGE = {
    "DUPLICATE":   ("#b3141c", "Duplicate payment"),
    "BANK_CHANGE": ("#b06a00", "Bank account changed"),
    "UNKNOWN":     ("#52525b", "Unknown — needs human"),
}


def esc(s):
    return html.escape(str(s))


# Per-card handoff packets — the EXACT record that rendered the card, verbatim.
# Signing downloads it as a two-plane .md (prose for the next human, fenced JSON
# for the next system). Deterministic: no model call, nothing added or dropped.
packets = {}
for r in flagged:
    e = reasons.get(r["line_id"])
    if isinstance(e, str):
        e = {"reason": e, "recommendation": None, "escalation_note": None}
    packets[r["line_id"]] = {**r, "ai": e}

cards = []
for r in flagged:
    color, label = BADGE.get(r["status"], ("#52525b", r["status"]))
    entry = reasons.get(r["line_id"])
    if isinstance(entry, str):          # old format tolerated
        entry = {"reason": entry, "recommendation": None, "escalation_note": None}
    if entry:
        rec = entry.get("recommendation")
        note = entry.get("escalation_note")
        reason_html = f'<div class="reason">{esc(entry["reason"])}</div>'
        if rec:
            reason_html += f'<div class="rec">AI recommendation <span>(advisory — you sign)</span>: <b>{esc(rec)}</b></div>'
        if note:
            reason_html += (f'<div class="note-block"><span class="note-head">Draft escalation note '
                            f'(ready to send to {esc(r["escalation_required"])})</span>{esc(note)}</div>')
    else:
        reason_html = ('<div class="reason pending">AI reason pending — run <code>reason_writer.py</code> '
                       'with an API key to generate the plain-language explanation.</div>')
    lid = r["line_id"]
    cards.append(f"""
    <div class="card" id="card-{esc(lid)}" style="border-left:6px solid {color}">
      <div class="row1">
        <span class="badge" style="background:{color}">{esc(label)}</span>
        <span class="amount">{r['amount_vnd']:,} <span class="vnd">VND</span></span>
      </div>
      <div class="vendor">{esc(r['vendor'])}</div>
      <div class="meta">{esc(r['store_id'])} · invoice {esc(r['invoice_number'])} · line {esc(lid)}</div>
      <div class="reason-label">Reviewer's read</div>
      {reason_html}
      <div class="cited">Cited from: <b>{esc(r['cited_from']['rule'])}</b> — {esc(r['cited_from']['evidence'])}</div>
      <div class="foot">
        <span class="esc">Escalation required: <b>{esc(r['escalation_required'])}</b></span>
        <span class="gate">
          <button class="approve" onclick="signCard('{esc(lid)}')">&#9997; Sign &amp; approve</button>
          <button class="reject" onclick="rejStart('{esc(lid)}')">Reject</button>
        </span>
      </div>
      <div class="rej-why" id="why-{esc(lid)}" style="display:none">
        <span class="why-head">Why reject? — the reason travels back with the return handoff</span>
        <span class="why-btns"></span>
      </div>
    </div>""")

# Sign/Reject behavior — plain string (not f-string) so JS braces stay untouched.
# The .md is assembled from PACKETS verbatim: nothing added, nothing dropped,
# nothing invented. Two planes in one file: prose for the next human, fenced
# JSON for the next system.
JS_BLOCK = """
<script>
const PACKETS = __PACKETS__;
const REJECT_WHY = {
  "DUPLICATE":   "Confirmed duplicate — invoice already settled in the ledger",
  "BANK_CHANGE": "Payee bank account does not match vendor master — unverified change",
  "UNKNOWN":     "Vendor cannot be verified against master data"
};
function dl(name, text){
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], {type:'text/markdown'}));
  a.download = name; a.click(); URL.revokeObjectURL(a.href);
}
function mdFor(p, decision, why){
  const ts = new Date().toISOString();
  const ai = p.ai || {};
  let m = '# handoff — ' + decision + ' · ' + p.vendor + ' · ' + p.amount_vnd.toLocaleString() + ' VND\\n';
  m += '> From: KFC-P1 AI Finance Reviewer · human decision at ' + ts + '\\n';
  m += '> Complete decision state, generated verbatim from the review record.\\n';
  m += '> Nothing added, nothing summarized away, nothing invented.\\n\\n';
  m += '## Decision\\n';
  m += decision === 'SIGNED'
     ? 'SIGNED for payment by the ' + p.escalation_required + ' level.\\n\\n'
     : 'REJECTED — reason: ' + why + '\\nReturn to requester: ' + p.store_id + '-manager\\n\\n';
  m += '## Why it was flagged\\n' + (ai.reason || p.cited_from.evidence) + '\\n\\n';
  m += 'Cited from: ' + p.cited_from.rule + ' — ' + p.cited_from.evidence + '\\n\\n';
  if (ai.recommendation) m += '## AI case (as read by the signer)\\n- Recommendation: ' + ai.recommendation + '\\n- Escalation note: ' + (ai.escalation_note || '-') + '\\n\\n';
  m += '## Payment record (machine-readable, verbatim)\\n```json\\n' + JSON.stringify(p, null, 2) + '\\n```\\n\\n';
  m += '## Execute next\\n';
  m += decision === 'SIGNED'
     ? '- Accounting: map to a journal entry in the ledger system — every required field is in the JSON above. No GL codes are assumed here; mapping stays in your chart of accounts.\\n'
     : '- Requester: correct or withdraw the submission; the reason above travels with it.\\n';
  m += '- Audit ref: ' + p.cited_from.rule + ' · output/audit_log.txt\\n\\n';
  m += '---\\n';
  m += '*This file carries the intent and the task together — that is why nothing is lost between hands, human or machine. Swap in real data and it becomes KFC\\'s own context; the format is disposable, the discipline is not.*\\n';
  m += '*— Peak · built solo at Agentic AI Build Week 2026*\\n';
  return m;
}
function collapse(id, cls, text){
  const c = document.getElementById('card-' + id);
  c.innerHTML = '<div class="done-strip ' + cls + '">' + text + '</div>';
}
function signCard(id){
  const p = PACKETS[id];
  dl('handoff-' + id + '.md', mdFor(p, 'SIGNED', null));
  collapse(id, 'ok', '&#10003; Signed — <b>handoff-' + id + '.md</b> downloaded · queued for accounting handoff (production: Digital Signature + journal mapping plug in here)');
}
function rejStart(id){
  const p = PACKETS[id];
  const box = document.getElementById('why-' + id);
  const btns = box.querySelector('.why-btns');
  btns.innerHTML = '';
  [REJECT_WHY[p.status] || 'Flagged by review', 'Other…'].forEach(function(w){
    const b = document.createElement('button');
    b.className = 'whyb'; b.textContent = w;
    b.onclick = function(){
      let why = w;
      if (w === 'Other…'){ why = prompt('Reason for rejection:') || ''; if (!why) return; }
      dl('return-' + id + '.md', mdFor(p, 'REJECTED', why));
      collapse(id, 'no', '&#10007; Rejected — reason: ' + why + ' · <b>return-' + id + '.md</b> downloaded, returned to requester');
    };
    btns.appendChild(b);
  });
  box.style.display = 'flex';
}
</script>
""".replace("__PACKETS__", json.dumps(packets, ensure_ascii=False))

DOC = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KFC-P1 · Finance Reviewer — Human Approval View</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#f4f4f5;color:#18181b;margin:0;padding:0 0 60px}}
 .wrap{{max-width:860px;margin:0 auto;padding:0 20px}}
 header{{background:#111;color:#fff;padding:22px 0}}
 header .wrap{{display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px}}
 h1{{font-size:19px;margin:0;font-weight:700}}
 .model{{background:#b3141c;color:#fff;font-size:11px;font-weight:700;letter-spacing:1px;padding:3px 8px;border-radius:4px}}
 .bar{{background:#fff;border-bottom:1px solid #e4e4e7;padding:16px 0}}
 .bar .wrap{{display:flex;gap:26px;flex-wrap:wrap;align-items:center}}
 .stat b{{font-size:22px}} .stat span{{color:#71717a;font-size:13px}}
 .clean b{{color:#15803d}} .flag b{{color:#b3141c}}
 .note{{color:#71717a;font-size:13px;margin-left:auto}}
 .risk{{background:#111;color:#fff;border-radius:14px;padding:22px 26px;margin:18px 0 22px}}
 .risk-head{{display:flex;justify-content:space-between;align-items:flex-start;gap:18px;flex-wrap:wrap}}
 .risk-kicker{{text-transform:uppercase;letter-spacing:2px;font-size:11.5px;color:#f87171;font-weight:800;margin-bottom:6px}}
 .risk-total{{font-size:34px;font-weight:800;letter-spacing:-.5px}}
 .risk-total span{{font-size:14px;font-weight:600;color:#a1a1aa;letter-spacing:0}}
 .risk-note{{color:#a1a1aa;font-size:13px;line-height:1.6;text-align:right}}
 .risk-rows{{border-top:1px solid #27272a;margin-top:16px;padding-top:6px}}
 .risk-row{{display:flex;align-items:baseline;gap:12px;padding:9px 0;font-size:14.5px;flex-wrap:wrap}}
 .risk-row b{{min-width:250px}}
 .dot{{width:10px;height:10px;border-radius:50%;flex:none;align-self:center}}
 .rvnd{{font-family:ui-monospace,monospace;font-weight:700;min-width:150px}}
 .rwhy{{color:#a1a1aa;font-size:13px}}
 .card{{background:#fff;border:1px solid #e4e4e7;border-radius:12px;padding:18px 20px;margin:16px 0;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
 .row1{{display:flex;justify-content:space-between;align-items:center;gap:10px}}
 .badge{{color:#fff;font-size:12px;font-weight:700;padding:4px 10px;border-radius:999px}}
 .amount{{font-size:24px;font-weight:800}} .vnd{{font-size:12px;color:#71717a;font-weight:600}}
 .vendor{{font-size:17px;font-weight:700;margin-top:10px}}
 .meta{{color:#71717a;font-size:13px;margin-top:2px;font-family:ui-monospace,monospace}}
 .reason-label{{text-transform:uppercase;letter-spacing:1px;font-size:11px;color:#b3141c;font-weight:700;margin-top:16px}}
 .reason{{font-size:16px;line-height:1.55;margin-top:6px;background:#fafafa;border:1px solid #eee;border-radius:8px;padding:12px 14px}}
 .reason.pending{{color:#a1a1aa;font-style:italic}}
 .rec{{margin-top:10px;font-size:14px}} .rec span{{color:#71717a;font-size:12px}} .rec b{{color:#b3141c}}
 .note-block{{margin-top:10px;background:#fffbeb;border:1px solid #fde68a;border-radius:8px;padding:10px 12px;font-size:13.5px;line-height:1.5}}
 .note-head{{display:block;text-transform:uppercase;letter-spacing:1px;font-size:10.5px;color:#92400e;font-weight:700;margin-bottom:5px}}
 .cited{{font-size:12.5px;color:#52525b;margin-top:10px;font-family:ui-monospace,monospace;background:#f4f4f5;padding:8px 10px;border-radius:6px}}
 .foot{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-top:16px;border-top:1px solid #f0f0f0;padding-top:14px}}
 .esc{{font-size:13px}}
 button{{font-size:13px;font-weight:600;border-radius:8px;padding:9px 16px;border:1px solid #d4d4d8;cursor:pointer}}
 .approve{{background:#15803d;color:#fff;border-color:#15803d}}
 .reject{{background:#fff;color:#b3141c;border-color:#e4c0c0;margin-left:8px}}
 .done-strip{{font-size:14.5px;padding:6px 2px;line-height:1.6}}
 .done-strip.ok{{color:#15803d}} .done-strip.no{{color:#b3141c}}
 .rej-why{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-top:12px;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;padding:10px 12px}}
 .why-head{{font-size:12px;color:#991b1b;font-weight:700}}
 .whyb{{background:#fff;color:#b3141c;border:1px solid #e4c0c0;margin-right:8px}}
 footer{{text-align:center;color:#a1a1aa;font-size:12px;margin-top:30px;line-height:1.7}}
</style></head><body>
<header><div class="wrap"><h1>KFC-P1 · AI Finance Reviewer — Human Approval View</h1><span class="model">MODEL DATA</span></div></header>
<div class="bar"><div class="wrap">
  <div class="stat"><b>{total}</b> <span>line-items reviewed</span></div>
  <div class="stat clean"><b>{counts['CLEAN']}</b> <span>clean, auto-cleared</span></div>
  <div class="stat flag"><b>{len(flagged)}</b> <span>need a human</span></div>
  <div class="note">Nothing is auto-approved. Each item below waits for a signature.</div>
</div></div>
<div class="wrap">
 <div class="risk">
  <div class="risk-head">
   <div>
    <div class="risk-kicker">⚠ The risk picture — this run</div>
    <div class="risk-total">{risk_total:,} <span>VND held back from payment</span></div>
   </div>
   <div class="risk-note">None of it moves until a human signs.<br>The cards below are the case for each hold.</div>
  </div>
  <div class="risk-rows">
   {''.join(
      f'<div class="risk-row"><span class="dot" style="background:{RISK_MEANING[s][0]}"></span>'
      f'<b>{v["n"]}× {BADGE[s][1]}</b><span class="rvnd">{v["vnd"]:,} VND</span>'
      f'<span class="rwhy">{RISK_MEANING[s][1]}</span></div>'
      for s, v in sorted(by_status.items(), key=lambda kv: -kv[1]["vnd"]))}
  </div>
 </div>
{''.join(cards)}
</div>
<footer>
  KFC-P1 Agentic Finance Reviewer · deterministic where money moves, AI where the reason is written<br>
  MODEL data — format real, vendors &amp; amounts modelled, not real KFC transactions.
  Human-gate active: staged for signature, never auto-approved.
</footer>
{JS_BLOCK}
</body></html>"""

Path("output/approve_view.html").write_text(DOC, encoding="utf-8")
print(f"Wrote output/approve_view.html — {len(flagged)} items staged for human "
      f"approval, {counts['CLEAN']} auto-cleared.")
