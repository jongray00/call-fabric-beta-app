"""Local self-test: synthesize a stereo MP3 (L=1000 Hz PSTN, R=440 Hz browser, 5 s silence gap on both
channels to mimic a 'silence' pause) plus a 'skip' variant, then prove the analyzer recovers the mapping,
the gap, and the shorter duration."""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from .audio import channel_map, make_fixtures, silent_spans
from .config import EVIDENCE


def synth(path: Path, gap: bool, seconds=20, rate=8000):
    t = np.arange(seconds * rate) / rate
    l = 0.3 * np.sin(2 * np.pi * 1000 * t)
    r = 0.3 * np.sin(2 * np.pi * 440 * t)
    if gap:
        l[8 * rate:13 * rate] = 0
        r[8 * rate:13 * rate] = 0
    else:  # skip: remove the window entirely
        keep = np.r_[0:8 * rate, 13 * rate:seconds * rate]
        l, r = l[keep], r[keep]
    pcm = (np.stack([l, r], 1) * 32767).astype("<i2").tobytes()
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "s16le", "-ar", str(rate), "-ac", "2", "-i", "-",
                    "-codec:a", "libmp3lame", "-b:a", "64k", str(path)], input=pcm, check=True)


def main():
    out = EVIDENCE / "selftest" / "audio"
    out.mkdir(parents=True, exist_ok=True)
    fx = make_fixtures(EVIDENCE / "fixtures")
    synth(out / "silence_variant.mp3", gap=True)
    synth(out / "skip_variant.mp3", gap=False)
    res = {k: channel_map(out / f"{k}.mp3") for k in ["silence_variant", "skip_variant"]}
    sv = res["silence_variant"]
    checks = {
        "fixtures_exist": all(Path(p).exists() for p in fx.values()),
        "ch0_is_pstn": sv["channels"]["ch0"]["majority"] == "pstn_1000",
        "ch1_is_browser": sv["channels"]["ch1"]["majority"] == "browser_440",
        "silence_gap_found": any(a >= 7 and b <= 13 and b - a >= 3 for a, b in silent_spans([r[0] for r in sv["timeline"]])),
        "skip_shorter": res["skip_variant"]["probe"]["duration_s"] < sv["probe"]["duration_s"] - 4,
        "skip_no_gap": not silent_spans([r[0] for r in res["skip_variant"]["timeline"]][1:-1]),
    }
    (out / "result.json").write_text(json.dumps({"checks": checks, "analysis": res}, indent=2))
    print(json.dumps(checks))
    sys.exit(0 if all(checks.values()) else 1)


if __name__ == "__main__":
    main()
