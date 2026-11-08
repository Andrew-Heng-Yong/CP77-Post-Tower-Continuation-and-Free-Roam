"""Stage and seal the verified QR19 delta against installed QR18."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile

from build import HERE, QR18, QR18_PIN, DEPOTS, SCRIPT, checked, read, sha, write

CANDIDATE = HERE / "candidate_01"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"


def baseline():
    installed = read(QR18 / "deployment_01/installed_manifest_01.json")
    assert installed["core_epoch"] == "QR18"
    pack = read(checked(installed["core_source_epoch"], QR18_PIN))
    assert pack["files"] == installed["core_files"]
    return installed, pack


def copy(source, destination, expected):
    checked(source, expected)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    checked(destination, expected)


def prepare():
    installed, base = baseline()
    assert not CANDIDATE.exists()
    prior = QR18 / "candidate_01"
    resources = base["source_resources"]
    leaves = {r["path"]: r["sha256"] for r in base["files"]}
    assert set(resources) == {str(p.relative_to(prior / "archive_source")) for p in (prior / "archive_source").rglob("*") if p.is_file()}
    assert set(leaves) == {p.relative_to(prior / "package").as_posix() for p in (prior / "package").rglob("*") if p.is_file()}
    for r in installed["core_files"] + installed["required_files"]:
        checked(Path(installed["game_root"]) / r["path"], r["sha256"])
    typed = read(HERE / "serialized_01/manifest.json")
    verification = read(HERE / "verification.json")
    assert verification["status"] == "PASS_QR19_TYPED_SMS_HANDOFF"
    changed = {r["depot"]: r for r in typed["resources"]}
    assert set(changed) == set(DEPOTS)
    replacement_hashes = {d: r["sha256"] for d, r in changed.items()}
    assert replacement_hashes == verification["resource_hashes"]
    script = read(HERE / "proposal_01/plan.json")["script"]
    compile_report = read(HERE / "compile_01/result.json")
    assert compile_report["status"] == "PASS_CURRENT_INPUT_OFFLINE_COMPILE"
    assert compile_report["candidate_script_sha256"] == script["sha256"]
    checked(HERE / "compile_01/cache/compiled.redscripts", compile_report["output_sha256"])
    for relative, digest in resources.items():
        old = checked(prior / "archive_source" / relative, digest)
        origin = Path(changed[relative]["raw"]) if relative in changed else old
        copy(origin, CANDIDATE / "archive_source" / relative, replacement_hashes.get(relative, digest))
    for relative, digest in leaves.items():
        if relative != ARCHIVE:
            origin = Path(script["source"]) if relative == SCRIPT else prior / "package" / relative
            copy(origin, CANDIDATE / "package" / relative, script["sha256"] if relative == SCRIPT else digest)
    write(HERE / "pack_inputs.json", {"source_resources": resources | replacement_hashes,
                                     "package_without_archive": {k: v for k, v in leaves.items() if k != ARCHIVE} | {SCRIPT: script["sha256"]}})


def seal():
    installed, base = baseline()
    inputs = read(HERE / "pack_inputs.json")
    archive = read(HERE / "archive_readback.json")
    assert archive["status"] == "PASS_ALL_ARCHIVE_MEMBERS"
    resources = inputs["source_resources"]
    assert resources == {r["depot"]: r["sha256"] for r in archive["resources"]}
    assert len(resources) == len(base["source_resources"]) == 1577
    assert {d for d, h in resources.items() if base["source_resources"][d] != h} == set(DEPOTS)
    leaves = inputs["package_without_archive"] | {ARCHIVE: archive["archive_sha256"]}
    old = {r["path"]: r["sha256"] for r in base["files"]}
    assert len(leaves) == len(old) == 51 and {p for p, h in leaves.items() if old[p] != h} == {ARCHIVE, SCRIPT}
    package = CANDIDATE / "package"
    assert set(leaves) == {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    for relative, digest in leaves.items():
        checked(package / relative, digest)
    zip_path = CANDIDATE / "PTFR_QR19_Staged_NotInstalled.zip"
    with zipfile.ZipFile(zip_path, "x", zipfile.ZIP_DEFLATED, compresslevel=6) as f:
        for relative in sorted(leaves):
            info = zipfile.ZipInfo(relative, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            f.writestr(info, (package / relative).read_bytes(), compresslevel=6)
    with zipfile.ZipFile(zip_path) as f:
        assert f.testzip() is None and len(f.namelist()) == len(leaves) and set(f.namelist()) == set(leaves)
        assert all(hashlib.sha256(f.read(p)).hexdigest().upper() == h for p, h in leaves.items())
    for row in installed["core_files"] + installed["required_files"]:
        checked(Path(installed["game_root"]) / row["path"], row["sha256"])
    protected_saves = [r for r in read(QR18 / "core_manifest_01.json")["protected_saves"] +
                       read(QR18 / "core_manifest_01.json")["working_save_files"]]
    for row in protected_saves:
        checked(Path(installed["save_root"]) / row["path"], row["sha256"])
    write(CANDIDATE / "package_manifest.json", {
        "status": "STAGED_QR19_READBACK_VERIFIED_NOT_INSTALLED", "predecessor": "QR18",
        "files": [{"path": p, "sha256": h, "bytes": (package / p).stat().st_size} for p, h in sorted(leaves.items())],
        "source_resources": resources, "changed_paths": [ARCHIVE, SCRIPT], "changed_depots": list(DEPOTS),
        "zip": str(zip_path), "zip_sha256": sha(zip_path), "xl_sha256": leaves[ARCHIVE + ".xl"],
        "preservation_verified": {"installed": len(installed["core_files"]) + len(installed["required_files"]),
                                  "original_saves": len(protected_saves)},
        "installed": False, "gameplay_validation": "UNTESTED",
    })
    print(f"Verified {len(leaves)} package files and {len(resources)} archive members")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("phase", choices=("prepare", "seal"))
    {"prepare": prepare, "seal": seal}[cli.parse_args().phase]()
