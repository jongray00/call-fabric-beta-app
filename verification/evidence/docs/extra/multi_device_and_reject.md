---
fetched_at: 2026-10-06T15:31:04Z
tool: mcp__SignalWire_Knowledge__search (vector collection signalwire_unified_v3)
queries: ["subscriber registered on multiple devices incoming call rings all devices browser SDK", "reject incoming call decline subscriber other devices stop ringing"]
---

## https://signalwire.com/docs/server-sdks/reference/typescript/relay/client/dial
> `"fabric"` -- a resource address. The platform resolves the address to whatever it points to, such as a subscriber or a Relay application, and rings every live registration of a subscriber at once.
> `devices[][].params.from` (string): Caller ID shown to the destination (for `"fabric"`).

## https://signalwire.com/docs/browser-sdk/guides/inbound-calls
> Subscribe to `client.session.incomingCalls$`. The stream emits the **current list** of inbound calls every time it changes, not one event per call
> | `from` | The caller's address (e.g. `/private/alice`) |
> | `fromName` | Display name, if the caller supplied one |
> The SDK hands you the raw list. It doesn't queue, dedupe, or pick a call for you. Two simultaneous callers land in the same emission
> **Decline the call.** `reject()` declines before any media negotiates; the caller sees a normal decline; the session never picks up

## https://signalwire.com/docs/browser-sdk/reference/webrtc-call/reject
> Declines an inbound call before it is answered. The caller-side rings stop, no media is negotiated, and the call instance transitions to `disconnected`.

## https://signalwire.com/docs/platform/voice/make-and-receive-calls
> Awaiting `register()` signs the page in and marks the Subscriber online ... calls ring only while it's online.

## https://signalwire.com/docs/server-sdks/reference/typescript/relay/events (CallStateEvent.endReason)
> "hangup", "cancel", "busy", "noAnswer", "decline", "error", "abandoned", "max_duration", "not_found"

Not found in public docs searched: the effect of reject() on other devices of the same Subscriber or on other parallel destinations; a maximum number of devices per Subscriber.
