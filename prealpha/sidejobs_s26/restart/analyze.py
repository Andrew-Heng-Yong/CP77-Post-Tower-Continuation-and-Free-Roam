"""Offline S26 capture triage. This program has no game mutation interface."""
import argparse
import json
from pathlib import Path


def observed(row):
    return row.get("value") if isinstance(row, dict) and row.get("status") == "Observed" else None


def assess(report):
    if report.get("schema") != 2 or report.get("kind") != "S26_READ_ONLY_RESTART_AND_SERVICE_CAPTURE":
        raise ValueError("Not an S26 capture")
    first, second = report.get("first", {}), report.get("second", {})
    rows, other = first.get("jobs", []), second.get("jobs", [])
    if len(rows) != 58 or len({r["id"] for r in rows}) != 58 or [r["id"] for r in rows] != [r["id"] for r in other]:
        raise ValueError("Incomplete or inconsistent whitelist")
    settled = (report.get("status") == "STABLE_READ_ONLY_CAPTURE" and report.get("repeatedReadMatched") is True and first == second
               and bool(first.get("context")) and all(observed(v) is not None for v in first.get("context", {}).values()))
    result = {"status": "READ_ONLY_TRIAGE_NOT_RESTART_AUTHORIZATION", "restart_authorized": False,
              "observations_settled": settled, "completed_protected": [], "candidates": [], "unknown": [], "jobs": []}
    for row in rows:
        state = row.get("rootState", "Unknown")
        # Completed root protection has precedence over any unfinished child.
        decision = "PRESERVE_COMPLETED" if state == "Succeeded" else (
            "RESTART_REVIEW" if settled and state in ("Active", "Inactive", "Failed") else "DEFER_UNKNOWN")
        key = {"PRESERVE_COMPLETED": "completed_protected", "RESTART_REVIEW": "candidates", "DEFER_UNKNOWN": "unknown"}[decision]
        result[key].append(row["id"])
        unknown_fields = [n for n, v in row.get("facts", {}).items() if observed(v) is None]
        unknown_fields += [n for o in row.get("owners", []) for n, v in o.get("facts", {}).items() if observed(v) is None]
        unknown_fields += [j["path"] for j in row.get("journals", []) if j.get("state") not in ("Active", "Inactive", "Failed", "Succeeded")]
        if decision == "RESTART_REVIEW" and unknown_fields:
            result[key].remove(row["id"]); result["unknown"].append(row["id"]); decision = "DEFER_UNKNOWN"
        result["jobs"].append({"id": row["id"], "root_state": state, "decision": decision, "unknown_fields": unknown_fields,
                               "completed_child_entries": [j["path"] for j in row.get("journals", []) if j.get("state") == "Succeeded" and j["path"] != row["root"]],
                               "restart_authorized": False, "missing_proofs": ["targeted owner retirement", "per-job reset allowlist", "world persistence and prior reward history"]})
    sacrum = next(r for r in rows if r["id"] == "mq032_sacrum")
    owner = next((o for o in sacrum.get("owners", []) if o["tag"] == "PTFRS2_MQ032"), {})
    issued = observed(owner.get("facts", {}).get("PTFRS2_MQ032_Issued"))
    complete = observed(sacrum.get("facts", {}).get("mq032_complete"))
    if sacrum.get("rootState") == "Succeeded" or (complete is not None and complete > 0):
        route = "PRESERVE: Sacrum completed; choose another incomplete standalone job"
    elif not settled or issued is None:
        route = "DEFER: missing/unstable exact S2 owner observation"
    elif issued != 0:
        route = "SAVED_MOD_OWNER_MIGRATION: implement and validate targeted S2 wrapper retirement before any state reset; never zero Issued"
    else:
        route = "UNISSUED_OWNER_REVIEW: audit exact local community/loot persistence and reset manifest; native Tower termination does not itself certify all graph instances"
    result["next_bounded_candidate"] = {"id": "mq032_sacrum", "route": route, "observed_issued": issued,
                                         "remaining_native_work": "S2 native hook/combat/epilogue phases, local Maelstrom communities and loot objective; no global prefix reset", "restart_authorized": False}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=Path)
    args = parser.parse_args()
    print(json.dumps(assess(json.loads(args.capture.read_text(encoding="utf-8-sig"))), indent=2))


if __name__ == "__main__":
    main()
