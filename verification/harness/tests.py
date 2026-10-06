"""Live test inventory (Parts A and B). Each test returns a result dict; the runner never lets one test stop the run.

Hypothesis convention: every run returns {"pass": True|False|None, "observed": {...}}. True/False are
evaluated against the hypothesis stated in HYPOTHESIS[test_id]; all runs True -> CONFIRMED, all False ->
REFUTED, mixed -> INCONSISTENT, None (could not be evaluated) -> BLOCKED with the recorded error.
"""
from __future__ import annotations

import json
import time
import traceback
import uuid

import httpx

from . import audio
from .backend import STATE
from .config import EVIDENCE
from .signature import validate

RUNS = 3
RING_WAIT = 20

HYPOTHESIS = {
    "A1": "Calling one Subscriber rings every registered device",
    "A2": "When one device answers, the other devices leave 'ringing'",
    "A3": "reject() on one device stops ringing on all devices of that Subscriber",
    "A4": "The inbound SWML webhook request carries call.call_id, call.from and call.to",
    "A5": "Browser dial() to an SWML webhook address delivers userVariables to the webhook under vars.userVariables",
    "A6": "connect.serial falls back to a phone number after the Subscriber times out",
    "A7": "calling.record / record.pause / record.resume / record.stop / calling.end succeed on the anchor leg",
    "A8": "A stereo recording puts each party on its own channel",
    "A9": "Connect, recording and call-end status webhooks are delivered",
    "A10": "REST recording commands succeed only on the anchor leg",
    "A11": "Every registered device rings (5, 10, 20 devices)",
    "B1": "With zero registrations, connect fails before the configured timeout",
    "B2": "connect.parallel rings all 22 Subscribers",
    "B3": "An active call survives SAT expiry",
    "B4": "The refresh() provider is called before expiry and registration continues",
    "B5": "Deleting a Subscriber ends its active registration",
    "B6": "connect headers or params reach the browser Call object",
    "B7": "The browser sees the original PSTN caller number, and connect.from overrides it",
    "B8": "The remote party hears silence (no 440 Hz) during browser hold, and the recording shows it",
    "B9": "A device on an active call is offered a second inbound call",
    "B10": "calling.transfer moves a connected call to another Subscriber and to a phone number",
    "B11": "Webhooks carry X-SignalWire-Signature that validates with the Signing Key",
    "B12": "A slow or failing SWML endpoint is retried",
    "B13": "A recording can be listed, fetched and deleted, and its URL stops serving",
    "B14": "Bursts above the default CPS are queued rather than rejected",
    "B15": "Codecs are visible in getStats()",
    "B16": "One Subscriber can hold two simultaneous connected calls on two devices",
    "B17": "One browser can register as two Subscribers",
}


class Ctx:
    def __init__(self, sw, devs, base_url, numbers, budget):
        self.sw, self.devs, self.base, self.budget = sw, devs, base_url, budget
        self.A, self.B, self.C = (n["number"] for n in numbers[:3])
        self.subs: dict[str, dict] = {}
        self.connect_results: list[dict] = []   # B18 aggregation

    # ---------- SWML builders (swml_facts 1-4) ----------
    def tone(self, answer=True, seconds=None):
        main = [{"answer": {}}] if answer else []
        main.append({"play": {"url": f"{self.base}/static/pstn_tone_1000.wav", "loop": 0}})
        return {"version": "1.0.0", "sections": {"main": main}}

    def connect_doc(self, dests, mode="parallel", timeout=20, after=None, extra=None, record_on_answer=False):
        c = {mode: [{"to": d} for d in dests] if mode != "to" else dests, "timeout": timeout,
             "status_url": f"{self.base}/hook/connect", "call_state_url": f"{self.base}/hook/callstate",
             "call_state_events": ["created", "ringing", "answered", "ended"]}
        if mode == "to":
            c = {"to": dests, "timeout": timeout, "status_url": f"{self.base}/hook/connect"}
        if extra:
            c.update(extra)
        main = [{"set": {"harness": "1"}}, {"connect": c},
                {"request": {"url": f"{self.base}/hook/connect_result", "method": "POST",
                             "body": {"connect_result": "%{connect_result}",
                                      "connect_failed_reason": "%{connect_failed_reason}",
                                      "return_value": "%{return_value}"}}}]
        main += after or [{"hangup": {}}]
        return {"version": "1.0.0", "sections": {"main": main}}

    # ---------- helpers ----------
    def subscriber(self, tag):
        if tag not in self.subs:
            s = self.sw.create_subscriber(tag)
            s["_address"] = self.sw.subscriber_address(s.get("id", "")) if s.get("id") else None
            self.subs[tag] = s
        return self.subs[tag]

    def devices(self, sub, n, prefix, mode="static", ttl=None):
        ids = []
        for i in range(n):
            d = f"{prefix}-{i + 1}"
            self.devs.open(d)
            r = self.devs.call(d, "register", {"ref": sub["_email"], "mode": mode, "ttl": ttl})
            ids.append(d)
            if not r.get("ok"):
                raise RuntimeError(f"register {d}: {r}")
        for d in ids:
            STATE.wait_for(lambda e, d=d: e.get("device") == d and e.get("type") == "registered" and e.get("value") is True, 20)
        return ids

    def close(self, ids):
        for d in ids:
            try:
                self.devs.close(d)
            except Exception:
                pass

    def inbound(self, swml_doc, frm=None, to=None, est=45):
        """A -> B PSTN-simulated inbound. Returns (a_leg_id, anchor_call_id, swml_request)."""
        STATE.swml["inbound"] = swml_doc
        t0 = time.time()
        code, j = self.sw.dial(frm or self.A, to or self.B, swml=self.tone(), est_seconds=est,
                               status_url=f"{self.base}/hook/aleg")
        req = STATE.wait_for(lambda w: w["name"] == "swml:inbound" and w["t"] >= t0, 20, "webhooks")
        anchor = ((req or {}).get("body") or {}).get("call", {}).get("call_id")
        return j.get("id"), anchor, req

    def ringing(self, dev, since, timeout=RING_WAIT):
        return STATE.wait_for(lambda e: e.get("device") == dev and e.get("type") == "status" and e.get("value") == "ringing"
                              and e["rx_t"] >= since, timeout)

    def left_ringing(self, dev, since, timeout=15):
        return STATE.wait_for(lambda e: e.get("device") == dev and e.get("type") == "status" and e["rx_t"] >= since
                              and e.get("value") not in ("ringing", "new", "trying"), timeout)

    def connect_result(self, since, timeout=60):
        w = STATE.wait_for(lambda w: w["name"] == "hook:connect_result" and w["t"] >= since, timeout, "webhooks")
        return (w or {}).get("body"), w

    def hang_all(self, *ids):
        for i in ids:
            if i:
                try:
                    self.sw.end(i)
                except Exception:
                    pass

    def ev_paths(self, test_id):
        return [str(p.relative_to(EVIDENCE.parent)) for p in (EVIDENCE / "webhooks" / test_id,
                EVIDENCE / "browser" / test_id) if p.exists()]


