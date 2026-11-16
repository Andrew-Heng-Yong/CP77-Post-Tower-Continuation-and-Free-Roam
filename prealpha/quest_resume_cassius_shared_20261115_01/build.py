"""Build the selection successor and run the shared native restore fixtures."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
SOURCE = HERE / "source_01"
PREVIOUS = PREALPHA / "universal_resume_native_registration_20261115_01"
sys.path.insert(0, str(PREALPHA / "universal_resume_live_candidate_20261115_01"))
from build_live import compile_candidate, inventory_from_compile, run_regressions, write_response
from candidate_common import ENGINE_SHA, VCVARS, checked_path, digest, load, payload_path, pin, require, write_json

INSTALL = PREVIOUS / "staged_01/deployment_01/installed_manifest_01.json"
INSTALL_SHA = "2BDDD85E989E3346B7973606D109FCE91982736517F38E96EA7FCE1096B8785F"
PREVIOUS_BUILD_SHA = "2247F349F279CFFBB163425EF84102D327029244337925A98B0410A9E31C95BB"
CONTRACT = PREALPHA / "quest_resume_stage_selection_20261115_01/stage_contract.json"
CONTRACT_SHA = "A4522783B63629F79A361114092CB575645ADAE86A9276F126B2C4811432D3BD"
EXPORT_SHA = "D519744FC3D88E28F60B0BF3E98673D2BC21283EA3A59CB72A24679036822C0D"
DLL_SOURCE = SOURCE / "NativeCheckpoint.cpp"
FIXTURES = {"StagePlanChecks": 20, "SharedRestoreChecks": 10}


def verify_baseline(baseline):
    require(baseline["checkpoint_version"] == "0.1.10", "Wrong installation predecessor")
    game = Path(baseline["game_root"])
    pin(game / "bin/x64/Cyberpunk2077.exe", ENGINE_SHA)
    for group, expected in (("core_files", 51), ("companion_files", 1), ("required_files", 26)):
        require(len(baseline[group]) == expected, f"Unexpected baseline count for {group}")
        for row in baseline[group]:
            pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])


def fixture_header(out, baseline, contract):
    export = Path(baseline["game_root"]) / (
        "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/"
        "checkpoint_execution_feff5775c34c732362f886201f4b2fb7.json"
    )
    capture = load(export, EXPORT_SHA)
    sample, = (row for row in contract["live_cutoffs"] if row["run_start"] == "ManualSave-31")
    require(sample["id"] == capture["id"] and sample["sha256"] == EXPORT_SHA, "Cutoff mismatch")
    restore_rows = [row["registration"] for row in sample["ancestor_owners"]] + [sample["live_listener"]]
    require(all(capture["handlers"].count(row) == 1 for row in restore_rows), "Missing original listener")
    body = sample["original_phase"][3]
    phases = [next(row for row in capture["phases"] if row[3] == body[:depth])
              for depth in range(1, len(body) + 1)]
    require(phases[-1] == sample["original_phase"] and len(restore_rows) == 5, "Unexpected fixture shape")
    excluded, = (row for row in capture["handlers"] if row[2:4] == [1551125999, 28])

    def handler(row):
        slot, type_hex, phase, node, binding = row
        require(binding == 1, "Unbound fixture handler")
        return f"Handler{{{{0x{type_hex}ULL, {phase}U, {node}U}}, {slot}U, Binding::Live}}"

    text = ['#pragma once', 'using namespace ptfr::resume;', 'inline constexpr std::array OriginalPhases{']
    for hash32, depot, handlers, path in phases:
        words = ", ".join(str(v) for v in path)
        text.append(f"    Phase{{{{{words}}}, {len(path)}, {hash32}U, 0x{depot}ULL, {handlers}U}},")
    text.extend(['};', 'inline constexpr std::array OriginalHandlers{'])
    text.extend(f"    {handler(row)}," for row in restore_rows)
    text.extend(['};', f"inline constexpr auto ExcludedMessageHandler = {handler(excluded)};", ''])
    target = out / "CassiusEvidence.hpp"
    target.write_text("\n".join(text), encoding="utf-8")
    return export, target


def run_fixtures(out):
    commands = [f'call "{checked_path(VCVARS)}" >nul']
    for name in FIXTURES:
        write_response(out, name, HERE / f"{name}.cpp", [f"/I{chr(34)}{out}{chr(34)}", f"/Fe{name}.exe"])
        commands.append(f"cl.exe @{name}.rsp")
    batch = out / "fixtures.cmd"
    batch.write_text("@echo off\n" + "\nif errorlevel 1 exit /b 1\n".join(commands) +
                     "\nif errorlevel 1 exit /b 1\n", encoding="ascii")
    built = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, capture_output=True,
                           text=True, errors="replace", timeout=100, creationflags=subprocess.CREATE_NO_WINDOW)
    (out / "fixture_compile.txt").write_text(built.stdout + built.stderr, encoding="utf-8")
    print(built.stdout + built.stderr, end="")
    built.check_returncode()
    counts = {}
    for name, expected in FIXTURES.items():
        run = subprocess.run([str(out / f"{name}.exe")], cwd=out, capture_output=True, text=True,
                             timeout=25, creationflags=subprocess.CREATE_NO_WINDOW)
        (out / f"{name}.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
        print(run.stdout + run.stderr, end="")
        run.check_returncode()
        counts[name] = len(re.findall(r"^PASS ", run.stdout, re.M))
        require(counts[name] == expected, f"Unexpected {name} pass count {counts[name]}")
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100))
    args = parser.parse_args()
    baseline = load(INSTALL, INSTALL_SHA)
    contract = load(CONTRACT, CONTRACT_SHA)
    previous = load(PREVIOUS / "run_01/assessment.json", PREVIOUS_BUILD_SHA)
    verify_baseline(baseline)
    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    export, fixture_input = fixture_header(out, baseline, contract)
    new_sources = {path: digest(path) for path in [*SOURCE.iterdir(), *(HERE / f"{name}.cpp" for name in FIXTURES)]}
    binary = compile_candidate(out, DLL_SOURCE)
    inventory = inventory_from_compile(out)
    counts = run_regressions(out) | run_fixtures(out)
    for name in FIXTURES:
        record = json.loads((out / f"{name}.deps.json").read_bytes())["Data"]
        inventory[name] = {Path(path): digest(Path(path)) for path in [record["Source"], *record["Includes"]]}
    known = {str(path).lower(): checksum for paths in previous["inputs"].values() for path, checksum in paths.items()}
    known.update({str(path).lower(): checksum for path, checksum in new_sources.items()})
    generated = {str(path).lower() for path in (fixture_input, out / "CheckpointChecks.cpp")}
    for sources in inventory.values():
        for path, checksum in sources.items():
            actual = str(path).lower()
            if actual not in generated:
                require(known.get(actual) == checksum, f"Unexpected compile input: {path}")
            require(digest(path) == checksum, f"Compile input changed: {path}")
    runtime = {path.name.lower() for path in inventory["NativeCheckpoint"] if path.parent == SOURCE}
    require({"nativecheckpoint.cpp", "nativesaveadmission.inc", "nativestageselection.inc",
             "stageplan.hpp", "retainedquestrestore.hpp"} == runtime, f"Wrong runtime inputs {runtime}")
    require(all("falco" not in path.name.lower() for path in inventory["NativeCheckpoint"]), "Excluded pilot compiled")
    verify_baseline(baseline)
    pin(export, EXPORT_SHA)
    pin(CONTRACT, CONTRACT_SHA)
    write_json(out / "assessment.json", {
        "status": "OFFLINE_SELECTION_AND_NATIVE_RESTORE_FIXTURES_PASS",
        "version": "0.1.11",
        "live_restore_enabled": False,
        "installed_manifest_sha256": INSTALL_SHA,
        "stage_contract_sha256": CONTRACT_SHA,
        "cutoff_export_sha256": EXPORT_SHA,
        "candidate_sha256": digest(binary),
        "checks": counts,
        "compile_inputs": {name: {str(path): sha for path, sha in rows.items()}
                           for name, rows in inventory.items()},
    })
    print(f"Saved assessment in {out}")


if __name__ == "__main__":
    main()
