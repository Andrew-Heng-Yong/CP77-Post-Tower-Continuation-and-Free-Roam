"""Analyze the manual writable P2 repair probe; requests are not repair success.

This tool only reads traces. --output writes a workspace analysis artifact, not
game state. It never combines pre/post states from different load sessions.
"""
import argparse
import json
import time
from collections import Counter
from pathlib import Path

PROBE = "Phase2B-P2-repair"
UNKNOWN = "UNKNOWN"
DOOR_ID = "13806931541592989805"
DOOR_REF = ("$/03_night_city/c_watson/little_china/"
            "loc_mystic_mistys_ripperdoc_prefabH2DWJJI/"
            "#loc_mystic_mistys_ripperdoc_gameplay/single_door_prefabSSNK5BI/"
            "#q115_dvc_ripperdoc_room_door")
GUARD_FACTS = {"PostTowerFreeRoamActive": 1, "q307_active": 0,
               "q307_done": 1, "q307_finished": 1, "q307_2079": 1}
DEFAULT_LOG = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\plugins\cyber_engine_tweaks\mods\PTFR_Phase2B_P2_RepairProbe\ptfr_p2_runtime.jsonl")


def mapping(value):
    # Empty Lua tables may encode as [] rather than {}.
    return value if isinstance(value, dict) else {}


def get(value, *keys):
    for key in keys:
        value = mapping(value).get(key, UNKNOWN)
    return UNKNOWN if value is None else value


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def known(value):
    return value is not None and value != UNKNOWN


def trace_rows(rows):
    return [r for r in rows if isinstance(r, dict) and r.get("probe") == PROBE]


def load_trace(path):
    rows = []
    diagnostics = {"malformed_lines": 0, "malformed_line_numbers": [],
                   "other_probe_lines": 0, "unsupported_schema_lines": 0}
    for index, line in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except (ValueError, TypeError):
            row = None
        if not isinstance(row, dict):
            diagnostics["malformed_lines"] += 1
            diagnostics["malformed_line_numbers"].append(index)
        elif row.get("probe") != PROBE:
            diagnostics["other_probe_lines"] += 1
        else:
            if row.get("schema") != 1:
                diagnostics["unsupported_schema_lines"] += 1
            rows.append(row)
    return rows, diagnostics


def identity(row):
    return (row.get("run_id", UNKNOWN), row.get("session_id", UNKNOWN))


def loaded(row):
    return get(row, "state", "player_exists") is True


def select_session(rows):
    """Latest loaded baseline/stage for analysis, with explicit currentness flag."""
    rows = trace_rows(rows)
    if not rows:
        raise ValueError("No Phase2B-P2 repair records")
    candidates = [r for r in rows if loaded(r) and (
        r.get("event") == "BASELINE" or r.get("stage") in {"J", "D"})]
    selected = identity(candidates[-1] if candidates else rows[-1])
    selected_rows = [r for r in rows if identity(r) == selected]
    return selected_rows, rows


def journal_state(state, entry):
    return get(state, "journal", entry, "state_value")


def journal_result(state, entry):
    return {"state": get(state, "journal", entry, "state"),
            "state_value": journal_state(state, entry),
            "tracked": get(state, "journal", entry, "tracked")}


def target_verified(state, stage):
    if stage == "J":
        return (get(state, "journal", "hierarchy_verified") is True
                or get(state, "hierarchy_verified") is True) and (
                    get(state, "journal", "objective", "id") == "05_take_walk")
    return (get(state, "door", "identity_verified") is True
            and get(state, "door", "id") == DOOR_ID
            and get(state, "door", "expected_id") == DOOR_ID
            and get(state, "door", "full_noderef") == DOOR_REF)


def target_value(state, stage):
    if not target_verified(state, stage):
        return UNKNOWN
    value = journal_state(state, "objective") if stage == "J" else get(state, "door", "device", "IsLocked")
    if stage == "J":
        return value == 3 if number(value) else UNKNOWN
    return not value if isinstance(value, bool) else UNKNOWN


def delta(before, after):
    if not known(before) or not known(after):
        return {"before": before, "after": after, "changed": UNKNOWN}
    return {"before": before, "after": after, "changed": before != after}


def cross_issue(before, after, stage):
    if stage == "J":
        names = ("IsLocked", "IsSealed", "IsOpen", "IsInteractive", "IsDisabled", "IsUnpowered", "IsOFF", "IsBusy", "IsPlayerAuthorized", "GetDoorType")
        return {name: delta(get(before, "door", "device", name), get(after, "door", "device", name)) for name in names}
    return {entry: delta(journal_state(before, entry), journal_state(after, entry))
            for entry in ("objective", "phase", "quest")}


