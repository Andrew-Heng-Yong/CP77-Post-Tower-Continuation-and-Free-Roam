"""Extract arrival-marker candidates and nearby authored collision without game writes."""
import bisect
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/phase2b_p4"
BASE = OUT / "staging_scan/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default"
ORIGIN = (-1545.4779052734, 1228.4576416016, 11.5202331543)
TARGET_REF = "#wat_lch_dataterm_05"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))["Data"]["RootChunk"]


def value(item):
    return item.get("$value", item) if isinstance(item, dict) else item


def xyz(pos):
    return tuple(pos[k] for k in ("X", "Y", "Z"))


def main():
    marker_root = load(BASE / "always_loaded_1.streamingsector.json")
    block = load(BASE / "blocks/all.streamingblock.json")
    markers = []
    for di, data in enumerate(marker_root["nodeData"]["Data"]):
        node = marker_root["nodes"][data["NodeIndex"]]["Data"]
        ref = value(data.get("QuestPrefabRefHash"))
        if node.get("$type") != "worldStaticMarkerNode" or not isinstance(ref, str):
            continue
        if "dataterm" not in ref:
            continue
        p = xyz(data["Position"])
        markers.append({"node_data": di, "node_index": data["NodeIndex"], "ref": ref,
                        "position": p, "orientation": data["Orientation"],
                        "enabled": node.get("isEnabled"), "source_prefab": node.get("sourcePrefabHash"),
                        "range": bisect.bisect_right(marker_root["variantIndices"], di)-1,
                        "distance_from_fixture": math.dist(p, ORIGIN)})
    markers.sort(key=lambda x:x["distance_from_fixture"])
    chosen = next(m for m in markers if m["ref"].endswith("/" + TARGET_REF))
    target = chosen["position"]
    sec_path = BASE / "exterior_-25_19_0_0.streamingsector.json"
    sector = load(sec_path)
    descriptor_index, descriptor = next((i,d) for i,d in enumerate(block["descriptors"])
        if value(d["data"]["DepotPath"]).endswith("\\exterior_-25_19_0_0.streamingsector"))
    marker_descriptor_index, marker_descriptor = next((i,d) for i,d in enumerate(block["descriptors"])
        if value(d["data"]["DepotPath"]).endswith("\\always_loaded_1.streamingsector"))
    ranges = sector["variantIndices"]
    by_node = {}
    for di,d in enumerate(sector["nodeData"]["Data"]):
        by_node.setdefault(d["NodeIndex"],[]).append({"node_data":di,"range":bisect.bisect_right(ranges,di)-1})
    collisions=[]
    meshes=[]
    for di,d in enumerate(sector["nodeData"]["Data"]):
        node=sector["nodes"][d["NodeIndex"]]["Data"]
        p=xyz(d["Position"])
        if node.get("$type")=="worldStaticMeshNode" and math.dist(p[:2],target[:2])<20 and abs(p[2]-target[2])<6:
            meshes.append({"node_data":di,"node_index":d["NodeIndex"],"range":bisect.bisect_right(ranges,di)-1,
                           "position":p,"orientation":d["Orientation"],"scale":d["Scale"],
                           "mesh":value(node.get("mesh",{}).get("DepotPath")),"source_prefab":node.get("sourcePrefabHash")})
    for ni,wrapper in enumerate(sector["nodes"]):
        node=wrapper["Data"]
        if node.get("$type")!="worldCollisionNode": continue
        for ai,actor in enumerate(node["compiledData"]["Data"]["Actors"]):
            p=tuple(actor["Position"][key]["Bits"]/131072 for key in "xyz")
            dist=math.dist(p[:2],target[:2])
            if dist>20 or abs(p[2]-target[2])>6: continue
            collisions.append({"node_index":ni,"instances":by_node.get(ni,[]),"actor_index":ai,
                               "position":p,"distance_xy":dist,"orientation":actor["Orientation"],
                               "scale":actor.get("Scale"),"shapes":actor["Shapes"],
                               "source_prefab":node.get("sourcePrefabHash"),"debug_name":value(node.get("debugName"))})
    collisions.sort(key=lambda x:x["distance_xy"])
    evidence={"candidate_markers":markers[:8],"chosen":chosen,
              "marker_descriptor":{"index":marker_descriptor_index,"data":marker_descriptor},
              "target_sector":{"path":str(sec_path.relative_to(ROOT)),"descriptor_index":descriptor_index,
                               "variant_indices":ranges,"descriptor":descriptor},
              "nearby_collision_actors":collisions,"nearby_static_meshes":meshes,
              "limits":"Authored marker and local collision presence are static evidence, not proof of runtime residency; live navmesh and support queries required."}
    (OUT/"target_evidence.json").write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"markers":markers[:8],"marker_descriptor_index":marker_descriptor_index,
                      "marker_descriptor_variants":marker_descriptor["variants"],
                      "nearby_collision_count":len(collisions),"nearby_mesh_count":len(meshes)},indent=2))


if __name__=="__main__": main()
