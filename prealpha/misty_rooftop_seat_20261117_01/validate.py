"""Read back the native seat, free-roam gate, ArchiveXL ID and staged package."""

import binascii
import math
import re
from pathlib import Path

from build import ARCHIVE, BASE_SHA, CHANGED, GAME, REDS, ROOT, XL, plain, read, sha, verified_baseline, verify_rows, write


WORK = ROOT / "work"
DEPOT = r"towercontinued\misty_rooftop_seat\gate.questphase"


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def handle_id(handle):
    return handle.get("HandleId", handle.get("HandleRefId"))


def resolver(document):
    handles = {node["HandleId"]: node["Data"] for node in walk(document) if "HandleId" in node}
    return lambda handle: handles[handle_id(handle)]


def fact_tests(condition, resolve):
    assert condition["operation"] == "AND"
    facts = {}
    for child in condition["conditions"]:
        comparison = resolve(resolve(child)["type"])
        assert comparison["comparisonType"] == "Equal"
        facts[comparison["factName"]] = comparison["value"]
    assert len(facts) == len(condition["conditions"])
    return facts


def gate_check(document, manifest):
    resolve = resolver(document)
    root = document["Data"]["RootChunk"]
    assert root["phasePrefabs"] == [] and root["inplacePhases"] == []
    nodes = {resolve(h)["id"]: resolve(h) for h in resolve(root["graph"])["nodes"]}
    assert set(nodes) == set(range(14))
    sockets = {handle_id(h): (owner, resolve(h)["name"]["$value"])
               for owner, node in nodes.items() for h in node["sockets"]}
    connections = [resolve(c) for n in nodes.values() for h in n["sockets"] for c in resolve(h)["connections"]]
    edges = [(*sockets[handle_id(c["source"])], *sockets[handle_id(c["destination"])]) for c in connections]
    expected = {
        (0, "Out", 1, "In"), (1, "Out", 2, "In"), (2, "Out", 3, "In"),
        (3, "True", 4, "In"), (3, "False", 2, "In"), (4, "Out", 5, "In"),
        (5, "Out", 6, "In"), (6, "Out", 7, "in"), (7, "out", 8, "In"),
        (8, "Out", 9, "In"), (9, "Out", 2, "In"), (7, "Default INT", 10, "In"),
        (10, "Out", 11, "In"), (11, "Out", 12, "In"), (12, "Out", 13, "In"),
        (13, "Out", 9, "In"),
    }
    assert set(edges) == expected and all(edges.count(edge) == 2 for edge in expected)
    for node in (2, 3):
        assert fact_tests(resolve(nodes[node]["condition"]), resolve) == manifest["guards"]
    assert fact_tests(resolve(nodes[12]["condition"]), resolve) == {"PTFRMistySeat_Depart": 1}
    assert resolve(resolve(nodes[9]["condition"])["type"])["seconds"] == 1
    assert nodes[7]["sceneLocation"]["nodeRef"]["$value"] == manifest["anchor_ref"]
    assert nodes[7]["sceneFile"]["DepotPath"]["$value"] == r"towercontinued\misty_rooftop_seat\sit.scene"
    assert all(x["factName"].startswith("PTFRMistySeat_") for x in walk(root) if x.get("$type") == "questSetVar_NodeType")