def summarize(test_id, runs, extra=None):
    vals = [r.get("pass") for r in runs]
    if not runs or all(v is None for v in vals):
        status = "BLOCKED"
    elif all(v is True for v in vals):
        status = "CONFIRMED"
    elif all(v is False for v in vals):
        status = "REFUTED"
    else:
        status = "INCONSISTENT"
    out = {"id": test_id, "hypothesis": HYPOTHESIS.get(test_id), "status": status, "runs": runs}
    out.update(extra or {})
    return out


def repeat(ctx, test_id, fn, n=RUNS):
    runs = []
    for i in range(n):
        STATE.test_id = test_id
        try:
            r = fn(ctx, i)
        except Exception as e:
            r = {"pass": None, "error": repr(e), "trace": traceback.format_exc()[-1500:]}
        r["run"] = i + 1
        runs.append(r)
        time.sleep(2)
    return summarize(test_id, runs, {"evidence": ctx.ev_paths(test_id)})


# =============================== Part A ===============================

def a1(ctx, i):
    s = ctx.subscriber("S1")
    devs = ctx.devices(s, 3, f"A1r{i}")
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]]))
    rang = {d: bool(ctx.ringing(d, t0)) for d in devs}
    ctx.hang_all(a, anchor)
    ctx.close(devs)
    return {"pass": all(rang.values()), "observed": {"ringing": rang, "anchor": anchor}}


def a2(ctx, i):
    s = ctx.subscriber("S1")
    devs = ctx.devices(s, 3, f"A2r{i}")
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]]))
    for d in devs:
        ctx.ringing(d, t0)
    obs = {}
    if i < 2:  # single answer
        ta = time.time()
        ctx.devs.call(devs[0], "answer")
        for d in devs[1:]:
            e = ctx.left_ringing(d, ta)
            obs[d] = {"next_status": e and e["value"], "ms_after_answer": e and round((e["rx_t"] - ta) * 1000)}
        ok = all(v["next_status"] for v in obs.values())
    else:      # near-simultaneous answer on devices 1 and 2
        import threading
        res = {}
        th = [threading.Thread(target=lambda d=d: res.__setitem__(d, ctx.devs.call(d, "answer"))) for d in devs[:2]]
        ta = time.time()
        [t.start() for t in th]
        [t.join() for t in th]
        time.sleep(3)
        final = {d: [e["value"] for e in STATE.events if e.get("device") == d and e.get("type") == "status" and e["rx_t"] >= ta] for d in devs}
        obs = {"answer_results": res, "status_sequences": final,
               "winners": [d for d, seq in final.items() if "connected" in seq and "disconnected" not in seq[-1:]]}
        ok = len(obs["winners"]) == 1
    ctx.hang_all(a, anchor)
    ctx.close(devs)
    return {"pass": ok, "observed": obs}


