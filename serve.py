"""
serve.py — the reviewer as the finance user sees it: a window and one click.

A thin local web wrapper over the SAME pipeline scripts (no engine logic here).
Two actions, each with REAL step-by-step progress (the server reports the stage
it is actually executing — not an animation):

  * Run monthly review      -> dataset -> review -> AI reasons -> view
  * Resubmit a paid invoice -> inject -> review -> AI reasons -> view

    python3 serve.py        ->  http://127.0.0.1:8123

Python stdlib only. The terminal path still works and remains the fallback.
"""

import json
import os
import subprocess
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
PORT = 8123

FLOWS = {
    "run": [
        ("Loading this month's batch — 300 requests from 250+ stores", ["python3", "generate_dataset.py"]),
        ("Sweeping every line-item — duplicates vs the paid ledger, accounts vs vendor master", ["python3", "reviewer.py"]),
        ("AI reviewer writing reasons, recommendations, escalation notes", ["python3", "reason_writer.py"]),
        ("Staging the approval view — nothing gets paid without a signature", ["python3", "build_report.py"]),
    ],
    "resubmit": [
        ("Resubmitting an already-paid invoice into the batch — openly", ["python3", "demo_resubmit.py"]),
        ("Re-running the review — watch for the catch", ["python3", "reviewer.py"]),
        ("AI reviewer writing the case for the new flag", ["python3", "reason_writer.py"]),
        ("Staging the approval view", ["python3", "build_report.py"]),
    ],
}

state = {"busy": False, "flow": None, "step": -1, "steps": [], "done": False, "error": ""}
lock = threading.Lock()


