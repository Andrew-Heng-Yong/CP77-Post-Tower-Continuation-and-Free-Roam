"""Locate an authored H10 street spawn and report limits of offline collision evidence."""
import bisect
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from collect_handoff_targets import load, value
from review_handoff_support import intersect, local_point, vector
from catalog_gig_rollout_r2 import sha

OUT = ROOT / "research/pre_alpha_clean/arrival"
MARKERS = ROOT / "research/phase2b_p4/staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/always_loaded_1.streamingsector.json"
BLOCK = MARKERS.parent / "blocks/all.streamingblock.json"


def main():
    marker_root = load(MARKERS)
    block = load(BLOCK)
    matches = []
    for index, instance in enumerate(marker_root["nodeData"]["Data"]):
        node = marker_root["nodes"][instance["NodeIndex"]]["Data"]
        ref = value(instance.get("QuestPrefabRefHash"))
        if node["$type"] == "worldStaticMarkerNode" and isinstance(ref, str) and ref.endswith("/#cp77_spwn_performance_test") and "loc_megabuilding_a" in ref:
            matches.append((index, instance, node, ref))
    assert len(matches) == 1
    index, instance, node, ref = matches[0]
    point = vector(instance["Position"])
    assert point[2] < 30  # Street entrance level, not H10 apartment floor (~123m).
    orientation = instance["Orientation"]
    yaw = math.degrees(2 * math.atan2(orientation["k"], orientation["r"]))
    while yaw > 180:
        yaw -= 360
    while yaw < -180:
        yaw += 360
    samples = [(0, 0), (.3, 0), (-.3, 0), (0, .3), (0, -.3)]
    findings = []
    pins = {str(MARKERS.relative_to(ROOT)): sha(MARKERS), str(BLOCK.relative_to(ROOT)): sha(BLOCK)}
    for path in (OUT / "sectors/json").rglob("*.streamingsector.json"):
        sector = load(path)
        pins[str(path.relative_to(ROOT))] = sha(path)
        descriptor = next(d for d in block["descriptors"] if value(d["data"]["DepotPath"]).endswith("\\" + path.name[:-5]))
        for ni, wrapper in enumerate(sector["nodes"]):
            collision = wrapper["Data"]
            if collision["$type"] != "worldCollisionNode":
                continue
            collision_instances = [{"node_data": di, "range": bisect.bisect_right(sector["variantIndices"], di) - 1} for di, d in enumerate(sector["nodeData"]["Data"]) if d["NodeIndex"] == ni]
            for ai, actor in enumerate(collision["compiledData"]["Data"]["Actors"]):
                for si, shape in enumerate(actor["Shapes"]):
                    if shape["ShapeType"] != "Box":
                        continue
                    heights = []
                    for dx, dy in samples:
                        top = (point[0] + dx, point[1] + dy, point[2] + .3)
                        bottom = (top[0], top[1], point[2] - 1.0)
                        t = intersect(local_point(top, actor, shape), local_point(bottom, actor, shape), vector(shape["Size"]))
                        heights.append(None if t is None else top[2] - 1.3 * t)
                    if all(h is not None and point[2] - .5 <= h <= point[2] + .1 for h in heights):
                        findings.append({"sector": str(path.relative_to(ROOT)), "node": ni, "actor": ai, "shape": si, "heights": heights, "instances": collision_instances, "descriptor": descriptor, "collision": {"actor": actor, "shape": shape}})
    support = max(findings, key=lambda x: x["heights"][0]) if findings else None
    result = {
        "status": "AUTHORED_H10_STREET_SPAWN_RUNTIME_SUPPORT_REQUIRED",
        "marker": {"node_data": index, "node_index": instance["NodeIndex"], "ref": ref, "position": list(point), "orientation": orientation, "yaw_degrees": yaw, "definition": node, "instance": instance},
        "ground_z": support["heights"][0] if support else None, "support": support,
        "source_pins": pins,
        "description": "Original player spawn marker under H10 loc_megabuilding_a, on the street at its frontage. Its z~23 is separate from H10 apartment/atrium z~123 and entrance elevator landing z~27. Original exact position/orientation retained.",
        "limits": "No box-only support proof at this authored marker. The nearby world geometry includes triangle collision, which this box-only audit does not decode. Exact position is an authored player spawn, not a guessed coordinate. Runtime uses the native TeleportToNode operation also used by stock FastTravelSystem, with no pre-stream ray/nav requirement that could deadlock a remote destination. The engine owns node placement/streaming; the mod acknowledges observed player position afterward. Live exterior identification, loading behavior and physical footing remain required tests; source location and position acknowledgment do not prove collision/rendered safety.",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "target.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["status"], list(point), "yaw", yaw, "floor", result["ground_z"])


if __name__ == "__main__":
    main()
