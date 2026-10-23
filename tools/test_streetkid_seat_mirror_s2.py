"""Static graph and scope contract for the Streetkid stool/fix-nose opt-in."""

from __future__ import annotations

import json
from pathlib import Path
from audit_scene_actor_ids import audit_scene_actor_ids

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "research/b0_streetkid_seat_mirror_s2"


def data(name: str) -> dict:
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))["Data"]["RootChunk"]


def node(graph: list[dict], ident: int) -> dict:
    found = [item["Data"] for item in graph if item["Data"]["nodeId"]["id"] == ident]
    assert len(found) == 1, ident
    return found[0]


def dest(n: dict, socket: int = 0) -> list[int]:
    return [d["nodeId"]["id"] for d in n["outputSockets"][socket]["destinations"]]


def anim(e: dict) -> str:
    return (e["Data"].get("animName") or {}).get("Data", {}).get("unk1", [{}])[0].get("$value", "")


def main() -> None:
    scene = data("scene.json")
    references = scene["resouresReferences"]
    assert len(references["gameplayAnimNames"]) == len(references["gameplayAnimSets"]), "paired gameplay animation tables are inconsistent"
    gameplay_declared = {a['$value'] for entry in references['gameplayAnimNames'] for a in entry['animationNames']}
    gameplay_used = {e['Data'].get('gameplayAnimName',{}).get('Data',{}).get('unk1',[{}])[0].get('$value','')
                     for n in scene['sceneGraph']['Data']['graph'] for e in n['Data'].get('events', [])} - {'','None'}
    cinematic_declared = {a['$value'] for entry in references['cinematicAnimNames'] for a in entry['animationNames']}
    assert gameplay_used <= (gameplay_declared | cinematic_declared)
    assert 'fpp_idle_stand' in gameplay_used and 'fpp_idle_stand' in gameplay_declared
    assert len(references['gameplayAnimSets']) == 2
    assert len(scene["props"]) == 1
    prop = scene['props'][0]
    assert prop['propId']['id'] == 0 and prop['entityAcquisitionPlan'] == 'spawnDespawn'
    assert prop['spawnDespawnParams']['keepAlive'] == 0
    assert prop['spawnDespawnParams']['alwaysSpawned'] == 1 and prop['spawnDespawnParams']['spawnOnStart'] == 1
    assert prop['spawnDespawnParams']['findInWorld'] == 0
    assert prop['spawnDespawnParams']['dynamicEntityUniqueName']['$value'] == 'p_PTFRSKS2_vodka_shot'
    graph = scene["sceneGraph"]["Data"]["graph"]
    declared = {a["$value"] for entry in references["cinematicAnimNames"] for a in entry["animationNames"]}
    used = {anim(e) for n in graph for e in n["Data"].get("events", []) if anim(e)}
    assert used <= declared, f"missing animation resource declarations: {used - declared}"
    assert len(references["cinematicAnimSets"]) == len(references["cinematicAnimNames"]) == 8
    assert len(references["lipsyncAnimSets"]) == 1
    actors = {a["actorId"]["id"]: a for a in scene["actors"] + scene["playerActors"]}
    audit_scene_actor_ids(scene)
    assert set(actors) == {0, 1, 2}
    performers = {1: 0, 257: 1, 513: 2}
    for actor in actors.values():
        assert actor["lipsyncAnimSet"]["id"] == (0 if actor["actorId"]["id"] == 2 else 4294967295)
        assert all(0 <= b["id"] < 8 for b in actor["bodyCinematicAnimSets"])
    for n in graph:
        for event in n["Data"].get("events", []):
            if not anim(event):
                continue
            actor = actors[performers[event["Data"]["performer"]["id"]]]
            bound = {a["$value"] for b in actor["bodyCinematicAnimSets"]
                     for a in references["cinematicAnimNames"][b["id"]]["animationNames"]}
            assert anim(event) in bound, f"clip not bound to its performer: {anim(event)}"
    loc = scene["locStore"]
    locales = {'db_db': 0, 'pl_pl': 1, 'en_us': 2}
    ordering = [(locales[d['localeId']], int(d['locstringId']['ruid'])) for d in loc['vdEntries']]
    assert ordering == sorted(ordering), 'localization lookup order differs from vanilla'
    for desc in loc["vdEntries"]:
        assert 0 <= desc["vpeIndex"] < len(loc["vpEntries"])
        assert desc["variantId"] == loc["vpEntries"][desc["vpeIndex"]]["variantId"]
    localized = {d["locstringId"]["ruid"] for d in loc["vdEntries"]}
    assert all(o["locstringId"]["ruid"] in localized for o in scene["screenplayStore"]["options"])
    for option in scene['screenplayStore']['options']:
        english = [d for d in loc['vdEntries'] if d['localeId'] == 'en_us' and d['locstringId'] == option['locstringId']]
        assert len(english) == 1 and loc['vpEntries'][english[0]['vpeIndex']]['content']
    assert scene["interruptionScenarios"] == []
    ids = [n["Data"]["nodeId"]["id"] for n in graph]
    assert len(ids) == len(set(ids)) == 28
    assert all(d['nodeId']['id'] in ids for n in graph for s in n['Data']['outputSockets'] for d in s['destinations'])
    assert dest(node(graph, 1)) == [4]
    assert dest(node(graph, 4)) == [595]
    for branch,chain in [(0,[1708,1713,1792,1689]),(1,[1709,1712,1794,1693])]:
        assert dest(node(graph,595),branch)==[chain[0]]
        for a,b in zip(chain,chain[1:]): assert dest(node(graph,a))==[b]
        assert dest(node(graph,chain[-1]),1)==[8]
    assert dest(node(graph,1049))==[1050] and dest(node(graph,1049),1)==[1051]
    for ident in [1050,1051]: assert dest(node(graph,ident))==[2000]
    for actor in scene['actors']:
        assert actor['spawnDespawnParams']['appearance']['$value']=='default'
        assert actor['spawnDespawnParams']['keepAlive']==0 and actor['spawnDespawnParams']['spawnOnStart']==0
    for ident in [1712,1713,1050,1051]:
        action=node(graph,ident)['questNode']['Data']['actions'][0]['type']['Data']
        assert action['entityReference']['dynamicEntityUniqueName']['$value'].startswith('a_PTFRSKS2_v_')
        assert action['action']==('Activate' if ident in [1712,1713] else 'Deactivate')
    for ident in [1708,1709]:
        assert node(graph,ident)['questNode']['Data']['type']['Data']['sceneFile']['DepotPath']['$value']=='towercontinued\\streetkid_seat_mirror_s2\\seat_mirror.scene'
    assert 'Items.Q000_StreetKid_' not in json.dumps(scene)
    assert prop['spawnDespawnParams']['spawnMarkerNodeRef']['$value'].endswith('/#q000_kid_01b_meet_your_fixer_bar')
    offset=prop['spawnDespawnParams']['spawnOffset']['position']
    assert -2.0 < offset['X'] < -1.6 and -0.2 < offset['Y'] < 0.1 and 1.05 < offset['Z'] < 1.17
    for ident in [4,10,2021]: assert node(graph,ident)['displayNameOverride']==''
    assert dest(node(graph, 8)) == [10]
    assert dest(node(graph, 10)) == [2010]
    assert dest(node(graph, 10), 1) == [2020]
    assert dest(node(graph, 2020)) == [10]
    assert dest(node(graph, 2010)) == [2021]
    assert dest(node(graph, 2021)) == [33]
    assert dest(node(graph, 33)) == [1049]
    assert node(graph, 10)["options"][0]["caption"]["$value"] == "fix_nose"
    assert len(node(graph, 10)["options"]) == 2
    assert node(graph, 10)['options'][1]['caption']['$value'] == 'vodka_shot'
    assert node(graph, 2021)['options'][0]['caption']['$value'] == 'get_up'
    assert [s['stamp']['ordinal'] for s in node(graph,10)['outputSockets'] if s['stamp']['name'] == 0] == [0,1]
    assert node(graph, 8)["sectionDuration"]["stu"] == 3000
    assert [e["Data"]["$type"] for e in node(graph, 8)["events"]] == ["scneventsSocket"]
    fix = node(graph, 2010)
    assert len([e for e in fix["events"] if "fix_nose" in anim(e)]) == 3
    assert fix["sectionDuration"]["stu"] == 9500
    assert sorted([d["nodeId"]["id"] for s in fix["outputSockets"] for d in s["destinations"]]) == [664, 1697, 1699, 2021]
    drink=node(graph,2020)
    assert len(drink['events']) == 6
    assert len([e for e in drink['events'] if 'drink_shot' in anim(e)]) == 3
    assert sorted(d['nodeId']['id'] for s in drink['outputSockets'] for d in s['destinations']) == [10,735]
    assert [e['Data']['propId']['id'] for e in drink['events'] if 'propId' in e['Data']] == [0,0]
    stand = node(graph, 33)
    assert len([e for e in stand["events"] if "sit_barstool_bar_lean0" in anim(e) and "to__stand" in anim(e)]) == 3
    assert not any("sit_bench" in anim(e) or "sit_chair" in anim(e) for n in graph for e in n["Data"].get("events", []))
    assert {w["workspotInstanceId"]["id"] for w in scene["workspotInstances"]} == {686, 664, 1697, 1699,735,1689,1693}
    event_ids = [e["Data"]["id"]["id"] for n in graph for e in n["Data"].get("events", [])]
    assert len(event_ids) == len(set(event_ids)), "duplicate scene event ids"
    assert [p["itemId"]["id"] for p in scene["screenplayStore"]["options"]] == [2, 258, 514, 770]
    assert scene["screenplayStore"]["lines"] == []
    assert not any("johnny" in json.dumps(actor).lower() for actor in scene["actors"])
    assert not any("questFactsDBManagerNodeDefinition" in json.dumps(n) for n in graph)

    gate, owner = data("gate.json"), data("owner.json")
    for resource in (gate, owner):
        for entry in resource["graph"]["Data"]["nodes"]:
            n = entry["Data"]
            if n["$type"] == "questFactsDBManagerNodeDefinition":
                assert n["type"]["Data"]["factName"].startswith("PTFRSKS2_")
    guard = next(n["Data"] for n in gate["graph"]["Data"]["nodes"] if n["Data"]["id"] == 2)
    conditions = {c["Data"]["type"]["Data"]["factName"]: c["Data"]["type"]["Data"]["value"]
                  for c in guard["condition"]["Data"]["conditions"]}
    assert conditions["PTFRSKS2_Enabled"] == 1
    assert conditions["PTFRSKS1_Enabled"] == 0
    assert conditions['PTFRSKS3_Enabled'] == conditions['PTFRSKS3_Active'] == 0
    from test_streetkid_scene_load_s3 import quest_edges
    gate_edges,gate_nodes=quest_edges(gate)
    assert gate_edges == {(0,'Out',9,'In'),(9,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In1')}
    revision=next(n for n in gate_nodes if n['id']==9)['type']['Data']
    assert revision['factName']=='PTFRSKS2_Revision' and revision['value']==4
    owner_edges,owner_nodes=quest_edges(owner)
    assert {(2,'Out',20,'In'),(20,'Out',23,'In'),(23,'Out',3,'in'),(3,'out',24,'In'),(24,'Out',21,'In'),(21,'Out',4,'In'),(3,'Default INT',25,'In'),(25,'Out',22,'In'),(22,'Out',7,'In')} <= owner_edges
    for ident, states in [(20,[0,1]),(21,[1,0]),(22,[1,0])]:
        n=next(n for n in owner_nodes if n['id']==ident)
        params=n['type']['Data']['params']
        assert len(params)==1
        assert params[0]['prefabNodeRef']['$value'].endswith('/#q000_kid_coyote_mirror')
        assert [v['show'] for v in params[0]['variantStates']]==states
    for ident, action in [(23,'ForceON'),(24,'ForceOFF'),(25,'ForceOFF')]:
        n=next(n for n in owner_nodes if n['id']==ident)
        params=n['type']['Data']['params']
        assert len(params)==1
        assert params[0]['Data']['objectRef']['$value'].endswith('/#q000_kid_coyote_mirror/#q000_kid_dvc_mirror_device')
        assert params[0]['Data']['deviceAction']['$value']==action
    assert conditions["q307_done"] == 1 and conditions["q000_done"] == 1
    assert not any("q000\\" in p for p in json.loads((AUDIT / "build_manifest.json").read_text())["resources"])
    print("Streetkid S2 scene route, V-only actions, fact scope, and rollback guard OK")


if __name__ == "__main__":
    main()
