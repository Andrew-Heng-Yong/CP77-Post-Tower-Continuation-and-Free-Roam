"""Catalogue vendor scene occurrences and their immediate/ancestor context.

Analysis only: ancestry facts are context, not proven executable guard predicates.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "research/b0_vendor_rollout"


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def unwrap(value):
    return value.get("$value", value) if isinstance(value, dict) else value


def local_context(nodes):
    facts, spawns, prefabs = set(), [], set()
    for node in nodes:
        # Exclude embedded children so the context has an unambiguous graph owner.
        own = {k: v for k, v in node.items() if k not in ("phaseGraph", "sockets")}
        for obj in walk(own):
            if "factName" in obj:
                facts.add(str(unwrap(obj["factName"])))
            if "prefabNodeRef" in obj:
                prefabs.add(str(unwrap(obj["prefabNodeRef"])))
            if obj.get("$type") == "questSpawnSet_NodeType":
                spawns.append({key: unwrap(obj.get(key)) for key in
                               ("action", "reference", "entryName", "phaseName")})
    return {"facts": sorted(facts), "spawn_actions": spawns, "prefabs": sorted(prefabs)}


def visit(graph, source, route="root", parents=()):
    nodes = [h["Data"] for h in graph.get("nodes", []) if "Data" in h]
    ctx = local_context(nodes)
    for node in nodes:
        if node.get("$type") == "questSceneNodeDefinition":
            scene = unwrap((node.get("sceneFile") or {}).get("DepotPath"))
            if isinstance(scene, str) and ("\\vendors\\" in scene or any(
                name in scene for name in ("victor_vector_default", "claire_default", "nix_default", "elcoyote_barman")
            )):
                yield {"source": source, "graph": route, "scene_node": node["id"],
                       "scene": scene, "scene_location": unwrap((node.get("sceneLocation") or {}).get("nodeRef")),
                       "local": ctx, "ancestor_context": list(parents)}
        child = (node.get("phaseGraph") or {}).get("Data")
        if isinstance(child, dict) and "nodes" in child:
            yield from visit(child, source, f"{route}/node{node['id']}",
                             (*parents, {"graph": route, **ctx}))


def main():
    sources = []
    for directory in (OUT / "regional_sources/json", OUT / "expanded_sources/json"):
        sources.extend((path, str(path.relative_to(directory)).removesuffix(".json").replace("/", "\\"))
                       for path in sorted(directory.rglob("*.questphase.json")))
    default = ROOT / "research/phase2b_p4/vendor_owner/json/base/quest/default_dialogs.questphase.json"
    sources.append((default, "base\\quest\\default_dialogs.questphase"))
    rows = []
    for path, source in sources:
        root = json.loads(path.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
        rows.extend(visit(root["graph"]["Data"], source))
    (OUT / "expanded_service_inventory.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    with (OUT / "expanded_service_inventory.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=("source", "graph", "scene_node", "scene", "scene_location", "local", "ancestor_context"))
        writer.writeheader()
        writer.writerows({k: json.dumps(v) if isinstance(v, (dict, list)) else v for k, v in row.items()} for row in rows)
    print(f"{len(sources)} sources; {len(rows)} scene occurrences; {len(set(r['scene'] for r in rows))} distinct scenes")
    for source in sorted(set(r["source"] for r in rows if r["source"].startswith("ep1") or r["source"].endswith("default_dialogs.questphase"))):
        sites = {r["scene"] for r in rows if r["source"] == source}
        print(source, len(sites))
        for scene in sorted(sites):
            print(" ", scene)
    scene_audit = []
    scene_paths = []
    for scene_root in (OUT / "special_scene_sources/json", OUT / "regional_scene_sources/json"):
        scene_paths.extend((path, scene_root) for path in sorted(scene_root.rglob("*.scene.json")))
    for path, scene_root in scene_paths:
        root = json.loads(path.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
        facts, vendors, writes = set(), set(), []
        for obj in walk(root):
            if "factName" in obj:
                facts.add(str(unwrap(obj["factName"])))
                if obj.get("$type") == "questSetVar_NodeType":
                    writes.append({k: obj.get(k) for k in ("factName", "value", "setExactValue")})
            for value in obj.values():
                if isinstance(value, str) and value.startswith("Vendors."):
                    vendors.add(value)
        controls = []
        for handle in root.get("sceneGraph", {}).get("Data", {}).get("graph", []):
            node = handle.get("Data", {})
            qnode = node.get("questNode", {}).get("Data", {})
            controls.append({"id": node.get("nodeId", {}).get("id"), "type": node.get("$type"),
                             "action_type": qnode.get("type", {}).get("Data", {}).get("$type"),
                             "quest_type": qnode.get("$type"),
                             "facts": sorted({str(o["factName"]) for o in walk(qnode) if "factName" in o}),
                             "targets": [d["nodeId"]["id"] for sock in node.get("outputSockets", []) for d in sock.get("destinations", [])]})
        scene_audit.append({
            "scene": str(path.relative_to(scene_root)).removesuffix(".json").replace("/", "\\"),
            "actors": [a.get("actorName") for a in root.get("actors", [])],
            "vendor_ids": sorted(vendors), "facts": sorted(facts), "fact_writes": writes,
            "entrypoints": [{"name": unwrap(e["name"]), "node": e["nodeId"]["id"]} for e in root.get("entryPoints", [])],
            "control_flow": controls,
        })
    (OUT / "service_scene_audit.json").write_text(json.dumps(scene_audit, indent=2) + "\n", encoding="utf-8")
    print(f"Scene audit: {len(scene_audit)} resources; fact mentions are not necessarily reachable")
    indexed = {item["scene"]: item for item in scene_audit}
    expected = {row["scene"] for row in rows}
    assert len(indexed) == len(scene_audit), "Duplicate scene audit resources"
    assert expected == set(indexed), "Owner inventory and scene audit coverage differ"
    lines = [
        "# Vendor service resource index", "",
        "Generated by `tools/inventory_b0_vendor_services.py`. Analysis only; not an enable list.", "",
        f"{len(sources)} questphase inputs; {len(rows)} scene occurrences; {len(indexed)} unique scene resources.", "",
        "An actor label is not necessarily an NPC identity. A fact mention is not a proven gate, "
        "and absence of a literal Vendor ID does not prove that no service exists. "
        "See [restoration plan](vendor_restoration_plan.md) for reviewed classifications. "
        "The Johnny Easter egg is intentionally inventoried but excluded from restoration.", "",
    ]
    for scene, item in sorted(indexed.items()):
        filename = scene.rsplit("\\", 1)[-1]
        links = []
        for directory in ("special_scene_sources", "regional_scene_sources"):
            relative = directory + "/json/" + scene.replace("\\", "/") + ".json"
            if (OUT / relative).exists():
                links.append(f"[export]({relative})")
        owners = [row for row in rows if row["scene"] == scene]
        lines.extend([
            f"## {filename}", "",
            f"Resource: `{scene}` ({', '.join(links)}).", "",
            "- Actors: " + (", ".join(f"`{a}`" for a in item["actors"]) or "none listed") + ".",
            "- Literal vendor records: " + (", ".join(f"`{v}`" for v in item["vendor_ids"]) or "none found") + ".",
            "- Fact mentions: " + (", ".join(f"`{f}`" for f in item["facts"]) or "none found") + ".",
            f"- Fact-write nodes found: {len(item['fact_writes'])} (reachability not implied).",
            "- Owner occurrences:",
        ])
        for row in owners:
            lines.append(f"  - `{row['source']}` / `{row['graph']}` / scene node `{row['scene_node']}`.")
        lines.append("")
    (OUT / "service_resource_index.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