def attempt_summary(rows, stage):
    before_row = next((r for r in rows if r.get("event") == "STAGE_BEFORE"), {})
    before = mapping(before_row.get("state"))
    requests = [r for r in rows if r.get("event") == "OPERATION_REQUESTED"]
    returns = [r for r in rows if r.get("event") == "OPERATION_RETURNED"]
    after_rows = [r for r in rows if r.get("event") == "STAGE_AFTER"]
    checks = [r for r in rows if r.get("event") == "STABILITY_CHECK"]
    after = mapping(after_rows[-1].get("state")) if after_rows else {}
    target_after = target_value(after, stage)
    observed_after_rows = [r for r in rows if r.get("event") in {"STAGE_AFTER", "STABILITY_CHECK"}]
    reached_rows = [r for r in observed_after_rows if target_value(mapping(r.get("state")), stage) is True]
    observed_success = (bool(requests) and target_value(before, stage) is False
                        and bool(reached_rows))
    if not requests:
        interpretation = "NO_OPERATION_REQUESTED"
    elif observed_success:
        interpretation = "TARGET_CHANGE_OBSERVED_AFTER_REQUEST_NOT_CAUSAL_PROOF"
    elif reached_rows:
        interpretation = "TARGET_STATE_OBSERVED_AFTER_REQUEST_TRANSITION_NOT_ESTABLISHED"
    elif target_after is False:
        interpretation = "TARGET_NOT_REACHED_IN_IMMEDIATE_SNAPSHOT"
    else:
        interpretation = "AFTER_STATE_UNKNOWN"
    delayed = [{"seq": r.get("seq"), "delay_s": get(r, "detail", "delay_s"),
                "target_reached": target_value(mapping(r.get("state")), stage),
                "journal": {k: journal_result(mapping(r.get("state")), k) for k in ("objective", "phase", "quest")},
                "facts": get(r, "state", "facts")}
               for r in checks]
    samples = [target_value(mapping(r.get("state")), stage) for r in observed_after_rows]
    first_reached = samples.index(True) if True in samples else None
    remaining = samples[first_reached + 1:] if first_reached is not None else []
    remained = (False if False in remaining else UNKNOWN if not remaining or UNKNOWN in remaining else True)
    return {"before_seq": before_row.get("seq", UNKNOWN),
            "operation_requests": len(requests),
            "requested_operations": [mapping(r.get("detail")) for r in requests],
            "operation_returns": [mapping(r.get("detail")) for r in returns],
            "already_target_events": sum(r.get("event") == "ALREADY_TARGET" for r in rows),
            "rejections": [mapping(r.get("detail")) for r in rows if r.get("event") == "STAGE_REJECTED"],
            "target_before": target_value(before, stage),
            "target_after": target_after,
            "first_observed_target_seq": reached_rows[0].get("seq", UNKNOWN) if reached_rows else UNKNOWN,
            "target_change_observed_after_request": observed_success,
            "interpretation": interpretation,
            "journal_before": {k: journal_result(before, k) for k in ("objective", "phase", "quest")},
            "journal_after": {k: journal_result(after, k) for k in ("objective", "phase", "quest")},
            "journal_state_deltas": {k: delta(journal_state(before, k), journal_state(after, k)) for k in ("objective", "phase", "quest")},
            "tracked_entry_before": get(before, "journal", "tracked"),
            "tracked_entry_after": get(after, "journal", "tracked"),
            "door_before": get(before, "door"), "door_after": get(after, "door"),
            "other_issue_deltas": cross_issue(before, after, stage),
            "fact_deltas": {k: delta(get(before, "facts", k), get(after, "facts", k)) for k in GUARD_FACTS},
            "delayed_checks": delayed,
            "target_remained_true_in_later_samples": remained,
            "stable_at_10s": next((d["target_reached"] for d in reversed(delayed) if number(d["delay_s"]) and d["delay_s"] >= 10), UNKNOWN),
            "hud_updated": UNKNOWN, "interaction_prompt_available": UNKNOWN,
            "normal_player_opening": UNKNOWN, "player_left_clinic": UNKNOWN}


