"""Write report/: REPORT.md, results.json, REPORT.pdf, discrepancies.md, swml/, snippets/."""
from __future__ import annotations

import json
import re
import shutil
import subprocess

from .config import REPORT, ROOT

BANNED = re.compile(r"\b(just|simply|easy|easily|straightforward)\b", re.I)


def lint(text: str) -> list[str]:
    issues = []
    for i, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "    ", "|---")) or line.strip().startswith(">"):
            continue
        if "—" in line or re.search(r"(?<![-|`])--(?![-|`])", line):
            issues.append(f"line {i}: dash")
        if BANNED.search(line) and "`" not in line:
            issues.append(f"line {i}: banned word {BANNED.search(line).group(0)}")
    return issues


def one_line(r):
    from .doc_answers import SHORT
    if r.get("answer") and r["id"] in SHORT:
        return SHORT[r["id"]]
    a = r.get("answer") or ""
    if not a and r.get("runs"):
        a = f"{r['status'].title()} by live test: {r.get('hypothesis')}. See runs."
    return a.split(". ")[0].rstrip(".") + "."


def write_all(results: dict, meta: dict):
    REPORT.mkdir(exist_ok=True)
    (REPORT / "results.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2, default=str))
    md = build_md(results, meta)
    issues = lint(md)
    (REPORT / "REPORT.md").write_text(md)
    (REPORT / "discrepancies.md").write_text(DISCREPANCIES)
    write_swml_and_snippets()
    render_pdf()
    if issues:
        (REPORT / "lint.txt").write_text("\n".join(issues))
    print(summary_table(results))


def summary_table(results):
    rows = ["| ID | Question | Status | One-line answer |", "|---|---|---|---|"]
    for tid, r in results.items():
        rows.append(f"| {tid} | {r['question']} | {r['status']} | {one_line(r).replace('|', '/')} |")
    return "\n".join(rows)


def build_md(results, meta):
    pf = meta.get("preflight", [])
    st = meta.get("selftests", {})
    counts = {}
    for r in results.values():
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    out = [
        "# SalesGodCRM browser calling verification",
        "",
        f"Run started {meta.get('started')}, finished {meta.get('finished')}. Harness code: `harness/`. Evidence: `evidence/`.",
        "",
        "## Run outcome",
        "",
        ("**No live calls were placed in this run.** The preflight checks failed, so every behavioral test fell back to documentary evidence or was marked BLOCKED. No status in this report was upgraded without evidence; nothing below is CONFIRMED or REFUTED, because those statuses require observed behavior."
         if not all(c["ok"] for c in pf) or meta.get("live_error") else
         "Live tests ran against the test Space. Statuses CONFIRMED, REFUTED and INCONSISTENT come from the runs shown in each section; any test that could not run falls back to its documentary status with the reason recorded."),
        "",
        "| Preflight check | Result | Detail |",
        "|---|---|---|",
    ]
    out += [f"| {c['check']} | {'pass' if c['ok'] else 'FAIL'} | {c['detail']} |" for c in pf]
    out += [
        "",
        "To run live: place `.env` (SW_SPACE, SW_PROJECT_ID, SW_API_TOKEN, optional SW_SIGNING_KEY for B11) in `verification/`, allow outbound HTTPS to the Space host and `signalwire.com`, and allow a public tunnel (cloudflared quick tunnel needs `api.trycloudflare.com` plus outbound connections to Cloudflare's edge on port 7844; or provide `NGROK_AUTHTOKEN`). Then run `python -m harness.run`. The same code path produces this report with live statuses.",
        "",
        "Status counts: " + ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())),
        "",
        "### Local self-tests (no Space required)",
        "",
        "These prove the harness's own components, not SignalWire behavior.",
        "",
        "| Self-test | Result | Output |",
        "|---|---|---|",
    ]
    for k, v in st.items():
        out.append(f"| {k} | {'pass' if v['ok'] else 'FAIL'} | `{v['stdout'][:300].replace('|', '/')}` |")
    out += ["", "## Executive summary", "", summary_table(results), ""]
    out += ["## Method notes", "",
            "- PSTN simulation: A to B calls are SignalWire-to-SignalWire between numbers owned by the test Space and may not traverse an external carrier. Every dial asserts the destination is owned by the Space and not on the emergency or N11 denylist (`harness/config.py`).",
            "- Documentation sources: the public `signalwire.com/docs` site was blocked by the network policy (HTTP 403), so docs were read through the SignalWire knowledge server, which indexes the same public pages and returns their URLs. Each relied-on page is saved under `evidence/docs/` with source and fetch time. Some SWML details come from the knowledge server's SWML reference rather than a public page; those are labeled in `evidence/docs/swml/`.",
            "- SDK facts come from the published npm package `@signalwire/js@4.0.0-rc.4` type declarations and implementation, read without executing it, with line citations in `evidence/sdk/sdk_facts.md`. The browser self-test then loaded that bundle in headless Chromium to confirm the exported identifiers.",
            "- Every behavioral test is coded to run 3 times (`harness/tests.py`, `RUNS = 3`). A result is definitive only when all runs agree.",
            ""]
    for part, title in (("A", "Part A: questions the customer asked"), ("B", "Part B: questions they are likely to ask"),
                        ("C", "Part C: not determinable by testing")):
        out += [f"## {title}", ""]
        for tid, r in results.items():
            if r["part"] != part:
                continue
            out += [f"### {tid}. {r['question']}", "", f"**Status:** {r['status']}", ""]
            if r.get("confirm_with"):
                out += [f"**Confirm with:** {r['confirm_with']}", ""]
            if r.get("hypothesis"):
                out += [f"**Method:** live test `{tid}` in `harness/tests.py`, hypothesis: {r['hypothesis']}. 3 runs.", ""]
            if r.get("blocked_reason"):
                out += ["**Runs:** none executed. Live test blocked (see Run outcome).", ""]
            elif r.get("runs"):
                out += ["**Runs:**", "", "```json", json.dumps(r["runs"], indent=1, default=str)[:4000], "```", ""]
            out += ["**Evidence:** " + ", ".join(f"`{e}`" for e in r.get("evidence", [])), ""]
            out += ["**Customer-facing answer:** " + (r.get("answer") or "See runs."), ""]
    return "\n".join(out)


