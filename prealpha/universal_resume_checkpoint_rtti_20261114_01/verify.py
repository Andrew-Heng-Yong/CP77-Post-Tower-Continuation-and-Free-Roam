"""Verify the native registration repair against RD10 and compile the staged scripts."""

import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys

from prepare import HERE, PREVIOUS, SOURCE, pinned, sha

WORKSPACE = HERE.parents[1]
REDSCRIPT = WORKSPACE / "research/redscript_2_5/binary_reader_01"
STOCK_NATIVE = HERE.parent / "quest_restoration_qr15/saved_graph_state_01"
sys.path.insert(0, str(REDSCRIPT))
from diagnose_01 import parse
sys.path.insert(0, str(STOCK_NATIVE))
from inspect_native import Image

PREVIOUS_CANDIDATE_SHA = "3D908EA14BB18926418F07BF64780C7533C0ED91080AD1AEE7411B8804BA0EE6"
RED4EXT_SHA = "58DDFE43766AA91249D11671B55A8323D5EC017F816D847AFFE4B6201DCD0709"
HISTORY = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
PROBE = "red4ext/plugins/PTFR_CheckpointRTTIProbe/PTFR_CheckpointRTTIProbe.dll"
REGISTRY = "r6/logs/redscript_rCURRENT.log"
BASE_CACHE = "r6/cache/final.redscripts"
CACHE_TS = "r6/cache/final.redscripts.ts"
COMPILER = "engine/tools/scc.exe"
READ_NAME = "PTFR.HistorySnapshotHS1.ReadExecutionCheckpoint"
DECODE_NAME = "PTFR.HistorySnapshotHS1.DecodeExecutionCheckpoint"


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(value, indent=2) + "\n")


