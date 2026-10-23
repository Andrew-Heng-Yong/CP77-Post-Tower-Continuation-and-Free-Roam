"""Bounded source-only audit of the two Tower alley vehicle spawners."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "research/misty_viktor_world"
SECTOR = ROOT / "research/phase2b_p4/variant_sectors/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/ep1/exterior_-13_9_0_1.streamingsector.json"
ENTITY = AUDIT / "r7_trucks_sources/json/ep1/vehicles/utility/v_utilty4_militech_behemoth_police_01.ent.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def value(obj):
    return obj.get("$value") if isinstance(obj, dict) else obj


def walk(obj, path=()):
    if isinstance(obj, dict):
        yield path, obj
        for key, item in obj.items():
            yield from walk(item, path + (key,))
    elif isinstance(obj, list):
        for key, item in enumerate(obj):
            yield from walk(item, path + (key,))


sector = load(SECTOR)["Data"]["RootChunk"]
entity = load(ENTITY)["Data"]["RootChunk"]
record = load(AUDIT / "r7_trucks_record.json")
rows = []
for ni, di in ((56, 66), (57, 67)):
    node = sector["nodes"][ni]["Data"]
    datum = sector["nodeData"]["Data"][di]
    assert node["$type"] == "worldPopulationSpawnerNode"
    assert datum["NodeIndex"] == ni
    assert value(node["objectRecordId"]) == "Vehicle.v_utility4_militech_behemoth_police"
    assert node["spawnOnStart"] == 1 and node["isVehicle"] == 0
    assert node["alwaysSpawned"] == "default__false_"
    rows.append({"node_index": ni, "data_index": di, "node": node, "placement": datum})

actions = []
q307_root = ROOT / "research/q307_extracted/json"
for path in q307_root.rglob("*.questphase.json"):
    resource = load(path)
    for ancestry, item in walk(resource):
        if item.get("$type") != "questTogglePrefabVariant_NodeTypeParams":
            continue
        states = [s for s in item.get("variantStates", []) if value(s.get("name")) == "q307_misty_alley"]
        if states:
            actions.append({"resource": str(path.relative_to(ROOT)), "json_path": list(ancestry), "owner": item["prefabNodeRef"], "states": states})

chunks = entity["compiledData"]["Data"]["Chunks"]
types = sorted(c["$type"] for c in chunks)
ai = next(c for c in chunks if c["$type"] == "AIVehicleAgent")
stub = next(c for c in chunks if c["$type"] == "gameEntityStubComponent")
assert ai["initCmd"] is None
assert value(stub["persistentState"]["Data"]["ownerCommunityEntryName"]) == "None"
fields = record["fields"]
report = {
    "status": "SOURCE_SUPPORTED_TWO_VEHICLE_CANDIDATE_LIVE_LIFECYCLE_PENDING",
    "source_sector": str(SECTOR.relative_to(ROOT)),
    "source_json_sha256": hashlib.sha256(SECTOR.read_bytes()).hexdigest(),
    "source_block_descriptor": 700,
    "source_variant": "q307_misty_alley",
    "variant_owner": "$/03_night_city/c_watson/little_china/wlc_02/#wlc_02_b_env",
    "source_range_index": 1,
    "source_range": [1, 68],
    "selected": rows,
    "identification": "Two native Tower NCPD Behemoth vehicle spawners at the user's missing-truck position; excluded from the passive R3/R6 overlay.",
    "record": record["record"],
    "record_type": record["type"],
    "record_properties": {key: fields[key] for key in ("appearanceName", "savable", "preventionPassengers", "randomPassengers", "weapons", "canBeActiveVehicle", "minVehiclePassengersCount", "maxVehiclePassengersCount", "enableDestruction", "tags")},
    "entity_template": "ep1\\vehicles\\utility\\v_utilty4_militech_behemoth_police_01.ent",
    "entity_json_sha256": hashlib.sha256(ENTITY.read_bytes()).hexdigest(),
    "entity_class": entity["entity"]["Data"]["$type"],
    "entity_default_appearance": entity["defaultAppearance"],
    "entity_appearances": entity["appearances"],
    "entity_component_types": types,
    "ai_initialization": ai,
    "entity_stub": stub,
    "vanilla_variant_actions": actions,
    "classification": "Full native vehicle objects; not static visual props. Standard vehicle AI, physics, interaction and occupant components exist. No explicit crew/community/scene/drive command is placed by these two spawners.",
    "minimal_candidate": "Copy only node56/57 and placement66/67 into a private empty-default sector controlled by existing PTFRMV_TowerStreet; retain generic vehicle record and all spawn settings/transform. Never enable original q307_misty_alley or q307 communities.",
    "no_claims": ["isVehicle=0 is retained; it is NOT proof of absent vehicle behavior or occupants", "randomPassengers exists; zero incidental occupants is unproven", "source and offline readbacks do not prove runtime cleanup, stability or duplicate suppression"],
    "live_checks": ["Exactly two expected trucks in original positions", "Stationary/no unexpected crew or driving", "Leave and return without duplicates", "Stop outside controller exclusion radius, return with both private trucks absent", "Re-enable and return without duplicates"]
}
(AUDIT / "r7_trucks_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "selected": len(rows), "entity_type": report["entity_class"], "variant_actions": len(actions)}))
