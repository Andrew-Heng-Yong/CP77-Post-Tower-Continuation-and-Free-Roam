"""Build and check a workspace-only checkpoint DLL with the native save guard."""

import argparse
import json
from pathlib import Path
import re
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
WORKSPACE = PREALPHA.parent
BASE = PREALPHA / "universal_resume_checkpoint_probe_20261114_01"
SDK = WORKSPACE / "research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include"
VCVARS = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat")
BASELINE = BASE / "deployment_01/installed_manifest_01.json"
DISPATCHER = 0x3CC488
PREFIX = bytes.fromhex("40 55 53 56 57 41 56 48")
PINS = {
    BASELINE: "309183BBB02B5F6A954AB31D6F71B2C9461D29F795193A29F465C1A194F98B2D",
    BASE / "source_02/NativeCheckpoint.cpp": "C5C84590DD0E11E2A242463214A29A466360C4D631F2348C88BA65D702B473C4",
    BASE / "source_02/Checkpoint.hpp": "9492B30D454CB6B2F3C3C8706744BE026C5EBB6D92F3A230D02D76B2CBEE431B",
    BASE / "source_02/CheckpointChecks.cpp": "0FD8134F2102C9E3850391199E417D6034B3F0A5C2CBD00D933CFC24AA4CEF29",
    BASE / "RegistrationChecks.cpp": "31AF7A7CB27713403458C4E8F66300CF2AEAE2EF593BBC532CE0253F36AC34B5",
    BASE / "CheckpointRegistration.hpp": "394E3C761E852063DFF31B26E384D738475DB095EF70B026A8EAADE52F3C54D7",
    BASE / "RegisterReader.inc": "E8BFE5C15FF641DDC8D9D4DE2DD84147BF7D8C0B1A4A02611A9093ACFEEDBDD1",
    PREALPHA / "universal_resume_boundary_20261114_01/TimerRecord.hpp":
        "5051CAC230C963BDCBDDC5238A8B8882872BEFE1FEF05D214069D7C4B841516B",
    PREALPHA / "universal_resume_eagles_20261114_01/GameTimeWait.hpp":
        "C578DA6C4AE25377C48C05B74806D6DB1EE0998E235EACFE9864BAE04D553F46",
    PREALPHA / "universal_resume_save_guard_20261115_01/SaveGuard.hpp":
        "F76CBF2CB175FD5563156CD60880F2D4EEA4D26B8544825AB3D0935EEBB98AC1",
    PREALPHA / "quest_restoration_qr15/saved_graph_state_01/inspect_native.py":
        "2B1CBF5AFF08934126DBB2887E0822D09019C7D3F822C00D670456C52C6CA195",
    PREALPHA / "universal_resume_live_handoff_20261114_01/build_save_observer.py":
        "255970FA31EC1DF8201CBE6BF2EB6737CDF17610C9CBA3BD825592CA71717ABF",
    SDK / "RED4ext/GameEngine-inl.hpp": "99013EC5B54E1363898E8008B510054B234EF66E33690164A254B081F51F4623",
    SDK / "RED4ext/GameEngine.hpp": "9F29941032B9577FF6B1BC2177E6E9F7CD0213C014CFBBDF47695D6BDC646718",
}

sys.path.insert(0, str(PREALPHA / "universal_resume_live_handoff_20261114_01"))
from build_save_observer import Image, digest, pinned, require, run_checks


