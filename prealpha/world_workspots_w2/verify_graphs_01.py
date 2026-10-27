"""Check all generated private owner graphs and exact serialized predicates."""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import json

H = Path(__file__).resolve().parent
manifest_path = H / "manifest_02.json"
export_path = H / "candidate_02/graph_export_proof_01.json"
out = H / "candidate_02/graph_validation_01.json"
assert not out.exists(), "Preserve previous validation"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
exports = json.loads(export_path.read_text(encoding="utf-8"))
assert manifest["owner_count"] == 206 and exports["resources"] == 9

def walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values(): yield from walk(v)
    elif isinstance(o, list):
        for v in o: yield from walk(v)

global_gates = {"PostTowerFreeRoamActive":1,"PTFRP0_DR13":1,
    "q307_active":0,"q307_done":1,"q307_finished":1,"q307_2079":1,
    "q307_main_game_killed":1,"q307_ep1_killed":1,
    "PTFRBASE_Suspended":0,"q305_johnny_scene_active":0,
    "q115_point_of_no_return":0,"q000_done":1}
by_source = defaultdict(list)
for g in manifest["groups"]:
    if g["id"] != 183: by_source[g["native_binary"]].append(g)
count = 0
proofs = []
for rec in exports["proofs"]:
    path = Path(rec["json"])
    assert sha256(path.read_bytes()).hexdigest().upper() == rec["json_sha256"]
    doc = json.loads(path.read_text(encoding="utf-8-sig"))
    handles = {str(o["HandleId"]):o["Data"] for o in walk(doc)
               if "HandleId" in o and isinstance(o.get("Data"),dict)}
    def deref(o): return o.get("Data",handles.get(str(o.get("HandleRefId")),o))
    def nodes(g): return {n["id"]:n for n in map(deref,g["nodes"])}
    def edges(g):
        nd=nodes(g); sockets={}
        for ident,n in nd.items():
            for sock in n["sockets"]:
                obj=deref(sock); sockets[id(obj)]=(ident,obj["name"]["$value"])
        found=set()
        for n in nd.values():
            for sock in map(deref,n["sockets"]):
                for conn in map(deref,sock["connections"]):
                    found.add((*sockets[id(deref(conn["source"]))],*sockets[id(deref(conn["destination"]))]))
        return found
    source = next((s for s in by_source if Path(s).stem+"_owners" == path.stem),None)
    assert source is not None, path
    groups=sorted(by_source[source],key=lambda x:x["id"])
    root=doc["Data"]["RootChunk"]
    assert not root.get("phasePrefabs") and not root.get("inplacePhases")
    assert not doc["Data"].get("EmbeddedFiles")
    graph=deref(root["graph"]); nd=nodes(graph)
    assert len(nd)==1+6*len(groups) and nd[0]["$type"]=="questInputNodeDefinition"
    expected_edges=set()
    for j,g in enumerate(groups):
        base=100+j*10; prefix=g["prefix"]
        ident=g["id"]
        expected_types=["questFactsDBManagerNodeDefinition","questPauseConditionNodeDefinition",
            "questFactsDBManagerNodeDefinition","questFactsDBManagerNodeDefinition",
            "questFactsDBManagerNodeDefinition","questPhaseNodeDefinition"]
        assert [nd[base+k]["$type"] for k in range(6)]==expected_types,ident
        cond=deref(nd[base+1]["condition"])
        assert cond["$type"]=="questLogicalCondition" and cond["operation"]=="AND"
        tests=[o for o in walk(cond) if "comparisonType" in o]
        want={**global_gates,prefix+"Request":1,prefix+"Claimed":0,prefix+"Entered":0,prefix+"Hold":0}
        assert len(tests)==16 and all(x["comparisonType"]=="Equal" for x in tests),ident
        assert {x["factName"]:x["value"] for x in tests}==want,ident
        writers=[o for k in (0,2,3,4) for o in walk(nd[base+k]) if o.get("$type")=="questSetVar_NodeType"]
        assert [(o["factName"],o["value"]) for o in writers]==[
            (prefix+"Ready",1),(prefix+"Claimed",1),(prefix+"Request",0),(prefix+"Ready",0)],ident
        owner=nd[base+5]
        assert owner["phaseInstancePrefabs"]==[{"$type":"questQuestPrefabEntry",
            "prefabNodeRef":{"$type":"NodeRef","$storage":"string","$value":g["prefab"]}}],ident
        inner=deref(owner["phaseGraph"]); inn=nodes(inner)
        assert set(inn)=={0,1,2}
        assert edges(inner)=={(0,"Out",1,"In"),(1,"Out",2,"In")},ident
        entered=[o for o in walk(inn[1]) if o.get("$type")=="questSetVar_NodeType"]
        assert len(entered)==1 and (entered[0]["factName"],entered[0]["value"])==(prefix+"Entered",1),ident
        hold=[o for o in walk(deref(inn[2]["condition"])) if "comparisonType" in o]
        assert len(hold)==1 and (hold[0]["factName"],hold[0]["value"],hold[0]["comparisonType"])==(prefix+"Hold",1,"Equal"),ident
        expected_edges.update({(0,"Out",base,"In"),(base,"Out",base+1,"In"),
            (base+1,"Out",base+2,"In"),(base+2,"Out",base+3,"In"),
            (base+3,"Out",base+4,"In"),(base+4,"Out",base+5,"In1")})
        count+=1
    assert edges(graph)==expected_edges,path
    forbidden={"questSpawnManagerNodeDefinition","questCommunityTemplate_NodeType",
        "questSceneNodeDefinition","questPuppetAIManagerNodeDefinition",
        "questShowWorldNode_NodeType","questOutputNodeDefinition"}
    assert not any(o.get("$type") in forbidden for o in walk(doc)),path
    proofs.append({"resource":rec["resource"],"owners":len(groups),"json_sha256":rec["json_sha256"]})
assert count==205
result={"status":"PASS_STATIC_PRIVATE_OWNER_GRAPHS","owners":count,"resources":len(proofs),
        "predicate_checks":count*16,"proofs":proofs,"limits":["Static proof does not establish live actor or scene behavior"],
        "game_writes":0,"save_writes":0}
out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:result[k] for k in ("status","owners","resources","predicate_checks")},indent=2))
