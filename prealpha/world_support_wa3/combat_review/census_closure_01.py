"""Read the complete native CE phase closure, including families outside the old477refs."""
from pathlib import Path
import collections
import hashlib
import json

H = Path(__file__).resolve().parent
W = H.parents[2]
N = H.parent / "native_review"
read = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest().upper()
def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)

hits = []
reports = []
for directory in ["combat_current_native_02", "combat_additional_native_01", "combat_additional_native_02"]:
    p = N / directory / "report_01.json"
    report = read(p)
    assert report["archives"] == 128
    hits += report["hits"]
    reports.append(p)
assert len(hits) == 247 and len({h["depot"] for h in hits}) == 247
seen = {h["depot"] for h in hits}
all_nodes = {}
all_graph_nodes = {}
pins = []
for h in hits:
    path = Path(h["copy"])
    assert sha(path) == h["sha256"]
    document = read(Path(str(path) + ".json"))
    hs = {d["HandleId"]: d["Data"] for d in walk(document) if "HandleId" in d and "Data" in d}
    def resolve(v): return v.get("Data", hs.get(v.get("HandleRefId"), v))
    def norm(v, graphs=True):
        if isinstance(v, dict):
            if "HandleId" in v or "HandleRefId" in v: return norm(resolve(v), graphs)
            return {k: norm(x, graphs) for k, x in v.items() if k != "sockets" and (graphs or k != "phaseGraph")}
        if isinstance(v, list): return [norm(x, graphs) for x in v]
        return v
    idx, full = {}, {}
    def visit(g, p):
        for handle in g["nodes"]:
            node = resolve(handle)
            q = p + "/" + str(node["id"])
            idx[q] = norm(node, False)
            if node.get("phaseInstancePrefabs"): full[q] = norm(node)
            if node.get("phaseGraph"): visit(resolve(node["phaseGraph"]), q)
    visit(resolve(document["Data"]["RootChunk"]["graph"]), "root")
    all_nodes[h["depot"]] = idx
    all_graph_nodes[h["depot"]] = full
    pins += [{"path": str(p.resolve()), "sha256": sha(p)} for p in [path, Path(str(path) + ".json")]]

unread = {d["$value"] for ns in all_nodes.values() for d in walk(ns)
          if d.get("$type") == "ResourcePath" and str(d.get("$value", "")).endswith(".questphase") and d["$value"] not in seen}
assert not unread, unread
combat = []
for resource, ns in all_nodes.items():
    for path, node in ns.items():
        types = [d["$type"] for d in walk(node) if "$type" in d]
        if any(any(token in t.lower() for token in ["combatnode", "injectcombatthreat", "setattitude", "faction"]) for t in types):
            combat.append({"resource": resource, "path": path, "types": types, "node": node})

def refs_for(resource, node, visited=None):
    visited = set() if visited is None else set(visited)
    refs = {d["$value"] for d in walk(node) if d.get("$type") == "NodeRef" and d.get("$value") not in ["0", "", "#player"]}
    for d in walk(node):
        if d.get("$type") == "ResourcePath" and str(d.get("$value", "")).endswith(".questphase") and d["$value"] not in visited:
            dep = d["$value"]
            refs |= refs_for(dep, all_nodes[dep], visited | {resource, dep})
    return refs

old = read(H.parent / "census_01.json")["rows"]
existing = {v for r in old for v in [r.get("resolved_prefab"), r.get("full_ref")] if v}
index = read(W / "diagnostics/world_npc_idle_20261026_02/world/registry_index_01.json")
global_refs = {r["ref"] for r in index["refs"]}
candidates = []
for hit in sorted(hits[186:], key=lambda h: h["depot"]):
    for path, node in sorted(all_graph_nodes[hit["depot"]].items()):
        for prefab in node["phaseInstancePrefabs"]:
            authored = prefab["prefabNodeRef"]["$value"]
            resolved = [authored] if authored.startswith("$/") else sorted(r for r in global_refs if r.endswith("/" + authored))
            refs = refs_for(hit["depot"], node)
            candidate_refs = set()
            for full in resolved:
                for ref in refs:
                    if ref.startswith("$/"): candidate_refs.add(ref)
                    elif ref.startswith("#"): candidate_refs.add(full + "/" + ref)
                candidate_refs |= {r for r in global_refs if r.startswith(full + "/") and ("_com" in r.rsplit("/", 1)[-1] or "community" in r.rsplit("/", 1)[-1])}
            candidates.append({"id": 1200 + len(candidates), "native_resource": hit["depot"], "native_binary": hit["copy"],
                               "native_binary_sha256": hit["sha256"], "source": hit["copy"] + ".json", "node_path": path,
                               "authored_prefab": authored, "resolved_prefabs": resolved,
                               "existing_prefab": any(r in existing for r in resolved), "reference_candidates": sorted(candidate_refs),
                               "native_refs": sorted(refs), "payload": node})
raw = {"status": "PASS_NATIVE_CE_PHASE_CLOSURE_INVENTORY_NOT_ADMISSION", "archives": 128, "resources": 247,
       "unread_external_phases": [], "combat_nodes": len(combat), "combat": combat, "new_prefab_rows": len(candidates),
       "already_known_prefab_rows": sum(r["existing_prefab"] for r in candidates), "candidates": candidates, "pins": pins,
       "game_writes": 0, "save_writes": 0}
(H / "closure_01.json").write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8", newline="\n")
registry = [{"id": r["id"], "prefab": r["resolved_prefabs"][0], "refs": r["reference_candidates"]}
            for r in candidates if len(r["resolved_prefabs"]) == 1 and not r["existing_prefab"]]
(H / "registry_candidates_01.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"resources": 247, "new_prefab_rows": len(candidates), "known": raw["already_known_prefab_rows"],
                  "registry_candidates": len(registry), "combat_nodes": len(combat),
                  "params": dict(collections.Counter(r["node"].get("params", {}).get("$type", "Attitude") for r in combat))}))
