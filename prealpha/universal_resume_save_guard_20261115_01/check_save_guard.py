"""Check the save guard and run it around the pinned native timer handoff fixture."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
STEP3 = HERE.parent / "universal_resume_step3_20261114_01"
sys.path.insert(0, str(STEP3))
from run_fixture import HANDOFF, RETIREMENT, verify_packet, verify_sources

VCVARS = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat")
INPUTS = "4C8B920FE11D4DBE37A3D46CE3F9F41B68825674DB736061F9F2DF1DDC9E58FA"
PRIOR = "B82CC608A66F4A6B917081ADFE0A449F37A35AA13BF5AE04E44F68A4A2A8CC23"


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def pin(path, expected):
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError(f"Changed input: {path}")
    return data


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError(f"Changed Step 3 fixture anchor: {before}")
    return text.replace(before, after, 1)


def guarded_source(contents):
    contents = replace_once(contents, 'namespace ptfr::resume\n{', '#include "SaveGuard.hpp"\n\nnamespace ptfr::resume\n{')
    if contents.count("bool saveExcluded") != 2:
        raise ValueError("Unexpected save-guard parameters")
    return contents.replace("bool saveExcluded", "const SaveGuard::HandoffPermit& savePermit").replace(
        "!saveExcluded", "!savePermit")


def guarded_checks(contents):
    contents, holds = re.subn(r"(\b(?:abandoned|transfer)\.Hold\([^\r\n]+), (true|false)\)",
                              lambda match: match[1] + (", *permit)" if match[2] == "true" else ", refused)"),
                              contents)
    contents, restores = re.subn(r"(\btransfer\.Restore\([^\r\n]+), true\)", r"\1, *permit)", contents)
    if (holds, restores) != (5, 7):
        raise ValueError(f"Unexpected transfer call sites: {holds}, {restores}")
    contents = replace_once(contents, "    RealTimeTransfer abandoned(address, ending, events, OldSlot);",
                            """    ptfr::resume::SaveGuard saves;
    RealTimeTransfer abandoned(address, ending, events, OldSlot);
    {
        const auto save = saves.TrySave();
        const auto unavailable = saves.TryHandoff();
        test.Expect(save && !unavailable &&
                        !abandoned.Hold(reload, oldOwner, old.handler.data(), native.timerId, 0.016f, false, unavailable) &&
                        test.Remaining(native.timerId) == native.remaining,
                    "an admitted save defers the handoff before removing the stock timer");
    }
    const ptfr::resume::SaveGuard::HandoffPermit refused;
    std::optional permit{saves.TryHandoff()};""")
    contents = replace_once(contents, "    RealTimeTransfer transfer(address, ending, events, OldSlot);",
                            """    permit.reset();
    test.Expect(static_cast<bool>(saves.TrySave()), "rollback opens save admission after the original wait returns");
    permit.emplace(saves.TryHandoff());
    RealTimeTransfer transfer(address, ending, events, OldSlot);""")
    contents = replace_once(contents, "    CopyInterleave copied{test, graph, transfer};",
                            """    test.Expect(!saves.TrySave(), "new saves defer while the native timer is held");
    CopyInterleave copied{test, graph, transfer};""")
    contents = replace_once(contents, "    clearMapping(quests, node); // Model native Uninitialize removing the original node-data row.",
                            """    test.Expect(!saves.TrySave(), "old-slot drain alone does not open the save gate");
    clearMapping(quests, node); // Model native Uninitialize removing the original node-data row.""")
    contents = replace_once(contents, "    gameClock.Restore(test);\n", "")
    contents = replace_once(contents, "    test.Tick(1.5f);",
                            """    gameClock.Restore(test);
    test.Expect(transfer.SaveCoherent() && !saves.TrySave(),
                "the replacement is coherent before releasing the handoff permit");
    permit.reset();
    std::optional save{saves.TrySave()};
    if (!test.Expect(static_cast<bool>(*save), "save admission reopens for the coherent native timer"))
        return;
    test.Tick(1.5f);""")
    contents = replace_once(contents, "    test.Remove(freshId);",
                            "    save.reset();\n    test.Remove(freshId);")
    return contents


