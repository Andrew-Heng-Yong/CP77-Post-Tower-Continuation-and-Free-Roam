"""Compact normal-world marker/device evidence from WolvenKit sector exports."""
import argparse
import json
from collections import Counter
from pathlib import Path


def value(item):
    return item.get("$value", item) if isinstance(item, dict) else item


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--match", default="fast_travel|dataterm|StaticMarker|StartPoint")
    args = parser.parse_args()
    import re
    pattern = re.compile(args.match, re.I)
    results = []
    for path in args.files:
        root = json.loads(path.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]
        nodes = root["nodes"]
        found = []
        for di, data in enumerate(root["nodeData"]["Data"]):
            ni = data["NodeIndex"]
            node = nodes[ni].get("Data", {})
            if not pattern.search(json.dumps(node)) and not pattern.search(json.dumps(data)):
                continue
            chunks = node.get("instanceData", {}).get("Data", {}).get("buffer", {}).get("Data", {}).get("Chunks", [])
            found.append({"node_data": di, "node_index": ni, "node_type": node.get("$type"),
                          "ref": value(data.get("QuestPrefabRefHash")), "data": data,
                          "node_fields": {k: v for k, v in node.items() if k != "instanceData"},
                          "device_links": [{"type": c.get("$type"),
                                            "linkedFastTravelPoint": c.get("linkedFastTravelPoint"),
                                            "exitNode": c.get("exitNode")}
                                           for c in chunks if "linkedFastTravelPoint" in c]})
        results.append({"file": str(path), "root_type": root.get("$type"),
                        "type_counts": Counter(n.get("Data", {}).get("$type") for n in nodes), "matches": found})
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
