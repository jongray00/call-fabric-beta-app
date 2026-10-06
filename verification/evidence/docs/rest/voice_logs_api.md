---
source: api_spec_signalwire_rest.json :: Voice Logs; SDK ref logs
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:46Z
note: Response schema fields (charge, charge_details) NOT present in indexed text
---

# GET /api/voice/logs "List voice logs"
"Lists historical voice activity in the project across supported call types. Use it for usage reporting, billing review, and troubleshooting, not live call control."
Params: include_deleted, created_before, created_on, created_after, page_number ("Requires `page_token` for values greater than 0"), page_size ("default page size is `50` and the maximum is `1000`"), page_token. Responses: 200, 400, 401, 422, 500
# GET /api/voice/logs/{id} "Get voice log": "`id` ... This is the segment_id you can find in Relay call details in your Dashboard UI or in return objects when using the SDK."
# GET /api/voice/logs/{id}/events "List voice log events": "Returns the recorded event timeline for one historical voice log."
# Python SDK example: `calls = client.logs.voice.list(page_size=20)` then `call.get("from"), call.get("to"), call.get("duration")` from `calls.get("data", [])`
# Conference logs: client.logs.conferences.list() ("Conference logs only support `list()`")
