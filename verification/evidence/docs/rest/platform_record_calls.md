---
source: https://signalwire.com/docs/platform/voice/record-calls (docs:fern/products/platform/pages/calling/voice/record-calls.mdx)
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:22:36Z
note: Multiple sections retrieved via separate searches
---

## Prepare for call recording
"Your Project ID and API token from the Dashboard's API credentials page. Enable the token's **Voice** permission for the Calling API."
"| `<YOUR_CALL_ID>` | The `id` of the live call you're sending a REST command to |"

## Pause and resume a recording
"Pausing and resuming act on a live call, so they come from a Relay call handler or the REST Calling API, not from SWML. Pausing takes an optional `behavior`. The default, `skip`, leaves the paused span out of the file entirely; `silence` replaces it with silence, so the recording's timing still lines up with the call."

```bash
curl -X POST "https://<YOUR_SPACE>.signalwire.com/api/calling/calls" \
  -u "<YOUR_PROJECT_ID>:<YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "calling.record.pause",
    "id": "<YOUR_CALL_ID>",
    "params": { "control_id": "main", "behavior": "skip" }
  }'

curl -X POST "https://<YOUR_SPACE>.signalwire.com/api/calling/calls" \
  -u "<YOUR_PROJECT_ID>:<YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "calling.record.resume",
    "id": "<YOUR_CALL_ID>",
    "params": { "control_id": "main" }
  }'
```

## Stop recording the call
"A background recording ends on hangup automatically. ... send `calling.record.stop` through the REST Calling API's call commands against any live call."

## Record the whole call via WebSocket (Relay) (2)
"The recording's URL is available as soon as it starts ... If you set a `status_url`, SignalWire also sends status callbacks as the recording changes state."

## View recordings from your dashboard
"Recordings appear under **Storage** > **Recordings** in your SignalWire Space." "A call's recordings are also listed on its log. Open **Logs** > **Voice**"
