"""Bounded source evidence for the reported wall gap and crowd crossing.

This writes a research report only. It never modifies game resources or state.
"""
from __future__ import annotations

import base64
import json
import math
import struct
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/misty_viktor_world"
VANILLA = AUDIT / "r6_wall_nav_sources/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/ep1/quest_bb3937b6e34a251c.streamingsector.json"
POINTS = {"wall_gap": [-1570.2421875, 1210.5838623, 16.99893],
          "npc_crossing": [-1544.0529785, 1174.8182373, 17.1723],
          "police_scene": [-1548.42639, 1172.786865, 16.32562]}


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def val(p):
    return p.get("$value", p) if isinstance(p, dict) else p


def xyz(p):
    return [p[k] for k in ("X", "Y", "Z")]


def main():
    plan = read(AUDIT / "street_selection_plan.json")
    root = read(VANILLA)["Data"]["RootChunk"]
    native_node = root["nodes"][62]["Data"]
    native_data = root["nodeData"]["Data"][62]
    assert native_node["$type"] == "worldCrowdNullAreaNode"
    buf = base64.b64decode(native_node["outline"]["Data"]["buffer"])
    count, = struct.unpack_from("<I", buf)
    outline = [struct.unpack_from("<4f", buf, 4 + 16*i) for i in range(count)]
    height, = struct.unpack_from("<f", buf, 4 + 16*count)
    assert count == 4 and len(buf) == 4 + 16*count + 4
    pos, scale = xyz(native_data["Position"]), xyz(native_data["Scale"])
    q = native_data["Orientation"]
    assert q["i"] == q["j"] == 0
    angle = 2*math.atan2(q["k"], q["r"])
    ca, sa = math.cos(angle), math.sin(angle)
    corners = [[pos[0] + ca*p[0]*scale[0] - sa*p[1]*scale[1],
                pos[1] + sa*p[0]*scale[0] + ca*p[1]*scale[1],
                pos[2] + p[2]*scale[2]] for p in outline]
    bounds = {"min": [min(p[k] for p in corners) for k in range(3)],
              "max": [max(p[k] for p in corners) for k in range(3)]}
    bounds["max"][2] += height*scale[2]
    point_checks = {}
    for key, point in POINTS.items():
        dx, dy, dz = [point[k]-pos[k] for k in range(3)]
        local = [(ca*dx + sa*dy)/scale[0], (-sa*dx + ca*dy)/scale[1], dz/scale[2]]
        point_checks[key] = {"position": point, "local": local,
                             "inside_xy": abs(local[0]) <= 1 and abs(local[1]) <= 1,
                             "inside_z": 0 <= local[2] <= height}

    pending_near_wall, selected_near_wall, collision_near_points = [], [], []
    for group in plan["source_ranges"]:
        for name, output in (("selected", selected_near_wall), ("pending_payload_audit", pending_near_wall)):
            for row in group[name]:
                d = math.dist(POINTS["wall_gap"], row["position"])
                if d < 12:
                    output.append(dict(sector=group["source_sector"], distance=round(d, 3), **row))
        sector_path = ROOT / "research/phase2b_p4/variant_sectors/ep1_1_nightcity/json" / (group["source_sector"] + ".json")
        sector = read(sector_path)["Data"]["RootChunk"]
        for row in group["selected"]:
            if row["type"] != "worldCollisionNode":
                continue
            node = sector["nodes"][row["node_index"]]["Data"]
            actors = node.get("compiledData", {}).get("Data", {}).get("Actors", [])
            for actor_index, actor in enumerate(actors):
                p = [actor["Position"][k]["Bits"]/131072 for k in ("x", "y", "z")]
                matches = {k: round(math.dist(p, point), 3) for k, point in POINTS.items()
                           if math.dist(p, point) < 8}
                if matches:
                    collision_near_points.append({"sector": group["source_sector"],
                                                  "data_index": row["data_index"], "node_index": row["node_index"],
                                                  "actor_index": actor_index, "position": p, "near": matches,
                                                  "shape_types": dict(Counter(s["ShapeType"] for s in actor["Shapes"]))})

    r5_art = []
    for p in AUDIT.glob("variants_r5_street_*.json"):
        sector = read(p)["Data"]["RootChunk"]
        for d in sector["nodeData"]["Data"]:
            n = sector["nodes"][d["NodeIndex"]]["Data"]
            if n["$type"] == "worldStaticMeshNode":
                r5_art.append((xyz(d["Position"]), val(n.get("mesh", {}).get("DepotPath"))))
    original_wall_meshes = [r for r in selected_near_wall if r["type"] == "worldStaticMeshNode" and
                            not any(k in r["name"] for k in ("police_tape", "police_signage", "ncpd_logo"))]
    original_wall_missing = [r for r in original_wall_meshes if not any(
        math.dist(r["position"], p) < .001 and r.get("mesh") == m for p, m in r5_art)]
    assert not original_wall_missing, original_wall_missing

    result = {"status": "STATIC_SOURCE_AUDIT_NOT_RUNTIME_PROOF", "reported_points": POINTS,
              "source_sector": str(VANILLA.relative_to(ROOT)),
              "source_node_counts": dict(Counter(n["Data"]["$type"] for n in root["nodes"])),
              "native_crowd_area": {"node_and_data_index": 62, "node_ref": val(native_data["QuestPrefabRefHash"]),
                                    "position": pos, "rotation_degrees": math.degrees(angle), "scale": scale,
                                    "outline_points_decoded": outline, "outline_height_decoded": height,
                                    "world_corners": corners, "world_aabb": bounds,
                                    "point_checks": point_checks,
                                    "IsForBlockade": native_node["IsForBlockade"],
                                    "permanentlyEnabledByDefault": native_node["permanentlyEnabledByDefault"],
                                    "activation": {"resource": "q307_05_alley.questphase", "nested_node": 10, "enable": 1},
                                    "release": {"resource": "q307_cleanup.questphase", "root_node": 26, "enable": 0}},
              "retained_static_wall_area_meshes_within_12m": sorted(original_wall_meshes, key=lambda r:r["distance"]),
              "retained_static_wall_area_mesh_count": len(original_wall_meshes),
              "missing_from_r5": original_wall_missing,
              "omitted_nodes_within_12m": sorted(pending_near_wall, key=lambda r:r["distance"]),
              "collision_actors_within_8m": collision_near_points,
              "conclusions": [
                  "The null area was not copied in R3/R5 and vanilla cleanup disables its ending owner.",
                  "The reported NPC position lies inside the vanilla q307 alley null area including its vertical span.",
                  "No non-police q307_misty_alley static mesh with origin within 12m of the wall point is absent from R5.",
                  "Nearby omitted TriggerNotifier_BarbedWire triggers affect TC_Player damage, not crowd navigation.",
                  "A null area can be a local crowd-exclusion candidate; these files do not prove rerouting, cleanup of already spawned pedestrians or behavior of non-crowd NPCs.",
                  "Wall gap repair requires identifying the absent surface/streaming instance; player position alone cannot name a missing mesh. Do not add speculative walls or copy whole quest staging."
              ]}
    (AUDIT / "r6_wall_nav_audit.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"source_null_index":62, "bounds": bounds, "point_checks":point_checks,
                      "wall_meshes_retained":len(original_wall_meshes), "wall_meshes_missing":0,
                      "omitted_types_near_wall":dict(Counter(r["type"] for r in pending_near_wall)),
                      "near_collision_actors":len(collision_near_points)}, indent=2))


if __name__ == "__main__":
    main()