def run_flow(flow):
    env = dict(os.environ, KFC_NO_BROWSER="1")
    if flow == "resubmit":
        env["KFC_INJECT_ONLY"] = "1"
    steps = FLOWS[flow]
    state.update(flow=flow, steps=[s[0] for s in steps], step=-1, done=False, error="")
    try:
        for i, (_label, cmd) in enumerate(steps):
            state["step"] = i
            r = subprocess.run(cmd, cwd=HERE, env=env, capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                state["error"] = (r.stderr or r.stdout or "step failed")[-500:]
                return
        state["done"] = True
    except Exception as e:
        state["error"] = str(e)
    finally:
        state["busy"] = False


PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KFC-P1 · Finance Reviewer</title><style>
 body{font-family:-apple-system,'Segoe UI',Roboto,sans-serif;background:#f4f4f5;color:#18181b;margin:0}
 .top{background:#111;color:#fff;padding:18px 32px;display:flex;justify-content:space-between;align-items:center}
 .top b{font-size:18px}.model{background:#b3141c;font-size:11px;font-weight:700;letter-spacing:1px;padding:3px 9px;border-radius:4px}
 .wrap{max-width:760px;margin:48px auto;padding:0 24px}
 h1{font-size:30px;margin:0 0 8px;font-weight:800}
 p.sub{color:#52525b;font-size:16px;line-height:1.6;margin:0 0 30px}
 .card{background:#fff;border:1px solid #e4e4e7;border-radius:14px;padding:24px;margin-bottom:16px;
       display:flex;justify-content:space-between;align-items:center;gap:18px}
 .card b{font-size:17px;display:block;margin-bottom:4px}
 .card small{color:#71717a;font-size:13.5px;line-height:1.5;display:block}
 button{font-size:15px;font-weight:700;border:none;border-radius:10px;padding:14px 22px;cursor:pointer;white-space:nowrap}
 .run{background:#15803d;color:#fff}.catch{background:#b3141c;color:#fff}
 button:disabled{background:#d4d4d8;color:#71717a;cursor:default}
 #phases{display:none;background:#fff;border:1px solid #e4e4e7;border-radius:14px;padding:22px 24px;margin-top:18px}
 .ph{display:flex;gap:12px;align-items:baseline;padding:8px 0;font-size:15px;color:#a1a1aa;transition:color .3s}
 .ph .ic{width:18px;text-align:center;font-weight:700}
 .ph.active{color:#18181b;font-weight:600}
 .ph.done{color:#15803d}
 .ph.active .ic::after{content:"";display:inline-block;width:11px;height:11px;border:2px solid #d4d4d8;
   border-top-color:#b3141c;border-radius:50%;animation:r .8s linear infinite}
 .ph.done .ic::after{content:"✓"}
 .ph.pending .ic::after{content:"·"}
 @keyframes r{to{transform:rotate(360deg)}}
 #err{color:#b3141c;font-size:14px;margin-top:14px;display:none}
 .foot{color:#a1a1aa;font-size:12.5px;margin-top:40px;line-height:1.7;text-align:center}
</style></head><body>
<div class="top"><b>KFC-P1 · Agentic Finance Reviewer</b><span class="model">MODEL DATA</span></div>
<div class="wrap">
 <h1>This month's batch is in.</h1>
 <p class="sub">300 payment requests · 761 line-items from 250+ stores, waiting for review.
 One click — the agent checks every line, writes its reasons, and stages anything doubtful for your signature.</p>

 <div class="card">
  <div><b>Run monthly review</b>
   <small>Sweep the full batch: duplicates vs the paid ledger, bank-account changes vs master data,
   escalation routing. The AI writes a reason, recommendation, and escalation note for every flag.</small></div>
  <button class="run" onclick="go('run')">Run review</button>
 </div>

 <div class="card">
  <div><b>Resubmit an already-paid invoice</b>
   <small>The question every Finance director asks: what if someone submits an invoice we already paid?
   Do it — openly — and watch the agent catch it, cited back to the original payment.</small></div>
  <button class="catch" onclick="go('resubmit')">Resubmit &amp; watch</button>
 </div>

 <div id="phases"></div>
 <div id="err"></div>
 <div class="foot">Deterministic where money moves · AI where the reason is written<br>
 Nothing is paid until a human signs. MODEL data — real format, modelled vendors.</div>
</div>
<script>
let poll=null;
async function go(action){
  document.querySelectorAll('button').forEach(b=>b.disabled=true);
  document.getElementById('err').style.display='none';
  const r=await fetch('/'+action,{method:'POST'});
  if(!r.ok){ fail('Could not start — is another run in progress?'); return; }
  poll=setInterval(tick, 500);
}
async function tick(){
  const s=await (await fetch('/status')).json();
  const box=document.getElementById('phases');
  box.style.display='block';
  box.innerHTML=s.steps.map((t,i)=>{
    const cls = i<s.step||s.done ? 'done' : (i===s.step&&!s.error ? 'active' : 'pending');
    return `<div class="ph ${cls}"><span class="ic"></span><span>${t}</span></div>`;
  }).join('');
  if(s.done){ clearInterval(poll); location.href='/view'; }
  if(s.error){ clearInterval(poll); fail('A step failed — fallback: run python3 run_demo.py in Terminal. '+s.error); }
}
function fail(msg){
  const e=document.getElementById('err'); e.textContent=msg; e.style.display='block';
  document.querySelectorAll('button').forEach(b=>b.disabled=false);
}
</script></body></html>"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE)
        elif self.path == "/status":
            self._send(200, json.dumps(state), "application/json")
        elif self.path == "/view":
            f = HERE / "output" / "approve_view.html"
            if f.exists():
                self._send(200, f.read_text(encoding="utf-8"))
            else:
                self._send(404, "No review yet — run one from the home page.")
        else:
            self._send(404, "not found")

    def do_POST(self):
        flow = {"/run": "run", "/resubmit": "resubmit"}.get(self.path)
        if not flow:
            self._send(404, "not found")
            return
        with lock:
            if state["busy"]:
                self._send(409, "busy")
                return
            state["busy"] = True
        threading.Thread(target=run_flow, args=(flow,), daemon=True).start()
        self._send(202, "started", "text/plain")


if __name__ == "__main__":
    url = f"http://127.0.0.1:{PORT}"
    print(f"KFC-P1 Finance Reviewer · {url}   (Ctrl-C to stop)")
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
