"""Verify the exact native lift devices, installed delta and compiled repair."""

import re
from pathlib import Path

from build import BASE_SHA, GAME, REDS, ROOT, read, sha, verified_baseline, verify_rows, write


LIFT_PATH = (
    "$/03_night_city/c_watson/little_china/loc_q115_mistyc_mistys_ripperdoc_roof_prefabDR5IG6A/"
    "loc_q115_mystic_mistys_ripperdoc_roof_gameplay_prefab75UZAWI/"
    "loc_q115_mystic_mistys_ripperdoc_roof_devices_prefabNCP6VPY/lift_2_floors_prefabXK7C7ZI/"
)
LIFT_ALIAS = "#q115_ripperdoc_roof_elevator"


def root_chunk(path):
    return read(Path(path))["Data"]["RootChunk"]


def device_actions(value, owner=None):
    if isinstance(value, list):
        for entry in value:
            yield from device_actions(entry, owner)
    elif isinstance(value, dict):
        if value.get("$type") == "questInteractiveObjectManagerNodeDefinition":
            owner = value["id"]
        if value.get("$type") == "questDeviceManager_NodeTypeParams":
            properties = tuple((prop["name"]["$value"], prop["value"]["Value"])
                               for prop in value["actionProperties"] if "Value" in prop["value"])
            yield (owner, value["deviceControllerClass"]["$value"], value["deviceAction"]["$value"],
                   value["objectRef"]["$value"], properties)
        for entry in value.values():
            yield from device_actions(entry, owner)


def native_actions(evidence, filename, provider):
    entries = [row for row in evidence["hits"]
               if row["depot"].split("\\")[-1] == filename and Path(row["archive"]).name == provider]
    assert len(entries) == 1
    entry = entries[0]
    assert sha(Path(entry["raw"])) == entry["sha256"]
    assert sha(Path(entry["json"])) == entry["json_sha256"]
    return set(device_actions(root_chunk(entry["json"])))


def ref_hash(value):
    result = 0xCBF29CE484222325
    for byte in value.encode("utf-8"):
        result = ((result ^ byte) * 0x100000001B3) & ((1 << 64) - 1)
    return str(result)


def placement(evidence, sector, part, template):
    providers = [row for row in evidence["rows"] if row["depot"].endswith(f"\\{sector}.streamingsector")]
    assert {Path(row["archive"]).name for row in providers} == {
        "basegame_3_nightcity.archive", "ep1_1_nightcity.archive"
    }
    ref = LIFT_PATH + part
    positions = []
    for row in providers:
        assert sha(Path(row["raw"])) == row["sha256"]
        assert sha(Path(row["json"])) == row["json_sha256"]
        sector_root = root_chunk(row["json"])
        assert sum(node["$value"].split(";")[0] == ref for node in sector_root["nodeRefs"]) == 1
        matches = [item for item in sector_root["persistentNodes"] if item["globalNodeId"]["hash"] == ref_hash(ref)]
        assert len(matches) == 1
        instance = matches[0]
        node = sector_root["nodes"][int(instance["nodeIdx"])]["Data"]
        assert node["entityTemplate"]["DepotPath"]["$value"].endswith(template)
        positions.append(instance["transform"]["position"])
    assert positions[0] == positions[1]
    return {key: positions[0][key] for key in "XYZ"}


def method(source, name):
    start = source.index(f"func {name}(")
    return source[start:source.index("\n  }", start)]


def ordered(source, *tokens):
    index = 0
    for token in tokens:
        index = source.index(token, index) + len(token)


