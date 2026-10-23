#!/usr/bin/env python3
"""Trace a bounded forward or reverse slice from a quest-graph node CSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict, deque
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("nodes_csv", type=Path)
    parser.add_argument("graph")
    parser.add_argument("start", type=int)
    parser.add_argument("--depth", type=int, default=8)
    parser.add_argument("--reverse", action="store_true")
    args = parser.parse_args()

    rows = [row for row in csv.DictReader(args.nodes_csv.open(encoding="utf-8-sig")) if row["graph"] == args.graph]
    by_id = {int(row["node_id"]): row for row in rows}
    adjacency: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        source = int(row["node_id"])
        field = "incoming" if args.reverse else "outgoing"
        for token in row[field].split("|"):
            if not token:
                continue
            if args.reverse:
                other = int(token.split(":", 1)[0])
            else:
                other = int(token.split("->", 1)[1].split(":", 1)[0])
            adjacency[source].append(other)

    queue = deque([(args.start, 0)])
    seen: set[int] = set()
    while queue:
        node_id, depth = queue.popleft()
        if node_id in seen or depth > args.depth:
            continue
        seen.add(node_id)
        row = by_id[node_id]
        print(
            f"depth={depth}\tnode={node_id}\t{row['node_type']}\t"
            f"IN[{row['incoming']}] OUT[{row['outgoing']}]\t{row['details']}"
        )
        for target in adjacency[node_id]:
            queue.append((target, depth + 1))


if __name__ == "__main__":
    main()
