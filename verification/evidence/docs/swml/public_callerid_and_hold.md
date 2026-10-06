---
source: "Caller ID and hold sources: https://signalwire.com/docs/swml/guides/forward-calls ; https://signalwire.com/docs/platform/voice/how-to-set-caller-id-or-cnam ; https://signalwire.com/docs/server-sdks/reference/typescript/relay/call/hold ; https://signalwire.com/docs/server-sdks/guides/call-transfer ; Browser SDK example signalwire-typescript-web:examples/06-call-controls"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## Forwarding calls (SWML guide)

```yaml
version: 1.0.0
sections:
  main:
    - connect:
        from: "%{call.from}"
        to: "+15551234567"
```

This Script will handle the call by making an outbound dial, setting the `from` address to be the address which created the initial call,
and then forwarding that call to the number specified in the `to` field.
[...] Notice how we used its `from` parameter to ensure that the number of the original caller
(stored in the `call.from` variable) is maintained as caller ID for the forwarded call.

## Caller ID & CNAM: Set caller ID for SIP credentials

- **Calling another SIP endpoint** — set the **Caller ID** field. This is the only way to display caller ID on SIP-to-SIP calls.
- **Calling a PSTN number** — set the **Send As** field to a purchased or verified number. If unset, the default behavior is to use a random number from your account.

## Call Transfer (Server SDK guide): Connect Method Parameters

| `from_addr` | str | None | Override caller ID for outbound leg |

## RELAY call.hold (TypeScript Server SDK reference)

Put the call on hold. The remote party hears hold music or silence while the
call is held.
Use `unhold()` to release the call from hold.
This method emits `calling.call.hold` events.

## Browser SDK example 06-call-controls

```javascript
    /**
     * Toggle call hold.
     */
    async function toggleHold(call) {
      await call.toggleHold();
    }
```
(No statement in this example about what the remote party hears.)

