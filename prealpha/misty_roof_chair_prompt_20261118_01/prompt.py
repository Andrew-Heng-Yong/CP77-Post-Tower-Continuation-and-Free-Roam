"""Locate the chair cushion in the installed mesh and qualify the packed prompt."""

import base64
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALIGN = ROOT.parent / "misty_rooftop_alignment_20261118_01"
sys.path.insert(0, str(ALIGN))
from placement import SEAT, compose, express_in, node, pose, read, root, sha

BASE = ROOT.parent / "misty_roof_lighting_and_seat_20261118_01/installed_manifest.json"
BASE_SHA = "C34D07FF41E4714082CAAD9294CE112AFD704EDFF2EB7F7626F5DBCDB2761BF4"
LIFT = ROOT.parent / "misty_rooftop_lift_20261117_01/work"
INPUTS = ROOT / "work/inputs"
PACK = ROOT / "work/pack_01"


def cushion_height(mesh, x, y):
    blob = mesh["renderResourceBlob"]["Data"]
    h = blob["header"]
    c, = [chunk for chunk in h["renderChunkInfos"] if chunk["lodMask"] == 1]
    vb = c["chunkVertices"]
    first = vb["vertexLayout"]["elements"]["Elements"][0]
    assert (first["usage"], first["type"], first["streamIndex"]) == ("PS_Position", "PT_Short4N", 0)
    stride = vb["vertexLayout"]["slotStrides"]["Elements"][0]
    assert c["chunkIndices"]["pe"] == "IBCT_IndexUShort" and c["numIndices"] % 3 == 0
    data = base64.b64decode(blob["renderBuffer"]["Bytes"], validate=True)
    vertices = []
    for i in range(c["numVertices"]):
        raw = struct.unpack_from("<hhh", data, vb["byteOffsets"]["Elements"][0] + i * stride)
        vertices.append(tuple(h["quantizationOffset"][a] + h["quantizationScale"][a] * v / 32767
                              for a, v in zip("XYZ", raw, strict=True)))
    indices = struct.unpack_from(f"<{c['numIndices']}H", data, h["indexBufferOffset"] + c["chunkIndices"]["teOffset"])
    hits = []
    for i in range(0, len(indices), 3):
        a, b, d = (vertices[j] for j in indices[i:i+3])
        bx, by, dx, dy = b[0]-a[0], b[1]-a[1], d[0]-a[0], d[1]-a[1]
        det = bx*dy - by*dx
        if abs(det) < 1e-9:
            continue
        u = ((x-a[0])*dy - (y-a[1])*dx) / det
        v = (bx*(y-a[1]) - by*(x-a[0])) / det
        if min(u, v, 1-u-v) >= -1e-7:
            hits.append(a[2] + u*(b[2]-a[2]) + v*(d[2]-a[2]))
    assert len(hits) >= 2 and 0.43 < max(hits) < 0.48
    return max(hits)


