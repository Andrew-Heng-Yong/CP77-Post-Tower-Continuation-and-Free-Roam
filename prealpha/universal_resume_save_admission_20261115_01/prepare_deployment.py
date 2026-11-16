"""Stage a fresh, one-DLL deployment using the checkpoint transaction template."""

from hashlib import file_digest, sha256
import json
from pathlib import Path
import re
import shutil


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
PREVIOUS = HERE.parent / "universal_resume_checkpoint_probe_20261114_01"
BUILD = HERE / "run_01"
OLD_MANIFEST = PREVIOUS / "deployment_01/installed_manifest_01.json"
ASSESSMENT = BUILD / "assessment.json"
TARGET = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
SCHEMA = "PTFR_RD10_EXECUTION_CHECKPOINT_SAVE_ADMISSION_CORE_V1"
EPOCH = "RD10_EXECUTION_CHECKPOINT_SAVE_ADMISSION"
ASSESSMENT_SHA = "5628381E92033F72738C9FE00ECA84F17EE7ECA090F53FBFA5DFB9CC1E273173"
PREDECESSOR_SHA = "309183BBB02B5F6A954AB31D6F71B2C9461D29F795193A29F465C1A194F98B2D"
TEMPLATE_SHA = "27FEA0F9214E25F44DEEBEDFA4E304974078598566559DEDF4DE4FBDD23FAFD2"
FIXTURE_SHA = "D1326378290CAEEFA32201BE3C124D7576C78A83483251DE053D5D16BBB6A527"


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def check(path, expected):
    if sha(path) != expected:
        raise ValueError(f"File hash changed: {path}")


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        if isinstance(value, str):
            stream.write(value)
        else:
            json.dump(value, stream, indent=2)
            stream.write("\n")


def replace(contents, old, new):
    if contents.count(old) != 1:
        raise ValueError(f"Deployment template anchor changed: {old}")
    return contents.replace(old, new)


def installer_source(manifest_sha):
    template = PREVIOUS / "deploy_core.ps1"
    check(template, TEMPLATE_SHA)
    source = template.read_text(encoding="utf-8-sig")
    replacements = {
        "# Guard the proposed v0.1.4 checkpoint probe DLL and REDscript replacements.":
            "# Guard the sole v0.1.6 checkpoint DLL replacement.",
        re.search(r"\$PinnedCoreManifestSHA='[0-9A-F]{64}'", source).group():
            f"$PinnedCoreManifestSHA='{manifest_sha}'",
        "PTFR_RD10_EXECUTION_CHECKPOINT_PROBE_CORE_V1": SCHEMA,
        "$manifest.source_epoch -cne 'RD10_EXECUTION_CHECKPOINT_PROBE'":
            f"$manifest.source_epoch -cne '{EPOCH}'",
        "$manifest.predecessor_epoch -cne 'RD10_EXECUTION_CHECKPOINT_DIAGNOSTICS'":
            "$manifest.predecessor_epoch -cne 'RD10_EXECUTION_CHECKPOINT_PROBE'",
        "recovery/resume_checkpoint_probe_01": "recovery/save_admission_01",
        "'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds',": "",
        "$changes.Count -ne 2": "$changes.Count -ne 1",
        "Execution checkpoint probe deployment scope drift": "Native save admission deployment scope drift",
        "if($count -eq 2){Fault 'AfterSecondReplace'}": "",
        next(line for line in source.splitlines() if "Known addon file removal failed" in line):
            " if($null -eq $wanted -or $null -eq $other){throw 'Only an existing DLL may be replaced'}",
        " if($null -eq $other){[IO.File]::Move($stage,$target,$false)}else{[IO.File]::Replace($stage,$target,[NullString]::Value)}":
            " [IO.File]::Replace($stage,$target,[NullString]::Value)",
    }
    for old, new in replacements.items():
        source = replace(source, old, new)
    # CheckPackage verifies every pinned C++ input. The historical REDscript
    # source-tree inventory was specific to the two-file script successor.
    first = source.index("function CheckCompileInventory {")
    last = source.index("function CheckPackage {", first)
    return (source[:first] + source[last:]).replace(
        " CheckCompileInventory\n", " if(-not $fixture -and !$manifest.compile_inputs.Count){throw 'Missing native compile inputs'}\n"
    )


