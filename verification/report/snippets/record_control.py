"""Calling API recording control and hangup. Commands: evidence/docs/rest/calling_api_call_commands.md.
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
