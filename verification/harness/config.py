"""Configuration, safety guards and budget tracking for the verification harness."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "evidence"
REPORT = ROOT / "report"

# Rule 3: emergency, N11 and short codes are never dialed.
DENYLIST_EXACT = {"911", "933", "988", "311", "411", "112", "999"}
N11_RE = re.compile(r"^\+?1?[2-9]11$")


def load_env(path: Path | None = None) -> dict:
    """Read .env (KEY=VALUE lines) and overlay os.environ. Missing file is not fatal."""
    env: dict[str, str] = {}
    for p in [path or ROOT / ".env", ROOT.parent / ".env"]:
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    for k in ["SW_SPACE", "SW_PROJECT_ID", "SW_API_TOKEN", "BUDGET_USD", "NUMBER_AREA_CODE",
              "RELEASE_NUMBERS", "NGROK_AUTHTOKEN", "SW_SIGNING_KEY"]:
        if os.environ.get(k):
            env[k] = os.environ[k]
    env.setdefault("BUDGET_USD", "25")
    env.setdefault("NUMBER_AREA_CODE", "561")
    env.setdefault("RELEASE_NUMBERS", "false")
    return env


def missing_inputs(env: dict) -> list[str]:
    return [k for k in ("SW_SPACE", "SW_PROJECT_ID", "SW_API_TOKEN") if not env.get(k)]


class DialRefused(Exception):
    pass


def assert_dialable(dest: str, owned_numbers: set[str]) -> None:
    """Rules 2 and 3. Raise unless dest is an E.164 number owned by this Space and not denylisted.

    Non-PSTN destinations (Fabric addresses like /private/x, sip: URIs on the Space) are allowed
    because they never leave SignalWire.
    """
    if dest.startswith("/") or dest.startswith("sip:") or dest.startswith("fabric:"):
        return
    digits = re.sub(r"[^\d+]", "", dest)
    bare = digits.lstrip("+")
    if bare in DENYLIST_EXACT or N11_RE.match(digits) or len(bare) < 10:
        raise DialRefused(f"denylisted or short code: {dest}")
    if digits not in owned_numbers:
        raise DialRefused(f"{dest} is not a number owned by this Space")


@dataclass
class Budget:
    cap_usd: float
    spent_usd: float = 0.0
    ledger: list = field(default_factory=list)

    def charge(self, amount: float, what: str) -> None:
        self.spent_usd += float(amount or 0)
        self.ledger.append({"t": time.time(), "usd": amount, "what": what, "total": self.spent_usd})

    def estimate_call(self, seconds: float, legs: int = 2, rate_per_min: float = 0.01) -> float:
        # Conservative placeholder used only for the stop rule; real figures come from logs (A12).
        return legs * rate_per_min * max(1, -(-seconds // 60))

    def can_spend(self, amount: float) -> bool:
        return self.spent_usd + amount <= self.cap_usd

    def dump(self) -> None:
        (EVIDENCE / "budget.json").write_text(json.dumps(
            {"cap_usd": self.cap_usd, "spent_usd": self.spent_usd, "ledger": self.ledger}, indent=2))
