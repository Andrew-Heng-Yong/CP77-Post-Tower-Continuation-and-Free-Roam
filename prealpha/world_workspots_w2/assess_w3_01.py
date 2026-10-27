"""Collect immutable W3 deployment status from pinned evidence."""
from hashlib import sha256
from pathlib import Path
import json

H = Path(__file__).resolve().parent
C = H / "candidate_04"
W = H.parents[1]
out = C / "assessment_01.json"
assert not out.exists()
digest = lambda p: sha256(p.read_bytes()).hexdigest().upper()
load = lambda p: json.loads(p.read_text(encoding="utf-8"))
manifest = load(C / "install_manifest_01.json")
package = load(C / "package_proof_01.json")
compile_result = load(C / "compile_01/result.json")
graphs = load(H / "candidate_03/graph_validation_01.json")
collisions = load(C / "collisions_01.json")
tests = load(C / "deployment_tests_01.json")
save = load(C / "save_comparison_01.json")
receipt = load(W / "recovery/world_workspots_w3_01/receipt.json")
zip_proof = load(C / "zip_proof_01.json")
assert manifest["full_package_count"] == 51 and manifest["private_owners"] == 237
assert package["archive_members"] == 1183 and package["checked_members"] == 1183
assert compile_result["status"] == "PASS" and compile_result["source_count"] == 64
assert graphs["status"] == "PASS_RANCHO_PRIVATE_OWNER_GRAPHS" and graphs["owners"] == 31
assert collisions["status"] == "PASS_ZERO_COLLISIONS" and not collisions["hits"]
assert tests["status"] == "PASS" and tests["interruption_points"] == 5
assert save["status"] == "PASS_ALL_SAVES_BYTE_IDENTICAL" and save["files"] == 301
assert receipt["status"] == "W3_51_PATH_INSTALLED_LIVE_PENDING"
assert digest(Path(zip_proof["path"])) == zip_proof["sha256"]
result = {
    "status": "W3_INSTALLED_STATIC_VERIFIED_LIVE_PENDING",
    "install_paths": 51, "replaced_paths": 3, "archive_members": 1183,
    "supported_native_prefab_owners": 237, "native_spawner_ids": 245,
    "new_rancho_alias_owners": 31, "native_source_prefab_references": 477,
    "excluded_source_references": 240,
    "live_proven_group": "Pacific car-goon Scavs after motorcycle dismount, WW1 preserved owner",
    "new_groups_live_proven": False,
    "full_redscript_compile": True, "resource_collisions": 0,
    "deployment_fixture_actions": tests["fixture_actions"],
    "interruption_points": tests["interruption_points"],
    "saved_game_files_unchanged": save["files"],
    "actual_install_receipt": str(W / "recovery/world_workspots_w3_01/receipt.json"),
    "zip_sha256": zip_proof["sha256"],
    "rollback_ready": True,
    "game_launched_by_assistant": False, "git_pushed": False, "public_release": False,
    "gameplay_limitation": "Other combat-event references and courier, scene, quest, and non-combat NPC families remain unverified",
}
out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
Path(str(out) + ".sha256").write_text(digest(out) + "\n", encoding="ascii")
print(json.dumps({"status": result["status"], "assessment_sha256": digest(out)}))
