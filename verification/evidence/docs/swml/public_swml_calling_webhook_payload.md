---
source: "https://signalwire.com/docs/swml/reference/calling (docs:fern/products/swml/pages/reference/methods/calling/overview.mdx) + https://signalwire.com/docs/swml/ (get-started/index.mdx)"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## Webhook and variable payload [#webhook-payload]

When SignalWire fetches a Calling SWML document from an external URL, it POSTs this payload to
your server — on the initial inbound fetch and on every fetch triggered by a method that hits
an external URL (`execute` with a remote URL,
[`transfer`](/docs/swml/reference/calling/transfer),
[`join_conference.wait_url`](/docs/swml/reference/calling/join-conference#properties),
[`enter_queue.wait_url`](/docs/swml/reference/calling/enter-queue#properties), and
[`connect.confirm`](/docs/swml/reference/calling/connect#properties)). Your server must respond
with a valid SWML document using one of these content types: `application/json`,
`application/yaml`, or `text/x-yaml`.

Inside the executing document, the `call`, `params`, and `envs` fields are available for
variable expansion via `${...}` (JavaScript expressions) and `%{...}` (path substitution). As
the script runs, methods also populate the **`vars.*` runtime scope** — those values are not in
the initial inbound payload, but they are propagated across `transfer` boundaries and delivered
on subsequent fetches.

See the [SWML inbound call webhook reference](/docs/apis/rest/webhooks/inbound-call-webhook) for the complete request schema. The fields used by SWML are documented below.

- `call` (object): Information about the current call. Call-specific and read-only. Each call leg (A-leg, B-leg) has its own unique `call` object with different `call_id`, `from`, `to`, etc. When connecting to a new leg, the `call` object is re-initialized with the new leg's data.
  - `call.call_id` (string): A unique identifier for the call.
  - `call.call_state` (string): The current state of the call.
  - `call.direction` (string): The direction of this call. Possible values: `inbound`, `outbound`.
  - `call.from` (string): The number/URI that initiated this call.
  - `call.headers` (object[]): The headers associated with this call.
    - `call.headers[].name` (string): The name of the header.
    - `call.headers[].value` (string): The value of the header.
  - `call.node_id` (string): A unique identifier for the node handling the call.
  - `call.project_id` (string): The Project ID this call belongs to.
  - `call.segment_id` (string): A unique identifier for the current call segment.
  - `call.space_id` (string): The Space ID this call belongs to.
  - `call.to` (string): The number/URI of the destination of this call.

## Webhook and variable payload (2)

- `call.type` (string): The type of call. Possible values: `sip`, `phone`, `webrtc`.
  - `call.sip_data` (object): SIP-specific data for SIP calls. Only present when `call.type` is `sip`. Contains detailed SIP header information.
    - `call.sip_data.sip_contact_host`, `sip_contact_params`, `sip_contact_port`, `sip_contact_uri`, `sip_contact_user`, `sip_from_host`, `sip_from_uri`, `sip_from_user`, `sip_req_host`, `sip_req_uri`, `sip_req_user`, `sip_to_host`, `sip_to_uri`, `sip_to_user`
- `params` (object): Parameters passed by the calling [`execute`](/docs/swml/reference/calling/execute) or [`transfer`](/docs/swml/reference/calling/transfer) step. Empty `{}` on the initial inbound fetch. Section-scoped — each `execute`/`transfer` replaces (does not merge with) the caller's `params`; when an `execute` returns, the caller's original `params` are restored.
- `vars` (object): Runtime variable scope, populated by methods as the script executes. **Not part of the initial inbound payload** — values appear here only after a method that sets them has run. The full `vars` object is propagated across `transfer` boundaries (and on remote-URL `execute`) and delivered as a top-level `vars` field on subsequent webhook payloads. [...] Connecting to a new call leg resets the `vars` object to an empty state. **Access:** Variables can be accessed with or without the `vars.` prefix. When you reference a variable without a scope prefix (e.g., `${my_variable}`), SWML first checks `vars`. If not found in `vars`, it automatically falls back to `envs`.

## From https://signalwire.com/docs/swml/ (Document-fetching webhook)

When SignalWire fetches a SWML script from an external URL, it sends a POST request whose payload
shape depends on the document type [...]
Your server must respond with a valid SWML document using one of these content types:
`application/json`, `application/yaml`, or `text/x-yaml`.

## From https://signalwire.com/docs/platform/voice/make-and-receive-calls

For an inbound call, the request SignalWire sends your server carries the call in its `call`
object: `from`, `to`, `direction`, and `call_id` (see the
webhook payload reference). The same fields are available inside any SWML
document as variables.

## Older internal example payload (mcp get_swml reference, "Document fetching")

```json
{
  "call": {
    "project_id": "project uuid",
    "space_id": "space_uuid",
    "call_id": "uuid",
    "state": "created",
    "type": "sip",
    "from": "sip:+15551231234@example.com",
    "to": "sip:+15553214321@example.com",
    "headers": [
      { "name": "X-Header-1", "value": "X-Header-1-Value" },
      { "name": "X-Header-2", "value": "X-Header-2-Value" }
    ]
  },
  "vars": {
    "customer_script_var_1": "customer_script_var_1_value",
    "customer_script_var_2": "customer_script_var_2_value"
  },
  "params": {
    "param_1": "param_1_value",
    "param_2": "param_2_value"
  }
}
```
