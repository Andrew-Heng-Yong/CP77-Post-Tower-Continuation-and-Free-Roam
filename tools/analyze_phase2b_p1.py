"""Summarize a read-only reload trace. Never interprets saved P0 markers as execution."""
import argparse
import json
from collections import Counter
from pathlib import Path


def mapping(value):
    # CET may encode an empty Lua table as [] rather than {}.
    return value if isinstance(value, dict) else {}


def summarize(rows):
    if not rows:
        raise ValueError("No Phase2B-P1 records")
    run = rows[-1]["run_id"]
    rows = [r for r in rows if r["run_id"] == run]
    failures = Counter()
    transitions = []
    loaded = []
    contexts = []
    for row in rows:
        state = mapping(row.get("state"))
        detail = mapping(row.get("detail"))
        errors = row.get("read_errors") or {}
        if isinstance(errors, dict):
            failures.update(errors.keys())
        if row["event"] in {"TIER_PAIR_CHANGE", "SCENE_TIER_CALLBACK", "HIGHLEVEL_CORRECTION_PENDING", "SCENE_TIER_DATA_CALL", "SCENE_TIER_CONTEXT_CALL"} or row["event"].startswith("PSM_TIER_WRITE"):
            transitions.append({k: row.get(k) for k in ("seq", "elapsed_s", "frame", "event", "detail")})
        if state.get("facts", {}).get("PostTowerFreeRoamActive") == 1 and state.get("player_exists") is True:
            loaded.append(row)
        if isinstance(detail.get("request"), dict):
            contexts.append(row)
    latest = loaded[-1].get("state", {}) if loaded else {}
    return {"run_id": run, "records": len(rows), "post_tower_records": len(loaded),
            "events": dict(Counter(r["event"] for r in rows)), "transitions": transitions,
            "context_records_with_readable_request": len(contexts),
            "latest_post_tower_state": latest, "read_failures": dict(failures),
            "callback_delivery": mapping(rows[-1].get("detail")).get("callbacks_delivered", "See HEARTBEAT"),
            "limitations": ["No native scene resource/instance enumeration.",
                            "Registration does not prove native engine-hook delivery.",
                            "Frame polling alone can miss multiple changes within a frame.",
                            "Door state belongs to recorded look target, not an assumed NodeRef."]}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("log", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    rows, bad = [], 0
    for line in args.log.read_text(encoding="utf-8-sig").splitlines():
        try:
            row = json.loads(line)
            if isinstance(row, dict) and row.get("probe") == "Phase2B-P1-readonly":
                rows.append(row)
            elif not isinstance(row, dict):
                bad += 1
        except (ValueError, TypeError):
            bad += 1
    result = summarize(rows)
    result["malformed_lines"] = bad
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
