"""Self-test: our validator agrees with SignalWire's own published Python RequestValidator (signalwire==2.1.1)
on valid signatures, and rejects a tampered body. Live verification against real webhooks runs in B11."""
import json
import sys

from signalwire.request_validator import RequestValidator

from .config import EVIDENCE
from .signature import sign_form, sign_json, validate

KEY = "PSKtest_selftest_signing_key"
URL = "https://example.trycloudflare.com/swml/inbound?test=B11"
BODY = json.dumps({"call": {"call_id": "abc", "from": "+15615550100", "to": "+15615550101"}, "params": {}})


def main():
    official = RequestValidator(KEY)
    sig = sign_json(KEY, URL, BODY)
    form = {"CallSid": "CA1", "From": "+15615550100", "To": "+15615550101"}
    checks = {
        "sha1_matches_official_build_signature": sig == official.build_signature(URL, BODY),
        "official_validates_our_sig": official.validate(URL, BODY, sig),
        "our_validator_accepts": validate(KEY, URL, {"X-SignalWire-Signature": sig}, BODY)["valid"],
        "sha256_accepted": validate(KEY, URL, {"x-signalwire-sha256-signature": sign_json(KEY, URL, BODY, "sha256")}, BODY)["valid"],
        "tampered_body_rejected": not validate(KEY, URL, {"X-SignalWire-Signature": sig}, BODY.replace("abc", "abd"))["valid"],
        "wrong_key_rejected": not validate("wrong", URL, {"X-SignalWire-Signature": sig}, BODY)["valid"],
        "form_matches_official_compat": official.validate_with_compatibility(URL, form, sign_form(KEY, URL, form)),
    }
    out = EVIDENCE / "selftest" / "signature"
    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps({"checks": checks, "url": URL, "body": BODY, "sig": sig}, indent=2))
    print(json.dumps(checks))
    sys.exit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
