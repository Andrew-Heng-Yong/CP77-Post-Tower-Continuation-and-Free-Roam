"""Pin installed W2 state without claiming universal live NPC coverage."""
from hashlib import sha256
from pathlib import Path
import json

H=Path(__file__).resolve().parent
W=H.parents[1]
P=H/"candidate_02"
G=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077")
out=H/"assessment_01.json"
assert not out.exists(),"Preserve earlier assessment"
sha=lambda p:sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
m=read(P/"install_manifest_01.json")
receipt=read(W/"recovery/world_workspots_w2_01/receipt.json")
assert receipt["status"]=="W2_51_PATH_INSTALLED_LIVE_PENDING"
assert m["full_package_count"]==51 and m["private_owners"]==206
assert all(sha(G/f["path"])==f["after"] for f in m["package_files"])
assert all(not (G/f["path"]).exists() for f in m["retired"])
assert read(P/"save_comparison_01.json")["status"]=="PASS_ALL_SAVES_BYTE_IDENTICAL"
assert read(P/"deployment_tests_02.json")["status"]=="PASS"
assert read(P/"compile_01/result.json")["status"]=="PASS"
assert read(P/"graph_validation_01.json")["status"]=="PASS_STATIC_PRIVATE_OWNER_GRAPHS"
assert read(P/"collisions_01.json")["status"]=="PASS_EXPECTED_PROBE_COLLISION_ONLY"
assert read(P/"zip_proof_01.json")["members"]==51
pin_paths=[P/"install_manifest_01.json",P/"compile_01/result.json",
    P/"graph_validation_01.json",P/"collisions_01.json",
    P/"deployment_tests_02.json",P/"zip_proof_01.json",
    P/"save_comparison_01.json",H/"audit_02.json",H/"manifest_02.json",
    H/"candidate_01/package_proof_01.json",
    W/"recovery/world_workspots_w2_01/receipt.json",
    W/"diagnostics/world_npc_idle_20261026_04/gamelog_probe05_live_success.log"]
result={"status":"W2_51_PATH_INSTALLED_STATIC_VERIFIED_NEW_GROUPS_LIVE_PENDING",
    "full_installed_paths":51,"changed_existing_paths":3,"removed_probe_paths":3,
    "packed_archive_members":1182,"new_private_resources":10,
    "private_prefab_owners":206,"live_proven_group_count":1,
    "new_groups_live_pending":205,"save_files_unchanged":301,
    "deployment_fixture_actions":23,"interruption_points":6,
    "scope_limit":"Not a repair for all NPCs; unresolved, content-bearing, courier and other families remain outside exact-owner cohort",
    "no_assistant_game_launch":True,"no_assistant_fact_edits":True,
    "no_public_release":True,"no_git_push":True,
    "rollback":"prealpha/world_workspots_w2/deploy_01.ps1 -Action ValidateRollback / Rollback with game closed; file undo is not save undo",
    "pins":[{"path":str(p.relative_to(W)),"sha256":sha(p)} for p in pin_paths]}
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
(out.with_suffix(out.suffix+".sha256")).write_text(sha(out)+"\n",encoding="ascii")
print(json.dumps({k:result[k] for k in ("status","full_installed_paths","private_prefab_owners","new_groups_live_pending","save_files_unchanged")},indent=2))
