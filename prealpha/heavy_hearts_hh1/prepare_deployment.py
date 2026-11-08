"""Bind HH1 to the reviewed two-file installer and current QR19 inputs."""

import hashlib
import zipfile
from pathlib import Path

from stage import ARCHIVE, CANDIDATE, HERE, QR19, XL, baseline, checked, read, sha, write

ALLOWED = [ARCHIVE, XL]
TRANSACTION = "core_manifest_01.json"
RECOVERY = "recovery/core_hh1_01"
ENGINE_SHA = "4B320A14E4B404E4FBAEDF33FC0B296243EF866191586B75846AADD0134BB61B"
OLD_MANIFEST_SHA = "AC73C58689393CB9C1E89E19AE5D485602D7ADB7923659EAE93F8B3E58C5BE14"
CANDIDATE_SHA = "6788ABB738106B19BEDACCCA2FBD99B7391272703A3E4FE6196EAD7A66CE1339"


def main():
    assert __debug__
    assert not any((HERE / path).exists() for path in (TRANSACTION, "deploy_core.ps1", RECOVERY))
    game, _ = baseline()
    candidate_path = checked(CANDIDATE / "package_manifest.json", CANDIDATE_SHA)
    candidate = read(candidate_path)
    assert candidate["status"] == "STAGED_HH1_READBACK_VERIFIED" and candidate["changed_paths"] == ALLOWED
    installed_path = QR19 / "deployment_01/installed_manifest_01.json"
    installed = read(checked(installed_path, "B926963B5BA85B95E8F371DBB00720A37793E5BC3E9904F770A220B8AED89784"))
    old_manifest_path = checked(QR19 / TRANSACTION, OLD_MANIFEST_SHA)
    old = read(old_manifest_path)
    assert installed["required_files"] == old["required_files"]
    before = {r["path"]: r for r in installed["core_files"]}
    after = {r["path"]: r for r in candidate["files"]}
    assert set(before) == set(after) and len(after) == 51
    assert sorted(p for p in before if before[p]["sha256"] != after[p]["sha256"]) == ALLOWED
    package = CANDIDATE / "package"
    assert {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()} == set(after)
    for path, row in after.items():
        checked(package / path, row["sha256"])
        checked(game / path, before[path]["sha256"])
    archive_path = HERE / "archive_readback.json"
    archive = read(checked(archive_path, "F05B2150209F063892849EDD239FA2E390F0422676912E1C064BA8BC75529A55"))
    assert archive["status"] == "PASS_ALL_ARCHIVE_MEMBERS"
    assert archive["archive_sha256"] == after[ARCHIVE]["sha256"]
    assert {r["depot"]: r["sha256"] for r in archive["resources"]} == candidate["source_resources"]
    assert len(archive["resources"]) == 1581
    owner_path = checked(HERE / "owner_verification.json", "33DACF677C02230ADF29A9757FD032863C3400206CD1B007B9E2585AAE98FEDB")
    world_path = checked(HERE / "built_04/world_verification.json", "AFF89FE8C93EADF04BC3FEC2F5B123A3DC65FC7617BBC2D7EE8431AFFEFAE2BE")
    assert read(owner_path)["status"] == "PASS_TYPED_OWNER_AND_REGISTRATIONS"
    assert read(world_path)["status"] == "PASS_TYPED_FILTERED_WORKSPOTS"

    # The resource-only delta preserves the complete, previously compiled source
    # inventory. Normal game runs refresh only this 16-byte timestamp sidecar.
    compiler_pins = dict(old["compile_inputs"])
    compile_path = checked(QR19 / "compile_deployment_01/result.json",
                           "31243092F2A39FF64BC4612FDC9DF7719AECA5042D6C129E5BB6F831BE3591F1")
    compiled = read(compile_path)
    script = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds"
    assert compiled["status"] == "PASS_CURRENT_INPUT_OFFLINE_COMPILE"
    assert compiled["input_pins"] == compiler_pins and compiled["source_count"] == 148
    assert compiled["candidate_script_sha256"] == before[script]["sha256"] == after[script]["sha256"]
    compiler_pins[str(game / script)] = compiled["candidate_script_sha256"]
    compiled_path = checked(QR19 / "compile_deployment_01/cache/compiled.redscripts", compiled["output_sha256"])
    stamp = game / "r6/cache/final.redscripts.ts"
    assert stamp.stat().st_size == 16 and str(stamp) in compiler_pins
    compiler_pins[str(stamp)] = sha(stamp)
    for path, digest in compiler_pins.items():
        checked(path, digest)
    expected_sources = {Path(p) for p in compiler_pins if Path(p).suffix.lower() == ".reds"}
    actual_sources = {p for root in (game / "r6/scripts", game / "red4ext/plugins") for p in root.rglob("*.reds")}
    assert expected_sources == actual_sources and len(expected_sources) == 148
    save = Path(installed["save_root"])
    for row in old["protected_saves"] + old["working_save_files"]:
        checked(save / row["path"], row["sha256"])
    for row in installed["required_files"]:
        checked(game / row["path"], row["sha256"])

    zip_path = CANDIDATE / "PTFR_HH1_Development.zip"
    with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for relative in sorted(after):
            info = zipfile.ZipInfo(relative, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            z.writestr(info, (package / relative).read_bytes(), compresslevel=6)
    with zipfile.ZipFile(zip_path) as z:
        assert z.testzip() is None and set(z.namelist()) == set(after) and len(z.namelist()) == 51
        assert all(hashlib.sha256(z.read(p)).hexdigest().upper() == row["sha256"] for p, row in after.items())

    proofs = [candidate_path, archive_path, owner_path, world_path, installed_path, old_manifest_path,
              compile_path, compiled_path]
    manifest = old | {
        "schema": "PTFR_HH1_CORE_V1", "source_epoch": "HH1", "predecessor_epoch": "QR19",
        "package_root": str(package), "zip": str(zip_path), "zip_sha256": sha(zip_path),
        "files": [{"path": p, "before": before[p]["sha256"], "before_bytes": before[p]["bytes"],
                   "after": after[p]["sha256"], "after_bytes": after[p]["bytes"]} for p in sorted(after)],
        "changing_paths": ALLOWED, "compile_inputs": compiler_pins,
        "compile_coverage": old["compile_coverage"] | {"mode": "UNCHANGED_REDS_CURRENT_HASHES_VERIFIED"},
        "proofs": [{"path": str(p), "sha256": sha(p)} for p in proofs],
        "scope": "Install HH1 by replacing the consolidated archive and its XL registration file.",
        "rollback_policy": "Restore the exact two QR19 files from this transaction's recovery copies.",
    }
    write(HERE / TRANSACTION, manifest)
    text = checked(QR19 / "deploy_core.ps1", ENGINE_SHA).read_text(encoding="utf-8-sig")
    changes = {
        "# QR19 deployment. Real mutations require authorization. Fixtures stay under this task.":
            "# HH1 deployment. User authorized installation. Fixtures stay under this task.",
        "# Derived from the QR18 transaction. Only two existing Core files may change.":
            "# Derived from the QR19 transaction. Only the archive and XL may change.",
        "$PinnedCoreManifestSHA='" + OLD_MANIFEST_SHA + "'":
            "$PinnedCoreManifestSHA='" + sha(HERE / TRANSACTION) + "'",
        "PTFR_QR19_JOURNAL_V1": "PTFR_HH1_JOURNAL_V1",
        "'PTFR_QR19_CORE_V1'": "'PTFR_HH1_CORE_V1'",
        "$manifest.source_epoch -cne 'QR19' -or $manifest.predecessor_epoch -cne 'QR18'":
            "$manifest.source_epoch -cne 'HH1' -or $manifest.predecessor_epoch -cne 'QR19'",
        "('recovery/core_qr19_01')": "('" + RECOVERY + "')",
        "'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'": "'" + XL + "'",
    }
    for a, b in changes.items():
        assert text.count(a) == (2 if a == "PTFR_QR19_JOURNAL_V1" else 1), a
        text = text.replace(a, b)
    with (HERE / "deploy_core.ps1").open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    write(HERE / "installer_review.json", {
        "status": "PASS_HH1_REVIEWED_TRANSACTION_DELTA", "predecessor_installer_sha256": ENGINE_SHA,
        "installer_sha256": sha(HERE / "deploy_core.ps1"), "manifest_sha256": sha(HERE / TRANSACTION),
        "allowed_replacements": ALLOWED, "engine_delta": list(changes.values()),
        "scope": "Identity, archive/XL allowlist and private recovery namespace. Transaction logic is inherited unchanged.",
    })
    test_source = (QR19 / "test_deployment.py").read_text(encoding="utf-8")
    assert test_source.count("QR18") == 2 and test_source.count("QR19") == 2
    test_source = test_source.replace("QR18", "QR19").replace(
        "Exercise the exact QR19 installer", "Exercise the exact HH1 installer").replace(
        "PASS_QR19_TWO_FILE_DEPLOYMENT_FIXTURES", "PASS_HH1_TWO_FILE_DEPLOYMENT_FIXTURES")
    with (HERE / "test_deployment.py").open("x", encoding="utf-8", newline="\n") as f:
        f.write(test_source)
    print("Prepared HH1 archive/XL transaction and exact Core51 development ZIP")


if __name__ == "__main__":
    main()
