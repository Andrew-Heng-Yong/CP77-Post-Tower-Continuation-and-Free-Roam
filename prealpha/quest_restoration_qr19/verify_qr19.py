"""Check the typed three-resource delta and adversarial admission cases."""
import copy
from collections import Counter
from pathlib import Path

from build import HERE, QR18, ENTRY, PRIVATE, NATIVE, MESSAGES, SCRIPT, DEPOTS, SOCKET, checked, read, sha, source, write
from model import Resource, reachable


def norm(doc):
    model = Resource(doc).normalize()
    assert not model["errors"], model["errors"]
    return model


def evaluate(node, facts, journals):
    t = node["$type"]
    if t == "questLogicalCondition":
        op = node["operation"]
        assert op in {"AND", "OR"}
        values = [evaluate(n, facts, journals) for n in node["conditions"]]
        return all(values) if op == "AND" else any(values)
    if t in ("questFactsDBCondition", "questJournalCondition"):
        return evaluate(node["type"], facts, journals)
    if t == "questVarComparison_ConditionType":
        v = facts.get(node["factName"], 0)
        compare = node["comparisonType"]
        if compare == "Equal":
            return v == node["value"]
        assert compare == "Greater", compare
        return v > node["value"]
    assert t == "questJournalEntryState_ConditionType" and not node["inverted"], t
    return journals.get(node["path"]["realPath"]) == node["state"]


def check_delta(depot, prior, current):
    assert all(prior[k] == current[k] for k in prior if k not in ("graphs", "refs"))
    assert prior["refs"] == current["refs"]
    assert current["graphs"].keys() == prior["graphs"].keys()
    assert all(prior["graphs"][k] == current["graphs"][k] for k in prior["graphs"] if k != "root")
    old, new = prior["graphs"]["root"], current["graphs"]["root"]
    n = new["nodes"]
    assert set(n) == set(old["nodes"]) | {"65008"}
    prior_edges = Counter(map(tuple, old["edges"]))
    current_edges = Counter(map(tuple, new["edges"]))
    extra_input = {"name": SOCKET, "type": "Input"}
    if depot == ENTRY:
        assert prior_edges - current_edges == Counter([("65006", "Out", "37", "In1")])
        assert current_edges - prior_edges == Counter([("65006", "Out", "65008", "In"),
                                                      ("65008", "False", "37", "In1"),
                                                      ("65008", "True", "37", SOCKET)])
        assert n["37"] == old["nodes"]["37"] | {"sockets": old["nodes"]["37"]["sockets"] + [extra_input]}
        for i in ("65003", "65004"):
            old_condition = old["nodes"][i]["payload"]["condition"]
            new_condition = n[i]["payload"]["condition"]
            assert new_condition["operation"] == "OR" and new_condition["conditions"][0] == old_condition
            resume = new_condition["conditions"][1]
            assert resume["operation"] == "AND"
            old_count = len(old_condition["conditions"])
            clone = copy.deepcopy(resume["conditions"][:old_count])
            changed = set()
            for cond in clone:
                value = cond.get("type", {})
                if value.get("factName") in {"mq018_active", "mq018_started"}:
                    assert value["value"] == 1
                    value["value"] = 0
                    changed.add(value["factName"])
            assert changed == {"mq018_active", "mq018_started"} and clone == old_condition["conditions"]
        excepted = {"37", "65003", "65004"}
    elif depot == PRIVATE + NATIVE:
        assert not prior_edges - current_edges
        assert current_edges - prior_edges == Counter([("65008", "Out", "7", SOCKET)])
        assert n["7"] == old["nodes"]["7"] | {"sockets": old["nodes"]["7"]["sockets"] + [extra_input]}
        excepted = {"7"}
    else:
        assert depot == PRIVATE + MESSAGES
        assert not prior_edges - current_edges
        assert current_edges - prior_edges == Counter([("65008", "Out", "67", "In"), ("65008", "Out", "69", "In")])
        available = reachable(n, new["edges"], {"65008"})
        assert {"67", "69", "71", "117", "119", "8", "116"} <= available
        assert available.isdisjoint({"50", "51", "53", "54", "55", "93"}), available
        excepted = set()
    for i, node in old["nodes"].items():
        if i not in excepted:
            assert node == n[i], (depot, i)
    assert not n["65008"]["writes"] and not n["65008"]["reward"]
    return old, new


