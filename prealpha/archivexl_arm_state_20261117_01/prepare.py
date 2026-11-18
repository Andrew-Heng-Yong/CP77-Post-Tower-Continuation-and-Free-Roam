"""Qualify the official ArchiveXL release against the current Tower installation."""

import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from zipfile import ZipFile


TASK = Path(__file__).absolute().parent
WORK = TASK / "work"
PREDECESSOR = TASK.parent / "tower_arm_refresh_20261117_01"
BASELINE = PREDECESSOR / "installed_manifest.json"
REVIEW = WORK / "package_review.json"
ZIP = WORK / "ArchiveXL-1.28.7.zip"
PACKAGE = WORK / "package_01"
COMPILE = WORK / "compile_01"
TEMPLATE = TASK.parent / "kold_mirage_gate_20261116_01/work/deploy_core.ps1"
ARCHIVEXL = "red4ext/plugins/ArchiveXL"
CHANGES = {f"{ARCHIVEXL}/{name}" for name in (
    "ArchiveXL.dll",
    "Bundle/ArchiveXL.archive",
    "Bundle/PlayerCustomizationBeardFix.xl",
    "Bundle/PlayerCustomizationHairFix.xl",
    "Bundle/PlayerCustomizationHairScope.xl",
    "Scripts/ArchiveXL.DynamicAppearance.reds",
    "Scripts/ArchiveXL.Global.reds",
    "Scripts/ArchiveXL.reds",
)}
ZIP_SHA = "8936787D7D5C7B9F9C60BE1F08DC93C8AFCE8040704C2F5965F474E10E010CAD"

# The inspected predecessor module has a guarded main. Reuse its path and hash checks.
sys.dont_write_bytecode = True
sys.path.insert(0, str(PREDECESSOR))
from build import GAME, SAVES, compiler_sources, plain, read, row, safe, sha, verify_rows, write


