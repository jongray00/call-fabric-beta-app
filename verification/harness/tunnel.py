"""Expose the backend publicly: cloudflared quick tunnel, then ngrok fallback."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path

from .config import EVIDENCE


def _install_cloudflared() -> str | None:
    if shutil.which("cloudflared"):
        return shutil.which("cloudflared")
    dst = Path.home() / ".local/bin/cloudflared"
    dst.parent.mkdir(parents=True, exist_ok=True)
    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
    r = subprocess.run(["curl", "-fsSL", "-o", str(dst), url], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    dst.chmod(0o755)
    return str(dst)


def start(port: int = 8000, timeout: float = 45) -> tuple[str | None, list[dict]]:
    """Return (public_url, attempts). attempts records every approach tried and why it failed."""
    attempts = []
    log = EVIDENCE / "tunnel.log"
    bin_ = _install_cloudflared()
    if not bin_:
        attempts.append({"approach": "cloudflared", "error": "could not download cloudflared binary"})
    else:
        f = log.open("w")
        p = subprocess.Popen([bin_, "tunnel", "--no-autoupdate", "--url", f"http://localhost:{port}"],
                             stdout=f, stderr=subprocess.STDOUT)
        end = time.time() + timeout
        while time.time() < end:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", log.read_text())
            if m:
                return m.group(0), attempts
            if p.poll() is not None:
                break
            time.sleep(0.5)
        p.kill()
        attempts.append({"approach": "cloudflared quick tunnel", "error": log.read_text()[-2000:]})
    if os.environ.get("NGROK_AUTHTOKEN") and shutil.which("ngrok"):
        p = subprocess.Popen(["ngrok", "http", str(port), "--log", "stdout", "--log-format", "logfmt"],
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        end = time.time() + timeout
        while time.time() < end:
            line = p.stdout.readline()
            m = re.search(r"url=(https://\S+)", line)
            if m:
                return m.group(1), attempts
        p.kill()
        attempts.append({"approach": "ngrok", "error": "no url within timeout"})
    else:
        attempts.append({"approach": "ngrok", "error": "NGROK_AUTHTOKEN or ngrok binary not present"})
    return None, attempts
