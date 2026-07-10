"""
make_loop_gif.py — the reviewer loop as an animated diagram for the submission page.

Renders each beat as HTML (same visual language as the approval view), screenshots
via headless Chrome, assembles an animated GIF with Pillow. Presentation asset only.

    python3 make_loop_gif.py   ->  submission/reviewer-loop.gif
"""

import subprocess
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1200, 800  # 3:2

BASE_CSS = """
 body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#f4f4f5;
      color:#18181b;margin:0;width:1200px;height:800px;overflow:hidden}
 .top{background:#111;color:#fff;padding:18px 40px;display:flex;
      justify-content:space-between;align-items:center}
 .top b{font-size:20px} .model{background:#b3141c;font-size:11px;font-weight:700;
      letter-spacing:1px;padding:3px 9px;border-radius:4px}
 .stage{padding:34px 48px}
 .kicker{text-transform:uppercase;letter-spacing:2.5px;font-size:13px;
      color:#b3141c;font-weight:800;margin-bottom:10px}
 h1{font-size:40px;margin:0 0 12px;font-weight:800;letter-spacing:-.5px}
 p.sub{font-size:20px;color:#52525b;margin:0 0 26px;max-width:850px;line-height:1.5}
 .row{display:flex;gap:18px}
 .chip{background:#fff;border:1px solid #e4e4e7;border-radius:12px;padding:18px 22px;
      font-size:17px;font-weight:600;box-shadow:0 1px 2px rgba(0,0,0,.05)}
 .chip small{display:block;color:#71717a;font-weight:400;font-size:13px;margin-top:4px}
 .big{font-size:64px;font-weight:800}
 .green{color:#15803d}.red{color:#b3141c}.amber{color:#b06a00}.grey{color:#52525b}
 .mono{font-family:ui-monospace,Menlo,monospace}
 .foot{position:absolute;bottom:0;left:0;right:0;background:#fff;
      border-top:1px solid #e4e4e7;padding:14px 48px;font-size:14px;color:#71717a}
"""


def frame(body, kicker, title, sub=""):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{BASE_CSS}</style>
</head><body>
<div class="top"><b>KFC-P1 · Agentic Finance Reviewer</b><span class="model">MODEL DATA</span></div>
<div class="stage">
  <div class="kicker">{kicker}</div>
  <h1>{title}</h1>
  <p class="sub">{sub}</p>
  {body}
</div>
<div class="foot">Deterministic where money moves · AI where the reason is written · a human signs everything</div>
</body></html>"""


FRAMES = [
    # 0 — the gag: their current "dashboard", quoted from KFC's own brief
    frame(
        """<div class="row">
             <div class="chip"><span class="big">📄×5</span><small>printed dossiers, signed in sequence</small></div>
             <div class="chip"><span class="big">Excel</span><small>re-keyed invoice data</small></div>
             <div class="chip"><span class="big">✉</span><small>approvals chased by email</small></div>
           </div>""",
        "Your current dashboard", "Five signatures. Two days. Every month.",
        "Excel + email + a 5-level paper chain across 250+ stores — KFC's own brief, verbatim: no dedicated workflow tool."),
    # 1 — the pile
    frame(
        """<div class="row">
             <div class="chip"><span class="big">300</span><small>payment requests</small></div>
             <div class="chip"><span class="big">761</span><small>line-items — rent, power, water, services</small></div>
             <div class="chip"><span class="big">250+</span><small>stores, organized by StoreID</small></div>
           </div>""",
        "This month's batch lands", "The pile is here.",
        "Recurring payment requests from every store — the work that used to enter a 5-level paper chain."),
    # 2 — one click
    frame(
        """<div class="row">
             <div class="chip">R-001 <small>duplicate — vs paid ledger + this batch</small></div>
             <div class="chip">R-002 <small>bank-account change — vs vendor master</small></div>
             <div class="chip">R-003 <small>threshold — routes to the right approver</small></div>
           </div>""",
        "One click", "The reviewer sweeps every line.",
        "Three editable rule templates. Deterministic — same input, same answer, auditable line by line."),
    # 3 — clean flow
    frame(
        """<div class="row">
             <div class="chip"><span class="big green">757</span><small>clean — cleared with citation</small></div>
             <div class="chip"><span class="big red">4</span><small>stopped for a human</small></div>
           </div>""",
        "Seconds later", "757 clear. 4 wait for you.",
        "The reviewer is selective — finance reads four cards, not seven hundred."),
    # 4 — the catches
    frame(
        """<div class="row" style="flex-wrap:wrap">
             <div class="chip"><span class="red">■ DUPLICATE</span><small class="mono">already PAID — cited: PAID-00418</small></div>
             <div class="chip"><span class="amber">■ BANK CHANGE</span><small class="mono">payee 999888… ≠ master 416614…</small></div>
             <div class="chip"><span class="grey">■ UNKNOWN ×2</span><small>no anchor — the agent refuses to guess</small></div>
           </div>""",
        "The catch", "Caught before the money moves.",
        "Every flag cites its exact source. No anchor to compare against? The answer is “unknown — needs a human,” never a guess."),
    # 5 — AI writes
    frame(
        """<div class="chip" style="max-width:900px">
             “This invoice appears to be a duplicate — the ledger already records it as settled
             under <span class="mono">PAID-00418</span>.”
             <small style="font-size:15px;margin-top:10px">AI recommendation: <b class="red">REJECT</b>
             · draft escalation note ready to send to CA</small>
           </div>""",
        "The AI reviewer", "Reason. Recommendation. Escalation note.",
        "For each catch, the AI writes what the approver needs — grounded in the cited evidence, never invented."),
    # 6 — human gate
    frame(
        """<div class="row">
             <div class="chip"><span class="big">✍</span><small>sign &amp; approve — or reject</small></div>
             <div class="chip"><span class="big green">0</span><small>payments released by the agent</small></div>
           </div>""",
        "The human gate", "Nothing is paid until a person signs.",
        "The agent prepares, flags, and stages. Approval belongs to a human — always."),
]


def main():
    shots = []
    with tempfile.TemporaryDirectory() as td:
        for i, html in enumerate(FRAMES):
            src = Path(td) / f"f{i}.html"
            png = Path(td) / f"f{i}.png"
            src.write_text(html, encoding="utf-8")
            subprocess.run([CHROME, "--headless", "--disable-gpu",
                            f"--screenshot={png}", f"--window-size={W},{H}",
                            "--hide-scrollbars", src.as_uri()],
                           check=True, capture_output=True)
            shots.append(Image.open(png).convert("P", palette=Image.ADAPTIVE))
    out = HERE / "submission" / "reviewer-loop.gif"
    shots[0].save(out, save_all=True, append_images=shots[1:],
                  duration=[2600, 2200, 2000, 1800, 2600, 2600, 2600], loop=0, optimize=True)
    print(f"wrote {out} ({out.stat().st_size/1024:.0f} KB, {len(shots)} frames)")


if __name__ == "__main__":
    main()