def stage() -> list[dict]:
    if sha(ZIP) != ZIP_SHA or sha(REVIEW) != "EB34B2FEED71FD2BD3D115B5D0D9CB02A2A9A6C0E7747BA2ED0BEE434FA5C101":
        raise RuntimeError("ArchiveXL release or reviewed file inventory changed")
    review = read(REVIEW)
    files = review["files"]
    if len(files) != 29 or {item["path"] for item in files if item["action"] != "same"} != CHANGES:
        raise RuntimeError("Unexpected ArchiveXL update scope")
    PACKAGE.mkdir(exist_ok=False)
    manifest_rows = []
    with ZipFile(ZIP) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Damaged ArchiveXL package")
        for item in files:
            path = item["path"]
            before = row(GAME, path)
            if before["sha256"] != item["before_sha256"] or before["bytes"] != item["before_bytes"]:
                raise RuntimeError(f"Installed ArchiveXL file changed: {path}")
            data = archive.read(path)
            target = safe(PACKAGE, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            after = row(PACKAGE, path)
            if after["sha256"] != item["after_sha256"] or after["bytes"] != item["after_bytes"]:
                raise RuntimeError(f"Staged ArchiveXL file changed: {path}")
            if path.endswith(".reds"):
                old = safe(GAME, path).read_bytes()
                if old.count(b"// ArchiveXL 1.28.0") != 1 or old.replace(b"// ArchiveXL 1.28.0", b"// ArchiveXL 1.28.7", 1) != data:
                    raise RuntimeError(f"Changed REDscript beyond its version comment: {path}")
            manifest_rows.append({"path": path, "before": before["sha256"], "before_bytes": before["bytes"],
                                  "after": after["sha256"], "after_bytes": after["bytes"]})
    dll = safe(PACKAGE, f"{ARCHIVEXL}/ArchiveXL.dll").read_bytes()
    pe_offset = struct.unpack_from("<I", dll, 0x3C)[0]
    if dll[:2] != b"MZ" or dll[pe_offset:pe_offset + 6] != b"PE\x00\x00\x64\x86":
        raise RuntimeError("The release DLL is not x64 PE")
    return manifest_rows


def compile_current(files: list[dict]) -> dict:
    sources = compiler_sources()
    registry = safe(GAME, "r6/logs/redscript_rCURRENT.log")
    log = registry.read_text(encoding="utf-8-sig")
    registered = set()
    for line in log.splitlines():
        value = line.strip()
        if value.lower().endswith(".reds"):
            path = Path(value)
            registered.add(path if path.is_absolute() else GAME / "r6/scripts" / path)
    if "Compilation complete" not in log or registered != set(sources.values()):
        raise RuntimeError("Registered REDscript source set differs from installed sources")
    compiler = safe(GAME, "engine/tools/scc.exe")
    cache_inputs = [safe(GAME, f"r6/cache/{name}") for name in ("final.redscripts", "final.redscripts.ts")]
    pins = {str(path): sha(path) for path in (*sources.values(), registry, compiler, *cache_inputs)}
    scripts = COMPILE / "scripts"
    cache = COMPILE / "cache"
    cache.mkdir(parents=True, exist_ok=False)
    changes = {item["path"]: item["after"] for item in files if item["path"].endswith(".reds")}
    if changes.keys() - sources.keys():
        raise RuntimeError("ArchiveXL REDscript replacement is outside the registered inventory")
    staged = {}
    for name, path in sources.items():
        destination = safe(scripts, name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(safe(PACKAGE, name) if name in changes else path, destination)
        staged[name] = sha(destination)
        if staged[name] != changes.get(name, pins[str(path)]):
            raise RuntimeError(f"Compile source copy mismatch: {name}")
    for path in cache_inputs:
        destination = cache / path.name
        shutil.copyfile(path, destination)
        if sha(destination) != pins[str(path)]:
            raise RuntimeError(f"Base cache copy mismatch: {path}")
    paths = COMPILE / "compile_paths.txt"
    paths.write_bytes(b"")
    output = cache / "compiled.redscripts"
    command = [str(value) for value in (compiler, "-compile", scripts, "-compilePathsFile", paths,
               "-customCacheDir", cache, "-outputCacheFile", output, cache / "final.redscripts")]
    result = subprocess.run(command, cwd=COMPILE, capture_output=True, encoding="utf-8",
                            errors="replace", timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
    build_log = result.stdout + result.stderr
    (COMPILE / "scc.log").write_text(build_log, encoding="utf-8")
    if result.returncode or "Compilation complete" not in build_log or not output.is_file():
        raise RuntimeError(f"Offline compile failed: {build_log[-4000:]}")
    if compiler_sources() != sources or any(sha(Path(path)) != digest for path, digest in pins.items()):
        raise RuntimeError("Live compiler inputs changed during the offline build")
    write(COMPILE / "assessment.json", {"status": "PASS", "source_count": len(sources),
          "staged_sources": staged, "live_inputs": pins, "compiled_sha256": sha(output),
          "changed_script_comments_only": sorted(changes), "game_writes": 0})
    print(f"Compiled all {len(sources)} registered sources with the ArchiveXL release scripts.")
    return pins


def main() -> None:
    for path in (TASK, WORK, GAME, SAVES, BASELINE, ZIP, REVIEW, TEMPLATE):
        plain(path)
    if sha(BASELINE) != "B8A5A7D558CBA805B08CAE066460DA2F5EBD704700E52553E088CE8163920338":
        raise RuntimeError("Recorded Tower baseline changed")
    if sha(TEMPLATE) != "E04403763302BAC9B39721435359F099C1C8FB96B60C2F5C02751A0524695EB1":
        raise RuntimeError("Reviewed installer template changed")
    baseline = read(BASELINE)
    if len(baseline["core_files"]) != 51 or baseline["core_epoch"] != "TOWER_ARM_AND_PHOTO_MODE_REFRESH_TEST":
        raise RuntimeError("Unexpected installed Tower build")
    prior = baseline["core_files"] + baseline["required_files"] + baseline["ifp_files"]
    verify_rows(GAME, prior)
    files = stage()
    pins = compile_current(files)
    managed = {item["path"] for item in files}
    protected = {item["path"]: dict(item, active_only=False) for item in prior if item["path"] not in managed}
    for item in baseline["preferences_at_install"]:
        path = item["path"]
        protected[path] = dict(row(GAME, path), active_only=False)
    proof_files = (BASELINE, REVIEW, COMPILE / "assessment.json")
    manifest = WORK / "tool_manifest_01.json"
    write(manifest, {"schema": "PTFR_ARCHIVEXL_1_28_7_V1", "component": "ArchiveXL",
        "source_epoch": "ARCHIVEXL_1_28_7", "predecessor_epoch": "ARCHIVEXL_1_28_0",
        "game_root": str(GAME), "save_root": str(SAVES), "package_root": str(PACKAGE),
        "process_names": ["Cyberpunk2077", "REDlauncher", "REDprelauncher"], "files": files,
        "required_files": list(protected.values()), "protected_saves": [], "working_save_files": [],
        "zip": str(ZIP), "zip_sha256": ZIP_SHA, "compile_inputs": pins,
        "proofs": [{"path": str(path), "sha256": sha(path)} for path in proof_files]})

    code = TEMPLATE.read_text(encoding="utf-8-sig")
    replacements = {
        "[ValidateSet('Core')][string]$Component='Core'": "[ValidateSet('ArchiveXL')][string]$Component='ArchiveXL'",
        "# Replace the qualified KOLD entry archive after installation authorization.": "# Update the eight changed official ArchiveXL release files.",
        "$PinnedCoreManifestSHA='07327F59484012AC446196A64CAC44BB5652262010C9F54CE109856041B6009C'": f"$PinnedCoreManifestSHA='{sha(manifest)}'",
        "'core_manifest_01.json'": "'tool_manifest_01.json'",
        "'PTFR_KM3_KOLD_PREPARED_ENTRY_CORE_V1'": "'PTFR_ARCHIVEXL_1_28_7_V1'",
        "'KM3_KOLD_PREPARED_ENTRY'": "'ARCHIVEXL_1_28_7'",
        "'RD10_MID_QUEST_RESUME_RETIRED'": "'ARCHIVEXL_1_28_0'",
        "'recovery/kold_gate_01'": "'recovery/archivexl_01'",
        "$wanted=@('archive/pc/mod/zzzz_PTFR_Combined.archive')": "$wanted=@(" + ",".join(f"'{p}'" for p in sorted(CHANGES)) + ")",
        "$manifest.files.Count -ne 51 -or $changes.Count -ne 1": "$manifest.files.Count -ne 29 -or $changes.Count -ne 8",
        "KOLD archive-only scope drift": "ArchiveXL exact-file scope drift",
    }
    for old, new in replacements.items():
        if code.count(old) != 1:
            raise RuntimeError(f"Installer template replacement is not unique: {old}")
        code = code.replace(old, new, 1)
    installer = WORK / "install.ps1"
    with installer.open("x", encoding="utf-8", newline="\r\n") as stream:
        stream.write(code)
    write(WORK / "scope_review.json", {"status": "PASS", "release_sha256": ZIP_SHA,
          "installer_sha256": sha(installer), "manifest_sha256": sha(manifest),
          "template_sha256": sha(TEMPLATE), "changing_paths": sorted(CHANGES),
          "protected_file_hashes": len(protected), "tower_files": len(baseline["core_files"]),
          "user_authorization": "ok update archive xl and try its arm state fix"})
    print(json.dumps({"status": "STAGED", "managed": len(files), "replacements": len(CHANGES),
                      "protected": len(protected), "manifest_sha256": sha(manifest)}))


if __name__ == "__main__":
    main()