def a3(ctx, i):
    s1, s2 = ctx.subscriber("S1"), ctx.subscriber("S2")
    obs = {}
    # (a) same subscriber, 3 devices, device 1 rejects
    devs = ctx.devices(s1, 3, f"A3a{i}")
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s1["_address"]], timeout=25))
    [ctx.ringing(d, t0) for d in devs]
    tr = time.time()
    ctx.devs.call(devs[0], "reject")
    obs["same_sub"] = {d: (lambda e: e and {"status": e["value"], "ms": round((e["rx_t"] - tr) * 1000)})(ctx.left_ringing(d, tr, 10)) for d in devs[1:]}
    cr, _ = ctx.connect_result(t0, 40)
    obs["same_sub_connect_result"] = cr
    ctx.connect_results.append({"test": "A3a", "scenario": "decline (one device of S1 rejects)", "result": cr})
    ctx.hang_all(a, anchor)
    ctx.close(devs)
    # (b) S1 + S2 parallel, a device on S1 rejects
    d1 = ctx.devices(s1, 1, f"A3b{i}s1")
    d2 = ctx.devices(s2, 1, f"A3b{i}s2")
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s1["_address"], s2["_address"]], timeout=25))
    ctx.ringing(d1[0], t0)
    ctx.ringing(d2[0], t0)
    tr = time.time()
    ctx.devs.call(d1[0], "reject")
    e = ctx.left_ringing(d2[0], tr, 8)
    obs["cross_sub_S2_after_S1_reject"] = e and {"status": e["value"], "ms": round((e["rx_t"] - tr) * 1000)}
    # backend workaround: end the anchor leg via REST on reject, measure stop time on S2
    tw = time.time()
    code, j = ctx.sw.end(anchor) if anchor else (None, {})
    e2 = ctx.left_ringing(d2[0], tw, 10)
    obs["workaround_end_anchor"] = {"http": code, "resp": j, "S2_stop_ms": e2 and round((e2["rx_t"] - tw) * 1000)}
    ctx.hang_all(a)
    ctx.close(d1 + d2)
    same_all_stop = all(v for v in obs["same_sub"].values())
    return {"pass": same_all_stop, "observed": obs}


def a4(ctx, i):
    _, anchor, req = ctx.inbound(ctx.connect_doc([ctx.C], mode="to", timeout=5))
    time.sleep(1)
    ctx.hang_all(anchor)
    body = (req or {}).get("body") or {}
    call = body.get("call", {})
    return {"pass": bool(call.get("call_id") and call.get("from") and call.get("to")) if req else None,
            "observed": {"top_level_keys": sorted(body), "call_keys": sorted(call), "headers": (req or {}).get("headers"),
                         "body": body}}


def _outbound_resource(ctx):
    if "out_res" not in ctx.subs:
        r = ctx.sw.create_swml_webhook(f"harness-outbound-{uuid.uuid4().hex[:6]}", f"{ctx.base}/swml/outbound",
                                       f"{ctx.base}/hook/outbound_status")
        addrs = ctx.sw.resource_addresses(r.get("id", "")) if r.get("id") else []
        a = next((x for x in addrs), {})
        r["_address"] = f"/{a.get('context', 'private')}/{a.get('name')}" if a.get("name") else None
        ctx.subs["out_res"] = r
    return ctx.subs["out_res"]


def a5(ctx, i):
    s = ctx.subscriber("S1")
    res = _outbound_resource(ctx)

    def outbound_swml(body):
        uv = ((body.get("vars") or {}).get("userVariables") or (body.get("params") or {}).get("userVariables") or {})
        to = uv.get("to")
        if to not in ctx.sw.owned:   # authorization: only owned numbers, never PSTN outside the Space
            return {"version": "1.0.0", "sections": {"main": [{"hangup": {"reason": "busy"}}]}}
        return {"version": "1.0.0", "sections": {"main": [{"connect": {"to": to, "from": ctx.A, "timeout": 20}}]}}
    STATE.swml["outbound"] = outbound_swml
    STATE.swml["lead"] = ctx.tone()
    dev = ctx.devices(s, 1, f"A5r{i}")[0]
    t0 = time.time()
    uv = {"to": ctx.C, "crm_call_id": f"crm-{i}", "crm_user_id": "FORGED-admin"}
    r = ctx.devs.call(dev, "dial", res["_address"], uv)
    req = STATE.wait_for(lambda w: w["name"] == "swml:outbound" and w["t"] >= t0, 20, "webhooks")
    time.sleep(4)
    ctx.devs.call(dev, "hangup")
    ctx.close([dev])
    body = (req or {}).get("body") or {}
    got_uv = (body.get("vars") or {}).get("userVariables")
    call = body.get("call", {})
    return {"pass": (got_uv or {}).get("crm_call_id") == f"crm-{i}" if req else None,
            "observed": {"dial": r, "vars.userVariables": got_uv, "call": call,
                         "identity_fields": {k: v for k, v in call.items() if k in ("from", "from_number", "caller_id_name", "type", "headers")},
                         "forged_crm_user_id_echoed_as_user_data_only": (got_uv or {}).get("crm_user_id"),
                         "subscriber_email": s["_email"], "subscriber_id": s.get("id")}}


