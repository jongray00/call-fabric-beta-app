---
source: https://signalwire.com/docs/platform/voice/make-and-receive-calls (docs:fern/products/platform/pages/calling/voice/make-and-receive-calls.mdx)
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:22:36Z
note: Section 'Track a call via SWML'
---

"To follow an outbound call, add `status_url` and `status_events` to the `dial` request ... SignalWire sends an HTTP POST to `status_url` as the call reaches each state you list: `created`, `ringing`, `answered`, or `ended`. Without `status_events`, you get `ended` only."

```bash
curl -X POST "https://<YOUR_SPACE>.signalwire.com/api/calling/calls" \
  -u "<YOUR_PROJECT_ID>:<YOUR_API_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "dial",
    "params": {
      "from": "<YOUR_CALLER_ID>",
      "to": "<YOUR_DESTINATION>",
      "swml": {
        "version": "1.0.0",
        "sections": {
          "main": [{ "play": {"url": "say:Hello, welcome to SignalWire!"} }]
        }
      },
      "status_url": "<YOUR_STATUS_WEBHOOK_URL>",
      "status_events": ["ringing", "answered", "ended"]
    }
  }'
```
Diagram text: "SignalWire returns the call id with status queued and rings the destination and reports status ringing."
