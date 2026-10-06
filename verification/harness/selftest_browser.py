"""Local self-test: the real v4 UMD bundle loads in headless Chromium with fake media, exposes the
identifiers the harness relies on, and the device page reports events to the backend. No Space needed."""
import json
import sys

from .audio import make_fixtures
from .backend import STATE, serve
from .config import EVIDENCE
from .devices import Devices


def main():
    fx = make_fixtures(EVIDENCE / "fixtures")
    serve(8000)
    STATE.test_id = "selftest_browser"
    devs = Devices("http://127.0.0.1:8000", str(fx["browser"]))
    try:
        r = devs.open("selftest-dev1")
        shape = r.get("shape", {})
        loaded = STATE.wait_for(lambda e: e.get("type") == "page_loaded", 10)
        # Registration with no minter must fail cleanly (proves the error path reports back).
        reg = devs.call("selftest-dev1", "register", {"ref": "nobody"})
        checks = {
            "umd_global_present": shape.get("global") == "object",
            "SignalWire_class": shape.get("SignalWire") == "function",
            "StaticCredentialProvider": shape.get("StaticCredentialProvider") == "function",
            "TokenRefreshError_exported": shape.get("TokenRefreshError") == "function",
            "page_reported_to_backend": loaded is not None,
            "register_without_token_fails_cleanly": reg.get("ok") is False and "token fetch 503" in reg.get("error", ""),
        }
        out = EVIDENCE / "selftest" / "browser"
        out.mkdir(parents=True, exist_ok=True)
        (out / "result.json").write_text(json.dumps({"checks": checks, "shape": shape, "register": reg}, indent=2))
        print(json.dumps(checks))
        sys.exit(0 if all(checks.values()) else 1)
    finally:
        devs.shutdown()


if __name__ == "__main__":
    main()
