"""Read-only reachable-node report for a WolvenKit-exported .scene JSON file."""

import argparse
import json
from collections import deque
from pathlib import Path


def unwrap(value):
    return value.get("$value") if isinstance(value, dict) and "$value" in value else value


def scalars(value, key):
    if isinstance(value, dict):
        for name, child in value.items():
            if name == key:
                yield unwrap(child)
            yield from scalars(child, key)
    elif isinstance(value, list):
        for child in value:
            yield from scalars(child, key)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("scene", type=Path)
    ap.add_argument("--entry", default="in_mirror")
    ap.add_argument("--node", type=int, help="Start from this graph node instead of a named entry")
    ap.add_argument("--summary", action="store_true", help="Print only choices, fact refs, and count")
    args = ap.parse_args()
    doc = json.loads(args.scene.read_text(encoding="utf-8-sig"))
    scene = doc["Data"]["RootChunk"]
    entry = args.node if args.node is not None else next(
        p["nodeId"]["id"] for p in scene["entryPoints"] if unwrap(p["name"]) == args.entry
    )
    nodes = {n["Data"]["nodeId"]["id"]: n["Data"] for n in scene["sceneGraph"]["Data"]["graph"]}
    edges = {
        node_id: [d["nodeId"]["id"] for socket in node.get("outputSockets", []) for d in socket.get("destinations", [])]
        for node_id, node in nodes.items()
    }
    seen = set()
    queue = deque([entry])
    while queue:
        node_id = queue.popleft()
        if node_id in seen:
            continue
        seen.add(node_id)
        queue.extend(edges.get(node_id, []))
    records = []
    for node_id in sorted(seen):
        node = nodes[node_id]
        quest = node.get("questNode", {}).get("Data", {})
        records.append({
            "id": node_id,
            "type": node["$type"],
            "quest_type": quest.get("$type"),
            "condition_type": quest.get("condition", {}).get("Data", {}).get("$type"),
            "action_type": quest.get("type", {}).get("Data", {}).get("$type"),
            "facts": sorted({str(x) for x in scalars(quest, "factName")}),
            "captions": sorted({str(unwrap(o.get("caption"))) for o in node.get("options", [])}),
            "targets": edges.get(node_id, []),
        })
    report = {
        "source": str(args.scene),
        "entry": args.entry if args.node is None else None,
        "entry_node": entry,
        "reachable_count": len(seen),
        "end_nodes_reachable": [p["id"] for p in scene["sceneGraph"]["Data"].get("endNodes", []) if p["id"] in seen],
        "records": records,
    }
    if args.summary:
        report["choices"] = [
            {"id": p["id"], "captions": p["captions"], "targets": p["targets"]}
            for p in records if p["type"] == "scnChoiceNode"
        ]
        report["facts"] = sorted({name for p in records for name in p["facts"]})
        report.pop("records")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
