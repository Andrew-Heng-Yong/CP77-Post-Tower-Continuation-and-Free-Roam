#!/usr/bin/env python3
"""Emit focused q307 post-credit lifecycle reports from analyze_q307.py output."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


INTERNET = (
    r"ep1\gameplay\gui\world\internet\internet_2_years_later"
    r"\internet_2_years_later.questphase"
)
ENDING = r"ep1\quest\main_quests\q307\phases\q307_ending_board.questphase"
FINAL_BOARDS = r"base\quest\main_quests\epilogue\final_boards.questphase"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def reachable(start: int, edges: list[dict[str, Any]]) -> set[int]:
    adjacency: dict[int, list[int]] = defaultdict(list)
    for edge in edges:
        adjacency[int(edge["source_node_id"])].append(int(edge["destination_node_id"]))
    seen: set[int] = set()
    queue = deque([start])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(adjacency[current])
    return seen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    data = json.loads(args.analysis.read_text(encoding="utf-8"))
    nodes: list[dict[str, Any]] = data["nodes"]
    edges: list[dict[str, Any]] = data["edges"]

    internet_nodes = [n for n in nodes if n["resource"] == INTERNET]
    internet_edges = [e for e in edges if e["resource"] == INTERNET]
    reached = reachable(0, internet_edges)
    incoming: dict[int, list[dict[str, Any]]] = defaultdict(list)
    outgoing: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in internet_edges:
        incoming[int(edge["destination_node_id"])].append(edge)
        outgoing[int(edge["source_node_id"])].append(edge)

    internet_outgoing = outgoing
    internet_rows: list[dict[str, Any]] = []
    for node in sorted(internet_nodes, key=lambda item: int(item["node_id"])):
        node_id = int(node["node_id"])
        details = node["details"]
        internet_rows.append(
            {
                "node_id": node_id,
                "node_type": node["node_type"],
                "reachable_from_input": node_id in reached,
                "incoming_sockets": "|".join(
                    sorted(str(e.get("destination_socket", "")) for e in incoming[node_id])
                ),
                "outgoing_nodes": "|".join(
                    str(e["destination_node_id"]) for e in outgoing[node_id]
                ),
                "journal_path": details.get("type.Data.path.Data.realPath", ""),
                "fact": details.get("condition.Data.type.Data.factName", ""),
                "comparison": details.get("condition.Data.type.Data.comparisonType", ""),
                "value": details.get("condition.Data.type.Data.value", ""),
                "delay_seconds": details.get("condition.Data.type.Data.seconds", ""),
                "output_type": details.get("type", ""),
            }
        )
    write_csv(args.output / "internet_2_years_later_nodes.csv", internet_rows)

    lifecycle_rows: list[dict[str, Any]] = []
    for resource in (ENDING, FINAL_BOARDS):
        top_graph = f"{resource}::Data.RootChunk.graph.Data"
        resource_nodes = [n for n in nodes if n["resource"] == resource and n["graph"] == top_graph]
        resource_edges = [e for e in edges if e["resource"] == resource and e["graph"] == top_graph]
        incoming = defaultdict(list)
        outgoing = defaultdict(list)
        for edge in resource_edges:
            incoming[int(edge["destination_node_id"])].append(edge)
            outgoing[int(edge["source_node_id"])].append(edge)
        for node in sorted(resource_nodes, key=lambda item: int(item["node_id"])):
            node_id = int(node["node_id"])
            lifecycle_rows.append(
                {
                    "resource": resource,
                    "node_id": node_id,
                    "node_type": node["node_type"],
                    "incoming": "|".join(
                        f"{e['source_node_id']}:{e.get('source_socket', '')}->{e.get('destination_socket', '')}"
                        for e in incoming[node_id]
                    ),
                    "outgoing": "|".join(
                        f"{e.get('source_socket', '')}->{e['destination_node_id']}:{e.get('destination_socket', '')}"
                        for e in outgoing[node_id]
                    ),
                    "details": json.dumps(node["details"], sort_keys=True, separators=(",", ":")),
                }
            )
    write_csv(args.output / "final_boards_lifecycle_nodes.csv", lifecycle_rows)

    owner_terms = (
        "restriction",
        "hud",
        "phone",
        "inventory",
        "save",
        "vehicle",
        "fasttravel",
        "fast travel",
        "crowd",
        "traffic",
        "worldinteraction",
        "contenttoken",
        "pause",
        "tier",
        "scenario",
        "fade",
        "showworld",
        "map_blocked",
        "hub_disabled",
    )
    restriction_rows: list[dict[str, Any]] = []
    for node in nodes:
        if "q307" not in node["resource"] and node["resource"] != FINAL_BOARDS:
            continue
        detail_text = json.dumps(node["details"], sort_keys=True, separators=(",", ":"))
        lowered = detail_text.lower().replace("_", "")
        if not any(term.replace("_", "") in lowered for term in owner_terms):
            continue
        restriction_rows.append(
            {
                "resource": node["resource"],
                "graph": node["graph"],
                "node_id": node["node_id"],
                "node_type": node["node_type"],
                "details": detail_text,
            }
        )
    write_csv(args.output / "restriction_owner_nodes.csv", restriction_rows)

    summary = {
        "internet_node_count": len(internet_nodes),
        "internet_edge_count": len(internet_edges),
        "internet_reachable_node_count": len(reached),
        "internet_output_nodes": [
            n["node_id"] for n in internet_nodes if n["node_type"] == "questOutputNodeDefinition"
        ],
        "internet_reachable_output_nodes": [
            n["node_id"]
            for n in internet_nodes
            if n["node_type"] == "questOutputNodeDefinition" and int(n["node_id"]) in reached
        ],
        "internet_terminal_reachable_nodes": sorted(
            node_id for node_id in reached if not internet_outgoing[node_id]
        ),
        "restriction_rows": len(restriction_rows),
    }
    (args.output / "postcredits_targeted_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
