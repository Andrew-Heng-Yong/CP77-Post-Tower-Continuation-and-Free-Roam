"""Compile the MS31 restore selector and exercise the pinned native mode-2 dispatcher."""

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
WORKSPACE = PREALPHA.parent
sys.path.insert(0, str(PREALPHA / "universal_resume_save_admission_20261115_01"))
from build_save_admission import Image, VCVARS, digest, pinned, require

sys.path.insert(0, str(PREALPHA / "universal_resume_20261114_01"))
from read_handlers import phase_hash, token


def native_dispatch():
    engine = Image()
    pins = {
        0x2B32B0: {0x2B3328: "mov r8b, 2", 0x2B3332: "dec dword ptr [rdi + 0xc]",
                   0x2B3343: "call 0x1402b30a0", 0x2B3365: "call qword ptr [rax + 0x130]",
                   0x2B3395: "call 0x1402b2eb4", 0x2B33AB: "call 0x1402b2d50"},
        0x2B33F0: {0x2B3417: "movzx r10d, word ptr [rax]", 0x2B34A1: "call r10"},
        0x2B0800: {0x2B0835: "cmp byte ptr [rdx + 1], 2", 0x2B084B: "call 0x14079cf00",
                   0x2B0855: "je 0x1402b08bf", 0x2B08B6: "call 0x140eb6b3c"},
        0x156EFD0: {0x156EFFE: "mov byte ptr [rdi + rdx], al", 0x156F001: "call 0x1402b32b0"},
    }
    for entry, expected in pins.items():
        info = engine.disasm(entry)
        require(int(info["begin_rva"], 16) == entry, f"Native entry moved {entry:X}")
        ops = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}' for row in info["instructions"]}
        require(all(ops.get(ip) == value for ip, value in expected.items()), f"Native restore layout changed {entry:X}")
    for vtable, method in ((0x3699F88, 0x2B33F0), (0x308A948, 0x2B0C4C)):
        value, = struct.unpack_from("<Q", engine.data, engine.off(vtable + 0x130))
        require(value == engine.base + method, "Root or phase restore virtual changed")
    entry = 0x2B32B0
    begin, end, _ = engine.function(entry)
    require(begin == entry and end - begin == 0x13F, "Restore dispatcher region changed")
    start = engine.off(begin)
    return engine.sha, engine.data[start:start + end - begin], pins


