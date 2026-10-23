"""Read-only mapping of candle-like shop placements to vanilla variant owners."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "research/phase2b_p4/variant_sectors/ep1_1_nightcity/json"
BLOCKS = ROOT / "research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default"
POINT = (-1546.1812744141, 1192.9306640625, 16.259811401367)

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]

def val(x):
    return x.get("$value", x) if isinstance(x, dict) else x

def main():
    results = []
    for block_rel in ("blocks/all.streamingblock.json", "ep1/blocks/all.streamingblock.json"):
        block = read(BLOCKS / block_rel)
        for descriptor_index, descriptor in enumerate(block["descriptors"]):
            sector_name = val(descriptor["data"]["DepotPath"])
            if not sector_name.endswith(("interior_-49_37_0_0.streamingsector", "interior_-49_38_0_0.streamingsector")):
                continue
            path = BASE / (sector_name + ".json")
            if not path.exists():
                continue
            sector = read(path)
            starts = sector["variantIndices"]
            variants = {}
            for variant in descriptor.get("variants", []):
                variants.setdefault(variant["rangeIndex"], []).append({
                    "name": val(variant["name"]), "owner": val(variant["nodeRef"]),
                    "enabled_by_default": variant["enabledByDefault"]})
            ri = 0
            for index, datum in enumerate(sector["nodeData"]["Data"]):
                while ri + 1 < len(starts) and starts[ri + 1] <= index:
                    ri += 1
                node = sector["nodes"][datum["NodeIndex"]]["Data"]
                if "candle" not in json.dumps(node, ensure_ascii=False).lower():
                    continue
                position = [datum["Position"][k] for k in ("X", "Y", "Z")]
                distance = math.dist(position, POINT)
                if distance > 25:
                    continue
                results.append({"block": block_rel, "descriptor": descriptor_index,
                                "sector": sector_name, "data_index": index,
                                "node_index": datum["NodeIndex"], "type": node["$type"],
                                "name": val(node.get("debugName")), "position": position,
                                "distance_to_player": round(distance, 3), "range_index": ri,
                                "variants": variants.get(ri, [])})
    result = {"player_position": POINT, "matches": sorted(results, key=lambda r: r["distance_to_player"])}
    out = ROOT / "research/misty_viktor_world/candle_source_audit.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"matches": len(results), "nearest": result["matches"][:10], "output": str(out)}, indent=2))

if __name__ == "__main__":
    main()
