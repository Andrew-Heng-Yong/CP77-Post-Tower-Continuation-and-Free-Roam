"""Trace pinned MQ011 cleanup and the scene exit without modifying resources."""
from pathlib import Path
import importlib.util
import json
import hashlib

H = Path(__file__).resolve().parent
W = H.parents[3]
spec = importlib.util.spec_from_file_location("quest_model", W / "prealpha/phone_support_ph1/model.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
pins = m.read(W / "prealpha/quest_restoration_qr4/groups/G05/verification_02/source_pins.json")
wanted = [r"base\quest\minor_quests\mq011\mq011.questphase",
          r"base\quest\minor_quests\mq011\scenes\mq011_00_gun_range.scene",
          r"towercontinued\sidejobs_s23\base_b\mq011.questphase",
          r"towercontinued\b0_wilson_vendor\owner.questphase"]
selected = [next(r for r in pins if r["depot"] == depot) for depot in wanted]
epoch = m.read(W / "prealpha/quest_restoration_qr8/source_epoch_02.json")
for r in selected:
    assert m.sha(r["binary"]) == r["resource_sha256"]
    assert m.sha(r["json"]) == r["json_sha256"]
    if r["depot"].startswith("towercontinued"):
        current = Path(epoch["candidate"]) / "archive_source" / r["depot"]
        assert m.sha(current) == r["resource_sha256"] == epoch["source_resources"][r["depot"]]
native = m.model(selected[0]["json"])
wrapper = m.model(selected[2]["json"])
vendor = m.model(selected[3]["json"])
data = m.read(selected[1]["json"])
handles = {x["HandleId"]: x["Data"] for x in m.walk(data) if "HandleId" in x and "Data" in x}


def clean(x):
    if isinstance(x, dict):
        if "HandleId" in x or "HandleRefId" in x:
            return clean(x.get("Data", handles.get(x.get("HandleRefId"), {})))
        return {k: clean(v) for k, v in x.items() if k not in ("sockets", "connections")}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x


nodes = {n["nodeId"]["id"]: n for row in data["Data"]["RootChunk"]["sceneGraph"]["Data"]["graph"]
         for n in [row.get("Data", row)]}
edges = [(i, d["nodeId"]["id"], sock["stamp"], d["isockStamp"])
         for i, n in nodes.items() for sock in n.get("outputSockets", []) for d in sock.get("destinations", [])]
scene_trace = []
for i in (1538, 1290, 1279, 1267, 338, 1653):
    n = nodes[i]
    scene_trace.append({"id": i, "type": n["$type"], "quest": clean(n.get("questNode", {})),
        "incoming": [e for e in edges if e[1] == i], "outgoing": [e for e in edges if e[0] == i]})


def take(graph, ids):
    return {"nodes": {i: graph["nodes"][i] for i in ids},
            "edges": [e for e in graph["edges"] if e[0] in ids or e[2] in ids]}


result = {"status": "PASS_PINNED_SOURCE_TRACE_CURRENT_PRIVATE_HASH_EQUIVALENCE",
          "source_pins": selected,
          "native_root_edges": native["root"]["edges"],
          "native_post_scene": take(native["root/27"], [69, 85, 1]),
          "native_cleanup": take(native["root/24"], [0, 33, 2, 3, 6, 7, 34, 59]),
          "scene_exit": scene_trace,
          "private_handoff": take(wrapper["root"], [15, 1007, 1012]),
          "vendor_wait": take(vendor["root"], [100, 101, 102, 103]),
          "scope": "Pinned vanilla/source JSON with matching raw hashes; current private wrapper/vendor payload equivalence checked. No engine owner/trigger execution observation or actual shop interaction proof."}
p = H / "native_trace.json"
assert not p.exists()
p.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "scene_conditions": [{"id": r["id"], "quest": r["quest"]}
    for r in scene_trace if r["id"] in (1538, 1290)], "output": str(p)}))
