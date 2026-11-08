"""Seal the bounded source result and named preservation checks, workspace only."""
from pathlib import Path
import datetime
import hashlib
import json

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
WORK = BASE.parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def pin(path):
    return {"path": str(Path(path).resolve()), "sha256": sha(path)}


def fresh(path, data):
    assert not path.exists(), "Fresh output required: " + str(path)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def manifest_check(path):
    data = read(path)
    for row in data["files"] + data.get("source_pins", []):
        source = Path(row["path"])
        if not source.is_absolute():
            source = (WORK / source) if (WORK / source).is_file() else path.parent / source
        assert sha(source) == row["sha256"], str(source)
    return len(data["files"])


def control_count(path):
    data = read(path)
    checks = data["checks"]
    assert checks and all(row.get("pass", row.get("result", row.get("status")) == "PASS") for row in checks), str(path)
    return {"evidence": pin(path), "recorded_controls": len(checks), "scope": "Static source, framing or review; not gameplay"}


def main():
    for name in ["preservation.json", "completion.json", "verification.json", "evidence_manifest_01.json"]:
        assert not (HERE / name).exists(), "Fresh final output required"
    for name in ["REPORT.md", "HANDOFF.md", "quest_handlers/REPORT.md", "quest_handlers/verification_01.json",
                 "quest_handlers/manifest_01.json", "vehicle_events/manifest_01.json", "review_01.json"]:
        assert (HERE / name).is_file(), "Final source/review missing: " + name
    review = read(HERE / "review_01.json")
    assert review["status"] == "PASS_BOUNDED_SOURCE_CAPTURE_AND_MEMBERSHIP_REVIEW_FINAL_SEAL_PENDING" and not review["mismatches"], "Independent review not passed"
    assert all(row["result"] == "PASS" for row in review["checks"])
    for row in review["input_pins"]:
        assert sha(row["path"]) == row["sha256"], "Independent review source changed: " + row["path"]
    vehicle_manifest = read(HERE / "vehicle_events/manifest_01.json")
    vehicle_verification = HERE / "vehicle_events" / vehicle_manifest["current_verification"]
    control_sources = [HERE / "analysis_01.json", HERE / "native_layout_01.json",
                       HERE / "quest_handlers/verification_01.json", vehicle_verification]
    controls = [control_count(path) for path in control_sources]
    vehicle_source = read(HERE / "vehicle_events/source_contract_01.json")
    for row in vehicle_source["source_pins"]:
        assert sha(row["path"]) == row["sha256"]
    assert sha(vehicle_source["graph"]["raw"]) == vehicle_source["graph"]["sha256"]
    assert sha(vehicle_source["graph"]["json"]) == vehicle_source["graph"]["json_sha256"]
    manifest_readback = {name: manifest_check(HERE / name) for name in ["quest_handlers/manifest_01.json", "vehicle_events/manifest_01.json"]}
    extraction = read(HERE / "components_01/manifest.json")
    assert extraction["source_unchanged"] and all(row["pass"] for row in extraction["checks"])
    for row in extraction["nodes"]:
        assert sha(row["path"]) == row["sha256"]
    assert sha(extraction["source"]) == extraction["source_sha256"]
    assert sha(extraction["metadata"]) == extraction["metadata_sha256"]
    source_scan = read(HERE / "registered_override_scan_01.json")
    for row in source_scan["pins"]:
        assert sha(row["path"]) == row["sha256"], row["path"]
    # Current registered inventory is checked by the scan; these pins are not
    # interpreted as proof about an executing cache or dynamic runtime hooks.
    baseline = read(BASE / "baseline.json")
    protected = {}
    for kind in ["installed", "original_saves"]:
        protected[kind] = []
        for row in baseline[kind]:
            actual = sha(row["path"])
            assert actual == row["sha256"], row["path"]
            protected[kind].append({**row, "actual_sha256": actual})
    epoch_path = WORK / "prealpha/quest_restoration_qr13/source_epoch_02.json"
    assert sha(epoch_path) == "A2EABC90B9A30E831703B1121BCD350D1AEA6C07C3453C696BBB5A0D56AED5F6"
    epoch = read(epoch_path)
    candidate = Path(epoch["candidate"])
    source_expected = {str(Path(name)).casefold() for name in epoch["source_resources"]}
    source_actual = {str(path.relative_to(candidate / "archive_source")).casefold() for path in (candidate / "archive_source").rglob("*") if path.is_file()}
    package_expected = {str(Path(row["path"])).casefold() for row in epoch["package_files"]}
    package_actual = {str(path.relative_to(candidate / "package")).casefold() for path in (candidate / "package").rglob("*") if path.is_file()}
    assert source_actual == source_expected and package_actual == package_expected
    for depot, expected in epoch["source_resources"].items():
        assert sha(candidate / "archive_source" / depot) == expected, depot
    for row in epoch["package_files"]:
        assert sha(candidate / "package" / row["path"]) == row["sha256"], row["path"]
    assert sha(epoch["zip"]) == epoch["zip_sha256"]
    base_source = read(BASE / "lifecycle_01/script_source/current_01/manifest.json")
    assert sha(base_source["input"]) == base_source["input_sha256"]
    assert sha(Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe")) == "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"
    assert sha(WORK / "research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/WolvenKit.RED4.dll") == extraction["reader_sha256"]
    assert read(WORK / "prealpha/general_gig_probe_gg1/active.json")["state"] == "STOPPED"
    checkpoint = read(BASE / "checkpoint.json")
    previous = checkpoint["latest_identity_step"]["completion"]
    assert sha(previous["path"]) == previous["sha256"]
    # Reused sealed identity evidence is immutable. Curated docs/checkpoints
    # are intentionally updated, and historical hashes are not rewritten.
    previous_evidence = read(BASE / "identity_01/evidence_manifest_01.json")
    for row in previous_evidence["files"]:
        assert sha(row["path"]) == row["sha256"], row["path"]
    fresh(HERE / "preservation.json", {
        "status": "NAMED_RUNTIME_SAVES_AND_CONSOLIDATED_CANDIDATE_PRESERVED", "protected": protected,
        "source_resources_match": len(epoch["source_resources"]), "package_files_match": len(epoch["package_files"]),
        "source_and_package_inventories_match": True, "zip_match": True, "source_epoch": pin(epoch_path),
        "historical_body_and_metadata_match": True, "base_script_cache_match": True, "native_executable_and_reader_match": True,
        "registered_reds_sources_match_capture": len(source_scan["pins"]), "prior_identity_evidence_unchanged": True,
        "proof_manifests_read_back": manifest_readback, "recorder_state": "STOPPED",
        "runtime_changes": 0, "save_or_fact_writes": 0,
        "limits": "Named six protected originals and one historical body, not all saves or any current executing owner. No compile/rebuild/deploy.",
    })
    files = [pin(path) for path in sorted(HERE.rglob("*")) if path.is_file() and "__pycache__" not in path.parts]
    fresh(HERE / "evidence_manifest_01.json", {"status": "SEALED_HANDLER_AND_EVENT_STAGE_EVIDENCE", "files": files, "runtime_artifact": False})
    completion = {
        "status": "NO_SAFE_SETUP_CERTIFICATE_IN_REVIEWED_HANDLER_EVENT_PROJECTIONS",
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "evidence_manifest": pin(HERE / "evidence_manifest_01.json"), "controls": controls,
        "extraction_controls": len(extraction["checks"]), "independent_review": pin(HERE / "review_01.json"),
        "controls_limit": "Overlapping static checks, not aggregate quest coverage or gameplay proof.",
        "restoration_complete": False, "confirmed_runtime_defect": False, "runtime_candidate": None,
        "runtime_changes": 0, "save_or_fact_writes": 0, "automated_game_calls": 0, "ready_human_tests": [],
        "decision": "Prepared Jason state remains unsupported. No safe replay/skip or admission exemption is justified.",
        "source_closed": [
            "Interned phase paths retained through cut are not active-owner/completion receipts",
            "Saved handler removal clears reusable identity slots; no finished-node history",
            "Exact original descendant and parent-context owner addresses queried",
            "Full32 nodeID query avoids managed low16 alias; current results independently checked",
            "103/104 advance without final visual/door application acknowledgement",
            "Source-bound wrapper, door-state and destruction-state component owners distinguished",
            "PersistencySystem own save/load does not serialize its live request ring",
        ],
        "unresolved": [
            "Exact visual/door application history and actual loaded JF01/JF02 body",
            "Higher-level save barriers, actor event-queue persistence and actual Tower queue scheduling",
            "Opaque saved subtype contents in other selected support/state blocks",
            "Full startup and shared-courier preservation contract for a non-replaying adapter",
        ],
        "next": "Keep this prepared instance deferred unless new positive genuine-stage evidence or a source-proven continuation preserving both histories becomes available. Do not repeat rejected key/path/queue/flag probes or successful gameplay tests.",
        "knowledge_pointers": [pin(WORK / "docs/knowledge/current-state.md"), pin(WORK / "docs/knowledge/native-saved-graph-state.md")],
    }
    fresh(HERE / "completion.json", completion)
    checkpoint["status"] = completion["status"]
    checkpoint["next"] = completion["next"]
    checkpoint["latest_event_stage"] = {"completion": pin(HERE / "completion.json"), "handoff": str(HERE / "HANDOFF.md")}
    (BASE / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    queue = read(BASE / "development_queue.json")
    queue["status"] = completion["status"]
    queue["latest_evidence"] = pin(HERE / "completion.json")
    queue["items"][0]["status"] = "REVIEWED_STAGE_INDICATORS_INSUFFICIENT_PREPARED_INSTANCE_DEFERRED"
    queue["items"][0]["required"] = completion["next"]
    for finding in completion["source_closed"]:
        if finding not in queue["source_closed"]:
            queue["source_closed"].append(finding)
    (BASE / "development_queue.json").write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    for row in files:
        assert sha(row["path"]) == row["sha256"]
    fresh(HERE / "verification.json", {
        "status": "SOURCE_REVIEW_PRESERVATION_AND_FINAL_READBACK_PASS_NO_REPAIR_SELECTED",
        "completion": pin(HERE / "completion.json"), "checkpoint": pin(BASE / "checkpoint.json"), "queue": pin(BASE / "development_queue.json"),
        "restoration_complete": False, "runtime_candidate": None, "ready_human_tests": [],
    })
    print(json.dumps({"status": completion["status"], "installed_preserved": len(protected["installed"]),
        "protected_original_files_preserved": len(protected["original_saves"]), "candidate_sources_preserved": len(epoch["source_resources"]),
        "package_leaves_preserved": len(epoch["package_files"]), "runtime_changes": 0, "ready_human_tests": []}))


if __name__ == "__main__":
    main()
