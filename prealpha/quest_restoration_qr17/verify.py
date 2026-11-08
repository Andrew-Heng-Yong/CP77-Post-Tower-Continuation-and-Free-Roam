"""Verify typed readback against the native route and the QR13 predecessor."""
from pathlib import Path
from collections import Counter

from prepare import HERE, QR13, PENDING, HELD, TAG, COIN, DUMPSTER, SPRAY, Resource, checked, read, sha, write

NEW = {str(i) for i in range(1120, 1132)}


def graph(doc):
    result = Resource(doc).normalize()
    assert not result["errors"], result["errors"]
    return result


def evaluate(node, facts, journals):
    kind = node["$type"]
    if kind == "questLogicalCondition":
        values = [evaluate(p, facts, journals) for p in node["conditions"]]
        if node["operation"] == "OR":
            return any(values)
        assert node["operation"] == "AND"
        return all(values)
    if kind in {"questFactsDBCondition", "questJournalCondition"}:
        return evaluate(node["type"], facts, journals)
    if kind == "questVarComparison_ConditionType":
        actual = facts.get(node["factName"], 0)
        assert node["comparisonType"] == "Equal"
        return actual == node["value"]
    assert kind == "questJournalEntryState_ConditionType" and not node["inverted"], kind
    return journals.get(node["path"]["realPath"]) == node["state"]


