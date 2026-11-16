"""Prepare and verify the automatic retained-history test installation."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

from build import (BASE, BASELINE, BASELINE_SHA, CANDIDATE, CHANGES, COMPILE, HERE, SAFE,
                   PACKAGE, PRE, RED, load_module)

EPOCH = "QP2_QUEST_HISTORY_AUTOLOAD"
BEFORE = "QP2_QUEST_HISTORY_TEST"
SCHEMA = "PTFR_QUEST_HISTORY_AUTOLOAD_CORE_V1"
INSTALLER = HERE / "deploy_core.ps1"
MANIFEST = HERE / "core_manifest_01.json"
DEPLOYMENT = HERE / "deployment_01"
JOURNAL = HERE / "recovery/core_quest_history_autoload_01/journal.json"
helper = load_module(SAFE / "build.py", "deployment_helpers")
read, write, sha, one = helper.read, helper.write, helper.sha, helper.one


def prepare(fixture_attempt):
    assert not (HERE / "readiness.json").exists()
    assert sha(BASELINE) == BASELINE_SHA
    baseline = read(BASELINE)
    assert baseline["core_epoch"] == BEFORE
    game = Path(baseline["game_root"])
    compile_result = COMPILE / "result.json"
    readback = CANDIDATE / "test_readback.json"
    verified = CANDIDATE / "verification.json"
    compiled, candidate = read(compile_result), read(verified)
    assert compiled["status"] == candidate["compile"] == "PASS"
    assert read(readback)["status"] == "PASS_SOURCE_AND_LUA_BRIDGE"
    assert compiled["staged_hashes"][RED] == candidate["overlay_sha256"][RED]
    assert {path for path, pin in compiled["staged_hashes"].items()
            if pin != compiled["input_pins"][path]} == {RED}
    files = []
    for item in baseline["core_files"]:
        rel = item["path"]
        assert sha(game / rel) == item["sha256"]
        staged = PACKAGE / rel
        after = sha(staged)
        assert after == candidate["overlay_sha256"].get(rel, item["sha256"])
        files.append({"path": rel, "before": item["sha256"], "before_bytes": item["bytes"],
                      "after": after, "after_bytes": staged.stat().st_size})
    assert len(files) == 51 and {row["path"] for row in files if row["after"] != row["before"]} == CHANGES
    template = BASE / "deploy_core.ps1"
    assert sha(template) == "1FFA0DD0685D4F1890DCC361FBB5435BEC8C91A7A040E75326DDF7217A085CCB"
    scope = "Fix the snapshot test crash and select verified pre-ending history automatically for the requested AutoSave-2 test."
    fixture = read(HERE / "autosave_2_readback.json")
    target = Path(baseline["save_root"]) / fixture["fixture"] / "sav.dat"
    assert sha(target) == fixture["save_sha256"]
    manifest = {
        "schema": SCHEMA, "component": "Core", "source_epoch": EPOCH, "predecessor_epoch": BEFORE,
        "scope": scope, "game_root": str(game), "save_root": baseline["save_root"],
        "package_root": str(PACKAGE), "process_names": read(BASE / "core_manifest_01.json")["process_names"],
        "files": files, "changing_paths": sorted(CHANGES), "required_files": baseline["required_files"],
        "protected_saves": [], "zip": "", "zip_sha256": None,
        "working_save_files": [{"path": f'{fixture["fixture"]}/sav.dat',
                                "sha256": fixture["save_sha256"], "bytes": target.stat().st_size}],
        "proofs": [{"path": str(path), "sha256": sha(path)} for path in
                   (BASELINE, compile_result, readback, verified, CANDIDATE / "source.patch",
                    HERE / "autosave_2_readback.json")],
        "compile_inputs": {str(game / path): pin for path, pin in compiled["input_pins"].items()},
    }
    if MANIFEST.exists():
        assert read(MANIFEST) == manifest
    else:
        write(MANIFEST, manifest)
    script = template.read_text(encoding="utf-8-sig")
    for old, new in (
        (sha(BASE / "core_manifest_01.json"), sha(MANIFEST)),
        ("PTFR_QUEST_HISTORY_TEST_CORE_V1", SCHEMA),
        ("$manifest.source_epoch -cne 'QP2_QUEST_HISTORY_TEST'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'QP2_TOWER_EVENING_RECOVERY'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ("recovery/core_quest_history_test_01", "recovery/core_quest_history_autoload_01"),
    ):
        script = one(script, old, new)
    if INSTALLER.exists():
        assert INSTALLER.read_text(encoding="utf-8") == script
    else:
        with INSTALLER.open("x", encoding="utf-8", newline="\n") as destination:
            destination.write(script)
    harness_path = PRE / "tower_recovery_profile_hold_20261111_01/deploy.py"
    assert sha(harness_path) == "05F0A78C9951F20788B318D1EF348B53BEA882C235E178843AF0B38396A832DB"
    current_build = sys.modules["build"]
    sys.modules["build"] = load_module(harness_path.with_name("build.py"), "profile_fixture_helpers")
    try:
        harness = load_module(harness_path, "test_overlay_fixtures")
    finally:
        sys.modules["build"] = current_build
    harness.INSTALLER = INSTALLER
    harness.CHANGES = CHANGES
    harness.FIXTURES = HERE / f"fixtures/deployment_{fixture_attempt:02}"
    actions = harness.run_fixtures({**manifest, "working_save_files": []})
    fixtures, review = HERE / "fixture_results.json", HERE / "scope_review.json"
    write(fixtures, {"status": "PASS", "installer_sha256": sha(INSTALLER), "actions": actions})
    write(review, {"scope": scope, "changed_paths": sorted(CHANGES), "manifest_sha256": sha(MANIFEST)})
    write(HERE / "readiness.json", {
        "status": "READY_NOT_INSTALLED", "manifest_sha256": sha(MANIFEST), "installer_sha256": sha(INSTALLER),
        "fixture_result": fixtures.name, "fixture_result_sha256": sha(fixtures),
        "scope_review": review.name, "scope_review_sha256": sha(review),
    })
    print(f"Prepared the history test. {len(actions)} transaction fixture actions passed.")


def record():
    baseline, manifest, envelope = read(BASELINE), read(MANIFEST), read(JOURNAL)
    payload = envelope["payload_json"]
    assert sha256(payload.encode()).hexdigest().upper() == envelope["payload_sha256"]
    journal = json.loads(payload)
    assert journal["manifest_sha256"] == sha(MANIFEST) and journal["state"] == "INSTALLED_VERIFIED"
    assert set(journal["completed_paths"]) == CHANGES
    assert read(DEPLOYMENT / "verify.json")["status"] == "VERIFIED_AFTER"
    assert read(DEPLOYMENT / "rollback_readiness.json")["status"] == "ROLLBACK_READY"
    before, after = journal["protection_before"], journal["protection_after"]
    assert before["saves"]["tree_sha256"] == after["saves"]["tree_sha256"]
    assert before["unmanaged"]["tree_sha256"] == after["unmanaged"]["tree_sha256"]
    assert before["dependencies"] == after["dependencies"]
    assert journal["save_writes"] == journal["game_launches"] == 0
    game = Path(manifest["game_root"])
    files = [{"path": item["path"], "bytes": item["after_bytes"], "sha256": item["after"]}
             for item in manifest["files"]]
    assert all(sha(game / item["path"]) == item["sha256"] for item in files + manifest["required_files"])
    save_count = sum(item["kind"] == "file" for item in after["saves"]["files"])
    write(DEPLOYMENT / "installed_manifest_01.json", {
        **baseline, "recorded_date": journal["updated_utc"][:10], "core_epoch": EPOCH,
        "predecessor_epoch": BEFORE, "authorization": manifest["scope"], "core_files": files,
        "source_candidate": str(CANDIDATE), "predecessor_manifest": str(BASELINE),
        "predecessor_manifest_sha256": BASELINE_SHA, "core_transaction": str(MANIFEST),
        "core_transaction_sha256": sha(MANIFEST), "installed_receipt": str(JOURNAL),
        "installed_receipt_sha256": sha(JOURNAL), "post_install_verification": str(DEPLOYMENT / "verify.json"),
        "rollback_readiness": str(DEPLOYMENT / "rollback_readiness.json"),
        "compile_result": str(COMPILE / "result.json"), "compile_sources": read(COMPILE / "result.json")["source_count"],
        "changed_paths": sorted(CHANGES), "unchanged_core_paths": 49, "save_files_preserved": save_count,
        "save_tree_sha256": after["saves"]["tree_sha256"], "gameplay": "UNVERIFIED_AUTOSAVE_2_ENDING_CONTINUATION",
    })
    print(f"Verified the installed override and {save_count} preserved save files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "record"))
    parser.add_argument("--fixture-attempt", type=int, default=1)
    args = parser.parse_args()
    if args.action == "prepare":
        prepare(args.fixture_attempt)
    else:
        record()
