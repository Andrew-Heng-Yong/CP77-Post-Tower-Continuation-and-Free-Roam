"""Build the exact MS31 integration and rerun the installed checkpoint regressions."""

import argparse
import json
from pathlib import Path
import re
import struct
import subprocess

from candidate_common import (ADMISSION, BASE, ENGINE_SHA, HERE, INSTALLED_SHA, LEGACY_BUILD, OLD_DLL_SHA,
                              OLD_INVENTORY_SHA, REGRESSION_COUNTS, RUNTIME_SOURCE, SDK, TARGET, VCVARS,
                              VERSION, WORKSPACE, checked_path, digest, load, pin, read_inventory,
                              require, verify_installed, verify_inventory, workspace_file, write_json)


READY_BUILD = "WORKSPACE_LIVE_HANDOFF_BUILD_AND_FIXTURES_PASS"
INTEGRATION_PASS = "LIVE_HANDOFF_INTEGRATION_FIXTURE_PASS"
OLD_CHECKS_SHA = "7353D5B1AD0402F5902C477D0A7C0180FBA80CFCA2B8A74171748D70A5B5CC05"
OLD_CHECKS = LEGACY_BUILD / "CheckpointChecks.cpp"


def read_integration(path, expected_sha, source_sha):
    proof = load(path, expected_sha)
    require(proof["status"] == INTEGRATION_PASS and proof["source_sha256"] == source_sha,
            "Integration proof does not bind this exact runtime source")
    require(type(proof["checks_passed"]) is int and proof["checks_passed"] > 0 and proof["inputs"],
            "No integration fixture inputs or pass count")
    inputs = {workspace_file(WORKSPACE / path): sha for path, sha in proof["inputs"].items()}
    verify_inventory({"integration": inputs})
    return inputs, proof["checks_passed"]


def quoted(path):
    value = str(path)
    require(not any(char in value for char in '\r\n"'), f"Cannot quote compiler path: {path}")
    return f'"{value}"'


def write_response(out, name, source, extra):
    flags = ["/nologo", "/std:c++20", "/W4", "/WX", "/O2", "/EHsc", "/MT", "/volatile:ms",
             f"/I{quoted(LEGACY_BUILD)}", f"/I{quoted(ADMISSION)}", f"/I{quoted(BASE / 'source_02')}",
             f"/external:I{quoted(SDK)}", "/external:W0", "/sourceDependencies", f"{name}.deps.json",
             *extra, quoted(source)]
    (out / f"{name}.rsp").write_text(" ".join(flags) + "\n", encoding="utf-8")


def compile_candidate(out, source):
    text = pin(OLD_CHECKS, OLD_CHECKS_SHA).read_text(encoding="utf-8-sig")
    require(text.count('#include "NativeCheckpoint.cpp"') == 1, "Checkpoint fixture include anchor drift")
    checkpoint = out / "CheckpointChecks.cpp"
    checkpoint.write_text(text.replace('#include "NativeCheckpoint.cpp"',
                                       f'#include "{source.as_posix()}"'), encoding="utf-8")
    dll = Path(TARGET).name
    write_response(out, "NativeCheckpoint", source, ["/LD", f"/Fe{dll}", "bcrypt.lib", "user32.lib"])
    fixture_sources = {
        "SaveAdmissionChecks": (ADMISSION / "SaveAdmissionChecks.cpp", []),
        "CheckpointChecks": (checkpoint, ["bcrypt.lib", "user32.lib"]),
        "RegistrationChecks": (BASE / "RegistrationChecks.cpp", ["user32.lib"]),
    }
    for name, (fixture, libs) in fixture_sources.items():
        write_response(out, name, fixture, [f"/Fe{name}.exe", *libs])
    checked_path(VCVARS)
    commands = [f'call "{VCVARS}" >nul', "cl.exe @NativeCheckpoint.rsp",
                f"dumpbin.exe /nologo /exports {dll} > exports.txt",
                *(f"cl.exe @{name}.rsp" for name in fixture_sources)]
    batch = out / "build.cmd"
    batch.write_text("@echo off\n" + "\nif errorlevel 1 exit /b 1\n".join(commands)
                     + "\nif errorlevel 1 exit /b 1\n", encoding="ascii")
    result = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, capture_output=True,
                            text=True, errors="replace", timeout=130, creationflags=subprocess.CREATE_NO_WINDOW)
    output = result.stdout + result.stderr
    (out / "compile.txt").write_text(output, encoding="utf-8")
    print(output, end="")
    result.check_returncode()
    read_binary(out / dll, out / "exports.txt")
    return out / dll


def read_binary(binary, exports_file):
    blob = checked_path(binary).read_bytes()
    require(len(blob) >= 64 and blob[:2] == b"MZ", "Expected a Windows PE DLL")
    offset, = struct.unpack_from("<I", blob, 0x3C)
    require(offset + 26 <= len(blob) and blob[offset:offset + 4] == b"PE\0\0", "Invalid PE header")
    machine, = struct.unpack_from("<H", blob, offset + 4)
    attributes, magic = struct.unpack_from("<HH", blob, offset + 22)
    require(machine == 0x8664 and attributes & 0x2000 and magic == 0x20B, "Expected an x64 PE32+ DLL")
    exports = checked_path(exports_file).read_text(encoding="ascii")
    names = re.findall(r"^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\w+)\s*$", exports, re.M)
    require(names == ["Main", "Query", "Supports"], "RED4ext export surface changed")


