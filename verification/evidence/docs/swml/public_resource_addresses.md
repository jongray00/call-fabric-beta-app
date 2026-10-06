---
source: "https://signalwire.com/docs/platform/glossary (Resource Address); Browser SDK migration doc (signalwire-typescript-web:docs/draft-migration-from-v3.md); Relay connect reference (docs/server-sdks/reference/typescript/relay/call/connect)"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## Glossary: Resource Address [#resource-address]

The path that reaches a Resource, in the form `/context/name`. Every Project starts with a `public` and a `private` context, and you can add named contexts of either access type from the Dashboard. The name defaults to the Resource's name in lowercase. An AI agent named `Sigmond` in the public context is reachable at `/public/sigmond`.

Addresses are mutable and a Resource can have several, including phone numbers and SIP URIs. When you're addressing a Resource from within its own context, you can omit the context: a Subscriber named `Bob` in the `private` context is reachable at `/private/bob`, or, from within that context, just `/bob`.

The REST API reference calls it a **Fabric Address**.

## SWML connect destination forms (connect page)

`serial_parallel[][].to` (string, required): Destination to dial. Can be: - Phone number in E.164 format (e.g., `+15552345678`) - SIP URI (e.g., `sip:alice@example.com`) - Resource Address (e.g., `/public/test_room`) - Queue (e.g., `queue:support`) - WebSocket stream (e.g., `stream:wss://example.com/audio`)

## RELAY connect (TypeScript Server SDK reference)

`devices` [...] Each device object contains: - `"type"` -- Device type (`"phone"`, `"sip"`, or `"fabric"` for a resource address) - `"params"` -- Type-specific parameters (`to_number` and `from_number` for phone; `to` plus optional `from` and `timeout` for fabric)

## Browser SDK migration from v3

```javascript
// Or still use URI strings
const call = await client.dial('/private/user1');
```
