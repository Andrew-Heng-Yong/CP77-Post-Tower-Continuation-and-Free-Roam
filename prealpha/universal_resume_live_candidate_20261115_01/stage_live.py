"""Prepare and exercise a local, exact one-DLL installer for the MS31 test."""

import argparse
from pathlib import Path
import re
import shutil

from build_live import READY_BUILD, read_binary, read_integration
from candidate_common import (ADDRESS_TABLE_SHA, ENGINE_SHA, EPOCH, HERE, INSTALLED, INSTALLED_SHA,
                              INSTALLER, INSTALLER_SHA, LOADER_SHA, OLD_DLL_SHA, PRIOR_EPOCH, REGRESSION_COUNTS,
                              RUNTIME_SOURCE, SAVE_FIXTURE, SCHEMA, TARGET, TEMPLATE, TEMPLATE_SHA, VERSION,
                              digest, load, payload_path, pin, read_inventory, require, verify_installed,
                              verify_inventory, workspace_file, write_json)
from fixtures import exercise
from verify_providers import verify as verify_providers


SCOPE = "Install checkpoint v0.1.8 for the genuine MS31 Over the Edge handoff test."


def read_build(path, sha):
    path = workspace_file(path)
    require(path.parent.parent == HERE and re.fullmatch(r"run_\d{2}", path.parent.name)
            and path.name == "assessment.json", "Build assessment must be this candidate's exact output")
    build = load(path, sha)
    require(build["status"] == READY_BUILD and build["version"] == VERSION
            and build["checks"] == REGRESSION_COUNTS and build["game_runtime_exercised"] is False
            and build["installed_manifest_sha256"] == INSTALLED_SHA and build["engine_sha256"] == ENGINE_SHA,
            "Compile-only or out-of-scope build cannot be staged")
    receipt = build["source"]
    require(workspace_file(receipt["path"]) == RUNTIME_SOURCE, "Wrong production source in assessment")
    pin(RUNTIME_SOURCE, receipt["sha256"])
    integration = build["integration"]
    proof = workspace_file(integration["path"])
    _, total = read_integration(proof, integration["sha256"], receipt["sha256"])
    require(total == integration["checks_passed"], "Integration fixture count drift")
    dependency_file = path.parent / "compile_inputs.json"
    inventory = read_inventory(dependency_file, build["compile_inputs_sha256"])
    verify_inventory(inventory)
    native = inventory["NativeCheckpoint"]
    require(native.get(RUNTIME_SOURCE) == receipt["sha256"], "Compile inventory missed the bound runtime")
    target = build["target"]
    require(target["path"] == TARGET and target["previous_sha256"] == OLD_DLL_SHA
            and target["candidate_sha256"] != OLD_DLL_SHA, "Wrong successor write-set")
    dll = pin(path.parent / Path(TARGET).name, target["candidate_sha256"], target["bytes"])
    exports = pin(path.parent / "exports.txt", build["exports_sha256"])
    read_binary(dll, exports)
    proofs = {path: sha.upper(), proof: integration["sha256"], dependency_file: build["compile_inputs_sha256"],
              exports: build["exports_sha256"]}
    return build, dll, native, proofs


def installer_text(manifest_sha, template):
    text = pin(INSTALLER, INSTALLER_SHA).read_text(encoding="utf-8-sig")
    changes = (
        (TEMPLATE_SHA, manifest_sha),
        (template["schema"], SCHEMA),
        (f"$manifest.source_epoch -cne '{PRIOR_EPOCH}'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        (f"$manifest.predecessor_epoch -cne '{template['predecessor_epoch']}'",
         f"$manifest.predecessor_epoch -cne '{PRIOR_EPOCH}'"),
        ("# Guard the sole v0.1.7 checkpoint DLL replacement.", "# Guard the sole v0.1.8 checkpoint DLL replacement."),
        ("Native save admission deployment scope drift", "Native handoff deployment scope drift"),
        ("(Split-Path $worker -Parent) 'quest_restoration_qr9/worker_a'",
         "(Split-Path (Split-Path $worker -Parent) -Parent) 'quest_restoration_qr9/worker_a'"),
        ("recovery/save_session_01", "recovery/ms31_live_handoff_01"),
    )
    for before, after in changes:
        require(text.count(before) == 1, f"Installer anchor drift: {before}")
        text = text.replace(before, after)
    return text


