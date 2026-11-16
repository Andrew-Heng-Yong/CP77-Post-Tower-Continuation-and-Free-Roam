"""Validate the checkpoint probe against the installed v0.1.3 inputs.

Reads the live installation. All compile, fixture and package outputs are
created in this successor directory. No install or live game call is made.
"""

import argparse
from collections import Counter
from hashlib import file_digest
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
PREVIOUS = PREALPHA / "universal_resume_checkpoint_diagnostics_20261114_01"
BASELINE = PREVIOUS / "deployment_01/installed_manifest_01.json"
BASELINE_SHA = "C5C08A48045DFB034DC23CAB4F2474330B88701E43391C3584EA5BE4AC2656D5"
ORIGINAL_COMPILE = PREALPHA / "universal_resume_checkpoint_runtime_20261114_01/compile_02/cache/compiled.redscripts"
ORIGINAL_COMPILE_SHA = "B1EAF9D2AD920239D2262D673A4EFA1627EB8CC300E23C0F58F6D87CE321A38C"
HISTORY = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
CACHE = "r6/cache/final.redscripts"
CACHE_TS = CACHE + ".ts"
SCC = "engine/tools/scc.exe"
REGISTRY = "r6/logs/redscript_rCURRENT.log"
SOURCES = HERE / "source_02"
BUILD = HERE / "build_01"
COMPILE = HERE / "compile_02"
CHECKS = HERE / "checks_01"
CANDIDATE = HERE / "candidate_01"
MANIFEST = HERE / "core_manifest_01.json"
SCHEMA = "PTFR_RD10_EXECUTION_CHECKPOINT_PROBE_CORE_V1"
EPOCH = "RD10_EXECUTION_CHECKPOINT_PROBE"
SCOPE = "Install v0.1.4 checkpoint probe and the inline gate writer repair for the shared execution collector."


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def pinned(path, digest):
    assert sha(path) == digest, path
    return path


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def baseline():
    installed = read(pinned(BASELINE, BASELINE_SHA))
    transaction = read(pinned(PREVIOUS / "core_manifest_01.json", installed["core_transaction_sha256"]))
    assert installed["core_epoch"] == transaction["source_epoch"] == "RD10_EXECUTION_CHECKPOINT_DIAGNOSTICS"
    assert len(installed["core_files"]) == 51 and len(installed["companion_files"]) == 1
    assert installed["companion_files"][0]["path"] == DLL
    assert len(installed["required_files"]) == 26
    return installed, transaction


def invoke(command, directory, log):
    result = subprocess.run([str(arg) for arg in command], cwd=directory, capture_output=True, timeout=180,
                            encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW)
    output = result.stdout + result.stderr
    with log.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(output)
    assert result.returncode == 0, output[-6500:]
    return output


def check_script_additions(old_path, new_path):
    # The new public request and its queue receiver are an additive overlay.
    blocks = ((b"public class ExecutionProbeHS3 extends ScriptableSystemRequest {",
               b"public class FileBeginRequestHS4 extends ScriptableSystemRequest {"),
              (b"  public func RequestExecutionProbe() -> Bool {", b"  private func ReadExecution(reader:"))
    after = new_path.read_bytes()
    for start, end in blocks:
        assert after.count(start) == after.count(end) == 1
        first = after.index(start)
        last = after.index(end, first)
        after = after[:first] + after[last:]
    assert after == old_path.read_bytes(), "unexpected history source edits"


