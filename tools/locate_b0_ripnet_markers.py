"""Find already-extracted vanilla service markers with bounded streaming memory."""

from __future__ import annotations

import json
import re
from collections import deque
from pathlib import Path

from report_b0_ripnet_candidates import BASE

ROOT = Path(__file__).resolve().parent.parent
SECTORS = (
    ROOT / "research/b0_second_mirror/always_loaded_zero/json/base/worlds/03_night_city/_compiled/default/always_loaded_0.streamingsector.json",
    ROOT / "research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/always_loaded_1.streamingsector.json",
)
POSITION = re.compile(r'"Position"\s*:\s*\{[^}]*?"X"\s*:\s*([-\d.eE+]+)\s*,\s*"Y"\s*:\s*([-\d.eE+]+)\s*,\s*"Z"\s*:\s*([-\d.eE+]+)', re.S)


def main() -> None:
    audit = json.loads((BASE / "vendor_template_audit.json").read_text())
    selected = {item["scene"] for item in audit
                if item["structural_candidate"] and item["category"] in {"ripperdoc", "netrunner", "tech"}}
    rows = json.loads((BASE / "regional_vendor_inventory.json").read_text())
    markers = {row["scene_location"]: row["spawn_activate"][0]["entry"]
               for row in rows if row["scene"] in selected}
    found: dict[str, dict] = {}
    for sector in SECTORS:
        recent: deque[str] = deque(maxlen=90)
        with sector.open(encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                recent.append(line)
                for marker, vendor_id in markers.items():
                    if marker not in line or vendor_id in found:
                        continue
                    matches = list(POSITION.finditer("".join(recent)))
                    if matches:
                        x, y, z = map(float, matches[-1].groups())
                        found[vendor_id] = {"marker": marker, "x": x, "y": y, "z": z,
                                            "sector": sector.name, "line": number}
        if len(found) == len(markers):
            break
    print(json.dumps(found, indent=2))
    if len(found) != len(markers):
        raise SystemExit("Missing markers: " + ", ".join(markers[m] for m in markers if markers[m] not in found))


if __name__ == "__main__":
    main()