def admission_tests(prior, current):
    a = prior["nodes"]["65003"]
    b = current["nodes"]["65003"]
    old = a["payload"]["condition"]
    new = b["payload"]["condition"]
    assert new == current["nodes"]["65004"]["payload"]["condition"]
    facts = dict.fromkeys(("PostTowerFreeRoamActive", "PTFRP0_DR13", "PTFRPA2_Finished", "q307_done", "q307_finished",
                           "q307_2079", "q307_main_game_killed", "q307_ep1_killed", "PTFRU9_Support_Issued",
                           "PTFRS29_mq018_writer_Permit", "PTFRS29_PHONE_nancy_Issued",
                           "q001_done", "q003_done", "q005_done", "q101_done", "q110_done"), 1)
    states = {p: "Inactive" for p in a["journal_paths"]}
    assert evaluate(old, facts, states)
    assert evaluate(new, facts, states)
    facts |= {"mq018_started": 1, "mq018_active": 1}
    expected_sms = [f"contacts/bartmoss/bartmoss_spam/msg{i}" for i in ("01", "02", "05", "06", "07")]
    states |= dict.fromkeys(expected_sms, "Active")
    assert not evaluate(old, facts, states) and evaluate(new, facts, states)
    assert evaluate(current["nodes"]["65008"]["payload"]["condition"], facts, states)
    rejected = []
    for name, state in [(s, "Inactive") for s in expected_sms] + [
        ("quests/minor_quest/mq018_writer", "Succeeded"), ("quests/minor_quest/mq018_writer", "Failed"),
        ("quests/minor_quest/mq018_writer/mq018_writer/access_website", "Active"),
        ("quests/minor_quest/mq018_writer/mq018_writer/02b_call_nancy", "Active"),
    ]:
        assert not evaluate(new, facts, states | {name: state}), name
        rejected.append([name, state])
    for name, value in (
        ("q307_main_game_killed", 0), ("PTFRS29_PHONE_nancy_Issued", 0), ("PTFRS29_mq018_writer_Issued", 1),
        ("PTFRS29_mq018_writer_Entered", 1), ("mq018_done", 1), ("mq018_visit_website", 1),
        ("mq018_web_bartmosscollective_visited", 1), ("mq018_active", 2), ("ep1_standalone", 1), ("q110_done", 0),
    ):
        assert not evaluate(new, facts | {name: value}, states), name
        rejected.append([name, value])
    return rejected


def main():
    plan = read(HERE / "proposal_01/plan.json")
    manifest = HERE / "serialized_01/manifest.json"
    serialized = {r["depot"]: r for r in read(manifest)["resources"]}
    assert set(serialized) == set(DEPOTS)
    checked_routes = {}
    for p in plan["resources"]:
        depot = p["depot"]
        row = serialized[depot]
        checked(row["raw"], row["sha256"])
        actual = norm(read(checked(row["readback"], row["readback_sha256"])))
        assert actual == norm(read(checked(p["proposed_json"], p["proposed_json_sha256"])))
        checked_routes[depot] = check_delta(depot, norm(source(depot)), actual)
    rejected = admission_tests(*checked_routes[ENTRY])
    # Corrupt an independently specified edge and prove the typed checker
    # catches a missing existing-message listener.
    msg = PRIVATE + MESSAGES
    original = norm(source(msg))
    mutated = norm(read(serialized[msg]["readback"]))
    mutated["graphs"]["root"]["edges"].remove(["65008", "Out", "69", "In"])
    try:
        check_delta(msg, original, mutated)
    except AssertionError:
        pass
    else:
        raise AssertionError("Missing final read listener escaped verification")
    prior_script = (QR18 / "candidate_01/package" / SCRIPT).read_text(encoding="utf-8")
    script = checked(plan["script"]["source"], plan["script"]["sha256"]).read_text(encoding="utf-8")
    assert script.split("public abstract class SideJobDataS29", 1)[1] == prior_script.split("public abstract class SideJobDataS29", 1)[1]
    assert script.count("SetFactStr(") == prior_script.count("SetFactStr(")
    write(HERE / "verification.json", {
        "status": "PASS_QR19_TYPED_SMS_HANDOFF", "serialized_manifest_sha256": sha(manifest),
        "resource_hashes": {d: r["sha256"] for d, r in serialized.items()},
        "predecessor_partial_eligible": False, "successor_partial_eligible": True,
        "predecessor_fresh_unchanged": True, "negative_witnesses": rejected,
        "missing_listener_control_detected": True, "replay_message_producers_reachable": False,
        "gameplay_validation": "UNTESTED",
    })
    print(f"Typed readback passed for three resources, with {len(rejected)} negative cases")


if __name__ == "__main__":
    main()