def make_manifest(stage, template, baseline, target=None, native=None, proofs=None):
    group = (*baseline["core_files"], *baseline["companion_files"])
    rows = [{"path": row["path"], "before": row["sha256"], "before_bytes": row["bytes"],
             "after": row["sha256"], "after_bytes": row["bytes"]} for row in group]
    if target:
        changed, = (row for row in rows if row["path"] == TARGET)
        changed.update(after=target["candidate_sha256"], after_bytes=target["bytes"])
    game = Path(baseline["game_root"])
    proofs = (proofs or {}) | {INSTALLED: INSTALLED_SHA, game / "red4ext/RED4ext.dll": LOADER_SHA,
                               game / "bin/x64/Cyberpunk2077.exe": ENGINE_SHA,
                               game / "bin/x64/cyberpunk2077_addresses.json": ADDRESS_TABLE_SHA}
    for path, expected in proofs.items():
        pin(path, expected)
    required = [dict(row, active_only=False) for row in baseline["required_files"]]
    return dict(template, schema=SCHEMA, source_epoch=EPOCH, predecessor_epoch=PRIOR_EPOCH, scope=SCOPE,
                game_root=baseline["game_root"], save_root=baseline["save_root"], package_root=str(stage / "files"),
                files=rows, changing_paths=[TARGET], required_files=required, working_save_files=[SAVE_FIXTURE],
                proofs=[{"path": str(path), "sha256": sha} for path, sha in proofs.items()],
                compile_inputs={str(path): sha for path, sha in (native or {}).items()})


def stage_build(stage, template, baseline, build_path, build_sha):
    build, dll, native, proofs = read_build(build_path, build_sha)
    stage.mkdir()
    proofs.update(verify_providers(stage))
    manifest = make_manifest(stage, template, baseline, build["target"], native, proofs)
    receipt = stage / "core_manifest_01.json"
    write_json(receipt, manifest)
    manifest_sha = digest(receipt)
    installer = stage / "deploy_core.ps1"
    installer.write_text(installer_text(manifest_sha, template), encoding="utf-8", newline="\n")
    installer_sha = digest(installer)
    package = stage / "files"
    actual = payload_path(package, TARGET)
    actual.parent.mkdir(parents=True)
    shutil.copyfile(dll, actual)
    pin(actual, build["target"]["candidate_sha256"], build["target"]["bytes"])
    require([p.relative_to(package).as_posix() for p in package.rglob("*") if p.is_file()] == [TARGET],
            "Staged package is not exactly the checkpoint DLL")
    exercises = exercise(stage, manifest)
    pin(receipt, manifest_sha)
    pin(installer, installer_sha)
    scope = stage / "scope_review.json"
    write_json(scope, {"scope": SCOPE, "changed_paths": [TARGET], "replaces_sha256": OLD_DLL_SHA,
                       "candidate_sha256": build["target"]["candidate_sha256"],
                       "predecessor_installed_manifest_sha256": INSTALLED_SHA,
                       "build_assessment_sha256": build_sha.upper(), "regressions": build["checks"],
                       "integration": build["integration"], "transaction_actions": len(exercises["actions"]),
                       "gameplay": "PENDING_GENUINE_MS31_TOWER_AND_RELOAD"})
    fixtures = stage / "fixture_results.json"
    write_json(stage / "readiness.json", {"status": "READY_NOT_INSTALLED", "manifest_sha256": manifest_sha,
                                          "installer_sha256": installer_sha, "fixture_result": fixtures.name,
                                          "fixture_result_sha256": digest(fixtures), "scope_review": scope.name,
                                          "scope_review_sha256": digest(scope)})
    print(f"Staged {VERSION} at {stage}. Exact installer manifest {manifest_sha}.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100))
    parser.add_argument("--build", type=Path)
    parser.add_argument("--build-sha")
    args = parser.parse_args()
    require(bool(args.build) == bool(args.build_sha), "Supply the build assessment and its SHA together")
    baseline = verify_installed()
    template = load(TEMPLATE, TEMPLATE_SHA)
    if args.build:
        stage_build(HERE / f"staged_{args.attempt:02}", template, baseline, args.build, args.build_sha)
        return
    stage = HERE / f"fixture_{args.attempt:02}"
    stage.mkdir()
    (stage / "deploy_core.ps1").write_text(installer_text("FIXTURE_ONLY", template), encoding="utf-8", newline="\n")
    exercise(stage, make_manifest(stage, template, baseline))


if __name__ == "__main__":
    main()