def verify_engine():
    engine = Image()
    require(engine.sha == "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4",
            "Wrong executable")
    offset = engine.off(DISPATCHER)
    require(engine.data[offset:offset + len(PREFIX)] == PREFIX, "Save dispatcher prefix changed")
    expected = {
        0x3CC094: {0x3CC0D0: "jmp 0x1403cc488"},
        DISPATCHER: {
            0x3CC49B: "mov al, byte ptr [rcx + 0x308]",
            0x3CC4D2: "call 0x1403ccbdc",
            0x3CC5D6: "call qword ptr [rax + 0x440]",
            0x3CC69A: "or byte ptr [rbx + 0x308], 0x20",
            0x3CC78C: "call 0x142f00628",
            0x3CC79A: "call 0x1422bdb10",
            0x3CC7BD: "call 0x14216bab0",
        },
        0x22C35A0: {0x22C35B1: "lea rdx, [rcx + 0x750]", 0x22C35C7: "call 0x1422ff6e0"},
        0x2F00628: {0x2F00632: "or byte ptr [rcx + 0x308], 0x10"},
        0x216BAB0: {0x216BABE: "call 0x142169610", 0x216BADF: "call 0x14216bc70"},
        0x22BDC96: {0x22BDDA4: "call 0x142f006f0"},
        0x2F006F0: {0x2F007AE: "and byte ptr [rbx + 0x308], 0xef"},
    }
    for entry, pins in expected.items():
        function = engine.disasm(entry)
        require(int(function["begin_rva"], 16) == entry, f"Changed function boundary: {entry:X}")
        instructions = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}'
                        for row in function["instructions"]}
        for ip, instruction in pins.items():
            require(instructions.get(ip) == instruction, f"Changed save instruction: {ip:X}")
    slots = {
        0x30C38D0: 0x3CC094,
        0x30A13A0: 0x2F06730, 0x30A13B0: 0x2F0694C, 0x30A13B8: 0x2F068B0, 0x30A1540: 0x22C35A0,
    }
    for slot, target in slots.items():
        value, = struct.unpack_from("<Q", engine.data, engine.off(slot))
        require(value == engine.base + target, f"Changed save vtable slot: {slot:X}")
    return {
        "sha256": engine.sha,
        "dispatch_rva": f"{DISPATCHER:08X}",
        "dispatch_prefix": PREFIX.hex(),
        "instructions": {f"{ip:08X}": instruction for pins in expected.values() for ip, instruction in pins.items()},
        "vtable_slots": {f"{slot:08X}": f"{target:08X}" for slot, target in slots.items()},
    }


def revise_source(source):
    prefix = "".join(f"\\x{byte:02X}" for byte in PREFIX)
    replacements = {
        '#include "Checkpoint.hpp"': '#include "Checkpoint.hpp"\n#include "SaveAdmission.hpp"',
        "void (*gameTickOriginal)(void*, float, const void*);":
            'void (*gameTickOriginal)(void*, float, const void*);\n\n#include "NativeSaveAdmission.inc"',
        "            out->Resize(1);":
            '            const auto handoffReady = static_cast<bool>(TryBeginNativeHandoff());\n'
            '            sdk->logger->InfoF(plugin, "PTFR native save handoff admission: %s",\n'
            '                               handoffReady ? "idle" : "deferred");\n'
            '            out->Resize(1);',
        "Hook hooks[]{":
            f'Hook hooks[]{{\n    MakeHook(0x{DISPATCHER:X}, "{prefix}", &DispatchSaves, dispatchSavesOriginal),',
        "        Read<const void*>(image + QuestSystem, 0x110)":
            "        Read<const void*>(image + GameEngine, 0x140) != image + 0x3CC094 ||\n"
            "        Read<const void*>(image + QuestSystem, 0x110)",
        "RED4EXT_V1_SEMVER(0, 1, 4)": "RED4EXT_V1_SEMVER(0, 1, 6)",
    }
    for old, new in replacements.items():
        require(source.count(old) == 1, f"Changed source anchor: {old}")
        source = source.replace(old, new)
    return source


def compile_candidate(out):
    flags = (f'/nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /volatile:ms '
             f'/I"{HERE}" /I"{BASE / "source_02"}" /external:I"{SDK}" /external:W0')
    commands = [
        "@echo off",
        f'call "{VCVARS}" >nul',
        "cl.exe /Bv > toolchain.txt 2>&1",
        f"cl.exe {flags} /sourceDependencies NativeCheckpoint.deps.json /LD NativeCheckpoint.cpp "
        "/link /OUT:PTFR_ExecutionCheckpoint.dll bcrypt.lib user32.lib",
        "dumpbin.exe /nologo /exports PTFR_ExecutionCheckpoint.dll > exports.txt",
        f'cl.exe {flags} /sourceDependencies SaveAdmissionChecks.deps.json "{HERE / "SaveAdmissionChecks.cpp"}" '
        '/link /OUT:SaveAdmissionChecks.exe',
        f"cl.exe {flags} /sourceDependencies CheckpointChecks.deps.json CheckpointChecks.cpp "
        "/link /OUT:CheckpointChecks.exe bcrypt.lib user32.lib",
        f'cl.exe {flags} /sourceDependencies RegistrationChecks.deps.json "{BASE / "RegistrationChecks.cpp"}" '
        '/link /OUT:RegistrationChecks.exe user32.lib',
    ]
    # MSVC /Bv reports its component versions and returns a missing-source error.
    batch = out / "build.cmd"
    batch.write_text("\n".join(commands[:1]) + "\n" + commands[1] + "\nif errorlevel 1 exit /b 1\n" +
                     commands[2] + "\n" + "\nif errorlevel 1 exit /b 1\n".join(commands[3:]) +
                     "\nif errorlevel 1 exit /b 1\n", encoding="ascii")
    build = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, capture_output=True, text=True,
                           errors="replace", timeout=120)
    (out / "compile.txt").write_text(build.stdout + build.stderr, encoding="utf-8")
    print(build.stdout + build.stderr, end="")
    build.check_returncode()
    exports = (out / "exports.txt").read_text(encoding="ascii")
    for symbol in ("Main", "Query", "Supports"):
        require(re.search(rf"\b{symbol}\s*$", exports, re.M), f"Missing RED4ext export {symbol}")