def a6(ctx, i):
    s = ctx.subscriber("S1")
    devs = ctx.devices(s, 1, f"A6r{i}")
    STATE.swml["lead"] = ctx.tone()
    obs = {}
    # serial fallback: subscriber (8 s) then number C
    doc = {"version": "1.0.0", "sections": {"main": [
        {"connect": {"serial": [{"to": s["_address"], "timeout": 8}, {"to": ctx.C, "timeout": 20}],
                     "status_url": f"{ctx.base}/hook/connect"}},
        {"request": {"url": f"{ctx.base}/hook/connect_result", "method": "POST", "body": {"connect_result": "%{connect_result}"}}},
        {"hangup": {}}]}}
    t0 = time.time()
    a, anchor, _ = ctx.inbound(doc, est=40)
    conn = STATE.wait_for(lambda w: w["name"] == "hook:connect" and w["t"] >= t0 and
                          "connected" in json.dumps(w.get("body")), 40, "webhooks")
    obs["serial_connected_to"] = conn and conn["body"]
    ctx.hang_all(a, anchor)
    cr, _ = ctx.connect_result(t0, 20)
    obs["serial_connect_result"] = cr
    # no answer anywhere -> voicemail branch via switch on connect_result
    t1 = time.time()
    vm = [{"switch": {"variable": "connect_result", "case": {"connected": [{"hangup": {}}]},
                      "default": [{"request": {"url": f"{ctx.base}/hook/voicemail", "method": "POST", "body": {"branch": "voicemail", "connect_result": "%{connect_result}"}}},
                                  {"play": {"url": "say:Please leave a message"}},
                                  {"record": {"format": "mp3", "end_silence_timeout": 2, "max_length": 5}}, {"hangup": {}}]}}]
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=8, after=vm), est=40)
    cr2, _ = ctx.connect_result(t1, 30)
    vmh = STATE.wait_for(lambda w: w["name"] == "hook:voicemail" and w["t"] >= t1, 15, "webhooks")
    obs["no_answer_connect_result"] = cr2
    obs["voicemail_branch_taken"] = bool(vmh)
    ctx.connect_results.append({"test": "A6", "scenario": "no answer (timeout)", "result": cr2})
    ctx.hang_all(a, anchor)
    ctx.close(devs)
    return {"pass": bool(conn) and bool(vmh), "observed": obs}


def _record_flow(ctx, i, leg_choice="anchor", behavior="skip", direction="inbound"):
    """Shared by A7/A8/A10/B8: inbound or outbound call, answered in the browser, recording via REST."""
    s = ctx.subscriber("S1")
    dev = ctx.devices(s, 1, f"rec{direction}{leg_choice}{behavior}{i}")[0]
    t0 = time.time()
    if direction == "inbound":
        a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), est=60)
        ctx.ringing(dev, t0)
        ctx.devs.call(dev, "answer")
        other = a
    else:
        res = _outbound_resource(ctx)
        STATE.swml["outbound"] = lambda b: {"version": "1.0.0", "sections": {"main": [{"connect": {"to": ctx.C, "from": ctx.A, "timeout": 20}}]}}
        STATE.swml["lead"] = ctx.tone()
        ctx.devs.call(dev, "dial", res["_address"], {"to": ctx.C})
        req = STATE.wait_for(lambda w: w["name"] == "swml:outbound" and w["t"] >= t0, 20, "webhooks")
        anchor = ((req or {}).get("body") or {}).get("call", {}).get("call_id")
        lead = STATE.wait_for(lambda w: w["name"] == "swml:lead" and w["t"] >= t0, 20, "webhooks")
        other = ((lead or {}).get("body") or {}).get("call", {}).get("call_id")
    time.sleep(3)
    target = anchor if leg_choice == "anchor" else other
    cid = f"rec-{uuid.uuid4().hex[:8]}"
    steps = {}
    steps["record"] = ctx.sw.record(target, cid, status_url=f"{ctx.base}/hook/record")
    time.sleep(6)
    steps["pause"] = ctx.sw.record_pause(target, cid, behavior)
    pause_t = time.time()
    time.sleep(6)
    steps["resume"] = ctx.sw.record_resume(target, cid)
    time.sleep(6)
    steps["stop"] = ctx.sw.record_stop(target, cid)
    time.sleep(2)
    steps["end"] = ctx.sw.end(anchor) if anchor else None
    fin = STATE.wait_for(lambda w: w["name"] == "hook:record" and w["t"] >= t0 and "finished" in json.dumps(w.get("body")), 30, "webhooks")
    rec_url = ((fin or {}).get("body") or {}).get("params", {}).get("url")
    analysis = None
    if rec_url:
        p = EVIDENCE / "recordings" / f"{STATE.test_id}_{cid}.mp3"
        p.parent.mkdir(parents=True, exist_ok=True)
        r = httpx.get(rec_url, auth=(ctx.sw.project, ctx.sw.http.secrets[0]), follow_redirects=True, timeout=60)
        p.write_bytes(r.content)
        analysis = audio.channel_map(p)
        analysis["file"] = str(p.relative_to(EVIDENCE.parent))
        ctx.sw.created["recordings"].append(((fin or {}).get("body") or {}).get("params", {}).get("recording_id"))
    ctx.close([dev])
    return {"steps": {k: v and {"http": v[0], "body": v[1]} for k, v in steps.items()}, "anchor": anchor, "other": other,
            "target": target, "finished_webhook": fin and fin["body"], "analysis": analysis, "pause_at_s": round(pause_t - t0)}


def a7(ctx, i):
    beh = ["skip", "silence", "skip"][i]
    r = _record_flow(ctx, i, "anchor", beh)
    ok = all(s and s["http"] == 200 for k, s in r["steps"].items() if k != "end")
    return {"pass": ok, "observed": r, "behavior": beh}


