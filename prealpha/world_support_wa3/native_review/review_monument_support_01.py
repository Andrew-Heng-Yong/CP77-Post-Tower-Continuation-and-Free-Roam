"""Review the Monument support subset independently of its encounter controllers."""
import hashlib
import json
from collections import Counter
from pathlib import Path

H = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
p = H / "ep1_prefab_decoded_01/base/worlds/03_night_city/_compiled/default/ep1/quest_356664e005c6bb0d.streamingsector.json"
r = read(p)
binding = next(b for b in read(H / "ep1_prefab_bindings_01.json") if b["id"] == 1103)
checks = []
def check(name, value):
    checks.append({"check": name, "pass": bool(value)})
    assert value, name

ns = {n["index"]: n["definition"] for n in r["nodes"]}
check("current native raw pinned", sha(Path(r["raw"])) == r["raw_sha256"])
check("one exact current Quest descriptor", len(binding["descriptors"]) == 1 and binding["descriptors"][0]["descriptor"]["category"] == "Quest")
descriptor = binding["descriptors"][0]["descriptor"]
check("native EP1 descriptor", descriptor["blockIndex"]["oup"] == "EP1" and descriptor["data"]["DepotPath"]["$value"] == r["resource"])
check("native full prefab ref", descriptor["questPrefabNodeRef"]["$value"] in binding["resolved_candidates"])
drop = [i for i, n in ns.items() if n["$type"] in ["worldDeviceNode", "worldTriggerAreaNode"]]
check("exact63devices33triggers", Counter(ns[i]["$type"] for i in drop) == {"worldDeviceNode": 63, "worldTriggerAreaNode": 33})
devices = [n for n in ns.values() if n["$type"] == "worldDeviceNode"]
check("devices only security systems/areas", Counter(n["entityTemplate"]["DepotPath"]["$value"] for n in devices) == {
    "base\\gameplay\\devices\\security_systems\\security_area\\security_area_1.ent": 35,
    "base\\gameplay\\devices\\security_systems\\security_system.ent": 28})
triggers = [n for n in ns.values() if n["$type"] == "worldTriggerAreaNode"]
check("only quest trigger notifiers", all(x["Data"]["$type"] == "questTriggerNotifier_Quest" for n in triggers for x in n["notifiers"]))
check("32respawn triggers and one authored scene trigger", sum("respawn" in n["debugName"]["$value"] for n in triggers) == 32
      and sum("car_sexworker_scene" in n["debugName"]["$value"] for n in triggers) == 1)
removed = [x for x in r["placements"] if x["node"] in drop]
check("one placement for each excluded node", len(removed) == len(drop) == 96)
aliases = [x["quest_ref"].split("/")[-1] for x in removed]
kept = [n for i, n in ns.items() if i not in drop]
check("no retained payload references removed trigger/security aliases", all(not any(a in json.dumps(n) for a in aliases) for n in kept))
types = Counter(n["$type"] for n in kept)
check("exact passive support retained", types == {"worldAISpotNode": 226, "worldSmartObjectNode": 81,
      "worldPatrolSplineNode": 32, "worldGuardAreaNode": 32, "worldPopulationSpawnerNode": 19})
preview = [n for n in kept if n["$type"] == "worldPopulationSpawnerNode"]
check("19native previews do not auto spawn", all(n["spawnOnStart"] == 0 and n["alwaysSpawned"] == "default__false_" for n in preview))
spec = {"id": 1103, "native_prefab": descriptor["questPrefabNodeRef"]["$value"], "sector_resource": r["resource"],
        "sector_raw": r["raw"], "sector_sha256": r["raw_sha256"], "sector_json": str(p.resolve()),
        "drop_nodes": drop, "drop_types": [ns[i]["$type"] for i in drop], "drop_placements": [x["datum"] for x in removed],
        "preserve_ai_spots": 226, "preserve_nodes": len(kept), "preserve_node_types": dict(types),
        "native_block": binding["descriptors"][0]["block"], "native_descriptor": descriptor,
        "reason": "Restore authored workspots, combat smart objects, patrol splines and guard areas for matched living existing communities; omit respawn/scene triggers and security-system/area controllers rather than replay native encounters.",
        "requires_native_parent_gate_review": True}
specpath = H / "ep1_1103_filter_spec_01.json"
specpath.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8", newline="\n")
result = {"status": "PASS_FILTERED_MONUMENT_SUPPORT_SPEC", "checks": checks, "check_count": len(checks), "spec": spec,
          "pins": [{"path": str(q.resolve()), "sha256": sha(q)} for q in [p, Path(r["raw"]), specpath, H / "ep1_prefab_bindings_01.json"]],
          "limits": "No runtime proof. Exact current community/entry bindings, native parent gates, final private-sector readback and winner scan remain required. Keeping combat-position smart objects does not force NPCs into combat.",
          "game_writes": 0, "save_writes": 0}
(H / "monument_support_assessment_01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": result["status"], "checks": len(checks), "retained_nodes": len(kept), "workspots": 226}))
