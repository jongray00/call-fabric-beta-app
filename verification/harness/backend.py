"""FastAPI webhook backend. Runs in-process (uvicorn thread) so the runner shares STATE directly.

Endpoints
  POST|GET /swml/{name}     serve the SWML configured for `name`, persist the request
  POST     /hook/{name}     status callbacks (connect, recording, call state), persist
  POST     /events          browser device events
  GET      /token           mint a Subscriber token through the configured minter
  GET      /static/{file}   audio fixtures and the browser page + SDK bundle
"""
from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

from .config import EVIDENCE, ROOT

app = FastAPI()


class State:
    def __init__(self):
        self.test_id = "setup"
        self.swml: dict[str, dict] = {}          # name -> SWML document (dict) or callable(body)->dict
        self.behavior: dict[str, dict] = {}      # name -> {"delay": s, "status": code}
        self.webhooks: list[dict] = []
        self.events: list[dict] = []
        self.token_minter = None                 # callable(subscriber_ref, ttl) -> dict
        self.lock = threading.Lock()
        self.static_dir = ROOT / "evidence" / "fixtures"
        self.browser_dir = ROOT / "harness" / "browser"

    def _persist(self, kind: str, rec: dict) -> None:
        d = EVIDENCE / kind / self.test_id
        d.mkdir(parents=True, exist_ok=True)
        with (d / f"{kind}.jsonl").open("a") as f:
            f.write(json.dumps(rec, default=str) + "\n")

    def wait_for(self, pred, timeout: float, src: str = "events") -> dict | None:
        end = time.time() + timeout
        while time.time() < end:
            with self.lock:
                for e in getattr(self, src):
                    if pred(e):
                        return e
            time.sleep(0.05)
        return None


STATE = State()


async def _capture(req: Request, name: str) -> dict:
    raw = await req.body()
    try:
        body = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        body = dict((await req.form()).items()) if raw else None
    rec = {"t": time.time(), "test_id": STATE.test_id, "name": name, "method": req.method,
           "url": str(req.url), "headers": dict(req.headers), "query": dict(req.query_params),
           "raw_body": raw.decode("utf-8", "replace"), "body": body}
    with STATE.lock:
        STATE.webhooks.append(rec)
    STATE._persist("webhooks", rec)
    return rec


@app.api_route("/swml/{name}", methods=["GET", "POST"])
async def swml(name: str, req: Request):
    rec = await _capture(req, f"swml:{name}")
    beh = STATE.behavior.get(name, {})
    if beh.get("delay"):
        await asyncio.sleep(beh["delay"])
    if beh.get("status"):
        return PlainTextResponse("forced error", status_code=beh["status"])
    doc = STATE.swml.get(name)
    if callable(doc):
        doc = doc(rec["body"] or {})
    if doc is None:
        return JSONResponse({"version": "1.0.0", "sections": {"main": [{"hangup": {}}]}})
    return JSONResponse(doc)


@app.api_route("/hook/{name}", methods=["GET", "POST"])
async def hook(name: str, req: Request):
    await _capture(req, f"hook:{name}")
    beh = STATE.behavior.get(f"hook:{name}", {})
    if beh.get("delay"):
        await asyncio.sleep(beh["delay"])
    if beh.get("status"):
        return PlainTextResponse("forced error", status_code=beh["status"])
    return PlainTextResponse("ok")


@app.post("/events")
async def events(req: Request):
    e = await req.json()
    e["rx_t"] = time.time()
    e["test_id"] = STATE.test_id
    with STATE.lock:
        STATE.events.append(e)
    STATE._persist("browser", e)
    return {"ok": True}


@app.get("/token")
async def token(ref: str, ttl: int | None = None):
    if not STATE.token_minter:
        return JSONResponse({"error": "no minter configured"}, status_code=503)
    beh = STATE.behavior.get("token", {})
    if beh.get("status"):
        return JSONResponse({"error": "forced refresh failure"}, status_code=beh["status"])
    return STATE.token_minter(ref, ttl)


@app.get("/static/{fname}")
async def static(fname: str):
    for d in (STATE.static_dir, STATE.browser_dir):
        p = (d / fname).resolve()
        if p.parent == d.resolve() and p.exists():
            return FileResponse(p)
    return PlainTextResponse("not found", status_code=404)


def serve(port: int = 8000) -> threading.Thread:
    cfg = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(cfg)
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    th.server = server  # type: ignore[attr-defined]
    return th
