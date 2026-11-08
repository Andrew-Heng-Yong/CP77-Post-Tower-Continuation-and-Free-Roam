"""Bind the reviewed two-file transaction to QR13:02 and the sealed QR18 ZIP."""
from pathlib import Path
import zipfile
import hashlib

from build import HERE, QR17, SCRIPT, read, sha, checked, write

QR14 = HERE.parent / "quest_restoration_qr14"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
ALLOWED = [ARCHIVE, SCRIPT]
TRANSACTION = "core_manifest_01.json"
RECOVERY = "recovery/core_qr18_01"
ZIP_SHA = "8E18F13ECBADF92BEE45C34874B5FA6AE215FFB6F92DD5D6B04124923709C10E"
BASE_ENGINE = "8DE067549901CD3AD6E41AE88F35DBAE4967DC6DEDAADADFF79CF6BB8E2A9A08"
BASE_MANIFEST = "6963CB2679BF3D0ABD9F34A662C437A185D0FBA10873913B6AEC7EC4F76299C0"


def prepare():
    assert not any((HERE / name).exists() for name in (TRANSACTION, "deploy_core.ps1", RECOVERY))
    candidate_path = HERE / "candidate_01/package_manifest.json"
    candidate = read(candidate_path)
    assert candidate["status"] == "STAGED_QR18_READBACK_VERIFIED_NOT_INSTALLED"
    assert candidate["zip_sha256"] == ZIP_SHA and candidate["changed_paths"] == ALLOWED
    package = candidate_path.parent / "package"
    installed_path = QR14 / "deployment_01/installed_manifest_01.json"
    installed = read(installed_path)
    assert installed["core_epoch"] == "QR13:02"
    base = read(checked(QR14 / "core_manifest_02.json", BASE_MANIFEST))
    assert installed["game_root"] == base["game_root"] and installed["save_root"] == base["save_root"]
    assert installed["required_files"] == base["required_files"]
    game = Path(installed["game_root"])
    save = Path(installed["save_root"])
    before = {r["path"]: r for r in installed["core_files"]}
    after = {r["path"]: r for r in candidate["files"]}
    assert len(before) == len(after) == 51 and set(before) == set(after)
    assert sorted(k for k in before if before[k]["sha256"] != after[k]["sha256"]) == ALLOWED
    assert set(after) == {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    zip_path = checked(candidate["zip"], ZIP_SHA)
    with zipfile.ZipFile(zip_path) as z:
        assert len(z.namelist()) == len(after) and set(z.namelist()) == set(after) and z.testzip() is None
        for path, row in after.items():
            checked(package / path, row["sha256"])
            checked(game / path, before[path]["sha256"])
            assert len(z.read(path)) == row["bytes"]
            assert hashlib.sha256(z.read(path)).hexdigest().upper() == row["sha256"]
    for row in base["required_files"]:
        checked(game / row["path"], row["sha256"])
    for row in base["protected_saves"] + base["working_save_files"]:
        checked(save / row["path"], row["sha256"])
    compile_path = HERE / "compile_01/result.json"
    compile_result = read(compile_path)
    assert compile_result["status"] == "PASS_CURRENT_INPUT_OFFLINE_COMPILE" and compile_result["source_count"] == 148
    assert compile_result["candidate_script_sha256"] == after[SCRIPT]["sha256"]
    compiler_pins = compile_result["input_pins"]
    assert len(compiler_pins) == 151
    for path, digest in compiler_pins.items():
        checked(path, digest)
    compiled = checked(HERE / "compile_01/cache/compiled.redscripts", compile_result["output_sha256"])
    archive_path = HERE / "archive_readback.json"
    archive = read(archive_path)
    assert archive["status"] == "PASS_ALL_ARCHIVE_MEMBERS" and archive["archive_sha256"] == after[ARCHIVE]["sha256"]
    assert len(archive["resources"]) == len(candidate["source_resources"]) == 1577
    assert {r["depot"]: r["sha256"] for r in archive["resources"]} == candidate["source_resources"]
    graph_path = HERE / "verification.json"
    graph = read(graph_path)
    assert graph["status"] == "PASS_SERIALIZED_HANDOFF_CONTRACT"
    assert graph["resource_sha256"] == candidate["source_resources"][candidate["changed_depots"][0]]
    proof_paths = [candidate_path, compile_path, compiled, archive_path, graph_path, installed_path, QR14 / "core_manifest_02.json"]
    manifest = base | {
        "schema": "PTFR_QR18_CORE_V1", "source_epoch": "QR18", "predecessor_epoch": "QR13:02",
        "package_root": str(package), "zip": str(zip_path), "zip_sha256": ZIP_SHA,
        "files": [{"path": k, "before": before[k]["sha256"], "before_bytes": before[k]["bytes"],
                   "after": after[k]["sha256"], "after_bytes": after[k]["bytes"]} for k in sorted(before)],
        "changing_paths": ALLOWED, "compile_inputs": compiler_pins,
        "compile_coverage": {"sources": 148, "input_pins": len(compiler_pins), "compiled_sha256": sha(compiled)},
        "proofs": [{"path": str(p), "sha256": sha(p)} for p in proof_paths],
        "scope": "Replace only the existing consolidated archive and S23 script. Preserve XL, diagnostics, saves, cache and external mods.",
        "rollback_policy": "Restore the two exact QR13:02 files from the current transaction. File rollback cannot undo save progress.",
    }
    write(HERE / TRANSACTION, manifest)
    engine = checked(QR14 / "deploy_core.ps1", BASE_ENGINE).read_text(encoding="utf-8-sig")
    changes = {
        "# QR14 preparation: real mutations require separate user authorization. Fixtures stay in QR14/fixtures.": "# QR18 deployment. Real mutations require authorization. Fixtures stay under this task.",
        "# Derived from inspected QR11 transaction; only three existing Core leaves may change.": "# Derived from the QR14 transaction. Only two existing Core files may change.",
        "# A three-file replacement is journaled, with per-file atomic replacement; Windows": "# The two-file replacement is journaled, with per-file atomic replacement; Windows",
        "$PinnedCoreManifestSHA='" + BASE_MANIFEST + "'": "$PinnedCoreManifestSHA='" + sha(HERE / TRANSACTION) + "'",
        "PTFR_QR14_JOURNAL_V1": "PTFR_QR18_JOURNAL_V1",
        "'core_manifest_02.json'": "'" + TRANSACTION + "'",
        "'PTFR_QR14_CORE_V1'": "'PTFR_QR18_CORE_V1'",
        "$manifest.source_epoch -cne 'QR13:02' -or $manifest.predecessor_epoch -cne 'QR8:02'":
            "$manifest.source_epoch -cne 'QR18' -or $manifest.predecessor_epoch -cne 'QR13:02'",
        "('recovery/core_qr13_02_01')": "('" + RECOVERY + "')",
        "'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds',": "",
        "$changes.Count -ne 3": "$changes.Count -ne 2",
        "Core51/three-existing-leaf scope drift": "Core51/two-existing-file scope drift",
    }
    for old, new in changes.items():
        assert old in engine, old
        engine = engine.replace(old, new)
    with (HERE / "deploy_core.ps1").open("x", encoding="utf-8", newline="\n") as f:
        f.write(engine)
    write(HERE / "installer_review.json", {
        "status": "PASS_QR18_REVIEWED_TRANSACTION_DELTA", "predecessor_installer_sha256": BASE_ENGINE,
        "installer_sha256": sha(HERE / "deploy_core.ps1"), "manifest_sha256": sha(HERE / TRANSACTION),
        "allowed_replacements": ALLOWED, "exact_verified_zip": ZIP_SHA,
        "engine_delta": list(changes.values()),
        "review_scope": "Identity, two-file allowlist and recovery namespace only. Locks, containment, journal, write path, process guard and recovery are inherited.",
    })
    print(f"Prepared a two-file transaction. Manifest SHA256 {sha(HERE / TRANSACTION)}")


if __name__ == "__main__":
    prepare()