DISCREPANCIES = """# Discrepancies

No live behavior was observed in this run, so this file lists only differences between sources (documentation versus documentation, documentation versus the published SDK, and customer assumptions versus documentation). Live observations will add rows when the harness runs against a Space.

| # | Topic | Side 1 | Side 2 |
|---|---|---|---|
| 1 | Parallel destination cap | Customer reports a 20-destination limit for `connect.parallel` | No limit appears in the SWML connect page or the SWML JSON schema (no `maxItems`). `evidence/docs/swml_facts.json` item 1 |
| 2 | `connect.status_url` | Public connect page documents `status_url` (event `calling.call.connect`). `evidence/docs/swml/public_swml_connect.md` | The SWML JSON schema connect definitions list `call_state_url` but not `status_url`. `evidence/docs/swml/mcp_swml_schema_connect_record.md` |
| 3 | Signature header casing | SWML webhook security guide: `X-Signalwire-Signature`, `X-Signalwire-SHA256-Signature`. `evidence/docs/swml/public_swml_webhook_security.md` | SDK docs: `X-SignalWire-Signature`, `X-SignalWire-Sha256-Signature`. `evidence/docs/swml/sdk_webhook_signature_validation.md`. HTTP headers are case-insensitive; the validator reads them that way |
| 4 | `record` direction values | Public record_call page: `speak`, `listen`, `both` | SWML cheatsheet and reference: `speak`, `hear`, `both`. `evidence/docs/swml_facts.json` item 2 gaps |
| 5 | Guest token authentication | One doc: `POST /api/fabric/guests/tokens` with a SAT | Another doc: with the project API token. `evidence/docs/rest_facts.json` 2_fabric_subscribers |
| 6 | `vars.userVariables` in SWML fetch | Customer expectation and SWAIG examples show `vars.userVariables` | SWML document-fetch payload docs do not list `vars` on the initial fetch and do not mention `userVariables`. `evidence/docs/swml_facts.json` item 5 |
| 7 | REST recording callback location | SDK-level docs put `status_url` in `calling.record` params | The Calling REST API reference retrieved shows no verbatim curl for `calling.record`. `evidence/docs/rest_facts.json` 1_calling_rest_api gaps |
| 8 | Retry behavior | cXML documents status callback retries (3 attempts) and 2 s / 5 s timeouts | SWML documents only an approximate 5 s wait and a fallback URL; no retry counts. `evidence/docs/swml/public_swml_webhook_reliability.md` |
"""


