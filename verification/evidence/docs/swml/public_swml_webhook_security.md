---
source: "https://signalwire.com/docs/swml/guides/webhook-security (docs:fern/products/swml/pages/guides/basics/webhook-security.mdx); also https://signalwire.com/docs/swml/guides/remote-server"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

# Verify SWML request signatures

When you serve SWML from your own web server, anyone who learns your endpoint URL can POST to it
and read back the SWML document you return. [...]

To let you check the caller, SignalWire signs every request for a SWML document with an HMAC
signature derived from your project's signing key. Verifying that signature proves the request came
from SignalWire and that neither the URL nor the body was altered in transit.

## Which requests are signed

Every POST SignalWire makes to fetch a SWML document from a URL you control is signed. That
includes:

- The initial fetch, when a Resource or phone number is configured with an **External URL** rather
  than a hosted script, and the fetch from your fallback URL when the primary one fails.
- Every subsequent fetch caused by [`execute`](/docs/swml/reference/calling/execute) or
  [`transfer`](/docs/swml/reference/calling/transfer) pointing at an external URL.
- The same fetches on the messaging side, when a number handles inbound SMS and MMS with
  [Messaging SWML](/docs/swml/reference/messaging).

Requests during a call carry two headers. Requests for a messaging document carry the SHA-1 header
alone, so verify that one if your endpoint serves both.

| Header | Algorithm | Sent on |
| :--- | :--- | :--- |
| `X-Signalwire-Signature` | HMAC-SHA1, hex encoded | Every signed request |
| `X-Signalwire-SHA256-Signature` | HMAC-SHA256, hex encoded | Call requests |

Both are computed over the same string: the request URL concatenated directly with the raw request
body, with no separator.

```text
signature = hex( HMAC( signing_key, url + raw_body ) )
```

The `url` is the full URL SignalWire requested, including any query string. A call request signs
that URL without any basic auth credentials you embedded in it; a message request signs it exactly
as you configured it, credentials included. The `raw_body` is the JSON payload exactly as sent —
the object containing `call` (or `message` for a messaging document), `vars`, `envs`, and, when the
document was reached through `execute` or `transfer`, `params`.

**Note:** Verify against the URL you configured in the Dashboard, not the URL your framework reconstructs
from the incoming request. Proxies, load balancers, and tunnels such as ngrok routinely rewrite the
host or scheme, which changes the string being hashed and makes a valid signature look invalid.

## Troubleshoot a failing signature

- **The URL does not match.** Scheme, host, port, path, and query string all feed the hash. [...]
- **The body was re-serialized.** Hash the bytes you received, not `JSON.stringify` of the parsed object.
- **The wrong project's key.** Signing keys are per project.
- **The key was just rotated.** A new key needs about a minute to become active.
- **Basic auth in the URL.** A call strips embedded credentials before signing, so hash the URL
  without them. A message signs the URL as configured, so hash it with them.

## From https://signalwire.com/docs/swml/guides/remote-server

SignalWire signs every request for a SWML document with an HMAC signature in the
`X-Signalwire-Signature` header, which you can verify against your project's signing key.
