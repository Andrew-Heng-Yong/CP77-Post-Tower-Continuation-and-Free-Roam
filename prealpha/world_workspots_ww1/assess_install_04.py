"""Pin installed probe state without launching the game or touching saves."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
W = H.parent.parent
P = H / "probe_04"
G = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
R = W / "recovery/world_workspots_ww1_probe_04_01"


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


manifest = read(P / "manifest_01.json")
zip_receipt = read(P / "zip_receipt_01.json")
install = read(R / "receipt.json")
tests = read(P / "deployment_tests_01.json")
saves = read(P / "save_comparison_01.json")
jc1 = read(W / "prealpha/coaster_jean_jc1/candidate_01/manifest.json")
compile_result = read(P / "compile_01/result.json")
collision = read(P / "collisions_01.json")
assert install["status"] == "INSTALLED" and install["zip_sha256"] == zip_receipt["sha256"]
assert install["manifest_sha256"] == sha(P / "manifest_01.json")
assert sha(R / "probe.zip") == sha(P / "Post-Tower-Continuation-and-Free-Roam-WW1-Scav-probe-unreleased.zip")
assert tests["status"] == "PASS" and tests["interruption_points"] == 6
assert saves["status"] == "UNCHANGED" and saves["before_count"] == saves["after_count"] == 301
assert compile_result["status"] == "PASS" and compile_result["source_count"] == 65
assert collision["collisions"] == [] and collision["installed_archives"] == 68
assert len(jc1["files"]) == 51 and len(manifest["files"]) == 3
for row in jc1["files"]:
    assert sha(G / row["path"]) == row["sha256"], row["path"]
for row in manifest["files"]:
    assert sha(G / row["path"]) == row["sha256"], row["path"]
assert {x["path"] for x in manifest["files"]}.isdisjoint(x["path"] for x in jc1["files"])

inputs = [P / name for name in ("manifest_01.json", "zip_receipt_01.json",
          "compile_01/result.json", "collisions_01.json", "deployment_tests_01.json",
          "save_before_01.json", "save_after_01.json", "save_comparison_01.json")]
inputs += [R / "receipt.json", R / "probe.zip"]
inputs += [H / name for name in ("deploy_probe_04.ps1", "pack_probe_04.ps1",
          "scan_probe_collisions_04.ps1", "compile_probe_04.py", "test_deploy_probe_04.py")]
result = {"status": "ADDITIVE_WW1_PROBE_INSTALLED_STATIC_VERIFIED_LIVE_UNTESTED",
          "added_game_files": 3, "existing_production_files_verified": 51,
          "save_files_unchanged": 301, "public_codeware_stack_compiled_sources": 65,
          "collision_archives_checked": 68, "interruption_fixtures_passed": 6,
          "rollback": str((H / "deploy_probe_04.ps1").relative_to(W)),
          "rollback_action": "Rollback (game closed)",
          "full_production_rule": "Replace within 51 paths and remove all three probe paths",
          "live_patrol_result": "UNKNOWN", "game_launches": 0,
          "pins": [{"path":str(path.relative_to(W)),"sha256":sha(path)} for path in inputs]}
target = P / "installed_assessment_01.json"
assert not target.exists()
target.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
(P / "installed_assessment_01.json.sha256").write_text(sha(target)+"\n",encoding="ascii")
print(json.dumps({"status":result["status"], "files":3,"saves":301,
                  "assessment_sha256":sha(target)},indent=2))
