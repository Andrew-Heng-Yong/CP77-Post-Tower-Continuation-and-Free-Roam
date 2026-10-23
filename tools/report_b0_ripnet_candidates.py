"""Read-only structural report for simple regional ripperdoc/netrunner leaves."""

from __future__ import annotations

import json
from pathlib import Path

from audit_b0_vendor_templates import BASE, graph_at
from audit_wilson_vendor_owner import graph_edges, walk
from report_scene_route import scalars


def node_map(graph: dict) -> dict[int, dict]:
    return {n["Data"]["id"]: n["Data"] for n in graph["nodes"]}


def spec(row: dict) -> dict:
    parts = row["graph"].split("/")
    outer = graph_at(row["source"], "/".join(parts[:-1]))
    outer_nodes = node_map(outer)
    phase_id = int(parts[-1].removeprefix("node"))
    inner = graph_at(row["source"], row["graph"])
    inner_nodes = node_map(inner)
    resource_path = BASE / "regional_sources/json" / (row["source"].replace("\\", "/") + ".json")
    resource = json.loads(resource_path.read_text())
    handles = {str(v["HandleId"]): v["Data"] for v in walk(resource)
               if "HandleId" in v and "Data" in v}
    inner_edges = [(e["source_node_id"], e["source_socket"], e["destination_node_id"], e["destination_socket"])
                   for e in graph_edges(inner, row["scene"], handles)]
    outer_dist = [n for n in outer_nodes.values()
                  if n["$type"] == "questPauseConditionNodeDefinition" and
                  "Less" in set(map(str, scalars(n, "comparisonType"))) and
                  50 in set(scalars(n, "distanceValue"))]
    inner_close = [n for n in inner_nodes.values()
                   if n["$type"] == "questPauseConditionNodeDefinition" and
                   "Less" in set(map(str, scalars(n, "comparisonType"))) and
                   12 in set(scalars(n, "distanceValue"))]
    inner_far = [n for n in inner_nodes.values()
                 if n["$type"] == "questPauseConditionNodeDefinition" and
                 "Greater" in set(map(str, scalars(n, "comparisonType"))) and
                 50 in set(scalars(n, "distanceValue"))]
    scene = inner_nodes[row["scene_node"]]
    scene_sockets = [s["Data"]["name"]["$value"] for s in scene["sockets"]
                     if "Data" in s]
    return {
        "id": row["spawn_activate"][0]["entry"],
        "source": row["source"], "outer_graph": "/".join(parts[:-1]),
        "outer_phase_id": phase_id,
        "outer_50_node": [n["id"] for n in outer_dist],
        "outer_facts": sorted(set(map(str, scalars(outer, "factName")))),
        "outer_nodes": [(n["id"], n["$type"]) for n in outer_nodes.values()],
        "inner_nodes": sorted(inner_nodes),
        "inner_close_12_node": [n["id"] for n in inner_close],
        "inner_far_50_node": [n["id"] for n in inner_far],
        "scene_node": row["scene_node"], "scene_sockets": scene_sockets,
        "inner_edges": sorted(inner_edges),
        "scene": row["scene"], "marker": row["scene_location"],
        "spawn": row["spawn_activate"][0], "despawn": row["spawn_deactivate"][0],
        "panel_records": sorted(set(map(str, scalars(scene, "vendorID")))),
    }


def main() -> None:
    audit = json.loads((BASE / "vendor_template_audit.json").read_text())
    selected = {item["scene"] for item in audit
                if item["structural_candidate"] and item["category"] in {"ripperdoc", "netrunner", "tech"}}
    rows = json.loads((BASE / "regional_vendor_inventory.json").read_text())
    report = [spec(row) for row in rows if row["scene"] in selected]
    assert len(report) == 10, len(report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
