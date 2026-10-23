#!/usr/bin/env python3
"""Build deterministic indexes from WolvenKit JSON exports of q307 resources."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


def walk(value: Any, path: tuple[Any, ...] = (), ancestors: tuple[dict[str, Any], ...] = ()):
    if isinstance(value, dict):
        yield value, path, ancestors
        next_ancestors = ancestors + (value,)
        for key, child in value.items():
            yield from walk(child, path + (key,), next_ancestors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (index,), ancestors)


def unwrap(wrapper: Any, handles: dict[str, dict[str, Any]]) -> tuple[str | None, dict[str, Any] | None]:
    if not isinstance(wrapper, dict):
        return None, None
    if "HandleId" in wrapper and isinstance(wrapper.get("Data"), dict):
        return str(wrapper["HandleId"]), wrapper["Data"]
    if "HandleRefId" in wrapper:
        handle_id = str(wrapper["HandleRefId"])
        return handle_id, handles.get(handle_id)
    return None, wrapper


def cname(value: Any) -> str | None:
    if isinstance(value, dict) and "$value" in value:
        return str(value["$value"])
    if value is None:
        return None
    return str(value)


def nearest_node(ancestors: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    for ancestor in reversed(tuple(ancestors)):
        node_type = ancestor.get("$type", "")
        if node_type.endswith("NodeDefinition") and "id" in ancestor:
            return ancestor
    return None


def scalar_details(value: Any, prefix: str = "", depth: int = 0) -> dict[str, Any]:
    if depth > 5:
        return {}
    output: dict[str, Any] = {}
    if isinstance(value, dict):
        if "$type" in value and "$value" in value:
            output[prefix.rstrip(".")] = value["$value"]
            return output
        for key, child in value.items():
            if key in {"sockets", "connections", "phaseGraph", "nodes"}:
                continue
            if key in {"HandleId", "HandleRefId"}:
                continue
            child_prefix = f"{prefix}{key}."
            if isinstance(child, (str, int, float, bool)) or child is None:
                output[child_prefix.rstrip(".")] = child
            elif isinstance(child, (dict, list)):
                output.update(scalar_details(child, child_prefix, depth + 1))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            output.update(scalar_details(child, f"{prefix}{index}.", depth + 1))
    return output


def classify_fact(container_type: str, node_type: str) -> str:
    joined = f"{container_type} {node_type}".lower()
    if "manager" in joined or "setvar" in joined:
        return "write"
    if "condition" in joined or "comparison" in joined:
        return "read"
    return "unknown"


def path_text(path: tuple[Any, ...]) -> str:
    return ".".join(str(part) for part in path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    json_files = sorted(args.input.rglob("*.json"))
    args.output.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"resources": [], "facts": [], "references": [], "nodes": [], "edges": []}

    for json_path in json_files:
        document = json.loads(json_path.read_text(encoding="utf-8-sig"))
        relative = json_path.relative_to(args.input).as_posix()
        resource_path = relative.removesuffix(".json").replace("/", "\\")

        handles: dict[str, dict[str, Any]] = {}
        for obj, _, _ in walk(document):
            if "HandleId" in obj and isinstance(obj.get("Data"), dict):
                handles[str(obj["HandleId"])] = obj["Data"]

        root = document.get("Data", {}).get("RootChunk", {})
        type_counts: Counter[str] = Counter()
        resource_refs: set[str] = set()
        fact_count = 0

        for obj, obj_path, ancestors in walk(document):
            object_type = str(obj.get("$type", ""))
            if object_type:
                type_counts[object_type] += 1

            if object_type == "ResourcePath" and isinstance(obj.get("$value"), str):
                resource_refs.add(obj["$value"])

            if "factName" in obj:
                node = nearest_node(ancestors)
                node_type = str(node.get("$type", "")) if node else ""
                node_id = node.get("id") if node else None
                details = scalar_details(obj)
                result["facts"].append(
                    {
                        "resource": resource_path,
                        "access": classify_fact(object_type, node_type),
                        "fact": str(obj["factName"]),
                        "container_type": object_type,
                        "node_type": node_type,
                        "node_id": node_id,
                        "value": details.get("value"),
                        "set_exact_value": details.get("setExactValue"),
                        "comparison_type": details.get("comparisonType"),
                        "json_path": path_text(obj_path),
                    }
                )
                fact_count += 1

        for reference in sorted(resource_refs):
            result["references"].append({"resource": resource_path, "reference": reference})

        graph_count = 0
        node_count = 0
        edge_count = 0
        for graph, graph_path, _ in walk(document):
            if graph.get("$type") != "questGraphDefinition" or not isinstance(graph.get("nodes"), list):
                continue
            graph_count += 1
            graph_name = f"{resource_path}::{path_text(graph_path)}"
            direct_nodes: dict[str, dict[str, Any]] = {}
            socket_owner: dict[str, str] = {}

            for wrapper in graph["nodes"]:
                handle_id, node = unwrap(wrapper, handles)
                if handle_id is None or node is None:
                    continue
                direct_nodes[handle_id] = node
                for socket_wrapper in node.get("sockets", []):
                    socket_handle, _ = unwrap(socket_wrapper, handles)
                    if socket_handle:
                        socket_owner[socket_handle] = handle_id

            for handle_id, node in direct_nodes.items():
                node_type = str(node.get("$type", ""))
                details = scalar_details(node)
                result["nodes"].append(
                    {
                        "resource": resource_path,
                        "graph": graph_name,
                        "handle_id": handle_id,
                        "node_id": node.get("id"),
                        "node_type": node_type,
                        "debug": node.get("debugString"),
                        "phase_resource": details.get("phaseResource.DepotPath"),
                        "scene_resource": details.get("sceneFile.DepotPath") or details.get("sceneResource.DepotPath"),
                        "details": details,
                    }
                )
                node_count += 1

                for socket_wrapper in node.get("sockets", []):
                    socket_handle, socket = unwrap(socket_wrapper, handles)
                    if not socket_handle or not socket:
                        continue
                    # REDengine stores each connection on both endpoint sockets.
                    # Index only forward flow from output sockets to avoid reverse/self duplicates.
                    if socket.get("type") != "Output":
                        continue
                    source_socket_name = cname(socket.get("name"))
                    for connection_wrapper in socket.get("connections", []):
                        _, connection = unwrap(connection_wrapper, handles)
                        if not connection:
                            continue
                        destination_wrapper = connection.get("destination")
                        destination_socket_handle, destination_socket = unwrap(destination_wrapper, handles)
                        destination_node_handle = socket_owner.get(destination_socket_handle or "")
                        if not destination_node_handle:
                            continue
                        result["edges"].append(
                            {
                                "resource": resource_path,
                                "graph": graph_name,
                                "source_handle": handle_id,
                                "source_node_id": node.get("id"),
                                "source_type": node_type,
                                "source_socket": source_socket_name,
                                "destination_handle": destination_node_handle,
                                "destination_node_id": direct_nodes[destination_node_handle].get("id"),
                                "destination_type": direct_nodes[destination_node_handle].get("$type"),
                                "destination_socket": cname(destination_socket.get("name")) if destination_socket else None,
                            }
                        )
                        edge_count += 1

        result["resources"].append(
            {
                "resource": resource_path,
                "root_type": root.get("$type"),
                "fact_occurrences": fact_count,
                "resource_reference_count": len(resource_refs),
                "graph_count": graph_count,
                "node_count": node_count,
                "edge_count": edge_count,
                "top_types": type_counts.most_common(20),
            }
        )

    (args.output / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    table_fields = {
        "resources.csv": ["resource", "root_type", "fact_occurrences", "resource_reference_count", "graph_count", "node_count", "edge_count"],
        "facts.csv": ["resource", "access", "fact", "container_type", "node_type", "node_id", "value", "set_exact_value", "comparison_type", "json_path"],
        "references.csv": ["resource", "reference"],
        "nodes.csv": ["resource", "graph", "handle_id", "node_id", "node_type", "debug", "phase_resource", "scene_resource"],
        "edges.csv": ["resource", "graph", "source_handle", "source_node_id", "source_type", "source_socket", "destination_handle", "destination_node_id", "destination_type", "destination_socket"],
    }
    for filename, fields in table_fields.items():
        key = filename.removesuffix(".csv")
        with (args.output / filename).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(result[key])

    print(f"Indexed {len(result['resources'])} resources")
    print(f"Fact occurrences: {len(result['facts'])}")
    print(f"Resource references: {len(result['references'])}")
    print(f"Quest nodes: {len(result['nodes'])}")
    print(f"Quest edges: {len(result['edges'])}")


if __name__ == "__main__":
    main()