def run_logged(args, out, logfile, timeout):
    result = subprocess.run(args, cwd=out, capture_output=True, text=True, errors="replace", timeout=timeout)
    (out / logfile).write_text(result.stdout + result.stderr, encoding="utf-8")
    summarized = "\n".join(line for line in result.stdout.splitlines() if not line.startswith("PASS "))
    if summarized or result.stderr:
        print(summarized + result.stderr)
    if result.returncode:
        print(result.stdout)
    result.check_returncode()
    return sum(line.startswith("PASS ") for line in result.stdout.splitlines())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100), metavar="1–99")
    args = parser.parse_args()
    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    old = STEP3 / "run_03"
    prior = json.loads(pin(old / "assessment.json", INPUTS))
    retirement = json.loads(pin(RETIREMENT / "evidence_05/assessment.json", PRIOR))
    files, hashes = verify_sources(retirement)
    for key, path in files.items():
        pin(path, prior["sources"][key])
    engine, real_clock, game_clock = verify_packet(retirement, prior["wait"])
    if sha(real_clock) != prior["fixture_sha256"] or sha(game_clock) != prior["game_clock_fixture_sha256"]:
        raise ValueError("Changed native fixture inputs")

    for name, data in (
        ("engine_slices.bin", real_clock),
        ("game_clock_slices.bin", game_clock),
        ("fixture_input.hpp", pin(old / "fixture_input.hpp", prior["sources"]["fixture_input.hpp"])),
        ("WaitTransfer.hpp", guarded_source((STEP3 / "WaitTransfer.hpp").read_text(encoding="utf-8")).encode()),
        ("WaitTransferChecks.cpp", guarded_checks((STEP3 / "WaitTransferChecks.cpp").read_text(encoding="utf-8")).encode()),
    ):
        (out / name).write_bytes(data)

    sources = [HERE / "SaveGuard.hpp", HERE / "SaveGuardChecks.cpp", Path(__file__),
               out / "WaitTransfer.hpp", out / "WaitTransferChecks.cpp"]
    source_hashes = {str(path.relative_to(HERE)): sha(path.read_bytes()) for path in sources}
    common = f'/nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /I"." /I"{HERE}" /I"{STEP3}" /I"{HANDOFF}"'
    (out / "build.cmd").write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe {common} "{HERE / "SaveGuardChecks.cpp"}" /link /OUT:SaveGuardChecks.exe\n'
        f'if errorlevel 1 exit /b 1\ncl.exe {common} WaitTransferChecks.cpp /link /OUT:WaitTransferChecks.exe\n',
        encoding="ascii",
    )
    run_logged(["cmd.exe", "/d", "/c", "build.cmd"], out, "build.txt", 90)
    guard_count = run_logged([str(out / "SaveGuardChecks.exe")], out, "guard.txt", 20)
    handoff_count = run_logged([str(out / "WaitTransferChecks.exe"), str(out / "engine_slices.bin"),
                                str(out / "game_clock_slices.bin")], out, "handoff.txt", 25)
    if (guard_count, handoff_count) != (9, 41):
        raise ValueError(f"Unexpected check count: {guard_count} and {handoff_count}")
    for path, digest in source_hashes.items():
        pin(HERE / path, digest)
    if any(sha(path.read_bytes()) != hashes[key] for key, path in files.items()):
        raise ValueError("Fixture changed during build")
    evidence = {"status": "GUARD_AND_NATIVE_TIMER_FIXTURE_PASS", "engine_sha256": engine,
                "guard_checks": guard_count, "timer_fixture_checks": handoff_count,
                "sources": source_hashes, "game_runtime_exercised": False}
    (out / "assessment.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"{guard_count} save-guard checks and {handoff_count} guarded timer checks passed")


if __name__ == "__main__":
    main()
