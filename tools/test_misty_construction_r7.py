"""Independent exact source/readback contract for R7 construction-only payload."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/misty_viktor_world"


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


def handles(v):
    return {x["HandleId"]: x["Data"] for x in walk(v) if "HandleId" in x and "Data" in x}


def canonical(v, mapping):
    if isinstance(v, dict):
        if "HandleRefId" in v:
            return canonical(mapping[v["HandleRefId"]], mapping)
        if "HandleId" in v and "Data" in v:
            return canonical(v["Data"], mapping)
        return {k: canonical(x, mapping) for k, x in v.items() if k not in ("BufferId",)}
    if isinstance(v, list):
        return [canonical(x, mapping) for x in v]
    return v


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()


def main():
    manifest = read(OUT / "r7_construction_manifest.json")
    audit = read(OUT / "r7_construction_audit.json")
    source_json = ROOT / manifest["source_raw"].replace("\\raw\\", "\\json\\")
    source = read(Path(str(source_json) + ".json"))
    private = read(OUT / "r7_construction_sector.json")
    block = read(OUT / "r7_construction_block.json")
    src, dst = source["Data"]["RootChunk"], private["Data"]["RootChunk"]
    sm, dm = handles(src), handles(dst)
    assert manifest["status"] == "BUILT_R7_CONSTRUCTION_SOURCE_NOT_INSTALLED_OR_LIVE"
    assert sha(ROOT / manifest["source_raw"]) == manifest["source_sha256"]
    resources = manifest["resources"]
    assert len(resources) == 2 and set(resources) == {
        r"towercontinued\misty_viktor_world\construction_r7.streamingsector",
        r"towercontinued\misty_viktor_world\construction_r7.streamingblock"}
    for depot, key in zip(resources, ("sector_sha256", "block_sha256")):
        assert sha(Path(manifest["source_root"]) / depot) == manifest[key]
    assert sha(OUT / "r7_construction_sector.json") == manifest["readback_sector_sha256"]
    assert sha(OUT / "r7_construction_block.json") == manifest["readback_block_sha256"]
    assert private["Data"]["EmbeddedFiles"] == block["Data"]["EmbeddedFiles"] == []
    assert dst["variantIndices"] == [0, 0]
    assert dst["nodeRefs"] == dst["localInplaceResource"] == dst["persistentNodes"] == []
    assert val(dst["externInplaceResource"]["DepotPath"]) == "0"
    assert len(dst["nodes"]) == len(dst["nodeData"]["Data"]) == 6
    all_transforms = []
    starts = []
    ids = []
    expected_rows = [575, 580, 897, 578, 581, 901]
    assert [r["source_data"] for r in manifest["source_rows"]] == expected_rows
    for i, row in enumerate(manifest["source_rows"]):
        orig = canonical(src["nodes"][row["source_node"]], sm)
        new = canonical(dst["nodes"][i], dm)
        assert orig["$type"] == new["$type"] == "worldInstancedDestructibleMeshNode"
        ob, nb = orig.pop("cookedInstanceTransforms"), new.pop("cookedInstanceTransforms")
        count, start = ob["numElements"], ob["startIndex"]
        transforms = ob["sharedDataBuffer"]["buffer"]["Data"]["Transforms"][start:start+count]
        assert start == row["old_transform_start"] and count == row["transform_count"]
        assert nb["startIndex"] == len(all_transforms) == row["new_transform_start"]
        assert nb["numElements"] == count
        starts.append(nb["startIndex"])
        assert nb["sharedDataBuffer"]["buffer"]["Data"]["Transforms"][nb["startIndex"]:nb["startIndex"]+count] == transforms
        all_transforms.extend(transforms)
        assert orig.pop("sourcePrefabHash") != "0" and new.pop("sourcePrefabHash") == "0"
        assert orig == new, f"Node {i}: unexpected field change"
        assert new["isDestructible"] == new["isWorkspot"] == 0
        assert val(new["idleEffect"]["DepotPath"]) == val(new["fracturingEffect"]["DepotPath"]) == "0"
        assert new["instanceTransforms"] == []
        old_data = copy.deepcopy(src["nodeData"]["Data"][row["source_data"]])
        new_data = copy.deepcopy(dst["nodeData"]["Data"][i])
        old_data.pop("Id"); ids.append(new_data.pop("Id"))
        assert ids[-1] == str(740000000007000+i) == row["new_id"]
        assert old_data.pop("NodeIndex") == row["source_node"]
        assert new_data.pop("NodeIndex") == i
        # Ref zero may be encoded as numeric zero or empty-string NodeRef.
        for key in ("QuestPrefabRefHash", "UkHash1"):
            assert val(old_data.pop(key)) in ("0", "")
            assert val(new_data.pop(key)) in ("0", "")
        assert old_data == new_data, f"Placement {i}: unexpected field change"
    assert len(set(ids)) == 6 and len(all_transforms) == 18
    assert starts == [0, 2, 5, 7, 8, 17]
    for handle in dst["nodes"]:
        node = canonical(handle, dm)
        assert node["cookedInstanceTransforms"]["sharedDataBuffer"]["buffer"]["Data"]["Transforms"] == all_transforms
    assert len(block["Data"]["RootChunk"]["descriptors"]) == 1
    d = copy.deepcopy(block["Data"]["RootChunk"]["descriptors"][0])
    expected = copy.deepcopy(audit["selected_rows"][0]["descriptor"])
    assert val(d.pop("data")["DepotPath"]) == resources[0]
    expected.pop("data")
    assert d.pop("numNodeRanges") == 2
    expected.pop("numNodeRanges")
    variants = d.pop("variants"); expected.pop("variants")
    assert d == expected, "Source descriptor bounds/grid/LOD changed"
    assert len(variants) == 1
    v = variants[0]
    assert v["rangeIndex"] == 1 and v["enabledByDefault"] == 0 and v["parentVariantID"] == 0
    assert val(v["name"]) == "PTFRMV_TowerStreet" and v["variantId"] == 3917072702
    assert val(v["nodeRef"]) == "$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env"
    assert d["level"] == 0
    mesh_types = {}
    for mesh, evidence in audit["mesh_dependencies"].items():
        mesh_data = read(ROOT / evidence["file"])["Data"]["RootChunk"]
        physics = [x for x in walk(mesh_data) if x.get("$type", "").startswith("physicsCollider")]
        assert physics, f"Expected native collision: {mesh}"
        assert evidence["parameters"] == ["meshMeshParamPhysics"]
        mesh_types[mesh] = [x["$type"] for x in physics]
    result = {"status": "PASS_R7_CONSTRUCTION_SOURCE_READBACK_NOT_LIVE", "nodes": 6,
              "placements": 6, "exact_cooked_transforms": 18, "private_id_count": 6,
              "source_descriptor_spatial_metadata_preserved": True, "default_empty": True,
              "exact_physics_and_all_unlisted_node_fields_preserved": True,
              "mesh_native_collision_types": mesh_types,
              "sector_sha256": manifest["sector_sha256"], "block_sha256": manifest["block_sha256"],
              "limitations": "No in-game visibility, collision, opt-out or impulse test performed. No added distant LOD proxy: source has native LOD0 groups and preserved original autohide values."}
    (OUT / "r7_construction_tests.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
