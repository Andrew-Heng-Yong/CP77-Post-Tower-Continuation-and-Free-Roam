"""Assess the completed Bullets route from copied probe and broader CET evidence."""
from pathlib import Path
import argparse
import csv
import datetime
import hashlib
import json

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
    assert out.resolve().is_relative_to(H) and not out.exists()
    collected = read(H / "collection.json")
    probe = H / "logs" / Path(collected["capture"]["path"]).name
    rows = [json.loads(s) for s in probe.read_text().splitlines()]
    assert read(H / "capture_analysis.json")["capture_integrity"] == "VALID_CAPTURE"
    journal = []
    for r in rows:
        if r["event"] in ("ATTACHED_STATE", "BOUNDED_STATE_CHANGE"):
            journal.append({"seq": r["seq"], "utc": r["utc"], "state": r["data"]["journal"]["quests/minor_quest/mq030_melisa"]["state"]})
    assert [r["state"] for r in journal] == ["gameJournalEntryState : Inactive (1)", "gameJournalEntryState : Active (2)", "gameJournalEntryState : Succeeded (3)"]
    assert rows[-2]["event"] == "STOP" and rows[-2]["data"]["reason"] == "USER_STOP"
    assert rows[-1]["data"]["failures"] == 0
    sources = read(H / "support_log_candidates.json")
    script = next(Path(r["copy"]) for r in sources if r.get("component") == "CET_scripting")
    lines = script.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    events = [{"line": i, "text": s} for i, s in enumerate(lines, 1)
              if s.startswith("[2026-11-02") and s[12:20] >= "16:18:00"
              and any(t in s for t in ("mq030", "cct_dtn_cloth_01", "[PTFR QR9]", "GetFactStr"))]
    assert any("mq030_maxtac_arrived : 0 -> 1" in r["text"] for r in events)
    assert any("mq030_done : 0 -> 1" in r["text"] for r in events)
    assert any("mq030_active : 1 -> 0" in r["text"] for r in events)
    observed = [r for r in events if "16:28:55" <= r["text"][12:20] <= "16:36:51" and " : " in r["text"] and any(t in r["text"] for t in ("mq030_maxtac_arrived", "mq030_zane_grateful", "mq030_done", "mq030_active"))]
    fact_rows = [r for r in rows if r["event"] == "FACT_DELIVERY"]
    assert len(observed) >= 4 and not fact_rows
    result = read(Q / "observations/WILSON_RELOAD_20261102_01/results.json")
    for r in result["observations"]:
        if r["test_id"] == "S05" and r["variant"] == "handoff_cleanup":
            r.update(status="INCONCLUSIVE", fixture_availability="LIVE_NATIVE_ROUTE_COMPLETED_VENDOR_RETIREMENT_PENDING",
                capture_run_ids=[probe.name], log_paths=[str(H)],
                visible_observation="User reports activation and finished recording; native journal/log/save corroborate quest completion.",
                diagnostic_observation="Journal Inactive→Active→Succeeded; broader CET logs MaxTac/gratitude/done1/active0. No reliable probe fact callbacks or end-of-run private lease query.",
                limitations=["Actual helper retirement/vendor return remains unobserved.", "Fact callback coverage remains unreliable; absence is not gameplay-negative evidence."],
                analysis_notes="Completion is a separate bounded PASS; the full S05 handoff contract remains INCONCLUSIVE pending vendor observation.")
    result["additional_observations"].append({"test_id": "ADHOC_MQ030_COMPLETION", "quest_id": "mq030_melisa", "status": "PASS",
        "scope": "Observed native encounter/MaxTac/dialogue route to Succeeded/done1, corroborated by finished ManualSave-24 metadata. Rewards, vendor lease, all branches and reload are separate unproven contracts."})
    out.mkdir()
    write = lambda p, d: p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write(out / "evidence.json", {"probe": {"path": str(probe), "sha256": sha(probe)},
        "broader_log": {"path": str(script), "sha256": sha(script)}, "events": events, "journal": journal,
        "interpretation": "Multiple attempts/reloads appear before final captured segment; do not concatenate them or infer duplicate completion from reset game clocks.",
        "known_callback_gap": {"watched_broader_transitions_in_probe_window": len(observed), "probe_fact_deliveries": len(fact_rows)}})
    write(out / "results.json", result)
    with (out / "results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(result["observations"][0]))
        writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()} for r in result["observations"])
    summary = {"status": "BULLETS_COMPLETION_PASS_VENDOR_RETIREMENT_AND_RELOAD_PENDING",
        "analyzed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "final_probe_window": "2026-11-02 16:28:55–16:36:51 EST", "probe_stop": "USER_STOP",
        "journal_transitions": journal, "done_callback_Toronto": "16:33:46 EST", "active_zero_callback_Toronto": "16:33:47 EST",
        "native_quest_completed": True, "vendor_return": "NOT_OBSERVED", "vendor_reload": "NOT_TESTED",
        "diagnostic_fact_callbacks": "LIVE_COVERAGE_GAP_PRESERVED; getter/journal and broader logs are separate evidence",
        "runtime_changes": 0, "gameplay_repair_justified": False,
        "next": "User leaves/returns to Jinguji after completed quest, checks normal Zane trade and completed-working-save reload; no quest replay or extra probe command."}
    write(out / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "journal": [r["state"] for r in journal], "callback_gap": True}))


if __name__ == "__main__":
    main()
