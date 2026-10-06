"""SignalWire webhook signature validation.

Documented scheme (evidence/docs/swml/public_swml_webhook_security.md, sdk_webhook_signature_validation.md):
  X-SignalWire-Signature        = hex(HMAC-SHA1(signing_key,   url + raw_body))   JSON requests
  X-SignalWire-Sha256-Signature = hex(HMAC-SHA256(signing_key, url + raw_body))   call requests
  form-encoded (cXML) requests  = base64(HMAC-SHA1(signing_key, url + k1 + v1 + k2 + v2 ...)), keys sorted
The key is the project Signing Key (Dashboard > API Credentials), not the API token.
For call requests the platform signs the URL with any embedded basic-auth credentials removed.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
from urllib.parse import urlsplit, urlunsplit


def _strip_userinfo(url: str) -> str:
    p = urlsplit(url)
    netloc = p.netloc.rsplit("@", 1)[-1]
    return urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment))


def sign_json(signing_key: str, url: str, raw_body: str | bytes, algo: str = "sha1") -> str:
    body = raw_body.decode() if isinstance(raw_body, bytes) else raw_body
    digest = hashlib.sha1 if algo == "sha1" else hashlib.sha256
    return hmac.new(signing_key.encode(), (url + body).encode(), digest).hexdigest()


def sign_form(signing_key: str, url: str, params: dict) -> str:
    s = url + "".join(k + str(params[k]) for k in sorted(params))
    return base64.b64encode(hmac.new(signing_key.encode(), s.encode(), hashlib.sha1).digest()).decode()


def validate(signing_key: str, url: str, headers: dict, raw_body: str | bytes) -> dict:
    """Return {"valid": bool, "checked": header_name, ...}. Header lookup is case-insensitive."""
    h = {k.lower(): v for k, v in headers.items()}
    candidates = [url, _strip_userinfo(url)]
    if "x-signalwire-sha256-signature" in h:
        sig = h["x-signalwire-sha256-signature"]
        ok = any(hmac.compare_digest(sign_json(signing_key, u, raw_body, "sha256"), sig) for u in candidates)
        return {"valid": ok, "checked": "X-SignalWire-Sha256-Signature"}
    sig = h.get("x-signalwire-signature") or h.get("x-twilio-signature")
    if not sig:
        return {"valid": False, "checked": None, "reason": "no signature header"}
    ok = any(hmac.compare_digest(sign_json(signing_key, u, raw_body), sig) for u in candidates)
    return {"valid": ok, "checked": "X-SignalWire-Signature"}