def fixture_input(before, wait):
    phase_registration = f"{token('questPhaseNodeDefinition'):016x}"
    rows = {row["slot"]: (row, control["phase"])
            for control in [*before["parents"], *before["body"]] for row in control["registrations"]}
    require(len(rows) == 9 and len(before["logical_latches"]) == 1 and not before["queue"]["notifications"]
            and not before["queue"]["resource_requests"], "Fixture has different native selection state")
    require(sum(row["type"] == phase_registration for row, _ in rows.values()) == 6,
            "Unexpected saved phase-node shape")
    timer, = wait["matches"]
    latch, = before["logical_latches"]
    require(timer["remaining_seconds"] == 86388 and latch["table"] == 5 and latch["value"] == 4,
            "Selected wait or branch changed")
    sorted_rows = sorted(rows.values(), key=lambda item: (len(item[1]), item[1], item[0]["node"]))
    text = ["using namespace ptfr::resume;", "constexpr std::array SavedHandlers{"]
    for row, path in sorted_rows:
        text.append(f'    Handler{{{{0x{row["type"]}ULL, 0x{phase_hash(path):08X}U, {row["node"]}}}, '
                    f'{row["slot"]}, Binding::Live}},')
    text.extend(["};", "constexpr std::array SavedInstances{"])
    text.extend(f'    NodeInstance{{0x{row["key"]}ULL, 0x{row["value"]}ULL}},' for row in before["node_instances"])
    text.extend(["};", f'constexpr Fact SavedChoice{{{latch["key"]}U, {latch["value"]}}};',
                 f'constexpr Timing SavedWait{{{timer["physical_slot"]}, Clock::Game, 0x{timer["timer"]}ULL, '
                 f'{timer["remaining_seconds"]}.0, 0}};'])
    return "\n".join(text) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(7, 100))
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()
    pins = {
        HERE / "run_05/selection_assessment.json": "A7533BD70ED0B8AF0CDD1A794061AAD6F955C406C5567A31862CDC23BC598D8D",
        HERE / "run_06/selection_assessment.json": "7E9AA594692F8FC26576F1C53EAD8BFA16536B8776DC33B1E622B7BD6F360EC1",
        PREALPHA / "universal_resume_first_live_wait_20261115_01/run_04/assessment.json":
            "FEAA8527FA62476056C3AC207613549985CEBA6D97D22C83D990A3FA6157CCB2",
        PREALPHA / "universal_resume_checkpoint_probe_20261114_01/source_02/Checkpoint.hpp":
            "9492B30D454CB6B2F3C3C8706744BE026C5EBB6D92F3A230D02D76B2CBEE431B",
        PREALPHA / "universal_resume_save_admission_20261115_01/SaveAdmission.hpp":
            "F9288E0F4A6B1CE6845FFAAE2372C126C0447AB6DDECDE81D1CB23A0EC17233E",
        PREALPHA / "universal_resume_save_guard_20261115_01/SaveGuard.hpp":
            "F76CBF2CB175FD5563156CD60880F2D4EEA4D26B8544825AB3D0935EEBB98AC1",
    }
    before, after, wait, *_ = (pinned(file, value) for file, value in pins.items())
    control = json.loads(after)
    require(control["tower_control"] and all(not row["registrations"] for row in control["parents"] + control["body"]),
            "Original rows still appear in the post-Tower control")
    engine_sha, native, native_pins = native_dispatch()
    blob = out / "native_dispatch.bin"
    blob.write_bytes(native)
    generated = out / "fixture_input.hpp"
    generated.write_text(fixture_input(json.loads(before), json.loads(wait)), encoding="ascii")

    batch = out / "build.cmd"
    batch.write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /I"." /sourceDependencies deps.json '
        f'"{HERE / "FalcoRestoreChecks.cpp"}" /link /OUT:FalcoRestoreChecks.exe\n',
        encoding="ascii",
    )
    result = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, text=True, capture_output=True,
                            errors="replace", timeout=90)
    (out / "build.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    print(result.stdout + result.stderr, end="")
    result.check_returncode()
    test = subprocess.run([str(out / "FalcoRestoreChecks.exe"), blob.name], cwd=out, text=True, capture_output=True,
                          errors="replace", timeout=30)
    (out / "fixture_checks.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    print(test.stdout + test.stderr, end="")
    test.check_returncode()
    passed = sum(line.startswith("PASS ") for line in test.stdout.splitlines())
    require(passed == 18, "Unexpected fixture check count")
    for path in (HERE / "FalcoRestorePlan.hpp", HERE / "FalcoRestoreChecks.cpp", generated, Path(__file__)):
        pins[path] = digest(path.read_bytes())
    inventory = json.loads((out / "deps.json").read_bytes())["Data"]
    for name in [inventory["Source"], *inventory["Includes"]]:
        path = Path(name).resolve()
        pins.setdefault(path, digest(path.read_bytes()))
    for path, value in pins.items():
        pinned(path, value)
    record = {
        "status": "NATIVE_MODE2_RESTORE_DISPATCH_FIXTURE_PASS", "game_runtime_exercised": False,
        "owner_and_prefab_callbacks": "STUBS", "engine_sha256": engine_sha, "native_checks": native_pins,
        "native_dispatch_sha256": digest(native), "checks_passed": passed,
        "inputs": {str(path.relative_to(WORKSPACE) if path.is_relative_to(WORKSPACE) else path): value
                   for path, value in pins.items()},
    }
    (out / "assessment.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