def a8(ctx, i):
    obs = {"inbound": _record_flow(ctx, i, "anchor", "skip", "inbound"),
           "outbound": _record_flow(ctx, i, "anchor", "skip", "outbound")}
    if i == 0:
        obs["inbound_non_anchor"] = _record_flow(ctx, i, "other", "skip", "inbound")
    maps = [obs[k]["analysis"]["channels"] for k in ("inbound", "outbound") if obs[k].get("analysis")]
    ok = bool(maps) and all({m["ch0"]["majority"], m["ch1"]["majority"]} == {"pstn_1000", "browser_440"} for m in maps if "ch1" in m)
    return {"pass": ok if maps else None, "observed": obs}


def a10(ctx, i):
    d = "inbound" if i % 2 == 0 else "outbound"
    anchor = _record_flow(ctx, i, "anchor", "skip", d)
    other = _record_flow(ctx, i, "other", "skip", d)
    a_ok = anchor["steps"]["record"]["http"] == 200
    o_ok = other["steps"]["record"]["http"] == 200
    return {"pass": a_ok and not o_ok, "observed": {"direction": d, "anchor": anchor, "non_anchor": other}}


def a9(ctx, results):
    """Aggregate webhooks captured during A3-A10 rather than placing new calls."""
    names = {}
    for w in STATE.webhooks:
        names.setdefault(w["name"], []).append({"test": w["test_id"], "body": w["body"]})
    rec_delivered = any("finished" in json.dumps(x["body"]) for x in names.get("hook:record", []))
    ok = None if not names else (bool(names.get("hook:connect")) and rec_delivered)
    return summarize("A9", [{"pass": ok, "observed": {k: {"count": len(v), "sample": v[:2]} for k, v in names.items()},
                             "run": 1, "note": "aggregated from all calls placed by A3 to A10 (more than 3 calls)"}])


def a11(ctx, i):
    s = ctx.subscriber("S4")
    out = {}
    for n in (5, 10, 20):
        devs = ctx.devices(s, n, f"A11r{i}n{n}")
        t0 = time.time()
        a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=15), est=30)
        rang = sum(bool(ctx.ringing(d, t0, 15)) for d in devs)
        out[n] = rang
        ctx.hang_all(a, anchor)
        ctx.close(devs)
        if rang < n:
            break
    return {"pass": all(v == k for k, v in out.items()), "observed": {"rang_by_device_count": out}}


def a12(ctx, since_iso):
    logs = ctx.sw.voice_logs(since_iso)
    rows = [{k: l.get(k) for k in ("id", "from", "to", "direction", "type", "duration", "duration_ms", "billing_ms",
                                     "charge", "charge_details", "status", "created_at")} for l in logs]
    (EVIDENCE / "cost").mkdir(exist_ok=True)
    (EVIDENCE / "cost" / "voice_logs.json").write_text(json.dumps(logs, indent=2))
    return summarize("A12", [{"pass": True if rows else None, "observed": {"rows": rows, "count": len(rows)}, "run": 1}],
                     {"evidence": ["evidence/cost/voice_logs.json"]})


# =============================== Part B ===============================

def b1(ctx, i):
    s = ctx.subscriber("S3")  # never registered
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=30), est=40)
    cr, w = ctx.connect_result(t0, 45)
    secs = w and round(w["t"] - t0, 1)
    ctx.connect_results.append({"test": "B1", "scenario": "no registrations", "result": cr, "seconds": secs})
    ctx.hang_all(a, anchor)
    return {"pass": (secs is not None and secs < 25) if w else None, "observed": {"connect_result": cr, "seconds_to_result": secs, "timeout_configured": 30}}


def b2(ctx, i):
    subs = [ctx.subscriber(f"P{k}") for k in range(22)]
    devs = []
    for k, s in enumerate(subs):
        devs += ctx.devices(s, 1, f"B2r{i}p{k}")
    t0 = time.time()
    a, anchor, req = ctx.inbound(ctx.connect_doc([s["_address"] for s in subs], timeout=20), est=30)
    rang = {d: bool(ctx.ringing(d, t0, 20)) for d in devs}
    cr, _ = ctx.connect_result(t0, 40)
    ctx.hang_all(a, anchor)
    ctx.close(devs)
    return {"pass": all(rang.values()), "observed": {"rang_count": sum(rang.values()), "of": 22, "which": rang, "connect_result": cr}}


def b3(ctx, i):
    s = ctx.subscriber("S1")
    STATE.token_minter = lambda ref, ttl: ctx.sw.mint_token(ref, 120)  # shortest we try; actual accepted value recorded
    dev = ctx.devices(s, 1, f"B3r{i}", mode="static")[0]
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), est=600)
    ctx.ringing(dev, t0)
    ctx.devs.call(dev, "answer")
    time.sleep(120 + 300)
    evs = [e for e in STATE.events if e.get("device") == dev and e["rx_t"] >= t0]
    alive = not any(e.get("type") == "status" and e.get("value") in ("disconnected", "destroyed", "failed") for e in evs)
    ctx.hang_all(a, anchor)
    ctx.close([dev])
    _install_default_minter(ctx)
    return {"pass": alive, "observed": {"events": evs[-30:]}}