def fixture_source():
    template = PREVIOUS / "fixtures.py"
    check(template, FIXTURE_SHA)
    source = template.read_text(encoding="utf-8-sig")
    source = replace(source, "two-file", "single-DLL")
    source = replace(source, 'HISTORY = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"\n', "")
    source = replace(source, "CHANGES = [HISTORY, DLL]", "CHANGES = [DLL]")
    first = source.index('        "crash_second":')
    last = source.index('        "game_running":', first)
    source = source[:first] + '''        "exception_replace": [("Install", 1, ["-FailurePoint", "AfterFirstReplace"]),
                              ("Verify", "VERIFIED_BEFORE", ["-ExpectedState", "Before"])],
''' + source[last:]
    source = replace(source, "fixture checkpoint probe", "fixture native save guard")
    source = replace(source, 'sha(HERE / "candidate_01/receipt.json")', f'sha(HERE / "run_01/{Path(TARGET).name}")')
    source = replace(source, "universal_resume_checkpoint_runtime_deploy_20261114_01/",
                     "universal_resume_checkpoint_probe_20261114_01/")
    source = replace(source, "PENDING_MANUAL_PROBE_AND_GENUINE_CUTOFF", "PENDING_MS26_SAVE_ADMISSION_SMOKE_TEST")
    source = replace(source, '        assert external.read_bytes() == b"unrelated mod"\n',
                     '        assert external.read_bytes() == b"unrelated mod"\n'
                     '        assert not list((folder / "recovery").rglob("*.dll.tmp"))\n'
                     '        assert not list((folder / "recovery/core/stage").rglob("*.dll"))\n')
    return source


def main():
    check(OLD_MANIFEST, PREDECESSOR_SHA)
    check(ASSESSMENT, ASSESSMENT_SHA)
    predecessor = json.loads(OLD_MANIFEST.read_bytes())
    assessment = json.loads(ASSESSMENT.read_bytes())
    target = assessment["target"]
    old, = predecessor["companion_files"]
    if (predecessor["core_epoch"] != "RD10_EXECUTION_CHECKPOINT_PROBE" or old["path"] != TARGET
            or target["path"] != TARGET or old["sha256"] != target["previous_sha256"]
            or assessment["status"] != "WORKSPACE_NATIVE_SAVE_ADMISSION_BUILD_AND_FIXTURES_PASS"
            or assessment["checks"] != {"SaveAdmissionChecks": 12, "CheckpointChecks": 51, "RegistrationChecks": 15}):
        raise ValueError("Wrong successor or predecessor")
    inventory_file = BUILD / "compile_inputs.json"
    check(inventory_file, assessment["compile_inputs_sha256"])
    inventory = json.loads(inventory_file.read_bytes())
    compile_inputs = {str(WORKSPACE / name): value for name, value in inventory["nativecheckpoint.cpp"].items()}
    if len(compile_inputs) != assessment["compile_input_counts"]["nativecheckpoint.cpp"]:
        raise ValueError("Wrong compile input count")
    for name, value in compile_inputs.items():
        check(Path(name), value)

    binary = BUILD / Path(TARGET).name
    check(binary, target["candidate_sha256"])
    if binary.stat().st_size != target["bytes"]:
        raise ValueError("Wrong candidate size")
    package = HERE / "candidate_01/files"
    staged = package / TARGET
    proofs = [
        {"path": str(OLD_MANIFEST), "sha256": PREDECESSOR_SHA},
        {"path": str(ASSESSMENT), "sha256": ASSESSMENT_SHA},
        {"path": str(inventory_file), "sha256": assessment["compile_inputs_sha256"]},
        {"path": str(Path(predecessor["game_root"]) / "red4ext/RED4ext.dll"),
         "sha256": "58DDFE43766AA91249D11671B55A8323D5EC017F816D847AFFE4B6201DCD0709"},
    ]
    for row in proofs:
        check(Path(row["path"]), row["sha256"])
    managed = [
        {"path": row["path"], "before": row["sha256"], "before_bytes": row["bytes"],
         "after": row["sha256"], "after_bytes": row["bytes"]}
        for row in [*predecessor["core_files"], old]
    ]
    managed[-1].update(after=target["candidate_sha256"], after_bytes=target["bytes"])
    manifest = {
        "schema": SCHEMA, "component": "Core", "source_epoch": EPOCH,
        "predecessor_epoch": predecessor["core_epoch"], "scope": "Install checkpoint v0.1.6 native save admission.",
        "game_root": predecessor["game_root"], "save_root": predecessor["save_root"], "package_root": str(package),
        "process_names": ["Cyberpunk2077", "REDlauncher", "REDprelauncher"],
        "files": managed, "changing_paths": [TARGET],
        "required_files": [dict(row, active_only=False) for row in predecessor["required_files"]],
        "protected_saves": [], "working_save_files": [], "zip": "", "zip_sha256": "",
        "proofs": proofs, "compile_inputs": compile_inputs,
    }
    if len(managed) != 52 or len(manifest["required_files"]) != 26:
        raise ValueError("Wrong installed inventory")
    manifest_path = HERE / "core_manifest_01.json"
    manifest_text = json.dumps(manifest, indent=2) + "\n"
    manifest_sha = sha256(manifest_text.encode("utf-8")).hexdigest().upper()
    installer = installer_source(manifest_sha)
    fixtures = fixture_source()
    staged.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(binary, staged)
    check(staged, target["candidate_sha256"])
    write(manifest_path, manifest_text)
    write(HERE / "deploy_core.ps1", installer)
    write(HERE / "fixtures.py", fixtures)
    print(f"Staged {target['candidate_sha256']} for one DLL replacement. Manifest {manifest_sha}.")


if __name__ == "__main__":
    main()
