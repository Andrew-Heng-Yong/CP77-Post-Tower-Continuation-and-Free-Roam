"""Print a shortest graph path between scene node IDs with compact node details."""

from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("start", type=int)
    parser.add_argument("target", type=int)
    args = parser.parse_args()
    root = json.loads(args.scene.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
    nodes = {item["Data"]["nodeId"]["id"]: item["Data"] for item in root["sceneGraph"]["Data"]["graph"]}
    outgoing: dict[int, list[int]] = {}
    for node_id, node in nodes.items():
        outgoing[node_id] = [target["nodeId"]["id"] for socket in node.get("outputSockets", [])
                             for target in socket.get("destinations", [])]
    queue = deque([args.start])
    parents = {args.start: None}
    while queue and args.target not in parents:
        source = queue.popleft()
        for target in outgoing[source]:
            if target not in parents:
                parents[target] = source
                queue.append(target)
    if args.target not in parents:
        raise SystemExit("target unreachable")
    path = []
    current = args.target
    while current is not None:
        path.append(current)
        current = parents[current]
    for node_id in reversed(path):
        node = nodes[node_id]
        quest = node.get("questNode", {}).get("Data", {})
        action = quest.get("type", {}).get("Data", {})
        print(json.dumps({"id": node_id, "type": node["$type"], "action": action.get("$type"),
                          "events": [event["Data"]["$type"] for event in node.get("events", [])],
                          "choices": [option.get("caption", {}).get("$value") for option in node.get("options", [])]},
                         ensure_ascii=False))


if __name__ == "__main__":
    main()
