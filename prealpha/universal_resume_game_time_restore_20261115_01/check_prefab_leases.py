"""Verify the prefab loader's readback ABI and the serial quest update boundary."""

import argparse
import json
from pathlib import Path
import struct
import subprocess

from check_game_time import HERE, PREALPHA, WORKSPACE, Image, VCVARS, digest, pinned, require


PINS = {
    0x22CA300: {0x22CA321: "lea esi, [rbp - 1]", 0x22CA32D: "lock cmpxchg byte ptr [rbx], sil"},
    0x698E24: {0x698E44: "lea rdx, [rcx + 0x30]", 0x698E51: "lea r12, [rsi + 0x38]",
               0x698E87: "imul rcx, rax, 0x68", 0x698E8B: "add rcx, qword ptr [rdi + 0x10]",
               0x698ECD: "xchg byte ptr [rax], cl", 0x698ED3: "lea rcx, [rsi + 0xa0]"},
    0x699F78: {0x699FC7: "lea rcx, [r15 + 0x38]", 0x69A053: "call 0x14019b75c",
               0x69A06F: "lea rcx, [r14 + 0x10]", 0x69A089: "mov byte ptr [r14 + 0x60], 1",
               0x69A094: "cmp dword ptr [r14 + 0x1c], esi"},
    0x699410: {0x699431: "test byte ptr [rcx + 0x20], dil", 0x69943F: "mov eax, dword ptr [rbx + 0xc]",
               0x69948F: "call 0x142ca34e8"},
    0x6996C0: {0x6996E8: "add rcx, 0x60", 0x69972A: "mov rsi, qword ptr [rbp + 0x70]",
               0x69974D: "mov dword ptr [rsi + rdi*4], eax"},
    0x698FC8: {0x698FD4: "cmp dword ptr [rcx + 0xac], 0", 0x699037: "call 0x140699064",
               0x699042: "and dword ptr [rsi + 0xac], 0"},
    0x4AD5CC: {0x4AD65B: "call 0x140698fc8", 0x4AD663: "call 0x140dad678", 0x4AD66B: "call 0x1403534dc",
               0x4AD757: "call 0x1402b28ec"},
    0x3534DC: {0x353583: "lea rdx, [rsi + 0x60]", 0x353590: "xchg byte ptr [rax], cl",
               0x3535A0: "call 0x141ffad60", 0x3536DF: "call 0x1419417f0"},
    0x7C0CA0: {0x7C0D56: "call 0x140b79234", 0x7C0D87: "call 0x140b79130"},
    0x2B26A4: {0x2B2858: "mov rcx, qword ptr [rax + 0x198]", 0x2B287F: "call qword ptr [rax + 0x28]",
               0x2B28B8: "call 0x1414d459c"},
    0x19387E4: {0x19387F7: "call 0x14035fc9c"},
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100))
    out = HERE / f"run_prefab_{parser.parse_args().attempt:02}"
    out.mkdir()
    image = Image()
    require(image.sha == "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4", "Wrong engine")
    for entry, expected in PINS.items():
        decoded = image.disasm(entry)
        require(int(decoded["begin_rva"], 16) == entry, f"Changed function boundary {entry:X}")
        ops = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}' for row in decoded["instructions"]}
        require(all(ops.get(ip) == value for ip, value in expected.items()), f"Changed native layout {entry:X}")
    value, = struct.unpack_from("<Q", image.data, image.off(0x306F758 + 0x28))
    require(value == image.base + 0x19387E4, "Changed native resource prefetch virtual")

    source = PREALPHA / "universal_resume_first_live_wait_20261115_01/run_sources_01/source_assessment.json"
    source_sha = "5905BCE8AFCC83AFA58BA4868AD45B01E0999741BD50A64C31DE3631264DE009"
    resources = json.loads(pinned(source, source_sha))["resources"]
    refs = [item["prefabNodeRef"]["$value"] for resource in resources
            for item in resource["root_support"]["phasePrefabs"]]
    require(refs == ["#mq049_pr_main", "#mq049_pr_reyes"], "Changed authored prefab obligations")
    require(all(not resource["root_support"]["inplacePhases"] for resource in resources),
            "Unexpected inplace subresource in the pinned path")

    batch = out / "build.cmd"
    batch.write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /EHsc /O2 /MT /sourceDependencies deps.json '
        f'"{HERE / "PrefabLeaseChecks.cpp"}" /link /OUT:PrefabLeaseChecks.exe\n', encoding="ascii",
    )
    built = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, capture_output=True,
                           text=True, errors="replace", timeout=90)
    log = built.stdout + built.stderr
    (out / "build.txt").write_text(log, encoding="utf-8")
    print(log, end="")
    built.check_returncode()
    exe = out / "PrefabLeaseChecks.exe"
    result = subprocess.run([str(exe)], cwd=out, capture_output=True, text=True, errors="replace", timeout=20)
    report = result.stdout + result.stderr
    (out / "checks.txt").write_text(report, encoding="utf-8")
    print(report, end="")
    result.check_returncode()
    passed = sum(line.startswith("PASS ") for line in report.splitlines())
    require(passed == 12, "Unexpected lease fixture result")
    paths = json.loads((out / "deps.json").read_bytes())["Data"]
    inputs = {source: source_sha}
    for filename in (paths["Source"], *paths["Includes"], str(Path(__file__))):
        file = Path(filename).resolve()
        inputs[file] = digest(file.read_bytes())
    record = {
        "status": "PREFAB_TICKET_READBACK_FIXTURE_PASS", "game_runtime_exercised": False,
        "engine_sha256": image.sha, "checks_passed": passed, "authored_refs": refs,
        "fixture_exe_sha256": digest(exe.read_bytes()), "native_instructions": PINS,
        "inputs": {str(path.relative_to(WORKSPACE) if path.is_relative_to(WORKSPACE) else path): value
                   for path, value in inputs.items()},
    }
    (out / "assessment.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
