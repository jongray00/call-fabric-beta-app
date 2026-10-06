---
source: "Server SDK docs: https://signalwire.com/docs/server-sdks/reference/python/core/security/validate-request ; signalwire-python:docs/security.md ; signalwire-typescript:docs/security.md ; sdk_surface.json"
retrieved_via: "mcp__SignalWire_Knowledge__search"
fetched_at: "2026-10-06T15:21:41Z"
note: "Verbatim chunk text as returned by the MCP vector search (signalwire_unified_v3 collection). Direct fetch of signalwire.com is blocked (403/EGRESS_BLOCKED)."
---

## signalwire-python:docs/security.md, Webhook Signature Validation

SignalWire signs every outbound webhook (SWML callbacks, SWAIG dispatch, post-prompt summaries, RELAY async events) with an HMAC. The signature is derived from a **Signing Key** the customer copies from the Dashboard's API Credentials page.

**Headers.** `X-SignalWire-Signature` carries a SHA-1 signature. Newer platform builds also send `X-SignalWire-Sha256-Signature`, and the agent checks it first when it's present. For cXML compatibility, `X-Twilio-Signature` is accepted in place of `X-SignalWire-Signature`.

**Scheme A: JSON requests** (SWML, SWAIG, post-prompt summaries, RELAY events). The signature is the lowercase hex HMAC of the full URL SignalWire POSTed to, followed by the raw request body:
```
signature        = hex(HMAC-SHA1(signing_key, url + raw_body))
sha256 signature = hex(HMAC-SHA256(signing_key, url + raw_body))
```
`url` is exactly what the platform called: scheme, host, any non-standard port, path and query string. `raw_body` is the body as sent, before JSON parsing. Parsing and re-serializing it changes the bytes and breaks the signature.

**Scheme B: form-encoded requests** (cXML and other compatibility endpoints). The form parameters are sorted by name, and each name and value is appended to the URL; a repeated name keeps its values in their original order. The signature is the standard base64 HMAC-SHA1 of that string. The platform signs some requests with the default port in the URL (`:443` or `:80`) and some without, so the validator tries both. When JSON is posted to a compatibility endpoint, the URL carries a `bodySHA256` query parameter: the signature covers that URL with no form parameters, and the body's SHA-256 hex digest must equal the parameter.

### Standalone validator (custom servers)
```python
from signalwire.core.security import validate_webhook_signature

ok = validate_webhook_signature(
    signing_key="PSK...",
    signature=request.headers["X-SignalWire-Signature"],
    url="https://my-public-host.example.com/webhook",
    raw_body=raw_request_body_bytes.decode("utf-8"),
)
if not ok:
    abort(403)
```
A legacy alias `validate_request(signing_key, signature, url, params_or_raw_body)` is provided for users migrating from the old `@signalwire/compatibility-api` shape. Pass a string raw body for the combined validator, or a pre-parsed dict for direct Scheme B (form-encoded).

## docs: validate_request (Python Server SDK reference)

Legacy-compatible webhook validator accepting a raw body or parsed form params. [...] When given a raw body string it delegates to `validate_webhook_signature`; when given parsed form params it validates them directly.
**Note:** For new custom servers, prefer `validate_webhook_signature` and pass the raw request body.

## sdk_surface.json

`validate_webhook_signature_sha256(signing_key: string, signature: string, url: string, raw_body: string) -> bool` (Python, TypeScript)

## signalwire-typescript:docs/security.md

- `X-SignalWire-Sha256-Signature`: the lowercase hex HMAC-SHA256 of the URL followed by the raw body. The agent checks it first when it's present.
- `X-SignalWire-Signature`: the SHA-1 signature. It decides when the SHA-256 header is missing or doesn't match. `X-Twilio-Signature` is accepted in its place for cXML compatibility.
For other frameworks, `validate(method, url, headers, rawBody, signingKey)` returns `null` for an authentic request, or a `[403, {}, 'Forbidden']` triple to send back. The lower-level `validateWebhookSignature()`, `validateWebhookSignatureSha256()` and `validateRequest()` return a boolean.
```typescript
import { webhookValidationMiddleware } from '@signalwire/sdk';
```
