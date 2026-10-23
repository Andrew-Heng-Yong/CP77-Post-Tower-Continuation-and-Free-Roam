"""Targeted, read-only queries over existing WolvenKit exports; no game access."""
import argparse
import json
import re
from pathlib import Path
from analyze_q307 import walk


def flatten(value, prefix=""):
    if isinstance(value, dict):
        if "$value" in value:
            return {prefix: value["$value"]}
        result = {}
        for key, child in value.items():
            if key not in {"sockets", "connections", "phaseGraph", "nodes", "HandleId", "HandleRefId"}:
                result.update(flatten(child, f"{prefix}.{key}".strip(".")))
        return result
    if isinstance(value, list):
        result = {}
        for i, child in enumerate(value):
            result.update(flatten(child, f"{prefix}.{i}"))
        return result
    return {prefix: value}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("root", type=Path)
    p.add_argument("--match", required=True, help="Case-insensitive scalar value substring")
    p.add_argument("--file", default="*.json")
    p.add_argument("--keys", help="Only output flattened data keys matching this regex")
    args = p.parse_args()
    for path in sorted(args.root.rglob(args.file)):
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
        seen = set()
        for obj, loc, ancestors in walk(doc):
            if not any(args.match.lower() in str(v).lower() for v in obj.values() if not isinstance(v, (dict, list))):
                continue
            lineage = [v for v in (*ancestors, obj) if "$type" in v]
            owner = next((v for v in reversed(lineage) if ("Node" in v["$type"] and "id" in v) or v["$type"].endswith("Event")), obj)
            key = id(owner)
            if key in seen:
                continue
            seen.add(key)
            data = flatten(owner)
            if args.keys:
                data = {k:v for k,v in data.items() if re.search(args.keys,k)}
            print(json.dumps({"file": str(path.relative_to(args.root)), "path": ".".join(map(str,loc)),
                "ancestors": [{"type": v["$type"], "id": v.get("id", v.get("nodeId"))} for v in lineage if "Node" in v["$type"] or "Event" in v["$type"]],
                "data": data}, separators=(",", ":")))


if __name__ == "__main__":
    main()
