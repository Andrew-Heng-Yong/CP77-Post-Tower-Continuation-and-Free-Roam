"""Action-free scene scope and reciprocal native-graph handle audit."""
import json
from pathlib import Path
from audit_scene_actor_ids import audit_scene_actor_ids, self_test

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "research/b0_streetkid_scene_load_s3"


def load(name):
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))["Data"]["RootChunk"]


def quest_edges(root):
    handles = {}

    def visit(value):
        if isinstance(value, dict):
            if "HandleId" in value and "Data" in value:
                assert value["HandleId"] not in handles
                handles[value["HandleId"]] = value["Data"]
            for v in value.values():
                visit(v)
        elif isinstance(value, list):
            for v in value:
                visit(v)

    visit(root)

    def key(value):
        return value.get("HandleId", value.get("HandleRefId"))

    def resolve(value):
        return handles[key(value)]

    sockets = {}
    for handle in resolve(root["graph"])["nodes"]:
        n = resolve(handle)
        for socket in n["sockets"]:
            ident = key(socket)
            assert ident not in sockets
            sockets[ident] = (n["id"], resolve(socket)["name"]["$value"])
    edges = set()
    for ident in sockets:
        for handle in handles[ident]["connections"]:
            c = resolve(handle)
            source, target = key(c["source"]), key(c["destination"])
            assert source in sockets and target in sockets
            assert ident in (source, target)
            for endpoint in (source, target):
                assert key(handle) in {key(h) for h in handles[endpoint]["connections"]}
            edges.add((*sockets[source], *sockets[target]))
    return edges, [resolve(n) for n in resolve(root["graph"])["nodes"]]


def main():
    s = load("scene.json")
    audit_scene_actor_ids(s)
    self_test()
    rejected = json.loads((AUDIT / 'crash_20260926_041324/rejected_artifact/scene.json').read_text(encoding='utf-8'))
    try:
        audit_scene_actor_ids(rejected)
    except ValueError:
        pass
    else:
        raise AssertionError('Original crashing S3 must fail the actor-ID regression check')
    graph = {n["Data"]["nodeId"]["id"]: n["Data"] for n in s["sceneGraph"]["Data"]["graph"]}
    assert set(graph) == {1, 8, 2000}
    assert graph[1]["outputSockets"][0]["destinations"][0]["nodeId"]["id"] == 8
    assert graph[8]["outputSockets"][0]["destinations"][0]["nodeId"]["id"] == 2000
    assert graph[8]["events"] == [] and graph[8]["sectionDuration"]["stu"] == 2000
    assert all(not socket["destinations"] for socket in graph[8]["outputSockets"][1:])
    assert s["props"] == s["workspots"] == s["workspotInstances"] == []
    assert s["screenplayStore"]["options"] == s["screenplayStore"]["lines"] == []
    assert s["locStore"]["vdEntries"] == s["locStore"]["vpEntries"] == []
    refs = s["resouresReferences"]
    assert len(refs["cinematicAnimSets"]) == len(refs["cinematicAnimNames"]) == 8
    assert refs["gameplayAnimSets"] == refs["gameplayAnimNames"] == []
    assert len(refs["lipsyncAnimSets"]) == 1
    actors = s["actors"] + s["playerActors"]
    assert {a["actorId"]["id"] for a in actors} == {0, 1, 2}
    for a in actors:
        assert a["lipsyncAnimSet"]["id"] == (0 if a["actorId"]["id"] == 2 else 4294967295)
        assert all(0 <= r["id"] < 8 for r in a["bodyCinematicAnimSets"])
    assert "johnny" not in json.dumps(s).lower()
    assert "#mq000_shower" not in json.dumps(s) and "#q001_v_room_tv" not in json.dumps(s)
    gate_edges, gate_nodes = quest_edges(load("gate.json"))
    assert gate_edges == {(0,"Out",9,"In"),(9,"Out",1,"In"),(1,"Out",2,"In"),(2,"Out",3,"In"),(3,"Out",4,"In1")}
    revision = next(n for n in gate_nodes if n['id'] == 9)['type']['Data']
    assert revision['factName'] == 'PTFRSKS3_Revision' and revision['value'] == 2
    owner_edges, owner_nodes = quest_edges(load("owner.json"))
    assert owner_edges == {(0,"Out",1,"In"),(1,"Out",2,"In"),(2,"Out",3,"in"),
                           (3,"out",4,"In"),(4,"Out",5,"In"),(5,"Out",6,"In"),
                           (3,"Default INT",7,"In"),(7,"Out",8,"In")}
    for n in gate_nodes + owner_nodes:
        if n["$type"] == "questFactsDBManagerNodeDefinition":
            assert n["type"]["Data"]["factName"].startswith("PTFRSKS3_")
    guard = next(n for n in gate_nodes if n["id"] == 2)
    conditions = {c["Data"]["type"]["Data"]["factName"]: c["Data"]["type"]["Data"]["value"]
                  for c in guard["condition"]["Data"]["conditions"]}
    assert conditions["PTFRSKS3_Enabled"] == 1
    assert conditions["PTFRSKS1_Enabled"] == conditions["PTFRSKS2_Enabled"] == 0
    assert conditions["q307_done"] == 1 and conditions["q307_active"] == 0
    print("S3: action-free scene, V bindings, genuine-completion guards, and reciprocal graph handles OK")


if __name__ == "__main__":
    main()