def scene_check(document, manifest):
    root = document["Data"]["RootChunk"]
    resolve = resolver(document)
    nodes = {resolve(h)["nodeId"]["id"]: resolve(h) for h in resolve(root["sceneGraph"])["graph"]}
    assert set(nodes) == {1, 4, 8, 10, 33, 36, 55, 943, 2000, 3030, 3031}
    assert [p["actorId"]["id"] for p in root["actors"] + root["playerActors"]] == [0, 1, 2]
    assert {p["actorName"] for p in root["actors"]} == {"v_male_tpp", "v_female_tpp"}
    assert all(p["spawnDespawnParams"]["spawnOnStart"] == 0 for p in root["actors"])
    assert root["playerActors"][0]["acquisitionPlan"] == "findInContext"
    assert not any("johnny" in str(v).lower() for item in walk(root) for v in item.values() if isinstance(v, str))

    expected = {1: {4, 3030}, 4: {3031}, 3031: {8}, 8: {10, 36}, 10: {33},
                33: {2000, 943, 55}, 3030: {2000}}
    for i, node in nodes.items():
        assert {edge["nodeId"]["id"] for s in node["outputSockets"] for edge in s["destinations"]} == expected.get(i, set())
    for node, icon in ((4, "ChoiceCaptionParts.SitIcon"), (10, "ChoiceCaptionParts.GetUpIcon")):
        option = nodes[node]["options"]
        assert len(option) == 1
        actual = option[0]["iconTagIds"][0]["$value"]
        assert actual in (icon, str(binascii.crc32(icon.encode()) | (len(icon) << 32)))
    native = lambda node: resolve(nodes[node]["questNode"])
    start = resolve(native(36)["paramsV1"])
    stop = resolve(native(55)["paramsV1"])
    assert start["function"] == "UseWorkspot" and start["entryId"]["id"] == 11 and start["isPlayer"] == 1
    assert start["playAtActorLocation"] == 0 and stop["function"] == "StopWorkspot"
    assert native(55)["entityReference"]["reference"]["$value"] == "#player"
    assert stop["instant"] == 1 and stop["repeatCommandOnInterrupt"] == 1
    assert resolve(native(943)["type"])["tier"] == "Tier1_FullGameplay"
    assert fact_tests(resolve(native(3030)["condition"]), resolve) == {"PTFRMistySeat_Depart": 1, "PTFRMistySeat_Using": 0}
    assert [(x["factName"], x["value"]) for x in walk(root) if x.get("$type") == "questSetVar_NodeType"] == [("PTFRMistySeat_Using", 1)]

    assert len(root["workspots"]) == len(root["workspotInstances"]) == 1
    workspot = resolve(root["workspots"][0])
    instance = root["workspotInstances"][0]
    assert instance["workspotInstanceId"] == start["workspotInstanceId"] and instance["dataId"] == workspot["dataId"]
    assert workspot["workspotResource"]["DepotPath"]["$value"] == manifest["workspot"]
    assert instance["originMarker"]["nodeRef"]["$value"] == manifest["anchor_ref"] and instance["playAtActorLocation"] == 0
    anchor, position, target = manifest["anchor"], instance["localTransform"], manifest["seat"]
    rotation = anchor["orientation"]
    assert abs(rotation["i"]) < 1e-6 and abs(rotation["j"]) < 1e-6
    yaw = 2 * math.atan2(rotation["k"], rotation["r"])
    x, y, z = (position["position"][k] for k in "XYZ")
    offset = (math.cos(yaw)*x - math.sin(yaw)*y, math.sin(yaw)*x + math.cos(yaw)*y, z)
    assert math.dist([anchor["position"][k]+v for k, v in zip("XYZ", offset)],
                     [target["position"][k] for k in "XYZ"]) < 0.001
    local_q, target_q = position["orientation"], target["orientation"]
    combined_yaw = yaw + 2 * math.atan2(local_q["k"], local_q["r"])
    assert abs(math.remainder(combined_yaw - 2*math.atan2(target_q["k"], target_q["r"]), 2*math.pi)) < 0.001


def crc16(key):
    state = 65535
    for byte in key.encode():
        state ^= byte << 8
        for _ in range(8):
            state = ((state << 1) ^ (0x1021 if state & 0x8000 else 0)) & 65535
    return state


