"""Build a read-only save observer over the exact installed checkpoint source."""

import argparse
import hashlib
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
BOUNDARIES = {
    0x2FC8524: ("SaveSystems", "saveSystemsOriginal"),
    0x2C9F364: ("ObserveSaveWriter<SaveComponent::Quests, saveQuestsOriginal>", "saveQuestsOriginal"),
    0x2AAC958: ("ObserveSaveWriter<SaveComponent::RealClock, saveRealClockOriginal>", "saveRealClockOriginal"),
    0x2AA8D00: ("ObserveSaveWriter<SaveComponent::GameClock, saveGameClockOriginal>", "saveGameClockOriginal"),
}
WRITER_SLOTS = {0x30BCE78: 0x2C9F364, 0x30A2A90: 0x2AAC958, 0x30BD228: 0x2AA8D00}

sys.path.insert(0, str(PREALPHA / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def pinned(path, value):
    contents = path.read_bytes()
    if digest(contents) != value:
        raise ValueError(f"Input hash changed: {path}")
    return contents


def require(condition, label):
    if not condition:
        raise ValueError(label)


def verify_engine():
    engine = Image()
    require(engine.sha == "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4",
            "Wrong executable")
    expected = {
        0x2FC88A0: {
            0x2FC8961: "call 0x142fc7b88", 0x2FC8989: "call 0x14069d640", 0x2FC89D3: "call 0x142fc7a28",
            0x2FC8A25: "call 0x142fc7c6c", 0x2FC8A4D: "call 0x14069d640",
        },
        0x2FC7A28: {0x2FC7AB0: "call 0x142fc7acc"},
        0x2FC7ACC: {0x2FC7AED: "lea rax, [rip + 0xbec]", 0x2FC7B70: "call 0x140272b40"},
        0x2FC86E0: {0x2FC8711: "call 0x142fc8524"},
        0x2FC8524: {0x2FC85C5: "mov rdx, qword ptr [rsi + 0x10]",
                    0x2FC85D1: "call qword ptr [rax + 0x138]", 0x2FC85F2: "jmp qword ptr [rax + 0x88]"},
    }
    traces = {}
    for function, pins in expected.items():
        contents = engine.disasm(function)
        require(int(contents["begin_rva"], 16) == function, f"Changed function boundary: {function:X}")
        instructions = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}'
                        for row in contents["instructions"]}
        for ip, instruction in pins.items():
            require(instructions.get(ip) == instruction, f"Changed native save instruction: {ip:X}")
        traces[f"{function:08X}"] = {f"{ip:08X}": instruction for ip, instruction in pins.items()}
    for table, method in WRITER_SLOTS.items():
        value, = struct.unpack_from("<Q", engine.data, engine.off(table + 0x138))
        require(value == engine.base + method, f"Changed writer vtable: {table:X}")
    prefixes = {}
    for rva in BOUNDARIES:
        require(engine.function(rva)[0] == rva, f"Changed hook entry: {rva:X}")
        offset = engine.off(rva)
        prefixes[rva] = engine.data[offset:offset + 8]
    return engine.sha, traces, prefixes


def revise_source(source, prefixes):
    new_hooks = []
    for rva, (detour, original) in BOUNDARIES.items():
        prefix = "".join(f"\\x{value:02X}" for value in prefixes[rva])
        new_hooks.append(f'    MakeHook(0x{rva:X}, "{prefix}", &{detour}, {original}),')
    writer_pins = [
        f"        Read<const void*>(image + 0x{table:X}, 0x138) != image + 0x{method:X} ||"
        for table, method in WRITER_SLOTS.items()
    ]
    replacements = {
        '#include "Checkpoint.hpp"': '#include "Checkpoint.hpp"\n#include "SaveWindow.hpp"',
        'void (*gameTickOriginal)(void*, float, const void*);':
            'void (*gameTickOriginal)(void*, float, const void*);\n\n#include "NativeSaveObservation.inc"',
        "Hook hooks[]{": "Hook hooks[]{\n" + "\n".join(new_hooks),
        "        Read<const void*>(image + QuestSystem, 0x110)": "\n".join(writer_pins) +
            "\n        Read<const void*>(image + QuestSystem, 0x110)",
        "RED4EXT_V1_SEMVER(0, 1, 4)": "RED4EXT_V1_SEMVER(0, 1, 5)",
    }
    for old, new in replacements.items():
        require(source.count(old) == 1, f"Changed source anchor: {old}")
        source = source.replace(old, new)
    return source


