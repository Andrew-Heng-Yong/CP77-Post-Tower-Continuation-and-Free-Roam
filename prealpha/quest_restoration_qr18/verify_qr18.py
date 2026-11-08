"""Independently compare the staged graph with native donors and QR17."""
from collections import Counter
from pathlib import Path
import re

from build import HERE, QR17, QR13, SCRIPT, PENDING, HELD, TAG, COIN, DUMPSTER, SPRAY, checked, read, sha, write
from verify import graph, evaluate

ADD = {str(i) for i in range(1140, 1151)}
REMOVED = [
    ("1120", "False", "1008", "In"), ("1122", "False", "1101", "In"),
]
ROUTE = [
    ("1120", "False", "1140", "In"), ("1140", "False", "1008", "In"), ("1140", "True", "1141", "In"),
    ("1141", "Out", "1110", "In1"), ("1122", "False", "1142", "In"), ("1142", "False", "1101", "In"),
    ("1142", "True", "1143", "In"), ("1142", "True", "1144", "In"), ("1144", "Out", "1145", "In"),
    ("1145", "Out", "1146", "In"), ("1146", "False", "1131", "In"), ("1146", "True", "1147", "In"),
    ("1147", "Out", "1148", "In"), ("1148", "Out", "1149", "In"), ("1149", "Out", "1150", "In"),
    ("1150", "Out", "34", "Girlfriend"),
]


def conds(payload):
    return payload["condition"]


def static_delta(old, actual):
    assert all(old[key] == actual[key] for key in old if key != "graphs")
    assert old["graphs"].keys() == actual["graphs"].keys()
    assert all(old["graphs"][k] == actual["graphs"][k] for k in old["graphs"] if k != "root")
    prior = old["graphs"]["root"]
    root = actual["graphs"]["root"]
    assert root["entries"] == prior["entries"]
    nodes = root["nodes"]
    assert set(nodes) == set(prior["nodes"]) | ADD
    for node_id, old_node in prior["nodes"].items():
        if node_id not in {"1002", "1004"}:
            assert nodes[node_id] == old_node, node_id
            continue
        old_payload, new_payload = (n["payload"] for n in (old_node, nodes[node_id]))
        current = conds(new_payload)
        assert {k: v for k, v in new_payload.items() if k != "condition"} == {
            k: v for k, v in old_payload.items() if k != "condition"}
        assert nodes[node_id]["sockets"] == old_node["sockets"]
        assert current["operation"] == "OR"
        assert current["conditions"] == conds(old_payload)["conditions"] + [conds(nodes["1140"]["payload"])]
    past = Counter(map(tuple, prior["edges"]))
    changed = Counter(map(tuple, root["edges"]))
    assert past - changed == Counter(REMOVED) and changed - past == Counter(ROUTE)
    return nodes


def source_donors(nodes):
    row, = (r for r in read(QR13 / "brendan_provider_validation_01/manifest.json")["resources"]
            if r["depot"].endswith("mq037_brendan.questphase"))
    g = graph(read(checked(row["json"], row["json_sha256"])))["graphs"]
    for dest, source in zip(("1143", "1144", "1145", "1148"), ("54", "24", "25", "26"), strict=True):
        n = g["root/19"]["nodes"][source]
        assert n["payload"] | {"id": int(dest)} == nodes[dest]["payload"]
        assert n["sockets"] == nodes[dest]["sockets"]
    assert g["root"]["entries"]["Girlfriend"] == "49"
    for e in (["19", "Out1", "23", "In1"], ["49", "Out", "50", "In1"], ["50", "Out1", "23", "In1"],
              ["23", "Out1", "25", "In1"], ["25", "Out1", "28", "In1"]):
        assert e in g["root"]["edges"]
    for e in (["23", "Out", "24", "In"], ["23", "Out", "54", "In"], ["24", "Out", "25", "In"],
              ["25", "Out", "26", "In"], ["26", "Out", "1", "In"]):
        assert e in g["root/19"]["edges"]
    assert ["3", "girl_dial_out", "51", "In"] in g["root/23/5"]["edges"]
    assert g["root/23/5"]["nodes"]["51"]["writes"][0]["factName"] == "mq037_post_girl_scene_on"
    prelude = g["root/50"]["nodes"]
    assert prelude["2"]["writes"] == [
        {"$type": "questSetVar_NodeType", "factName": "mq037_brendan_introduced", "setExactValue": 1, "value": 1}]
    assert prelude["3"]["payload"]["actions"][0]["type"]["action"] == "Activate"
    assert prelude["5"]["payload"]["type"]["enable"] == 0


