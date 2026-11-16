"""Compile and qualify the workspace candidate without starting Cyberpunk."""

import argparse
from collections import Counter
import importlib.util
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from prepare_sources import (DLL, HERE, HISTORY, LUA, ORIGINAL, PREVIOUS, PREVIOUS_CANDIDATE_SHA, pinned,
                             previous_candidate, read_json, sha, write_json)


WORKSPACE = HERE.parents[1]
sys.path.insert(0, str(WORKSPACE / "research/redscript_2_5/binary_reader_01"))
from diagnose_01 import parse

sys.path.insert(0, str(ORIGINAL))
from stage import ARCHIVE_SHA, CACHE, CACHE_TS, COMPILER, REGISTRY, baseline


RED4EXT_SHA = "58DDFE43766AA91249D11671B55A8323D5EC017F816D847AFFE4B6201DCD0709"
PRIOR_COMPILE_SHA = "BC49973F2E83495F24E6DB42D39AECECF5600F97F0E55215701AA36D10C278E6"
CHECKPOINT_NAMES = ("PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint",
                    "PTFR.HistorySnapshotHS1.DecodeExecutionCheckpoint")


def installed_inputs():
    game, core = baseline()
    assert not (game / DLL).exists()
    assert not list((game / "red4ext/plugins").glob("*RTTI*Probe*/*.dll"))
    pinned(game / "red4ext/RED4ext.dll", RED4EXT_SHA)
    return game, core


def number_dir(label, number):
    return HERE / f"{label}_{number:02d}"


def invoke(command, directory, log, timeout):
    result = subprocess.run([str(item) for item in command], cwd=directory, capture_output=True, encoding="utf-8",
                            errors="replace", timeout=timeout, creationflags=subprocess.CREATE_NO_WINDOW)
    text = result.stdout + result.stderr
    log.write_text(text, encoding="utf-8")
    assert result.returncode == 0, text[-6000:]
    return text


def compile_scripts(source, attempt):
    game, core = installed_inputs()
    prior = read_json(pinned(PREVIOUS / "compile_02/receipt.json", PRIOR_COMPILE_SHA))
    expected = {path: digest for path, digest in prior["compiler_inputs"].items() if path.lower().endswith(".reds")}
    sources = {path.relative_to(game).as_posix() for directory in ("r6/scripts", "red4ext/plugins")
               for path in (game / directory).rglob("*.reds")}
    registry = (game / REGISTRY).read_text(encoding="utf-8-sig")
    logged = {(game / "r6/scripts" / line.strip()).resolve() for line in registry.splitlines()
              if line.strip().lower().endswith(".reds")}
    assert "Compilation complete" in registry and logged == {(game / path).resolve() for path in sources}
    assert len(sources) == 148 and sources == set(expected)
    expected.update({path: prior["compiler_inputs"][path] for path in (CACHE, COMPILER)})
    for path, digest in expected.items():
        pinned(game / path, digest)
    # Running SCC updates the timestamp sidecar. Copy the exact current bytes.
    inputs = {**expected, CACHE_TS: sha(game / CACHE_TS), REGISTRY: sha(game / REGISTRY)}

    out = number_dir("compile", attempt)
    cache = out / "cache"
    cache.mkdir(parents=True, exist_ok=False)
    for path in (CACHE, CACHE_TS):
        target = cache / Path(path).name
        shutil.copyfile(game / path, target)
        pinned(target, inputs[path])
    source_receipt = read_json(source / "receipt.json")
    history = pinned(source / Path(HISTORY).name, source_receipt["sources"][Path(HISTORY).name])
    staged = {}
    for path in sorted(sources):
        target = out / "scripts" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        donor = history if path == HISTORY else game / path
        shutil.copyfile(donor, target)
        staged[path] = sha(target)
        assert staged[path] == sha(donor)
    assert [path for path in staged if staged[path] != inputs[path]] == [HISTORY]

    paths = out / "compile_paths.txt"
    paths.touch(exist_ok=False)
    compiled = cache / "compiled.redscripts"
    command = [game / COMPILER, "-compile", out / "scripts", "-compilePathsFile", paths, "-customCacheDir", cache,
               "-outputCacheFile", compiled, cache / "final.redscripts"]
    log = invoke(command, out, out / "scc.log", timeout=180)
    assert "Compilation complete" in log and compiled.is_file(), log[-6000:]
    for path, digest in inputs.items():
        pinned(game / path, digest)
    assert installed_inputs() == (game, core)
    write_json(out / "receipt.json", {"source_count": len(sources), "compiler_inputs": inputs, "staged_sources": staged,
                                      "compiled_sha256": sha(compiled), "source_receipt_sha256": sha(source / "receipt.json"),
                                      "checkpoint_dll_present_during_offline_compile": False})
    print(f"Compiled {len(sources)} installed source inputs with only the history script replaced.")


