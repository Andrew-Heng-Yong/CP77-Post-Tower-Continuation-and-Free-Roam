"""Read-only P4 exploration trace analysis; API absence is never a broken system."""
import argparse
import json
import math
import time
from pathlib import Path

from package_phase2b_p2 import ROOT, MODS

MODULE = "PTFR_Phase2B_P4_Explore"
LOG = MODS / MODULE / "ptfr_p4_explore.jsonl"
SYSTEMS = ("ground", "movement", "pedestrians", "weapons", "police", "map", "inventory", "character",
           "saving", "reload", "traffic", "vehicles", "phone", "vendors", "fast_travel", "apartments",
           "encounters", "quests", "dogtown", "media")


def obj(value):
    if value is None or value == []:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Expected JSON object or empty Lua table, not " + type(value).__name__)
    return value


def read_rows(path):
    content = path.read_text(encoding="utf-8-sig")
    lines, rows, warnings = content.splitlines(), [], []
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            if i == len(lines) and not content.endswith("\n"):
                warnings.append("Ignored incomplete final line while writer was active")
                continue
            raise ValueError(f"Invalid JSON at line {i}")
        if not isinstance(row, dict) or row.get("probe") != "Phase2B-P4-explore" or row.get("schema") != 1:
            raise ValueError(f"Wrong trace schema/probe at line {i}")
        for name in ("state", "detail", "read_errors"):
            row[name] = obj(row.get(name))
        rows.append(row)
    if not rows:
        raise ValueError("No complete P4 trace records")
    return rows, warnings


def current_run(rows):
    run = rows[-1].get("run_id")
    chosen = [r for r in rows if r.get("run_id") == run]
    seqs = [r.get("seq") for r in chosen]
    if any(not isinstance(s, int) for s in seqs) or any(a >= b for a, b in zip(seqs, seqs[1:])):
        raise ValueError("Run sequence is not strictly increasing")
    return chosen


def readiness(rows, age):
    selected = current_run(rows)
    failures = []
    if age > 30:
        failures.append("Trace is stale; restart/load the game and run Inspect")
    if any(r.get("event") == "SHUTDOWN" for r in selected):
        failures.append("Latest process has shut down")
    init = [r for r in selected if r.get("event") == "INIT"]
    if not init or init[-1]["detail"].get("manual_only") is not True or init[-1]["detail"].get("hooks_registered") is not True:
        failures.append("Manual-only INIT/lifecycle hooks not verified")
    session = selected[-1].get("session_id")
    loaded = [r for r in selected if r.get("session_id") == session]
    life = [r["event"] for r in loaded if r["event"] in ("PLAYER_ATTACHED", "PLAYER_DETACH")]
    if not life or life[-1] != "PLAYER_ATTACHED":
        failures.append("Current fixture is not attached")
    if any(r["event"] == "RELOCATION_REQUEST" for r in selected):
        failures.append("One relocation already requested in this process; no retry")
    preflight = [r for r in loaded if r["event"] == "PREFLIGHT"]
    if not preflight:
        failures.append("Run GetMod(\"PTFR_Phase2B_P4_Explore\").Inspect() first")
    else:
        last = preflight[-1]
        if selected[-1].get("elapsed_s", 0) - last.get("elapsed_s", 0) > 30:
            failures.append("Preflight is older than 30 unpaused seconds; Inspect again")
        if last["detail"].get("baseline_ready") is not True or obj(last["state"].get("guard")).get("passed") is not True:
            failures.append("Current post-Tower fixture guard/baseline failed")
        target = obj(last["detail"].get("target_check"))
        if target.get("passed") is not True:
            failures.extend(target.get("failures") or ["Target support/clearance/navmesh not ready"])
    return failures