def run_checks(out, name, count):
    check = subprocess.run([str(out / f"{name}.exe")], cwd=out, capture_output=True, text=True,
                           errors="replace", timeout=30)
    (out / f"{name}.txt").write_text(check.stdout + check.stderr, encoding="utf-8")
    check.check_returncode()
    passed = sum(line.startswith("PASS ") for line in check.stdout.splitlines())
    require(passed == count, f"Unexpected passed-check count for {name}: {passed}")
    print(f"{name}: {passed} passed")
    return passed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100), metavar="1–99")
    args = parser.parse_args()
    out = HERE / f"run_build_{args.attempt:02}"
    out.mkdir()

    pins = {
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
    }
    originals = {path: pinned(path, value) for path, value in pins.items()}
    engine_sha, instructions, prefixes = verify_engine()
    native = out / "NativeCheckpoint.cpp"
    native.write_text(revise_source(originals[BASE / "source_02/NativeCheckpoint.cpp"].decode("utf-8-sig"),
                                    prefixes), encoding="utf-8")
    checks = out / "CheckpointChecks.cpp"
    checks.write_bytes(originals[BASE / "source_02/CheckpointChecks.cpp"])
    for path in (native, checks, HERE / "SaveWindow.hpp", HERE / "NativeSaveObservation.inc",
                 HERE / "SaveWindowChecks.cpp", Path(__file__)):
        pins[path] = digest(path.read_bytes())

    sdk = f'/external:I"{SDK}" /external:W0'
    flags = f'/nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /I"{HERE}" /I"{BASE / "source_02"}" {sdk}'
    commands = [
        "@echo off",
        f'call "{VCVARS}" >nul',
        f"cl.exe {flags} /LD NativeCheckpoint.cpp /link /OUT:PTFR_ExecutionCheckpoint.dll bcrypt.lib user32.lib",
        "dumpbin.exe /nologo /exports PTFR_ExecutionCheckpoint.dll > exports.txt",
        f'cl.exe {flags} "{HERE / "SaveWindowChecks.cpp"}" /link /OUT:SaveWindowChecks.exe',
        f"cl.exe {flags} CheckpointChecks.cpp /link /OUT:CheckpointChecks.exe bcrypt.lib user32.lib",
        f'cl.exe {flags} "{BASE / "RegistrationChecks.cpp"}" /link /OUT:RegistrationChecks.exe user32.lib',
    ]
    batch = out / "build.cmd"
    batch.write_text("\nif errorlevel 1 exit /b 1\n".join(commands) + "\n", encoding="ascii")
    build = subprocess.run(["cmd.exe", "/d", "/c", "build.cmd"], cwd=out, capture_output=True, text=True,
                           errors="replace", timeout=120)
    (out / "compile.txt").write_text(build.stdout + build.stderr, encoding="utf-8")
    print(build.stdout + build.stderr, end="")
    build.check_returncode()
    exports = (out / "exports.txt").read_text(encoding="ascii")
    for symbol in ("Main", "Query", "Supports"):
        require(re.search(rf"\b{symbol}\s*$", exports, re.M), f"Missing RED4ext export {symbol}")
    validation = {name: run_checks(out, name, count) for name, count in (
        ("SaveWindowChecks", 10), ("CheckpointChecks", 51), ("RegistrationChecks", 15)
    )}
    for path, expected in pins.items():
        pinned(path, expected)
    report = {
        "status": "ISOLATED_NATIVE_SAVE_OBSERVER_COMPILE_AND_FIXTURES_PASS",
        "game_runtime_exercised": False, "mutating_handoff_enabled": False, "engine_sha256": engine_sha,
        "native_save_instructions": instructions,
        "prefixes": {f"{rva:08X}": data.hex() for rva, data in prefixes.items()},
        "sources": {path.relative_to(WORKSPACE).as_posix(): value for path, value in pins.items()},
        "checks": validation, "dll_sha256": digest((out / "PTFR_ExecutionCheckpoint.dll").read_bytes()),
    }
    (out / "assessment.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