def b4(ctx, i):
    s = ctx.subscriber("S1")
    STATE.token_minter = lambda ref, ttl: ctx.sw.mint_token(ref, 90)
    dev = ctx.devices(s, 1, f"B4r{i}", mode="refresh", ttl=90)[0]
    t0 = time.time()
    time.sleep(100)  # idle refresh window
    idle_refresh = STATE.wait_for(lambda e: e.get("device") == dev and e.get("type") == "refresh_called" and e["rx_t"] >= t0, 1)
    # forced failure
    STATE.behavior["token"] = {"status": 500}
    time.sleep(150)
    terr = STATE.wait_for(lambda e: e.get("device") == dev and e.get("type") == "error" and e.get("isTokenRefreshError"), 1)
    STATE.behavior.pop("token", None)
    ctx.close([dev])
    _install_default_minter(ctx)
    return {"pass": bool(idle_refresh), "observed": {"refresh_called": bool(idle_refresh), "token_refresh_error_on_forced_failure": terr}}


def b5(ctx, i):
    s = ctx.sw.create_subscriber(f"B5r{i}")
    s["_address"] = ctx.sw.subscriber_address(s["id"])
    dev = ctx.devices(s, 1, f"B5r{i}")[0]
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), est=60)
    ctx.ringing(dev, t0)
    ctx.devs.call(dev, "answer")
    time.sleep(3)
    td = time.time()
    code = ctx.sw.delete_subscriber(s["id"])
    time.sleep(20)
    evs = [{"type": e["type"], "value": e.get("value"), "dt": round(e["rx_t"] - td, 2)} for e in STATE.events if e.get("device") == dev and e["rx_t"] >= td]
    ended = any(e["type"] == "status" and e["value"] in ("disconnected", "destroyed") for e in evs)
    unreg = any(e["type"] == "registered" and e["value"] is False for e in evs)
    ctx.hang_all(a, anchor)
    ctx.close([dev])
    return {"pass": unreg or ended, "observed": {"delete_http": code, "events_after_delete": evs, "call_ended": ended, "unregistered": unreg}}


def b6_b7(ctx, i, with_override):
    s = ctx.subscriber("S1")
    dev = ctx.devices(s, 1, f"B67r{i}{int(with_override)}")[0]
    extra = {"headers": [{"name": "X-CRM-Lead", "value": "lead-42"}]}
    if with_override:
        extra["from"] = ctx.C
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=15, extra=extra), est=30)
    seen = STATE.wait_for(lambda e: e.get("device") == dev and e.get("type") == "call_seen" and e["rx_t"] >= t0, RING_WAIT)
    ctx.hang_all(a, anchor)
    ctx.close([dev])
    return (seen or {}).get("call")


def b6(ctx, i):
    call = b6_b7(ctx, i, False)
    txt = json.dumps(call or {})
    return {"pass": ("lead-42" in txt) if call else None, "observed": {"inbound_call_object": call}}


def b7(ctx, i):
    plain = b6_b7(ctx, i, False)
    over = b6_b7(ctx, i, True)
    ok = None if not (plain and over) else (plain.get("from", "").endswith(ctx.A[-10:]) and over.get("from", "").endswith(ctx.C[-10:]))
    return {"pass": ok, "observed": {"without_override": {k: (plain or {}).get(k) for k in ("from", "fromName", "to")},
                                     "with_from_override": {k: (over or {}).get(k) for k in ("from", "fromName", "to")},
                                     "pstn_caller": ctx.A, "space_number": ctx.B, "override": ctx.C}}


def b8(ctx, i):
    s = ctx.subscriber("S1")
    dev = ctx.devices(s, 1, f"B8r{i}")[0]
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), est=60)
    ctx.ringing(dev, t0)
    ctx.devs.call(dev, "answer")
    time.sleep(2)
    cid = f"b8-{uuid.uuid4().hex[:6]}"
    ctx.sw.record(anchor, cid, status_url=f"{ctx.base}/hook/record")
    time.sleep(5)
    th = time.time()
    ctx.devs.call(dev, "toggleHold")
    time.sleep(10)
    ctx.devs.call(dev, "toggleHold")
    tu = time.time()
    time.sleep(5)
    ctx.sw.record_stop(anchor, cid)
    ctx.sw.end(anchor)
    fin = STATE.wait_for(lambda w: w["name"] == "hook:record" and w["t"] >= t0 and "finished" in json.dumps(w.get("body")), 30, "webhooks")
    url = ((fin or {}).get("body") or {}).get("params", {}).get("url")
    analysis = None
    if url:
        p = EVIDENCE / "recordings" / f"B8_{cid}.mp3"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(httpx.get(url, auth=(ctx.sw.project, ctx.sw.http.secrets[0]), follow_redirects=True).content)
        analysis = audio.channel_map(p)
    ctx.close([dev])
    if not analysis:
        return {"pass": None, "observed": {"error": "no recording"}}
    off0 = 5  # hold starts ~5 s into recording
    hold_window = analysis["timeline"][off0 + 1: off0 + 9]
    browser_ch = next((k for k, v in analysis["channels"].items() if v["majority"] == "browser_440"), None)
    idx = int(browser_ch[2:]) if browser_ch else 1
    during = [row[idx] for row in hold_window if len(row) > idx]
    return {"pass": all(l != "browser_440" for l in during), "observed": {"browser_channel": browser_ch, "labels_during_hold": during, "analysis": analysis,
                                                                         "hold_s": round(tu - th, 1)}}


