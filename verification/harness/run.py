"""Unattended runner. python -m harness.run

Order: preflight -> local self-tests -> (if live possible) harness self-test, Part A, Part B -> aggregation,
cost pull -> cleanup -> report. A failed test never stops the run.
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import time
import traceback

import httpx

from . import tests as T
from .backend import STATE, serve
from .config import EVIDENCE, Budget, load_env, missing_inputs
from .doc_answers import DOC, QUESTIONS


def now_iso():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def preflight(env) -> tuple[bool, list[dict]]:
    checks = []
    miss = missing_inputs(env)
    checks.append({"check": ".env inputs SW_SPACE, SW_PROJECT_ID, SW_API_TOKEN", "ok": not miss,
                   "detail": f"missing: {miss}" if miss else "present"})
    host = env.get("SW_SPACE") or "signalwire.com"
    for url in [f"https://{host}/api/relay/rest/phone_numbers", "https://signalwire.com/docs/llms.txt", "https://api.trycloudflare.com"]:
        try:
            r = httpx.get(url, timeout=10, auth=(env.get("SW_PROJECT_ID", "x"), env.get("SW_API_TOKEN", "x")))
            checks.append({"check": f"reach {url}", "ok": r.status_code < 500, "detail": f"HTTP {r.status_code}"})
        except Exception as e:
            checks.append({"check": f"reach {url}", "ok": False, "detail": repr(e)[:300]})
    return all(c["ok"] for c in checks), checks


def selftests() -> dict:
    out = {}
    for mod in ("selftest_audio", "selftest_signature", "selftest_browser", "selftest_mock"):
        r = subprocess.run([sys.executable, "-m", f"harness.{mod}"], capture_output=True, text=True, timeout=300)
        out[mod] = {"ok": r.returncode == 0, "stdout": r.stdout.strip()[-2000:], "stderr": r.stderr.strip()[-1500:]}
    return out


def merge(live: dict, blocked_reason: str | None) -> dict:
    results = {}
    for tid, q in QUESTIONS.items():
        d = DOC[tid]
        r = live.get(tid)
        base = {"id": tid, "part": tid[0], "question": q, "doc_answer": d["answer"], "doc_citations": d["cites"]}
        if tid.startswith("C"):
            base.update(status=d["status"], answer=d["answer"], confirm_with=d.get("confirm"), evidence=d["cites"])
        elif r and r["status"] != "BLOCKED":
            base.update(status=r["status"], answer=None, runs=r["runs"], evidence=r.get("evidence", []), hypothesis=r.get("hypothesis"))
        else:
            reason = blocked_reason or "; ".join(x.get("error", "") for x in (r or {}).get("runs", []))[:600]
            base.update(status=d["status"], answer=d["answer"], blocked_reason=reason,
                        runs=(r or {}).get("runs", []), evidence=d["cites"], hypothesis=T.HYPOTHESIS.get(tid))
        results[tid] = base
    return results


def live_run(env, budget) -> dict:
    from .devices import Devices
    from .sw import SW
    from .tunnel import start as tunnel_start
    from .audio import make_fixtures

    live = {}
    fx = make_fixtures(EVIDENCE / "fixtures")
    serve(8000)
    url, attempts = tunnel_start(8000)
    (EVIDENCE / "tunnel_attempts.json").write_text(json.dumps(attempts, indent=2))
    if not url:
        raise RuntimeError(f"no public tunnel: {attempts}")
    ref = {"id": "setup"}
    sw = SW(env, budget, ref)
    nums = sw.ensure_numbers(env["NUMBER_AREA_CODE"], 3)
    if len(nums) < 3:
        raise RuntimeError(f"could not obtain 3 numbers, have {len(nums)}")
    sw.route_number(nums[1]["id"], f"{url}/swml/inbound")
    sw.route_number(nums[2]["id"], f"{url}/swml/lead")
    STATE.token_minter = lambda r, ttl: sw.mint_token(r, ttl)
    devs = Devices(url, str(fx["browser"]))
    ctx = T.Ctx(sw, devs, url, nums, budget)
    start_iso = now_iso()
    try:
        # self-test gate: one inbound, one outbound, one recording
        STATE.test_id = "selftest_live"
        st = {"inbound": T.a1(ctx, 0), "recording_outbound": T.a7(ctx, 0)}
        (EVIDENCE / "selftest_live.json").write_text(json.dumps(st, indent=2, default=str))
        for tid, fn in T.INVENTORY:
            ref["id"] = tid
            try:
                live[tid] = T.repeat(ctx, tid, fn)
            except Exception as e:
                live[tid] = T.summarize(tid, [{"pass": None, "error": repr(e), "run": 1}])
            budget.dump()
            if not budget.can_spend(0.05):
                break
        live["A9"] = T.a9(ctx, live)
        live["B11"] = T.b11(ctx, env.get("SW_SIGNING_KEY"))
        live["B18"] = T.b18(ctx)
        time.sleep(30)
        live["A12"] = T.a12(ctx, start_iso)
    finally:
        cleanup(sw, devs, env)
    return live


def cleanup(sw, devs, env):
    log = []
    try:
        devs.shutdown()
    except Exception as e:
        log.append(repr(e))
    for cid in sw.created["calls"]:
        try:
            sw.end(cid)
        except Exception:
            pass
    for s in sw.created["subscribers"]:
        log.append({"delete_subscriber": s.get("id"), "http": sw.delete_subscriber(s.get("id"))})
    for r in sw.created["resources"]:
        log.append({"delete_resource": r.get("id"), "http": sw.delete_resource("swml_webhooks", r.get("id"))})
    for rid in sw.created["recordings"]:
        if rid:
            log.append({"delete_recording": rid, "http": sw.delete_recording(rid)})
    if env.get("RELEASE_NUMBERS", "false").lower() == "true":
        for n in sw.created["numbers"]:
            log.append({"release_number": n.get("number"), "http": sw.http.delete(f"/api/relay/rest/phone_numbers/{n['id']}").status_code})
    (EVIDENCE / "cleanup.json").write_text(json.dumps(log, indent=2, default=str))


def main():
    EVIDENCE.mkdir(exist_ok=True)
    env = load_env()
    budget = Budget(float(env["BUDGET_USD"]))
    meta = {"started": now_iso()}
    ok, pf = preflight(env)
    meta["preflight"] = pf
    meta["selftests"] = selftests()
    live, blocked = {}, None
    if ok:
        try:
            live = live_run(env, budget)
        except Exception as e:
            blocked = f"live harness failed: {e!r}"
            meta["live_error"] = traceback.format_exc()[-3000:]
    else:
        blocked = "Live tests not run. Preflight failed: " + "; ".join(f"{c['check']} -> {c['detail']}" for c in pf if not c["ok"])
    meta["finished"] = now_iso()
    meta["budget"] = {"cap_usd": budget.cap_usd, "estimated_spend_usd": budget.spent_usd}
    results = merge(live, blocked)
    (EVIDENCE / "run_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    (EVIDENCE / "results_raw.json").write_text(json.dumps(results, indent=2, default=str))
    from .report import write_all
    write_all(results, meta)


if __name__ == "__main__":
    main()
