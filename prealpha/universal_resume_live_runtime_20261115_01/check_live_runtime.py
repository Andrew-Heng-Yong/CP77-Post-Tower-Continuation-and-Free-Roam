"""Build the integrated native handoff fixture and pin its deployable input set."""

import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
WORKSPACE = PREALPHA.parent
SOURCE = HERE / "source_01/NativeCheckpoint.cpp"
sys.path.insert(0, str(PREALPHA / "universal_resume_save_admission_20261115_01"))
from build_save_admission import Image, SDK, VCVARS, digest, pinned, require


HOOKS = {
    0x1934AC: "48895c2408488974", 0x193C74: "48895c2420555657",
    0xA0A84C: "48895c241848894c", 0x88BC58: "89542410534883ec",
    0xEB6B3C: "40534883ec308379", 0x69B1FC: "488bc44889580848",
}
VTABLES = {
    0x31C2388 + 0x10: 0x193C74, 0x31C2388 + 0x20: 0x1934AC,
    0x30BCE78 + 0x200: 0x88BC58, 0x30BCE78 + 0x2C8: 0x194AC4,
    0x308F3B8 + 0x18: 0x69B1FC, 0x306FA58 + 0x18: 0x350E50,
}

CONTROL = HERE / "run_02/assessment.json"
WAIT = PREALPHA / "universal_resume_first_live_wait_20261115_01/run_04/assessment.json"
EVIDENCE = {
    CONTROL: "8DEFA956FD334419A959DBB48E025F17F9BF3FC56B0365D0048D3493C3F1091A",
    WAIT: "FEAA8527FA62476056C3AC207613549985CEBA6D97D22C83D990A3FA6157CCB2",
    PREALPHA / "universal_resume_falco_transfer_20261115_01/run_08/assessment.json":
        "BC8A966754F946110ACD93B1DBB022535F54E614718FB5066707B686BDFDEDA8",
    PREALPHA / "universal_resume_game_time_restore_20261115_01/run_01/assessment.json":
        "02E32F09A6C471277596D7AB2B6A1CBFAE2B03D6139555FB4730F6A3079A5E2A",
}


def native_checks():
    engine = Image()
    for address, expected in HOOKS.items():
        offset = engine.off(address)
        require(engine.data[offset:offset + 8].hex() == expected, f"Hook entry moved {address:X}")
    for address, expected in VTABLES.items():
        target, = struct.unpack_from("<Q", engine.data, engine.off(address))
        require(target == engine.base + expected, f"Virtual method moved {address:X}")
    return engine.sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(3, 100))
    parser.add_argument("--compile", required=True, type=Path)
    parser.add_argument("--quest-proof", required=True, type=Path)
    parser.add_argument("--world-proof", required=True, type=Path)
    args = parser.parse_args()
    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    engine_sha = native_checks()
    pins = dict(EVIDENCE)
    facts = json.loads(pinned(CONTROL, pins[CONTROL]))["facts"]
    timer, = json.loads(pinned(WAIT, pins[WAIT]))["matches"]
    header = out / "control_input.hpp"
    rows = "".join(f'    Fact{{FactId("{key}"), {value}}},\n' for key, value in facts.items() if value is not None)
    header.write_text(f"constexpr std::array CompletionFacts{{\n{rows}}};\n"
                      f"constexpr auto GateTicket = {facts['PTFRHS3_GateTicket']};\n"
                      f"constexpr auto CapturedSeconds = {timer['remaining_seconds']}U;\n"
                      f"constexpr auto SavedTimer = 0x{timer['timer']}U;\n"
                      f"constexpr auto SavedSlot = {timer['physical_slot']}U;\n", encoding="ascii")
    batch = out / "build.cmd"
    batch.write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /volatile:ms /I"." /external:I"{SDK}" /external:W0 '
        f'/sourceDependencies deps.json "{HERE / "LiveHandoffChecks.cpp"}" /link bcrypt.lib user32.lib '
        '/OUT:LiveHandoffChecks.exe\n', encoding="ascii",
    )
    compile_result = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out,
                                    capture_output=True, text=True, errors="replace", timeout=90)
    compile_log = compile_result.stdout + compile_result.stderr
    (out / "build.txt").write_text(compile_log, encoding="utf-8")
    print(compile_log, end="")
    compile_result.check_returncode()
    exe = out / "LiveHandoffChecks.exe"
    result = subprocess.run([str(exe)], cwd=out, capture_output=True, text=True, errors="replace", timeout=30)
    output = result.stdout + result.stderr
    (out / "checks.txt").write_text(output, encoding="utf-8")
    print(output, end="")
    result.check_returncode()
    passed = sum(line.startswith("PASS ") for line in output.splitlines())
    require(passed == 20, "Unexpected integrated fixture count")

    results = {}
    for component, path in (("quest", args.quest_proof.resolve()), ("world", args.world_proof.resolve())):
        raw = path.read_bytes()
        component_result = json.loads(raw)
        require(component_result["engine_sha256"] == engine_sha and component_result["game_runtime_exercised"] is False and
                component_result["checks_passed"] > 0 and component_result["status"].endswith("PASS"), "Unexpected component fixture")
        for item, expected in component_result["inputs"].items():
            source = WORKSPACE / item
            pinned(source, expected)
            if source.is_relative_to(WORKSPACE):
                pins[source] = expected
        pins[path] = digest(raw)
        results[component] = component_result["checks_passed"]

    compile_inputs = args.compile.resolve()
    inventory = json.loads(compile_inputs.read_bytes())["NativeCheckpoint"]
    pins[compile_inputs] = digest(compile_inputs.read_bytes())
    for name, expected in inventory.items():
        path = Path(name)
        pinned(path, expected)
        if path.is_relative_to(WORKSPACE):
            pins[path] = expected
    require(SOURCE in pins, "Compile inventory missed the integration translation unit")

    actual = json.loads((out / "deps.json").read_bytes())["Data"]
    for name in (actual["Source"], *actual["Includes"], str(Path(__file__)), str(HERE / "stage_runtime.py")):
        path = Path(name).resolve()
        if path.is_relative_to(WORKSPACE):
            pins.setdefault(path, digest(path.read_bytes()))
    for path, expected in pins.items():
        pinned(path, expected)
    record = {
        "status": "LIVE_HANDOFF_INTEGRATION_FIXTURE_PASS",
        "source_sha256": pins[SOURCE], "engine_sha256": engine_sha, "game_runtime_exercised": False,
        "checks_passed": passed, "component_checks": results, "fixture_exe_sha256": digest(exe.read_bytes()),
        "hook_prefixes": {f"{address:08X}": prefix for address, prefix in HOOKS.items()},
        "inputs": {path.relative_to(WORKSPACE).as_posix(): expected for path, expected in pins.items()},
    }
    proof = out / "assessment.json"
    proof.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"{proof} {digest(proof.read_bytes())}")


if __name__ == "__main__":
    main()
