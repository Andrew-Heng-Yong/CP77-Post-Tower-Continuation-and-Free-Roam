"""Verify the selected quest lane against the pinned executable and runtime layout fixture."""

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
WORKSPACE = PREALPHA.parent
sys.path.insert(0, str(PREALPHA / "universal_resume_falco_transfer_20261115_01"))
from build_restore_fixture import Image, VCVARS, digest, pinned, require


PINS = {
    0x21F99E0: {0x21F9A1B: "test rcx, rcx", 0x21F9A20: "inc dword ptr [rcx + 0x20]",
               0x21F9A23: "cmp qword ptr [rsi + 0x40], 0", 0x21F9A55: "xor al, al"},
    0x350C30: {0x350C4A: "lea rdx, [rcx + 0x18]", 0x350CA5: "mov qword ptr [rdi + 8], rax",
               0x350CAE: "lock inc dword ptr [rax]"},
    0x34F7C4: {0x34F7DC: "lea rdx, [rcx + 0x18]", 0x34F825: "call 0x14034f680"},
    0x350BF8: {0x350C0E: "add rcx, 0x48", 0x350C1F: "lock xadd byte ptr [rbx + 0x58], al"},
    0x34F330: {0x34F342: "lock xadd byte ptr [rcx + 0x58], al", 0x34F369: "call 0x140195798"},
    0x2B1020: {0x2B1107: "call 0x140d6272c", 0x2B1126: "call 0x14035fddc"},
    0x2B11A4: {0x2B1233: "call qword ptr [rax + 0x40]", 0x2B1245: "call 0x140350bf8"},
    0x2B13F0: {0x2B1474: "call 0x140351ca8", 0x2B14B9: "call 0x140889c38"},
    0x2B1D30: {0x2B1ED3: "test rdx, rdx", 0x2B1F10: "mov rax, qword ptr [rcx]",
               0x2B1F13: "call qword ptr [rax + 0x38]", 0x2B1F36: "call 0x140698e24"},
    0x34F0D0: {0x34F109: "call 0x14034f2b4", 0x34F126: "call 0x14034f330"},
    0x88AFCC: {0x88B006: "cmp sil, 2", 0x88B011: "xchg byte ptr [rbx + 0x50], al",
               0x88B104: "call 0x140dd514c"},
    0x2B32B0: {0x2B3343: "call 0x1402b30a0", 0x2B3365: "call qword ptr [rax + 0x130]",
               0x2B33AB: "call 0x1402b2d50"},
    0x2B28EC: {0x2B297B: "call 0x1402b30a0", 0x2B29A7: "call qword ptr [rax + 0x138]",
               0x2B29E5: "call 0x1402b2d50"},
    0x2B0800: {0x2B084B: "call 0x14079cf00", 0x2B0855: "je 0x1402b08bf",
               0x2B08B6: "call 0x140eb6b3c"},
    0xBEC6D4: {0xBEC75A: "call 0x1402b1d30", 0xBEC76E: "call 0x1401cafc4"},
    0x2FCEAC: {0x2FCED4: "call 0x1402b1b64", 0x2FCEE7: "call 0x1402fcfd0",
               0x2FCF07: "jmp 0x1402fcf0c"},
    0x2FCF0C: {0x2FCF77: "call qword ptr [rax + 0x20]", 0x2FCF90: "call 0x1402fd024"},
    0x2FDA9C: {0x2FDAC6: "call qword ptr [rax + 0x80]", 0x2FDADD: "call qword ptr [rax + 0x68]"},
    0x351358: {0x351370: "call qword ptr [rax + 0x170]", 0x351389: "call qword ptr [rax + 0xd8]"},
    0x249934: {0x249944: "mov rax, qword ptr [rcx]", 0x24994B: "call qword ptr [rax + 0x1d0]",
               0x249953: "xchg dword ptr [rbx + 0x30], eax"},
    0x88AFA0: {0x88AFBD: "call qword ptr [rax + 0x30]", 0x88AFC2: "xchg dword ptr [rbx + 0x30], eax"},
    0x88B6AC: {0x88B6AC: "mov eax, dword ptr [rcx + 0x30]", 0x88B6B4: "je 0x14088b6d9"},
    0x1934AC: {0x1934EF: "call qword ptr [rax + 0x2c0]", 0x193502: "call qword ptr [rax + 0x250]",
               0x193508: "xchg dword ptr [rbx + 0x30], edi"},
    0x22CA300: {0x22CA32D: "lock cmpxchg byte ptr [rbx], sil"},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100))
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()
    image = Image()
    require(image.sha == "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4", "Wrong engine")
    for entry, expected in PINS.items():
        decoded = image.disasm(entry)
        require(int(decoded["begin_rva"], 16) == entry, f"Changed function boundary {entry:X}")
        ops = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}' for row in decoded["instructions"]}
        for ip, value in expected.items():
            require(ops.get(ip) == value, f"Changed native layout {ip:X}: {ops.get(ip)}")

    vtables = {(0x306F758, 0x38): 0x34F7C4, (0x306F758, 0x40): 0x350C30,
               (0x3699F88, 0x130): 0x2B33F0, (0x3699F88, 0x138): 0x2B25CC,
               (0x30470A8, 0x188): 0x3519F8, (0x3046748, 0x10): 0x88AFCC,
               (0x30476E8, 0x178): 0x2FDA9C, (0x30FB0E0, 0xE8): 0x351358, (0x30D8CE0, 0xE8): 0x351358,
               (0x310C838, 0xD8): 0x3625C4, (0x302BEC8, 0xD8): 0x351660, (0x3048D60, 0x20): 0x249934,
               (0x30467A8, 0x20): 0x88AFA0}
    for (vt, slot), target in vtables.items():
        value, = struct.unpack_from("<Q", image.data, image.off(vt + slot))
        require(value == image.base + target, f"Changed virtual {vt:X}+{slot:X}")

    source = PREALPHA / "universal_resume_first_live_wait_20261115_01/run_sources_01/source_assessment.json"
    source_sha = "5905BCE8AFCC83AFA58BA4868AD45B01E0999741BD50A64C31DE3631264DE009"
    bind = json.loads(pinned(source, source_sha))
    require(len(bind["resources"]) == 7 and bind["native_ancestry"][-1] == [0], "Unexpected source selection")

    batch = out / "build.cmd"
    batch.write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /EHsc /O2 /MT /sourceDependencies deps.json '
        f'"{HERE / "RetainedQuestRestoreChecks.cpp"}" /link /OUT:RetainedQuestRestoreChecks.exe\n', encoding="ascii",
    )
    built = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, capture_output=True,
                           text=True, errors="replace", timeout=90)
    log = built.stdout + built.stderr
    (out / "build.txt").write_text(log, encoding="utf-8")
    print(log, end="")
    built.check_returncode()
    exe = out / "RetainedQuestRestoreChecks.exe"
    result = subprocess.run([str(exe)], cwd=out, capture_output=True, text=True, errors="replace", timeout=20)
    report = result.stdout + result.stderr
    (out / "checks.txt").write_text(report, encoding="utf-8")
    print(report, end="")
    result.check_returncode()
    passed = sum(line.startswith("PASS ") for line in report.splitlines())
    require(passed == 17, "Unexpected quest fixture result")
    paths = json.loads((out / "deps.json").read_bytes())["Data"]
    inputs = {source: source_sha}
    for filename in (paths["Source"], *paths["Includes"], str(Path(__file__))):
        file = Path(filename).resolve()
        inputs[file] = digest(file.read_bytes())
    record = {
        "status": "RETAINED_QUEST_RESTORE_FIXTURE_PASS", "game_runtime_exercised": False,
        "engine_sha256": image.sha, "checks_passed": passed, "fixture_exe_sha256": digest(exe.read_bytes()),
        "instructions": PINS, "virtuals": [{"vtable": vt, "offset": slot, "target": target}
                                           for (vt, slot), target in vtables.items()],
        "inputs": {str(path.relative_to(WORKSPACE) if path.is_relative_to(WORKSPACE) else path): value
                   for path, value in inputs.items()},
    }
    (out / "assessment.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