def record_compile_inputs(out):
    inventory = {}
    hashes = {}
    for dependencies in sorted(out.glob("*.deps.json")):
        source = json.loads(dependencies.read_bytes())["Data"]
        inputs = [Path(name).resolve() for name in [source["Source"], *source["Includes"]]]
        require(inputs[0].suffix == ".cpp" and len(inputs) > 1, f"Missing input list: {dependencies}")
        display = []
        for path in inputs:
            if path not in hashes:
                hashes[path] = digest(path.read_bytes())
            display.append(path.relative_to(WORKSPACE).as_posix() if path.is_relative_to(WORKSPACE) else str(path))
        inventory[source["Source"].rsplit("\\", 1)[-1]] = dict(zip(display, (hashes[path] for path in inputs)))
    require(len(inventory) == 4, "Incomplete compile inventory")
    (out / "compile_inputs.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    return {name: len(inputs) for name, inputs in inventory.items()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100), metavar="1–99")
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()

    originals = {path: pinned(path, value) for path, value in PINS.items()}
    engine = verify_engine()
    baseline = json.loads(originals[BASELINE])
    root = Path(baseline["game_root"])
    groups = ("core_files", "companion_files", "required_files")
    for group in groups:
        for file in baseline[group]:
            pinned(root / file["path"], file["sha256"])
    target, = baseline["companion_files"]

    native = out / "NativeCheckpoint.cpp"
    native.write_text(revise_source(originals[BASE / "source_02/NativeCheckpoint.cpp"].decode("utf-8-sig")),
                      encoding="utf-8")
    (out / "CheckpointChecks.cpp").write_bytes(originals[BASE / "source_02/CheckpointChecks.cpp"])
    successor_sources = (native, HERE / "SaveAdmission.hpp", HERE / "NativeSaveAdmission.inc",
                         HERE / "SaveAdmissionChecks.cpp", Path(__file__))
    source_hashes = {path: digest(path.read_bytes()) for path in successor_sources}
    compile_candidate(out)
    inventory_counts = record_compile_inputs(out)
    validation = {name: run_checks(out, name, count) for name, count in (
        ("SaveAdmissionChecks", 12), ("CheckpointChecks", 51), ("RegistrationChecks", 15)
    )}
    for path, expected in (PINS | source_hashes).items():
        pinned(path, expected)
    dll = out / Path(target["path"]).name
    report = {
        "status": "WORKSPACE_NATIVE_SAVE_ADMISSION_BUILD_AND_FIXTURES_PASS",
        "game_runtime_exercised": False,
        "mutating_handoff_enabled": False,
        "engine": engine,
        "verified_baseline": {group: len(baseline[group]) for group in groups},
        "compile_input_counts": inventory_counts,
        "compile_inputs_sha256": digest((out / "compile_inputs.json").read_bytes()),
        "sources": {path.relative_to(WORKSPACE).as_posix(): sha for path, sha in (PINS | source_hashes).items()},
        "checks": validation,
        "target": {"path": target["path"], "previous_sha256": target["sha256"],
                   "candidate_sha256": digest(dll.read_bytes()), "bytes": dll.stat().st_size},
    }
    (out / "assessment.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
