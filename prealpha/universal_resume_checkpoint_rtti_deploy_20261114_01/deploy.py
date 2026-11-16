"""Stage and verify the authorized checkpoint registration repair installation."""

import argparse
from hashlib import file_digest, sha256
import importlib.util
import json
from pathlib import Path
import shutil

HERE = Path(__file__).resolve().parent
TRANSACTION = HERE.parent / "universal_resume_checkpoint_deploy_20261114_01"
FIX = HERE.parent / "universal_resume_checkpoint_rtti_20261114_01"
RD10 = HERE.parent / "resume_dispatcher_rd10_kirk_20261113_01/deployment_01/installed_manifest_01.json"
RD10_SHA = "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8"
GUARD_SHA = "C6C20D72E1D21FDDA1A56C7C5043D9C614F788C93CA63D67EFB1F85143EAF906"
FIXTURE_DRIVER_SHA = "42824D3BDCA9E391AA18EDE416E14CDC430396D00E204071A2E0AA9532734613"
OLD_MANIFEST_SHA = "6C0BE1797CE0A165677CF3353E273FD05E8FB24386A1FEF2BBBCCCDB59EAD83B"
CANDIDATE = FIX / "candidate_02/receipt.json"
CANDIDATE_SHA = "84EA250DAFDBBFF10AABC0C6947B0FFF7C943D97D71BF6593524CD80A7A0005D"
MANIFEST = HERE / "core_manifest_01.json"
INSTALLER = HERE / "deploy_core.ps1"
DEPLOYMENT = HERE / "deployment_01"
RECOVERY = HERE / "recovery/resume_checkpoint_rtti_01"
EPOCH = "RD10_EXECUTION_CHECKPOINT_RTTI_REPAIR"
SCHEMA = "PTFR_RD10_EXECUTION_CHECKPOINT_RTTI_REPAIR_CORE_V1"
DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
REDS = "r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
LUA = "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua"
CHANGES = {DLL, REDS, LUA}


def sha(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest().upper()


def pinned(path, digest):
    assert sha(path) == digest, path
    return path


def read(path):
    return json.loads(path.read_bytes())


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(data, indent=2) + "\n")


def read_journal(path):
    envelope = read(path)
    assert sha256(envelope["payload_json"].encode()).hexdigest().upper() == envelope["payload_sha256"]
    return json.loads(envelope["payload_json"])


