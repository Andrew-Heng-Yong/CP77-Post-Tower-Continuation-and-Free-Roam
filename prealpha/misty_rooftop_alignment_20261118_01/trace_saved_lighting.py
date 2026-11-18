"""Read the observed world-state layout and resolve variant values by their native owner and name."""

import json
import math
import struct
import argparse
from pathlib import Path

from capture_save_samples import ENDING_OUT, OUT
from placement import ROOT, SEAT, express_in, pose, read, root, sha


ROOF = ("$/03_night_city/c_watson/little_china/loc_q115_mistyc_mistys_ripperdoc_roof_prefabDR5IG6A/"
        "#loc_q115_mystic_mistys_ripperdoc_roof_lighting")
CLINIC = ("$/03_night_city/c_watson/little_china/loc_mystic_mistys_ripperdoc_prefabH2DWJJI/"
          "#loc_mystic_mistys_ripperdoc_lightning")
VARIANTS = ("Q307_AV", "q116_neklace", "L_q116_05", "L_q115_02b", "L_q115_toss_pills")


def fnv(text):
    result = 0xCBF29CE484222325
    for byte in text.encode("utf-8"):
        result = ((result ^ byte) * 0x100000001B3) & 0xffffffffffffffff
    return result


def saved_groups(data):
    # Only accept the observed single 'None' region layout for these saves.
    prefix = b"\x01\x84None"
    if not data.startswith(prefix) or data[len(prefix)] not in (0, 1):
        raise ValueError("Unrecognized WorldStateSystem header")
    # The following header flag varies on the after-credits checkpoint.
    # Neither value supplies a variant state.
    offset = len(prefix) + 1

    def count():
        nonlocal offset
        first = data[offset]
        offset += 1
        if first & 0x80:
            raise ValueError("Negative array size")
        value = first & 63
        more = first & 64
        shift = 6
        while more:
            byte = data[offset]
            offset += 1
            value |= (byte & 127) << shift
            more = byte & 128
            shift += 7
        return value

    def u64():
        nonlocal offset
        value, = struct.unpack_from("<Q", data, offset)
        offset += 8
        return value

    def keys():
        result = [u64() for _ in range(count())]
        if result != sorted(set(result)):
            raise ValueError("Unsorted or duplicate world-state keys")
        return result

    simple = keys()
    flags = data[offset:offset + len(simple)]
    if len(flags) != len(simple) or set(flags) - {0, 1}:
        raise ValueError("Unexpected simple world-state flags")
    offset += len(flags)
    tables = []
    for _ in range(2):
        groups = {}
        for owner in keys():
            values = {}
            for _ in range(count()):
                name, value = u64(), u64()
                if name in values or value not in (0, 1):
                    raise ValueError("Unexpected named world-state entry")
                values[name] = value
            groups[owner] = values
        tables.append(groups)
    if offset != len(data):
        raise ValueError("Unclassified bytes after named world-state tables")
    return tables


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    if isinstance(value, list):
        for child in value:
            yield from walk(child)


