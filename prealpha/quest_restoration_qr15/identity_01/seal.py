"""Seal this bounded source investigation; never build or write external files.

Existing successful source controls are reused, not counted as fresh gameplay
or re-executed into occupied outputs. This verifies their hashes and the named
protected inputs, then changes only workspace continuation pointers.
"""
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


def resolve_pin(path, directory):
    path = Path(path)
    if path.is_absolute():
        return path
    return WORK / path if (WORK / path).is_file() else directory / path


def check_manifest(path):
    manifest = read(path)
    for row in manifest["files"]:
        assert sha(resolve_pin(row["path"], path.parent)) == row["sha256"], row["path"]
    for row in manifest.get("source_pins", []):
        assert sha(resolve_pin(row["path"], path.parent)) == row["sha256"], row["path"]
    return len(manifest["files"])


def passed_controls(path):
    data = read(path)
    rows = data["checks"]
    assert rows
    assert all(row.get("pass", row.get("result", row.get("status")) == "PASS") for row in rows), str(path)
    return {"path": str(path), "count": len(rows), "result": "RECORDED_PASS_INPUTS_REUSED"}


def main():
    for name in ["completion.json", "preservation.json", "verification.json", "evidence_manifest_01.json"]:
        assert not (HERE / name).exists(), "Fresh output required"
    # Required final source reports are deliberately named, not chosen by mtime.
    required = [
        HERE / "REPORT.md", HERE / "HANDOFF.md",
        HERE / "entity_origin/verification_02.json",
        HERE / "native_pid/verification_01.json",
        HERE / "native_pid/zero_entries_01/verification_01.json",
        HERE / "vehicle_data_native/verification_01.json",
        HERE / "save_inventory/review_01/verification_01.json",
        HERE / "actor_assignment/evidence_03.json",
        HERE / "actor_assignment/REPORT_03.md",
        HERE / "review_04.json", HERE / "review_04_addendum.json",
        HERE / "native_pid/flags_lifecycle_01/REPORT.md",
        HERE / "native_pid/flags_lifecycle_01/verification_01.json",
    ]
    assert all(p.is_file() for p in required), "Final evidence/report missing"
    for relative in ["review_04.json", "review_04_addendum.json"]:
        path = HERE / relative
        independent_review = read(path)
        assert independent_review["status"] == "PASS" and not independent_review["mismatches"]
        for name, expected in independent_review["pins"].items():
            assert sha(name) == expected, "Independent review input changed: " + name
    native_exe = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077\bin\x64\Cyberpunk2077.exe")
    native_sha = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"
    reader_path = WORK / "research/sidejobs_s28/tooling/wolvenkit_9_1_0/package/WolvenKit.RED4.dll"
    reader_sha = "EF17F40D73F207F0F71F1F41A70A4549A19792D438F680A9BFBB4800D2EE2987"
    assert sha(native_exe) == native_sha and sha(reader_path) == reader_sha
    controls = [passed_controls(p) for p in required if p.name.startswith("verification_")]
    controls.extend(passed_controls(HERE / name) for name in ["review_04.json", "review_04_addendum.json"])
    for p in [HERE / "actor_assignment/evidence_01.json", HERE / "actor_assignment/evidence_02.json", HERE / "actor_assignment/evidence_03.json"]:
        controls.append(passed_controls(p))
    arithmetic = read(HERE / "native_pid/hash_controls_01.json")
    assert arithmetic["all_pass"] and all(r["pass"] for r in arithmetic["controls"])
    manifests = {}
    for relative in [
        "native_pid/manifest_01.json", "native_pid/zero_entries_01/manifest_01.json",
        "save_inventory/review_01/manifest_02.json", "native_pid/flags_lifecycle_01/manifest_01.json",
    ]:
        path = HERE / relative
        manifests[relative] = check_manifest(path)
    for relative in ["entity_origin/verification_02.json", "vehicle_data_native/evidence_01.json"]:
        path = HERE / relative
        for name, expected in read(path).get("pins", {}).items():
            assert sha(resolve_pin(name, path.parent)) == expected, name

    captured = read(HERE / "save_inventory/capture_03/manifest.json")
    assert captured["source_unchanged"] and not captured["candidate_matches"]
    assert captured["ps2_entry_count"] == 116594 and captured["class_counts"]["vehiclePersistentDataPS"] == 200
    assert captured["vehicle_metadata_rows"] == 966 and not captured["ps2_header_ids_contain_raw_target"]
    assert captured["class_counts"]["NULL"] == captured["ps2_entry_duplicate_keys"] + 1
    source_capture = read(BASE / "lifecycle_01/save_community/capture_01/capture.json")
    assert captured["source_sha256"] == source_capture["source_sha256"]
    assert captured["metadata_sha256"] == source_capture["metadata_sha256"]
    assert sha(source_capture["source"]) == source_capture["source_sha256"]
    assert sha(source_capture["metadata"]) == source_capture["metadata_sha256"]

    baseline = read(BASE / "baseline.json")
    protected = {}
    for name in ["installed", "original_saves"]:
        protected[name] = []
        for row in baseline[name]:
            actual = sha(row["path"])
            assert actual == row["sha256"], row["path"]
            protected[name].append({**row, "actual_sha256": actual})
    epoch_path = WORK / "prealpha/quest_restoration_qr13/source_epoch_02.json"
    assert sha(epoch_path) == "A2EABC90B9A30E831703B1121BCD350D1AEA6C07C3453C696BBB5A0D56AED5F6"
    epoch = read(epoch_path)
    candidate = Path(epoch["candidate"])
    expected_sources = {str(Path(name)).casefold() for name in epoch["source_resources"]}
    actual_sources = {str(p.relative_to(candidate / "archive_source")).casefold()
                      for p in (candidate / "archive_source").rglob("*") if p.is_file()}
    assert actual_sources == expected_sources, "Candidate source inventory changed"
    expected_package = {str(Path(row["path"])).casefold() for row in epoch["package_files"]}
    actual_package = {str(p.relative_to(candidate / "package")).casefold()
                      for p in (candidate / "package").rglob("*") if p.is_file()}
    assert actual_package == expected_package, "Candidate package inventory changed"
    for depot, expected in epoch["source_resources"].items():
        assert sha(candidate / "archive_source" / depot) == expected, depot
    for row in epoch["package_files"]:
        assert sha(candidate / "package" / row["path"]) == row["sha256"], row["path"]
    assert sha(epoch["zip"]) == epoch["zip_sha256"]
    decompile = read(BASE / "lifecycle_01/script_source/current_01/manifest.json")
    assert sha(decompile["input"]) == decompile["input_sha256"]
    assert read(WORK / "prealpha/general_gig_probe_gg1/active.json")["state"] == "STOPPED"
    checkpoint = read(BASE / "checkpoint.json")
    prior = checkpoint["latest_lifecycle_step"]["completion"]
    assert sha(prior["path"]) == prior["sha256"]
    fresh(HERE / "preservation.json", {
        "status": "NAMED_CURRENT_RUNTIME_PROTECTED_SAVES_AND_CANDIDATE_UNCHANGED",
        "protected": protected, "source_resources_match": len(epoch["source_resources"]),
        "package_files_match": len(epoch["package_files"]), "zip_match": True,
        "source_and_package_inventories_match": True,
        "source_epoch": pin(epoch_path), "pinned_historical_body_and_metadata_match": True,
        "native_executable_match": True, "save_reader_match": True,
        "base_script_cache_match": True, "proof_manifests_read_back": manifests,
        "prior_lifecycle_completion_match": True, "recorder_state": "STOPPED",
        "runtime_changes": 0, "save_or_fact_writes": 0,
        "limits": "Named six protected originals and one historical body checked; this is not an all-save/live-owner claim. No build/deploy performed.",
    })
    evidence = [pin(p) for p in sorted(HERE.rglob("*")) if p.is_file() and "__pycache__" not in p.parts]
    fresh(HERE / "evidence_manifest_01.json", {
        "status": "SEALED_BOUNDED_SOURCE_EVIDENCE", "files": evidence,
        "runtime_artifact": False, "limits": "Failed/predecessor evidence remains; primary files are selected explicitly in the report.",
    })
    completion = {
        "status": "CANONICAL_CAR_IDENTITY_BOUND_SAVED_SETUP_STAGE_NOT_DISCRIMINATED",
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "evidence_manifest": pin(HERE / "evidence_manifest_01.json"),
        "knowledge_pointers": [pin(WORK / "docs/knowledge/current-state.md"), pin(WORK / "docs/knowledge/native-saved-graph-state.md")],
        "source_controls": controls, "arithmetic_controls_recorded": len(arithmetic["controls"]),
        "controls_limit": "Overlapping static source and extraction controls; do not sum as quest/gameplay coverage.",
        "restoration_complete": False, "runtime_candidate": None, "runtime_changes": 0,
        "save_or_fact_writes": 0, "automated_game_calls": 0, "ready_human_tests": [],
        "canonical_entity_id": "10229047", "native_vehicle_component": "vehiclePersistentDataPS",
        "canonical_native_key_u64": "17113219195054135786", "nonzero_key_matches_in_pinned_body": 0,
        "actual_loaded_body_bound": False, "pending_vs_applied_setup_proven": False,
        "unsafe_diagnostic_rejected": "GetConstAccessToPSObject permits creation/hydration/initialization; not passive.",
        "next": "A non-replaying continuation still needs native setup/queued-event stage evidence or a source-proven route preserving both possible histories. A missing PS key is not a stage certificate; do not repeat JF01/JF02 or weaken U9/HS1.",
        "closed": [
            "Saved associated ID enters the native EntityID/stub namespace unchanged",
            "Exact native PersistentID arithmetic and PS2 entry-key serialization",
            "Canonical native vehiclePersistentDataPS component and stub lookup address",
            "Global four-key membership and retention of all 200 native vehicle-data payloads",
            "Native anonymous-zero filtering and matching parser semantics",
            "Native persistence-selection flag lifecycle refutes PS absence as a setup receipt",
            "Registered population queue and materialization parameter source trace",
            "Const PS lookup is allocation-enabled, unsuitable for a passive diagnostic",
        ],
        "unresolved": [
            "Actual historical/current visual-door and queued-event stage",
            "Complete 16-branch startup preserve/rearm/hold design",
            "Shared courier saved-stage and non-repeating increment contract",
            "Exact body loaded during JF01/JF02 and current executing-owner/physical lease state",
        ],
    }
    fresh(HERE / "completion.json", completion)
    checkpoint["status"] = completion["status"]
    checkpoint["next"] = completion["next"]
    checkpoint["latest_identity_step"] = {"completion": pin(HERE / "completion.json"), "handoff": str(HERE / "HANDOFF.md")}
    (BASE / "checkpoint.json").write_text(json.dumps(checkpoint, indent=2) + "\n", encoding="utf-8")
    queue = read(BASE / "development_queue.json")
    queue["status"] = completion["status"]
    queue["latest_evidence"] = pin(HERE / "completion.json")
    queue["items"][0]["status"] = "CANONICAL_IDENTITY_CLOSED_SETUP_STAGE_HELD"
    queue["items"][0]["required"] = completion["next"]
    for item in completion["closed"]:
        if item not in queue["source_closed"]:
            queue["source_closed"].append(item)
    (BASE / "development_queue.json").write_text(json.dumps(queue, indent=2) + "\n", encoding="utf-8")
    for row in evidence:
        assert sha(row["path"]) == row["sha256"], row["path"]
    fresh(HERE / "verification.json", {
        "status": "PRESERVATION_AND_EVIDENCE_READBACK_PASS_RESTORATION_STILL_HELD",
        "completion": pin(HERE / "completion.json"), "checkpoint": pin(BASE / "checkpoint.json"),
        "queue": pin(BASE / "development_queue.json"), "runtime_candidate": None,
        "restoration_complete": False, "ready_human_tests": [],
    })
    print(json.dumps({"status": completion["status"], "installed_preserved": len(protected["installed"]),
        "protected_originals_preserved": len(protected["original_saves"]), "source_resources_preserved": len(epoch["source_resources"]),
        "package_files_preserved": len(epoch["package_files"]), "runtime_changes": 0, "ready_human_tests": []}))


if __name__ == "__main__":
    main()
