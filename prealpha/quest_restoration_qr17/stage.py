"""Stage the reviewed two-file package delta and seal the verified ZIP."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile

from prepare import HERE, PRIVATE, SCRIPT, checked, read, sha, write

CANDIDATE = HERE / "candidate_01"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"


def copy_verified(source, destination, expected):
    checked(source, expected)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    checked(destination, expected)


def predecessors():
    installed = read(HERE.parent / "quest_restoration_qr14/deployment_01/installed_manifest_01.json")
    source = read(checked(installed["core_source_epoch"], installed["core_source_epoch_sha256"]))
    assert installed["core_epoch"] == source["epoch_key"] == "QR13:02"
    return installed, source


def prepare():
    installed, predecessor = predecessors()
    assert not CANDIDATE.exists()
    old_source = Path(predecessor["candidate"]) / "archive_source"
    old_package = old_source.parent / "package"
    resources = predecessor["source_resources"]
    leaves = {r["path"]: r["sha256"] for r in predecessor["package_files"]}
    assert set(resources) == {str(p.relative_to(old_source)) for p in old_source.rglob("*") if p.is_file()}
    assert set(leaves) == {p.relative_to(old_package).as_posix() for p in old_package.rglob("*") if p.is_file()}
    for relative, digest in leaves.items():
        checked(Path(installed["game_root"]) / relative, digest)
    graph = read(HERE / "serialized_01/manifest.json")
    plan = read(HERE / "proposal_01/plan.json")
    script = plan["script"]
    verification = read(HERE / "verification.json")
    compile_result = read(HERE / "compile_01/result.json")
    assert verification["status"] == "PASS_SERIALIZED_HANDOFF_CONTRACT"
    assert graph["depot"] == PRIVATE and verification["resource_sha256"] == graph["sha256"]
    assert compile_result["status"] == "PASS_CURRENT_INPUT_OFFLINE_COMPILE"
    assert script["path"] == SCRIPT and compile_result["candidate_script_sha256"] == script["sha256"]
    checked(HERE / "compile_01/cache/compiled.redscripts", compile_result["output_sha256"])
    for relative, digest in resources.items():
        raw = checked(old_source / relative, digest)
        assert b"PTFRQR17_MQ037_HandoffPending" not in raw.read_bytes()
        source, expected = (Path(graph["raw"]), graph["sha256"]) if relative == PRIVATE else (raw, digest)
        copy_verified(source, CANDIDATE / "archive_source" / relative, expected)
    for relative, digest in leaves.items():
        if relative != ARCHIVE:
            source, expected = (Path(script["source"]), script["sha256"]) if relative == SCRIPT else (old_package / relative, digest)
            copy_verified(source, CANDIDATE / "package" / relative, expected)
    write(HERE / "pack_inputs.json", {
        "source_resources": resources | {PRIVATE: graph["sha256"]},
        "package_without_archive": {k: v for k, v in leaves.items() if k != ARCHIVE} | {SCRIPT: script["sha256"]},
    })


def seal():
    _, predecessor = predecessors()
    inputs = read(HERE / "pack_inputs.json")
    archive_result = read(HERE / "archive_readback.json")
    assert archive_result["status"] == "PASS_ALL_ARCHIVE_MEMBERS"
    assert {r["depot"]: r["sha256"] for r in archive_result["resources"]} == inputs["source_resources"]
    leaves = inputs["package_without_archive"] | {ARCHIVE: archive_result["archive_sha256"]}
    old_leaves = {r["path"]: r["sha256"] for r in predecessor["package_files"]}
    assert {k for k, v in leaves.items() if old_leaves[k] != v} == {ARCHIVE, SCRIPT}
    assert len(leaves) == len(old_leaves) == 51
    resources = inputs["source_resources"]
    assert len(resources) == len(predecessor["source_resources"]) == 1577
    assert {k for k, v in resources.items() if predecessor["source_resources"][k] != v} == {PRIVATE}
    package = CANDIDATE / "package"
    assert set(leaves) == {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    zip_path = CANDIDATE / "PTFR_QR17_Staged_NotInstalled.zip"
    for relative, digest in leaves.items():
        checked(package / relative, digest)
    with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for relative in sorted(leaves):
            item = zipfile.ZipInfo(relative, (1980, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, (package / relative).read_bytes(), compresslevel=6)
    with zipfile.ZipFile(zip_path) as archive:
        assert archive.testzip() is None and len(archive.namelist()) == len(leaves)
        assert set(archive.namelist()) == set(leaves)
        assert all(hashlib.sha256(archive.read(p)).hexdigest().upper() == digest for p, digest in leaves.items())
    preserved = {"installed": 0, "original_saves": 0}
    for row in read(HERE.parent / "quest_restoration_qr15/preservation.json")["checks"]:
        scope = row["scope"]
        if scope in preserved:
            checked(row["path"], row["expected"])
            preserved[scope] += 1
    assert preserved == {"installed": 77, "original_saves": 6}
    write(CANDIDATE / "package_manifest.json", {
        "status": "STAGED_QR17_READBACK_VERIFIED_NOT_INSTALLED",
        "predecessor": "QR13:02",
        "files": [{"path": p, "sha256": digest, "bytes": (package / p).stat().st_size}
                  for p, digest in sorted(leaves.items())],
        "source_resources": resources, "changed_paths": [ARCHIVE, SCRIPT], "changed_depots": [PRIVATE],
        "zip": str(zip_path), "zip_sha256": sha(zip_path), "xl_sha256": leaves[ARCHIVE + ".xl"],
        "preservation_verified": preserved, "installed": False, "gameplay_validation": "PENDING_GENUINE_FIXTURE",
    })
    print(f"Verified {len(leaves)} package paths and {len(resources)} archive payloads: {zip_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("prepare", "seal"))
    {"prepare": prepare, "seal": seal}[parser.parse_args().phase]()
