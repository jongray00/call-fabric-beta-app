---
source: https://signalwire.com/docs/platform/webhooks; https://signalwire.com/docs/swml/guides/webhook-security; signalwire-python:docs/security.md
retrieved_via: mcp__SignalWire_Knowledge__last_resort_search (collection signalwire_unified_v3)
fetched_at: 2026-10-06T15:23:46Z
note: 
---

Platform webhooks: "SignalWire signs its requests with a digital HMAC security key. You can verify that the security key matches the key documented in your Dashboard's API Credentials with the `validateRequest` method."
JS example: validateRequest("<SIGNING_KEY_FROM_Dashboard>", req.headers["x-signalwire-signature"], "https://example.ngrok.io/mywebhook", req.rawBody)

Python SDK security.md:
"**Headers.** `X-SignalWire-Signature` carries a SHA-1 signature. Newer platform builds also send `X-SignalWire-Sha256-Signature`, and the agent checks it first when it's present. For cXML compatibility, `X-Twilio-Signature` is accepted in place of `X-SignalWire-Signature`."
"**Scheme A: JSON requests** (SWML, SWAIG, post-prompt summaries, RELAY events). The signature is the lowercase hex HMAC of the full URL SignalWire POSTed to, followed by the raw request body:
signature        = hex(HMAC-SHA1(signing_key, url + raw_body))
sha256 signature = hex(HMAC-SHA256(signing_key, url + raw_body))"
"**Scheme B: form-encoded requests** (cXML ...). The form parameters are sorted by name, and each name and value is appended to the URL ... The signature is the standard base64 HMAC-SHA1 of that string. The platform signs some requests with the default port in the URL (`:443` or `:80`) and some without, so the validator tries both."
