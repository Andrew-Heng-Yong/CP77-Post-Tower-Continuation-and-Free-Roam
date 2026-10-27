"""Promote Rancho aliases only after byte-identical native resource proof."""
from hashlib import sha256
from pathlib import Path
import json

H=Path(__file__).resolve().parent
out=H/"audit_03.json"
assert not out.exists(),"Preserve audit evidence"
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
census_path=H.parents[1]/"diagnostics/world_npc_idle_20261026_02/families/census_03.json"
census=read(census_path)
validation_path=H/"native_validation_01.json";validation=read(validation_path)
decoded_path=H/"decoded_mismatch_02.json";decoded=read(decoded_path)
resolution_path=H/"mismatch_resolution_01.json";resolution=read(resolution_path)
byid={r["candidate_index"]:r for r in census["rows"]}
byref={s["full_ref"]:s for s in census["sectors"]}
bydecoded={r["id"]:r for r in decoded["rows"]}
byresolved={r["id"]:r for r in resolution["rows"]}
proved=[]
for f in validation["failures"]:
    ident=f["id"]
    row=byid[ident]
    authored=f["stored_refs"][0]
    registry=row["full_ref"]
    exact=bydecoded[ident]["winner"]["sha256"]
    registered=byref[registry]["winner"]["raw_sha256"]
    # The comparison is the required invariant; keep both selected source pins.
    assert exact==registered,ident
    assert authored != registry and "/#rancho_coronado/" in authored
    assert "/rancho_coronado/" in registry
    assert row["asset_classification"]=="SUPPORT_SHAPED_SOURCE_NOT_ELIGIBILITY_ALLOWLIST"
    assert row["binding_classification"]=="OWN_COMMUNITY_ALL_WITHIN"
    assert len(row["community_spawners"]) in (1,2)
    assert all(c.startswith(registry+"/") for c in row["community_spawners"])
    assert byresolved[ident]["native_ref"]==authored
    proved.append({"id":ident,"authored_prefab":authored,"registry_prefab":registry,
        "shared_native_bytes_sha256":exact,"community_refs":row["community_spawners"]})
assert len(proved)==31
result={"status":"RANCHO_AUTHORED_ALIAS_BYTE_IDENTITY_PROVED_NOT_DEPLOYED",
    "alias_groups":31,"previous_exact_groups":206,"total_supported_candidates":237,
    "pins":[{"path":str(p),"sha256":digest(p)} for p in (census_path,validation_path,decoded_path,resolution_path)],
    "groups":proved,
    "scope":"The original owner uses the authored path; community spawner uses the registry path. Both native archive resources have identical bytes.",
    "limit":"Asset equivalence does not prove live patrol, actor presence or every NPC family",
    "game_writes":0,"save_writes":0}
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:result[k] for k in ("status","alias_groups","total_supported_candidates")},indent=2))
