"""Python side of the Playwright device driver."""
from __future__ import annotations

import os
import subprocess
import time

import httpx

from .config import EVIDENCE, ROOT


class Devices:
    def __init__(self, backend_url: str, wav: str, port: int | None = None):
        if port is None:
            import socket
            with socket.socket() as so:
                so.bind(("127.0.0.1", 0))
                port = so.getsockname()[1]
        self.backend, self.wav, self.port = backend_url, wav, port
        self.base = f"http://127.0.0.1:{port}"
        log = (EVIDENCE / "driver.log").open("a")
        env = dict(os.environ, DRIVER_PORT=str(port))
        self.proc = subprocess.Popen(["node", str(ROOT / "harness/browser/driver.cjs")], stdout=log, stderr=log, env=env)
        for _ in range(100):
            try:
                httpx.get(self.base + "/devices/x/call", timeout=0.5)
                break
            except Exception:
                if self.proc.poll() is not None:
                    raise RuntimeError("device driver exited; see evidence/driver.log")
                time.sleep(0.1)
        self.ids: list[str] = []

    def open(self, dev_id: str) -> dict:
        r = httpx.post(self.base + "/devices", json={"id": dev_id, "backend": self.backend, "wav": self.wav}, timeout=60).json()
        self.ids.append(dev_id)
        return r

    def call(self, dev_id: str, fn: str, *args, timeout: float = 60):
        return httpx.post(f"{self.base}/devices/{dev_id}/call", json={"fn": fn, "args": list(args)}, timeout=timeout).json()

    def close(self, dev_id: str):
        httpx.delete(f"{self.base}/devices/{dev_id}", timeout=30)
        if dev_id in self.ids:
            self.ids.remove(dev_id)

    def shutdown(self):
        for d in list(self.ids):
            try:
                self.close(d)
            except Exception:
                pass
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