def summarize(rows, warnings=None):
    selected = current_run(rows)
    report = {"run_id": selected[-1]["run_id"], "rows": len(selected), "warnings": warnings or [],
              "systems": {s: {"status": "UNKNOWN / NOT TESTED", "basis": "No conclusive outcome reported"} for s in SYSTEMS},
              "loaded_sessions": [], "requests": [], "human_reports": [], "read_errors": {}, "alerts": [],
              "current_active_quest_graph_instances": "UNKNOWN", "complete_world_streaming": "UNKNOWN"}
    for row in selected:
        event, detail, state = row["event"], row["detail"], row["state"]
        if event == "INIT":
            for system, status in obj(detail.get("prior_observed")).items():
                if system in report["systems"] and status == "WORKING":
                    report["systems"][system] = {"status": "WORKING", "basis": "Prior tester-observed retained-session result, not a new current-run test"}
        if event == "HUMAN_REPORT":
            report["human_reports"].append({"session": row.get("session_id"), "seq": row["seq"], **detail})
            system, status = detail.get("system"), detail.get("status")
            if system in report["systems"] and status in ("WORKING", "BROKEN", "UNKNOWN"):
                report["systems"][system] = {"status": "UNKNOWN / NOT TESTED" if status == "UNKNOWN" else status,
                                             "basis": "Tester report: " + str(detail.get("note", "")), "seq": row["seq"]}
        if event == "RELOCATION_REQUEST":
            report["requests"].append({"seq": row["seq"], "session": row["session_id"], **detail})
        if event in ("INITIAL_FALL_ALERT", "COMMAND_ERROR", "POLL_ERROR"):
            report["alerts"].append({"event": event, "seq": row["seq"], "detail": detail})
        for key, value in row["read_errors"].items():
            item = report["read_errors"].setdefault(key, {"count": 0, "latest": None})
            item["count"] += 1
            item["latest"] = value
    sessions = list(dict.fromkeys(r["session_id"] for r in selected if "/load-" in r["session_id"]))
    for session in sessions:
        group = [r for r in selected if r["session_id"] == session]
        request_rows = [r for r in group if r["event"] == "RELOCATION_REQUEST"]
        states = [r for r in group if r["state"].get("player_exists") is True]
        arrival = [r for r in group if r["event"] == "ARRIVAL_SAMPLE"]
        first_facts, last_facts = {}, {}
        for row in states:
            for name, value in obj(row["state"].get("facts")).items():
                if type(value) in (int, float) and math.isfinite(value):
                    first_facts.setdefault(name, value)
                    last_facts[name] = value
        summary = {"session": session, "rows": len(group), "relocation_requests": len(request_rows),
                   "initial_arrival_evidence": [r["detail"] for r in arrival if r["detail"].get("milestone") == 10],
                   "first_facts": first_facts, "last_facts": last_facts,
                   "fact_comparison_scope": "First and last successful numeric read per fact within this load; missing/unavailable reads are not changes or proof of unchanged state",
                   "fact_differences": {}, "readable_system_snapshots": []}
        for key, before in summary["first_facts"].items():
            after = summary["last_facts"].get(key, "UNKNOWN")
            if after != before:
                summary["fact_differences"][key] = {"before": before, "after": after, "cause": "Not established by this comparison"}
        for r in states:
            if r["state"].get("systems"):
                summary["readable_system_snapshots"].append({"seq": r["seq"], "state": r["state"]})
        # Preserve baseline and latest rich reads without dumping a several-minute trace.
        snaps = summary["readable_system_snapshots"]
        if len(snaps) > 2:
            summary["readable_system_snapshots"] = [snaps[0], snaps[-1]]
        report["loaded_sessions"].append(summary)
    report["interpretation"] = [
        "A returned teleport call is not arrival or free-roam success.",
        "Supported target samples establish local support only; human reports determine actual exploration outcomes.",
        "Unavailable getters and zero callback counts are UNKNOWN, not BROKEN.",
        "Journal-active quests are not running quest-root instances; compare each load separately.",
        "Successful ordinary-world exploration can mean that world was already present; the probe does not restore it.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=LOG)
    parser.add_argument("--ready", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        rows, warnings = read_rows(args.log)
        if args.ready:
            failures = readiness(rows, time.time() - args.log.stat().st_mtime)
            if failures:
                print("NOT READY — no relocation needed: " + "; ".join(failures))
                return 1
            print("READY at last Inspect. The relocation command will recheck all safety conditions before moving.")
            return 0
        result = json.dumps(summarize(rows, warnings), indent=2)
        if args.output:
            target = args.output.resolve()
            if not target.is_relative_to(ROOT.resolve()):
                raise ValueError("Analysis output must stay inside the workspace")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(result + "\n", encoding="utf-8")
        print(result)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print("ANALYSIS NOT READY: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
