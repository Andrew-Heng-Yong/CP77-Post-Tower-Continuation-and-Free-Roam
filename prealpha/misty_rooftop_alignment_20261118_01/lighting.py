"""Identify rooftop lighting using the current expansion sectors and their actual variant ranges."""

import math
from collections import Counter
from pathlib import Path

from placement import ROOT, SEAT, pose, express_in, read, root, sha


def main():
    sources = read(ROOT / "work/lighting_01/providers.json")
    census = read(ROOT / "work/pickup_ranges_01/providers.json")
    assert sources["archives_checked"] == census["archives_checked"] == 135
    capture = SEAT.parent / "misty_rooftop_lift_20261117_01/work/native_01"
    originals = read(capture / "providers.json")["hits"]
    block, = [h for h in originals if h["depot"].endswith(r"default\blocks\all.streamingblock")
              and Path(h["archive"]).name == "ep1_1_nightcity.archive"]
    assert sha(Path(block["json"])) == block["json_sha256"]
    blocks = {d["data"]["DepotPath"]["$value"]: d for d in root(Path(block["json"]))["descriptors"]}
    counts = Counter()
    for provider in census["providers"]:
        assert sha(Path(provider["raw"])) == provider["sha256"]
        assert sha(Path(provider["json"])) == provider["json_sha256"]
        for item in read(Path(provider["json"])):
            counts[item["type"]] += 1
    assert sum(counts.values()) == 13 and len(census["providers"]) == 7
    sector, = [h for h in sources["providers"] if h["depot"].endswith("exterior_-7_4_0_2.streamingsector")
               and Path(h["archive"]).name == "ep1_1_nightcity.archive"]
    assert sha(Path(sector["json"])) == sector["json_sha256"]
    world = root(Path(sector["json"]))
    variant, = [v for v in blocks[sector["depot"]]["variants"] if v["name"]["$value"] == "Q307_AV"]
    assert variant["enabledByDefault"] == 0 and variant["variantId"] == 194410905
    item, = world["variantNodes"][variant["rangeIndex"] - 1]
    index = int(item["nodeIdx"])
    assert item == world["nodeData"]["Data"][2940] and index == 207
    area = world["nodes"][index]["Data"]
    assert area["debugName"]["$value"] == "{T_Rooftop}"
    definition, = [h["Data"] for h in area["notifiers"]]
    assert definition["$type"] == "worldEnvAreaNotifier" and definition["isEnabled"] == 1
    assert definition["blendTimeIn"] == definition["blendTimeOut"] == 5
    shape = area["outline"]["Data"]
    assert {(p["X"], p["Y"]) for p in shape["points"]} == {(-1,-1), (-1,1), (1,1), (1,-1)}
    geometry = read(SEAT / "work/scene_01/manifest.json")
    frame = pose(item["transform"])
    for key in ("seat", "anchor"):
        xy, z, _ = express_in(frame, pose(geometry[key]))
        assert abs(xy.real) < item["scale"]["X"] and abs(xy.imag) < item["scale"]["Y"]
        assert 0 < z < shape["height"] * item["scale"]["Z"]
    active = [h["Data"] for h in definition["params"]["areaParameters"] if h["Data"]["enable"]]
    assert {a["$type"] for a in active} == {"CameraAreaSettings","CloudAreaSettings","VolumetricFogAreaSettings"}
    camera, = [a for a in active if a["$type"] == "CameraAreaSettings"]
    assert math.isclose(camera["fStop"], 1.4, abs_tol=1e-6) and camera["ISO"] == 50 and camera["shutterTime"] == 1
    print("Q307_AV covers the landing and chair. The group has", dict(counts),
          "across seven sectors. Live contribution needs confirmation.")


if __name__ == "__main__":
    main()
