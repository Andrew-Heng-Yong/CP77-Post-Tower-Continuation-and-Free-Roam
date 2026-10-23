"""List world-sector nodes near a position without dumping the whole sector."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def compact(value: object, key: str) -> list[str]:
    found = []
    if isinstance(value, dict):
        if key in value:
            item = value[key]
            if isinstance(item, dict):
                item = item.get("$value", item)
            found.append(str(item))
        for item in value.values():
            found.extend(compact(item, key))
    elif isinstance(value, list):
        for item in value:
            found.extend(compact(item, key))
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sector", type=Path)
    parser.add_argument("x", type=float)
    parser.add_argument("y", type=float)
    parser.add_argument("z", type=float)
    parser.add_argument("--radius", type=float, default=12)
    parser.add_argument("--types", help="Comma-separated node types to include")
    args = parser.parse_args()
    allowed = set(args.types.split(",")) if args.types else None
    root = json.loads(args.sector.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
    nodes = [item["Data"] for item in root["nodes"]]
    data = root["nodeData"]
    if isinstance(data, dict):
        data = data["Data"]
    rows = []
    for item in data:
        position = item["Position"]
        distance = math.dist((position["X"], position["Y"], position["Z"]),
                             (args.x, args.y, args.z))
        if distance > args.radius:
            continue
        node = nodes[item["NodeIndex"]]
        if allowed is not None and node["$type"] not in allowed:
            continue
        rows.append({
            "distance": round(distance, 2),
            "xyz": [round(position[k], 2) for k in ("X", "Y", "Z")],
            "type": node["$type"],
            "name": compact(node, "debugName")[:2],
            "resources": compact(node, "DepotPath")[:3],
            "refs": compact(item, "QuestPrefabRefHash")[:2],
        })
    for row in sorted(rows, key=lambda row: row["distance"]):
        print(json.dumps(row, ensure_ascii=False))
    print(f"nearby_nodes={len(rows)}")


if __name__ == "__main__":
    main()
