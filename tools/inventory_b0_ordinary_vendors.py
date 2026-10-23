"""Inventory vendor scene/spawn leaves from the 16 regional vanilla owners.

This is read-only analysis of previously extracted WolvenKit JSON. It does not
classify a scene as post-Tower-safe or generate a restoration package.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "research/b0_vendor_rollout/regional_sources/json"
OUTPUT = ROOT / "research/b0_vendor_rollout"


def value(item):
    if isinstance(item, dict):
        return item.get("$value", item)
    return item


def children(graph, path):
    nodes = [item["Data"] for item in graph.get("nodes", [])]
    yield path, nodes
    for node in nodes:
        phase = (node.get("phaseGraph") or {}).get("Data")
        if isinstance(phase, dict) and "nodes" in phase:
            yield from children(phase, f"{path}/node{node['id']}")


def describe(graph_nodes, source, graph_path):
    scenes = []
    spawns = []
    facts = []
    for node in graph_nodes:
        kind = node.get("$type")
        if kind == "questSceneNodeDefinition":
            depot = value((node.get("sceneFile") or {}).get("DepotPath"))
            if isinstance(depot, str) and depot.startswith("base\\open_world\\vendors\\"):
                scenes.append((node["id"], depot, value((node.get("sceneLocation") or {}).get("nodeRef"))))
        elif kind == "questSpawnManagerNodeDefinition":
            for action in node.get("actions") or []:
                data = (action.get("type") or {}).get("Data") or {}
                if data.get("$type") == "questSpawnSet_NodeType":
                    spawns.append({
                        "node": node["id"], "action": data.get("action", ""),
                        "reference": value(data.get("reference")),
                        "entry": value(data.get("entryName")),
                        "phase": value(data.get("phaseName")),
                    })
        elif kind == "questFactsDBManagerNodeDefinition":
            name = ((node.get("type") or {}).get("Data") or {}).get("factName")
            if name:
                facts.append(name)
    if not scenes:
        return []
    return [{
        "source": source, "graph": graph_path, "scene_node": node_id,
        "scene": scene, "scene_location": location,
        "spawn_activate": [s for s in spawns if s["action"] in ("Activate", "Reactivate")],
        "spawn_deactivate": [s for s in spawns if s["action"] == "Deactivate"],
        "local_fact_writes": sorted(set(facts)),
    } for node_id, scene, location in scenes]


def main():
    files = sorted(SOURCE.rglob("*.questphase.json"))
    if len(files) != 16:
        raise SystemExit(f"Expected 16 extracted regional owners, found {len(files)}")
    rows = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        source = str(path.relative_to(SOURCE)).removesuffix(".json").replace("/", "\\")
        graph = data["Data"]["RootChunk"]["graph"]["Data"]
        for graph_path, nodes in children(graph, "root"):
            rows.extend(describe(nodes, source, graph_path))
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "regional_vendor_inventory.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (OUTPUT / "regional_vendor_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "source", "graph", "scene_node", "scene", "scene_location",
            "spawn_activate", "spawn_deactivate", "local_fact_writes",
        ))
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key], ensure_ascii=False) if isinstance(row[key], list)
                             else row[key] for key in writer.fieldnames})
    counts = Counter(row["source"].split("\\")[3] for row in rows)
    print(f"Regional roots: {len(files)}; vendor-scene leaves: {len(rows)}")
    print("District counts:", ", ".join(f"{name}={count}" for name, count in sorted(counts.items())))
    print("Leaves with no same-graph spawn activation:",
          sum(not row["spawn_activate"] for row in rows))


if __name__ == "__main__":
    main()
