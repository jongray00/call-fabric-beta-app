"""Mint a Subscriber Access Token. Endpoint and fields: evidence/docs/rest/fabric_subscribers_and_tokens.md.
Proof status: request shape from docs; not yet exercised against a live Space."""
import time, httpx

def mint_sat(space, project_id, api_token, subscriber_email, ttl_s=3600, fingerprint=None, refreshable=False):
    body = {"reference": subscriber_email, "expire_at": int(time.time()) + ttl_s}
    if fingerprint:
        body["fingerprint"] = fingerprint
    if refreshable:
        body["scope"] = ["sat:refresh"]
    r = httpx.post(f"https://{space}/api/fabric/subscribers/tokens", json=body, auth=(project_id, api_token))
    r.raise_for_status()
    j = r.json()
    j["expiry_at"] = body["expire_at"] * 1000  # Browser SDK v4 expects milliseconds
    return j
