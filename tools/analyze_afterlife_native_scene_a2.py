"""Read-only verdict for one completed Afterlife native A2 scene log.

Usage: python tools/analyze_afterlife_native_scene_a2.py <exact-log-path>
The physical prompt and action results must still be reported by the player.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


STORY_GUARDS = {
    "PostTowerFreeRoamActive": 1, "PTFRP0_DR13": 1, "q307_active": 0,
    "q307_done": 1, "q307_finished": 1, "q307_2079": 1,
    "q307_main_game_killed": 1, "q305_johnny_scene_active": 0,
    "mirror_interaction_disabled": 0, "q115_point_of_no_return": 0,
}
FRESH = ("Requested", "Guard", "Ready", "Active", "Completed", "Interrupted",
         "SceneRequests", "SceneReturns", "Rearms")
ROUTE = ("outside-armed", "first-at-mirror", "first-outside",
         "second-at-mirror", "second-outside")


def facts(row: dict) -> dict:
    return row.get("state", {}).get("facts", {})


def counter(row: dict, suffix: str):
    return facts(row).get("PTFRALMA2_" + suffix, "MISSING")


def main(path: Path) -> int:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError("Empty log")
    failures: list[str] = []
    if len({row.get("run_id") for row in rows}) != 1:
        failures.append("multiple run IDs")
    if [row.get("seq") for row in rows] != list(range(1, len(rows) + 1)):
        failures.append("records missing or out of order")
    if rows[0].get("event") != "INITIAL_BASELINE" or rows[-1].get("event") != "STOP":
        failures.append("baseline or clean Stop missing")
    if counter(rows[0], "Boot") != 1:
        failures.append("fresh A2 bootstrap not witnessed")
    for suffix in FRESH:
        if counter(rows[0], suffix) != 0:
            failures.append(f"baseline {suffix} is not zero: {counter(rows[0], suffix)}")
    if facts(rows[0]).get("PTFRB0ALM_Enabled") != 1 or facts(rows[0]).get("PTFRALMA1_Requested") != 0:
        failures.append("old owner/A1 baseline was not isolated")
    if not any(row.get("event") == "ARMED" for row in rows):
        failures.append("A2 Arm did not complete")

    marks = {row.get("detail", {}).get("label"): row for row in rows if row.get("event") == "MARK"}
    ordered = [marks[label]["seq"] for label in ROUTE if label in marks]
    if len(ordered) != len(ROUTE) or ordered != sorted(ordered):
        failures.append("required route marks missing or out of order")
    for row in rows:
        if row.get("state", {}).get("read_errors"):
            failures.append(f"snapshot read error at seq {row.get('seq')}")
        for name, expected in STORY_GUARDS.items():
            if facts(row).get(name) != expected:
                failures.append(f"story guard {name} changed at seq {row.get('seq')}")
        if row.get("event") in ("ARM_REFUSED", "ARM_FAILED"):
            failures.append(f"Arm failed at seq {row.get('seq')}")
    for label, requests, returns, rearms, active in (
        ("first-at-mirror", 1, 0, 0, 1),
        ("first-outside", 1, 1, 1, 0),
        ("second-at-mirror", 2, 1, 1, 1),
        ("second-outside", 2, 2, 2, 0),
    ):
        if label not in marks:
            continue
        row = marks[label]
        observed = (counter(row, "SceneRequests"), counter(row, "SceneReturns"),
                    counter(row, "Rearms"), counter(row, "Active"))
        expected = (requests, returns, rearms, active)
        if observed != expected:
            failures.append(f"{label}: request/return/rearm/active {observed}, expected {expected}")
    for row in rows:
        if row.get("event") not in ("ARMED", "MARK", "STOP") or row is rows[0]:
            continue
        if facts(row).get("PTFRB0ALM_Enabled") != 0 or facts(row).get("PTFRB0ALM_Active") != 0:
            failures.append(f"old v5 scene owner was not disabled at seq {row.get('seq')}")
    final = rows[-1]
    if counter(final, "SceneRequests") != 2 or counter(final, "SceneReturns") != 2 or counter(final, "Rearms") != 2:
        failures.append("final native scene lifecycle counters were not 2/2/2")
    if counter(final, "Interrupted") != 0 or counter(final, "Active") != 0:
        failures.append("A2 was interrupted or still active at Stop")

    print(f"Run: {rows[0].get('run_id')} ({len(rows)} records)")
    for label in ROUTE:
        if label in marks:
            row = marks[label]
            print(f"{label}: requests={counter(row, 'SceneRequests')} "
                  f"returns={counter(row, 'SceneReturns')} "
                  f"rearms={counter(row, 'Rearms')} active={counter(row, 'Active')}")
    if failures:
        print("A2 NATIVE SCENE LIFECYCLE: NOT PASSED")
        for failure in dict.fromkeys(failures):
            print("- " + failure)
        return 1
    print("A2 NATIVE SCENE LIFECYCLE: COUNTERS PASS")
    print("Physical Look/expression/Stop and reload still require separate confirmation.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(Path(sys.argv[1])))
