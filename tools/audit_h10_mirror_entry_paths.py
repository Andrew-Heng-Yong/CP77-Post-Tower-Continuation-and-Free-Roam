"""Compare executable mirror paths with scene choice-attachment links."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from test_b0_h10_mirror_prompt import nodes, read


def path(graph: dict, start: int, target: int, *, attachments: bool) -> list[int] | None:
    queue = deque([(start,)])
    visited: set[int] = set()
    while queue:
        route = queue.popleft()
        current = route[-1]
        if current == target:
            return list(route)
        if current in visited:
            continue
        visited.add(current)
        for socket in graph[current].get("outputSockets", []):
            for edge in socket.get("destinations", []):
                if not attachments and edge["isockStamp"]["name"] == 1:
                    continue
                next_id = edge["nodeId"]["id"]
                if next_id not in visited:
                    queue.append((*route, next_id))
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("scene", type=Path)
    parser.add_argument("--start", type=int, default=220)
    parser.add_argument("--targets", type=int, nargs="+", default=[226, 1125, 1246, 1156, 1423, 1617])
    args = parser.parse_args()
    graph = nodes(read(args.scene))
    for target in args.targets:
        for attachments in (False, True):
            route = path(graph, args.start, target, attachments=attachments)
            print(f"{target} attachments={attachments}: {route}")


if __name__ == "__main__":
    main()
