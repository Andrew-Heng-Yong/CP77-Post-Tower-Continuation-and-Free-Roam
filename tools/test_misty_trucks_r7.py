"""Independent, bounded equality/scope checks for R7's two native truck spawners."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/misty_viktor_world"


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def val(obj):
    return obj.get("$value") if isinstance(obj, dict) else obj


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def buffers(obj, path=()):
    found = []
    if isinstance(obj, dict):
        if "BufferId" in obj:
            found.append(path)
        for key, item in obj.items():
            found.extend(buffers(item, path + (key,)))
    elif isinstance(obj, list):
        for key, item in enumerate(obj):
            found.extend(buffers(item, path + (key,)))
    return found


def main():
    manifest = read(AUDIT / "r7_trucks_manifest.json")
    assert manifest["status"] == "BUILT_R7_TRUCK_SOURCE_NOT_INSTALLED_OR_LIVE"
    assert manifest["source_sha256"] == "CAA6C704093CB6905C191A464F7885683872033828386807EC9AEC0BDCB03A15"
    assert sha(ROOT / manifest["source"]) == manifest["source_sha256"]
    assert sha(ROOT / manifest["source_block"]) == manifest["source_block_sha256"]
    source = read(AUDIT / "r7_trucks_source_sector.json")["Data"]["RootChunk"]
    output_document = read(AUDIT / "r7_trucks_sector.json")
    output = output_document["Data"]["RootChunk"]
    block_document = read(AUDIT / "r7_trucks_block.json")
    block = block_document["Data"]["RootChunk"]
    source_block = read(ROOT / (manifest["source_block"].replace("\\raw\\", "\\json\\") + ".json"))["Data"]["RootChunk"]
    assert len(output["nodes"]) == len(output["nodeData"]["Data"]) == 2
    assert output["variantIndices"] == [0, 0]
    assert output["variantNodes"] == [[], []]
    assert buffers(output_document) == [("Data", "RootChunk", "nodeData")]
    assert not buffers(block_document)
    assert output["level"] == source["level"] == 1
    assert output["category"] == source["category"] == "Exterior"
    assert not output["localInplaceResource"] and not output["persistentNodes"]
    assert output["persistentNodeIndex"] == -1
    assert val(output["externInplaceResource"]["DepotPath"]) in ("0", "")
    for document in (output_document, block_document):
        assert not document["Data"].get("EmbeddedFiles", [])
    identities = []
    for index, ni, di in ((0, 56, 66), (1, 57, 67)):
        expected_name = f"PTFRMV_NCPDTruck{index+1:02}"
        expected_ref = "$/03_night_city/#" + expected_name
        expected_id = str(750000000007066 + index)
        src_node = source["nodes"][ni]["Data"]
        dst_node = copy.deepcopy(output["nodes"][index]["Data"])
        assert dst_node["$type"] == "worldPopulationSpawnerNode"
        assert val(dst_node["debugName"]) == expected_name
        assert dst_node["sourcePrefabHash"] == "0"
        for key in ("debugName", "sourcePrefabHash"):
            dst_node[key] = src_node[key]
        assert dst_node == src_node, "Unexpected population setting or record delta"
        assert dst_node["spawnOnStart"] == 1 and dst_node["isVehicle"] == 0
        assert dst_node["alwaysSpawned"] == "default__false_"
        assert dst_node["tag"] == dst_node["tagExt"] == "None"
        assert val(dst_node["objectRecordId"]) in ("Vehicle.v_utility4_militech_behemoth_police", "188555135153")
        src_datum = source["nodeData"]["Data"][di]
        dst_datum = copy.deepcopy(output["nodeData"]["Data"][index])
        assert dst_datum["Id"] == expected_id and dst_datum["NodeIndex"] == index
        assert val(dst_datum["QuestPrefabRefHash"]) == expected_ref
        assert val(dst_datum["UkHash1"]) in ("0", "")
        for key in ("Id", "NodeIndex", "QuestPrefabRefHash", "UkHash1"):
            dst_datum[key] = src_datum[key]
        assert dst_datum == src_datum, "Unexpected transform/streaming data delta"
        identities.append(expected_ref)
    assert [val(ref) for ref in output["nodeRefs"]] == identities
    assert len(block["descriptors"]) == 1
    descriptor = block["descriptors"][0]
    original_descriptor = source_block["descriptors"][700]
    assert descriptor["numNodeRanges"] == 2 and len(descriptor["variants"]) == 1
    variant = descriptor["variants"][0]
    assert variant["rangeIndex"] == 1 and variant["enabledByDefault"] == 0
    assert variant["variantId"] == 3917072702 and variant["parentVariantID"] == 0
    assert val(variant["name"]) == "PTFRMV_TowerStreet"
    assert val(variant["nodeRef"]) == "$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env"
    for key in ("blockIndex", "level", "category", "questPrefabNodeRef", "streamingBox"):
        assert descriptor[key] == original_descriptor[key], key
    assert descriptor["level"] == 1
    assert val(descriptor["data"]["DepotPath"]) == manifest["resources"][0]
    assert manifest["resources"] == ["towercontinued\\misty_viktor_world\\trucks_alley_r7.streamingsector", "towercontinued\\misty_viktor_world\\trucks_alley_r7.streamingblock"]
    source_root = Path(manifest["source_root"])
    assert sha(source_root / manifest["resources"][0]) == manifest["sha256"] == manifest["sector_sha256"]
    assert sha(source_root / manifest["resources"][1]) == manifest["block_sha256"]
    assert sorted(str(p.relative_to(source_root)) for p in source_root.rglob("*") if p.is_file()) == sorted(manifest["resources"])
    for key in ("explicit_npc_community_scene_commands", "story_fact_writes", "private_phase_changes", "record_mutations", "global_ai_changes"):
        assert manifest[key] == 0
    record = read(AUDIT / "r7_trucks_record.json")
    assert record["record"] == "Vehicle.v_utility4_militech_behemoth_police"
    assert record["record_hash"] == 188555135153 and record["type"] == "gamedataVehicle_Record"
    assert record["fields"]["savable"] == "False"
    report = {"status": "PASS", "nodes": 2, "placements": 2, "exact_source_equality": True, "empty_default_and_private_controlled_range": True, "sector_sha256": manifest["sector_sha256"], "block_sha256": manifest["block_sha256"], "live_lifecycle": "UNVERIFIED; parked state, occupants, duplication and Stop must be observed"}
    (AUDIT / "r7_trucks_tests.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report))
    return report


if __name__ == "__main__":
    main()