def rooftop_writes(resource):
    writes = []
    for node in walk(resource):
        if node.get("$type") != "questWorldDataManagerNodeDefinition":
            continue
        for param in walk(node.get("type", {})):
            if param.get("$type") != "questTogglePrefabVariant_NodeTypeParams":
                continue
            if param["prefabNodeRef"]["$value"] not in (ROOF, ROOF[ROOF.rindex("#"):]):
                continue
            writes.extend((node["id"], v["name"]["$value"], v["show"]) for v in param["variantStates"])
    return writes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ending", action="store_true")
    ending = parser.parse_args().ending
    captures = ENDING_OUT if ending else OUT
    assert fnv(ROOF.replace("#", "")) == 0xabd74373424e4654  # WolvenKit NodeRef.CalculateHash
    assert fnv("Q307_AV") == 0x5d43736ac09dd496
    capture = SEAT.parent / "misty_rooftop_lift_20261117_01/work/native_01"
    providers = read(capture / "providers.json")["hits"]
    def verified_resource(suffix):
        item, = [r for r in providers if r["depot"].endswith(suffix) and Path(r["archive"]).name.startswith("ep1_")]
        assert sha(Path(item["raw"])) == item["sha256"] and sha(Path(item["json"])) == item["json_sha256"]
        return root(Path(item["json"]))
    pickup = rooftop_writes(verified_resource("q307_01_pickup.scene"))
    assert pickup == [(2022, "Q307_AV", 1), (3050, "Q307_AV", 1)]
    assert not rooftop_writes(verified_resource("q307_cleanup.questphase"))
    block = verified_resource(r"default\blocks\all.streamingblock")
    defaults = {v["name"]["$value"]: v["enabledByDefault"] for d in block["descriptors"]
                for v in d["variants"] if v["nodeRef"]["$value"] == ROOF}
    assert all(defaults[name] == 0 for name in VARIANTS)
    target, = [h for h in read(ROOT / "work/lighting_01/providers.json")["providers"]
               if h["depot"].endswith("exterior_-7_4_0_2.streamingsector") and Path(h["archive"]).name.startswith("ep1_")]
    assert sha(Path(target["json"])) == target["json_sha256"]
    sector = root(Path(target["json"]))
    instance = sector["nodeData"]["Data"][2940]
    area = sector["nodes"][int(instance["nodeIdx"])]["Data"]
    assert area["debugName"]["$value"] == "{T_Rooftop}"
    settings = area["notifiers"][0]["Data"]["params"]["areaParameters"]
    manual, = [h["Data"] for h in settings if h["Data"]["$type"] == "CameraAreaSettings" and h["Data"]["enable"]]
    assert not manual["automated"] and int(manual["disabledIndexedProperties"]) == 0
    assert math.isclose(manual["fStop"], 1.4, abs_tol=1e-6)
    frame = pose(instance["transform"])
    scale = instance["scale"]
    height = area["outline"]["Data"]["height"] * scale["Z"]
    samples = []
    for sample in read(captures / "sources.json"):
        slot = sample["slot"]
        path = captures / (slot + ".world")
        assert sha(path) == sample["sections"]["world"]
        _, groups = saved_groups(path.read_bytes())
        roof = groups.get(fnv(ROOF.replace("#", "")), {})
        clinic = groups.get(fnv(CLINIC.replace("#", "")), {})
        states = {name: roof.get(fnv(name)) for name in VARIANTS}
        controls = {name: clinic.get(fnv(name)) for name in ("Q307_VV", "V_Default")}
        pos = sample["metadata"]["playerPosition"]
        xy, z, _ = express_in(frame, (complex(pos["X"], pos["Y"]), pos["Z"], 1))
        samples.append({"slot": slot, "save_sha256": sample["sha256"],
                        "inside_rooftop_volume_at_save": abs(xy.real) < scale["X"] and abs(xy.imag) < scale["Y"] and 0 < z < height,
                        "saved_roof_states": states, "independent_clinic_controls": controls,
                        "variant_owners_in_table": len(groups)})
    observations = {"scope": "Saved variant overrides and authored geometry. Rendered brightness was not measured.",
                    "owner_node_hash": "0xabd74373424e4654", "variant_cname_hash": "0x5d43736ac09dd496",
                    "owner": ROOF, "defaults": {k: defaults[k] for k in VARIANTS}, "pickup_writes": pickup,
                    "q307_cleanup_explicit_roof_variant_writes": [], "camera_automated": bool(manual["automated"]),
                    "samples": samples}
    output = ROOT / ("saved_ending_trace.json" if ending else "saved_lighting_trace.json")
    encoded = json.dumps(observations, indent=2) + "\n"
    if output.exists():
        if output.read_text(encoding="utf-8") != encoded:
            raise ValueError("Recorded trace differs")
    else:
        with output.open("x", encoding="utf-8", newline="\n") as f:
            f.write(encoded)
    for sample in samples:
        print(sample["slot"], sample["saved_roof_states"], sample["independent_clinic_controls"],
              "inside", sample["inside_rooftop_volume_at_save"])


if __name__ == "__main__":
    main()
