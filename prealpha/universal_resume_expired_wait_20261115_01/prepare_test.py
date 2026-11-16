"""Build and stage the MS31 successor without touching the live installation."""

import argparse
from pathlib import Path
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "universal_resume_live_candidate_20261115_01"
sys.path.insert(0, str(PRIOR))
from build_live import compile_candidate, inventory_from_compile, run_regressions, write_response
from candidate_common import TARGET, VCVARS, WORKSPACE, digest, load, payload_path, pin, require, write_json
from fixtures import exercise
from verify_providers import verify as verify_providers
import verify_providers as provider_scan


INSTALLED = PRIOR / "staged_01/deployment_01/installed_manifest_01.json"
INSTALLED_SHA = "CD3646E15634C649F1547D38AA5F757195461BF4C6A6E1D175D1ED41867F59F7"
BEFORE = "RD10_EXECUTION_CHECKPOINT_LIVE_HANDOFF"
AFTER = "RD10_EXECUTION_CHECKPOINT_FALCO_ELAPSED"
SCHEMA = f"PTFR_{AFTER}_CORE_V1"
SCOPE = "Install checkpoint v0.1.9 for the genuine MS31 Over the Edge handoff with native wait expiry."
CONTROL = HERE.parent / "universal_resume_live_runtime_20261115_01/run_06/control_input.hpp"
CONTROL_SHA = "7F548CBAB59A7B76B8FE14C7AFBCF127469F6D9B08D3EAF2E775627C1B272E60"
BASE_DLL_SHA = "98840F6F4AC2BAE2FC9A8020D66F6D7DD70EB93FB49AB2BA562AFA50CFFC3AB9"
ENGINE_SHA = "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4"
PRIOR_STAGE = PRIOR / "staged_01"
TEMPLATE_SHA = "30A84D9C9EE2D3602C11D07D55A0A4142F713A0525670E05F4E813EA8F99324B"
SCRIPT_SHA = "AC3C04060C3502EA646E3E72905F6A20DBA6FC84C0194AED075664D15CBACEDC"
PRIOR_INPUTS_SHA = "7E519A0D297560F830A1F13ACB4570D38D94EE0AEA9BE232FD5786FEAA7F6C08"


def verify_baseline(baseline):
    require(baseline["checkpoint_version"] == "0.1.8" and baseline["core_epoch"] == BEFORE,
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
    return checks


def run_fixtures(out):
    names = {"LiveHandoffChecks": (28, ["bcrypt.lib", "user32.lib"]),
             "RetainedQuestRestoreChecks": (21, [])}
    shutil.copyfile(pin(CONTROL, CONTROL_SHA), out / CONTROL.name)
    commands = [f'call "{VCVARS}" >nul']
    for name, (_, libraries) in names.items():
        write_response(out, name, HERE / f"{name}.cpp", ["/I.", f"/Fe{name}.exe", *libraries])
        commands.append(f"cl.exe @{name}.rsp")
    batch = out / "handoff_checks.cmd"
    batch.write_text("@echo off\n" + "\nif errorlevel 1 exit /b 1\n".join(commands)
                     + "\nif errorlevel 1 exit /b 1\n", encoding="ascii")
    with (out / "handoff_compile.txt").open("wb") as log:
        subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=100, creationflags=subprocess.CREATE_NO_WINDOW)
    counts = {}
    for name, (expected, _) in names.items():
        result = subprocess.run([str(out / f"{name}.exe")], cwd=out, capture_output=True, text=True, timeout=25,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        (out / f"{name}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
        result.check_returncode()
        counts[name] = sum(line.startswith("PASS ") for line in result.stdout.splitlines())
        require(counts[name] == expected, f"Unexpected check count for {name}")
    return counts


def installer_text(manifest_sha):
    script = pin(PRIOR_STAGE / "deploy_core.ps1", SCRIPT_SHA).read_text(encoding="utf-8-sig")
    for before, after in (
        (TEMPLATE_SHA, manifest_sha),
        (f"PTFR_{BEFORE}_CORE_V1", SCHEMA),
        (f"source_epoch -cne '{BEFORE}'", f"source_epoch -cne '{AFTER}'"),
        ("predecessor_epoch -cne 'RD10_EXECUTION_CHECKPOINT_SAVE_SESSION'", f"predecessor_epoch -cne '{BEFORE}'"),
        ("sole v0.1.8 checkpoint DLL", "sole v0.1.9 checkpoint DLL"),
        ("recovery/ms31_live_handoff_01", "recovery/ms31_falco_elapsed_01"),
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
        "status": "READY_NOT_INSTALLED", "version": "0.1.9", "target": TARGET, "sha256": binary_sha,
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

    prior = load(PRIOR / "run_06/compile_inputs.json", PRIOR_INPUTS_SHA)["NativeCheckpoint"]
    known = {WORKSPACE / path: sha for path, sha in prior.items()}
    source = HERE / "source_01/NativeCheckpoint.cpp"
    successor = {path: digest(path) for path in (source, source.with_name("NativeHandoff.inc"),
                                                source.with_name("RetainedQuestRestore.hpp"))}
    known.update(successor)

    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    binary = compile_candidate(out, source)
    checks = run_regressions(out) | run_fixtures(out)
    inventory = inventory_from_compile(out)
    compiled = inventory["NativeCheckpoint"]
    for path in successor:
        require(path in compiled, f"Successor file was not compiled: {path}")
    for path, sha in compiled.items():
        require(known.get(path) == sha, f"Unexpected native compile input: {path}")
    build = out / "assessment.json"
    write_json(build, {
        "version": "0.1.9", "gameplay": "PENDING", "engine_sha256": ENGINE_SHA,
        "baseline_sha256": INSTALLED_SHA, "checks": checks, "dll_sha256": digest(binary),
        "inputs": {group: {str(path): sha for path, sha in files.items()} for group, files in inventory.items()},
    })
    proofs[build] = digest(build)
    print(f"Passed {sum(checks.values())} offline checks.", flush=True)
    stage_test(HERE / f"staged_{args.attempt:02}", baseline, binary, compiled, proofs)


if __name__ == "__main__":
    main()
