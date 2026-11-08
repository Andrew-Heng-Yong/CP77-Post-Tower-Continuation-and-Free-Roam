"""Stage the verified resource delta on QR19 and seal after archive readback."""

import argparse
import json
from pathlib import Path
from shutil import copyfile

from verify import CONTRACTS, DEPPATH, HERE, SERIALIZED, read, sha

QR19 = HERE.parent / "quest_restoration_qr19"
PRIOR = QR19 / "candidate_01"
CANDIDATE = HERE / "candidate_01"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
DELTA = {f"{DEPPATH}\\{name}.questphase" for name in CONTRACTS}


def checked(path, digest):
    path = Path(path)
    assert sha(path) == digest, f"Hash mismatch: {path}"
    return path


def write(path, data):
    with path.open("x", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
        file.write("\n")


def baseline():
    installed = read(checked(
        QR19 / "deployment_01/installed_manifest_01.json",
        "B926963B5BA85B95E8F371DBB00720A37793E5BC3E9904F770A220B8AED89784",
    ))
    base = read(checked(
        PRIOR / "package_manifest.json",
        "7259E12EABB61A8253F50A22BE6198DA7CFECA65692D99C37AE7283F2ADE942D",
    ))
    assert installed["core_epoch"] == "QR19" and installed["core_files"] == base["files"]
    rows = installed["core_files"] + installed["required_files"]
    assert len(rows) == 77
    for row in rows:
        checked(Path(installed["game_root"]) / row["path"], row["sha256"])
    return base


def stage():
    assert not CANDIDATE.exists()
    base = baseline()
    verification = read(HERE / "verification.json")
    assert verification["status"] == "PASS_TYPED_JUDY_TRAVEL_GUARDS"
    new = {row["depot"]: row["sha256"] for row in verification["resources"]}
    assert set(new) == DELTA and not DELTA.intersection(base["source_resources"])
    source = PRIOR / "archive_source"
    package = PRIOR / "package"
    assert set(base["source_resources"]) == {str(p.relative_to(source)) for p in source.rglob("*") if p.is_file()}
    leaves = {row["path"]: row["sha256"] for row in base["files"]}
    assert set(leaves) == {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}

    resources = base["source_resources"] | new
    for depot, digest in resources.items():
        origin = SERIALIZED / Path(depot).name if depot in new else source / depot
        target = CANDIDATE / "archive_source" / depot
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(checked(origin, digest), target)
    checked(package / ARCHIVE, leaves.pop(ARCHIVE))
    for relative, digest in leaves.items():
        target = CANDIDATE / "package" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(checked(package / relative, digest), target)
    write(HERE / "pack_inputs.json", {"source_resources": resources, "package_without_archive": leaves})

    # Reuse the pinned pack/readback procedure with this directory's new inputs.
    copyfile(checked(QR19 / "pack.ps1", "7768A9C08234D5840403993A880A8A824A230300D35E41658076F0988491968E"),
             HERE / "pack.ps1")


def seal():
    base = baseline()
    packed = read(HERE / "archive_readback.json")
    assert packed["status"] == "PASS_ALL_ARCHIVE_MEMBERS"
    resources = {r["depot"]: r["sha256"] for r in packed["resources"]}
    keys = {r["depot"]: r["key"] for r in packed["resources"]}
    previous = read(checked(
        QR19 / "archive_readback.json", "871B30C20EAD08CBEE3CAB9A43DA86FC80D2D80815671E67EEA6E160839B0315",
    ))
    assert {r["depot"]: r["sha256"] for r in previous["resources"]} == base["source_resources"]
    assert all(keys[r["depot"]] == r["key"] for r in previous["resources"])
    assert len(resources) == len(set(keys.values())) == len(packed["resources"]) == 1580
    native = read(SERIALIZED / "manifest.json")
    new = {r["depot"]: r["sha256"] for r in native["resources"]}
    assert set(new) == DELTA and all(keys[p] == native["providers"][Path(p).stem]["key"] for p in DELTA)
    assert resources == base["source_resources"] | new
    assert not DELTA.intersection(base["source_resources"])

    previous_files = {r["path"]: r["sha256"] for r in base["files"]}
    leaves = previous_files | {ARCHIVE: packed["archive_sha256"]}
    assert {p for p in leaves if leaves[p] != previous_files[p]} == {ARCHIVE}
    package = CANDIDATE / "package"
    assert len(leaves) == 51 and set(leaves) == {p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()}
    files = []
    for relative, digest in sorted(leaves.items()):
        path = checked(package / relative, digest)
        files.append({"path": relative, "sha256": digest, "bytes": path.stat().st_size})
    write(CANDIDATE / "package_manifest.json", {
        "status": "STAGED_JUDY_TRAVEL_SMS_READBACK_VERIFIED",
        "predecessor": "QR19", "files": files, "source_resources": resources,
        "changed_paths": [ARCHIVE], "added_official_depot_overrides": sorted(DELTA),
        "retained_archive_members": 1577, "installed_paths_verified": 77,
        "installed": False, "gameplay_validation": "UNTESTED",
    })
    print(f"Verified {len(files)} staged package paths and {len(resources)} archived payloads")


if __name__ == "__main__":
    assert __debug__, "Run staging with assertions enabled"
    cli = argparse.ArgumentParser()
    cli.add_argument("phase", choices=("stage", "seal"))
    {"stage": stage, "seal": seal}[cli.parse_args().phase]()
