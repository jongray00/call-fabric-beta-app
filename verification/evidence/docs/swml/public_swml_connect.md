---
source: "https://signalwire.com/docs/swml/reference/calling/connect (docs:fern/products/swml/pages/reference/methods/calling/connect/index.mdx)"
retrieved_via: "mcp__SignalWire_Knowledge__search, several queries"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## Variables

Set by the method:

- **connect_result:** (out) `connected` | `failed`.
- **connect_failed_reason:** (out) Detailed reason for failure.
- **return_value:** (out) Same value as `connect_result`.

## Properties (chunk "Example (2)")

- `connect.answer_on_bridge` (boolean): Delay answer until the B-leg answers.
- `connect.call_state_events` (string[]): An array of call state event names to be notified about. Allowed event names are `created`, `ringing`, `answered`, and `ended`. Can be overwritten on each destination.
- `connect.call_state_url` (string): Webhook url to send call status change notifications to for all legs. Can be overwritten on each destination. Authentication can also be set in the url in the format of `username:password@url`. Learn more about status callbacks.
- `connect.codecs` (string): Comma-separated string of codecs to offer. Has no effect on calls to phone numbers.
- `connect.confirm` (string | object[]): Confirmation to execute when the call is connected. Can be either: - A URL (string) that returns a SWML document - An array of SWML methods to execute inline
- `connect.confirm_timeout` (integer): The amount of time, in seconds, to wait for the `confirm` script to execute.
- `connect.encryption` (string): The encryption method to use for the call. Possible values: `mandatory`, `optional`, `forbidden`.
- `connect.from` (string): Caller ID number. Optional. Can be overwritten on each destination.
- `connect.from_name` (string): The caller ID name shown to the person you're calling, displayed alongside the `from` number (sometimes called CNAM). Applies to SIP calls only — it has no effect on calls to phone numbers. Can be overridden on each destination.
- `connect.headers` (object[]): Custom SIP headers to add to INVITE. Has no effect on calls to phone numbers.
- `headers[].name` (string, required): The name of the header.
- `headers[].value` (string, required): The value of the header.
- `connect.max_duration` (integer): Maximum duration, in seconds, allowed for the call.
- `connect.result` (object | object[]): Action to take based on the result of the call. This will run once the peer leg of the call has ended. Will use the [`switch properties`](/docs/swml/reference/calling/switch#properties) when the `return_value` is a object, and will use the [`cond properties`](/docs/swml/reference/calling/cond#properties) method when the `return_value` is an array. See [Variables](#variables) for details.
- `connect.ringback` (string[]): Array of `play` URIs to play as ringback tone.
- `connect.session_timeout` (integer): Time, in seconds, to set the SIP `Session-Expires` header in INVITE. Must be a positive, non-zero number. Has no effect on calls to phone numbers.

## Properties (chunk "Example (3)")

- `connect.status_url` (string): Webhook URL to deliver status events. Reports the connect operation status (connecting, connected, failed, disconnected). See [Connect Status Callbacks](#connect-status-callbacks).
- `connect.timeout` (integer): Maximum time, in seconds, to wait for an answer.
- `connect.webrtc_media` (boolean): If true, WebRTC media is offered to the SIP endpoint. Has no effect on calls to phone numbers.

## serial_parallel and destination forms (chunk "Example")

Combine both strategies. The outer array is the **serial** dimension — groups are tried one at a time, in order. Each inner array is the **parallel** dimension — all destinations in that group are dialed simultaneously. If no destination answers in the first group, the next group is attempted.

- `connect.serial_parallel` (object[][], required): Array of arrays combining both strategies. [...]
- `serial_parallel[][].to` (string, required): Destination to dial. Can be: - Phone number in E.164 format (e.g., `+15552345678`) - [SIP URI](/docs/platform/voice/sip) (e.g., `sip:alice@example.com`) - [Resource Address](/docs/platform/addresses) (e.g., `/public/test_room`) - Queue (e.g., `queue:support`) - WebSocket stream (e.g., `stream:wss://example.com/audio`)
- `serial_parallel[][].from` (string): Caller ID number. Overrides the top-level `from`.
- `serial_parallel[][].from_name` (string): The caller ID name shown to this destination. Overrides the top-level `from_name`. Applies to SIP calls only.
- `serial_parallel[][].username` (string): SIP authentication username (`sip_auth_username`) for this destination. **Only applies to SIP URI targets.**

## StatusCallbacks (call_state_url)

A POST request will be sent to `call_state_url` with a JSON payload when the call state changes.
Only events listed in `call_state_events` will be sent (default: `ended`).

- `event_type` (string): The type of event. Always `calling.call.state` for this method.
- `event_channel` (string): The channel for the event, includes the SWML session ID.
- `timestamp` (number): Unix timestamp (float) when the event was generated.
- `project_id` (string): The project ID associated with the call.
- `space_id` (string): The Space ID associated with the call.
- `params` (object): An object containing call state parameters.
- `params.call_id` (string): The call ID.
- `params.node_id` (string): The node handling the call.
- `params.call_state` (string): The current call state. **Valid values:** `created`, `ringing`, `answered`, `ended`.
- `params.direction` (string): The direction of the call leg (e.g., `outbound`).
- `params.device` (object): Details about the device involved in the call.
- `device.type` (string): The type of device (e.g., `phone`, `sip`).
- `device.params.from_number` (string): The originating phone number.
- `device.params.to_number` (string): The destination phone number.
- `params.end_reason` (string): The reason the call ended (only present when `call_state` is `ended`). **Valid values:** `hangup`, `busy`, `no_answer`, `cancel`, `declined`, `error`.

## Connect Status Callbacks (status_url)

When you provide a top-level `status_url`, SignalWire sends HTTP POST requests reporting the overall status of the connect operation.

- `event_type` (string): The type of event. Always `calling.call.connect` for connect status events.
- `event_channel` (string): The channel for the event, includes the SWML session ID.
- `timestamp` (number): Unix timestamp (float) when the event was generated.
- `project_id` (string): The project ID associated with the call.
- `space_id` (string): The Space ID associated with the call.
- `params` (object): An object containing connect status parameters.
- `params.call_id` (string): The call ID.
- `params.node_id` (string): The node handling the call.
- `params.segment_id` (string): The segment ID for the call leg. Present when a segment ID has been assigned.
- `params.tag` (string): The tag associated with the call. Present when a tag has been set.
- `params.connect_state` (string): The current connect state. Possible values: - `connecting` — Attempting to connect - `connected` — Successfully connected - `failed` — Connection failed - `disconnected` — Connection ended
- `params.failed_reason` (string): The reason the connection failed. Only present when `connect_state` is `failed`.
- `params.peer` (object): Details about the connected peer. Present when `connect_state` is `connected`.
- `peer.call_id` (string): The peer's call ID.
- `peer.tag` (string): The tag associated with the peer call. Present when a tag has been set on the peer.
- `peer.node_id` (string): The node ID of the node handling this call.
- `peer.queue_id` (string): The queue ID when the peer was connected via a queue. Only present for queue-based connections.
- `peer.queue_name` (string): The queue name when the peer was connected via a queue. Only present for queue-based connections.
- `peer.device` (object): Details about the peer's device.

## Stream-specific properties

The following properties apply only when `to` starts with `stream:wss://`.
- `connect.authorization_bearer_token`, `connect.codec`, `connect.custom_parameters`, `connect.name`, `connect.realtime` (see source).

## Example (serial SIP)

```yaml
version: 1.0.0
sections:
  main:
    - connect:
        from: "+15551112222"
        serial:
          - to: "sip:primary@example.com"
            username: "primary_user"
            password: "primary_pw"
          - to: "sip:backup@example.com"
            username: "backup_user"
            password: "backup_pw"
```
