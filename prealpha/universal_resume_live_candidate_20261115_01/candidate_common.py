"""Exact inputs for the local MS31 native handoff candidate."""

from hashlib import file_digest, sha256
import json
from pathlib import Path, PurePosixPath
import re
import stat


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
WORKSPACE = PREALPHA.parent
PRIOR = PREALPHA / "universal_resume_save_session_20261115_01"
ADMISSION = PREALPHA / "universal_resume_save_admission_20261115_01"
BASE = PREALPHA / "universal_resume_checkpoint_probe_20261114_01"
RUNTIME_SOURCE = PREALPHA / "universal_resume_live_runtime_20261115_01/source_01/NativeCheckpoint.cpp"
SDK = WORKSPACE / "research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include"
VCVARS = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat")

LEGACY_BUILD = PRIOR / "run_01"
INSTALLED = PRIOR / "deployment_01/installed_manifest_01.json"
INSTALLED_SHA = "57A78D066D6B7465572FB5F61AA0644AC6D247308C00E4AD1A7E07F59A4AB5C4"
TEMPLATE = PRIOR / "core_manifest_01.json"
TEMPLATE_SHA = "6A07282552CE9728C66A6497CF3F9EC3129314B9C15D822F7305DE5A31141222"
INSTALLER = PRIOR / "deploy_core.ps1"
INSTALLER_SHA = "8C67A8B073B7139B6550A8E5295A1B00E81B365F2D4779B081FF3080EB7A4FAC"
ENGINE_SHA = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"
OLD_DLL_SHA = "70A820D791635CA2AA9455D31BFB95169EA4ECE1943B4C6E77F4E3936F505568"
OLD_INVENTORY_SHA = "406F157EF650C5CB0B7609351753B6B6FC92444E889909549C060D9781018BEB"
ADDRESS_TABLE_SHA = "EAB304F38074145AB5EF53E2AA741576BA00674138761FAFFF23252005948FD4"
LOADER_SHA = "58DDFE43766AA91249D11671B55A8323D5EC017F816D847AFFE4B6201DCD0709"
TARGET = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
SAVE_FIXTURE = {
    "path": "ManualSave-31/sav.dat", "bytes": 4652669,
    "sha256": "2E0F3C99AF3E98601CFC6363BBC068635D0C50ABB32F8E81B2A57B056B02F43D",
}
PRIOR_EPOCH = "RD10_EXECUTION_CHECKPOINT_SAVE_SESSION"
EPOCH = "RD10_EXECUTION_CHECKPOINT_LIVE_HANDOFF"
SCHEMA = f"PTFR_{EPOCH}_CORE_V1"
VERSION = "0.1.8"
REGRESSION_COUNTS = {"SaveAdmissionChecks": 12, "CheckpointChecks": 60, "RegistrationChecks": 15}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_path(path):
    path = Path(path).absolute()
    require(".." not in path.parts, f"Noncanonical path: {path}")
    for item in (path, *path.parents):
        metadata = item.lstat()
        require(not metadata.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT,
                f"Reparse input refused: {item}")
    require(path.is_file(), f"Expected regular file: {path}")
    return path


def workspace_file(path):
    path = checked_path(path)
    require(path.is_relative_to(WORKSPACE), f"Expected a workspace file: {path}")
    return path


def payload_path(root, relative):
    parts = PurePosixPath(relative).parts
    require(parts and all(re.fullmatch(r"[A-Za-z0-9_. -]+", item) and item not in (".", "..")
                          and not item.endswith((".", " ")) for item in parts),
            f"Unsafe payload path: {relative}")
    require("/".join(parts) == relative, f"Noncanonical payload path: {relative}")
    return root.joinpath(*parts)


def digest(path):
    path = checked_path(path)
    before = path.stat()
    with path.open("rb") as stream:
        result = file_digest(stream, "sha256").hexdigest().upper()
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns),
            f"File changed during hash: {path}")
    return result


def pin(path, sha, size=None):
    path = checked_path(path)
    require(re.fullmatch(r"[A-Fa-f0-9]{64}", sha) and digest(path) == sha.upper(), f"Hash drift: {path}")
    require(size is None or path.stat().st_size == size, f"Size drift: {path}")
    return path


def load(path, sha):
    path = checked_path(path)
    raw = path.read_bytes()
    require(sha256(raw).hexdigest().upper() == sha.upper(), f"Hash drift: {path}")
    return json.loads(raw)


def write_json(path, record):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(record, stream, indent=2)
        stream.write("\n")


def read_inventory(path, sha):
    inventory = load(path, sha)
    require(inventory and all(files for files in inventory.values()), f"Empty compile inventory: {path}")
    return {group: {Path(WORKSPACE / name): expected for name, expected in files.items()}
            for group, files in inventory.items()}


def verify_inventory(inventory):
    merged = {}
    for files in inventory.values():
        for path, expected in files.items():
            if path in merged:
                require(merged[path] == expected, f"Conflicting compile input hashes: {path}")
                continue
            pin(path, expected)
            merged[path] = expected
    return merged


def verify_installed():
    baseline = load(INSTALLED, INSTALLED_SHA)
    require(baseline["core_epoch"] == PRIOR_EPOCH and baseline["checkpoint_version"] == "0.1.7",
            "Wrong installed predecessor")
    groups = ("core_files", "companion_files", "required_files")
    require(tuple(len(baseline[group]) for group in groups) == (51, 1, 26), "Installed inventory size drift")
    companion, = baseline["companion_files"]
    require(companion["path"] == TARGET and companion["sha256"] == OLD_DLL_SHA, "Installed checkpoint scope drift")
    game = Path(baseline["game_root"])
    seen = set()
    for group in groups:
        for row in baseline[group]:
            require(row["path"].lower() not in seen, f"Overlapping installed path: {row['path']}")
            seen.add(row["path"].lower())
            pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    pin(game / "bin/x64/Cyberpunk2077.exe", ENGINE_SHA)
    pin(game / "bin/x64/cyberpunk2077_addresses.json", ADDRESS_TABLE_SHA)
    pin(game / "red4ext/RED4ext.dll", LOADER_SHA)
    pin(payload_path(Path(baseline["save_root"]), SAVE_FIXTURE["path"]), SAVE_FIXTURE["sha256"], SAVE_FIXTURE["bytes"])
    return baseline
