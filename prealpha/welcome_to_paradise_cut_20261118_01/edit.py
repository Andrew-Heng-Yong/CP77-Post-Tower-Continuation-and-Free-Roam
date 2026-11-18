"""Prepare private tour resources from the verified staged build and its current native donors."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / "welcome_to_paradise_20261118_01"
sys.path.insert(0, str(PARENT))
import prepare as src

WORK = ROOT / "work"
EDITS = WORK / "edit_02"
PACKAGE = PARENT / "candidate_01"
PARENT_SHA = "B40DCB11B13739552FEB0F35E105B6563E3C35E5C9763CACF3F1192740E3D9F8"
DIR = "base\\quest\\minor_quests\\mq061\\"
LIP = r"towercontinued\sidejob_repair_sr1\en-us.lipmap"
# Node IDs and screenplay line IDs from the tour dialogue audit.
CUT = {
    "01_nc_tower_scene": {735: [5633]},
    "03_arasaka_memorial_scene": {623: [6913], 629: [7169], 700: [7425]},
    "07_rancho_scene": {281: [5377], 288: [5633]},
    "12_kabuki_scene": {123: [2817,3073], 172: [4865], 238: [5633], 239: [5889]},
    "12_kabuki_scene_haze_body": {74: [1281], 82: [1537]},
    "13_end_scene": {275: [7681], 276: [7937]},
}


def resources():
    assert src.sha(PACKAGE/"core_manifest.json") == PARENT_SHA
    staged = {x["depot"]:x for x in src.read(PARENT/"work/cook_02/manifest.json")["resources"]}
    registry = {v["sha256"]:v for line in src.REGISTRY.open(encoding="utf8") if (v:=json.loads(line)).get("json")}
    docs = {}
    for h in src.read(PARENT/"work/sources_01/providers.json")["hits"]:
        d = h["depot"]
        if not d.startswith(DIR):
            continue
        private = staged.get(src.PREFIX+d)
        origin = private or registry[h["sha256"]]
        assert src.sha(h["raw"]) == h["sha256"] and src.sha(origin["json"]) == origin["json_sha256"]
        if private:
            assert src.sha(PARENT/"work/pack_01/source"/(src.PREFIX+d)) == private["sha256"]
        docs[d] = src.read(origin["json"])
    assert len(docs)==33
    return docs, staged


def scene_nodes(doc):
    handles = src.definitions(doc)
    def resolve(handle):
        return handles[handle.get("HandleId",handle.get("HandleRefId"))]
    root = doc["Data"]["RootChunk"]
    return root, {resolve(h)["nodeId"]["id"]:resolve(h) for h in resolve(root["sceneGraph"])["graph"]}, resolve


def socket(node, name=0, ordinal=0):
    port, = [s for s in node["outputSockets"] if (s["stamp"]["name"],s["stamp"]["ordinal"])==(name,ordinal)]
    return port


def destination(node, ordinal=0):
    return {"$type":"scnInputSocketId", "nodeId":{"$type":"scnNodeId","id":node},
            "isockStamp":{"$type":"scnInputSocketStamp","name":0,"ordinal":ordinal}}


def edit_scene(doc, name):
    root, nodes, resolve = scene_nodes(doc)
    johnny, = [actor for actor in root["actors"] if actor["actorName"]=="Johnny"]
    actor_id = johnny["actorId"]["id"]
    lines = root["screenplayStore"]["lines"]
    ids = {v["itemId"]["id"] for v in lines if actor_id in (v["speaker"]["id"],v["addressee"]["id"])}
    assert ids == {i for section in CUT[name].values() for i in section}
    # Stock screenplay IDs encode the array slot above the low byte. Remove
    # playback references while preserving every other line's lookup position.
    assert all(line["itemId"]["id"] == (i << 8 | 1) for i,line in enumerate(lines))

    def route(start, old, new, port=(0,0)):
        s = socket(nodes[start], *port)
        a = destination(*old)
        assert s["destinations"].count(a)==1,(name,start,old,port)
        idx = s["destinations"].index(a)
        s["destinations"][idx:idx+1] = [destination(*d) for d in new]

    if name=="01_nc_tower_scene":
        # Follow Richard's native staging delay. His workspot, speech and the next
        # hologram activation can now start without Johnny's holding animation.
        route(518,(735,),[(1160,1),(328,),(882,1)])
    elif name=="03_arasaka_memorial_scene":
        # Richard finishes the preceding line and moves to the next position
        # before his narration resumes. Keep the teleport and mappin callbacks.
        route(581,(623,),[],(2,0))
        socket(nodes[588])["destinations"].append(destination(582))
        route(582,(700,),[])
        route(286,(619,1),[])
        route(582,(735,1),[])
        route(215,(8,1),[(696,2)])
    elif name=="07_rancho_scene":
        # Journal arrival / combat writes run before the native security event
        # and End johnny. No actor is acquired or polled on this path.
        route(301,(308,1),[(302,1),(306,)])
    elif name=="12_kabuki_scene":
        # Remove the response-only option. Compact just the choice sockets;
        # their stored option IDs and the special outputs are independent.
        menu=nodes[710]
        assert [o["screenplayOptionId"]["id"] for o in menu["options"]]==[1794,2050,2306]
        assert socket(menu)["destinations"]==[destination(123),destination(198,1)]
        menu["options"].pop(0)
        menu["outputSockets"].remove(socket(menu))
        for out in menu["outputSockets"]:
            if out["stamp"]["name"]==0:
                assert out["stamp"]["ordinal"] in (1,2)
                out["stamp"]["ordinal"]-=1
        options=root["screenplayStore"]["options"]
        assert sum(o["itemId"]["id"]==1794 for o in options)==1
        assert all(o["itemId"]["id"] == (i << 8 | 2) for i,o in enumerate(options))
        route(484,(172,),[(487,1)],(0,1))
        route(244,(307,1),[])
        route(42,(513,1),[(156,1)])
        for predecessor in (143,146):
            route(predecessor,(239,),[(572,)])
        route(572,(594,),[])
    elif name=="12_kabuki_scene_haze_body":
        route(64,(80,1),[(72,1)])
        for predecessor in (68,70):
            route(predecessor,(74,),[(90,)])
        route(90,(94,),[])
    elif name=="13_end_scene":
        route(188,(293,),[])

    # Preserve section and actor IDs for resource references. Every removed
    # section is off the executing route; eliminate its old event clocks too.
    emptied = set(CUT[name])
    if name=="12_kabuki_scene":
        emptied.add(545)
    removed = set()
    for i, node in nodes.items():
        if i in emptied:
            events = [resolve(h) for h in node["events"]]
            assert [e["screenplayLineId"]["id"] for e in events if e["$type"]=="scnDialogLineEvent"] == CUT[name].get(i,[])
            removed.update(str(e["id"]["id"]) for e in events)
            node["events"]=[]
            node["sectionDuration"]["stu"]=0
            for out in node["outputSockets"]:
                out["destinations"]=[]
        if "actorBehaviors" in node:
            node["actorBehaviors"] = [b for b in node["actorBehaviors"] if b["actorId"]["id"]!=actor_id]
    johnny["acquisitionPlan"]="spawnDespawn"
    for field in ("isEnabled","spawnOnStart","alwaysSpawned","keepAlive","findInWorld","prefetchAppearance"):
        johnny["spawnDespawnParams"][field]=0
    symbols=root["debugSymbols"]["sceneEventsDebugSymbols"]
    for group in list(symbols):
        original=group["sceneEventIds"]
        group["sceneEventIds"]=[e for e in original if str(e["id"]) not in removed]
        if original and not group["sceneEventIds"]:
            symbols.remove(group)
    return {"sections":sorted(emptied),"removed_lines":sorted(ids),"removed_event_ids":sorted(removed)}


def main():
    docs, staged=resources()
    added=set()
    changed=set()
    evidence={}
    for name in CUT:
        depot=DIR+"scenes\\mq061_"+name+".scene"
        changed.add(depot)
        if src.PREFIX+depot not in staged:
            added.add(depot)
    # Follow callers through all 19 phases. The four existing scene aliases
    # and the established root/entry remain usable in the staged package.
    while True:
        count=len(changed)
        for d,doc in docs.items():
            if any(v.get("$type")=="ResourcePath" and src.value(v) in added for v in src.walk(doc)):
                changed.add(d)
                if src.PREFIX+d not in staged:
                    added.add(d)
        if len(changed)==count:
            break
    assert len(added)==4 and src.QUEST in changed
    for d in sorted(changed):
        doc=docs[d]
        originals=src.definitions(doc)
        if d.endswith(".scene"):
            key=Path(d).stem.removeprefix("mq061_")
            evidence[d]=edit_scene(doc,key)
        for v in src.walk(doc):
            if v.get("$type")=="ResourcePath" and src.value(v) in added:
                v["$value"]=src.PREFIX+v["$value"]
        ordered=src.canonical(doc,originals|src.definitions(doc),set())
        src.write(EDITS/(src.PREFIX+d+".json"),ordered)
    src.write(EDITS/"plan.json",{"parent_sha256":PARENT_SHA,"changed":sorted(changed),"added":sorted(added),"scenes":evidence})
    print(f"{len(changed)} scene/phase edits, {len(added)} new private depots")


if __name__=="__main__":
    main()