def prepare():
    baseline = read(pinned(RD10, RD10_SHA))
    original_manifest = pinned(TRANSACTION / "core_manifest_01.json", OLD_MANIFEST_SHA)
    manifest = read(original_manifest)
    prior_rollback = TRANSACTION / "recovery/resume_checkpoint_01/journal.json"
    rollback = read_journal(prior_rollback)
    assert rollback["manifest_sha256"] == OLD_MANIFEST_SHA and rollback["state"] == "ROLLED_BACK_VERIFIED"
    assert rollback["save_writes"] == rollback["game_launches"] == 0
    assert manifest["game_root"] == baseline["game_root"] and manifest["save_root"] == baseline["save_root"]
    assert manifest["predecessor_epoch"] == baseline["core_epoch"] == "RD10_MEET_KIRK_CONTENT_LOCK"
    assert manifest["required_files"] == baseline["required_files"] and len(manifest["required_files"]) == 26

    selected = read(pinned(CANDIDATE, CANDIDATE_SHA))
    evidence = read(FIX / "checkpoint.json")
    compile_receipt = pinned(FIX / evidence["compile"], selected["compile_receipt_sha256"])
    test_receipt = pinned(FIX / evidence["checks"], selected["checks_sha256"])
    build_receipt = pinned(FIX / evidence["native_build"], selected["build_receipt_sha256"])
    tests = read(test_receipt)
    assert len(tests["registration_checks"]) == 23 and len(tests["checkpoint_checks"]) == 41
    assert len(tests["native_donor_checks"]["stock_labels"]) == 6
    compile_data = read(compile_receipt)
    assert compile_data["source_count"] == 148 and compile_data["replaced_source"] == {REDS: selected["files"][REDS]}
    assert compile_data["script_contract"] == tests["script_contract"]
    assert set(selected["files"]) == CHANGES and selected["archive_sha256"] == baseline["archive_sha256"]
    native_hash, = (row["sha256"] for row in read(build_receipt) if row["name"] == Path(DLL).name)
    assert selected["files"][DLL] == native_hash
    package = CANDIDATE.parent / "files"
    assert {path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file()} == CHANGES
    payload = {rel: pinned(package / rel, digest) for rel, digest in selected["files"].items()}

    game = Path(baseline["game_root"])
    current = {row["path"]: row for row in baseline["core_files"]}
    assert len(current) == 51
    for row in manifest["files"]:
        rel = row["path"]
        if rel == DLL:
            assert row["before"] is None and not (game / rel).exists() and native_hash != row["after"]
        else:
            old = current[rel]
            assert row["before"] == old["sha256"] and row["before_bytes"] == old["bytes"]
            assert pinned(game / rel, old["sha256"]).stat().st_size == old["bytes"]
        if rel in CHANGES:
            row["after"] = selected["files"][rel]
            row["after_bytes"] = payload[rel].stat().st_size
        else:
            assert row["before"] == row["after"] and row["before_bytes"] == row["after_bytes"]
    assert set(manifest["changing_paths"]) == CHANGES
    for row in manifest["required_files"]:
        assert pinned(game / row["path"], row["sha256"]).stat().st_size == row["bytes"]
    compiler = {str(pinned(game / rel, digest)): digest for rel, digest in compile_data["compiler_inputs"].items()}
    compiler[str(pinned(game / "bin/x64/Cyberpunk2077.exe", tests["native_donor_checks"]["exe_sha256"]))] = (
        tests["native_donor_checks"]["exe_sha256"])
    compiler[str(pinned(game / "red4ext/RED4ext.dll", tests["native_donor_checks"]["red4ext_sha256"]))] = (
        tests["native_donor_checks"]["red4ext_sha256"])

    DEPLOYMENT.mkdir(exist_ok=False)
    authorization = DEPLOYMENT / "user_authorization.json"
    write(authorization, {"request": "install the repair and i will do the test for step 2",
                          "candidate_sha256": CANDIDATE_SHA, "paths": sorted(CHANGES)})
    proofs = [RD10, original_manifest, prior_rollback, CANDIDATE, compile_receipt, test_receipt, build_receipt, authorization]
    manifest.update(
        schema=SCHEMA, source_epoch=EPOCH, package_root=str(package),
        scope="Install the verified checkpoint registration repair so the user can run the Step 2 Tower test.",
        proofs=[{"path": str(path), "sha256": sha(path)} for path in proofs], compile_inputs=compiler)
    write(MANIFEST, manifest)

    guard = pinned(TRANSACTION / "deploy_core.ps1", GUARD_SHA).read_text(encoding="utf-8-sig")
    edits = [
        (OLD_MANIFEST_SHA, sha(MANIFEST)),
        ("PTFR_RD10_EXECUTION_CHECKPOINT_CORE_V1", SCHEMA),
        ("$manifest.source_epoch -cne 'RD10_EXECUTION_CHECKPOINT'", f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("resume_checkpoint_01", "resume_checkpoint_rtti_01"),
        ("# Install checkpoint candidate 02 with the authorized two replacements and private plugin.",
         "# Install the checkpoint registration repair with the authorized two replacements and private plugin."),
    ]
    for before, after in edits:
        assert guard.count(before) == 1, before
        guard = guard.replace(before, after, 1)
    with INSTALLER.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(guard)
    print("Prepared the registration repair against the verified RD10 rollback.")


def driver():
    source = pinned(TRANSACTION / "deploy.py", FIXTURE_DRIVER_SHA)
    spec = importlib.util.spec_from_file_location("checkpoint_transaction_checks", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for key, value in {
        "HERE": HERE, "BASELINE": RD10, "BASELINE_SHA": RD10_SHA, "CANDIDATE": CANDIDATE,
        "CANDIDATE_SHA": CANDIDATE_SHA, "MANIFEST": MANIFEST, "INSTALLER": INSTALLER,
        "DEPLOYMENT": DEPLOYMENT, "RECOVERY": RECOVERY, "EPOCH": EPOCH,
    }.items():
        setattr(module, key, value)
    return module


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "fixtures", "record"))
    parser.add_argument("--powershell", default=shutil.which("pwsh") or "pwsh")
    options = parser.parse_args()
    if options.action == "prepare":
        prepare()
    elif options.action == "fixtures":
        driver().fixtures(options.powershell)
    else:
        driver().record()
