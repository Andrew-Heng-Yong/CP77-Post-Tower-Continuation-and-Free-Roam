"""Build and stage the MS31 successor without touching the live installation."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "universal_resume_live_candidate_20261115_01"
sys.path.insert(0, str(PRIOR))
from build_live import compile_candidate, inventory_from_compile, run_regressions, write_response
from candidate_common import SAVE_FIXTURE, TARGET, VCVARS, WORKSPACE, checked_path, digest, load, payload_path, pin, require, write_json
from fixtures import exercise
from verify_providers import verify as verify_providers
import verify_providers as provider_scan


PREDECESSOR = HERE.parent / "universal_resume_expired_wait_20261115_01"
PRIOR_STAGE = PREDECESSOR / "staged_05"
INSTALLED = PRIOR_STAGE / "deployment_01/installed_manifest_01.json"
INSTALLED_SHA = "F5495916387E24C33C34F5C17FE16FEBBE6F1573EABBD8E50CEBAD768013498F"
BEFORE = "RD10_EXECUTION_CHECKPOINT_FALCO_ELAPSED"
AFTER = "RD10_EXECUTION_CHECKPOINT_NATIVE_REGISTRATION"
SCHEMA = f"PTFR_{AFTER}_CORE_V1"
VERSION = "0.1.10"
SCOPE = f"Install checkpoint v{VERSION} for the genuine MS31 Over the Edge handoff with corrected native registration."
CONTROL = HERE.parent / "universal_resume_live_runtime_20261115_01/run_06/control_input.hpp"
CONTROL_SHA = "7F548CBAB59A7B76B8FE14C7AFBCF127469F6D9B08D3EAF2E775627C1B272E60"
BASE_DLL_SHA = "3C03247AFA2F2AD27936D22811C93A06BDC7AA704D8B19FDC2C696C63B8A7A95"
ENGINE_SHA = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"
TEMPLATE_SHA = "4F44844272CBBBAB2CA516BBE8CF6C15847B222FE35C51CB5577024975E1D2F7"
SCRIPT_SHA = "81D8196A5B7B465EBD026E00143A2DCA6F792E6D5E7C706F48AD24D7F8EB74FD"
PRIOR_BUILD_SHA = "62A24CE6711DAF1C047CFF8AECD1E02C9BB0ED3B412D6B9100FB3C83F57B1587"
PRIOR_SOURCE_SHA = "480EA4424F9774C4221DF72A0EEB7B1067D63679AB9B0F6F6CB90492B0C94B04"


def verify_baseline(baseline):
    require(baseline["checkpoint_version"] == "0.1.9" and baseline["core_epoch"] == BEFORE,
            "Wrong installed predecessor")
    game = Path(baseline["game_root"])
    checks = {game / "bin/x64/Cyberpunk2077.exe": ENGINE_SHA}
    pin(game / "bin/x64/Cyberpunk2077.exe", ENGINE_SHA)
    for group, size in (("core_files", 51), ("companion_files", 1), ("required_files", 26)):
        require(len(baseline[group]) == size, f"Unexpected baseline count for {group}")
        for row in baseline[group]:
            pin(payload_path(game, row["path"]), row["sha256"], row["bytes"])
    companion, = baseline["companion_files"]
    require(companion["path"] == TARGET and companion["sha256"] == BASE_DLL_SHA, "Wrong installed DLL")
    pin(payload_path(Path(baseline["save_root"]), SAVE_FIXTURE["path"]), SAVE_FIXTURE["sha256"], SAVE_FIXTURE["bytes"])
    return checks


def extract_registration_bytes(engine_path, output):
    engine = checked_path(engine_path).read_bytes()
    require(sha256(engine).hexdigest().upper() == ENGINE_SHA, "Unexpected executable for native registration fixture")
    pe, = struct.unpack_from("<I", engine, 0x3C)
    count, = struct.unpack_from("<H", engine, pe + 6)
    optional_size, = struct.unpack_from("<H", engine, pe + 20)
    image_base, = struct.unpack_from("<Q", engine, pe + 48)
    table = pe + 24 + optional_size
    sections = [struct.unpack_from("<4I", engine, table + 40 * index + 8) for index in range(count)]

    def read(rva, size):
        offset, = (raw + rva - start for _, start, length, raw in sections
                   if start <= rva and rva + size <= start + length)
        return engine[offset:offset + size]

    key_builder, allocator = 0x2B2224, 0xEB6B3C
    target, = struct.unpack("<Q", read(0x3040630 + 0xA0, 8))
    require(target == image_base + key_builder, "PhaseContext key builder virtual changed")
    key = read(key_builder, 0x4B)
    require(key[0x13:0x23] == bytes.fromhex("45 89 41 04 8B 88 80 00 00 00 49 8B C1 41 89 09"),
            "Native phase and node output layout changed")
    output.write_bytes(key + read(allocator, 0x5F))
    return output


def run_fixtures(out, registration_bytes):
    live = HERE / "LiveHandoffChecks.cpp"
    retained = PREDECESSOR / "RetainedQuestRestoreChecks.cpp"
    predecessor_source = pin(PREDECESSOR / "source_01/NativeCheckpoint.cpp", PRIOR_SOURCE_SHA)
    baseline = out / "PriorRegistrationChecks.cpp"
    include = '#include "source_01/NativeCheckpoint.cpp"'
    harness = live.read_text(encoding="utf-8")
    require(harness.count(include) == 1, "Registration fixture include anchor drift")
    baseline.write_text(harness.replace(include, f'#include "{predecessor_source.as_posix()}"'), encoding="utf-8")
    names = {"LiveHandoffChecks": (live, ["bcrypt.lib", "user32.lib"]),
             "RetainedQuestRestoreChecks": (retained, []),
             "PriorRegistrationChecks": (baseline, ["bcrypt.lib", "user32.lib"])}
    shutil.copyfile(pin(CONTROL, CONTROL_SHA), out / CONTROL.name)
    commands = [f'call "{VCVARS}" >nul']
    for name, (source, libraries) in names.items():
        write_response(out, name, source, ["/I.", f"/Fe{name}.exe", *libraries])
        commands.append(f"cl.exe @{name}.rsp")
    batch = out / "handoff_checks.cmd"
    batch.write_text("@echo off\n" + "\nif errorlevel 1 exit /b 1\n".join(commands)
                     + "\nif errorlevel 1 exit /b 1\n", encoding="ascii")
    with (out / "handoff_compile.txt").open("wb") as log:
        subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=100, creationflags=subprocess.CREATE_NO_WINDOW)
    counts = {}
    for name in names:
        command = [str(out / f"{name}.exe")]
        if name != "RetainedQuestRestoreChecks":
            command.append(str(registration_bytes))
        if name == "PriorRegistrationChecks":
            command.append("registration-only")
        result = subprocess.run(command, cwd=out, capture_output=True, text=True, timeout=25,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        (out / f"{name}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        if name == "PriorRegistrationChecks":
            failures = [line for line in result.stdout.splitlines() if line.startswith("FAIL ")]
            require(result.returncode == 1 and failures == [
                "FAIL the first native phase registration enrolls before its initializer can notify",
                "FAIL commit publishes the native root notification exactly once",
            ], "The installed predecessor did not reproduce the registration failure")
        else:
            result.check_returncode()
            counts[name] = sum(line.startswith("PASS ") for line in result.stdout.splitlines())
            require(counts[name] == {"LiveHandoffChecks": 33, "RetainedQuestRestoreChecks": 21}[name],
                    f"Unexpected check count for {name}")
    dependencies = {}
    for name in names:
        files = json.loads((out / f"{name}.deps.json").read_bytes())["Data"]
        paths = [checked_path(files["Source"]), *(checked_path(path) for path in files["Includes"])]
        dependencies[name] = {path: digest(path) for path in paths}
    return counts, dependencies


def installer_text(manifest_sha):
    script = pin(PRIOR_STAGE / "deploy_core.ps1", SCRIPT_SHA).read_text(encoding="utf-8-sig")
    for before, after in (
        (TEMPLATE_SHA, manifest_sha),
        (f"PTFR_{BEFORE}_CORE_V1", SCHEMA),
        (f"source_epoch -cne '{BEFORE}'", f"source_epoch -cne '{AFTER}'"),
        ("predecessor_epoch -cne 'RD10_EXECUTION_CHECKPOINT_LIVE_HANDOFF'", f"predecessor_epoch -cne '{BEFORE}'"),
        ("sole v0.1.9 checkpoint DLL", f"sole v{VERSION} checkpoint DLL"),
        ("recovery/ms31_falco_elapsed_01", "recovery/ms31_native_registration_01"),
    ):
        require(script.count(before) == 1, f"Installer anchor drift: {before}")
        script = script.replace(before, after)
    return script


def stage_test(stage, baseline, binary, sources, proofs):
    stage.mkdir()
    # The scanner resolves the pinned project via parent directories. This
    # successor uses the same directory depth as its predecessor.
    provider_scan.HERE = HERE
    proofs.update(verify_providers(stage))
    packaged = payload_path(stage / "files", TARGET)
    packaged.parent.mkdir(parents=True)
    shutil.copyfile(binary, packaged)
    binary_sha = digest(binary)
    pin(packaged, binary_sha, binary.stat().st_size)

    template = load(PRIOR_STAGE / "core_manifest_01.json", TEMPLATE_SHA)
    rows = [{"path": row["path"], "before": row["sha256"], "before_bytes": row["bytes"],
             "after": row["sha256"], "after_bytes": row["bytes"]}
            for row in (*baseline["core_files"], *baseline["companion_files"])]
    changed, = (row for row in rows if row["path"] == TARGET)
    changed.update(after=binary_sha, after_bytes=binary.stat().st_size)
    require(changed["before"] != binary_sha, "Expected a new checkpoint DLL")
    manifest = dict(template, schema=SCHEMA, source_epoch=AFTER, predecessor_epoch=BEFORE, scope=SCOPE,
                    game_root=baseline["game_root"], save_root=baseline["save_root"], package_root=str(stage / "files"),
                    files=rows, changing_paths=[TARGET],
                    required_files=[dict(row, active_only=False) for row in baseline["required_files"]],
                    proofs=[{"path": str(path), "sha256": sha} for path, sha in proofs.items()],
                    compile_inputs={str(path): sha for path, sha in sources.items()})
    for path, sha in proofs.items():
        pin(path, sha)
    manifest_path = stage / "core_manifest_01.json"
    write_json(manifest_path, manifest)
    script = stage / "deploy_core.ps1"
    script.write_text(installer_text(digest(manifest_path)), encoding="utf-8", newline="\n")
    install_fixtures = exercise(stage, manifest)
    fixture_result = stage / "fixture_results.json"
    scope_review = stage / "scope_review.json"
    write_json(scope_review, {
        "scope": SCOPE, "changed_paths": [TARGET], "replaces_sha256": BASE_DLL_SHA,
        "candidate_sha256": binary_sha, "predecessor_installed_manifest_sha256": INSTALLED_SHA,
        "gameplay": "PENDING_GENUINE_MS31_TOWER_AND_RELOAD",
    })
    write_json(stage / "readiness.json", {
        "status": "READY_NOT_INSTALLED", "version": VERSION, "target": TARGET, "sha256": binary_sha,
        "manifest_sha256": digest(manifest_path), "installer_sha256": digest(script),
        "fixture_result": fixture_result.name, "fixture_result_sha256": digest(fixture_result),
        "scope_review": scope_review.name, "scope_review_sha256": digest(scope_review),
        "transaction_actions": len(install_fixtures["actions"]),
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, choices=range(1, 100), required=True)
    args = parser.parse_args()
    baseline = load(INSTALLED, INSTALLED_SHA)
    proofs = verify_baseline(baseline)
    proofs.update({INSTALLED: INSTALLED_SHA})
    for row in baseline["required_files"]:
        if row["path"] in ("red4ext/RED4ext.dll", "bin/x64/cyberpunk2077_addresses.json"):
            proofs[Path(baseline["game_root"]) / row["path"]] = row["sha256"]

    prior = load(PREDECESSOR / "run_04/assessment.json", PRIOR_BUILD_SHA)["inputs"]["NativeCheckpoint"]
    known = {WORKSPACE / path: sha for path, sha in prior.items()}
    source = HERE / "source_01/NativeCheckpoint.cpp"
    successor = {path: digest(path) for path in (source, source.with_name("NativeHandoff.inc"))}
    known.update(successor)

    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    registration_bytes = extract_registration_bytes(Path(baseline["game_root"]) / "bin/x64/Cyberpunk2077.exe",
                                                       out / "native_registration.bin")
    binary = compile_candidate(out, source)
    fixtures, fixture_inputs = run_fixtures(out, registration_bytes)
    checks = run_regressions(out) | fixtures
    inventory = inventory_from_compile(out) | fixture_inputs
    compiled = inventory["NativeCheckpoint"]
    for path in successor:
        require(path in compiled, f"Successor file was not compiled: {path}")
    for path, sha in compiled.items():
        require(known.get(path) == sha, f"Unexpected native compile input: {path}")
    build = out / "assessment.json"
    write_json(build, {
        "version": VERSION, "gameplay": "PENDING", "engine_sha256": ENGINE_SHA,
        "baseline_sha256": INSTALLED_SHA, "checks": checks, "dll_sha256": digest(binary),
        "predecessor_failure_reproduced": True, "native_registration_bytes_sha256": digest(registration_bytes),
        "inputs": {group: {str(path): sha for path, sha in files.items()} for group, files in inventory.items()},
    })
    proofs[build] = digest(build)
    proofs[registration_bytes] = digest(registration_bytes)
    print(f"Passed {sum(checks.values())} offline checks.", flush=True)
    stage_test(HERE / f"staged_{args.attempt:02}", baseline, binary, compiled, proofs)


if __name__ == "__main__":
    main()
