"""Read the commit and genuine completion facts from the pinned MS29 control."""

import argparse
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "universal_resume_first_live_wait_20261115_01"))
from qualify_saved_wait import (INSTALLED, TOWER_CONTROL, TOWER_CONTROL_SHA, make_reader, pin, read, write)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100))
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()
    baseline = read(pin(INSTALLED, "57A78D066D6B7465572FB5F61AA0644AC6D247308C00E4AD1A7E07F59A4AB5C4"))
    facts = ["PTFRHS3_GateOpen", "PTFRHS3_GateTicket", "PTFRHS3_GateRoute", "PTFRHS3_GateResult",
             "PostTowerFreeRoamActive", "PTFRP0_DR13", "q307_debug_reset"]
    write(out / "selection.json", {
        "slots": [TOWER_CONTROL], "tower_control": True,
        "fact_names": facts, "phase_hashes": [], "journal_hashes": [],
    })
    target = Path(baseline["save_root"]) / TOWER_CONTROL / "sav.dat"
    pin(target, TOWER_CONTROL_SHA)
    reader = make_reader(out)
    result = subprocess.run(["pwsh", "-NoProfile", "-File", str(reader), "-Directory", str(out)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=75)
    (out / "reader.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    result.check_returncode()
    raw = read(out / f"{TOWER_CONTROL}.json")
    if raw.get("decision") != "read_for_binding" or raw["sha256"] != TOWER_CONTROL_SHA:
        raise ValueError(f"Unavailable Tower control: {raw.get('binding_error')}")
    pin(target, TOWER_CONTROL_SHA)
    body = {"slot": TOWER_CONTROL, "save_sha256": raw["sha256"], "facts": raw["facts"]}
    write(out / "assessment.json", body)
    print(json.dumps(body, indent=2))


if __name__ == "__main__":
    main()