def script_contract(compiled):
    prior = read_json(pinned(PREVIOUS / "compile_02/receipt.json", PRIOR_COMPILE_SHA))
    old = pinned(PREVIOUS / "compile_02/cache/compiled.redscripts", prior["script_contract"]["compiled_sha256"])

    def inspect(path):
        cache, header, pools, definitions = parse(path)
        assert header["version"] == 14

        def body(row):
            return cache[row["offset"]:row["offset"] + row["size"]]

        def owner(row):
            return definitions[row["parent"]]["name"] if row["parent"] else ""

        def func_flags(row):
            return struct.unpack_from("<I", body(row), 1)[0]

        def stable_function_name(name):
            # SCC numbers its generated alias pairs by definition index.
            return re.sub(r"^(proxy|wrapper)\$[0-9]+$", r"\1$", name)

        natives = Counter((owner(row), stable_function_name(row["name"])) for row in definitions if row["type"] == 5
                          and row["size"] >= 5 and func_flags(row) & 0x10)
        fields = {}
        for row in definitions:
            if row["type"] == 8 and owner(row).endswith(".CaptureArchiveHS3") and row["name"].startswith("executionCheckpoint"):
                raw = body(row)
                assert raw[0] == 0
                type_id, flags = struct.unpack_from("<II", raw, 1)
                assert definitions[type_id]["type"] == 0
                fields[row["name"]] = (definitions[type_id]["name"], flags)
        return natives, fields, pools, definitions, cache

    previous, old_fields, _, _, _ = inspect(old)
    current, fields, pools, definitions, cache = inspect(compiled)
    expected = Counter(("", name) for name in CHECKPOINT_NAMES)
    assert previous - current == expected and not current - previous, (previous - current, current - previous)
    assert all(row["type"] != 5 or row["name"] not in CHECKPOINT_NAMES for row in definitions)
    assert all(name in pools["cnames"] for name in CHECKPOINT_NAMES)
    assert previous[("Reflection", "GetGlobalFunction")] == current[("Reflection", "GetGlobalFunction")] == 1
    assert previous[("ReflectionStaticFunc", "Call")] == current[("ReflectionStaticFunc", "Call")] == 1
    assert len(fields) == 9 and fields == old_fields
    assert fields["executionCheckpointState"][0] == "array:Uint64"
    assert {name for name, (_, flags) in fields.items() if flags & 0x100} == set(fields) - {"executionCheckpointAttempts"}

    def method(owner, name):
        result, = (row for row in definitions if row["type"] == 5 and definitions[row["parent"]]["name"] == owner
                   and row["name"].split(";", 1)[0] == name)
        return result

    def body(row):
        return cache[row["offset"]:row["offset"] + row["size"]]

    def call_sites(blob, row, opcode):
        index = row["index"] if opcode == 36 else row["name_index"]
        operand = re.escape(struct.pack("<I", index))
        return [match.start() for match in re.finditer(re.escape(bytes([opcode])) + b"...." + operand, blob, re.DOTALL)]

    def name_sites(blob, name):
        operand = bytes([14]) + struct.pack("<I", pools["cnames"].index(name))
        return [match.start() for match in re.finditer(re.escape(operand), blob)]

    history_owner = "PTFR.HistorySnapshotHS1.CaptureArchiveHS3"
    lookup = method("Reflection", "GetGlobalFunction")
    call = method("ReflectionStaticFunc", "Call")
    read = method(history_owner, "ReadExecution")
    decode = method(history_owner, "DecodeExecution")
    for row, type_name in ((read, "array:Uint64"), (decode, "String")):
        result, = (entry for entry in definitions if entry["type"] == 0 and entry["name"] == type_name)
        code = body(row)
        call_at, = call_sites(code, call, 36)
        result_conversion = bytes([93]) + struct.pack("<I", result["index"])
        assert code.find(result_conversion) > call_at

    poll = body(method(history_owner, "OnCapturePollHS3"))
    read_lookup, decode_lookup = call_sites(poll, lookup, 36)
    read_name, = name_sites(poll, CHECKPOINT_NAMES[0])
    decode_name, = name_sites(poll, CHECKPOINT_NAMES[1])
    sample, = call_sites(poll, read, 37)
    commit, = call_sites(poll, method(history_owner, "StoreExecutionCheckpoint"), 37)
    gate_read, gate_ack = name_sites(poll, "PTFRHS3_GateResult")
    assert gate_read < read_lookup < read_name < decode_lookup < decode_name < sample < commit < gate_ack
    for name, bridge_name in zip(CHECKPOINT_NAMES, ("PrimeExecutionCheckpoint", "ExecutionCheckpointJSON"), strict=True):
        code = body(method(history_owner, bridge_name))
        found, = call_sites(code, lookup, 36)
        name_at, = name_sites(code, name)
        assert found < name_at

    return {"removed_native_declarations": list(CHECKPOINT_NAMES), "new_native_declarations": [],
            "runtime_cnames": list(CHECKPOINT_NAMES), "checkpoint_fields_and_flags": fields,
            "codeware_methods": ["Reflection.GetGlobalFunction", "ReflectionStaticFunc.Call"],
            "compiled_commit_precedes_gate_acknowledgement": True}


