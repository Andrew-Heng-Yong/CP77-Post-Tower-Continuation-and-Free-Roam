"""Compile and verify selected stock game-time initialization in an isolated fixture."""

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
WORKSPACE = PREALPHA.parent
SELECTION = PREALPHA / "universal_resume_falco_transfer_20261115_01"
sys.path.insert(0, str(SELECTION))
from build_restore_fixture import Image, VCVARS, digest, pinned, require


INPUTS = {
    PREALPHA / "universal_resume_save_session_20261115_01/deployment_01/installed_manifest_01.json":
        "57A78D066D6B7465572FB5F61AA0644AC6D247308C00E4AD1A7E07F59A4AB5C4",
    PREALPHA / "universal_resume_first_live_wait_20261115_01/run_04/assessment.json":
        "FEAA8527FA62476056C3AC207613549985CEBA6D97D22C83D990A3FA6157CCB2",
    SELECTION / "run_05/selection_assessment.json":
        "A7533BD70ED0B8AF0CDD1A794061AAD6F955C406C5567A31862CDC23BC598D8D",
    SELECTION / "run_06/ManualSave-29.json":
        "61B9C4C7E7B0BC8B8A3210298E62780729EE007A7529FDBF9F1FEEBF3205B03B",
    PREALPHA / "universal_resume_eagles_20261114_01/GameTimeWait.hpp":
        "C578DA6C4AE25377C48C05B74806D6DB1EE0998E235EACFE9864BAE04D553F46",
    PREALPHA / "universal_resume_save_guard_20261115_01/SaveGuard.hpp":
        "F76CBF2CB175FD5563156CD60880F2D4EEA4D26B8544825AB3D0935EEBB98AC1",
}

FUNCTIONS = {
    0x193C74: {0x193CB5: "call qword ptr [rax + 0x2c8]", 0x193D6B: "mov rdi, qword ptr [rax + 0x240]",
               0x193DAB: "mov r8d, dword ptr [rsi + 0x44]", 0x193DEA: "call rdi",
               0x193E06: "call qword ptr [rax + 0x2b8]", 0x193E16: "call 0x14088b6ac"},
    0xA09BC4: {0xA09BE8: "lock xadd dword ptr [rcx + 0x118], eax", 0xA09C03: "call qword ptr [rax + 0xf8]",
               0xA09C1A: "add ecx, dword ptr [rbp + 0x57]", 0xA09C4D: "call 0x140a0a84c",
               0xA09C7F: "call 0x142179b80"},
    0xA0A84C: {0xA0A8B6: "mov ebx, dword ptr [rbx]", 0xA0A8C9: "mov r9d, ebx",
               0xA0A8EF: "call 0x140a0a45c"},
    0xA0A45C: {0xA0A4B8: "mov dword ptr [r14 + 0x90], eax", 0xA0A4CD: "mov dword ptr [r14 + 0x40], ebx"},
    0x193B00: {0x193B11: "cmp dword ptr [rdi + 0x40], ebx", 0x193B2E: "call qword ptr [rax + 0x130]"},
    0x1934AC: {0x1934EF: "call qword ptr [rax + 0x2c0]", 0x193502: "call qword ptr [rax + 0x250]"},
    0x193674: {0x19367C: "add rcx, 0x63200", 0x193688: "call 0x142179420"},
    0x195A38: {}, 0x193E58: {}, 0x7604B4: {}, 0x1AAAC8: {},
    0x88BB20: {}, 0x1AAB14: {},
}
LEAVES = {
    0x18F2540: 0x18F2556, 0x1304ED8: 0x1304EE3, 0x258480: 0x258489,
    0x88B6AC: 0x88B6EF, 0x88BB74: 0x88BB93, 0x88BC48: 0x88BC56, 0x1AAB88: 0x1AABA6,
}
SLOTS = {
    0x31C2388 + 0x10: 0x193C74, 0x31C2388 + 0x20: 0x1934AC,
    0x30BD228 + 0x240: 0xA09BC4, 0x30BD228 + 0x250: 0x193674,
    0x30BCE78 + 0x2B8: 0x194718, 0x30BCE78 + 0x2C8: 0x194AC4,
    0x30A75A8 + 0x120: 0x193B00, 0x30A75A8 + 0x130: 0x193E58,
    0x36A1D50: 0x18F2540, 0x36A1D58: 0x18F2540, 0x36A1D60: 0x1304ED8, 0x36A1D70: 0x258480,
}


