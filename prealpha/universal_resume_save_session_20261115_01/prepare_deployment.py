"""Stage the authorized one-DLL successor without writing into the game."""

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
PRIOR = HERE.parent / "universal_resume_save_admission_20261115_01"
BUILD = HERE / "run_01"
PRIOR_INSTALLED = PRIOR / "deployment_01/installed_manifest_01.json"
ASSESSMENT = BUILD / "assessment.json"
TARGET = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
PRIOR_EPOCH = "RD10_EXECUTION_CHECKPOINT_SAVE_ADMISSION"
EPOCH = "RD10_EXECUTION_CHECKPOINT_SAVE_SESSION"
PRIOR_MANIFEST_SHA = "304A33635419442922944A3DADD75313C0C0902BB0052421F1D7ECC83FDF4352"
PRIOR_INSTALLED_SHA = "7971F2E6AE7AF81E3B276FCBDDDD2DD0C25DB42069FAEE30000CE6DE92B16636"
ASSESSMENT_SHA = "747177A2460DE99E204F1BD268671BC2BC884AD1A6899DEB202A35E7986DC837"

sys.path.insert(0, str(PRIOR))
from prepare_deployment import check, replace, write


def main():
    template_path = PRIOR / "core_manifest_01.json"
    check(template_path, PRIOR_MANIFEST_SHA)
    check(PRIOR_INSTALLED, PRIOR_INSTALLED_SHA)
    check(ASSESSMENT, ASSESSMENT_SHA)
    template = json.loads(template_path.read_bytes())
    baseline = json.loads(PRIOR_INSTALLED.read_bytes())
    assessment = json.loads(ASSESSMENT.read_bytes())
    target = assessment["target"]
    old, = baseline["companion_files"]
    if (baseline["core_epoch"] != PRIOR_EPOCH or old["path"] != TARGET or target["path"] != TARGET
            or old["sha256"] != target["previous_sha256"] or template["changing_paths"] != [TARGET]
            or assessment["status"] != "WORKSPACE_SESSION_SAVE_ADMISSION_BUILD_AND_FIXTURES_PASS"
            or assessment["checks"] != {"SaveAdmissionChecks": 12, "CheckpointChecks": 60, "RegistrationChecks": 15}):
        raise ValueError("Wrong installed baseline or candidate")
    root = Path(baseline["game_root"])
    inventory_file = BUILD / "compile_inputs.json"
    check(inventory_file, assessment["compile_inputs_sha256"])
    inventory = json.loads(inventory_file.read_bytes())["nativecheckpoint.cpp"]
    if len(inventory) != assessment["compile_input_counts"]["nativecheckpoint.cpp"]:
        raise ValueError("Wrong compile input count")
    compile_inputs = {str(WORKSPACE / name): value for name, value in inventory.items()}
    for name, value in compile_inputs.items():
        check(Path(name), value)

    binary = BUILD / Path(TARGET).name
    check(binary, target["candidate_sha256"])
    if binary.stat().st_size != target["bytes"]:
        raise ValueError("Wrong candidate size")
    package = HERE / "candidate_01/files"
    staged = package / TARGET
    managed = [
        {"path": row["path"], "before": row["sha256"], "before_bytes": row["bytes"],
         "after": row["sha256"], "after_bytes": row["bytes"]}
        for row in [*baseline["core_files"], old]
    ]
    managed[-1].update(after=target["candidate_sha256"], after_bytes=target["bytes"])
    proofs = [
        {"path": str(PRIOR_INSTALLED), "sha256": PRIOR_INSTALLED_SHA},
        {"path": str(ASSESSMENT), "sha256": ASSESSMENT_SHA},
        {"path": str(inventory_file), "sha256": assessment["compile_inputs_sha256"]},
        {"path": str(root / "red4ext/RED4ext.dll"),
         "sha256": "58DDFE43766AA91249D11671B55A8323D5EC017F816D847AFFE4B6201DCD0709"},
        {"path": str(root / "bin/x64/cyberpunk2077_addresses.json"),
         "sha256": assessment["engine"]["session"]["address_table_sha256"]},
    ]
    for proof in proofs:
        check(Path(proof["path"]), proof["sha256"])
    required = [dict(row, active_only=False) for row in baseline["required_files"]]
    if len(managed) != 52 or len(required) != 26:
        raise ValueError("Wrong installed inventory")
    schema = f"PTFR_{EPOCH}_CORE_V1"
    manifest = dict(template, schema=schema, source_epoch=EPOCH, predecessor_epoch=PRIOR_EPOCH,
                    scope="Install checkpoint v0.1.7 with the corrected save-session probe.",
                    game_root=baseline["game_root"], save_root=baseline["save_root"], package_root=str(package),
                    files=managed, required_files=required, proofs=proofs, compile_inputs=compile_inputs)
    body = json.dumps(manifest, indent=2) + "\n"
    manifest_sha = sha256(body.encode("utf-8")).hexdigest().upper()

    installer_path = PRIOR / "deploy_core.ps1"
    check(installer_path, "E24095A1F9CCE530701D78B9FEBBAD874D07FCABBEA94355D8630A92B3BA04C0")
    installer = installer_path.read_text(encoding="utf-8-sig")
    for before, after in (
        (PRIOR_MANIFEST_SHA, manifest_sha),
        (template["schema"], schema),
        (f"$manifest.source_epoch -cne '{PRIOR_EPOCH}'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        (f"$manifest.predecessor_epoch -cne '{template['predecessor_epoch']}'",
         f"$manifest.predecessor_epoch -cne '{PRIOR_EPOCH}'"),
        ("# Guard the sole v0.1.6 checkpoint DLL replacement.", "# Guard the sole v0.1.7 checkpoint DLL replacement."),
        ("recovery/save_admission_01", "recovery/save_session_01"),
    ):
        installer = replace(installer, before, after)
    fixtures_path = PRIOR / "fixtures.py"
    check(fixtures_path, "9A09209625B572C1CED4E6FAA8EE986C5302CE13D379A62CCA4DC75D413A54A8")
    fixtures = replace(fixtures_path.read_text(encoding="utf-8-sig"),
                       "universal_resume_checkpoint_probe_20261114_01/deployment_01/installed_manifest_01.json",
                       f"{PRIOR.name}/deployment_01/installed_manifest_01.json")
    fixtures = replace(fixtures, "PENDING_MS26_SAVE_ADMISSION_SMOKE_TEST", "PENDING_MS30_SAVE_SESSION_SMOKE_TEST")

    staged.parent.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(binary, staged)
    check(staged, target["candidate_sha256"])
    write(HERE / "core_manifest_01.json", body)
    write(HERE / "deploy_core.ps1", installer)
    write(HERE / "fixtures.py", fixtures)
    deployment = HERE / "deployment_01"
    deployment.mkdir()
    write(deployment / "authorization_01.json", {
        "user_reply": "install now", "authorized_action": "Install checkpoint v0.1.7",
        "paths": [TARGET], "candidate_sha256": target["candidate_sha256"], "manifest_sha256": manifest_sha,
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
    })
    print(f"Staged v0.1.7 for one DLL replacement. Manifest {manifest_sha}.")


if __name__ == "__main__":
    main()
