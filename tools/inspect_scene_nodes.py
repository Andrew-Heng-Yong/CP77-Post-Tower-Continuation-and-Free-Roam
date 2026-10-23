"""Print compact predecessor/successor and quest action detail for scene IDs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def unwrap(value: object) -> object:
    return value.get("$value", value) if isinstance(value, dict) else value


def pick(value: object, key: str) -> list[object]:
    result = []
    if isinstance(value, dict):
        if key in value:
            result.append(unwrap(value[key]))
        for item in value.values():
            result.extend(pick(item, key))
    elif isinstance(value, list):
        for item in value:
            result.extend(pick(item, key))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("ids", nargs="+", type=int)
    args = parser.parse_args()
    root = json.loads(args.scene.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
    nodes = {item["Data"]["nodeId"]["id"]: item["Data"]
             for item in root["sceneGraph"]["Data"]["graph"]}
    incoming: dict[int, list[int]] = defaultdict(list)
    outgoing: dict[int, list[int]] = defaultdict(list)
    for node_id, node in nodes.items():
        for socket in node.get("outputSockets", []):
            for target in socket.get("destinations", []):
                dest = target["nodeId"]["id"]
                outgoing[node_id].append(dest)
                incoming[dest].append(node_id)
    for node_id in args.ids:
        node = nodes[node_id]
        quest = node.get("questNode", {}).get("Data", {})
        action = quest.get("type", {}).get("Data", {})
        print(json.dumps({
            "id": node_id, "type": node["$type"],
            "in": incoming[node_id], "out": outgoing[node_id],
            "quest": quest.get("$type"), "action": action.get("$type"),
            "condition": quest.get("condition", {}).get("Data", {}).get("$type"),
            "facts": pick(node, "factName"), "refs": pick(action, "nodeRef"),
            "variants": pick(action, "variantName"),
            "captions": [unwrap(option.get("caption")) for option in node.get("options", [])],
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
