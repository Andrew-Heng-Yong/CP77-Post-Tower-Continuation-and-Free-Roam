"""Classify extracted regional vendor scenes by *structural* one-shop shape.

Read-only. A matching shape is not a runtime-success or safety determination.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "research/b0_vendor_rollout"
ROWS = json.loads((BASE / "regional_vendor_inventory.json").read_text(encoding="utf-8"))
SOURCES = BASE / "regional_sources/json"


def graph_at(source: str, route: str) -> dict:
    path = SOURCES / (source.replace("\\", "/") + ".json")
    graph = json.loads(path.read_text(encoding="utf-8"))["Data"]["RootChunk"]["graph"]["Data"]
    for part in route.split("/")[1:]:
        target = int(part.removeprefix("node"))
        node = next(n["Data"] for n in graph["nodes"] if n["Data"]["id"] == target)
        graph = node["phaseGraph"]["Data"]
    return graph


def node_types(graph: dict) -> Counter:
    return Counter(node["Data"]["$type"] for node in graph["nodes"])


def main() -> None:
    by_scene = defaultdict(list)
    for row in ROWS:
        by_scene[row["scene"]].append(row)
    result = []
    for scene, occurrences in sorted(by_scene.items()):
        row = occurrences[0]
        graph = graph_at(row["source"], row["graph"])
        shape = node_types(graph)
        exact_seven = shape == Counter({
            "questInputNodeDefinition": 1,
            "questOutputNodeDefinition": 1,
            "questSceneNodeDefinition": 1,
            "questSpawnManagerNodeDefinition": 2,
            "questPauseConditionNodeDefinition": 2,
        })
        one_spawn_pair = (len(row["spawn_activate"]) == 1 and
                          len(row["spawn_deactivate"]) == 1 and
                          row["spawn_activate"][0]["entry"] == row["spawn_deactivate"][0]["entry"] and
                          row["spawn_activate"][0]["reference"] == row["spawn_deactivate"][0]["reference"])
        name = Path(scene.replace("\\", "/")).stem.lower()
        if "ripdoc" in name or "ripperdoc" in name:
            category = "ripperdoc"
        elif "netrun" in name:
            category = "netrunner"
        elif "medic" in name:
            category = "medical"
        elif "cloth" in name:
            category = "clothing"
        elif "gunsmith" in name:
            category = "gunsmith"
        elif "melee" in name:
            category = "melee"
        elif "food" in name:
            category = "food"
        elif "junk" in name:
            category = "junk"
        elif "tech" in name:
            category = "tech"
        else:
            category = "unknown"
        result.append({
            "scene": scene, "source": row["source"], "graph": row["graph"],
            "category": category, "occurrences": len(occurrences),
            "exact_seven_node_shape": exact_seven,
            "one_matching_spawn_pair": one_spawn_pair,
            "local_fact_writes": row["local_fact_writes"],
            "structural_candidate": len(occurrences) == 1 and exact_seven and one_spawn_pair and not row["local_fact_writes"],
        })
    (BASE / "vendor_template_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Distinct scene resources: {len(result)}")
    print("Seven-node shape:", sum(r["exact_seven_node_shape"] for r in result))
    print("Unique-branch, matching-spawn structural candidates:", sum(r["structural_candidate"] for r in result))
    print("Candidate categories:", dict(sorted(Counter(r["category"] for r in result if r["structural_candidate"]).items())))


if __name__ == "__main__":
    main()