def target():
    assert sha(BASE) == BASE_SHA
    hits = read(INPUTS / "providers.json")["hits"]
    mesh, = [h for h in hits if h["depot"].endswith(".mesh")]
    assert mesh["sha256"] == sha(Path(mesh["raw"])) == "488D47DDFF407AFA0479F7A9C2F33F7FC7C00BDA598454883430CC1A939A121D"
    sector, = [h for h in hits if h["archive"] == "zzzz_PTFR_Combined.archive" and h["depot"].endswith(".streamingsector")]
    decoded, = [h for h in read(LIFT / "decoded_10_01/manifest.json")["rows"] if
                h["depot"] == sector["depot"] and Path(h["archive"]).name == sector["archive"]]
    assert sha(Path(sector["raw"])) == sector["sha256"] == decoded["sha256"]
    assert sha(Path(decoded["json"])) == decoded["json_sha256"]
    world = root(Path(decoded["json"]))
    s = world["nodeData"]["Data"][2036]
    inner = world["nodes"][int(s["nodeIdx"])]["Data"]["buffer"]["Data"]["InnerNodes"][s["instanceIndex"]]
    assert inner["mesh"]["DepotPath"]["$value"] == mesh["depot"] and [s["scale"][k] for k in "XYZ"] == [1,1,1]
    chair = pose(s["transform"])
    geometry = read(SEAT / "work/scene_01/manifest.json")
    assert abs(chair[0] - pose(geometry["seat"])[0]) < 0.26
    # Center of the chair's width. Pick the middle of the flat seat, clear of the backrest.
    y = 0.10
    height = cushion_height(root(Path(mesh["raw"] + ".json")), 0, y)
    icon, = [x for x in world["nodeData"]["Data"] if x["globalNodeId"]["hash"] == "17982712683434736922"]
    assert world["nodes"][int(icon["nodeIdx"])]["Data"]["debugName"]["$value"] == "{q307_ent_rooftop_icon}"
    assert abs(pose(icon["transform"])[0] - chair[0]) < 0.15
    native, = [h for h in read(LIFT / "native_01/providers.json")["hits"] if h["depot"].endswith("q307_01_pickup.scene")]
    assert sha(Path(native["json"])) == native["json_sha256"]
    choices = [node(root(Path(native["json"])), i) for i in (3468,3474)]
    choice = choices[0]
    assert all(n["atgoParams"]["nodeRef"]["$value"] == "#q307_ent_rooftop_icon" and
               n["displayNameOverride"] == "LocKey#85596" and
               n["shapeParams"]["Data"]["rotation"] == choice["shapeParams"]["Data"]["rotation"] for n in choices)
    loc = ROOT.parents[1] / "research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens"
    entries = [entry for path in loc.glob("*.json") for entry in root(path)["root"]["Data"]["entries"]
               if entry["primaryKey"] == "85596"]
    assert entries and all(e["femaleVariant"] == "Chair" for e in entries)
    frame = pose(geometry["anchor"])
    world_point = compose(chair,(complex(0,y),height + 0.06,1))
    local_xy, local_z, local_dir = express_in(frame,(world_point[0],world_point[1],pose(icon["transform"])[2]))
    half = math.atan2(local_dir.imag,local_dir.real)/2
    rotation = choice["shapeParams"]["Data"]["rotation"]
    return {"x":local_xy.real, "y":local_xy.imag, "z":local_z, "k":math.sin(half), "r":math.cos(half),
            "shape_k":rotation["k"], "shape_r":rotation["r"], "label":choice["displayNameOverride"],
            "surface_height":height, "world":[world_point[0].real,world_point[0].imag,world_point[1]]}


def verify():
    t = target()
    before = root(ALIGN / "work/pack_01/packed.scene.json")
    after = root(PACK / "packed.scene.json")
    owners = [(node(before, i), node(after, i)) for i in (4,10)]
    for old, new in owners:
        assert old["displayNameOverride"] == "LocKey#46417" and new["displayNameOverride"] == t["label"]
        new["displayNameOverride"] = old["displayNameOverride"]
    old, new = owners[0]
    for field, keys, expected in (("entityPosition","XYZ",[t["x"],t["y"],t["z"]]),
                                  ("entityOrientation","ijkr",[0,0,t["k"],t["r"]])):
        actual = new["atwParams"][field]
        assert max(abs(actual[k]-v) for k,v in zip(keys,expected,strict=True)) < 2e-5
        new["atwParams"][field] = old["atwParams"][field]
    actual = new["shapeParams"]["Data"]["rotation"]
    assert max(abs(actual[k]-v) for k,v in zip("ijkr",[0,0,t["shape_k"],t["shape_r"]],strict=True)) < 2e-6
    new["shapeParams"]["Data"]["rotation"] = old["shapeParams"]["Data"]["rotation"]
    assert before == after, "Unexpected scene delta outside the two choice nodes"
    print("Verified Chair on Sit/Get Up, mesh-relative marker, native interaction facing and full scene diff.")


if __name__ == "__main__":
    if sys.argv[1:] == ["--target"]:
        print(json.dumps(target()))
    else:
        verify()