def read_fixture():
    baseline, source, owners, tower, *_ = (json.loads(pinned(path, value)) if path.suffix == ".json"
                                         else pinned(path, value) for path, value in INPUTS.items())
    timer, = source["matches"]
    require(source["save_sha256"] == owners["save_sha256"] and tower["slot"] == "ManualSave-29",
            "Unexpected fixture saves")
    mapping = [row for row in owners["node_instances"] if row["key"] == timer["node_key"]]
    require(len(mapping) == 1 and mapping[0]["value"] == timer["timer"], "Falco's saved node mapping differs")
    part = tower["components"]["time_core"]
    clock = bytes.fromhex(part["hex"])
    require(len(clock) == part["size"] == 24 and struct.unpack_from("<I", clock)[0] == part["id"],
            "Unexpected saved game-clock framing")
    now, = struct.unpack_from("<I", clock, 8)
    fixture = {
        "SavedNodeKey": (int(timer["node_key"], 16), "ULL"),
        "SavedTimer": (int(timer["timer"], 16), "U"),
        "SavedAuthoredSeconds": (int(timer["authored_seconds"]), "U"),
        "SavedRemainingSeconds": (timer["remaining_seconds"], "U"),
        "FixtureClock": (now, "U"),
    }
    require(0 < timer["remaining_seconds"] < int(timer["authored_seconds"]) and 0 < now < 0x7FFF0000,
            "Invalid original wait or illustrative post-Tower clock")
    text = "".join(f"constexpr auto {name} = {value}{suffix};\n" for name, (value, suffix) in fixture.items())
    return baseline, fixture, text


def native_packet():
    image = Image()
    require(image.sha == "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4",
            "Unknown game executable")
    spans = dict(LEAVES)
    for entry, pins in FUNCTIONS.items():
        begin, end, _ = image.function(entry)
        require(begin == entry, f"Changed native function boundary {entry:X}")
        spans[entry] = end
        if pins:
            ops = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}'
                   for row in image.disasm(entry)["instructions"]}
            require(all(ops.get(addr) == value for addr, value in pins.items()), f"Changed function {entry:X}")
    for addr, expected in SLOTS.items():
        target, = struct.unpack_from("<Q", image.data, image.off(addr))
        require(target == image.base + expected, f"Changed native slot {addr:X}")
    packet = bytearray(struct.pack("<I", len(spans)))
    slices = {}
    for entry, end in sorted(spans.items()):
        offset = image.off(entry)
        data = image.data[offset:offset + end - entry]
        packet.extend(struct.pack("<II", entry, len(data)))
        packet.extend(data)
        slices[f"{entry:08X}"] = {"end": f"{end:08X}", "sha256": digest(data)}
    return image.sha, packet, slices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100))
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()
    baseline, fixture, source = read_fixture()
    engine_sha, packet, slices = native_packet()
    binary = out / "native.bin"
    binary.write_bytes(packet)
    generated = out / "fixture_input.hpp"
    generated.write_text(source, encoding="ascii")
    batch = out / "build.cmd"
    batch.write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /EHsc /O2 /MT /I"." /sourceDependencies deps.json '
        f'"{HERE / "GameTimeRestoreChecks.cpp"}" /link /OUT:GameTimeRestoreChecks.exe\n', encoding="ascii",
    )
    build = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, capture_output=True,
                           text=True, errors="replace", timeout=90)
    (out / "build.txt").write_text(build.stdout + build.stderr, encoding="utf-8")
    print(build.stdout + build.stderr, end="")
    build.check_returncode()
    exe = out / "GameTimeRestoreChecks.exe"
    result = subprocess.run([str(exe), binary.name], cwd=out, capture_output=True,
                            text=True, errors="replace", timeout=25)
    output = result.stdout + result.stderr
    (out / "checks.txt").write_text(output, encoding="utf-8")
    print(output, end="")
    result.check_returncode()
    passed = sum(line.startswith("PASS ") for line in output.splitlines())
    require(passed == 13, "Unexpected number of passed checks")

    dependencies = json.loads((out / "deps.json").read_bytes())["Data"]
    inputs = dict(INPUTS)
    for filename in (dependencies["Source"], *dependencies["Includes"], str(Path(__file__))):
        path = Path(filename).resolve()
        inputs.setdefault(path, digest(path.read_bytes()))
    for path, expected in inputs.items():
        pinned(path, expected)
    record = {
        "status": "NATIVE_GAME_TIME_RESTORE_FIXTURE_PASS", "game_runtime_exercised": False,
        "installed_checkpoint_version": baseline["checkpoint_version"], "engine_sha256": engine_sha,
        "checks_passed": passed, "ms31": {name: value for name, (value, _) in fixture.items() if name != "FixtureClock"},
        "ms29_model_clock": fixture["FixtureClock"][0], "slices": slices, "fixture_only_relay_rva": "00A09C4D",
        "native_packet_sha256": digest(packet), "fixture_exe_sha256": digest(exe.read_bytes()),
        "inputs": {str(path.relative_to(WORKSPACE) if path.is_relative_to(WORKSPACE) else path): value
                   for path, value in inputs.items()},
    }
    (out / "assessment.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
