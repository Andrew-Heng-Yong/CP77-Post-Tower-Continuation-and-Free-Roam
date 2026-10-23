"""Independent static box-ray/support audit for the P4 arrival marker; no game access."""
import bisect
import json
import math
from pathlib import Path

from collect_handoff_targets import BASE, ROOT, load, value

TARGET = (-1556.03113, 1246.02136, 19.0753651)


def vector(v):
    return tuple(v[k] for k in ("X", "Y", "Z"))


def quat(q):
    return tuple(q[k] for k in ("i", "j", "k", "r"))


def rotate(q, v):
    x, y, z, w = q
    a, b, c = v
    # Unit quaternion rotation; exporter quaternions differ from unit by float noise.
    t = (2 * (y*c-z*b), 2 * (z*a-x*c), 2 * (x*b-y*a))
    return (a+w*t[0]+y*t[2]-z*t[1], b+w*t[1]+z*t[0]-x*t[2], c+w*t[2]+x*t[1]-y*t[0])


def inverse(q):
    return (-q[0], -q[1], -q[2], q[3])


def local_point(point, actor, shape):
    origin = tuple(actor["Position"][k]["Bits"] / 131072 for k in "xyz")
    p = rotate(inverse(quat(actor["Orientation"])), tuple(a-b for a,b in zip(point,origin)))
    scale = vector(actor.get("Scale", {"X":1,"Y":1,"Z":1}))
    p = tuple(a/b for a,b in zip(p,scale))
    p = tuple(a-b for a,b in zip(p,vector(shape["Position"])))
    return rotate(inverse(quat(shape["Rotation"])), p)


def intersect(point0, point1, extent):
    near, far = 0., 1.
    for a,b,e in zip(point0,point1,extent):
        delta = b-a
        if abs(delta) < 1e-10:
            if abs(a)>e: return None
            continue
        low, high = sorted(((-e-a)/delta,(e-a)/delta))
        near, far = max(near,low),min(far,high)
        if near>far: return None
    return near


def main():
    block = load(BASE / "blocks/all.streamingblock.json")
    results = []
    start, end = (*TARGET[:2],TARGET[2]+1),(*TARGET[:2],TARGET[2]-4)
    for filename in ("exterior_-25_19_0_0.streamingsector.json", "exterior_-13_9_0_1.streamingsector.json"):
        sector=load(BASE/filename)
        descriptor=next(d for d in block["descriptors"] if value(d["data"]["DepotPath"]).endswith("\\"+filename[:-5]))
        variants={v["rangeIndex"]:{"name":value(v["name"]),"ref":value(v["nodeRef"]),"enabledByDefault":v["enabledByDefault"]} for v in descriptor["variants"]}
        instances={}
        for di,d in enumerate(sector["nodeData"]["Data"]):
            ri=bisect.bisect_right(sector["variantIndices"],di)-1
            instances.setdefault(d["NodeIndex"],[]).append({"node_data":di,"range":ri,"variant":variants.get(ri)})
        for ni,wrapper in enumerate(sector["nodes"]):
            node=wrapper["Data"]
            if node.get("$type")!="worldCollisionNode":continue
            for ai,actor in enumerate(node["compiledData"]["Data"]["Actors"]):
                for si,shape in enumerate(actor["Shapes"]):
                    if shape["ShapeType"]!="Box": continue
                    p0,p1=local_point(start,actor,shape),local_point(end,actor,shape)
                    t=intersect(p0,p1,vector(shape["Size"]))
                    if t is None:continue
                    results.append({"sector":filename,"node":ni,"actor":ai,"shape":si,"instances":instances[ni],
                                    "debug_name":value(node.get("debugName")),"source_prefab":node.get("sourcePrefabHash"),
                                    "estimated_top_z":start[2]+(end[2]-start[2])*t,
                                    "actor_data":actor,"shape_data":shape})
    report={"target":TARGET,"method":"Transform vertical segment into each box's local frame; Size treated as half-extents, matching PhysX box shape convention. Mesh hulls are not decoded.","box_intersections":results}
    out=ROOT/"research/phase2b_p4/target_support_review.json"
    out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    for row in results:
        print(json.dumps({k:v for k,v in row.items() if k not in ("actor_data","shape_data")}))
    print("Intersections:",len(results),"Output:",out)


if __name__=="__main__":main()
