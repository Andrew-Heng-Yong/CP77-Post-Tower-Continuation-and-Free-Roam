"""Exercise the native handler pass after the selected phase pass."""

import argparse
import json
from pathlib import Path
import struct
import subprocess

from build_restore_fixture import HERE, WORKSPACE, Image, VCVARS, digest, pinned, require


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(8, 100))
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()
    prior = HERE / "run_07"
    receipt = pinned(prior / "assessment.json", "030E7C9872466E757DA1B667C3EE9C6F239587F2ACF5663BF0990AC959CDB009")
    base = json.loads(receipt)
    require(base["status"] == "NATIVE_MODE2_RESTORE_DISPATCH_FIXTURE_PASS", "Missing phase-pass fixture")
    for name, expected in base["inputs"].items():
        pinned(WORKSPACE / name, expected)
    engine = Image()
    require(engine.sha == base["engine_sha256"], "Engine moved since the phase pass")
    entry = 0x2B28EC
    info = engine.disasm(entry)
    require(int(info["begin_rva"], 16) == entry and int(info["end_rva"], 16) - entry == 0x185,
            "Changed native handler dispatcher size")
    expected = {
        0x2B2903: "mov rcx, qword ptr [rcx + 0xe8]",
        0x2B295C: "call 0x1402b1bc4",
        0x2B2972: "mov r8b, 2",
        0x2B297B: "call 0x1402b30a0",
        0x2B298D: "call 0x1402b2f08",
        0x2B29A7: "call qword ptr [rax + 0x138]",
        0x2B29E5: "call 0x1402b2d50",
    }
    instructions = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}' for row in info["instructions"]}
    require(all(instructions.get(ip) == value for ip, value in expected.items()), "Changed handler pass layout")
    for vtable, method in ((0x3699F88, 0x2B25CC), (0x308A948, 0x2B16E0)):
        value, = struct.unpack_from("<Q", engine.data, engine.off(vtable + 0x138))
        require(value == engine.base + method, "Changed handler restore virtual")
    start = engine.off(entry)
    handler = out / "native_handler_dispatch.bin"
    handler.write_bytes(engine.data[start:start + 0x185])
    phase = prior / "native_dispatch.bin"
    pinned(phase, base["native_dispatch_sha256"])

    batch = out / "build.cmd"
    batch.write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /I"{prior}" /sourceDependencies deps.json '
        f'"{HERE / "FalcoHandlerChecks.cpp"}" /link /OUT:FalcoHandlerChecks.exe\n',
        encoding="ascii",
    )
    build = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, text=True, capture_output=True,
                           errors="replace", timeout=90)
    (out / "build.txt").write_text(build.stdout + build.stderr, encoding="utf-8")
    print(build.stdout + build.stderr, end="")
    build.check_returncode()
    result = subprocess.run([str(out / "FalcoHandlerChecks.exe"), str(phase), str(handler)],
                            cwd=out, text=True, capture_output=True, errors="replace", timeout=30)
    (out / "fixture_checks.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    print(result.stdout + result.stderr, end="")
    result.check_returncode()
    passed = sum(line.startswith("PASS ") for line in result.stdout.splitlines())
    require(passed == 5, "Unexpected native handler test count")
    files = json.loads((out / "deps.json").read_bytes())["Data"]
    paths = [Path(name).resolve() for name in [files["Source"], *files["Includes"]]]
    record = {
        "status": "FALCO_NATIVE_PHASE_AND_HANDLER_DISPATCH_FIXTURE_PASS",
        "checks_passed": passed, "game_runtime_exercised": False,
        "phase_restore_fixture_sha256": digest(receipt),
        "native_instructions": {f"{ip:08X}": value for ip, value in expected.items()},
        "native_handler_sha256": digest(handler.read_bytes()),
        "compile_inputs": {str(path.relative_to(WORKSPACE) if path.is_relative_to(WORKSPACE) else path):
                           digest(path.read_bytes()) for path in paths},
    }
    (out / "assessment.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
