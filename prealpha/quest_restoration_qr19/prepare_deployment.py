"""Bind the reviewed two-file transaction to QR18 and the sealed QR19 ZIP."""
from pathlib import Path
import zipfile
import hashlib

from build import HERE, QR18, SCRIPT, DEPOTS, read, sha, checked, write

ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
ALLOWED = [ARCHIVE, SCRIPT]
TRANSACTION = "core_manifest_01.json"
RECOVERY = "recovery/core_qr19_01"
ZIP_SHA = "CBED68B9868EDDD5A3F097DBD45F4D6A48E0C7E51327A5DCF975B41FB733521E"
BASE_ENGINE = "D93DC0001B2B5CC1751BE4CB9DE3DF4A3E92EF93F252CFB407411161238AA17B"
BASE_MANIFEST = "E38145F3C7D3A2CCDE265017972FFEF4BCF5B7677B1BF6A7CAFC661BCCE952DD"
BASE_INSTALLED = "4E128EDB80D690C871480BFA7DF21FDA78251EF1590D2299AEF1AEE7D64840F2"
CANDIDATE_MANIFEST = "7259E12EABB61A8253F50A22BE6198DA7CFECA65692D99C37AE7283F2ADE942D"


def prepare():
    assert not any((HERE / name).exists() for name in (TRANSACTION, "deploy_core.ps1", RECOVERY))
    candidate_path = HERE / "candidate_01/package_manifest.json"
    candidate = read(checked(candidate_path, CANDIDATE_MANIFEST))
    assert candidate["status"] == "STAGED_QR19_READBACK_VERIFIED_NOT_INSTALLED"
    assert candidate["zip_sha256"] == ZIP_SHA and candidate["changed_paths"] == ALLOWED
    package = candidate_path.parent / "package"
    installed_path = QR18 / "deployment_01/installed_manifest_01.json"
    installed = read(checked(installed_path, BASE_INSTALLED))
    assert installed["core_epoch"] == "QR18"
    base_path = checked(QR18 / TRANSACTION, BASE_MANIFEST)
    base = read(base_path)
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
    compile_path = HERE / "compile_deployment_01/result.json"
    compile_result = read(compile_path)
    assert compile_result["status"] == "PASS_CURRENT_INPUT_OFFLINE_COMPILE" and compile_result["source_count"] == 148
    assert compile_result["candidate_script_sha256"] == after[SCRIPT]["sha256"]
    compiler_pins = compile_result["input_pins"]
    assert len(compiler_pins) == 151
    for path, digest in compiler_pins.items():
        checked(path, digest)
    compiled = checked(HERE / "compile_deployment_01/cache/compiled.redscripts", compile_result["output_sha256"])
    archive_path = HERE / "archive_readback.json"
    archive = read(archive_path)
    assert archive["status"] == "PASS_ALL_ARCHIVE_MEMBERS" and archive["archive_sha256"] == after[ARCHIVE]["sha256"]
    assert len(archive["resources"]) == len(candidate["source_resources"]) == 1577
    assert {r["depot"]: r["sha256"] for r in archive["resources"]} == candidate["source_resources"]
    graph_path = HERE / "verification.json"
    graph = read(graph_path)
    assert graph["status"] == "PASS_QR19_TYPED_SMS_HANDOFF"
    assert set(candidate["changed_depots"]) == set(DEPOTS)
    prior = read(checked(installed["core_source_epoch"], installed["core_source_epoch_sha256"]))["source_resources"]
    current = candidate["source_resources"]
    assert prior.keys() == current.keys()
    assert {d for d in prior if prior[d] != current[d]} == set(DEPOTS)
    assert graph["resource_hashes"] == {d: current[d] for d in DEPOTS}
    proof_paths = [candidate_path, compile_path, compiled, archive_path, graph_path, installed_path, base_path]
    manifest = base | {
        "schema": "PTFR_QR19_CORE_V1", "source_epoch": "QR19", "predecessor_epoch": "QR18",
        "package_root": str(package), "zip": str(zip_path), "zip_sha256": ZIP_SHA,
        "files": [{"path": k, "before": before[k]["sha256"], "before_bytes": before[k]["bytes"],
                   "after": after[k]["sha256"], "after_bytes": after[k]["bytes"]} for k in sorted(before)],
        "changing_paths": ALLOWED, "compile_inputs": compiler_pins,
        "compile_coverage": {"sources": 148, "input_pins": len(compiler_pins), "compiled_sha256": sha(compiled)},
        "proofs": [{"path": str(p), "sha256": sha(p)} for p in proof_paths],
        "scope": "Replace only the existing consolidated archive and S29 script. Preserve XL, diagnostics, saves, cache and external mods.",
        "rollback_policy": "Restore the two exact QR18 files from the current transaction. File rollback cannot undo save progress.",
    }
    write(HERE / TRANSACTION, manifest)
    engine = checked(QR18 / "deploy_core.ps1", BASE_ENGINE).read_text(encoding="utf-8-sig")
    changes = {
        "# QR18 deployment. Real mutations require authorization. Fixtures stay under this task.": "# QR19 deployment. Real mutations require authorization. Fixtures stay under this task.",
        "# Derived from the QR14 transaction. Only two existing Core files may change.": "# Derived from the QR18 transaction. Only two existing Core files may change.",
        "$PinnedCoreManifestSHA='" + BASE_MANIFEST + "'": "$PinnedCoreManifestSHA='" + sha(HERE / TRANSACTION) + "'",
        "PTFR_QR18_JOURNAL_V1": "PTFR_QR19_JOURNAL_V1",
        "'PTFR_QR18_CORE_V1'": "'PTFR_QR19_CORE_V1'",
        "$manifest.source_epoch -cne 'QR18' -or $manifest.predecessor_epoch -cne 'QR13:02'":
            "$manifest.source_epoch -cne 'QR19' -or $manifest.predecessor_epoch -cne 'QR18'",
        "('recovery/core_qr18_01')": "('" + RECOVERY + "')",
        "'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'": "'" + SCRIPT + "'",
    }
    for old, new in changes.items():
        assert engine.count(old) == (2 if old == "PTFR_QR18_JOURNAL_V1" else 1), old
        engine = engine.replace(old, new)
    with (HERE / "deploy_core.ps1").open("x", encoding="utf-8", newline="\n") as f:
        f.write(engine)
    write(HERE / "installer_review.json", {
        "status": "PASS_QR19_REVIEWED_TRANSACTION_DELTA", "predecessor_installer_sha256": BASE_ENGINE,
        "installer_sha256": sha(HERE / "deploy_core.ps1"), "manifest_sha256": sha(HERE / TRANSACTION),
        "allowed_replacements": ALLOWED, "exact_verified_zip": ZIP_SHA,
        "engine_delta": list(changes.values()),
        "review_scope": "Identity, two-file allowlist and recovery namespace only. Locks, containment, journal, write path, process guard and recovery are inherited.",
    })
    print(f"Prepared a two-file transaction. Manifest SHA256 {sha(HERE / TRANSACTION)}")


if __name__ == "__main__":
    prepare()
