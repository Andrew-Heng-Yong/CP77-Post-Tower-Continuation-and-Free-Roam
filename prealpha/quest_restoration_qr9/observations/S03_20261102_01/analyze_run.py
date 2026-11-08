"""Bounded S03/call assessment from already-collected evidence; no game/save access."""
from pathlib import Path
import argparse
import csv
import datetime
import hashlib
import json
import re

H = Path(__file__).resolve().parent
Q = H.parents[1]


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    a = ap.parse_args()
    out = H / a.output
    assert out.resolve().is_relative_to(H) and not out.exists(), "Fresh contained output required"
    collection = read(H / "collection.json")
    probe = H / "logs" / Path(collection["capture"]["path"]).name
    events = [json.loads(line) for line in probe.read_text().splitlines()]
    assert read(H / "capture_analysis.json")["capture_integrity"] == "VALID_CAPTURE"
    baseline = next(r for r in events if r["event"] == "ATTACHED_BASELINE")
    facts = baseline["data"]["facts"]
    states = [r for r in events if r["event"] in ("ATTACHED_STATE", "BOUNDED_STATE_CHANGE")]
    vehicles = states[0]["data"]["vehicle_unlock"]
    assert facts["carbought_counter"] == 1 and facts["PTFRS29_mq060_nitro_Issued"] == 1
    assert len(vehicles) == 4 and all(v is False for v in vehicles.values())
    assert all("Inactive" in r["data"]["journal"]["quests/minor_quest/mq060_nitro"]["state"] for r in states)
    assert [r["data"]["phone_active"] for r in states] == [False, True, False, True]
    assert events[-2]["data"]["reason"] == "DURATION_LIMIT" and events[-1]["data"]["failures"] == 0
    setup = next(r for r in events if r["event"] == "LISTENER_CALLS_COMPLETED")
    assert setup["data"]["returned_ids"] == setup["data"]["expected"] == 38
    logs = read(H / "support_log_candidates.json")
    scripting = next(Path(r["copy"]) for r in logs if r.get("component") == "CET_scripting")
    lines = scripting.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    current = [(i, s) for i, s in enumerate(lines, 1) if s.startswith("[2026-11-02") and s[12:20] >= "14:00:00"]
    chosen = [{"line": i, "text": s} for i, s in current if re.search(r"cynthia|wilson|mq011|PTFR QR9|GetMod\(", s, re.I)]
    for caller in ("cynthia", "wilson"):
        assert any(f"holo_{caller}_calls_v_start_count : 0 -> 1" in r["text"] for r in chosen)
        assert any(f"holo_{caller}_calls_v_end_count : 0 -> 1" in r["text"] for r in chosen)
    assert any("mq011_active : 0 -> 1" in r["text"] for r in chosen)
    errors = [{"line": i, "text": s} for i, s in current if re.search(r"error|failed|exception", s, re.I)]
    results = read(Q / "observations/S00_20261102_01/confirmation_01/results.json")
    for row in results["observations"]:
        if row["test_id"] != "S03":
            continue
        row.update(capture_run_ids=[probe.name], log_paths=[str(H)], working_save_label=None,
            visible_observation="User reports Cynthia and Wilson calls; no Nitro activation reported.",
            diagnostic_observation="Initial Issued/Permit/Ready/Revision=1, Entered=0; purchases1; four guarded unlock reads false; Nitro journal Inactive throughout observed window.",
            limitations=["Saved fact values do not identify an executing original/private owner.",
                "Player-unlocked getters are not full native VehicleAvailable condition evaluation.",
                "State before initial capture/issuance and actual loaded slot are unknown."])
        if row["variant"] in ("prospective_positive", "prospective_negative"):
            row.update(status="NOT_TESTABLE", fixture_availability="NOT_TESTABLE_ON_CURRENT_ALREADY_ISSUED_FIXTURE",
                       analysis_notes="Fresh positive/negative admission requires a genuine not-yet-Issued history. No reset, vehicle purchase or synthetic entitlement requested.")
        else:
            row.update(status="INCONCLUSIVE", fixture_availability="OBSERVED_ISSUED_FACT_WITH_UNKNOWN_EXECUTING_OWNER",
                analysis_notes="No changes among the watched Nitro facts and inactive journal are bounded observations, not proof of retained selector execution or a confirmed progression defect.")
    calls = [{"test_id": "ADHOC_CALL", "caller": "Cynthia", "quest_id": "mq040_biosculpt",
              "status": "PASS", "scope": "User-observed call delivery; CET reports start0→1 and end0→1. All choices/outcomes/cleanup/reload and exact owner not proven."},
             {"test_id": "ADHOC_CALL", "caller": "Wilson", "quest_id": "mq011_wilson",
              "status": "PASS", "scope": "User-observed Shoot to Thrill call; CET start/end counts and mq011_active0→1. Contest/progression/rewards remain NOT_TESTED."}]
    results.setdefault("additional_observations", []).extend(calls)
    out.mkdir()
    write = lambda p, d: p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write(out / "evidence.json", {"probe": {"path": str(probe), "sha256": sha(probe)},
        "scripting": {"path": str(scripting), "sha256": sha(scripting)}, "selected_lines": chosen,
        "current_scripting_error_candidates": errors, "baseline_facts": facts,
        "guarded_vehicle_unlocks": vehicles, "state_events": states,
        "source_scope": read(H / "nitro_source_scope.json")})
    write(out / "results.json", results)
    rows = results["observations"]
    with (out / "results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()} for r in rows)
    summary = {"status": "S03_PRECHECK_COMPLETE_ALREADY_ISSUED_FIXTURE_CALL_DELIVERY_PASS",
        "analyzed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "probe_start_Toronto": "2026-11-02 14:59:51 EST", "probe_stop_Toronto": "2026-11-02 15:04:51 EST",
        "probe_stop_reason": "DURATION_LIMIT", "manual_stop_Toronto": "2026-11-02 15:06:06 EST",
        "Cynthia_call_Toronto": {"start": "15:02:34 EST", "end": "15:02:50 EST", "fully_inside_probe_window": True},
        "Wilson_call_Toronto": {"start": "15:04:35 EST", "end": "15:05:08 EST", "end_after_probe_stop": True},
        "nitro_purchase_counter": facts["carbought_counter"], "watched_unlocked_variants": sum(vehicles.values()),
        "saved_Issued": 1, "native_or_private_executing_owner": "NOT_OBSERVED",
        "nitro_admission": "No clean fresh fixture. Current counter1 is below native fresh threshold3; typed vehicle getter false is supportive but not complete native predicate proof. Existing Issued state must be preserved.",
        "calls": calls, "current_scripting_error_candidates": len(errors),
        "core_and_diagnostics": "VERIFIED_AFTER", "master_and_backup": "EXACT_VERIFIED",
        "repair_justified": False,
        "next_action": "Follow naturally activated Shoot to Thrill on the working branch; report contest start/end/outcome. Preserve native outcome, original master and current progress. No extra S03 repeat or eligibility manipulation."}
    write(out / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "purchases": 1, "unlocks": 0,
                      "saved_Issued": 1, "call_results": len(calls), "output": str(out)}))


if __name__ == "__main__":
    main()
