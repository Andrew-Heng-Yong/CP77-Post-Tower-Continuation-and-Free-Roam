"""Verify the saved wait, full graph delta and the stock lock operand."""
from copy import deepcopy
from prepare import HERE, STAGE, read, sha, write
from compare_entrances import load_export, normalize


def root(model):
    return next(scope for scope in model["graphs"] if scope["path"] == "root")


def main():
    evidence = HERE / "evidence_01"
    pins = read(evidence / "inputs.json")
    old = pins["root"]["path"]
    receipt = HERE / "graph_01/readback.json"
    packed = read(receipt)
    assert sha(old + ".json") == pins["root"]["export_sha256"]
    assert sha(packed["path"]) == packed["sha256"]
    assert sha(packed["path"] + ".json") == packed["export_sha256"]
    assert sha(pins["donor"]["export_path"]) == pins["donor"]["export_sha256"]
    assert sha(STAGE) == pins["playtest_sha256"]
    before = normalize(load_export(old + ".json"))
    after = normalize(load_export(packed["path"] + ".json"))
    donor = normalize(load_export(pins["donor"]["export_path"]))
    lock = next(n for n in root(donor)["nodes"] if n["id"] == 43)["parameters"]["condition"]
    assert lock == {"$type": "questContentCondition",
                    "type": {"$type": "questContentLock_ConditionType", "isContentBlocked": 0}}
    expected = deepcopy(before)
    for id_ in (61013, 61014):
        node = next(n for n in root(expected)["nodes"] if n["id"] == id_)
        assert node["type"] == "questPauseConditionNodeDefinition"
        predicate = node["parameters"]["condition"]
        assert predicate["operation"] == "AND"
        terms = predicate["conditions"]
        assert terms[0]["type"]["factName"] == "PTFRS29_mq017_streetkid_ResumeOutsideBar"
        assert terms[1]["type"] == {"$type": "questContentToken_ConditionType", "type": "MinorQuestAndSts"}
        if id_ == 61014:
            assert terms[2]["$type"] == "questTriggerCondition"
        terms[1] = lock
    assert expected == after
    write(evidence / "assessment.json", {"status": "PASS", "readback_sha256": sha(receipt),
        "exact_changed_nodes": [61013, 61014], "fresh_gate_unchanged": True, "gameplay": "PENDING"})
    print("Verified two resumed-stage predicates and the unchanged fresh admission graph.")


if __name__ == "__main__":
    main()
