"""Identify only the two user-reported omitted construction piles.

Read official extracted resources and prepared R6 exports. Write research only.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/misty_viktor_world"
DEPOT = r"base\worlds\03_night_city\_compiled\default\ep1\exterior_-25_18_0_0.streamingsector"
SOURCE = ROOT / "research/phase2b_p4/variant_sectors/ep1_1_nightcity"
SELECT = {575: "hotel", 580: "hotel", 897: "hotel", 578: "pallet", 581: "pallet", 901: "pallet"}
POINTS = {"hotel": [-1543.0413818359, 1182.2197265625, 17.047134399414],
          "pallet": [-1561.0388183594, 1206.59765625, 16.594467163086]}


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def val(v):
    return v.get("$value", v) if isinstance(v, dict) else v


def walk(v):
    if isinstance(v, dict):
        yield v
        for x in v.values():
            yield from walk(x)
    elif isinstance(v, list):
        for x in v:
            yield from walk(x)


def xyz(v):
    return [v[k] for k in "XYZ"]


def rotate(q, v):
    u, w = [q[k] for k in ("i", "j", "k")], q["r"]
    uv, uu = sum(a*b for a, b in zip(u, v)), sum(a*a for a in u)
    cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
    return [2*uv*u[i] + (w*w-uu)*v[i] + 2*w*cross[i] for i in range(3)]


def transform_point(t, p):
    off = rotate(t["orientation"], p)
    return [a+b for a, b in zip(xyz(t["position"]), off)]


def aabb(points):
    return {"min": [min(p[k] for p in points) for k in range(3)],
            "max": [max(p[k] for p in points) for k in range(3)]}


def main():
    raw = SOURCE / "raw" / DEPOT
    source = read(SOURCE / "json" / (DEPOT + ".json"))
    s = source["Data"]["RootChunk"]
    handles = {x["HandleId"]: x["Data"] for x in walk(s) if "HandleId" in x and "Data" in x}
    plan = read(OUT / "street_selection_plan.json")
    all_groups = [g for g in plan["source_ranges"] if g["source_sector"] == DEPOT]
    block_path = ROOT / all_groups[0]["source_block"]
    block = read(block_path)["Data"]["RootChunk"]
    rows = []
    meshes = {}
    for index, point_name in SELECT.items():
        nd = s["nodeData"]["Data"][index]
        n = s["nodes"][nd["NodeIndex"]]["Data"]
        assert n["$type"] == "worldInstancedDestructibleMeshNode"
        assert n["isDestructible"] == n["isWorkspot"] == n["isHostOnly"] == 0
        assert val(n["idleEffect"]["DepotPath"]) == val(n["fracturingEffect"]["DepotPath"]) == "0"
        assert val(nd["QuestPrefabRefHash"]) == val(nd["UkHash1"]) == "0"
        buf = n["cookedInstanceTransforms"]
        shared = buf["sharedDataBuffer"]
        shared = handles[shared["HandleRefId"]] if "HandleRefId" in shared else shared["Data"]
        transforms = shared["buffer"]["Data"]["Transforms"][buf["startIndex"]:buf["startIndex"]+buf["numElements"]]
        assert len(transforms) == buf["numElements"]
        assert len(n["instanceTransforms"]) == 0
        pos, scale = xyz(nd["Position"]), xyz(nd["Scale"])
        assert scale == [1, 1, 1]
        positions = [[a+b for a, b in zip(pos, rotate(nd["Orientation"], xyz(t["position"])))] for t in transforms]
        group = next(g for g in all_groups if g["range"][0] <= index < g["range"][1])
        assert any(x["data_index"] == index for x in group["pending_payload_audit"])
        descriptor = block["descriptors"][group["descriptor_index"]]
        mesh = val(n["mesh"]["DepotPath"])
        mesh_file = OUT / "r7_construction_sources/json" / (mesh + ".json")
        corners = None
        if mesh_file.exists():
            mesh_data = read(mesh_file)["Data"]["RootChunk"]
            bounds = mesh_data["boundingBox"]
            corners = list(itertools.product(*zip(xyz(bounds["Min"]), xyz(bounds["Max"]))))
            mesh_deps = sorted(set(val(v["DepotPath"]) for v in walk(mesh_data) if "DepotPath" in v and val(v["DepotPath"]) != "0"))
            meshes[mesh] = {"bounding_box": bounds, "resource_dependencies": mesh_deps,
                            "parameters": [v.get("Data", {}).get("$type") for v in mesh_data.get("parameters", [])],
                            "file": str(mesh_file.relative_to(ROOT))}
        world_corners = []
        if corners:
            for t in transforms:
                for corner in corners:
                    local = transform_point(t, corner)
                    world_corners.append([a+b for a, b in zip(pos, rotate(nd["Orientation"], local))])
        rows.append({"point_name": point_name, "data_index": index, "node_index": nd["NodeIndex"],
                     "type": n["$type"], "name": val(n["debugName"]), "mesh": mesh,
                     "source_prefab_hash": n["sourcePrefabHash"], "node": n, "placement": nd,
                     "source_descriptor_index": group["descriptor_index"], "descriptor": descriptor,
                     "variant": group["variant"], "source_range": group["range"],
                     "transform_start": buf["startIndex"], "transform_count": len(transforms),
                     "local_transforms": transforms, "instance_positions": positions,
                     "instance_origins_aabb": aabb(positions),
                     "mesh_world_aabb": aabb(world_corners) if world_corners else None,
                     "reported_point_distance_to_closest_origin": min(math.dist(p, POINTS[point_name]) for p in positions)})
    assert sum(x["transform_count"] for x in rows) == 18
    all_nodes = [x["node"] for x in rows]
    # Search the whole already audited source selection for siblings and LOD copies.
    sibling_rows = [dict(source_sector=g["source_sector"], selection=bucket, **n)
                    for g in plan["source_ranges"] for bucket in ("selected", "pending_payload_audit")
                    for n in g[bucket] if n.get("mesh") in meshes]
    record = {"status": "SOURCE_AUDITED_TWO_PILES_NOT_INSTALLED_OR_LIVE",
              "source_sector": DEPOT, "source_raw": str(raw.relative_to(ROOT)),
              "source_sha256": hashlib.sha256(raw.read_bytes()).hexdigest().upper(),
              "source_block": str(block_path.relative_to(ROOT)), "reported_points": POINTS,
              "selected_rows": rows, "mesh_dependencies": meshes,
              "same_mesh_members_in_all_q307_misty_alley_ranges": sibling_rows,
              "selected_node_count": 6, "selected_node_data_count": 6, "visible_mesh_instances": 18,
              "collision_policy": "Preserve original physics-bearing node type/filter/simulation and vanilla mesh collision resources. Do not flatten to render-only static meshes or add guessed collision. Mesh bounds are resource AABBs transformed through local cooked and outer instance transforms.",
              "scope_limit": "Two exact reported piles only. All six source placements were omitted by passive-only R3 selection, retained omitted in R6. No standalone scene, entity, workspot, actor, trigger, light, audio, or fact dependency is in these nodes.",
              "build_plan": "Six native cloned instanced mesh nodes, six cloned placements, trim shared transform buffer to exactly 18 selected transforms; retain exact physics/filter fields, clear original source prefab identities, assign private IDs, default-empty controlled range1 under existing PTFRMV_TowerStreet. No original variant toggles or core R6 changes."}
    (OUT / "r7_construction_audit.json").write_text(json.dumps(record, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "nodes": 6, "instances": 18,
                      "meshes": len(meshes), "source_sha256": record["source_sha256"],
                      "piles": [{k: r[k] for k in ("point_name", "data_index", "node_index", "name", "transform_count", "instance_origins_aabb", "mesh_world_aabb")} for r in rows]}, indent=2))


if __name__ == "__main__":
    main()