def main():
    prior, = read(QR13 / "coordinator/brendan_06/serialized_01/manifest.json")["resources"]
    old = graph(read(checked(prior["readback_json"], prior["readback_json_sha256"])))
    serialized = read(HERE / "serialized_01/manifest.json")
    checked(serialized["raw"], serialized["sha256"])
    proposed, = read(HERE / "proposal_01/plan.json")["resources"]
    actual = graph(read(checked(serialized["readback"], serialized["readback_sha256"])))
    assert actual == graph(read(checked(proposed["proposed_json"], proposed["proposed_json_sha256"])))
    assert all(actual[k] == old[k] for k in actual if k != "graphs")
    assert actual["graphs"].keys() == old["graphs"].keys()
    assert all(actual["graphs"][g] == old["graphs"][g] for g in actual["graphs"] if g != "root")
    old_root = old["graphs"]["root"]
    root = actual["graphs"]["root"]
    nodes = root["nodes"]
    assert root["entries"] == old_root["entries"]
    assert set(nodes) - set(old_root["nodes"]) == NEW
    for node_id, prior in old_root["nodes"].items():
        if node_id in {"1002", "1004"}:
            old_cond = prior["payload"]["condition"]
            new_cond = nodes[node_id]["payload"]["condition"]
            assert old_cond["operation"] == new_cond["operation"] == "OR"
            assert new_cond["conditions"][:-1] == old_cond["conditions"]
            assert new_cond["conditions"][-1] == nodes["1120"]["payload"]["condition"]
        else:
            assert prior == nodes[node_id], node_id
    before_edges = Counter(map(tuple, old_root["edges"]))
    after_edges = Counter(map(tuple, root["edges"]))
    assert before_edges - after_edges == Counter({
        ("1100", "False", "1008", "In"): 1, ("1110", "Ready", "1101", "In"): 1,
    })
    routes = (
        ("1100", "False", "1120", "In"), ("1120", "False", "1008", "In"), ("1120", "True", "1121", "In"),
        ("1121", "Out", "1110", "In1"), ("1110", "Ready", "1122", "In"), ("1122", "False", "1101", "In"),
        ("1122", "True", "1123", "In"), ("1123", "Out", "1124", "In"), ("1124", "Out", "1125", "In"),
        ("1125", "True", "1128", "In"), ("1128", "Out", "1126", "In"), ("1126", "Out", "1127", "Inactive"),
        ("1127", "Out", "1129", "In"), ("1129", "Out", "1130", "In"), ("1130", "Out", "34", "brendan_gone"),
        ("1125", "False", "1131", "In"), ("1131", "Out", "1110", "Release"),
    )
    assert after_edges - before_edges == Counter(routes)

    native, = (r for r in read(QR13 / "brendan_provider_validation_01/manifest.json")["resources"]
               if r["depot"].endswith("mq037_brendan.questphase"))
    native_graphs = graph(read(checked(native["json"], native["json_sha256"])))["graphs"]
    donor = native_graphs["root/25"]["nodes"]
    for node_id, original_id in zip(("1123", "1124", "1126", "1127"), ("38", "39", "40", "36"), strict=True):
        original = donor[original_id]
        assert nodes[node_id]["payload"] == original["payload"] | {"id": int(node_id)}
        assert nodes[node_id]["sockets"] == original["sockets"]
    native_root = native_graphs["root"]
    assert native_root["entries"]["brendan_gone"] == "30"
    for edge in (["30", "Out", "60", "In1"], ["60", "Out1", "28", "In1"], ["25", "Out1", "28", "In1"]):
        assert edge in native_root["edges"]
    assert ["0", "Out", "138", "In1"] in native_graphs["root/28"]["edges"]
    assert ["34", "Out1", "1111", "In"] in root["edges"]
    assert ["1111", "True", "1110", "Release"] in root["edges"]
    assert ["1110", "Out1", "1112", "In"] in root["edges"]
    assert actual["graphs"]["root/1110"]["nodes"]["6"]["payload"]["type"] == "Terminating"
    writers = {n: (nodes[n]["writes"][0]["factName"], nodes[n]["writes"][0]["value"]) for n in NEW if nodes[n]["writes"]}
    assert writers == {"1121": (PENDING, 1), "1128": (TAG + "_Issued", 1),
                       "1129": (TAG + "_Entered", 1), "1130": (PENDING, 0), "1131": (PENDING, 0)}
    assert not any(nodes[n]["reward"] for n in NEW)

    # Independent quest vectors expressed as game outcomes. They contain no
    # named save, archived history certificate or host-specific values.
    coin_phase = COIN + "/mq037_brendan"
    journals = {COIN: "Inactive", coin_phase: "Inactive"}
    for suffix in ("01_go_to_service", "01_go_to_service/description", "02_find_brendan", "02b_ask_clerk",
                   "02c_destroy_turret", "03_talk_brendan", "04_talk_theo"):
        journals[coin_phase + "/" + suffix] = "Inactive"
    journals |= {
        DUMPSTER: "Succeeded",
        DUMPSTER + "/mq037_brendan_dumpster/00_push_dumpster": "Succeeded",
        DUMPSTER + "/mq037_brendan_dumpster/01_talk_brendan": "Succeeded",
        SPRAY: "Succeeded",
        SPRAY + "/mq037_brendan_hooligan/00_deal_with_the_hooligan": "Succeeded",
        SPRAY + "/mq037_brendan_hooligan/01_talk_with_brendan": "Succeeded",
    }
    facts = dict.fromkeys(("PostTowerFreeRoamActive", "PTFRP0_DR13", "PTFRPA2_Finished", "q307_done",
                           "q307_finished", "q307_2079", "q307_main_game_killed", "q307_ep1_killed",
                           "PTFRU9_Support_Issued", "mq037_brendan_introduced", TAG + "_Permit"), 1)
    for n in ("1002", "1004"):
        assert not evaluate(old_root["nodes"][n]["payload"]["condition"], facts, journals), n
        assert evaluate(nodes[n]["payload"]["condition"], facts, journals), n
    pre = nodes["1120"]["payload"]["condition"]
    post = nodes["1125"]["payload"]["condition"]
    assert evaluate(pre, facts, journals)
    assert not evaluate(post, facts, journals)
    rejected = []
    for name, altered in ((DUMPSTER, "Inactive"), (SPRAY, "Failed"), (COIN, "Active"), (COIN, "Succeeded"),
                          (coin_phase + "/02_find_brendan", "Active"), (SPRAY, None)):
        assert not evaluate(pre, facts, journals | {name: altered}), name
        rejected.append([name, altered])
    for name, altered in ((TAG + "_Issued", 1), (TAG + "_Entered", 1), (PENDING, 1), (HELD, 1),
                          ("q307_main_game_killed", 0), ("q115_point_of_no_return", 1), ("mq037_done", 1),
                          ("mq037_final_scene_active", 1), ("mq037_clerk_aggroed", 1)):
        assert not evaluate(pre, facts | {name: altered}, journals), name
        rejected.append([name, altered])
    armed = facts | {HELD: 1, PENDING: 1, TAG + "_Permit": 0}
    assert evaluate(post, armed, journals)
    assert not evaluate(post, armed, journals | {COIN: "Active"})
    assert not evaluate(post, armed | {TAG + "_Issued": 1}, journals)
    assert not evaluate(post, armed | {HELD: 0}, journals)

    write(HERE / "verification.json", {
        "status": "PASS_SERIALIZED_HANDOFF_CONTRACT",
        "resource_sha256": serialized["sha256"], "resource_manifest_sha256": sha(HERE / "serialized_01/manifest.json"),
        "prior_eligible": False, "successor_eligible": True, "rejected_witnesses": rejected,
        "readback_equal": True, "native_nodes": [38, 39, 40, 36], "new_nodes": sorted(NEW),
        "old_nested_graphs_preserved": True, "private_mutations": writers,
        "runtime_owner_and_clock_reload": "UNTESTED",
    })
    print(f"Verified typed graph and {len(rejected)} rejected scenarios")


if __name__ == "__main__":
    main()
