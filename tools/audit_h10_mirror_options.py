"""Summarize vanilla H10 mirror option subgraphs before they rejoin the mirror loop."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from report_scene_route import scalars, unwrap
from test_b0_h10_mirror_prompt import nodes, read, targets


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene", type=Path)
    args = parser.parse_args()
    graph = nodes(read(args.scene))
    stops = {2, 220, 226, 509}
    for start in (1125, 1246, 1250):
        seen: set[int] = set()
        queue = deque([start])
        while queue:
            node_id = queue.popleft()
            if node_id in seen:
                continue
            seen.add(node_id)
            if node_id not in stops:
                queue.extend(targets(graph[node_id]))
        print(f"ENTRY {start}: {len(seen)} nodes, returns {sorted(seen & stops)}")
        for node_id in sorted(seen):
            node = graph[node_id]
            quest = node.get("questNode", {}).get("Data", {})
            action = quest.get("type", {}).get("Data", {})
            condition = quest.get("condition", {}).get("Data", {})
            choices = [unwrap(option.get("caption")) for option in node.get("options", [])]
            facts = sorted({str(value) for value in scalars(quest, "factName")})
            bits = [str(node_id), node["$type"]]
            if quest:
                bits.append(f"quest={quest.get('$type')}")
            if action:
                bits.append(f"action={action.get('$type')}")
            if condition:
                bits.append(f"condition={condition.get('$type')}")
            if facts:
                bits.append(f"facts={','.join(facts)}")
            if choices:
                bits.append(f"choices={','.join(choices)}")
            bits.append(f"next={','.join(map(str, targets(node)))}")
            print("  " + " ".join(bits))


if __name__ == "__main__":
    main()