def compiled_contract(path):
    sys.path.insert(0, str(HERE.parents[1] / "research/redscript_2_5/binary_reader_01"))
    from diagnose_01 import parse

    owner = "PTFR.HistorySnapshotHS1.CaptureArchiveHS3"

    def inspect(compiled):
        raw, header, _, rows = parse(compiled)
        assert header["version"] == 14
        fields, methods, natives = {}, set(), Counter()
        for row in rows:
            parent = rows[row["parent"]]["name"] if row["parent"] else ""
            if row["type"] == 5:
                if parent == owner:
                    methods.add(row["name"])
                if row["size"] >= 5 and struct.unpack_from("<I", raw, row["offset"] + 1)[0] & 0x10:
                    natives[parent, row["name"]] += 1
            if row["type"] == 8 and parent == owner:
                type_id, flags = struct.unpack_from("<II", raw, row["offset"] + 1)
                fields[row["name"]] = (rows[type_id]["name"], flags)
        return fields, methods, natives

    before_fields, before_methods, before_natives = inspect(pinned(ORIGINAL_COMPILE, ORIGINAL_COMPILE_SHA))
    after_fields, after_methods, after_natives = inspect(path)
    assert before_fields == after_fields
    assert before_methods.issubset(after_methods)
    added = {name.split(";", 1)[0] for name in after_methods - before_methods}
    assert added == {"RequestExecutionProbe", "OnExecutionProbeHS3"}
    assert before_natives == after_natives
    return {"added_methods": sorted(added), "history_field_layout_matches": True, "new_native_declarations": 0}


def compile_scripts():
    installed, transaction = baseline()
    game = Path(installed["game_root"])
    inputs = {}
    for absolute, digest in transaction["compile_inputs"].items():
        path = Path(absolute)
        relative = path.relative_to(game).as_posix()
        inputs[relative] = sha(path)
        if relative not in (CACHE_TS, REGISTRY):
            assert inputs[relative] == digest, path
    sources = {p for p in inputs if p.lower().endswith(".reds")}
    paths = {(game / path).resolve() for path in sources}
    actual = {path.resolve() for root in ("r6/scripts", "red4ext/plugins") for path in (game / root).rglob("*.reds")}
    registry = (game / REGISTRY).read_text(encoding="utf-8-sig")
    logged = {(game / "r6/scripts" / line.strip()).resolve() for line in registry.splitlines()
              if line.strip().lower().endswith(".reds")}
    assert len(sources) == 148 and paths == actual == logged and "Compilation complete" in registry
    source_receipt = SOURCES / "receipt.json"
    history = SOURCES / Path(HISTORY).name
    pinned(history, read(source_receipt)["sources"][history.name])
    check_script_additions(game / HISTORY, history)

    cache = COMPILE / "cache"
    cache.mkdir(parents=True, exist_ok=False)
    for path in (CACHE, CACHE_TS):
        shutil.copyfile(game / path, cache / Path(path).name)
        pinned(cache / Path(path).name, inputs[path])
    staged = {}
    for path in sorted(sources):
        target = COMPILE / "scripts" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(history if path == HISTORY else game / path, target)
        staged[path] = sha(target)
        assert staged[path] == (sha(history) if path == HISTORY else inputs[path])
    assert [path for path in staged if staged[path] != inputs[path]] == [HISTORY]

    compiled = cache / "compiled.redscripts"
    path_list = COMPILE / "compile_paths.txt"
    path_list.touch(exist_ok=False)
    output = invoke([game / SCC, "-compile", COMPILE / "scripts", "-compilePathsFile", path_list,
                     "-customCacheDir", cache, "-outputCacheFile", compiled, cache / "final.redscripts"],
                    COMPILE, COMPILE / "scc.log")
    assert "Compilation complete" in output and compiled.is_file()
    for path, digest in inputs.items():
        pinned(game / path, digest)
    write(COMPILE / "receipt.json", {"source_count": len(sources), "compiler_inputs": inputs,
                                     "staged_sources": staged, "compiled_sha256": sha(compiled),
                                     "source_receipt_sha256": sha(source_receipt),
                                     "script_contract": compiled_contract(compiled)})
    print(f"Compiled and read back {len(sources)} registered REDscript sources.")


def run_checks():
    CHECKS.mkdir(exist_ok=False)
    reports = {}
    for label, binary in (("checkpoint", "CheckpointChecks.exe"), ("registration", "RegistrationChecks.exe")):
        exe = BUILD / binary
        report = invoke([exe], BUILD, CHECKS / (label + ".log"))
        assert not any(line.startswith("FAIL ") for line in report.splitlines()), label
        reports[label] = [line.removeprefix("PASS ") for line in report.splitlines() if line.startswith("PASS ")]
        if label == "checkpoint":
            payload, = (json.loads(line[8:]) for line in report.splitlines() if line.startswith("PAYLOAD "))
            assert payload["origin"] == "pre_native_cleanup" and payload["route"] == 1
            assert payload["graph_facts"][1] == [[3673229151, 70]] and len(payload["timings"]) == 2
    assert len(reports["checkpoint"]) == 51 and len(reports["registration"]) == 15
    reports["dll_sha256"] = sha(BUILD / Path(DLL).name)
    write(CHECKS / "results.json", reports)
    print("Passed 51 checkpoint and probe checks and 15 registration checks.")


