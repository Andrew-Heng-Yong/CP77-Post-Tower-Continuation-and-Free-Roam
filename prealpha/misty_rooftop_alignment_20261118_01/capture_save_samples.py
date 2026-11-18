"""Capture just the world and weather sections from five saves, with source hashes."""

import base64
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from functools import partial
import subprocess

from placement import ROOT, sha


SLOTS = ("ManualSave-26", "AutoSave-16", "ManualSave-32", "AutoSave-9", "AutoSave-10")
OUT = ROOT / "work/saved_world_01"
ENDING_OUT = ROOT / "work/saved_ending_01"


def capture(slot, out):
    result = subprocess.run(["pwsh", "-NoProfile", "-File", str(ROOT / "read_lighting_evidence.ps1"),
                             "-Slot", slot], capture_output=True, text=True, check=True)
    result = json.loads(result.stdout)
    assert result["slot"] == slot
    source = Path("C:/Users/Ayong/Saved Games/CD Projekt Red/Cyberpunk 2077") / slot
    meta = json.loads((source / "metadata.9.json").read_text(encoding="utf-8-sig"))
    result["sections"] = {}
    for key in ("world", "weather"):
        target = out / (slot + "." + key)
        with target.open("xb") as f:
            f.write(base64.b64decode(result.pop(key), validate=True))
        result["sections"][key] = sha(target)
    result["metadata"] = {"sha256": sha(source / "metadata.9.json")}
    def extract(data):
        for key, value in data.items():
            if key in ("playerPosition", "finishedQuests", "trackedQuestEntry", "debugString", "playthroughID"):
                result["metadata"][key] = value
            elif isinstance(value, dict):
                extract(value)
    extract(meta["Data"])
    assert sha(source / "sav.dat") == result["sha256"]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ending", action="store_true")
    ending = parser.parse_args().ending
    out = ENDING_OUT if ending else OUT
    slots = ("AutoSave-15", "EndGameSave-124") if ending else SLOTS
    out.mkdir(exist_ok=False)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(partial(capture, out=out), slots))
    with (out / "sources.json").open("x", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"Verified {len(results)} read-only world and weather section captures.")
