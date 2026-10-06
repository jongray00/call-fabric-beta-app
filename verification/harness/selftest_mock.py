"""Dry-run of the live test plumbing against a fake SignalWire + fake devices. Proves the harness logic
(inbound flow, webhook capture, ring detection, run summarizing, guards). Says nothing about SignalWire."""
import json
import sys
import threading
import time

import httpx

from . import tests as T
from .backend import STATE, serve
from .config import EVIDENCE, Budget, DialRefused, assert_dialable

BASE = "http://127.0.0.1:8001"


class FakeSW:
    def __init__(self):
        self.owned = {"+15615550001", "+15615550002", "+15615550003"}
        self.created = {"subscribers": [], "resources": [], "numbers": [], "recordings": [], "calls": []}
        self.budget = Budget(25)
        self.ended = []
        self.devs = None

    def create_subscriber(self, tag):
        return {"id": f"id-{tag}", "_email": f"{tag}@example.com"}

    def subscriber_address(self, sid):
        return f"/private/{sid}"

    def dial(self, from_, to, swml=None, url=None, status_url=None, est_seconds=60):
        assert_dialable(to, self.owned)
        cid = f"aleg-{time.time()}"
        def platform():  # what SignalWire would do: fetch the inbound SWML for number B
            httpx.post(f"{BASE}/swml/inbound", json={"call": {"call_id": "anchor-1", "from": from_, "to": to, "type": "phone"}, "params": {}})
        threading.Thread(target=platform).start()
        for d in (self.devs.registered if self.devs and self.devs.ring else []):
            threading.Timer(0.5, lambda d=d: httpx.post(f"{BASE}/events", json={"device": d, "type": "status", "value": "ringing", "call_id": "c1"})).start()
        return 200, {"id": cid}

    def end(self, cid, reason="hangup"):
        self.ended.append(cid)
        return 200, {}


class FakeDevices:
    def __init__(self, ring=True):
        self.ring = ring
        self.registered = []

    def open(self, d):
        return {"ok": True}

    def call(self, d, fn, *a):
        if fn == "register":
            httpx.post(f"{BASE}/events", json={"device": d, "type": "registered", "value": True})
            self.registered.append(d)
        return {"ok": True}

    def close(self, d):
        if d in self.registered:
            self.registered.remove(d)


def main():
    serve(8001)
    nums = [{"number": n} for n in ("+15615550001", "+15615550002", "+15615550003")]
    sw, dv = FakeSW(), FakeDevices()
    sw.devs = dv
    ctx = T.Ctx(sw, dv, BASE, nums, Budget(25))
    T.RUNS = 3
    a1 = T.repeat(ctx, "MOCK_A1", T.a1)
    a4 = T.repeat(ctx, "MOCK_A4", T.a4)
    try:
        assert_dialable("911", ctx.sw.owned); guard911 = False
    except DialRefused:
        guard911 = True
    try:
        assert_dialable("+12125550100", ctx.sw.owned); guard_unowned = False
    except DialRefused:
        guard_unowned = True
    checks = {
        "a1_confirmed_with_ringing_devices": a1["status"] == "CONFIRMED" and len(a1["runs"]) == 3,
        "a4_captured_call_fields": a4["status"] == "CONFIRMED" and "call_id" in a4["runs"][0]["observed"]["call_keys"],
        "anchor_id_extracted": a1["runs"][0]["observed"]["anchor"] == "anchor-1",
        "hangup_sent_to_anchor": "anchor-1" in ctx.sw.ended,
        "denylist_blocks_911": guard911,
        "unowned_number_blocked": guard_unowned,
    }
    sw2, dv2 = FakeSW(), FakeDevices(ring=False)
    sw2.devs = dv2
    ctx2 = T.Ctx(sw2, dv2, BASE, nums, Budget(25))
    T.RING_WAIT = 2
    a1n = T.repeat(ctx2, "MOCK_A1_noring", T.a1)
    checks["a1_refuted_when_no_ringing"] = a1n["status"] == "REFUTED"
    out = EVIDENCE / "selftest" / "mock"
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps({"checks": checks, "a1": a1, "a4": a4}, indent=2, default=str))
    print(json.dumps(checks))
    sys.exit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