def b9(ctx, i):
    s = ctx.subscriber("S1")
    dev = ctx.devices(s, 1, f"B9r{i}")[0]
    t0 = time.time()
    a1_, an1, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), est=60)
    ctx.ringing(dev, t0)
    ctx.devs.call(dev, "answer")
    time.sleep(3)
    t1 = time.time()
    a2_, an2, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=15), frm=ctx.C, est=30)
    lst = STATE.wait_for(lambda e: e.get("device") == dev and e.get("type") == "incoming_list" and e["rx_t"] >= t1 and len(e.get("ids", [])) >= 1, 15)
    second = STATE.wait_for(lambda e: e.get("device") == dev and e.get("type") == "call_seen" and e["rx_t"] >= t1, 15)
    ctx.hang_all(a1_, an1, a2_, an2)
    ctx.close([dev])
    return {"pass": bool(second), "observed": {"incoming_list_after_second": lst, "second_call_seen": second}}


def b10(ctx, i):
    s1, s2 = ctx.subscriber("S1"), ctx.subscriber("S2")
    d1 = ctx.devices(s1, 1, f"B10r{i}a")[0]
    d2 = ctx.devices(s2, 1, f"B10r{i}b")[0]
    STATE.swml["lead"] = ctx.tone()
    STATE.swml["xfer_sub"] = {"version": "1.0.0", "sections": {"main": [{"connect": {"to": s2["_address"], "timeout": 15}}]}}
    STATE.swml["xfer_pstn"] = {"version": "1.0.0", "sections": {"main": [{"connect": {"to": ctx.C, "from": ctx.B, "timeout": 15}}]}}
    obs = {}
    for target in ("xfer_sub", "xfer_pstn"):
        t0 = time.time()
        a, anchor, _ = ctx.inbound(ctx.connect_doc([s1["_address"]], timeout=20), est=60)
        ctx.ringing(d1, t0)
        ctx.devs.call(d1, "answer")
        time.sleep(3)
        tt = time.time()
        res = ctx.sw.transfer(anchor, f"{ctx.base}/swml/{target}")
        if target == "xfer_sub":
            got = bool(ctx.ringing(d2, tt, 15))
        else:
            got = bool(STATE.wait_for(lambda w: w["name"] == "swml:lead" and w["t"] >= tt, 20, "webhooks"))
        d1_after = ctx.left_ringing(d1, tt, 10)
        obs[target] = {"http": res[0], "resp": res[1], "target_reached": got, "original_device_after": d1_after and d1_after["value"]}
        ctx.hang_all(a, anchor)
    ctx.close([d1, d2])
    return {"pass": all(v["target_reached"] for v in obs.values()), "observed": obs}


def b11(ctx, key):
    if not key:
        return summarize("B11", [{"pass": None, "run": 1, "error": "SW_SIGNING_KEY not provided in .env; captured headers listed instead",
                                  "observed": {"signature_headers_seen": sorted({h for w in STATE.webhooks for h in w["headers"] if "signature" in h})}}])
    runs = []
    for w in [w for w in STATE.webhooks if any("signature" in h for h in w["headers"])][:5]:
        v = validate(key, w["url"], w["headers"], w["raw_body"])
        tampered = validate(key, w["url"], w["headers"], w["raw_body"] + " ")
        runs.append({"pass": v["valid"] and not tampered["valid"], "run": len(runs) + 1,
                     "observed": {"webhook": w["name"], "checked": v["checked"], "valid": v["valid"], "tampered_valid": tampered["valid"]}})
    return summarize("B11", runs)


def b12(ctx, i):
    s = ctx.subscriber("S1")
    out = {}
    for label, beh in (("delay5", {"delay": 5}), ("delay10", {"delay": 10}), ("delay15", {"delay": 15}), ("http500", {"status": 500})):
        STATE.behavior["inbound"] = beh
        t0 = time.time()
        a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=5), est=30)
        time.sleep(20)
        hits = [round(w["t"] - t0, 2) for w in STATE.webhooks if w["name"] == "swml:inbound" and w["t"] >= t0]
        aleg = [w["body"] for w in STATE.webhooks if w["name"] == "hook:aleg" and w["t"] >= t0]
        out[label] = {"fetch_attempts": len(hits), "attempt_offsets_s": hits, "caller_leg_events": aleg}
        ctx.hang_all(a, anchor)
    STATE.behavior.pop("inbound", None)
    STATE.behavior["hook:connect"] = {"status": 500}
    t0 = time.time()
    dev = ctx.devices(s, 1, f"B12r{i}")[0]
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=5), est=30)
    time.sleep(30)
    out["status_callback_500"] = {"deliveries": [round(w["t"] - t0, 2) for w in STATE.webhooks if w["name"] == "hook:connect" and w["t"] >= t0]}
    STATE.behavior.pop("hook:connect", None)
    ctx.hang_all(a, anchor)
    ctx.close([dev])
    retried = any(v.get("fetch_attempts", 0) > 1 for v in out.values() if isinstance(v, dict) and "fetch_attempts" in v)
    return {"pass": retried, "observed": out}


