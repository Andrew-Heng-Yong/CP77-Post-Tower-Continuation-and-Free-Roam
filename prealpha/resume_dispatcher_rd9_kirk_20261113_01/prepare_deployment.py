"""Stage the verified two-file successor and bind its own transaction."""
from hashlib import sha256
from pathlib import Path
import shutil
from zipfile import ZIP_DEFLATED, ZipFile
from prepare import ARCHIVE, DEPOT, HERE, OBSERVATION, PACKAGE, RD8, SCRIPT, baseline, plain, read, sha, write

BASELINE = RD8 / "deployment_01/installed_manifest_01.json"
EPOCH = "RD9_MEET_KIRK_DISTANCE"
BEFORE = "RD8_MEET_KIRK_RESUME"
SCHEMA = "PTFR_RD9_MEET_KIRK_DISTANCE_CORE_V1"
CHANGES = {ARCHIVE, SCRIPT}
MANIFEST = HERE / "core_manifest_01.json"
INSTALLER = HERE / "deploy_core.ps1"
DEPLOYMENT = HERE / "deployment_01"
PS = Path(r"C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe")


def adapt(template, destination, template_hash, replacements):
    assert sha(template) == template_hash
    source = template.read_text(encoding="utf-8-sig")
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new, 1)
    with destination.open("x", encoding="utf-8", newline="\n") as file:
        file.write(source)


def main():
    installed, members = baseline()
    game = Path(installed["game_root"])
    compile_result = HERE / "compile_01/result.json"
    pack_result = HERE / "archive_01/readback.json"
    assessment = HERE / "evidence_01/assessment.json"
    compiled, packed, graph = (read(p) for p in (compile_result, pack_result, assessment))
    assert compiled["status"] == graph["status"] == "PASS" and compiled["source_count"] == 148
    assert packed["status"] == "MEMBERS_VERIFIED" and packed["changed_depot"] == DEPOT
    packed_archive = pack_result.parent / Path(ARCHIVE).name
    assert sha(packed_archive) == packed["archive_sha256"] and sha(PACKAGE / SCRIPT) == compiled["staged_hashes"][SCRIPT]
    updated = {r["depot"]: r["sha256"] for r in packed["members"]}
    assert members.keys() == updated.keys()
    assert {key for key, value in updated.items() if value != members[key]} == {DEPOT}
    assert all(sha(game / rel) == digest for rel, digest in compiled["input_pins"].items())
    files = []
    for row in installed["core_files"]:
        rel = row["path"]
        dest = PACKAGE / rel
        if rel != SCRIPT:
            assert not dest.exists()
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(packed_archive if rel == ARCHIVE else game / rel, dest)
        files.append({"path": rel, "before": row["sha256"], "before_bytes": row["bytes"],
                      "after": sha(dest), "after_bytes": dest.stat().st_size})
    assert len(files) == 51 and {r["path"] for r in files if r["before"] != r["after"]} == CHANGES
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file()} == {r["path"] for r in files}
    package_manifest = PACKAGE.parent / "manifest.json"
    write(package_manifest, {"status": "STAGED_OFFLINE", "core_files": files, "changes": sorted(CHANGES),
                             "archive_sha256": packed["archive_sha256"], "archive_payloads": 1748})
    DEPLOYMENT.mkdir()
    (HERE / "fixtures").mkdir()
    (HERE / "recovery").mkdir()
    bundle = DEPLOYMENT / "RD9_Meet_Kirk_candidate_01.zip"
    with ZipFile(bundle, "x", ZIP_DEFLATED, compresslevel=6) as archive:
        for row in files:
            archive.write(PACKAGE / row["path"], row["path"])
    with ZipFile(bundle) as archive:
        assert len(archive.namelist()) == 51 and archive.testzip() is None
        assert all(sha256(archive.read(row["path"])).hexdigest().upper() == row["after"] for row in files)
    proofs = [BASELINE, compile_result, pack_result, assessment, package_manifest, HERE / "evidence_01/inputs.json",
              OBSERVATION / "bar_anchor.json", OBSERVATION / "saved_stage_and_handlers_02.json"]
    prior_transaction = RD8 / "core_manifest_01.json"
    write(MANIFEST, {"schema": SCHEMA, "component": "Core", "source_epoch": EPOCH, "predecessor_epoch": BEFORE,
                     "scope": "Correct the stalled Meet Kirk playtest with the verified two-file successor.",
                     "game_root": str(game), "save_root": installed["save_root"], "package_root": str(PACKAGE),
                     "process_names": read(prior_transaction)["process_names"],
                     "files": files, "changing_paths": sorted(CHANGES), "required_files": installed["required_files"],
                     "protected_saves": [], "working_save_files": [], "zip": str(bundle), "zip_sha256": sha(bundle),
                     "proofs": [{"path": str(p), "sha256": sha(p)} for p in proofs],
                     "compile_inputs": {str(game / rel): h for rel, h in compiled["input_pins"].items()}})
    adapt(RD8 / "deploy_core.ps1", INSTALLER, "3961EDF2E8D9C1F76AF08CFF1E97FB3AE6A59975663C68F04CA152BBDF65ADB8", (
        (sha(prior_transaction), sha(MANIFEST)),
        ("PTFR_RD8_MEET_KIRK_RESUME_CORE_V1", SCHEMA),
        ("$manifest.source_epoch -cne 'RD8_MEET_KIRK_RESUME'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'RD5_RITE_OF_PASSAGE_RESUME'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ("core_resume_rd8_kirk_01", "core_resume_rd9_kirk_01"),
    ))
    adapt(RD8 / "deploy.py", HERE / "deploy.py", "1D48D0DCAF6D01FFE2E0D08DFC93C439430CA22DE0BDEA3E1C29AB80CEFECA9A", (
        ("core_resume_rd8_kirk_01", "core_resume_rd9_kirk_01"),
        ("HERE/'archive_02/source'", "HERE/'archive_01/source'"),
        ("PENDING_MEET_KIRK_RESUME_PLAYTEST", "PENDING_MEET_KIRK_DISTANCE_RETEST"),
    ))
    print("Staged the verified 51-file package and two-file transaction.")


if __name__ == "__main__":
    main()