def prepare():
    assert not CANDIDATE.exists() and not MANIFEST.exists()
    installed, manifest = baseline()
    game = Path(installed["game_root"])
    managed = {row["path"]: row for row in installed["core_files"] + installed["companion_files"]}
    assert len(managed) == 52 and len(manifest["files"]) == 52
    assert manifest["required_files"] == installed["required_files"]
    for row in [*managed.values(), *installed["required_files"]]:
        target = pinned(game / row["path"], row["sha256"])
        assert target.stat().st_size == row["bytes"]

    compiled = read(COMPILE / "receipt.json")
    assert compiled["source_count"] == 148 and compiled["script_contract"]["history_field_layout_matches"]
    for path, digest in compiled["compiler_inputs"].items():
        pinned(game / path, digest)
    checks = read(CHECKS / "results.json")
    assert len(checks["checkpoint"]) == 51 and len(checks["registration"]) == 15
    source_receipt = pinned(SOURCES / "receipt.json", compiled["source_receipt_sha256"])
    build = read(BUILD / "build.json")
    build_files = {row["name"]: row["sha256"] for row in build}
    for name in ("NativeCheckpoint.cpp", "Checkpoint.hpp", "CheckpointChecks.cpp"):
        pinned(SOURCES / name, build_files[name])
        assert build_files[name] == read(source_receipt)["sources"][name]
    assert build_files[Path(DLL).name] == checks["dll_sha256"]
    changes = {HISTORY: pinned(SOURCES / Path(HISTORY).name, compiled["staged_sources"][HISTORY]),
               DLL: pinned(BUILD / Path(DLL).name, checks["dll_sha256"])}
    package = CANDIDATE / "files"
    for path, donor in changes.items():
        target = package / path
        target.parent.mkdir(parents=True, exist_ok=False)
        shutil.copyfile(donor, target)
        pinned(target, sha(donor))

    for row in manifest["files"]:
        path = row["path"]
        old = managed[path]
        row.update(before=old["sha256"], before_bytes=old["bytes"],
                   after=old["sha256"], after_bytes=old["bytes"])
        if path in changes:
            row.update(after=sha(package / path), after_bytes=(package / path).stat().st_size)
    delta = {row["path"]: {key: row[key] for key in ("before", "after", "before_bytes", "after_bytes")}
             for row in manifest["files"] if row["before"] != row["after"]}
    assert set(delta) == set(changes)
    receipt = CANDIDATE / "receipt.json"
    write(receipt, {"status": "CHECKPOINT_PROBE_READY_FOR_REVIEW", "version": "0.1.4",
                    "predecessor_manifest_sha256": BASELINE_SHA, "changed_files": delta,
                    "compile_receipt_sha256": sha(COMPILE / "receipt.json"), "checks_sha256": sha(CHECKS / "results.json"),
                    "live_probe_verified": False, "live_cutoff_verified": False})
    manifest.update(schema=SCHEMA, source_epoch=EPOCH, predecessor_epoch=installed["core_epoch"], scope=SCOPE,
                    package_root=str(package), changing_paths=sorted(changes),
                    compile_inputs={str(game / path): digest for path, digest in compiled["compiler_inputs"].items()},
                    proofs=[{"path": str(path), "sha256": sha(path)} for path in
                            (BASELINE, source_receipt, BUILD / "build.json", COMPILE / "receipt.json",
                             CHECKS / "results.json", receipt)])
    write(MANIFEST, manifest)
    print("Staged the DLL and additive REDscript change against 52 managed paths and 26 dependencies.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("compile", "checks", "prepare"))
    action = parser.parse_args().action
    {"compile": compile_scripts, "checks": run_checks, "prepare": prepare}[action]()
