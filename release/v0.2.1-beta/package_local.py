"""Package the pinned WO1 build and verify its byte-identical local installation."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[2]
VERSION = "v0.2.1-beta"
OUTPUT = ROOT / "dist" / VERSION
ZIP_NAME = f"Post-Tower-Continuation-and-Free-Roam-{VERSION}.zip"
WO1 = ROOT / "prealpha/world_overlap_20261116_01/work"
BASELINE = WO1 / "deployment_01/installed_manifest_01.json"
BASELINE_SHA = "F9AA02A1C70BE28CB1C0B343C542FD5B204CAAE9048EDF94C8AD281FBED63A05"
PROOFS = {
    "archive_01/readback.json": "6180A2E5401C2F8BA7448ADAEF1547EE021AFFDC73F46FC54F721F5F97F5D957",
    "xl_assessment.json": "E3B5C9976798E754FC24EBAA9A0B7DDDA319D32A0742BE7F6A041DA7A9F94A35",
    "compile_01/assessment.json": "69A153A41F1B38140403BE12A0809ED96AF5113AE86CED9E25DA65515088044E",
}
OBSOLETE_SHA = "2BA889B1BE2A92989EB09640F8B5C20B92C1CCAE8CAC41150296D8B11D0828DE"
ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
STACK = {
    "Cyberpunk 2077": "2.5 with Phantom Liberty",
    "RED4ext": "1.31.0",
    "redscript": "0.5.32",
    "Cyber Engine Tweaks": "1.38.0",
    "Codeware": "1.21.1",
    "ArchiveXL": "1.28.0",
    "TweakXL": "1.12.0",
}
FRAMEWORK_SOURCES = tuple(f"red4ext/plugins/{name}/Scripts/" for name in ("ArchiveXL", "Codeware", "TweakXL"))
SETTINGS = "bin/x64/plugins/cyber_engine_tweaks/bindings.json"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def plain(path):
    for ancestor in reversed((path, *path.parents)):
        try:
            attrs = ancestor.lstat().st_file_attributes
        except FileNotFoundError:
            continue
        require(not attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT, f"Reparse point: {ancestor}")
    return path


def safe(root, relative):
    for segment in relative.split("/"):
        require(
            re.fullmatch(r"[A-Za-z0-9_. -]+", segment)
            and not segment.endswith((".", " "))
            and not re.match(r"^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.|$)", segment, re.I),
            f"Unsafe path: {relative}",
        )
    return plain(root / relative)


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def file_sha(path):
    with plain(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def json_bytes(value):
    return (json.dumps(value, indent=2) + "\n").encode("utf-8")


def read_json(path, expected_sha=None):
    data = plain(path).read_bytes()
    if expected_sha:
        require(digest(data) == expected_sha, f"JSON hash drift: {path}")
    return json.loads(data)


def create_file(path, data):
    plain(path).parent.mkdir(parents=True, exist_ok=True)
    with plain(path).open("xb") as stream:
        stream.write(data)


def checked_payload(data, row):
    require(len(data) == row["bytes"] and digest(data) == row["sha256"], f"File mismatch: {row['path']}")
    return data


def check_files(root, rows):
    for row in rows:
        path = safe(root, row["path"])
        require(path.stat().st_size == row["bytes"] and file_sha(path) == row["sha256"], f"File mismatch: {path}")


def inputs():
    baseline = read_json(BASELINE, BASELINE_SHA)
    rows = baseline["core_files"]
    paths = {row["path"].casefold() for row in rows}
    require(baseline["core_epoch"] == "WO1_STREET_OVERLAP_CLEANUP" and len(paths) == len(rows) == 51,
            "Unexpected WO1 payload")
    require(Path(baseline["source_candidate"]) == WO1 / "candidate_01", "Unexpected source candidate")
    beta = read_json(ROOT / "release/manifest-v0.2.0-beta.json",
                     "DF44EEC3FEBD74CF8EA2F6DAEAC4338E2E3B7E9C85195B71DAF7637E222964E4")
    require({row["path"] for row in rows} == {row["path"] for row in beta["files"]}, "Beta paths changed")
    return baseline, beta


def obsolete_catalog(baseline):
    current = {row["path"].casefold() for row in baseline["core_files"] + baseline["required_files"]}
    entries = {}
    for path in (
        "release/manifest.json",
        "release/manifest-v0.1.1-alpha.20261024.json",
        "prealpha/full_consolidation_v1/candidate_01/install_manifest_01.json",
    ):
        old = read_json(ROOT / path)
        for row in old.get("old_files", old.get("files", [])):
            if row["path"].casefold() not in current:
                entries.setdefault(row["path"], set()).add(row["sha256"])
    catalog = {
        "purpose": "AI/manual cleanup without an old ZIP or backups",
        "files": [{"path": path, "accepted_sha256": sorted(shas)} for path, shas in sorted(entries.items())],
    }
    require(len(entries) == 124 and digest(json_bytes(catalog)) == OBSOLETE_SHA, "Reviewed obsolete catalogue changed")
    return catalog


def references(baseline, beta, obsolete):
    release = ROOT / "release"
    ai = plain(release / "AI_CLEANUP_INSTRUCTIONS.md").read_text(encoding="utf-8")
    manual = plain(release / "MANUAL_CLEANUP_INSTRUCTIONS.md").read_text(encoding="utf-8")
    ai = ai.replace("Open Beta 0.2.0", "Beta 0.2.1", 1)
    ai = ai.replace("The player requests deletion of verified obsolete files rather than archiving\nthem.",
                    "Perform cleanup only when the player requests it.")
    manual = manual.replace("Open Beta 0.2.0", "Beta 0.2.1", 1)
    manual = manual.replace(
        "## Remove the old files",
        "## Requirements and installation\n\n"
        "Use Windows and Cyberpunk 2077 Patch 2.5 with Phantom Liberty. The tested stack uses\n"
        "RED4ext 1.31.0, redscript 0.5.32, Cyber Engine Tweaks 1.38.0, Codeware 1.21.1,\n"
        "ArchiveXL 1.28.0 and TweakXL 1.12.0. Install these frameworks separately.\n\n"
        "For a fresh install, close the game and launcher and merge `archive`, `bin` and\n"
        "`r6` into your game folder. Apply the correction below if Virtual Atelier is\n"
        "installed. Install before your first run of The Tower so the mod can capture\n"
        "pre-ending history.\n\n"
        "## Remove the old files",
    )
    compatibility = beta["required_compatibility"]
    before, after = re.findall(r"```reds\n(.*?)\n```", manual, re.S)
    before = before.replace("\n", "\r\n").encode("utf-8")
    after = after.replace("\n", "\r\n").encode("utf-8")
    original = plain(ROOT / "prealpha/computer_overlay_co1/candidate_02/original/SetupNewTab.reds").read_bytes()
    require(digest(original) == compatibility["supported_original_sha256"] and original.count(before) == 1
            and digest(original.replace(before, after)) == compatibility["patched_sha256"], "Atelier patch mismatch")
    return {
        "readme/AI_CLEANUP_INSTRUCTIONS.md": ai.encode("utf-8"),
        "readme/MANUAL_CLEANUP_INSTRUCTIONS.md": manual.encode("utf-8"),
        "readme/FILES.json": json_bytes({
            "release": VERSION, "file_count": 51, "files": baseline["core_files"],
            "tested_stack": STACK, "required_compatibility": compatibility,
        }),
        "readme/OBSOLETE_FILES.json": json_bytes(obsolete),
    }


def verify_zip(path, rows, docs, unpack_to=None):
    core = {row["path"]: row for row in rows}
    with zipfile.ZipFile(plain(path)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(names) == 55 and set(names) == core.keys() | docs.keys(), "Unexpected ZIP entries")
        require({name.split("/")[0] for name in names} == {"archive", "bin", "r6", "readme"}, "Unexpected ZIP layout")
        for info in infos:
            require(stat.S_ISREG(info.external_attr >> 16) and not info.flag_bits & 1, f"Unexpected ZIP entry type: {info.filename}")
            payload = archive.read(info)  # Reading every member checks its CRC.
            if info.filename in core:
                checked_payload(payload, core[info.filename])
                if unpack_to:
                    create_file(safe(unpack_to, info.filename), payload)
            else:
                require(payload == docs[info.filename], f"Reference mismatch: {info.filename}")


def compile_release(game, unpacked, rows, work, compile_proof):
    expected = compile_proof["staged"]
    framework = {name: sha for name, sha in expected.items() if name.startswith(FRAMEWORK_SOURCES)}
    stage = work / "compile"
    scripts = stage / "scripts"
    cache = stage / "cache"
    modified_inputs = {}
    for row in rows:
        name = row["path"]
        if name.endswith(".reds"):
            require(expected.get(name) == row["sha256"], f"Core compile input drift: {name}")
            create_file(safe(scripts, name), checked_payload(safe(unpacked, name).read_bytes(), row))
            modified_inputs[name] = row["sha256"]
    require(len(modified_inputs) == 46 and len(framework) == 10, "Unexpected standalone compile inputs")
    compiler = safe(game, "engine/tools/scc.exe")
    paths = {safe(game, name): sha for name, sha in framework.items()}
    for rel in ("engine/tools/scc.exe", "r6/cache/final.redscripts"):
        path = safe(game, rel)
        matches = [sha for original, sha in compile_proof["input_pins"].items() if Path(original) == path]
        require(len(matches) == 1, f"Missing pinned compiler input: {rel}")
        paths[path] = matches[0]
    # The game refreshes this timestamp sidecar when it compiles on startup.
    timestamp = safe(game, "r6/cache/final.redscripts.ts")
    paths[timestamp] = file_sha(timestamp)
    for path, sha in paths.items():
        require(file_sha(path) == sha, f"Framework or tool input drift: {path}")
        relative = path.relative_to(game).as_posix()
        if relative in framework:
            create_file(safe(scripts, relative), path.read_bytes())
        elif relative.startswith("r6/cache/"):
            create_file(plain(cache / path.name), path.read_bytes())
    registration = stage / "compile_paths.txt"
    create_file(registration, b"")
    compiled = cache / "compiled.redscripts"
    run = subprocess.run([
        str(compiler), "-compile", str(scripts), "-compilePathsFile", str(registration),
        "-customCacheDir", str(cache), "-outputCacheFile", str(compiled), str(cache / "final.redscripts"),
    ], cwd=stage, capture_output=True, encoding="utf-8", errors="replace", timeout=120,
       creationflags=subprocess.CREATE_NO_WINDOW)
    log = run.stdout + run.stderr
    create_file(stage / "scc.log", log.encode("utf-8"))
    require(run.returncode == 0 and "Compilation complete" in log and compiled.is_file(),
            f"Release compile failed. See {stage / 'scc.log'}")
    require(all(file_sha(path) == sha for path, sha in paths.items()), "Installed compiler inputs changed")
    return {
        "status": "PASS", "core_redscripts": len(modified_inputs), "framework_redscripts": framework,
        "core_inputs": modified_inputs,
        "tools_and_cache": {path.relative_to(game).as_posix(): sha for path, sha in paths.items()
                            if not path.relative_to(game).as_posix().startswith(FRAMEWORK_SOURCES)},
        "compiled_sha256": file_sha(compiled),
    }


def build(baseline, rows, docs):
    game = Path(baseline["game_root"])
    check_files(game, rows + baseline["required_files"])
    proof = {name: read_json(WO1 / name, sha) for name, sha in PROOFS.items()}
    archive = proof["archive_01/readback.json"]
    require(archive["status"] == "MEMBERS_VERIFIED" and len(archive["members"]) == 1749
            and archive["archive_sha256"] == next(row["sha256"] for row in rows if row["path"] == ARCHIVE)
            and proof["xl_assessment.json"]["status"] == "PASS" and proof["compile_01/assessment.json"]["status"] == "PASS",
            "WO1 build proof mismatch")
    plain(OUTPUT).mkdir(exist_ok=True)
    for name in (ZIP_NAME, f"{ZIP_NAME}.sha256", "package-verification.json", "installation.json"):
        require(not safe(OUTPUT, name).exists(), f"Release output already exists: {name}")
    work = safe(OUTPUT, "qualification_02")
    work.mkdir()
    zip_stage = work / ZIP_NAME
    base = WO1 / "candidate_01/package"
    core = {row["path"]: row for row in rows}
    with zipfile.ZipFile(zip_stage, "x") as target:
        for name in sorted(core.keys() | docs.keys()):
            payload = checked_payload(safe(base, name).read_bytes(), core[name]) if name in core else docs[name]
            info = zipfile.ZipInfo(name, (2026, 11, 16, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            target.writestr(info, payload, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    unpacked = work / "core"
    verify_zip(zip_stage, rows, docs, unpack_to=unpacked)
    check_files(unpacked, rows)
    compile_check = compile_release(game, unpacked, rows, work, proof["compile_01/assessment.json"])
    zip_hash = file_sha(zip_stage)
    zip_stage.rename(plain(OUTPUT / ZIP_NAME))
    create_file(OUTPUT / f"{ZIP_NAME}.sha256", f"{zip_hash}  {ZIP_NAME}\n".encode("ascii"))
    result = {
        "status": "PASS", "release": VERSION, "zip": ZIP_NAME, "zip_sha256": zip_hash,
        "zip_bytes": (OUTPUT / ZIP_NAME).stat().st_size, "files": 51, "entries": 55,
        "core_epoch": baseline["core_epoch"], "installed_baseline_sha256": BASELINE_SHA,
        "archive_payloads": len(archive["members"]), "source_proofs": PROOFS, "qualification": work.name,
        "readme_members": sorted(docs), "atelier_example_hash_verified": True,
        "reviewed_obsolete_paths": 124, "release_compile": compile_check,
    }
    create_file(OUTPUT / "package-verification.json", json_bytes(result))
    print(f"PASS {VERSION}: 55 ZIP members, 51 Core files, standalone REDscript compile passed. SHA-256 {zip_hash}")


def game_closed():
    powershell = Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    cmd = "$ErrorActionPreference='Stop'; Get-Process | Select-Object -ExpandProperty ProcessName"
    output = subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-Command", cmd],
                            check=True, capture_output=True, text=True, errors="replace", timeout=20,
                            creationflags=subprocess.CREATE_NO_WINDOW).stdout
    processes = {name.strip().casefold() for name in output.splitlines()}
    require(bool(processes), "Windows process list unavailable")
    running = processes & {"cyberpunk2077", "redlauncher", "redprelauncher"}
    require(not running, f"Close the game and launcher before checking installation: {sorted(running)}")


def inventory(root, exact=False, skip=()):
    excluded = {path.casefold() for path in skip}
    tree = []
    for folder, dirs, files in os.walk(plain(root), onerror=lambda error: require(False, str(error))):
        for name in dirs + files:
            path = Path(folder) / name
            rel = path.relative_to(root).as_posix()
            if rel.casefold() in excluded:
                continue
            info = path.lstat()
            if info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                require(not exact, f"Linked save entry: {path}")
                if name in dirs:
                    dirs.remove(name)
                tree.append((rel, "reparse", info.st_file_attributes))
            elif stat.S_ISDIR(info.st_mode):
                tree.append((rel, "directory"))
            else:
                require(stat.S_ISREG(info.st_mode), f"Unexpected file type: {path}")
                content = file_sha(path) if exact else info.st_mtime_ns
                tree.append((rel, "file", info.st_size, content))
    return {"sha256": digest(json_bytes(sorted(tree))), "files": sum(row[1] == "file" for row in tree)}


def verify_installed(baseline, rows, docs, obsolete, beta):
    """Apply the release manifest to the already matching local installation."""
    game = Path(baseline["game_root"])
    saves = Path(baseline["save_root"])
    game_closed()
    require(not (OUTPUT / "installation.json").exists(), "Installation receipt already exists")
    result = read_json(OUTPUT / "package-verification.json")
    package = plain(OUTPUT / ZIP_NAME)
    zip_hash = file_sha(package)
    require(result["status"] == result["release_compile"]["status"] == "PASS"
            and result["installed_baseline_sha256"] == BASELINE_SHA and zip_hash == result["zip_sha256"]
            and (OUTPUT / f"{ZIP_NAME}.sha256").read_bytes() == f"{zip_hash}  {ZIP_NAME}\n".encode("ascii"),
            "Unverified distribution ZIP")
    check_files(game, rows + baseline["required_files"])
    settings = safe(game, SETTINGS)
    before = (inventory(saves, exact=True), inventory(game, skip=[r["path"] for r in rows]), file_sha(settings))
    verify_zip(package, rows, docs)
    old_present = [row["path"] for row in obsolete["files"] if safe(game, row["path"]).exists()]
    require(not old_present, f"Review existing obsolete paths: {old_present}")
    compatibility = beta["required_compatibility"]
    atelier_hash = file_sha(safe(game, compatibility["target"]))
    require(atelier_hash == compatibility["patched_sha256"], "Atelier correction mismatch")
    after = (inventory(saves, exact=True), inventory(game, skip=[r["path"] for r in rows]), file_sha(settings))
    require(before == after, "Saves, unmanaged game metadata or CET settings changed during verification")
    check_files(game, rows + baseline["required_files"])
    game_closed()
    create_file(OUTPUT / "installation.json", json_bytes({
        "status": "ALREADY_INSTALLED_VERIFIED", "release": VERSION, "zip_sha256": zip_hash,
        "installed_manifest_sha256": BASELINE_SHA, "verified_core_files": 51, "files_replaced": 0,
        "verified_dependencies": len(baseline["required_files"]), "obsolete_paths_present": old_present,
        "atelier_corrected_sha256": atelier_hash, "saves_before_and_after": before[0],
        "unmanaged_game_metadata_before_and_after": before[1], "cet_bindings_before_and_after": before[2],
    }))
    print(f"ALREADY_INSTALLED_VERIFIED {VERSION}: all 51 ZIP payloads match the game, {before[0]['files']} save files verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("build", "verify-installed"))
    args = parser.parse_args()
    baseline, beta = inputs()
    rows = baseline["core_files"]
    obsolete = obsolete_catalog(baseline)
    docs = references(baseline, beta, obsolete)
    if args.action == "build":
        build(baseline, rows, docs)
    else:
        verify_installed(baseline, rows, docs, obsolete, beta)