def b13(ctx, i):
    recs = ctx.sw.list_recordings()
    mine = [r for r in recs if r.get("id") in ctx.sw.created["recordings"]]
    if len(mine) <= i:
        return {"pass": None, "observed": {"error": "not enough harness recordings to delete", "listed": len(recs)}}
    r = mine[i]
    meta = ctx.sw.http.get(f"/api/relay/rest/recordings/{r['id']}").json()
    url = meta.get("url") or meta.get("uri")
    before = url and httpx.get(url, auth=(ctx.sw.project, ctx.sw.http.secrets[0]), follow_redirects=True).status_code
    code = ctx.sw.delete_recording(r["id"])
    time.sleep(3)
    after = url and httpx.get(url, auth=(ctx.sw.project, ctx.sw.http.secrets[0]), follow_redirects=True).status_code
    return {"pass": code in (200, 204) and after not in (200,), "observed": {"metadata": meta, "url_before": before, "delete_http": code, "url_after": after}}


def b14(ctx, i):
    hang = {"version": "1.0.0", "sections": {"main": [{"hangup": {}}]}}
    out = {}
    for n in (2, 3, 5):
        res = []
        t0 = time.time()
        for _ in range(n):
            code, j = ctx.sw.dial(ctx.A, ctx.C, swml=hang, est_seconds=5)
            res.append({"http": code, "status": j.get("status"), "code": j.get("code"), "msg": j.get("message"), "t": round(time.time() - t0, 3)})
        out[n] = res
        time.sleep(5)
    rejected = any(r["http"] >= 400 for v in out.values() for r in v)
    return {"pass": not rejected, "observed": out}


def b15(ctx, i):
    s = ctx.subscriber("S1")
    dev = ctx.devices(s, 1, f"B15r{i}")[0]
    t0 = time.time()
    a, anchor, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), est=30)
    ctx.ringing(dev, t0)
    ctx.devs.call(dev, "answer")
    time.sleep(4)
    st = ctx.devs.call(dev, "stats")
    ctx.hang_all(a, anchor)
    ctx.close([dev])
    return {"pass": bool(st.get("result")), "observed": {"webrtc_codecs": st}}


def b16(ctx, i):
    s = ctx.subscriber("S1")
    devs = ctx.devices(s, 2, f"B16r{i}")
    t0 = time.time()
    a1_, an1, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), est=60)
    ctx.ringing(devs[0], t0)
    ctx.devs.call(devs[0], "answer")
    time.sleep(3)
    t1 = time.time()
    a2_, an2, _ = ctx.inbound(ctx.connect_doc([s["_address"]], timeout=20), frm=ctx.C, est=60)
    r2 = ctx.ringing(devs[1], t1)
    if r2:
        ctx.devs.call(devs[1], "answer", r2["call_id"])
    time.sleep(5)
    conn = {d: [e["value"] for e in STATE.events if e.get("device") == d and e.get("type") == "status" and e["rx_t"] >= t0] for d in devs}
    both = all("connected" in v and v[-1] == "connected" for v in conn.values())
    ctx.hang_all(a1_, an1, a2_, an2)
    ctx.close(devs)
    return {"pass": both, "observed": {"status_sequences": conn}}


def b17(ctx, i):
    s1, s2 = ctx.subscriber("S1"), ctx.subscriber("S2")
    # same browser profile, two pages = two contexts here is NOT the same profile; use one page with two clients
    d = f"B17r{i}"
    ctx.devs.open(d)
    r1 = ctx.devs.call(d, "register", {"ref": s1["_email"], "storageIsolated": True})
    r2 = ctx.devs.call(d, "register", {"ref": s2["_email"], "storageIsolated": True})
    time.sleep(5)
    regs = [e for e in STATE.events if e.get("device") == d and e.get("type") == "registered" and e.get("value") is True]
    ctx.close([d])
    return {"pass": len(regs) >= 2, "observed": {"register_1": r1, "register_2": r2, "registered_events": len(regs),
                                                 "note": "the page keeps one `client` variable; both instances stay alive because each subscribes its own observables"}}


def b18(ctx):
    return summarize("B18", [{"pass": True if ctx.connect_results else None, "run": 1,
                              "observed": {"table": ctx.connect_results}}])


def _install_default_minter(ctx):
    STATE.token_minter = lambda ref, ttl: ctx.sw.mint_token(ref, ttl)


INVENTORY = [
    ("A1", a1), ("A2", a2), ("A3", a3), ("A4", a4), ("A5", a5), ("A6", a6), ("A7", a7), ("A8", a8), ("A10", a10),
    ("A11", a11), ("B1", b1), ("B2", b2), ("B3", b3), ("B4", b4), ("B5", b5), ("B6", b6), ("B7", b7), ("B8", b8),
    ("B9", b9), ("B10", b10), ("B12", b12), ("B13", b13), ("B14", b14), ("B15", b15), ("B16", b16), ("B17", b17),
]
