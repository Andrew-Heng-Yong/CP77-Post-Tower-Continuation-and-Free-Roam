"""Separate border-crossing workspots from native security and encounter triggers."""
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
p = H / "outside_prefab_decoded_01/quest_769927088f9d9c0c.json"
data = read(p)
source = next(r for r in read(H / "outside_support_assessment_01.json")["rows"] if r["id"] == 1000)
drop = [26, 27, 28, 50, 51, 52, 53, 60]
checks = []
def check(name, result):
    checks.append({"check": name, "pass": bool(result)})
    assert result, name
def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)

nodes = {n["index"]: n["definition"] for n in data["nodes"]}
check("native sector pinned", sha(Path(data["raw"])) == data["raw_sha256"] == source["sector_sha256"])
check("native sector61nodes", len(nodes) == 61)
check("exact5questtriggers", [i for i, n in nodes.items() if n["$type"] == "worldTriggerAreaNode"] == [26, 27, 28, 50, 60])
check("exact3securitydevices", [i for i, n in nodes.items() if n["$type"] == "worldDeviceNode"] == [51, 52, 53])
devices = []
for i in [51, 52, 53]:
    n = nodes[i]
    connections = [{"class": c["deviceClassName"]["$value"], "refs": [v["$value"] for v in c["nodeRefs"]]}
                   for c in n["deviceConnections"]]
    if i in [51, 52]:
        check(str(i) + " cameras26turrets connected", any(c["class"] == "SurveillanceCameraControllerPS" and len(c["refs"]) == 22 for c in connections)
              and any(c["class"] == "SecurityTurretControllerPS" and len(c["refs"]) == 26 for c in connections))
        states = [d for d in walk(n) if d.get("$type") == "SecurityAreaControllerPS"]
        check(str(i) + " native area startsdisabled", len(states) == 1 and states[0]["securityAreaType"] == "DISABLED")
    devices.append({"index": i, "template": n["entityTemplate"]["DepotPath"]["$value"], "connections": connections})
removed_refs = [x["quest_ref"].split("/")[-1] for x in data["placements"] if x["node"] in drop]
keep = [n for i, n in nodes.items() if i not in drop]
check("retain41nativeworkspots", len([n for n in keep if n["$type"] == "worldAISpotNode"]) == 41)
check("retained payloads no references to removed devices/triggers", all(not any(v in json.dumps(n) for v in removed_refs) for n in keep))
allowed = {"worldAISpotNode", "worldSpeedSplineNode", "worldPatrolSplineNode", "worldCrowdNullAreaNode", "worldGuardAreaNode", "worldPopulationSpawnerNode"}
check("retained types supportonly", all(n["$type"] in allowed for n in keep))
preview = [n for n in keep if n["$type"] == "worldPopulationSpawnerNode"]
check("all8previewspawners disabled", len(preview) == 8 and all(n["spawnOnStart"] == 0 and n["alwaysSpawned"] == "false_" for n in preview))
check("preserveexactcommunityguard", nodes[29]["communityEntries"][0]["communityArea"]["reference"]["$value"] == "#q000_ow_com")
spec = {"id": 1000, "native_prefab": source["prefab"], "sector_resource": source["resource"],
        "sector_raw": data["raw"], "sector_sha256": data["raw_sha256"], "sector_json": str(p.resolve()),
        "drop_nodes": drop, "drop_types": [nodes[i]["$type"] for i in drop],
        "drop_placements": [x["datum"] for x in data["placements"] if x["node"] in drop],
        "preserve_ai_spots": 41, "preserve_nodes": 53,
        "reason": "Do not restore border respawn, combat, kill or security triggers or security connections to external cameras/turrets. Preserve native workspots and passive support for already-active matched communities.",
        "requires_native_parent_gate_review": True}
(H / "outside1000_filter_spec_01.json").write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8", newline="\n")
result = {"status": "PASS_FILTERED_BORDER_SUPPORT_SPEC", "check_count": len(checks), "checks": checks,
          "spec": spec, "devices": devices,
          "pins": [{"path": str(q.resolve()), "sha256": sha(q)} for q in [p, Path(data["raw"]), H / "outside1000_filter_spec_01.json"]],
          "limits": "No claim that border security or vehicle/encounter controllers are restored. Final current winner scan, private-sector verification and native parent admission gates required before promotion.",
          "game_writes": 0, "save_writes": 0}
(H / "border_support_assessment_01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": result["status"], "checks": len(checks), "preserved_spots": 41}))
