"""Read-only verdict for the single-site Coyote C1 native crossing log."""

import argparse
import json
from pathlib import Path


EXPECTED_FACTS = {
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
}
ROUTE = [
    "outside-before-request",
    "outside-armed",
    "inside-first",
    "outside-first",
    "inside-second",
    "outside-second",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.log.read_text(encoding="utf-8").splitlines()]
    failures: list[str] = []
    if not rows or rows[0].get("event") != "START" or rows[-1].get("event") != "STOP":
        failures.append("log is missing START or STOP")
    if any(row.get("probe") != "CoyoteTriggerAudit-C1" for row in rows):
        failures.append("unexpected probe identifier")
    if [row.get("sequence") for row in rows] != list(range(1, len(rows) + 1)):
        failures.append("sequence gap or duplicate")
    marks = [row for row in rows if row.get("event") == "MARK"]
    labels = [row.get("label") for row in marks]
    if labels != ROUTE:
        failures.append(f"route labels differ: {labels}")
    for row in rows:
        state = row.get("state", {})
        if state.get("errors"):
            failures.append(f"row {row.get('sequence')} read errors: {state['errors']}")
        facts = state.get("facts", {})
        for name, expected in EXPECTED_FACTS.items():
            if facts.get(name) != expected:
                failures.append(f"row {row.get('sequence')} {name}={facts.get(name)!r}, expected {expected}")
    if marks:
        initial = marks[0]["state"]["facts"]
        for suffix in ("Requested", "Guard", "Owner", "Outside", "Inside", "Exits"):
            if initial.get("PTFRCM1_" + suffix) != 0:
                failures.append(f"baseline {suffix} not zero")
        if initial.get("PTFRCM1_Boot") != 1:
            failures.append("baseline Boot is not 1")
        final = marks[-1]["state"]["facts"]
        for suffix, expected in (("Guard", 1), ("Owner", 1), ("Outside", 1), ("Inside", 2), ("Exits", 2)):
            if final.get("PTFRCM1_" + suffix) != expected:
                failures.append(f"final {suffix}={final.get('PTFRCM1_' + suffix)!r}, expected {expected}")
    print(json.dumps({
        "verdict": "PASS_NATIVE_CROSSINGS_ONLY" if not failures else "FAIL_OR_INCOMPLETE",
        "rows": len(rows),
        "route": labels,
        "final_counters": {name: marks[-1]["state"]["facts"].get("PTFRCM1_" + name)
                           for name in ("Boot", "Guard", "Owner", "Outside", "Inside", "Exits")}
        if marks else {},
        "failures": failures,
        "limitation": "Counter snapshots do not prove that a Look prompt or scene was restored.",
    }, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