def check_witnesses(old, nodes):
    # The model states below describe native player histories directly.
    coin = COIN + "/mq037_brendan"
    spray = SPRAY + "/mq037_brendan_hooligan"
    journals = dict.fromkeys((COIN, coin, SPRAY, spray), "Inactive")
    journals |= {f"{coin}/{s}": "Inactive" for s in (
        "01_go_to_service", "01_go_to_service/description", "02_find_brendan", "02b_ask_clerk",
        "02c_destroy_turret", "03_talk_brendan", "04_talk_theo")}
    journals |= {f"{spray}/{s}": "Inactive" for s in ("00_deal_with_the_hooligan", "01_talk_with_brendan")}
    journals |= dict.fromkeys((DUMPSTER, DUMPSTER + "/mq037_brendan_dumpster/00_push_dumpster",
                               DUMPSTER + "/mq037_brendan_dumpster/01_talk_brendan"), "Succeeded")
    facts = dict.fromkeys(("PostTowerFreeRoamActive", "PTFRP0_DR13", "PTFRPA2_Finished", "q307_done",
                           "q307_finished", "q307_2079", "q307_main_game_killed", "q307_ep1_killed",
                           "PTFRU9_Support_Issued", "mq037_brendan_introduced", TAG + "_Permit"), 1)
    for gate in ("1002", "1004"):
        prior = old["graphs"]["root"]["nodes"][gate]
        assert not evaluate(conds(prior["payload"]), facts, journals)
        assert evaluate(conds(nodes[gate]["payload"]), facts, journals)
    early = conds(nodes["1140"]["payload"])
    post = conds(nodes["1146"]["payload"])
    assert evaluate(early, facts, journals)
    rejected = []
    for key, state in ((DUMPSTER, "Inactive"), (SPRAY, "Active"), (SPRAY, "Failed"), (COIN, "Active"),
                       (COIN, "Succeeded"), (spray + "/00_deal_with_the_hooligan", "Active"), (COIN, None)):
        assert not evaluate(early, facts, journals | {key: state}), key
        rejected.append([key, state])
    for key, val in (("mq037_post_girl_scene_on", 1), ("mq037_vandal_painted_brendan", 1), ("mq037_01_05Sure", 1),
                     ("mq037_brendan_introduced", 0), ("q307_main_game_killed", 0), (TAG + "_Issued", 1),
                     (TAG + "_Entered", 1), (TAG + "_Finished", 1), (PENDING, 1), (HELD, 1)):
        assert not evaluate(early, facts | {key: val}, journals), key
        rejected.append([key, val])
    waited = facts | {HELD: 1, PENDING: 2, TAG + "_Permit": 0}
    assert evaluate(post, waited, journals)
    assert not evaluate(post, waited | {PENDING: 1}, journals)
    assert not evaluate(post, waited | {"mq037_post_girl_scene_on": 1}, journals)
    assert not evaluate(post, waited, journals | {SPRAY: "Active"})
    six_hour = conds(nodes["1122"]["payload"])
    eight_hour = conds(nodes["1142"]["payload"])
    assert (evaluate(six_hour, {PENDING: 1}, {}), evaluate(eight_hour, {PENDING: 1}, {})) == (True, False)
    assert (evaluate(six_hour, {PENDING: 2}, {}), evaluate(eight_hour, {PENDING: 2}, {})) == (False, True)
    assert (evaluate(six_hour, {}, {}), evaluate(eight_hour, {}, {})) == (False, False)
    return rejected


def verify_script(script, graph_conditions):
    text = Path(script["source"]).read_text(encoding="utf-8")
    old = (QR17 / "candidate_01/package" / SCRIPT).read_text(encoding="utf-8")
    start = text.index("  private func ReadBrendanAfterDumpster(")
    end = text.index("  private func Same(", start)
    method = text[start:end]
    restored = (text[:start] + text[end:]).replace(
        '(this.ReadBrendanHandoff(paths, sample.states, names, sample.facts) ||\n'
        '        this.ReadBrendanAfterDumpster(paths, sample.states, names, sample.facts))',
        'this.ReadBrendanHandoff(paths, sample.states, names, sample.facts)').replace(
        'Earned Brendan continuation matches a native handoff from its starting wait.',
        'Earned Spray Paint complete. Starting the native Coin Operated Boy handoff from its six-hour wait.')
    assert restored == old
    states = {"Inactive": "1", "Succeeded": "3"}
    expected_states = set()
    expected_facts = set()
    for p in graph_conditions["conditions"]:
        payload = p["type"]
        if payload["$type"] == "questJournalEntryState_ConditionType":
            expected_states.add((payload["path"]["realPath"], states[payload["state"]]))
        elif payload["factName"].startswith("mq037_"):
            expected_facts.add((payload["factName"], str(payload["value"])))
    assert set(re.findall(r'State\(paths, states, "([^"]+)"\) == (\d+)', method)) == expected_states
    assert set(re.findall(r'Fact\(names, facts, "([^"]+)"\) == (\d+)', method)) == expected_facts


def main():
    prior = read(QR17 / "serialized_01/manifest.json")
    old = graph(read(checked(prior["readback"], prior["readback_sha256"])))
    serialized = read(HERE / "serialized_01/manifest.json")
    checked(serialized["raw"], serialized["sha256"])
    actual = graph(read(checked(serialized["readback"], serialized["readback_sha256"])))
    plan = read(HERE / "proposal_01/plan.json")
    proposed, = plan["resources"]
    assert actual == graph(read(checked(proposed["proposed_json"], proposed["proposed_json_sha256"])))
    nodes = static_delta(old, actual)
    source_donors(nodes)
    rejected = check_witnesses(old, nodes)
    verify_script(plan["script"], conds(nodes["1140"]["payload"]))
    assert not any(nodes[n]["reward"] for n in ADD)
    writers = {n: (nodes[n]["writes"][0]["factName"], nodes[n]["writes"][0]["value"]) for n in ADD if nodes[n]["writes"]}
    assert writers == {"1141": (PENDING, 2), "1147": (TAG + "_Issued", 1),
                       "1149": (TAG + "_Entered", 1), "1150": (PENDING, 0)}
    write(HERE / "verification.json", {
        "status": "PASS_SERIALIZED_HANDOFF_CONTRACT", "resource_sha256": serialized["sha256"],
        "resource_manifest_sha256": sha(HERE / "serialized_01/manifest.json"), "native_nodes": [54, 24, 25, 26],
        "prior_eligible": False, "successor_eligible": True, "rejected_witnesses": rejected,
        "script_and_graph_agree": True, "predecessor_nested_graphs_preserved": True,
        "private_mutations": writers, "gameplay_and_save_reload": "UNTESTED",
    })
    print(f"Verified typed graph and script, rejected {len(rejected)} ineligible histories")


if __name__ == "__main__":
    main()
