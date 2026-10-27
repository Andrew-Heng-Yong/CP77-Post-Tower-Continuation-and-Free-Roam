"""Exercise additive install, rollback and interruption recovery in workspace fixtures."""
import hashlib
import json
import subprocess
from pathlib import Path

H = Path(__file__).resolve().parent
P = H / "probe_04"
ROOT = P / "deploy_fixtures_01"
assert not ROOT.exists(), "Preserve fixture evidence; use a successor"
ROOT.mkdir(parents=True)
INSTALLER = H / "deploy_probe_04.ps1"
MANIFEST = json.loads((P / "manifest_01.json").read_text(encoding="utf-8"))


def call(root, action, fail=""):
    command = ["pwsh", "-NoProfile", "-File", str(INSTALLER), "-Action", action,
               "-FixtureRoot", str(root)]
    if fail:
        command += ["-TestFailPoint", fail]
    return subprocess.run(command, capture_output=True, text=True, timeout=60)


def absent(root):
    assert all(not (root / "game" / row["path"]).exists() for row in MANIFEST["files"])
    assert all(not (root / "game" / (row["path"] + ".ptfr-ww1-stage")).exists() for row in MANIFEST["files"])


rows = []
for point in ("AfterBackup", "AfterStage", "BeforeFirstMove", "AfterFirstMove", "AfterAllMoves", "BeforeReceipt"):
    root = ROOT / point
    root.mkdir()
    assert call(root, "Validate").returncode == 0, point
    result = call(root, "Install", point)
    assert result.returncode != 0, point
    absent(root)
    failure = json.loads((root / "backup/failed_receipt.json").read_text())
    assert failure["status"] == "FAILED_ROLLED_BACK" and not failure["remaining"], point
    rows.append({"point": point, "status": "ROLLBACK_PASS"})

root = ROOT / "success"
root.mkdir()
for action in ("Validate", "Install", "Verify", "ValidateRollback", "Rollback"):
    result = call(root, action)
    assert result.returncode == 0, (action, result.stdout, result.stderr)
absent(root)
assert json.loads((root / "backup/rollback_receipt.json").read_text())["status"] == "ROLLED_BACK"

preexisting = ROOT / "preexisting"
preexisting.mkdir()
existing = preexisting / "game" / MANIFEST["files"][0]["path"]
existing.parent.mkdir(parents=True)
existing.write_bytes(b"independent existing file")
result = call(preexisting, "Validate")
assert result.returncode != 0 and existing.read_bytes() == b"independent existing file"
assert not (preexisting / "backup").exists()

proof = {"status": "PASS", "interruption_points": 6, "interruptions": rows,
         "success_install_verify_rollback": True, "preexisting_target_refused": True,
         "installed_writes": 0, "fixture_root": str(ROOT),
         "installer_sha256": hashlib.sha256(INSTALLER.read_bytes()).hexdigest().upper()}
target = P / "deployment_tests_01.json"
assert not target.exists()
target.write_text(json.dumps(proof, indent=2)+"\n", encoding="utf-8")
print(json.dumps(proof, indent=2))
