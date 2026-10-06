"""Audio fixtures (tones) and recording analysis (ffprobe + per-channel per-second FFT)."""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np

BROWSER_HZ = 440.0
PSTN_HZ = 1000.0
SILENCE_RMS = 0.005  # normalized RMS below this is treated as silence


def write_tone(path: Path, hz: float, seconds: float = 30.0, rate: int = 48000, amp: float = 0.3) -> Path:
    t = np.arange(int(seconds * rate)) / rate
    data = (amp * np.sin(2 * np.pi * hz * t) * 32767).astype("<i2")
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(data.tobytes())
    return path


def make_fixtures(dir_: Path) -> dict:
    return {
        "browser": write_tone(dir_ / "browser_tone_440.wav", BROWSER_HZ, 120),
        "pstn": write_tone(dir_ / "pstn_tone_1000.wav", PSTN_HZ, 30, rate=8000),
    }


def ffprobe(path: Path) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)],
        capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    s = next(x for x in j["streams"] if x.get("codec_type") == "audio")
    return {
        "format": j["format"].get("format_name"), "codec": s.get("codec_name"),
        "channels": int(s.get("channels", 0)), "sample_rate": int(s.get("sample_rate", 0)),
        "duration_s": float(j["format"].get("duration", 0)), "bit_rate": j["format"].get("bit_rate"),
    }


def decode(path: Path, rate: int = 8000) -> np.ndarray:
    """Decode to float32 array shape (frames, channels) at `rate`, keeping the original channel count."""
    ch = ffprobe(path)["channels"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le",
                          "-ar", str(rate), "-ac", str(ch), "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype="<f4").reshape(-1, ch)


def per_second(path: Path, rate: int = 8000) -> list[dict]:
    """For each 1 s window and channel: dominant frequency (Hz) and RMS."""
    x = decode(path, rate)
    rows = []
    for i in range(0, len(x) // rate):
        seg = x[i * rate:(i + 1) * rate]
        row = {"second": i, "channels": []}
        for c in range(seg.shape[1]):
            s = seg[:, c]
            rms = float(np.sqrt(np.mean(s ** 2)))
            spec = np.abs(np.fft.rfft(s * np.hanning(len(s))))
            freqs = np.fft.rfftfreq(len(s), 1 / rate)
            dom = float(freqs[int(np.argmax(spec[1:]) + 1)]) if rms > SILENCE_RMS else None
            row["channels"].append({"dominant_hz": dom, "rms": round(rms, 5)})
        rows.append(row)
    return rows


def classify(hz: float | None) -> str:
    if hz is None:
        return "silence"
    if abs(hz - BROWSER_HZ) <= 15:
        return "browser_440"
    if abs(hz - PSTN_HZ) <= 15:
        return "pstn_1000"
    return f"other_{int(hz)}"


def channel_map(path: Path) -> dict:
    """Majority label per channel across non-silent seconds, plus the silent-second spans."""
    rows = per_second(path)
    nch = len(rows[0]["channels"]) if rows else 0
    result = {"probe": ffprobe(path), "channels": {}, "timeline": []}
    for c in range(nch):
        labels = [classify(r["channels"][c]["dominant_hz"]) for r in rows]
        voiced = [l for l in labels if l != "silence"]
        maj = max(set(voiced), key=voiced.count) if voiced else "silence"
        result["channels"][f"ch{c}"] = {"majority": maj, "silent_seconds": [i for i, l in enumerate(labels) if l == "silence"]}
    result["timeline"] = [[classify(ch["dominant_hz"]) for ch in r["channels"]] for r in rows]
    return result


def silent_spans(labels: list[str]) -> list[tuple[int, int]]:
    spans, start = [], None
    for i, l in enumerate(labels + ["x"]):
        if l == "silence" and start is None:
            start = i
        elif l != "silence" and start is not None:
            spans.append((start, i - 1))
            start = None
    return spans