def stage_summary(rows, stage):
    stage_rows = [r for r in rows if r.get("stage") == stage]
    attempts, current = [], []
    for row in stage_rows:
        if row.get("event") == "STAGE_BEFORE" and current:
            attempts.append(attempt_summary(current, stage))
            current = []
        current.append(row)
    if current:
        attempts.append(attempt_summary(current, stage))
    return {"record_count": len(stage_rows), "attempts": attempts}


def fact_history(rows):
    output = {}
    for name in GUARD_FACTS:
        values, changes, unavailable = [], [], 0
        previous = UNKNOWN
        for row in rows:
            value = get(row, "state", "facts", name)
            if not number(value):
                unavailable += 1
                continue
            if not values or values[-1] != value:
                values.append(value)
            if number(previous) and previous != value:
                changes.append({"seq": row.get("seq"), "before": previous, "after": value})
            previous = value
        output[name] = {"observed_values": values, "changes": changes, "unavailable_records": unavailable}
    return output


def session_summary(selected, all_rows):
    """One session only. Kept separate so collection never recursively summarizes."""
    key = identity(selected[-1])
    read_errors = Counter(k for r in selected for k in mapping(r.get("read_errors")))
    baseline = next((r for r in selected if r.get("event") == "BASELINE" and loaded(r)), {})
    return {"probe": PROBE, "run_id": key[0], "session_id": key[1],
            "selected_session_is_latest_record_session": key == identity(all_rows[-1]),
            "records": len(selected), "total_probe_records": len(all_rows),
            "events": dict(Counter(r.get("event", UNKNOWN) for r in selected)),
            "baseline": mapping(baseline.get("state")),
            "journal_repair": stage_summary(selected, "J"),
            "door_repair": stage_summary(selected, "D"),
            "fact_history": fact_history([r for r in selected if loaded(r)]),
            "read_failures": dict(read_errors),
            "errors": [{"seq": r.get("seq"), "detail": r.get("detail")} for r in selected if r.get("event") == "ERROR"],
            "limitations": ["An API return or operation request is not target-state success.",
                            "Snapshots report observed states, not proof of original journal write chronology.",
                            "Stability checks are discrete snapshots, not continuous-state proof.",
                            "HUD visibility, normal door use and clinic exit require human observation.",
                            "No before/after comparisons cross a load session.",
                            "Mock traces validate parsing only; they are not game runtime evidence."]}


def summarize(rows):
    selected, all_rows = select_session(rows)
    result = session_summary(selected, all_rows)
    loaded_keys = []
    for row in all_rows:
        if loaded(row) and (row.get("event") == "BASELINE" or row.get("stage") in {"J", "D"}):
            key = identity(row)
            if key not in loaded_keys:
                loaded_keys.append(key)
    result["loaded_sessions"] = [
        session_summary([row for row in all_rows if identity(row) == key], all_rows)
        for key in loaded_keys
    ]
    result["session_reporting"] = (
        "Top-level result selects the latest loaded baseline/stage session. "
        "loaded_sessions preserves each independently, including original repair "
        "attempts when an optional reload has a later Inspect baseline. "
        "No state deltas or repair results are combined across loads."
    )
    return result


def state_readiness_failures(state):
    problems = []
    if get(state, "player_exists") is not True:
        problems.append("No readable loaded player.")
    for name, expected in GUARD_FACTS.items():
        value = get(state, "facts", name)
        if not number(value) or value != expected:
            problems.append(f"Guard fact {name} is {value!r}, expected {expected}.")
    if get(state, "guard", "passed") is not True:
        problems.append("Probe guard did not pass.")
    if get(state, "in_scene") is not False:
        problems.append("Player scene state is not confirmed false.")
    if not target_verified(state, "J"):
        problems.append("Exact journal hierarchy/target is not verified.")
    for entry in ("objective", "phase", "quest"):
        if (get(state, "journal", entry, "present") is not True
                or not number(journal_state(state, entry))):
            problems.append(f"Journal {entry} is not readable.")
    if not target_verified(state, "D"):
        problems.append("Exact clinic door identity/full identifier is not verified.")
    if not isinstance(get(state, "door", "device", "IsLocked"), bool):
        problems.append("Clinic door lock state is not readable.")
    for stage, readiness in stage_readiness(state).items():
        problems.extend(stage + ": " + problem for problem in readiness["failures"])
    return problems


