from pathlib import Path
import json

W = Path(__file__).resolve().parents[2]
N = W / "research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/mq007.questphase.json"
R = W / "research/sidejobs_s23/base_a_v2/resume_02/mq007_resume_owner.json"
S = W / "prealpha/sidejobs_s30/prepared_02/json/towercontinued/sidejobs_s30/native/base/quest/minor_quests/mq006/scenes/mq006_02_finale.scene.json"


def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)


def node_summary(path):
    root = json.loads(path.read_text(encoding="utf-8"))["Data"]["RootChunk"]
    out = []
    for i, h in enumerate(root["graph"]["Data"]["nodes"]):
        d = h.get("Data", {})
        if not d:
            continue
        refs = []
        for x in walk(d):
            if "phaseResource" in x and isinstance(x["phaseResource"], dict):
                refs.append(x["phaseResource"].get("DepotPath", {}).get("$value"))
            if "phaseInstancePrefabs" in x:
                refs.extend(v.get("prefabNodeRef", {}).get("$value") for v in x["phaseInstancePrefabs"])
        out.append({"index": i, "id": d.get("id"), "type": d.get("$type"), "refs": refs})
    return out


for label, path in (("native_mq007", N), ("resume_mq007", R)):
    print(label)
    for row in node_summary(path):
        print(row)
    if label == "native_mq007":
        root = json.loads(path.read_text(encoding="utf-8"))["Data"]["RootChunk"]
        def graph_visit(graph, path="root"):
            for h in graph.get("nodes", []):
                x = h.get("Data", {})
                if not x:
                    continue
                here = path + "/" + str(x.get("id"))
                if x.get("$type") == "questPauseConditionNodeDefinition" and any(y.get("$type") == "questInventory_ConditionType" and y.get("itemID", {}).get("$value") == "Items.mq007_skippy" for y in walk(x)):
                    print("native_skippy_inventory_node", here)
                sub = (x.get("phaseGraph") or {}).get("Data", {})
                if sub:
                    graph_visit(sub, here)
        graph_visit(root["graph"]["Data"])

scene = json.loads(S.read_text(encoding="utf-8"))["Data"]["RootChunk"]
print("scene_keys", list(scene))
print("screenplay_type", type(scene["screenplayStore"]).__name__)
print("screenplay_keys", list(scene["screenplayStore"]) if isinstance(scene["screenplayStore"], dict) else len(scene["screenplayStore"]))
print("sceneGraph_keys", list(scene["sceneGraph"]))
lines = {}
for x in walk(scene["screenplayStore"]):
    if x.get("$type") == "scnscreenplayDialogLine":
        lines[x["itemId"]["id"]] = {"speaker": x["speaker"]["id"], "loc": x["locstringId"]["ruid"]}
print("screenplay_lines", len(lines), "johnny", [(k, v) for k, v in lines.items() if v["speaker"] == 5])
dialog = []
for x in walk(scene["sceneGraph"]):
    if x.get("$type") == "scnDialogLineEvent":
        line_id = x["screenplayLineId"]["id"]
        dialog.append({"line": line_id, "speaker": lines.get(line_id, {}).get("speaker"), "event": x["id"]["id"], "duration": x["duration"]})
print("dialog_events", len(dialog), "johnny", [x for x in dialog if x["speaker"] == 5])
print("other_speakers", {a["actorName"]: sum(x["speaker"] == a["actorId"]["id"] for x in dialog) for a in scene["actors"]})
for h in scene["sceneGraph"]["Data"]["graph"]:
    d = h.get("Data", {})
    ids = [x.get("screenplayLineId", {}).get("id") for x in walk(d) if x.get("$type") == "scnDialogLineEvent"]
    if any(x in {line for line, actor in lines.items() if actor["speaker"] == 5} for x in ids):
        print("johnny_graph_node", d.get("nodeId", {}).get("id"), d.get("$type"), "sectionDuration", d.get("sectionDuration"), "num_events", len(d.get("events", [])))
