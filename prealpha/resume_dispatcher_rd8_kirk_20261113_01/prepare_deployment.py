"""Stage the exact two-file RD8 transaction using the reviewed RD5 installer."""
from pathlib import Path
import shutil
from prepare import HERE, RD5, RD7, SCRIPT, ARCHIVE, MANIFEST as BASELINE_PIN, load_baseline, read, sha, write
from zipfile import ZIP_DEFLATED, ZipFile

BASELINE = RD5 / BASELINE_PIN[0]
EPOCH = "RD8_MEET_KIRK_RESUME"
BEFORE = "RD5_RITE_OF_PASSAGE_RESUME"
SCHEMA = "PTFR_RD8_MEET_KIRK_RESUME_CORE_V1"
CHANGES = {ARCHIVE, SCRIPT}
PACKAGE = HERE / "candidate_01/package"
MANIFEST = HERE / "core_manifest_01.json"
INSTALLER = HERE / "deploy_core.ps1"
DEPLOYMENT = HERE / "deployment_01"
PS = Path(r"C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe")
from review_batch import plain


def adapt(template, destination, changes):
    source = template.read_text(encoding="utf-8-sig")
    for old, new in changes:
        assert source.count(old) == 1, old
        source = source.replace(old, new, 1)
    with destination.open("x", encoding="utf-8", newline="\n") as file:
        file.write(source)


def main():
    game, members, xl = load_baseline()
    old = read(BASELINE)
    compile_result = HERE / "compile_01/result.json"
    pack_result = HERE / "archive_02/readback.json"
    assessment = HERE / "evidence_01/assessment_02.json"
    compiled, packed, graph = (read(p) for p in (compile_result, pack_result, assessment))
    assert compiled["status"] == graph["status"] == "PASS" and compiled["source_count"] == 148
    assert packed["status"] == "MEMBERS_VERIFIED" and packed["registered_paths_changed"] == 0
    packed_archive = HERE / "archive_02" / Path(ARCHIVE).name
    assert sha(packed_archive) == packed["archive_sha256"] and sha(PACKAGE / SCRIPT) == compiled["staged_hashes"][SCRIPT]
    updated = {r["depot"]: r["sha256"] for r in packed["members"]}
    assert len(updated) == 1748 and members.keys() <= updated.keys()
    assert {k for k, v in updated.items() if members.get(k) != v} == set(packed["changes"])
    assert all(sha(game / p) == digest for p, digest in compiled["input_pins"].items())
    files = []
    for row in old["core_files"]:
        rel = row["path"]
        dest = PACKAGE / rel
        if rel != SCRIPT:
            assert not dest.exists()
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(packed_archive if rel == ARCHIVE else game / rel, dest)
        files.append({"path": rel, "before": row["sha256"], "before_bytes": row["bytes"],
                      "after": sha(dest), "after_bytes": dest.stat().st_size})
    assert sha(PACKAGE / xl["path"]) == xl["sha256"]
    assert len(files) == 51 and {r["path"] for r in files if r["before"] != r["after"]} == CHANGES
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file()} == {r["path"] for r in files}
    candidate_manifest = PACKAGE.parent / "manifest.json"
    write(candidate_manifest, {"status": "STAGED_OFFLINE", "core_files": files, "changes": sorted(CHANGES),
                               "archive_sha256": packed["archive_sha256"], "archive_payloads": 1748})
    DEPLOYMENT.mkdir()
    (HERE / "fixtures").mkdir()
    (HERE / "recovery").mkdir()
    bundle = DEPLOYMENT / "RD8_Meet_Kirk_candidate_01.zip"
    with ZipFile(bundle, "x", ZIP_DEFLATED, compresslevel=6) as archive:
        for row in files:
            archive.write(PACKAGE / row["path"], row["path"])
    with ZipFile(bundle) as archive:
        import hashlib
        assert len(archive.namelist()) == 51 and archive.testzip() is None
        assert all(hashlib.sha256(archive.read(row["path"])).hexdigest().upper() == row["after"] for row in files)
    proofs = [BASELINE, compile_result, pack_result, assessment, candidate_manifest, HERE / "evidence_01/inputs.json",
              RD7 / "evidence_04/assessment.json"]
    write(MANIFEST, {"schema": SCHEMA, "component": "Core", "source_epoch": EPOCH, "predecessor_epoch": BEFORE,
                     "scope": "Install the closed-game Meet Kirk resume test candidate.",
                     "game_root": str(game), "save_root": old["save_root"], "package_root": str(PACKAGE),
                     "process_names": read(RD5 / "core_manifest_01.json")["process_names"],
                     "files": files, "changing_paths": sorted(CHANGES), "required_files": old["required_files"],
                     "protected_saves": [], "working_save_files": [], "zip": str(bundle), "zip_sha256": sha(bundle),
                     "proofs": [{"path": str(p), "sha256": sha(p)} for p in proofs],
                     "compile_inputs": {str(game / p): h for p, h in compiled["input_pins"].items()}})
    adapt(RD5 / "deploy_core.ps1", INSTALLER, (
        (sha(RD5 / "core_manifest_01.json"), sha(MANIFEST)),
        ("PTFR_RD5_RITE_OF_PASSAGE_RESUME_CORE_V1", SCHEMA),
        ("$manifest.source_epoch -cne 'RD5_RITE_OF_PASSAGE_RESUME'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'RD4_BEAT_ON_THE_BRAT_RESUME'", f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ("core_resume_rd5_rite_01", "core_resume_rd8_kirk_01"),
        ("'r6/scripts/PTFR_Consolidated/PTFR_ActivityStateR3.reds'", f"'{SCRIPT}'"),
        ("Core51/two-file Rite scope drift", "Core51/two-file Meet Kirk scope drift"),
        ("# Replace the two qualified Rite of Passage files", "# Replace the two qualified Meet Kirk files"),
    ))
    adapt(RD5 / "deploy.py", HERE / "deploy.py", (
        ("Rite deployment fixture runner", "Meet Kirk deployment fixture runner"),
        ("core_resume_rd5_rite_01", "core_resume_rd8_kirk_01"),
        ("'archive_payloads': 1745", "'archive_payloads': 1748"),
        ("HERE/'archive_01/source'", "HERE/'archive_02/source'"),
        ("PENDING_RITE_OF_PASSAGE_RESUME_PLAYTEST", "PENDING_MEET_KIRK_RESUME_PLAYTEST"),
    ))
    print("Staged the verified 51-file package and two-file transaction.")


if __name__ == "__main__":
    main()
