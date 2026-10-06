"""Thin SignalWire REST wrapper. Every endpoint and field name here is taken from evidence/docs/rest_facts.json
(see the per-method source notes). All traffic goes through LoggedClient (evidence/http.log.jsonl)."""
from __future__ import annotations

import time
import uuid

from .config import Budget, assert_dialable
from .httplog import LoggedClient


class SW:
    def __init__(self, env: dict, budget: Budget, test_ref: dict):
        self.space = env["SW_SPACE"]
        self.project = env["SW_PROJECT_ID"]
        self.http = LoggedClient(f"https://{self.space}", env["SW_PROJECT_ID"], env["SW_API_TOKEN"], test_ref)
        self.budget = budget
        self.owned: set[str] = set()
        self.created = {"subscribers": [], "resources": [], "numbers": [], "recordings": [], "calls": []}

    # ---- phone numbers (rest_facts 4) ----
    def refresh_owned(self) -> list[dict]:
        r = self.http.get("/api/relay/rest/phone_numbers", params={"page_size": 100})
        data = r.json().get("data", []) if r.status_code == 200 else []
        self.owned = {n["number"] for n in data if n.get("number")}
        return data

    def ensure_numbers(self, area_code: str, n: int = 3) -> list[dict]:
        have = self.refresh_owned()
        need = max(0, n - len(have))
        if need:
            found = self.http.get("/api/relay/rest/phone_numbers/search",
                                  params={"areacode": area_code, "number_type": "local", "max_results": need + 2}).json()
            for cand in (found.get("data") or [])[:need]:
                r = self.http.post("/api/relay/rest/phone_numbers", json={"number": cand["number"]})
                if r.status_code in (200, 201):
                    self.created["numbers"].append(r.json())
            have = self.refresh_owned()
        return have[:n]

    def route_number(self, number_id: str, swml_url: str) -> dict:
        # rest_facts 3: call_handler=relay_script + call_relay_script_url
        return self.http.put(f"/api/relay/rest/phone_numbers/{number_id}",
                             json={"call_handler": "relay_script", "call_relay_script_url": swml_url}).json()

    # ---- subscribers and tokens (rest_facts 2) ----
    def create_subscriber(self, tag: str) -> dict:
        email = f"harness-{tag}-{uuid.uuid4().hex[:6]}@example.com"
        r = self.http.post("/api/fabric/resources/subscribers", json={"email": email, "first_name": "Harness", "last_name": tag})
        j = r.json()
        j["_email"] = email
        if r.status_code in (200, 201):
            self.created["subscribers"].append(j)
        return j

    def delete_subscriber(self, sub_id: str) -> int:
        return self.http.delete(f"/api/fabric/resources/subscribers/{sub_id}").status_code

    def subscriber_address(self, sub_id: str) -> str | None:
        r = self.http.get(f"/api/fabric/resources/subscribers/{sub_id}/addresses")
        for a in (r.json().get("data") or []):
            ch = a.get("channels") or {}
            if isinstance(ch, dict) and ch.get("audio"):
                return ch["audio"].split("?")[0]
            if a.get("name") and a.get("context"):
                return f"/{a['context']}/{a['name']}"
        return None

    def mint_token(self, reference: str, ttl_s: int | None = None, fingerprint: str | None = None, scope=None) -> dict:
        body = {"reference": reference}
        if ttl_s:
            body["expire_at"] = int(time.time()) + int(ttl_s)
        if fingerprint:
            body["fingerprint"] = fingerprint
        if scope:
            body["scope"] = scope
        r = self.http.post("/api/fabric/subscribers/tokens", json=body)
        j = r.json()
        j["_status"] = r.status_code
        if body.get("expire_at"):
            j["expiry_at"] = body["expire_at"] * 1000  # SDK expects ms (sdk_facts item1)
        return j

    # ---- resources (rest_facts 3) ----
    def create_swml_webhook(self, name: str, url: str, status_url: str | None = None) -> dict:
        body = {"name": name, "used_for": "calling", "primary_request_url": url, "primary_request_method": "POST"}
        if status_url:
            body.update(status_callback_url=status_url, status_callback_method="POST")
        r = self.http.post("/api/fabric/resources/swml_webhooks", json=body)
        j = r.json()
        if r.status_code in (200, 201):
            self.created["resources"].append(j)
        return j

    def resource_addresses(self, res_id: str) -> list[dict]:
        return self.http.get(f"/api/fabric/resources/{res_id}/addresses").json().get("data", [])

    def delete_resource(self, kind: str, res_id: str) -> int:
        return self.http.delete(f"/api/fabric/resources/{kind}/{res_id}").status_code

    # ---- calling API (rest_facts 1) ----
    def command(self, command: str, call_id: str | None = None, **params) -> tuple[int, dict]:
        body = {"command": command, "params": params}
        if call_id:
            body["id"] = call_id
        r = self.http.post("/api/calling/calls", json=body)
        try:
            j = r.json()
        except Exception:
            j = {"raw": r.text}
        return r.status_code, j

    def dial(self, from_: str, to: str, swml: dict | None = None, url: str | None = None,
             status_url: str | None = None, est_seconds: int = 60) -> tuple[int, dict]:
        assert_dialable(to, self.owned)                 # rules 2 + 3, checked before every dial
        if from_ not in self.owned:
            raise ValueError(f"from {from_} not owned")
        cost = self.budget.estimate_call(est_seconds)
        if not self.budget.can_spend(cost):
            raise RuntimeError("budget cap reached")
        params = {"from": from_, "to": to}
        if swml is not None:
            params["swml"] = swml
        if url:
            params["url"] = url
        if status_url:
            params.update(status_url=status_url, status_events=["created", "ringing", "answered", "ended"])
        code, j = self.command("dial", **params)
        self.budget.charge(cost, f"dial {from_}->{to}")
        if j.get("id"):
            self.created["calls"].append(j["id"])
        return code, j

    def end(self, call_id: str, reason: str = "hangup"):
        return self.command("calling.end", call_id, reason=reason)

    def record(self, call_id: str, control_id: str, status_url: str | None = None, stereo=True, fmt="mp3", direction="both"):
        p = {"control_id": control_id, "audio": {"format": fmt, "stereo": stereo, "direction": direction, "beep": False}}
        if status_url:
            p["status_url"] = status_url
        return self.command("calling.record", call_id, **p)

    def record_pause(self, call_id, control_id, behavior=None):
        p = {"control_id": control_id}
        if behavior:
            p["behavior"] = behavior
        return self.command("calling.record.pause", call_id, **p)

    def record_resume(self, call_id, control_id):
        return self.command("calling.record.resume", call_id, control_id=control_id)

    def record_stop(self, call_id, control_id):
        return self.command("calling.record.stop", call_id, control_id=control_id)

    def transfer(self, call_id, dest):
        return self.command("calling.transfer", call_id, dest=dest)

    # ---- recordings and logs (rest_facts 5, 6) ----
    def list_recordings(self) -> list[dict]:
        return self.http.get("/api/relay/rest/recordings", params={"page_size": 100}).json().get("data", [])

    def delete_recording(self, rec_id: str) -> int:
        return self.http.delete(f"/api/relay/rest/recordings/{rec_id}").status_code

    def voice_logs(self, created_after: str) -> list[dict]:
        out, params = [], {"created_after": created_after, "page_size": 1000}
        r = self.http.get("/api/voice/logs", params=params).json()
        out += r.get("data", [])
        return out
