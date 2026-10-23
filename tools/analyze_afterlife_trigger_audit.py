"""Read-only verdict for a completed Afterlife A1 JSONL run.

Usage: python tools/analyze_afterlife_trigger_audit.py <exact-log-path>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


GUARD_FACTS = {
    "PostTowerFreeRoamActive": 1,
    "PTFRP0_DR13": 1,
    "q307_active": 0,
    "q307_done": 1,
    "q307_finished": 1,
    "q307_2079": 1,
    "q307_main_game_killed": 1,
    "q305_johnny_scene_active": 0,
    "mirror_interaction_disabled": 0,
    "q115_point_of_no_return": 0,
    "PTFRB0ALM_Enabled": 1,
    "PTFRB0ALM_Interrupted": 0,
}
COUNTERS = ("Requested", "Boot", "Guard", "Owner", "Outside", "Inside", "Exits")


def values(row: dict) -> dict[str, int | str]:
    facts = row.get("state", {}).get("facts", {})
    return {suffix: facts.get("PTFRALMA1_" + suffix, "MISSING") for suffix in COUNTERS}


def main(path: Path) -> int:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Empty log")
    failures: list[str] = []
    if len({row.get("run_id") for row in rows}) != 1:
        failures.append("multiple run IDs in one file")
    if [row.get("seq") for row in rows] != list(range(1, len(rows) + 1)):
        failures.append("missing or out-of-order records")
    if rows[0].get("event") != "INITIAL_BASELINE":
        failures.append("initial baseline record absent")
    if rows[-1].get("event") != "LISTENERS_CLOSED":
        failures.append("logger was not stopped cleanly")

    baseline, ending = values(rows[0]), values(rows[-1])
    if rows[0].get("state", {}).get("player_exists") is not True:
        failures.append("player was absent at baseline")
    if baseline["Boot"] != 1:
        failures.append(f"fresh phase bootstrap was not 1 at baseline: {baseline['Boot']}")
    for suffix in ("Requested", "Guard", "Owner", "Outside", "Inside", "Exits"):
        if baseline[suffix] != 0:
            failures.append(f"nonzero baseline {suffix}={baseline[suffix]}; stale-state confound")
    ready = [row for row in rows if row.get("event") == "LISTENERS_READY"]
    if not ready or not any(row.get("detail", {}).get("registered") == 23 and
                            row.get("detail", {}).get("complete") is True for row in ready):
        failures.append("all 23 fact listeners were not confirmed")
    for row in rows:
        if row.get("event") in ("LOG_ERROR", "LISTENER_FAILED", "UNREGISTER_FAILED", "LISTENERS_UNAVAILABLE"):
            failures.append(f"recorder problem at seq {row.get('seq')}: {row.get('event')}")
        fact_snapshot = row.get("state", {}).get("facts", {})
        if row.get("state", {}).get("errors"):
            failures.append(f"snapshot read error at seq {row.get('seq')}")
        for fact, expected in GUARD_FACTS.items():
            if fact_snapshot.get(fact) != expected:
                failures.append(f"guard fact {fact} differed from {expected} at seq {row.get('seq')}")
    for suffix in ("Guard", "Owner", "Outside"):
        if ending[suffix] != 1:
            failures.append(f"native milestone {suffix} should be 1, got {ending[suffix]}")
    for suffix in ("Inside", "Exits"):
        if ending[suffix] != 2:
            failures.append(f"native {suffix} should be 2, got {ending[suffix]}")
    labels = [row.get("detail", {}).get("label") for row in rows if row.get("event") == "MARK"]
    required = ("outside-before-request", "outside-armed", "at-mirror-first",
                "outside-first-exit", "at-mirror-second", "outside-second-exit")
    indexes = [labels.index(label) for label in required if label in labels]
    if len(indexes) != len(required) or indexes != sorted(indexes):
        failures.append("required route markers missing or out of order")
    print(f"Run: {rows[0].get('run_id')} ({len(rows)} flushed records)")
    print(f"Baseline: {baseline}")
    print(f"Final: {ending}")
    print(f"Marks: {labels}")
    if failures:
        print("NATIVE SHADOW TEST: NOT PASSED")
        for failure in dict.fromkeys(failures):
            print("- " + failure)
        return 1
    print("NATIVE SHADOW TEST: PASS (two native entries and two native exits)")
    print("The redscript scene driver remains in use; native scene replacement is untested.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(Path(sys.argv[1])))