def main():
    base = verified_baseline()
    candidate = ROOT / "candidate_02"
    manifest_path = candidate / "core_manifest.json"
    manifest = read(manifest_path)
    compile_path = candidate / "compile_01"
    compile_proof = read(compile_path / "assessment.json")
    assert manifest["baseline_sha256"] == BASE_SHA and manifest["changed_paths"] == [REDS]
    assert manifest["compile_assessment_sha256"] == sha(compile_path / "assessment.json")
    assert compile_proof["status"] == "PASS" and compile_proof["changed_sources"] == [REDS]
    assert compile_proof["compiled_sha256"] == sha(compile_path / "cache/compiled.redscripts")
    verify_rows(candidate / "package", manifest["core_files"])
    old_core = {row["path"]: row for row in base["core_files"]}
    new_core = {row["path"]: row for row in manifest["core_files"]}
    assert old_core.keys() == new_core.keys()
    assert {path for path in old_core if old_core[path] != new_core[path]} == {REDS}

    work = ROOT / "work"
    ending = read(work / "native_01/providers.json")
    assert len(ending["archives"]) == len(read(work / "roof_02/providers.json")["archives"])
    provider = "ep1_2_gamedata.archive"
    opt_in = native_actions(ending, "q307_00_opt_in.questphase", provider)
    assert (45, "LiftControllerPS", "ForceEnabled", LIFT_ALIAS, ()) in opt_in
    assert (46, "LiftControllerPS", "ShowFloor", LIFT_ALIAS, (("floorNumber", 1),)) in opt_in
    pickup = native_actions(ending, "q307_01_pickup.scene", provider)
    assert (884, "LiftControllerPS", "ForceDisabled", LIFT_ALIAS, ()) in pickup
    assert (881, "DoorControllerPS", "ForceLock", "#q115_dvc_misty_roof_doors", ()) in pickup
    for src, node in (("q307_04_cabride.questphase", 17), ("q307.questphase", 5)):
        arrival = native_actions(ending, src, provider)
        assert (node, "ElevatorFloorTerminalControllerPS", "ForceDisabled", LIFT_PATH + "lift_terminal_1", ()) in arrival
        assert (node, "DoorControllerPS", "ForceSeal", LIFT_PATH + "lift_door_1", ()) in arrival
    assert not any(LIFT_ALIAS == entry[3] or entry[3].startswith(LIFT_PATH)
                   for entry in native_actions(ending, "q307_cleanup.questphase", provider))

    decoded = read(work / "decoded_roof_02/manifest.json")
    street = placement(decoded, "interior_-49_37_0_0", "lift_terminal_1", "elevator_floor_terminal_1.ent")
    roof = placement(decoded, "interior_-49_37_1_0", "lift_terminal_2", "elevator_floor_terminal_1.ent")
    landing = placement(decoded, "interior_-25_18_0_1", "lift_door_1", "common_lift_door.ent")
    assert abs(street["Z"] - landing["Z"]) < 2.0 and roof["Z"] - street["Z"] > 30.0

    old = (GAME / REDS).read_text(encoding="utf-8-sig")
    new = (candidate / "package" / REDS).read_text(encoding="utf-8-sig")
    for name in ("Completed", "Safe", "SafeStreet", "RefreshStreetCleanupPermit"):
        assert method(old, name) == method(new, name), name
    assert new.count(".SetFact(") == old.count(".SetFact(")
    assert new.count("persistent let") == old.count("persistent let")
    readback_path = compile_path / "compiled.script"
    compiled = readback_path.read_text(encoding="utf-8-sig")
    driver = compiled[compiled.index("class PTFR.MistyViktorAuto.MistyViktorAuto "):]
    assert LIFT_PATH in method(driver, "RooftopLiftNode")
    ordered(method(driver, "RooftopLiftController"), ".GetParents(", "as LiftControllerPS", "ArraySize(floors",
            ".GetFloorID(0) == streetID", ".GetFloorID(1) == roofID")
    ordered(method(driver, "Poll"), "expectedEpoch != this.epoch", "this.Completed(q",
            "StartupCoverLC1.GameplayReleased(game", "this.SafeStreet(p", ".IsDead()", "this.RestoreRooftopLift(game")
    repair = method(driver, "RestoreRooftopLift")
    ordered(repair, '"lift_terminal_1"', '"lift_terminal_2"', "as ElevatorFloorTerminal", "this.RooftopLiftController(",
            ".IsMoving()", ".IsDisabled()", 'n"ForceEnabled", n"lift"', 'n"ForceEnabled", n"street-panel"',
            ".m_isHidden", 'n"ShowFloor", n"roof-stop"', '"lift_door_1"', "as Door", ".IsSealed()",
            'n"ForceUnseal", n"street-landing"', "this.rooftopLiftRestrictionsCleared = true")
    assert re.findall(r'\.RequestRooftopLiftAction\(.*?, n"([^"]+)"', repair) == [
        "ForceEnabled", "ForceEnabled", "ShowFloor", "ForceUnseal"
    ]
    dispatch = method(driver, "RequestRooftopLiftAction")
    ordered(dispatch, "ArrayContains(this.rooftopLiftActions", ".GetQuestActionByName(",
            "as QuestShowFloor", ".SetProperties(1)", ".ExecutePSAction(", "ArrayPush(this.rooftopLiftActions")
    for name in ("OnAttach", "OnRestored"):
        assert "this.ResetRooftopLift()" in method(driver, name)
    assert "ArrayClear(this.rooftopLiftActions)" in method(driver, "ResetRooftopLift")

    write(candidate / "verification.json", {
        "status": "PASS", "candidate_sha256": sha(manifest_path), "compiled_readback_sha256": sha(readback_path),
        "archive_providers_inventoried": len(ending["archives"]),
        "native_street_panel": street, "native_roof_panel": roof, "native_street_landing": landing,
        "checked": ["retail ending writers and floor visibility action", "exact two-floor devices in base and EP1",
                    "complete installed source delta", "compiled completion guard, binding and actions",
                    "request reset on save restore", "existing street cleanup policy preserved"],
        "gameplay": "PENDING",
    })
    print("Verified the native devices, Tower actions and compiled rooftop lift repair.")


if __name__ == "__main__":
    main()
