"""Independent normalized-matrix check of authored P4 sidewalk support.

Consumes extracted evidence only; no game access or runtime operations. The
geometry derivation deliberately does not import the original ray implementation.
"""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/phase2b_p4"


def xyz(v):
    return [v[k] for k in "XYZ"]


def matrix(q):
    x, y, z, w = (q[k] for k in ("i", "j", "k", "r"))
    n = math.sqrt(x*x+y*y+z*z+w*w)
    x, y, z, w = x/n, y/n, z/n, w/n
    return [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
            [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
            [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]


def mv(m, v):
    return [sum(a*b for a,b in zip(row, v)) for row in m]


def mm(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def add(a, b):
    return [x+y for x,y in zip(a,b)]


def main():
    evidence = json.loads((OUT / "destination_support_evidence.json").read_text())
    destination = next(r for r in evidence if r["key"] == "wat_lch_dataterm_11")
    sector = destination["sectors"][1]
    hit = sector["box_hits"][0]
    actor, shape = hit["actor_data"], hit["shape_data"]
    origin = [actor["Position"][k]["Bits"]/131072 for k in "xyz"]
    assert xyz(actor["Scale"]) == [1, 1, 1]
    ar = matrix(actor["Orientation"])
    rotation = mm(ar, matrix(shape["Rotation"]))
    center = add(origin, mv(ar, xyz(shape["Position"])))
    axes = [[rotation[i][j] for i in range(3)] for j in range(3)]
    extents = xyz(shape["Size"])
    face_axis = max(range(3), key=lambda i: abs(axes[i][2]))
    sign = 1 if axes[face_axis][2] > 0 else -1
    normal = [v*sign for v in axes[face_axis]]
    face_center = add(center, [v*extents[face_axis] for v in normal])
    marker = destination["marker"]["position"]
    horizontal_axes = [i for i in range(3) if i != face_axis]
    samples = []
    for dx in (-.3, 0., .3):
        for dy in (-.3, 0., .3):
            x, y = marker[0]+dx, marker[1]+dy
            z = face_center[2] - (normal[0]*(x-face_center[0])+normal[1]*(y-face_center[1]))/normal[2]
            rel = [x-center[0], y-center[1], z-center[2]]
            local = [dot(axis, rel) for axis in axes]
            margins = [extents[i]-abs(local[i]) for i in horizontal_axes]
            samples.append({"offset_xy": [dx, dy], "world": [x,y,z], "local": local,
                            "edge_margins_local": margins, "supported": all(v>0 for v in margins)})
    central = next(r for r in samples if r["offset_xy"] == [0., 0.])
    # A diagonal-support grid tests a square that contains a radius-.3m footprint.
    assert all(r["supported"] for r in samples)
    assert abs(central["world"][2] - hit["hit_z"]) < 1e-5
    source = json.loads((ROOT / sector["path"]).read_text())["Data"]["RootChunk"]
    collision_instance = source["nodeData"]["Data"][1792]
    matched = [m for m in sector["nearby_meshes"]
               if math.dist(xyz(m["data"]["Position"]), origin)<1e-5
               and m["data"]["Orientation"] == actor["Orientation"]]
    assert len(matched) == 1
    mesh = matched[0]
    report = {
        "static_review_passed": True,
        "approval_scope": "Development-only explicit relocation target, conditional on live fail-closed safety gates; not production or runtime approval",
        "verdict": "PASS static support/provenance for a runtime-gated development probe only",
        "method": "Independent normalized rotation matrices; analytic upward Box face plane, then orthonormal footprint projection. No original quaternion/ray helper imported.",
        "target": destination["marker"], "origin": origin,
        "normalized_actor_matrix": ar, "combined_shape_matrix": rotation,
        "shape_center_world": center, "upward_normal": normal,
        "slope_degrees": math.degrees(math.acos(normal[2])),
        "box_full_dimensions_local": [2*x for x in extents],
        "central_support_z": central["world"][2],
        "original_ray_support_z": hit["hit_z"],
        "independent_delta_z": central["world"][2]-hit["hit_z"],
        "marker_above_support_m": marker[2]-central["world"][2],
        "central_edge_margins_local": central["edge_margins_local"],
        "grid_min_edge_margin_local": min(m for r in samples for m in r["edge_margins_local"]),
        "support_samples": samples,
        "collision_instance": collision_instance,
        "collision_node": hit["node"], "collision_actor": hit["actor"], "collision_shape": hit["shape"],
        "collision_instances_and_variants": hit["instances"],
        "mesh_node": mesh["node"], "mesh_instance": mesh["instance"],
        "mesh_definition": mesh["definition"],
        "mesh_actor_position_delta_m": math.dist(xyz(mesh["data"]["Position"]), origin),
        "mesh_actor_orientation_exact_match": mesh["data"]["Orientation"]==actor["Orientation"],
        "limits": [
            "Static Box support is not a native physics or navmesh query, nor a streamed-residency guarantee.",
            "Compiled actor poses treated as world coordinates, corroborated by exact ordinary mesh pose; collision-node aggregate position is not reapplied.",
            "Size as half-extents is corroborated by the matched 300cm x 300cm sidewalk mesh; runtime native ray remains required.",
            "No complete overhead/body capsule clearance audit or highest-surface proof; live ground, navmesh and overlap checks remain mandatory.",
            "No claim that the linked data-terminal service itself works in retained Tower state.",
        ],
    }
    (OUT / "destination_independent_math.json").write_text(json.dumps(report, indent=2)+"\n")
    for key in ("verdict", "central_support_z", "independent_delta_z", "marker_above_support_m", "slope_degrees", "central_edge_margins_local", "grid_min_edge_margin_local", "mesh_actor_position_delta_m"):
        print(key, report[key])


if __name__ == "__main__":
    main()
