"""Review group393's exact static corpse templates and selected appearances."""
from pathlib import Path
import json
import hashlib

H = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
checks = []
pins = []
def check(name, value):
    checks.append({"check": name, "pass": bool(value)})
    assert value, name
def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values():
            yield from walk(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk(v)

hits = {}
for directory in ["corpse_native_01", "corpse_appearances_native_01"]:
    report = H / directory / "report_01.json"
    data = read(report)
    check(directory + " current128 census", data["archives"] == 128)
    check(directory + " exactly two native hits", len(data["hits"]) == 2)
    pins.append({"path": str(report), "sha256": sha(report)})
    for hit in data["hits"]:
        p = Path(hit["copy"])
        check(p.name + " sole original appearance archive", Path(hit["archive"]).name == "basegame_4_appearance.archive")
        check(p.name + " extracted hash", sha(p) == hit["sha256"])
        hits[hit["depot"]] = hit
        pins.extend({"path": str(q), "sha256": sha(q)} for q in [p, Path(str(p) + ".json")])

rows = []
for sex, name in [("wa", "wa_generic_trunk_01"), ("ma", "ma_generic_passenger_06")]:
    depot = f"base\\characters\\entities\\corpse\\{sex}_corpse.ent"
    ent = read(Path(hits[depot]["copy"] + ".json"))["Data"]["RootChunk"]
    check(name + " entity class is plain entEntity", ent["entity"]["Data"]["$type"] == "entEntity")
    check(name + " no inherited templates", ent["includes"] == [] and ent["resolvedDependencies"] == [])
    compiled = ent["compiledData"]["Data"]["Chunks"]
    check(name + " exact static components", [c["$type"] for c in compiled] ==
          ["entEntity", "entCorpseComponent", "gameinfluenceObstacleComponent"])
    appearances = [a for a in ent["appearances"] if a["name"]["$value"] == name + "_corpse"]
    check(name + " exact appearance exists", len(appearances) == 1)
    appearance_depot = appearances[0]["appearanceResource"]["DepotPath"]["$value"]
    check(name + " exact appearance binding", appearance_depot == f"base\\characters\\appearances\\corpse\\generated\\{name}.app")
    app = read(Path(hits[appearance_depot]["copy"] + ".json"))["Data"]["RootChunk"]
    check(name + " no additional base entity", app["baseEntity"]["DepotPath"]["$value"] == "0")
    types = {d["$type"] for d in walk(app) if "$type" in d}
    components = {t for t in types if t.endswith("Component")}
    check(name + " appearance visual components only", components ==
          {"entGarmentSkinnedMeshComponent", "entSkinnedMeshComponent", "entVisualControllerComponent"})
    paths = {d["$value"] for d in walk(app) if d.get("$type") == "ResourcePath"}
    check(name + " appearance dependencies only meshes/rig", all(v == "0" or v.endswith((".mesh", ".rig")) for v in paths))
    check(name + " no inventory or gameplay components", not any(
        any(token in t.lower() for token in ["loot", "inventory", "npcpuppet", "transaction", "quest", "interact"])
        for t in types | {c["$type"] for c in compiled}))
    rows.append({"template": depot, "appearance": appearance_depot, "entity_class": "entEntity",
                 "components": [c["$type"] for c in compiled], "appearance_components": sorted(components)})

result = {"status": "PASS_STATIC_NATIVE_CORPSE_SUPPORT", "check_count": len(checks), "checks": checks,
          "rows": rows, "pins": pins,
          "decision": "Retain exact group393 static corpse placements. The physics preset named Lootable Corpse is a collision filter; these exact templates have no NPC, loot-container, inventory or gameplay interaction component and selected appearances add only visual components.",
          "condition": "Only valid for the two exact template/appearance pairs with no instance data; runtime agent verifies those sector placements and native identity.",
          "runtime_verified": False, "game_writes": 0, "save_writes": 0}
(H / "corpse_assessment_01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": result["status"], "checks": len(checks)}))
