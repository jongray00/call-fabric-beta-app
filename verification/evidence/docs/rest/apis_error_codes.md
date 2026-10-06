---
source: https://signalwire.com/docs/apis/error-codes (docs:fern/products/apis/pages/core/error-codes.mdx) + TS SDK RestError
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:22:36Z
note: 
---

"- `400 Bad Request` — the request was malformed (bad JSON, missing required fields).
- `401 Unauthorized` — credentials missing or invalid.
- `403 Forbidden` — your token lacks the required scope.
- `404 Not Found` — the resource doesn't exist, or doesn't belong to your project.
- `422 Unprocessable Entity` — the request was well-formed but failed validation. The body contains an `errors` array with specifics.
- `429 Too Many Requests` — you've exceeded a rate limit. Back off and retry.
- `500 Internal Server Error` — an unexpected server-side failure."

TS SDK RestError: "`body`: ... A `SignalWireErrorBody` object (`code`, `message`, and optional `more_info` and `status`) when the response was valid JSON"
