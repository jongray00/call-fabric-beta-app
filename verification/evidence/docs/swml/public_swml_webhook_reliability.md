---
source: "SWML webhook reliability sources: https://signalwire.com/docs/server-sdks/guides/mapping-numbers ; https://signalwire.com/docs/server-sdks/guides/troubleshooting ; https://signalwire.com/docs/swml/reference/errors ; api_spec_signalwire_rest.json (PATCH /api/fabric/resources/swml_webhooks/{id}) ; api_fabric.json (External SWML Handlers)"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## Mapping Numbers: Fallback URL (Server SDK guide)

Configure a fallback for errors:

| Setting | Value |
|---------|-------|
| Primary URL | `https://your-server.com/agent` |
| Fallback URL | `https://backup-server.com/agent` |

**Fallback triggers on:**

- Connection timeout
- HTTP 5xx errors
- Invalid SWML response

## Troubleshooting: Timeout Issues (Server SDK guide)

**SWML Request Timeout:**

- SignalWire waits ~5 seconds for SWML
- Make sure server responds quickly

**Function Timeout:**

- SWAIG functions should complete in under 30 seconds

## SWML Errors: Document fetch / route

- `http_retrieval_error` (string): The attempt to retrieve the SWML document timed out or failed.
- `url_failed_to_parse` (string): The configured SWML URL could not be parsed.

## REST: PATCH /api/fabric/resources/swml_webhooks/{id} (Update SWML webhook)

- `primary_request_url` (string): Primary URL SignalWire fetches the SWML document from when the webhook fires. The webhook payload depends on `used_for`: for `calling`, see the SWML inbound call webhook; for `messaging`, see the SWML inbound message webhook.
- `primary_request_method`: Primary request method of the SWML Webhook.
- `fallback_request_url` (string): Fallback URL SignalWire fetches the SWML document from if the primary URL fails. Receives the same payload as `primary_request_url` [...]
- `fallback_request_method`: Fallback request method of the SWML Webhook.
- `status_callback_url` (string): URL to receive message status callback events for outbound messages sent by this webhook (`reply` or `send_sms`).

## api_fabric.json: External SWML Handlers

"invalid_http_method" is a validation error on `fallback_request_method`.
It appears on the External SWML Handlers screen (`/api/fabric/resources/external_swml_handlers`) in your SignalWire Space.
Allowed values for `fallback_request_method`: GET, POST.

## SWML webhook security guide (signed requests include fallback)

"The initial fetch, when a Resource or phone number is configured with an **External URL** rather
  than a hosted script, and the fetch from your fallback URL when the primary one fails."
