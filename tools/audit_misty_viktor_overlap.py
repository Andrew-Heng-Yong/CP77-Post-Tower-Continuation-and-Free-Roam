"""Read-only inventory of local default dressing versus the R3 street copy."""
import json
import math
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "research/phase2b_p4/staging_scan/ep1_1_nightcity/json"
PLAN = ROOT / "research/misty_viktor_world/street_selection_plan.json"
AREA = lambda p: -1590 <= p[0] <= -1520 and 1150 <= p[1] <= 1250 and 5 <= p[2] <= 35
KEYWORDS = ("police", "crime", "tape", "barrier", "fence", "wall", "construction", "evidence", "scaffold", "ncpd", "shutter", "door", "tripod", "body_bag", "floodlight")

def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))

def val(x):
    return x.get("$value", x) if isinstance(x, dict) else x

def inspect(sector, start, end):
    rows = []
    for i in range(start, end):
        datum = sector["nodeData"]["Data"][i]
        node = sector["nodes"][datum["NodeIndex"]]["Data"]
        p = [datum["Position"][k] for k in ("X", "Y", "Z")]
        if not AREA(p):
            continue
        row = {"data_index": i, "type": node["$type"], "name": val(node.get("debugName")), "position": p}
        for field in ("mesh", "entityTemplate", "material", "effect", "resource"):
            asset = node.get(field)
            if isinstance(asset, dict):
                row[field] = val(asset.get("DepotPath"))
        rows.append(row)
    return rows

def main():
    old = []
    default = []
    block_paths = [SCAN / "base/worlds/03_night_city/_compiled/default/blocks/all.streamingblock.json",
                   SCAN / "base/worlds/03_night_city/_compiled/default/ep1/blocks/all.streamingblock.json"]
    for block_path in block_paths:
      block = read(block_path)["Data"]["RootChunk"]
      for di, desc in enumerate(block["descriptors"]):
          sector_path = val(desc["data"]["DepotPath"])
          if not sector_path.endswith((
              "exterior_-25_18_0_0.streamingsector", "exterior_-25_19_0_0.streamingsector",
              "exterior_-30_10_0_0.streamingsector", "exterior_-30_11_0_0.streamingsector",
              "exterior_-13_9_0_1.streamingsector", "exterior_-8_2_0_2.streamingsector",
              "exterior_-7_4_0_2.streamingsector", "exterior_-4_2_0_3.streamingsector",
          )):
                continue
          resource = next((p for p in (
              SCAN / (sector_path + ".json"),
              ROOT / "research/phase2b_p4/variant_sectors/ep1_1_nightcity/json" / (sector_path + ".json"),
              ROOT / "research/misty_viktor_world/overlap_ep1_sources/json" / (sector_path + ".json"),
          ) if p.exists()), None)
          if resource is None:
              continue
          sector = read(resource)["Data"]["RootChunk"]
          data = sector["nodeData"]["Data"]
          starts = sector["variantIndices"]
          default += [dict(sector=sector_path, **m) for m in inspect(sector, starts[0], starts[1])]
          for variant in desc.get("variants", []):
              name = val(variant["name"])
              if name not in ("q307_misty_alley_hide", "q307_misty_scene", "q307_misty_scene_hide", "q307_final_scene_hide"):
                  continue
              ri = variant["rangeIndex"]
              end = starts[ri + 1] if ri + 1 < len(starts) else len(data)
              members = inspect(sector, starts[ri], end)
              old.append({"descriptor": di, "sector": sector_path, "variant": name,
                          "enabled_by_default": variant["enabledByDefault"],
                          "owner": val(variant["nodeRef"]), "range": [starts[ri], end],
                          "all_count": end - starts[ri], "local_count": len(members),
                          "local_types": dict(Counter(m["type"] for m in members)),
                          "members": members})
    plan = read(PLAN)
    added = [dict(sector=r["source_sector"], **m) for r in plan["source_ranges"] for m in r["selected"]
             if AREA(m["position"])]
    police = [dict(sector=r["source_sector"], **m) for r in plan["source_ranges"] for m in r["selected"]
              if any(k in str(m["name"]).lower() for k in ("police_tape", "police_signage", "ncpd_logo"))]
    assert len(police) == 24 and sum(r["variant"] == "q307_misty_alley_hide" for r in old) == 15
    overlap = []
    for a in added:
        if a["type"] not in ("worldStaticMeshNode", "worldStaticDecalNode"):
            continue
        for b in default:
            if b["type"] != a["type"] or not b["sector"].split("\\")[-1] == a["sector"].split("\\")[-1]:
                continue
            distance = math.dist(a["position"], b["position"])
            if distance < 0.25:
                overlap.append({"distance": round(distance, 4), "r3": a, "default": b})
    def matched(row):
        return any(k in (str(row.get("name", "")) + " " + str(row.get("mesh", ""))).lower() for k in KEYWORDS)
    result = {"scope": "local clinic/street box only; static source membership, not runtime visibility",
              "area": {"x": [-1590, -1520], "y": [1150, 1250], "z": [5, 35]},
              "old_or_default_ranges": old,
              "unconditional_default_count_in_area": len(default),
              "unconditional_default_types": dict(Counter(m["type"] for m in default)),
              "unconditional_default_lexical_candidates": [m for m in default if matched(m)],
              "unconditional_near_police_tape_a": [m for m in default
                                                     if math.dist(m["position"], [-1553.69458, 1180.20056, 16.50178]) < 24
                                                     and m["type"] not in ("worldStaticDecalNode", "worldCollisionNode")],
              "unconditional_near_pairs_under_25cm": overlap,
              "r3_added_count_in_area": len(added),
              "r3_police_scene_candidates": police,
              "r3_added_types": dict(Counter(m["type"] for m in added)),
              "r3_lexical_candidates": [m for m in added if matched(m)],
              "old_lexical_candidates": [dict(variant=r["variant"], sector=r["sector"], **m)
                                          for r in old for m in r["members"] if matched(m)]}
    out = ROOT / "research/misty_viktor_world/overlap_source_audit.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"old_ranges": len(old), "old_local_nodes": sum(r["local_count"] for r in old),
                      "old_variants": dict(Counter(r["variant"] for r in old)),
                      "r3_local_nodes": len(added), "unconditional_default_nodes": len(default),
                      "r3_police_scene_candidates": len(police),
                      "unconditional_near_pairs_under_25cm": len(overlap),
                      "unconditional_default_keyword_candidates": len(result["unconditional_default_lexical_candidates"]),
                      "r3_keyword_candidates": len(result["r3_lexical_candidates"]),
                      "old_keyword_candidates": len(result["old_lexical_candidates"]),
                      "output": str(out)}, indent=2))

if __name__ == "__main__":
    main()
