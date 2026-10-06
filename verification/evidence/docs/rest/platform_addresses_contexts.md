---
source: https://signalwire.com/docs/platform/addresses (docs:fern/products/platform/pages/platform/call-fabric/addresses.mdx)
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:11Z
note: Contexts section
---

"An alias lives in a context, and the context's access type decides who can reach it. `public` and `private` are built in and can't be changed:
- **`public`** Addresses are reachable by anyone, including unauthenticated callers. Use them for entry points such as a support agent behind a click-to-call button.
- **`private`** Addresses are reachable only by authenticated users, which makes them the home of Subscribers and anything only your own users should dial.
A SIP Address's domain is a context too, and phone numbers sit in the `external` context."
"**Tip:** Only a call placed by an authenticated Subscriber can omit the context: a Subscriber in `private` reaches `/private/bob` as `/bob`. REST dials and SWML `connect` need the full `/<context>/<name>`."

Browser SDK migration doc (signalwire-typescript-web:docs/draft-migration-from-v2.md): `'/pstn/+15551234567'`, `'/sip/user@domain'`, `'/private/resource-name'`, `'/public/room-name'`
