"""Prepare the save-compatible RD10 build with the exact-resume experiment detached."""

from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
sys.path.insert(0, str(PREALPHA / "universal_resume_live_candidate_20261115_01"))
from candidate_common import ENGINE_SHA, digest, load, payload_path, pin, require, write_json

CURRENT = PREALPHA / "quest_resume_travel_20261115_01/staged_01/deployment_01/installed_manifest_01.json"
CURRENT_SHA = "4515664293C0646B4ED5C51051F6FD4877F6418CB66015921FF7E9410EBA004B"
RD10 = PREALPHA / "resume_dispatcher_rd10_kirk_20261113_01"
DONOR = RD10 / "deployment_01/installed_manifest_01.json"
DONOR_SHA = "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8"
DONOR_FILES = RD10 / "candidate_01/package"
HISTORY = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1"
PREFIX = "r6/scripts/PTFR_Consolidated/"
HS1 = PREFIX + "PTFR_HistorySnapshotHS1.reds"
LUA = HISTORY + "/init.lua"
CORE_REPLACEMENTS = [HS1, PREFIX + "PTFR_SideJobsS22.reds", PREFIX + "PTFR_SideJobsS24.reds", LUA]
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
CACHE = "r6/cache/final.redscripts.modded"
BLOCKED_SYMBOLS = (
    b"ReadExecutionCheckpoint", b"DecodeExecutionCheckpoint", b"ExecutionCheckpointJSON",
    b"ExecutionProbeHS3", b"PTFRSharedCassiusOwner", b"SharedCassiusResume", b"CassiusResumeBridge",
    b"checkpoint_execution_",
)
STAGE = HERE / "stage_02"


def stage_core(baseline, donor, package):
    game = Path(baseline["game_root"])
    expected = {row["path"]: row for row in baseline["core_files"]}
    approved = {row["path"]: row for row in donor["core_files"]}
    require(set(expected) == set(approved) and len(expected) == 51, "Core file inventory drift")
    require({p for p in expected if expected[p]["sha256"] != approved[p]["sha256"]} == set(CORE_REPLACEMENTS),
            "Pre-experiment donor differs outside the exact-resume overlays")
    result = {}
    current = payload_path(game, HS1).read_bytes()
    fields = re.findall(rb"^  private persistent let executionCheckpoint\w+: [^\r\n]+;\r?$",
                        current, re.MULTILINE)
    require(len(fields) == 8 and len(set(fields)) == 8, "Checkpoint persistence layout drift")
    for path in CORE_REPLACEMENTS:
        row = approved[path]
        exact = pin(payload_path(DONOR_FILES, path), row["sha256"], row["bytes"])
        data = exact.read_bytes()
        require(not any(symbol in data for symbol in BLOCKED_SYMBOLS), f"Resume code in pre-experiment donor: {path}")
        if path == HS1:
            anchor = b"public class CaptureArchiveHS3 extends ScriptableSystem {\n"
            require(data.count(anchor) == 1, "History persistence insertion point changed")
            preserved = b"".join(field.rstrip(b"\r") + b"\n" for field in fields)
            inert = b"  // Reserved for saves written with the archived native checkpoint feature.\n" + preserved + b"\n"
            data = data.replace(anchor, anchor + inert, 1)
            require(data.replace(anchor + inert, anchor, 1) == exact.read_bytes(),
                    "History source differs beyond the existing saved fields")
            for field in fields:
                name = field.split(b"let ", 1)[1].split(b":", 1)[0]
                require(data.count(name) == 1, f"Archived field is used by runtime: {name!r}")
        target = payload_path(package, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        result[path] = dict(sha256=digest(target), bytes=len(data))
    return result, [f.strip().decode("ascii") for f in fields]


def compile_scripts(game, package):
    compiler = game / "engine/tools/scc.exe"
    cache = [game / "r6/cache" / p for p in ("final.redscripts", "final.redscripts.ts")]
    sources = {p for root in ("r6/scripts", "red4ext/plugins") for p in (game / root).rglob("*.reds")}
    registries = sorted((game / "r6/logs").glob("redscript*.log"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    registry = None
    for path in registries:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        listed = {(game / "r6/scripts" / line.strip()).resolve()
                  for line in text.splitlines() if line.strip().lower().endswith(".reds")}
        if listed == sources and "Compilation complete" in text:
            registry = path
            break
    require(registry and len(sources) == 148, "Registered REDscript source inventory changed")
    inputs = {path: digest(path) for path in sorted(sources | {compiler, registry, *cache})}
    out = STAGE / "compile"
    (out / "cache").mkdir(parents=True)
    for path in cache:
        shutil.copyfile(path, out / "cache" / path.name)
    staged = {}
    for path in sorted(sources):
        relative = path.relative_to(game).as_posix()
        source = payload_path(package, relative) if relative in CORE_REPLACEMENTS else path
        target = out / "scripts" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        require(not any(symbol in target.read_bytes() for symbol in BLOCKED_SYMBOLS),
                f"Active checkpoint symbol survived in {relative}")
        staged[relative] = digest(target)
    paths = out / "compile_paths.txt"
    paths.write_bytes(b"")
    target = out / "cache/compiled.redscripts"
    command = [compiler, "-compile", out / "scripts", "-compilePathsFile", paths,
               "-customCacheDir", out / "cache", "-outputCacheFile", target, out / "cache/final.redscripts"]
    result = subprocess.run(list(map(str, command)), capture_output=True, encoding="utf-8",
                            errors="replace", timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    output = result.stdout + result.stderr
    (out / "scc.log").write_text(output, encoding="utf-8")
    require(result.returncode == 0 and "Compilation complete" in output and target.is_file(), output[-22000:])
    image = target.read_bytes()
    require(not any(symbol in image for symbol in BLOCKED_SYMBOLS), "Compiled cache retains active resume symbols")
    require(all(digest(p) == expected for p, expected in inputs.items()), "Live compiler inputs changed")
    report = out / "assessment.json"
    write_json(report, dict(status="PASS", sources=len(staged), input_pins={str(p): sha for p, sha in inputs.items()},
                            staged=staged, compiled_sha256=digest(target)))
    return report


def main():
    current, donor = load(CURRENT, CURRENT_SHA), load(DONOR, DONOR_SHA)
    game = Path(current["game_root"])
    for group, count in (("core_files", 51), ("companion_files", 1), ("required_files", 26)):
        require(len(current[group]) == count, f"Installed {group} drift")
        for row in current[group]:
            pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    pin(game / "bin/x64/Cyberpunk2077.exe", ENGINE_SHA)
    STAGE.mkdir()
    replacements, fields = stage_core(current, donor, STAGE / "files")
    compile_report = compile_scripts(game, STAGE / "files")
    write_json(STAGE / "preparation.json", dict(status="PASS", replacements=replacements,
               preserved_saved_fields=fields, compile_report_sha256=digest(compile_report)))
    print("Prepared four Core replacements. All 148 registered REDscript sources compiled without active resume symbols.")


if __name__ == "__main__":
    main()
