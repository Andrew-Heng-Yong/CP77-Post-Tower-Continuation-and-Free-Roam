"""Freeze the archive-only successor and its guarded transaction."""
from hashlib import sha256
from pathlib import Path
import shutil
from zipfile import ZIP_DEFLATED, ZipFile
from prepare import ARCHIVE, BASELINE, DEPOT, HERE, PACKAGE, RD9, STAGE, baseline, pinned, read, sha, write
from review_batch import plain

EPOCH = "RD10_MEET_KIRK_CONTENT_LOCK"
BEFORE = "RD9_MEET_KIRK_DISTANCE"
SCHEMA = "PTFR_RD10_MEET_KIRK_CONTENT_LOCK_CORE_V1"
CHANGES = {ARCHIVE}
MANIFEST = HERE / "core_manifest_01.json"
INSTALLER = HERE / "deploy_core.ps1"
DEPLOYMENT = HERE / "deployment_01"
PS = Path(r"C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe")
COMPILE = RD9 / "compile_01/result.json"


def adapt(name, digest, replacements):
    source = pinned(RD9, (name, digest)).read_text(encoding="utf-8-sig")
    for old, new in replacements:
        assert source.count(old) == 1, old
        source = source.replace(old, new, 1)
    with (HERE / name).open("x", encoding="utf-8", newline="\n") as file:
        file.write(source)


def main():
    installed, members = baseline()
    game = Path(installed["game_root"])
    compile_proof = read(pinned(COMPILE.parent, (COMPILE.name, "2B54DE7AABB7A78B5BF3CCB07DFD5CADAF063A8CC991315F52D91A13A54FC3B7")))
    assert compile_proof["status"] == "PASS" and compile_proof["source_count"] == 148
    sources = {p.relative_to(game).as_posix() for root in ("r6/scripts", "red4ext/plugins")
               for p in (game / root).rglob("*.reds")}
    assert sources == set(compile_proof["staged_hashes"])
    for rel in sources:
        pinned(game, (rel, compile_proof["staged_hashes"][rel]))
    inputs = {str(game / rel): compile_proof["staged_hashes"][rel] for rel in sources}
    # The archive change has no REDscript overlay. Reuse the exact compiled
    # source inventory and verify the compiler executable and base bytecode.
    for rel in compile_proof["input_pins"].keys() - sources:
        if rel.endswith(".ts"):
            continue  # The live compiler refreshes this cache sidecar.
        digest = compile_proof["input_pins"][rel]
        pinned(game, (rel, digest))
        inputs[str(game / rel)] = digest
    pack_result = HERE / "archive_01/readback.json"
    assessment = HERE / "evidence_01/assessment.json"
    pack, graph = read(pack_result), read(assessment)
    assert graph["status"] == "PASS" and pack["status"] == "MEMBERS_VERIFIED" and pack["changed_depot"] == DEPOT
    packed_archive = pinned(pack_result.parent, (Path(ARCHIVE).name, pack["archive_sha256"]))
    updated = {r["depot"]: r["sha256"] for r in pack["members"]}
    assert members.keys() == updated.keys() and {key for key in members if updated[key] != members[key]} == {DEPOT}
    files = []
    for row in installed["core_files"]:
        rel = row["path"]
        dest = PACKAGE / rel
        assert not dest.exists()
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(packed_archive if rel == ARCHIVE else game / rel, dest)
        files.append({"path": rel, "before": row["sha256"], "before_bytes": row["bytes"],
                      "after": sha(dest), "after_bytes": dest.stat().st_size})
    assert len(files) == 51 and {r["path"] for r in files if r["before"] != r["after"]} == CHANGES
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file()} == {r["path"] for r in files}
    package_manifest = PACKAGE.parent / "manifest.json"
    write(package_manifest, {"status": "STAGED_OFFLINE", "core_files": files, "changes": sorted(CHANGES),
                             "archive_sha256": pack["archive_sha256"], "archive_payloads": 1748})
    DEPLOYMENT.mkdir()
    (HERE / "fixtures").mkdir()
    (HERE / "recovery").mkdir()
    bundle = DEPLOYMENT / "RD10_Meet_Kirk_candidate_01.zip"
    with ZipFile(bundle, "x", ZIP_DEFLATED, compresslevel=6) as archive:
        for row in files:
            archive.write(PACKAGE / row["path"], row["path"])
    with ZipFile(bundle) as archive:
        assert len(archive.namelist()) == 51 and archive.testzip() is None
        assert all(sha256(archive.read(row["path"])).hexdigest().upper() == row["after"] for row in files)
    proofs = [BASELINE, COMPILE, pack_result, assessment, package_manifest, HERE / "evidence_01/inputs.json", STAGE]
    prior = pinned(RD9, ("core_manifest_01.json", "9463A316AEF28EDFFFCA626F6675C39AE96DA9FE78EE8A54176F89421FEE3173"))
    write(MANIFEST, {"schema": SCHEMA, "component": "Core", "source_epoch": EPOCH, "predecessor_epoch": BEFORE,
                     "scope": "Repair the earned Meet Kirk content wait with the verified archive-only successor.",
                     "game_root": str(game), "save_root": installed["save_root"], "package_root": str(PACKAGE),
                     "process_names": read(prior)["process_names"],
                     "files": files, "changing_paths": sorted(CHANGES), "required_files": installed["required_files"],
                     "protected_saves": [], "working_save_files": [], "zip": str(bundle), "zip_sha256": sha(bundle),
                     "proofs": [{"path": str(p), "sha256": sha(p)} for p in proofs], "compile_inputs": inputs})
    adapt("deploy_core.ps1", "FB81C34810D0CA9F4D80D73357A592DFB4D6ACF31CEDEDF79D69FE1205DE9C06", (
        (sha(prior), sha(MANIFEST)),
        ("PTFR_RD9_MEET_KIRK_DISTANCE_CORE_V1", SCHEMA),
        ("$manifest.source_epoch -cne 'RD9_MEET_KIRK_DISTANCE'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'RD8_MEET_KIRK_RESUME'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ("core_resume_rd9_kirk_01", "core_resume_rd10_kirk_01"),
        ("the two qualified Meet Kirk files", "the qualified Meet Kirk archive"),
        ("$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')",
         "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')"),
        ("$changes.Count -ne 2", "$changes.Count -ne 1"),
        ("Core51/two-file Meet Kirk scope drift", "Core51/archive-only Meet Kirk scope drift"),
    ))
    adapt("deploy.py", "53DFF64D31C7244BEAAF7D38FD6845D7206774F7881790A0F4E77C361CA63399", (
        ("core_resume_rd9_kirk_01", "core_resume_rd10_kirk_01"),
        ("from prepare_deployment import HERE, BASELINE, plain, read, sha, write",
         "from prepare_deployment import HERE, BASELINE, COMPILE, plain, read, sha, write"),
        ("        'crash_second': [('Install', 72, '-FailurePoint', 'CrashAfterSecondReplace'),\n"
         "                         ('Recover', 'RECOVERED_BEFORE'), ('Verify', 'VERIFIED_BEFORE', '-ExpectedState', 'Before')],\n", ""),
        ("str(HERE / 'compile_01/result.json')", "str(COMPILE)"),
        ("'unchanged_core_paths': 49", "'unchanged_core_paths': 50"),
        ("PENDING_MEET_KIRK_DISTANCE_RETEST", "PENDING_MEET_KIRK_CONTENT_LOCK_RETEST"),
    ))
    print("Staged the verified 51-file package and archive-only transaction.")


if __name__ == "__main__":
    main()