INBOUND_SWML = {
    "version": "1.0.0",
    "sections": {"main": [
        {"connect": {"parallel": [{"to": "/private/<subscriber-1>"}, {"to": "/private/<subscriber-2>"}],
                     "timeout": 20, "status_url": "https://<backend>/hook/connect",
                     "call_state_url": "https://<backend>/hook/callstate",
                     "call_state_events": ["created", "ringing", "answered", "ended"],
                     "result": {"case": {"connected": [{"hangup": {}}]}, "default": [{"execute": {"dest": "voicemail"}}]}}}],
        "voicemail": [{"play": {"url": "say:Please leave a message after the tone."}},
                      {"record": {"format": "mp3", "beep": True, "end_silence_timeout": 3, "max_length": 120}},
                      {"request": {"url": "https://<backend>/hook/voicemail", "method": "POST", "body": {"recording": "%{record_url}"}}},
                      {"hangup": {}}]}}

OUTBOUND_SWML_NOTE = ("Outbound authorization SWML is generated per request by the backend: it reads the destination from "
                      "userVariables, refuses any number not on the allow list, and returns a connect to that number. "
                      "See snippets/outbound_authorization.py.")

SNIPPETS = {
    "mint_token.py": '''"""Mint a Subscriber Access Token. Endpoint and fields: evidence/docs/rest/fabric_subscribers_and_tokens.md.
Proof status: request shape from docs; not yet exercised against a live Space."""
import time, httpx

def mint_sat(space, project_id, api_token, subscriber_email, ttl_s=3600, fingerprint=None, refreshable=False):
    body = {"reference": subscriber_email, "expire_at": int(time.time()) + ttl_s}
    if fingerprint:
        body["fingerprint"] = fingerprint
    if refreshable:
        body["scope"] = ["sat:refresh"]
    r = httpx.post(f"https://{space}/api/fabric/subscribers/tokens", json=body, auth=(project_id, api_token))
    r.raise_for_status()
    j = r.json()
    j["expiry_at"] = body["expire_at"] * 1000  # Browser SDK v4 expects milliseconds
    return j
''',
    "refresh_provider.js": '''// Browser SDK v4 credential provider with backend-driven refresh.
// API surface verified against @signalwire/js@4.0.0-rc.4 types (evidence/sdk/sdk_facts.md, Item 1) and loaded
// in headless Chromium by the browser self-test. Live refresh behavior: not yet observed.
import { SignalWire, TokenRefreshError } from "@signalwire/js";

async function fetchSat() {
  const r = await fetch("/token");            // your backend calls mint_sat()
  const { token, expiry_at } = await r.json(); // expiry_at in ms since epoch
  return { token, expiry_at };
}

const first = await fetchSat();
const client = new SignalWire({
  authenticate: async () => first,
  refresh: async () => fetchSat(),             // called 5 s before expiry_at, up to 5 retries
});
client.errors$.subscribe((e) => {
  if (e instanceof TokenRefreshError) {
    // SDK has disconnected; prompt re-login or rebuild the client
  }
});
''',
    "dial_with_user_variables.js": '''// Browser SDK v4 dial with userVariables. Shape verified from the published types (sdk_facts.md Item 3).
// Live delivery location of userVariables in the webhook: not yet observed (see A5).
const call = await client.dial("/private/salesgod-outbound", {
  audio: true,
  video: false,
  userVariables: { to: "+15615550123", crm_call_id: "c-123" },
});
call.status$.subscribe((s) => console.log("status", s));
''',
    "record_control.py": '''"""Calling API recording control and hangup. Commands: evidence/docs/rest/calling_api_call_commands.md.
Proof status: names and params from docs; not yet exercised live (see A7, A10)."""
import httpx

def cmd(space, pid, tok, command, call_id, **params):
    body = {"command": command, "id": call_id, "params": params}
    r = httpx.post(f"https://{space}/api/calling/calls", json=body, auth=(pid, tok))
    return r.status_code, r.json()

# start a stereo MP3 recording with a completion webhook
# cmd(space, pid, tok, "calling.record", anchor_call_id, control_id="rec-1",
#     audio={"format": "mp3", "stereo": True, "direction": "both"}, status_url="https://backend/hook/record")
# cmd(space, pid, tok, "calling.record.pause", anchor_call_id, control_id="rec-1", behavior="silence")  # or "skip"
# cmd(space, pid, tok, "calling.record.resume", anchor_call_id, control_id="rec-1")
# cmd(space, pid, tok, "calling.record.stop", anchor_call_id, control_id="rec-1")
# cmd(space, pid, tok, "calling.end", anchor_call_id, reason="hangup")
''',
    "validate_signature.py": None,  # copied from harness/signature.py (proven by selftest_signature)
    "outbound_authorization.py": '''"""Outbound authorization webhook (FastAPI). Proof status: served by the harness backend in the local self-test;
the field read for userVariables is the documented-candidate `vars.userVariables` and must be confirmed by A5."""
from fastapi import FastAPI, Request

app = FastAPI()
ALLOWED = set()  # numbers this CRM user may dial

@app.post("/swml/outbound")
async def outbound(req: Request):
    body = await req.json()
    uv = (body.get("vars") or {}).get("userVariables") or {}
    caller = body.get("call", {}).get("from")  # platform-asserted identity; never trust uv["crm_user_id"]
    to = uv.get("to")
    if to not in ALLOWED:
        return {"version": "1.0.0", "sections": {"main": [{"hangup": {"reason": "decline"}}]}}
    return {"version": "1.0.0", "sections": {"main": [
        {"record_call": {"stereo": True, "format": "mp3", "status_url": "https://backend/hook/record"}},
        {"connect": {"to": to, "from": "+1561XXXXXXX", "timeout": 30}}]}}
''',
}