def run_fixture(binary, built, out, count):
    log = invoke([binary], built, out, timeout=45)
    checks = [line[5:] for line in log.splitlines() if line.startswith("PASS ")]
    assert len(checks) == count, log[-4000:]
    return log, checks


def native_resolution_contract(image_class):
    image = image_class()
    sites = (
        (0x279E78, 0x279F09, "call", "0x1406bfb28"),
        (0x6BFB28, 0x6BFB6D, "call", "0x14027830c"),
        (0x27830C, 0x278321, "call", "0x140279964"),
        (0x27830C, 0x27832F, "call", "0x1402782a4"),
        (0x27830C, 0x278361, "add", "r8, 0x14"),
        (0x6BFB28, 0x6BFC01, "call", "qword ptr [rbx + 0x10]"),
        (0x6BD564, 0x6BD586, "xor", "r11d, r11d"),
        (0x6BD564, 0x6BD590, "mov", "qword ptr [rcx + 0x18], r11"),
    )
    result = []
    for function, address, mnemonic, operands in sites:
        row, = (item for item in image.disasm(function)["instructions"] if int(item["rva"], 16) == address)
        assert row["mnemonic"] == mnemonic and row["operands"] == operands, row
        result.append(row)
    return {"exe_sha256": image.sha, "instructions": result}


