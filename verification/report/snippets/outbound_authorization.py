"""Outbound authorization webhook (FastAPI). Proof status: served by the harness backend in the local self-test;
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