def stage_readiness(state):
    """Reflect trigger gates without coupling a no-op to unnecessary action gates."""
    j_value = journal_state(state, "objective")
    j_problems = []
    if not number(j_value) or j_value not in (2, 3):
        j_problems.append("Objective is neither Active (repair) nor Succeeded (no-op).")
    locked = get(state, "door", "device", "IsLocked")
    d_problems = []
    if locked is not False:
        if locked is not True:
            d_problems.append("Door lock is UNKNOWN; repair/no-op cannot be selected.")
        if get(state, "door", "controller_verified") is not True:
            d_problems.append("DoorControllerPS is not verified.")
        expected = {"type_interactive": True, "IsInteractive": True,
                    "IsDisabled": False, "IsUnpowered": False, "IsOFF": False,
                    "IsBusy": False, "IsSealed": False, "IsOpen": False}
        for name, value in expected.items():
            actual = get(state, "door", "device", name)
            if actual is not value:
                d_problems.append(f"Door gate {name} is {actual!r}, expected {value!r} for ForceUnlock.")
    return {"J": {"ready": not j_problems, "mode": "ALREADY_TARGET_NO_OP" if j_value == 3 else "REPAIR_CANDIDATE", "failures": j_problems},
            "D": {"ready": not d_problems, "mode": "ALREADY_TARGET_NO_OP" if locked is False else "REPAIR_CANDIDATE", "failures": d_problems}}


def readiness_failures(rows, log_age_s=0, max_log_age_s=30):
    """Fail closed on the actual latest live run/session, never an older baseline."""
    rows = trace_rows(rows)
    if not rows:
        return ["No Phase2B-P2 repair records; probe startup is not verified."]
    problems = []
    if not number(log_age_s) or log_age_s < -5 or log_age_s > max_log_age_s:
        problems.append(f"Trace is stale or timestamp invalid (age {log_age_s!r}s; limit {max_log_age_s}s).")
    last = rows[-1]
    run_rows = [r for r in rows if r.get("run_id") == last.get("run_id")]
    current = [r for r in run_rows if r.get("session_id") == last.get("session_id")]
    if not any(r.get("event") == "INIT" and get(r, "detail", "mode") == "WRITABLE_REPAIR_PROBE_MANUAL_TRIGGERS_ONLY"
               and get(r, "detail", "hooks_registered") is True for r in run_rows):
        problems.append("Current run has no verified writable/manual-only INIT with registered load hooks.")
    if any(r.get("event") == "SHUTDOWN" for r in run_rows):
        problems.append("Probe has shut down; this is not a live readiness check.")
    lifecycle = [r.get("event") for r in current if r.get("event") in {"SESSION_ATTACHED", "SESSION_DETACHED"}]
    if not lifecycle or lifecycle[-1] != "SESSION_ATTACHED":
        problems.append("Latest session is not attached.")
    baselines = [r for r in current if r.get("event") == "BASELINE" and loaded(r)]
    if not baselines:
        problems.append("Current attached session has no loaded Inspect/BASELINE snapshot.")
    else:
        problems.extend("Baseline: " + p for p in state_readiness_failures(mapping(baselines[-1].get("state"))))
    problems.extend("Latest: " + p for p in state_readiness_failures(mapping(last.get("state"))))
    if any(r.get("schema") != 1 for r in run_rows):
        problems.append("Unsupported trace schema in current run.")
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", nargs="?", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-ready", action="store_true")
    parser.add_argument("--log-age", type=float, default=30, metavar="SECONDS",
                        help="Maximum trace age for --check-ready (default: 30).")
    args = parser.parse_args()
    try:
        rows, diagnostics = load_trace(args.log)
        result = summarize(rows)
        result["parse_quality"] = diagnostics
        result["source_log"] = str(args.log)
        if args.check_ready:
            failures = readiness_failures(rows, time.time() - args.log.stat().st_mtime, args.log_age)
            if diagnostics["malformed_lines"]:
                failures.append("Trace contains malformed/truncated lines; preserve the log and inspect before repair.")
            result["readiness"] = {"ready": not failures, "failures": failures,
                                   "latest_stage_readiness": stage_readiness(mapping(rows[-1].get("state"))),
                                   "scope": "Recorder/target reads only; package hashes, disposable fixture and human results are checked separately."}
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
        if args.check_ready:
            failures = result["readiness"]["failures"]
            print("NOT READY: " + " ".join(failures) if failures else "READY: live probe, loaded baseline, guard and exact targets verified. J and D remain manual separate triggers.")
            return 1 if failures else 0
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError) as error:
        print("NOT READY: " + str(error) if args.check_ready else "ERROR: " + str(error))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
