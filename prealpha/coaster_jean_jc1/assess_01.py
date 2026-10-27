"""Pin JC1 source, installation, rollback, collision and save evidence."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent.parent
P = H / "candidate_01"
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


manifest = read(P / "install_manifest_01.json")
receipt = read(W / "recovery/coaster_jean_jc1_01/receipt.json")
fixtures = read(P / "deployment_tests_01.json")
collisions = read(P / "collisions_01.json")
saves = read(P / "save_baseline_01.json")["files"]
assert manifest["status"] == "JC1_CONSOLIDATED_SUCCESSOR_STAGED"
assert receipt["status"] == "JC1_CONSOLIDATED_INSTALLED_LIVE_PENDING"
assert fixtures["status"] == "PASS" and fixtures["action_count"] == 38
assert collisions["collisions"] == [] and collisions["changed_paths"] == 2
assert len(manifest["package_files"]) == 51
for row in manifest["package_files"]:
    assert sha(G / row["path"]) == row["after"], row["path"]
for row in saves:
    assert sha(Path(row["path"])) == row["sha256"], row["path"]
assert len(saves) == 301
proofs = [
    P / "manifest.json",
    P / "install_manifest_01.json",
    P / "deployment_tests_01.json",
    P / "collisions_01.json",
    P / "save_baseline_01.json",
    P / "dist/Post-Tower-Continuation-and-Free-Roam-JC1-unreleased.zip",
    H / "validation_01.json",
    H / "compile_01/result.json",
    H / "build_01.ps1",
    H / "verify_01.py",
    H / "deploy_01.ps1",
    H / "test_deploy_01.py",
    H / "scan_collisions_01.ps1",
    W / "recovery/coaster_jean_jc1_01/receipt.json",
    W / "recovery/coaster_jean_jc1_interrupted_01/receipt.json",
]
result = {
    "status": "JC1_INSTALLED_STATIC_VERIFIED_LIVE_PENDING",
    "package_files": 51,
    "changed_installed_files": 2,
    "archive_resources": 1172,
    "external_mod_archives_scanned": collisions["archives"],
    "external_resource_collisions": 0,
    "deployment_fixture_actions": 38,
    "save_files_unchanged": len(saves),
    "game_launched_by_assistant": False,
    "manual_fact_writes": 0,
    "github_release": False,
    "proofs": [{"path": str(path), "sha256": sha(path)} for path in proofs],
}
out = H / "assessment_01.json"
assert not out.exists(), out
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
(H / "assessment_01.json.sha256").write_text(sha(out) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "assessment_sha256": sha(out), "save_files": len(saves)}))
