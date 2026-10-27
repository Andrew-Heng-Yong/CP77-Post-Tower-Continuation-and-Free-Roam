"""Read back all 31 alias owner graphs and their fact/phase boundaries."""
from hashlib import sha256
from pathlib import Path
import json

H=Path(__file__).resolve().parent
docpath=H/"candidate_03/graph_export_01.json"
manifest=H/"manifest_03.json"
alias=H/"audit_03.json"
out=H/"candidate_03/graph_validation_01.json"
assert not out.exists(),"Preserve prior validation"
read=lambda p:json.loads(p.read_text(encoding="utf-8-sig"))
doc,m,a=map(read,(docpath,manifest,alias))
ids={r["id"] for r in a["groups"]}
groups=sorted((g for g in m["groups"] if g["id"] in ids),key=lambda g:g["id"])
assert len(groups)==31
def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for value in obj.values():yield from walk(value)
    elif isinstance(obj,list):
        for value in obj:yield from walk(value)
handles={str(o["HandleId"]):o["Data"] for o in walk(doc) if "HandleId" in o and isinstance(o.get("Data"),dict)}
def deref(o):return o.get("Data",handles.get(str(o.get("HandleRefId")),o))
def nodes(g):return {n["id"]:n for n in map(deref,g["nodes"])}
root=doc["Data"]["RootChunk"]
assert not root.get("phasePrefabs") and not root.get("inplacePhases")
graph=deref(root["graph"]);nd=nodes(graph)
assert len(nd)==1+31*6
globals={"PostTowerFreeRoamActive":1,"PTFRP0_DR13":1,"q307_active":0,"q307_done":1,
 "q307_finished":1,"q307_2079":1,"q307_main_game_killed":1,"q307_ep1_killed":1,
 "PTFRBASE_Suspended":0,"q305_johnny_scene_active":0,"q115_point_of_no_return":0,"q000_done":1}
for j,g in enumerate(groups):
    base=100+j*10;p=g["prefix"]
    types=[nd[base+k]["$type"] for k in range(6)]
    assert types==["questFactsDBManagerNodeDefinition","questPauseConditionNodeDefinition",
        "questFactsDBManagerNodeDefinition","questFactsDBManagerNodeDefinition",
        "questFactsDBManagerNodeDefinition","questPhaseNodeDefinition"],g["id"]
    cond=deref(nd[base+1]["condition"])
    tests=[o for o in walk(cond) if "comparisonType" in o]
    want={**globals,p+"Request":1,p+"Claimed":0,p+"Entered":0,p+"Hold":0}
    assert cond["operation"]=="AND" and len(tests)==16 and all(t["comparisonType"]=="Equal" for t in tests)
    assert {t["factName"]:t["value"] for t in tests}==want,g["id"]
    written=[o for k in (0,2,3,4) for o in walk(nd[base+k]) if o.get("$type")=="questSetVar_NodeType"]
    assert [(w["factName"],w["value"]) for w in written]==[(p+"Ready",1),(p+"Claimed",1),(p+"Request",0),(p+"Ready",0)]
    owner=nd[base+5]
    assert len(owner["phaseInstancePrefabs"])==1 and owner["phaseInstancePrefabs"][0]["prefabNodeRef"]["$value"]==g["prefab"]
    inner=nodes(deref(owner["phaseGraph"]))
    assert set(inner)=={0,1,2}
    entered=[o for o in walk(inner[1]) if o.get("$type")=="questSetVar_NodeType"]
    hold=[o for o in walk(deref(inner[2]["condition"])) if "comparisonType" in o]
    assert len(entered)==len(hold)==1
    assert (entered[0]["factName"],entered[0]["value"])==(p+"Entered",1)
    assert (hold[0]["factName"],hold[0]["value"],hold[0]["comparisonType"])==(p+"Hold",1,"Equal")
forbidden={"questSpawnManagerNodeDefinition","questCommunityTemplate_NodeType","questSceneNodeDefinition",
 "questPuppetAIManagerNodeDefinition","questShowWorldNode_NodeType","questOutputNodeDefinition"}
assert not any(o.get("$type") in forbidden for o in walk(doc))
result={"status":"PASS_RANCHO_PRIVATE_OWNER_GRAPHS","owners":31,"gates":31*16,
 "authored_prefab_aliases":31,"export_sha256":sha256(docpath.read_bytes()).hexdigest().upper(),
 "game_writes":0,"save_writes":0}
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps(result,indent=2))
