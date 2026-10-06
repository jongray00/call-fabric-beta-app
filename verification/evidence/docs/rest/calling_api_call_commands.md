---
source: api_spec_signalwire_rest.json :: POST /api/calling/calls (public ref /docs/apis/rest/calls/call-commands)
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:22:36Z
note: Verbatim excerpt of indexed OpenAPI description.
---

# POST /api/calling/calls  "Send call commands"

"Unified JSON-RPC style endpoint for executing call methods through command-based dispatch.
Send a request with the appropriate `command` field to invoke the desired call operation.
Only the commands listed below are supported. Most operate on an already-active call; `dial` creates a new one. All commands are sent over HTTP (no persistent WebSocket connection required) and return immediately; operations that continue asynchronously deliver their results to your `status_url` webhooks."

| Command | Description |
|---|---|
| `dial` | Create and initiate a new outbound call |
| `update` | Modify an active call's dialplan in real-time |
| `calling.end` | Terminate an active call immediately |
| `calling.transfer` | Transfer a call to a new SWML destination (URL or inline document) |
| `calling.disconnect` | Disconnect bridged calls without hanging up either leg |
| `calling.play` / `.pause` / `.resume` / `.stop` / `.volume` | playback |
| `calling.record` | Start recording a call |
| `calling.record.pause` | Pause active recording |
| `calling.record.resume` | Resume paused recording |
| `calling.record.stop` | Stop active recording |
| `calling.collect`, `calling.collect.stop`, `calling.collect.start_input_timers` | input |
| `calling.detect`, `calling.detect.stop` | detectors |
| `calling.tap`, `calling.tap.stop`, `calling.stream`, `calling.stream.stop` | media |
| `calling.transcribe`, `calling.transcribe.stop`, `calling.denoise`, `calling.denoise.stop` | |
| `calling.ai_hold`, `calling.ai_unhold`, `calling.ai_message`, `calling.ai.stop` | AI |
| `calling.ai_sidecar`, `.poke`, `.ask`, `.stop`, `.status` | AI sidecar |
| `calling.live_transcribe`, `calling.live_translate` | |
| `calling.send_fax.stop`, `calling.receive_fax.stop`, `calling.refer`, `calling.user_event` | |

"The API token used to authenticate must have the following scope(s) enabled to make a successful request: _Voice_."
"**Responses:** 200, 400, 401, 404, 422, 500"

## SDK REST docs (signalwire-python:rest/docs/calling.md, same text in Go/Ruby/C++/Java/Perl)
"Every method on `client.calling` sends a POST request with this structure:
{ "command": "calling.play", "id": "<call-uuid>", "params": { ... } }
For `dial` and `update`, the call details are inside `params` (no top-level `id`). For all other commands, `id` is the UUID of the call to control."

signalwire-typescript:rest/docs/calling.md: "`end` hangs up a call. The optional `reason` is one of `hangup`, `cancel`, `busy`, `noAnswer`, `decline` or `error`"
"`transfer` moves a call to a new destination: a SIP URI, a phone number or an inline SWML object."
signalwire-java:rest/docs/calling.md: `client.calling().transfer(callId, Calling.TransferRequest.builder().dest(Map.of("to", "sip:agent@example.com")).build());`
Java/Perl/Ruby/C++: dial(from, to, url) returns result with `id`; `update(id, url)` "Update an active call's dialplan mid-call."
docs:fern/.../python/rest/calling/dial.mdx: "Provide either a `url` pointing to a SWML document or an inline `swml` object to control the call flow."
docs:fern/.../python/rest/calling/record.mdx: "Pass a `control_id` to name the recording so you can pause, resume, or stop it later. The response never carries `control_id` back"; example `client.calling.record(call_id="call-id-xxx", control_id="record-1", audio={"format": "mp3", "stereo": True})`