def verify(source, compiled, built, attempt):
    game, core = installed_inputs()
    out = number_dir("checks", attempt)
    out.mkdir(exist_ok=False)
    compilation = read_json(compiled / "receipt.json")
    assert compilation["source_receipt_sha256"] == sha(source / "receipt.json")
    builds = {row["name"]: row["sha256"] for row in read_json(built / "build.json")}
    for name in ("NativeCheckpoint.cpp", "Checkpoint.hpp", "CheckpointChecks.cpp"):
        pinned(source / name, builds[name])
    for name in ("CheckpointRegistration.hpp", "RegisterReader.inc", "RegistrationChecks.cpp"):
        pinned(HERE / name, builds[name])
    binary = pinned(compiled / "cache/compiled.redscripts", compilation["compiled_sha256"])
    contract = script_contract(binary)
    _, registration = run_fixture(pinned(built / "RegistrationChecks.exe", builds["RegistrationChecks.exe"]),
                                  built, out / "registration.txt", 15)
    log, checkpoint = run_fixture(pinned(built / "CheckpointChecks.exe", builds["CheckpointChecks.exe"]),
                                  built, out / "checkpoint.txt", 41)
    payload, = (line[8:] for line in log.splitlines() if line.startswith("PAYLOAD "))

    # Reuse the previously reviewed read-only evidence functions and Lua fixture.
    # The original runner's guarded CLI is never called.
    spec = importlib.util.spec_from_file_location("checkpoint_evidence", ORIGINAL / "verify.py")
    evidence = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evidence)
    resolution = native_resolution_contract(evidence.Image)
    native_capture = evidence.native_binary()
    control = evidence.saved_input(evidence.json.loads(payload))
    previous, prior = previous_candidate()
    lua = pinned(previous / "files" / LUA, prior["files"][LUA])
    lua_checks = evidence.lua_checks(lua.read_text(encoding="utf-8"), game, payload)
    assert len(lua_checks) == 12 and len(core) == 77
    assert installed_inputs() == (game, core)
    for path, digest in compilation["compiler_inputs"].items():
        pinned(game / path, digest)

    checks_path = out / "results.json"
    write_json(checks_path, {"status": "OFFLINE_RUNTIME_CHECKPOINT_VERIFIED", "registration_checks": registration,
                             "checkpoint_checks": checkpoint, "script_contract": contract, "native_resolution": resolution,
                             "native_capture_checks": native_capture, "saved_epistrophy_control": control, "lua_checks": lua_checks,
                             "installed_core_and_dependency_paths_verified": len(core), "live_startup_verified": False,
                             "game_writes": 0, "save_writes": 0})
    candidate = number_dir("candidate", attempt)
    candidate.mkdir(exist_ok=False)
    payload_paths = {HISTORY: pinned(compiled / "scripts" / HISTORY, compilation["staged_sources"][HISTORY]),
                     LUA: lua, DLL: pinned(built / Path(DLL).name, builds[Path(DLL).name])}
    files = {}
    for name, input_path in payload_paths.items():
        target = candidate / "files" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(input_path, target)
        files[name] = sha(target)
        assert files[name] == sha(input_path)
    assert prior["archive_sha256"] == ARCHIVE_SHA and files[DLL] != prior["files"][DLL]
    write_json(candidate / "receipt.json", {"status": "WORKSPACE_RUNTIME_CHECKPOINT_CANDIDATE",
                                            "archive_sha256": ARCHIVE_SHA, "files": files,
                                            "predecessor_candidate_sha256": PREVIOUS_CANDIDATE_SHA,
                                            "compile_receipt_sha256": sha(compiled / "receipt.json"),
                                            "build_receipt_sha256": sha(built / "build.json"),
                                            "checks_sha256": sha(checks_path), "live_startup_verified": False})
    print(f"Verified {len(registration)} registration, {len(checkpoint)} capture and {len(lua_checks)} Lua checks.")
    print("Compiled definitions contain zero new native declarations. Verified all three candidate file readbacks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("compile", "verify"))
    parser.add_argument("--source", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--attempt", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--compiled", type=int, choices=range(1, 100))
    parser.add_argument("--built", type=int, choices=range(1, 100))
    args = parser.parse_args()
    sources = number_dir("source", args.source)
    if args.mode == "compile":
        compile_scripts(sources, args.attempt)
    else:
        if args.compiled is None or args.built is None:
            parser.error("verify requires --compiled and --built")
        verify(sources, number_dir("compile", args.compiled), number_dir("build", args.built), args.attempt)