def xl_check(package, evidence):
    parent = next(x for x in evidence["hits"] if x["depot"] == r"ep1\quest\ep1.quest")
    assert sha(Path(parent["raw"])) == parent["sha256"] and sha(Path(parent["json"])) == parent["json_sha256"]
    root = read(Path(parent["json"]))["Data"]["RootChunk"]["graph"]["Data"]
    native_ids = {node["Data"]["id"] for node in root["nodes"]}
    old, new = (GAME / XL).read_bytes(), (package / XL).read_bytes()
    addition = read(WORK / "pack_01/readback.json")["xl_addition"].encode()
    assert new.count(addition) == 1 and new.replace(addition, b"", 1) == old
    ids = {}
    files = sorted(path for folder in (GAME / "archive/pc", GAME / "mods") if folder.exists()
                   for path in folder.rglob("*.xl"))
    for path in files:
        plain(path)
        contents = (package / XL if path == GAME / XL else path).read_text(encoding="utf-8-sig")
        match = re.search(r"(?ms)^quest:[ \t]*\n(.*?)(?=^[a-zA-Z_][^\n]*:|\Z)", contents)
        if not match:
            assert not re.search(r"(?m)^quest\s*:", contents)
            continue
        phases = re.search(r"(?ms)^  phases:[ \t]*\n(.*?)(?=^  [a-zA-Z_][^\n]*:|\Z)", match[1])
        if not phases:
            assert "phases:" not in match[1]
            continue
        prefix, *blocks = re.split(r"(?m)^    - path:[ \t]*", phases[1])
        assert all(not line.strip() or line.lstrip().startswith("#") for line in prefix.splitlines())
        for block in blocks:
            depot = block.splitlines()[0].strip()
            p = re.search(r"(?m)^      parent: (.+)$", block)
            assert p, path
            if p[1].strip() != r"ep1\quest\ep1.quest":
                continue
            assert re.search(r"(?m)^        node: \[1\]\s*$", block) and re.search(r"(?m)^        socket: Out\s*$", block)
            key = depot + ":1"
            ident = binascii.crc_hqx(key.encode(), 65535)
            assert ident == crc16(key) and ident not in native_ids and ident not in ids, (depot, ids.get(ident), ident)
            ids[ident] = depot
    assert list(ids.values()).count(DEPOT) == 1
    return len(files), len(ids), next(i for i, depot in ids.items() if depot == DEPOT)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", nargs="?", default="candidate_01", choices=("candidate_01", "candidate_02", "candidate_03"))
    candidate = ROOT / parser.parse_args().candidate
    package = candidate / "package"
    baseline = verified_baseline()
    manifest_path = candidate / "core_manifest.json"
    manifest = read(manifest_path)
    assert manifest["baseline_sha256"] == BASE_SHA
    verify_rows(package, manifest["core_files"])
    before = {v["path"]: v for v in baseline["core_files"]}
    after = {v["path"]: v for v in manifest["core_files"]}
    assert before.keys() == after.keys() and {p for p in before if before[p] != after[p]} == set(CHANGED)
    asset_path = WORK / "pack_01/readback.json"
    assets = read(asset_path)
    assert manifest["asset_assessment_sha256"] == sha(asset_path)
    assert assets["unchanged_members"] == 1749 and assets["packed_members"] == 1751 and assets["native_resource_changes"] == 0
    verify_rows(package, assets["package_files"])
    scene = read(WORK / "scene_01/manifest.json")
    for resource in assets["private_resources"]:
        assert sha(Path(resource["raw"])) == resource["sha256"] and sha(Path(resource["json"])) == resource["json_sha256"]
        (gate_check if resource["depot"] == DEPOT else scene_check)(read(Path(resource["json"])), scene)
    xl_files, registrations, new_id = xl_check(package, read(WORK / "native_01/providers.json"))

    compile_dir = candidate / "compile_01"
    proof = read(compile_dir / "assessment.json")
    assert proof["status"] == "PASS" and proof["changed_sources"] == [REDS]
    assert sha(compile_dir / "assessment.json") == manifest["compile_assessment_sha256"]
    assert sha(compile_dir / "cache/compiled.redscripts") == proof["compiled_sha256"]
    compiled_path = compile_dir / "compiled.script"
    code = compiled_path.read_text(encoding="utf-8-sig")
    start = code.index("func RefreshRooftopSeat(")
    driver = code[start:code.index("\n  }", start)]
    for token in ('"PTFRMistySeat_Registered"', "this.Completed(", "StartupCoverLC1.GameplayReleased(",
                  "GetLocalPlayerControlledGameObject()", "CyberwarePolicy.Safe(", '"lift_terminal_2"', '"PTFRMistySeat_Permit"'):
        assert token in driver
    assert set(re.findall(r'n"(PTFRMistySeat_\w+)"', driver)) == {
        "PTFRMistySeat_Registered", "PTFRMistySeat_Permit", "PTFRMistySeat_Depart",
        "PTFRMistySeat_Active", "PTFRMistySeat_Interrupted",
    }
    write(candidate / "verification.json", {
        "status": "PASS", "candidate_sha256": sha(manifest_path), "compiled_readback_sha256": sha(compiled_path),
        "xl_files": xl_files, "checked_phase_registrations": registrations, "seat_phase_id": new_id,
        "packed_members": 1751, "preserved_prior_members": 1749,
        "checked": ["retail chair animation and native placement", "V-only Sit and Get Up graph",
                    "normal exit, departure and interruption paths", "private fact writes and native guard",
                    "archive provider and quest registration uniqueness", "compiled permit driver and full payload"],
        "gameplay": "PENDING",
    })
    print(f"Verified the native seat, {registrations} EP1 registrations and the staged build. Seat registration {new_id}.")


if __name__ == "__main__":
    main()