def baseline():
    # The predecessor module guards its entry point. Reuse its read-only
    # manifest verification without invoking its builder or staging old files.
    spec = importlib.util.spec_from_file_location("checkpoint_baseline", PREVIOUS / "stage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    game, core = module.baseline()
    assert not (game / DLL).exists()
    assert not (game / PROBE).exists()
    assert not list((game / "red4ext/plugins").glob("*RTTI*Probe*/*.dll"))
    pinned(game / "red4ext/RED4ext.dll", RED4EXT_SHA)
    return game, core


def compile_candidate(out, game, previous, old_candidate):
    original = read(pinned(PREVIOUS / previous["compile_receipt"], previous["compile_receipt_sha256"]))
    expected_sources = {path: digest for path, digest in original["compiler_inputs"].items()
                        if path.lower().endswith(".reds")}
    actual_sources = {path.relative_to(game).as_posix() for folder in ("r6/scripts", "red4ext/plugins")
                      for path in (game / folder).rglob("*.reds")}
    assert set(expected_sources) == actual_sources and len(actual_sources) == 148
    log = (game / REGISTRY).read_text(encoding="utf-8-sig")
    logged = {(game / "r6/scripts" / line.strip()).resolve() for line in log.splitlines()
              if line.strip().lower().endswith(".reds")}
    assert "Compilation complete" in log and logged == {(game / path).resolve() for path in actual_sources}
    for path, digest in expected_sources.items():
        pinned(game / path, digest)
    for path in (BASE_CACHE, COMPILER):
        pinned(game / path, original["compiler_inputs"][path])

    inputs = {path: sha(game / path) for path in sorted(actual_sources | {BASE_CACHE, CACHE_TS, COMPILER, REGISTRY})}
    cache = out / "cache"
    cache.mkdir()
    for relative in (BASE_CACHE, CACHE_TS):
        shutil.copyfile(game / relative, cache / Path(relative).name)
    for path in sorted(actual_sources):
        target = out / "scripts" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        source = pinned(old_candidate / "files" / path, previous["files"][path]) if path == HISTORY else game / path
        shutil.copyfile(source, target)
        assert sha(source) == sha(target)
    argsfile = out / "compile_paths.txt"
    argsfile.touch(exist_ok=False)
    compiled = cache / "compiled.redscripts"
    command = [game / COMPILER, "-compile", out / "scripts", "-compilePathsFile", argsfile,
               "-customCacheDir", cache, "-outputCacheFile", compiled, cache / "final.redscripts"]
    result = subprocess.run([str(part) for part in command], capture_output=True, encoding="utf-8",
                            errors="replace", timeout=180, creationflags=subprocess.CREATE_NO_WINDOW)
    logs = result.stdout + result.stderr
    (out / "scc.log").write_text(logs, encoding="utf-8")
    assert result.returncode == 0 and "Compilation complete" in logs and compiled.is_file(), logs[-5000:]
    assert all(sha(game / rel) == digest for rel, digest in inputs.items())
    return compiled, inputs


def signature_contract(compiled):
    data, header, _, definitions = parse(compiled)
    assert header["version"] == 14

    def definition(name, kind, owner):
        found, = (item for item in definitions
                  if item["name"] == name and item["type"] == kind and item["parent"] == owner)
        return found

    def body(defn):
        return data[defn["offset"]:defn["offset"] + defn["size"]]

    def typ(index):
        definition = definitions[index]
        assert definition["type"] == 0
        return definition["name"]

    def native(name, owner):
        shape = definition(name, 5, owner)
        raw = body(shape)
        # Native functions with a result and argument list use this shape.
        # The capture and decode need the same native/static flags as the donors.
        assert raw[0] == 0 and (struct.unpack_from("<I", raw, 1)[0] & 0x11) == 0x11
        result, = struct.unpack_from("<I", raw, 5)
        count, = struct.unpack_from("<I", raw, 10)
        assert len(raw) == 14 + 4 * count
        args = []
        for index, in struct.iter_unpack("<I", raw[14:]):
            arg = definitions[index]
            assert arg["type"] == 6 and arg["parent"] == shape["index"]
            args.append((arg["name"], struct.unpack_from("<I", body(arg))[0]))
        return result, args

    game = definition("GameInstance", 1, 0)["index"]
    slots = {"quests": ("GetQuestsSystem", "ref:QuestsSystem"),
             "delay": ("GetDelaySystem", "ref:DelaySystem"),
             "clock": ("GetTimeSystem", "ref:TimeSystem")}
    capture, params = native(READ_NAME, 0)
    decode, decoder_args = native(DECODE_NAME, 0)
    resolved = []
    for (name, (getter, expected)), (actual_name, index) in zip(slots.items(), params[:3], strict=True):
        stock, args = native(getter, game)
        assert [arg_name for arg_name, _ in args] == ["self"]
        assert actual_name == name and stock == index and typ(stock) == expected
        resolved.append({"parameter": name, "stock": f"GameInstance.{getter}", "type": expected})
    assert [(name, typ(index)) for name, index in params[3:6]] == [
        ("ticket", "Int32"), ("route", "Int32"), ("historyRevision", "Int32")]
    covers = definition("MultiSelectCovers", 1, 0)["index"]
    field = definition("selectedCovers", 8, covers)
    field_data = body(field)
    assert field_data[0] == 0
    words, = struct.unpack_from("<I", field_data, 1)
    assert typ(words) == "array:Uint64"
    assert params[6:] == [("presentation", words)] and capture == words and decoder_args == [("data", words)]
    assert typ(decode) == "String"
    return {"native_functions": [READ_NAME, DECODE_NAME], "handle_arguments": resolved,
            "array_donor": "MultiSelectCovers.selectedCovers",
            "identical_array_references": ["presentation", "capture result", "decode data"],
            "compiled_sha256": sha(compiled)}


def native_contract():
    native = Image()
    # Registration entry points in the same executable used by the build.
    # The getter names and the array property are resolved from their RIP LEAs.
    sites = [
        (0x15B05A0, 0x15B05EF, "ScriptGameInstance"),
        (0xFC8484, 0xFC848D, "GetQuestsSystem"),
        (0xFC8930, 0xFC893D, "GetDelaySystem"),
        (0xFC7A84, 0xFC7A8D, "GetTimeSystem"),
        (0x14DF70C, 0x14DF780, "MultiSelectCovers"),
        (0x14DF70C, 0x14DF7C7, "selectedCovers"),
    ]
    for function, instruction, expected in sites:
        run = native.disasm(function)
        row, = (row for row in run["instructions"] if int(row["rva"], 16) == instruction)
        assert row["mnemonic"] == "lea" and "[rip +" in row["operands"]
        raw = bytes.fromhex(row["bytes"])
        target = instruction + len(raw) + struct.unpack_from("<i", raw, len(raw) - 4)[0]
        offset = native.off(target)
        text = native.data[offset:native.data.index(0, offset)]
        assert text == expected.encode(), (function, instruction, expected, text)
    return {"exe_sha256": native.sha, "red4ext_sha256": RED4EXT_SHA,
            "stock_labels": [{"rva": f"0x{site:X}", "name": label} for _, site, label in sites]}


def fixture_run(binary, out, expected):
    result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=45)
    out.write_text(result.stdout + result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    checks = [line[5:] for line in result.stdout.splitlines() if line.startswith("PASS ")]
    assert len(checks) == expected
    return checks


def run(attempt, built):
    game, core = baseline()
    receipt_path = pinned(PREVIOUS / "candidate_02/receipt.json", PREVIOUS_CANDIDATE_SHA)
    previous = read(receipt_path)
    native = HERE / f"build_{built:02d}"
    hashes = {row["name"]: row["sha256"] for row in read(native / "build.json")}
    for relative in ("source_01/NativeCheckpoint.cpp", "CheckpointRegistration.hpp", "RegisterReader.inc",
                     "RegistrationChecks.cpp", "source_01/CheckpointChecks.cpp", "source_01/Checkpoint.hpp"):
        pinned(HERE / relative, hashes[Path(relative).name])
    out = HERE / f"checks_{attempt:02d}"
    out.mkdir(exist_ok=False)
    reg_checks = fixture_run(pinned(native / "RegistrationChecks.exe", hashes["RegistrationChecks.exe"]),
                             out / "registration.txt", 23)
    cutoff_checks = fixture_run(pinned(native / "CheckpointChecks.exe", hashes["CheckpointChecks.exe"]),
                                out / "checkpoint.txt", 41)
    abi = native_contract()
    compile_dir = HERE / f"compile_{attempt:02d}"
    compile_dir.mkdir(exist_ok=False)
    compiled, input_pins = compile_candidate(compile_dir, game, previous, receipt_path.parent)
    script = signature_contract(compiled)
    assert baseline() == (game, core)

    tests = out / "results.json"
    write(tests, {"status": "OFFLINE_REGISTRATION_REPAIR_VERIFIED", "registration_checks": reg_checks,
                  "checkpoint_checks": cutoff_checks, "native_donor_checks": abi, "script_contract": script,
                  "live_startup_verified": False, "game_writes": 0, "save_writes": 0})
    write(compile_dir / "receipt.json", {"script_contract": script, "source_count": 148, "compiler_inputs": input_pins,
                                         "replaced_source": {HISTORY: previous["files"][HISTORY]}})
    candidate = HERE / f"candidate_{attempt:02d}"
    candidate.mkdir(exist_ok=False)
    payloads = {
        DLL: pinned(native / Path(DLL).name, hashes[Path(DLL).name]),
        HISTORY: pinned(compile_dir / "scripts" / HISTORY, previous["files"][HISTORY]),
        LUA: pinned(receipt_path.parent / "files" / LUA, previous["files"][LUA]),
    }
    files = {}
    for path, source in payloads.items():
        copy = candidate / "files" / path
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, copy)
        files[path] = sha(copy)
        assert files[path] == sha(source)
    assert files[DLL] != previous["files"][DLL]
    write(candidate / "receipt.json", {
        "status": "WORKSPACE_CANDIDATE", "predecessor_candidate_sha256": PREVIOUS_CANDIDATE_SHA,
        "archive_sha256": previous["archive_sha256"], "files": files,
        "build_receipt_sha256": sha(native / "build.json"), "checks_sha256": sha(tests),
        "compile_receipt_sha256": sha(compile_dir / "receipt.json"), "live_startup_verified": False,
    })
    print(f"Verified {len(reg_checks)} registration checks, {len(cutoff_checks)} checkpoint checks "
          f"and {len(abi['stock_labels'])} native donor anchors. Compiled 148 sources and matched both native signatures.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--built", type=int, choices=range(1, 100), required=True)
    options = parser.parse_args()
    run(options.attempt, options.built)
