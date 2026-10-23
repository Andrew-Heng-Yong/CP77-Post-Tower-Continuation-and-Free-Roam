#!/usr/bin/env python3
"""Create compact graph summaries from analyze_q307.py's analysis.json output."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def compact_details(details: dict[str, Any]) -> str:
    omitted = {"$type"}
    return json.dumps(
        {key: value for key, value in details.items() if key not in omitted},
        sort_keys=True,
        separators=(",", ":"),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", type=Path)
    parser.add_argument("resource")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    data = json.loads(args.analysis.read_text(encoding="utf-8"))
    nodes = [row for row in data["nodes"] if row["resource"] == args.resource]
    edges = [row for row in data["edges"] if row["resource"] == args.resource]
    if not nodes:
        raise SystemExit(f"Resource not indexed: {args.resource}")

    args.output.mkdir(parents=True, exist_ok=True)
    incoming: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    outgoing: dict[tuple[str, Any], list[dict[str, Any]]] = defaultdict(list)
    for edge in edges:
        incoming[(edge["graph"], edge["destination_node_id"])].append(edge)
        outgoing[(edge["graph"], edge["source_node_id"])].append(edge)

    node_rows: list[dict[str, Any]] = []
    for node in sorted(nodes, key=lambda row: (row["graph"], int(row["node_id"]))):
        key = (node["graph"], node["node_id"])
        node_rows.append(
            {
                "graph": node["graph"],
                "node_id": node["node_id"],
                "node_type": node["node_type"],
                "incoming": "|".join(
                    f"{edge['source_node_id']}:{edge.get('source_socket', '')}->{edge.get('destination_socket', '')}"
                    for edge in incoming[key]
                ),
                "outgoing": "|".join(
                    f"{edge.get('source_socket', '')}->{edge['destination_node_id']}:{edge.get('destination_socket', '')}"
                    for edge in outgoing[key]
                ),
                "details": compact_details(node["details"]),
            }
        )

    with (args.output / "nodes.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=node_rows[0].keys())
        writer.writeheader()
        writer.writerows(node_rows)

    graphs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        graphs[node["graph"]].append(node)
    graph_rows = []
    for graph, graph_nodes in sorted(graphs.items()):
        graph_edges = [edge for edge in edges if edge["graph"] == graph]
        types = Counter(node["node_type"] for node in graph_nodes)
        graph_rows.append(
            {
                "graph": graph,
                "node_count": len(graph_nodes),
                "edge_count": len(graph_edges),
                "node_types": "|".join(f"{key}:{value}" for key, value in sorted(types.items())),
            }
        )
    with (args.output / "graphs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=graph_rows[0].keys())
        writer.writeheader()
        writer.writerows(graph_rows)

    print(f"Resource: {args.resource}")
    print(f"Graphs: {len(graph_rows)}")
    print(f"Nodes: {len(node_rows)}")
    print(f"Edges: {len(edges)}")


if __name__ == "__main__":
    main()
