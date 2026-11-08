"""Reproduce the bounded November 2 assessment from collected copies only."""
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
    args = ap.parse_args()
    out = H / args.output
    assert out.resolve().is_relative_to(H) and not out.exists(), "Fresh contained analysis output required"
    collection = read(H / "collection.json")
    integrity = read(H / "capture_analysis.json")
    assert integrity["capture_integrity"] == "VALID_CAPTURE"
    probe = H / "logs" / Path(collection["capture"]["path"]).name
    events = [json.loads(line) for line in probe.read_text().splitlines()]
    assert events[0]["event"] == "CAPTURE_START" and events[-1]["event"] == "LISTENER_CLEANUP_CALLS"
    stop = next(r for r in events if r["event"] == "STOP")
    assert stop["data"]["reason"] == "DURATION_LIMIT" and stop["wall_elapsed_s"] == 300
    setup = next(r for r in events if r["event"] == "LISTENER_CALLS_COMPLETED")
    assert setup["data"]["returned_ids"] == setup["data"]["expected"] == 17
    assert events[-1]["data"]["failures"] == 0

    sources = []
    evidence = []

    def lines(filename):
        p = H / "logs" / filename
        sources.append({"path": str(p), "sha256": sha(p)})
        return p.read_text(encoding="utf-8-sig", errors="replace").splitlines()

    def extract(label, ls, pred):
        found = [{"source": label, "line": i, "text": text} for i, text in enumerate(ls, 1) if pred(text)]
        evidence.extend(found)
        return found

    scripting = lines("CET_scripting_0_scripting.log")
    current = lambda s: s.startswith("[2026-11-02")
    gig = extract("CET_scripting", scripting, lambda s: current(s) and any(t in s for t in
        ["hil_01", "holo_wakako_calls_v_", 'GetMod("PTFR_QR9_Diagnostics")', "[PTFR QR9]"]))
    assert any("hil_01_finished : 0 -> 1" in r["text"] for r in gig)
    assert any("holo_wakako_calls_v_end_count : 5 -> 6" in r["text"] for r in gig)
    scripting_errors = extract("CET_scripting", scripting, lambda s: current(s) and bool(re.search(r"error|failed|exception", s, re.I)))
    archive = lines("ArchiveXL_0_ArchiveXL-2026-11-02-11-39-56.log")
    previous = lines("ArchiveXL_1_ArchiveXL-2026-11-01-00-11-43.log")
    merges = extract("ArchiveXL", archive, lambda s: s.startswith("[2026-11-02 11:44:") and
        any(t in s for t in ["Patching phase", "ronald_news_future.questphase", "studio_support.questphase", "ronald_news_markers.streamingblock"]))
    assert any("Merged phase" in r["text"] and "ronald_news_future.questphase" in r["text"] for r in merges)
    signature = lambda s: re.sub(r"^\[[^]]+\] \[\d+\] ", "", s)
    warnings = lambda ls: {signature(s) for s in ls if "[error]" in s or "[warning]" in s}
    diagnostic_messages = extract("ArchiveXL", archive, lambda s: "[error]" in s or "[warning]" in s)
    new_messages = sorted(warnings(archive) - warnings(previous))
    redscript = lines("REDscript_0_redscript_rCURRENT.log")
    compile_ok = extract("REDscript", redscript, lambda s: "Compilation complete" in s or "Output successfully saved" in s)
    assert len(compile_ok) == 2
    red4ext = lines("RED4ext_0_red4ext-2026-11-02-11-39-55.log")
    shutdown = extract("RED4ext", red4ext, lambda s: "RED4ext has been shut down" in s)
    assert len(shutdown) == 1

    template = read(Q / "worker_c/verification_01/test_results_template.json")
    rows = template["observations"]
    report = read(H / "user_report.json")
    for row in rows:
        if row["test_id"] != "S00":
            continue
        row.update(capture_run_ids=[probe.name], working_save_label=report.get("confirmed_loaded_slot"),
                   visible_observation=report["verbatim"], log_paths=[str(H)],
                   limitations=["Only the first five minutes were captured; gig completion occurred later.",
                       "Loaded-slot identity awaits user confirmation; entity ID and metadata alone do not prove it.",
                       "No standalone map/UI or all-route acceptance is inferred from the user's successful gig."])
        if row["variant"] == "visible_smoke":
            row.update(status="PASS", diagnostic_observation="Main-menu arm, attached player and normal shutdown; user reports entering game and a problem-free gig.",
                       analysis_notes="Bounded user-observed load/play smoke, not full compliance with the exact short no-gig card or exact map check.")
        elif row["variant"] == "registration_attempt":
            row.update(status="PASS", diagnostic_observation="Current-load ArchiveXL logs parent patching and merges of the exact Ronald and studio resources.",
                       analysis_notes="PASS for logged resource merge/startup preparation only. Not successful owner activation or private PIP acquisition.")
        elif row["variant"] == "private_owner_activation":
            row.update(status="INCONCLUSIVE", diagnostic_observation="No actual private-owner execution or numeric engine receipt observation is provided.",
                       analysis_notes="Issued/retired/native facts and resource merge lines do not prove actual owner execution.")
    ad_hoc = {"test_id": "ADHOC_GIG", "quest_id": "sts_wbr_hil_01", "title": "Until Death Do Us Part",
              "status": "PASS", "basis": "User-reported no problems, corroborated by logged deposit receipt, Wakako start/end counters, hil_01_finished transition, and save-metadata completion addition.",
              "quest_identity": "Strong log/metadata correlation; await user confirmation.",
              "scope": "One continued/pre-existing active gig route to completion. Master and working-candidate metadata already track the councilman-apartment stage; fresh admission is not demonstrated.",
              "not_proven": ["Exact native controller identity", "All call audio/notification variants", "Exact reward amount/idempotence", "Fresh restored admission", "Reload after completion", "All branches"]}
    out.mkdir()
    write = lambda p, d: p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write(out / "evidence.json", {"sources": sources + [{"path": str(probe), "sha256": sha(probe)}], "lines": evidence})
    write(out / "results.json", {"schema": "ptfr.qr9.runtime_results.v1", "allowed_statuses": template["allowed_statuses"],
        "binding": template["binding"], "observations": rows, "additional_observations": [ad_hoc],
        "scope": "Fresh successor assessment. Sealed templates remain unchanged. PASS rows have explicit bounded scope."})
    with (out / "results.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, list) else v for k, v in r.items()} for r in rows)
    summary = {"status": "S00_BOUNDED_VISIBLE_AND_RESOURCE_MERGE_PASS_PRIVATE_OWNER_INCONCLUSIVE",
        "analyzed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "probe_window_Toronto": {"start": "2026-11-02 11:44:34 EST", "end": "2026-11-02 11:49:34 EST", "reason": "DURATION_LIMIT"},
        "gig_finished_log_Toronto": "2026-11-02 11:53:34 EST", "manual_stop_command_Toronto": "2026-11-02 11:53:59 EST",
        "probe_rows": len(events), "fact_delivery_rows": sum(r["event"] == "FACT_DELIVERY" for r in events),
        "listener_ids_returned": 17, "cleanup_call_failures": 0,
        "current_scripting_error_candidates": len(scripting_errors),
        "ArchiveXL_prior_error_or_warning_signatures": sorted(warnings(previous)),
        "ArchiveXL_new_error_or_warning_signatures": new_messages,
        "ArchiveXL_message_count": len(diagnostic_messages), "redscript_compilation": "CURRENT_RUN_LOG_SUCCESS",
        "collector_dependency_limit": "LizziesBDs.archive exceeds the collector's64MiB bound and is UNAVAILABLE there; separate Core Verify rehashed all six pinned dependencies successfully.",
        "current_installation": "Core51 and Diagnostics2 VERIFIED_AFTER; master3 and backup exact.",
        "repair_justified": False, "remaining": ["User confirmation of exact gig and loaded slot", "Private graph/owner/receipt/timer/queue/save identity not observed", "Further cards require genuine eligible fixtures; Ronald contact is Inactive/messages0 in this S00 baseline."]}
    write(out / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "gig": ad_hoc["title"], "probe_seconds": 300,
                      "new_ArchiveXL_errors_or_warnings": len(new_messages), "output": str(out)}))


if __name__ == "__main__":
    main()
