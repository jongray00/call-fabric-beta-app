"""HTTP client wrapper that logs every request/response to evidence/http.log.jsonl with the token redacted."""
from __future__ import annotations

import base64
import json
import threading
import time

import httpx

from .config import EVIDENCE

_lock = threading.Lock()
LOG = EVIDENCE / "http.log.jsonl"


def _redact(s: str, secrets: list[str]) -> str:
    for sec in secrets:
        if sec:
            s = s.replace(sec, "<REDACTED>")
    return s


class LoggedClient:
    def __init__(self, base_url: str, project_id: str, token: str, test_id_ref: dict | None = None):
        self.secrets = [token, base64.b64encode(f"{project_id}:{token}".encode()).decode()]
        self.client = httpx.Client(base_url=base_url, auth=(project_id, token), timeout=30)
        self.test_id_ref = test_id_ref if test_id_ref is not None else {"id": "setup"}

    def request(self, method: str, url: str, **kw) -> httpx.Response:
        t0 = time.time()
        err = None
        resp = None
        try:
            resp = self.client.request(method, url, **kw)
        except Exception as e:  # logged then re-raised
            err = repr(e)
        rec = {
            "t": t0, "test_id": self.test_id_ref.get("id"), "method": method,
            "url": str(self.client.base_url) + url if not url.startswith("http") else url,
            "request_body": kw.get("json") if "json" in kw else kw.get("data"),
            "params": kw.get("params"),
            "status": resp.status_code if resp is not None else None,
            "elapsed_ms": round((time.time() - t0) * 1000),
            "response_body": (resp.text[:20000] if resp is not None else None),
            "error": err,
        }
        line = _redact(json.dumps(rec, default=str), self.secrets)
        with _lock:
            LOG.parent.mkdir(parents=True, exist_ok=True)
            with LOG.open("a") as f:
                f.write(line + "\n")
        if err:
            raise RuntimeError(err)
        return resp

    def get(self, url, **kw):
        return self.request("GET", url, **kw)

    def post(self, url, **kw):
        return self.request("POST", url, **kw)

    def put(self, url, **kw):
        return self.request("PUT", url, **kw)

    def patch(self, url, **kw):
        return self.request("PATCH", url, **kw)

    def delete(self, url, **kw):
        return self.request("DELETE", url, **kw)
