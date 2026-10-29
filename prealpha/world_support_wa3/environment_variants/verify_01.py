"""Verify environmental support against current native variant ranges and cooked owners."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
WS = HERE.parents[2]

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

checks = []
def check(name, result):
    checks.append({"check": name, "pass": bool(result)})
    if not result:
        raise AssertionError(name)

def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)

def expand(value):
    # Leaf payloads only: graph socket references are intentionally excluded.
    if isinstance(value, dict):
        if "HandleId" in value:
            return expand(value["Data"])
        return {k: expand(v) for k, v in value.items() if k != "sockets"}
    if isinstance(value, list):
        return [expand(v) for v in value]
    return value

inputs = read(HERE / "inputs_01.json")
proof = read(HERE / "build_proof_01.json")
variants = read(HERE / "variant_ranges_01.json")["rows"]
old_scan = read(HERE / "extract_01/report_01.json")
scan = read(HERE / "extract_02/report_01.json")
check("fresh 128-archive inventory", scan["archives"] == 128)
hit_key = lambda h: (Path(h["archive"]).name, h["depot"])
check("native winners unchanged across added external mods",
      {hit_key(h): h["sha256"] for h in old_scan["hits"]} ==
      {hit_key(h): h["sha256"] for h in scan["hits"]})
for hit in scan["hits"]:
    check("fresh native hash " + Path(hit["raw"]).name, sha(Path(hit["raw"])) == hit["sha256"])

allowed = {
    "worldCookedStaticMeshNode", "worldStaticDecalNode", "worldInstancedDestructibleMeshNode",
    "worldEntityNode", "worldCollisionNode", "worldStaticLightNode", "worldPhysicalDestructionNode",
    "worldStaticMeshNode", "worldStaticSoundEmitterNode", "worldCookedStaticDecalNode", "worldCookedCollisionNode",
}
groups = []
for source in inputs["groups"]:
    ident = source["id"]
    owner = next(o for o in proof["owners"] if o["id"] == ident)
    native = WS / source["native_binary"]
    check(f"{ident} pinned native graph", sha(native) == source["native_binary_sha256"])
    check(f"{ident} cooked owner hash", sha(Path(owner["path"])) == owner["sha256"])
    root = read(HERE / f"owner_{ident}_readback_01.json")["Data"]["RootChunk"]
    nodes = root["graph"]["Data"]["nodes"]
    by_id = {n["Data"]["id"]: n["Data"] for n in nodes}
    check(f"{ident} bounded nine-node graph", len(nodes) == 9 and len(owner["edges"]) == 8)
    event = expand(by_id[owner["native_event"]])
    check(f"{ident} exact native visibility payload", event == source["operations"][0]["payload"])
    guard = expand(by_id[2]["condition"])
    facts = {d["factName"]: d["value"] for d in walk(guard) if d.get("$type") == "questVarComparison_ConditionType"}
    check(f"{ident} sixteen exact guards", facts == owner["facts"] and len(facts) == 16)
    spawners = [d for d in walk(guard) if "spawnerReference" in d]
    check(f"{ident} exact native ready guard", len(spawners) == 1 and
          spawners[0]["spawnerReference"]["$value"] == owner["community_ref"] and
          spawners[0].get("$type") == "questSpawnerReady_ConditionType")
    writes = [d for d in walk(root) if d.get("$type") == "questSetVar_NodeType"]
    check(f"{ident} only private receipt writes", len(writes) == 5 and
          all(d["factName"].startswith(f"PTFRWA3ENV_{ident}_") and d["setExactValue"] == 1 for d in writes))
    eid = owner["native_event"]
    expected_edges = {"0.Out -> 1.In", "1.Out -> 2.In", "2.Out -> 3.In", "3.Out -> 4.In",
                      "4.Out -> 5.In", f"5.Out -> {eid}.In", f"{eid}.Out -> 7.In", "7.Out -> 8.In"}
    check(f"{ident} no replay or reactivation edge", set(owner["edges"]) == expected_edges)
    ranges = [r for r in variants if r["group"] == ident and r["archive"] == "ep1_1_nightcity.archive"]
    check(f"{ident} three current EP1 ranges", len(ranges) == 3)
    params = event["type"]["params"]
    states = {(p["prefabNodeRef"]["$value"], s["name"]["$value"]) for p in params for s in p["variantStates"]}
    check(f"{ident} all native operations show only", all(s["show"] == 1 for p in params for s in p["variantStates"]))
    types = Counter()
    for r in ranges:
        key = (r["variant"]["nodeRef"]["$value"], r["variant"]["name"]["$value"])
        check(f"{ident} native selected variant {r['start']}", key in states)
        check(f"{ident} current raw {r['start']}", sha(Path(r["raw"])) == r["raw_sha256"])
        matches = [h for h in scan["hits"] if h["depot"] == r["depot"]]
        check(f"{ident} only base/EP1 winners {r['start']}", {Path(h["archive"]).name for h in matches} ==
              {"basegame_3_nightcity.archive", "ep1_1_nightcity.archive"})
        check(f"{ident} exterior default descriptor {r['start']}", r["descriptor"]["category"] == "Exterior" and
              r["descriptor"]["level"] == 0 and r["descriptor"]["questPrefabNodeRef"]["$value"] == "0")
        check(f"{ident} exact placement range {r['start']}", len(r["placements"]) == r["end"] - r["start"])
        check(f"{ident} no spawn/loot/quest-trigger node {r['start']}", all(p["type"] in allowed for p in r["placements"]))
        types.update(p["type"] for p in r["placements"])
        for n in r["nodes"]:
            definition = n["definition"]
            if definition["$type"] == "worldEntityNode":
                check(f"{ident} entity is native TV only", definition["entityTemplate"]["DepotPath"]["$value"] ==
                      "base\\gameplay\\devices\\home_appliances\\tv_sets\\tv_5.ent")
        base = [b for b in variants if b["group"] == ident and b["archive"] == "basegame_3_nightcity.archive"
                and b["variant"]["rangeIndex"] == r["variant"]["rangeIndex"]]
        check(f"{ident} variant declaration stable across base/EP1 {r['start']}", len(base) == 1 and base[0]["variant"] == r["variant"])
    groups.append({"id": ident, "resource": owner["resource"], "placement_count": sum(types.values()),
                   "placement_types": dict(types), "default_enabled": ident == 461,
                   "native_variant_keys": sorted(states)})

result = {"status": "PASS", "checks": checks, "check_count": len(checks), "groups": groups,
          "selected_current_placements": sum(g["placement_count"] for g in groups),
          "scope": "Native show-once environment only; no native sector override or encounter replay.",
          "limits": ["Source validation is not runtime proof.", "Base/EP1 placement payloads differ; current EP1 ranges were reviewed.",
                     "461 is already enabled by default; its event retains native show semantics."],
          "game_writes": 0, "save_writes": 0}
(HERE / "assessment_01.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": result["status"], "checks": len(checks), "placements": result["selected_current_placements"]}))