def write_swml_and_snippets():
    sd = REPORT / "swml"
    sd.mkdir(exist_ok=True)
    (sd / "inbound_ring_group.json").write_text(json.dumps(INBOUND_SWML, indent=2))
    (sd / "README.md").write_text("# SWML\n\n`inbound_ring_group.json`: parallel ring of Subscriber addresses with a voicemail branch on `connect_result`. "
                                  "Built from documented methods; not yet exercised live.\n\n" + OUTBOUND_SWML_NOTE + "\n")
    nd = REPORT / "snippets"
    nd.mkdir(exist_ok=True)
    for name, body in SNIPPETS.items():
        if body is None:
            shutil.copy(ROOT / "harness" / "signature.py", nd / name)
        else:
            (nd / name).write_text(body)


def render_pdf():
    md = REPORT / "REPORT.md"
    html = REPORT / "REPORT.html"
    css = "<style>body{font-family:Helvetica,Arial,sans-serif;font-size:10pt;max-width:180mm;margin:auto}table{border-collapse:collapse;font-size:8pt}td,th{border:1px solid #999;padding:3px;vertical-align:top}pre{font-size:7pt;white-space:pre-wrap}</style>"
    r = subprocess.run(["pandoc", str(md), "-f", "gfm", "-t", "html", "-s", "--metadata", "title=SalesGodCRM calling verification"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return
    html.write_text(r.stdout.replace("</head>", css + "</head>"))
    js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://{html}');await p.pdf({{path:'{REPORT / "REPORT.pdf"}',format:'A4',margin:{{top:'12mm',bottom:'12mm',left:'10mm',right:'10mm'}}}});await b.close();}})();"""
    subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=120)
    html.unlink(missing_ok=True)
