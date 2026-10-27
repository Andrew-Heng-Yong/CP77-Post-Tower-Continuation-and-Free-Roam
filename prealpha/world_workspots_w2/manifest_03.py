"""Identity map for 206 exact groups plus 31 byte-identical Rancho aliases."""
from hashlib import sha256
from pathlib import Path
import json

H=Path(__file__).resolve().parent
out=H/"manifest_03.json"
assert not out.exists(),"Preserve manifest evidence"
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
sha=lambda p:sha256(p.read_bytes()).hexdigest().upper()
old=H/"manifest_01.json";old_data=read(old)
audit=H/"audit_03.json";aliases=read(audit)
validated=H/"native_validation_01.json";v=read(validated)
assert old_data["owner_count"]==237 and aliases["alias_groups"]==v["failed_count"]==31
byid={r["id"]:r for r in aliases["groups"]}
groups=[]
for item in old_data["groups"]:
    group=dict(item)
    if group["id"] in byid:
        alias=byid[group["id"]]
        assert group["prefab"]==alias["registry_prefab"]
        assert group["community_refs"]==alias["community_refs"]
        assert group["asset_sha256"]==alias["shared_native_bytes_sha256"]
        group["registry_prefab"] = group["prefab"]
        group["prefab"] = alias["authored_prefab"]
        group["alias_proof_sha256"] = alias["shared_native_bytes_sha256"]
    groups.append(group)
assert len(groups)==237 and len({g["id"] for g in groups})==237
assert len({h for g in groups for h in g["spawner_hashes"]})==245
assert next(g for g in groups if g["id"]==183)["prefab"]==next(g for g in old_data["groups"] if g["id"]==183)["prefab"]
result={"status":"W3_SOURCE_IDENTITY_MANIFEST_NOT_DEPLOYABLE",
    "input_pins":[{"path":str(p),"sha256":sha(p)} for p in (old,audit,validated)],
    "owner_count":237,"spawner_count":245,"authored_aliases":31,
    "live_proven_owner_id":183,"groups":groups,
    "limits":["Only the existing Pacifica Scav group has a live patrol result",
              "This exact combat-event source cohort is not all NPCs",
              "No game or saved-game files changed"]}
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:result[k] for k in ("status","owner_count","spawner_count","authored_aliases")},indent=2))