def inventory_from_compile(out):
    inventory = {}
    for name in ("NativeCheckpoint", *REGRESSION_COUNTS):
        record = json.loads((out / f"{name}.deps.json").read_bytes())["Data"]
        files = [checked_path(record["Source"]), *(checked_path(name) for name in record["Includes"])]
        require(len(files) > 1 and files[0].suffix == ".cpp", f"Incomplete compile evidence for {name}")
        inventory[name] = dict.fromkeys(files)
    merged = {file: digest(file) for file in dict.fromkeys(file for files in inventory.values() for file in files)}
    return {name: {file: merged[file] for file in files} for name, files in inventory.items()}


def run_regressions(out):
    counts = {}
    for label, expected in REGRESSION_COUNTS.items():
        exe = out / f"{label}.exe"
        result = subprocess.run([str(exe)], cwd=out, capture_output=True, text=True, errors="replace", timeout=35,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        output = result.stdout + result.stderr
        (out / f"{label}.txt").write_text(output, encoding="utf-8")
        result.check_returncode()
        total = len(re.findall(r"^PASS", output, re.M))
        require(total == expected, f"Expected {expected} {label} checks, observed {total}")
        counts[label] = total
    print(f"Passed {sum(counts.values())} checkpoint regressions.")
    return counts


def verify_scope(actual, known, source):
    runtime = actual["NativeCheckpoint"]
    require(source in runtime and source in actual["CheckpointChecks"], "Regressions missed the compiled runtime source")
    for path, sha in runtime.items():
        if path.is_relative_to(WORKSPACE):
            require(path in known, f"Missing pinned workspace input in the integration proof: {path}")
        if path in known:
            require(known[path] == sha, f"Known input drift during compile: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=RUNTIME_SOURCE)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100))
    parser.add_argument("--proof", type=Path)
    parser.add_argument("--proof-sha")
    args = parser.parse_args()
    require(bool(args.proof) == bool(args.proof_sha), "Supply the integration proof and its SHA together")
    source = workspace_file(args.source)
    require(source == RUNTIME_SOURCE, "Candidate source must use the reviewed runtime path")
    source_sha = args.source_sha.upper()
    text = pin(source, source_sha).read_text(encoding="utf-8-sig")
    require(re.findall(r"RED4EXT_V1_SEMVER\(\s*(\d+),\s*(\d+),\s*(\d+)\s*\)", text) == [tuple(VERSION.split("."))],
            "Unexpected native plugin semantic version")
    verify_installed()
    old = read_inventory(LEGACY_BUILD / "compile_inputs.json", OLD_INVENTORY_SHA)
    known = verify_inventory(old)
    proof, fixture_count = None, 0
    if args.proof:
        proof = workspace_file(args.proof)
        measured, fixture_count = read_integration(proof, args.proof_sha, source_sha)
        for path, sha in measured.items():
            require(path not in known or known[path] == sha, f"Integration proof replaces a pinned input: {path}")
            known[path] = sha
    known[source] = source_sha

    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    binary = compile_candidate(out, source)
    actual = inventory_from_compile(out)
    if proof:
        verify_scope(actual, known, source)
    counts = run_regressions(out)
    inventory_path = out / "compile_inputs.json"
    write_json(inventory_path, {label: {str(path): sha for path, sha in files.items()}
                                for label, files in actual.items()})
    verify_inventory(actual)
    verify_inventory({"prechecked": known})
    if proof:
        pin(proof, args.proof_sha)
    candidate_sha = digest(binary)
    require(candidate_sha != OLD_DLL_SHA, "Build reproduced the predecessor rather than the new runtime")
    assessment = {
        "status": READY_BUILD if proof else "WORKSPACE_LIVE_HANDOFF_COMPILE_ONLY_PASS",
        "version": VERSION, "installed_manifest_sha256": INSTALLED_SHA, "engine_sha256": ENGINE_SHA,
        "game_runtime_exercised": False, "checks": counts,
        "compile_inputs_sha256": digest(inventory_path), "exports_sha256": digest(out / "exports.txt"),
        "source": {"path": str(source), "sha256": source_sha},
        "integration": {"path": str(proof), "sha256": args.proof_sha.upper(), "checks_passed": fixture_count}
        if proof else None,
        "target": {"path": TARGET, "previous_sha256": OLD_DLL_SHA,
                   "candidate_sha256": candidate_sha, "bytes": binary.stat().st_size},
    }
    write_json(out / "assessment.json", assessment)
    print(f"Saved {assessment['status']} assessment at {out / 'assessment.json'}")


if __name__ == "__main__":
    main()
