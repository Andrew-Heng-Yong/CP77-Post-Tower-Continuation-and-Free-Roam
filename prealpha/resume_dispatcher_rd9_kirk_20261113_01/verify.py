"""Compare the serialized successor to the installed phase and saved wait."""
from copy import deepcopy
import math
from zlib import crc32
from prepare import HERE, RD8, OBSERVATION, FACT, read, sha, write
from compare_entrances import load_export, normalize


def main():
    evidence = HERE / "evidence_01"
    pins = read(evidence / "inputs.json")
    old = pins["root"]["raw"]
    assert sha(old) == pins["root"]["raw_sha256"]
    receipt = HERE / "graph_01/readback.json"
    result = read(receipt)
    assert sha(result["path"]) == result["sha256"]
    assert sha(result["path"] + ".json") == result["export_sha256"]
    original = normalize(load_export(old + ".json"))
    repaired = normalize(load_export(result["path"] + ".json"))
    expected = deepcopy(original)
    root, = [scope for scope in expected["graphs"] if scope["path"] == "root"]
    for node in root["nodes"]:
        if node["id"] in (9, 61010):
            identity = node["parameters"]["condition"]["type"]["scriptCondition"]["lifePathId"]
            name = identity["$value"].encode()
            assert identity["$storage"] == "string" and name == b"LifePaths.StreetKid"
            identity.update({"$storage": "uint64", "$value": str((len(name) << 32) | crc32(name))})
    for node_id in (61013, 61014):
        node, = [node for node in root["nodes"] if node["id"] == node_id]
        terms = node["parameters"]["condition"]["conditions"]
        assert terms[0]["$type"] == "questDistanceCondition"
        assert terms[0]["type"]["comparisonType"] == "Greater"
        assert terms[0]["type"]["distanceDefinition2"]["distanceValue"] == 50
        assert terms[1]["type"]["type"] == "MinorQuestAndSts"
        terms[0] = {"$type": "questFactsDBCondition", "type": {
            "$type": "questVarComparison_ConditionType", "comparisonType": "Equal", "factName": FACT, "value": 1,
        }}
    assert expected == repaired
    assert "questTriggerCondition" in str(next(n for n in root["nodes"] if n["id"] == 61014))
    marker = read(OBSERVATION / "bar_anchor.json")["sectors"][0]["markers"][0]
    anchor = marker["position"]
    save_position = (-1327.788330078125, -1003.420166015625, 12.345008850097656)
    distance = math.dist(anchor, save_position)
    assert 62.9 < distance < 63.0
    assert marker["streaming_distance"] == 10 < 50 < distance
    fixtures = ((0, False), (10, False), (49.99, False), (50, False), (50.01, True), (62.92, True))
    assert all((value**2 > 2500.0) == expected_result for value, expected_result in fixtures)
    baseline_compile = read(RD8 / "compile_01/result.json")
    assert baseline_compile["status"] == "PASS"
    write(evidence / "assessment.json", {"status": "PASS", "readback_sha256": sha(receipt),
        "changed_nodes": [61013, 61014], "save_distance_m": distance, "distance_cases": fixtures,
        "content_gate_preserved": True, "saved_wait_identity_preserved": True, "gameplay": "PENDING"})
    print("Verified the serialized two-operand change and the 50 m boundary.")


if __name__ == "__main__":
    main()
