"""Check the offline handoff against its serialized graph and historic saves."""
from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent / "resume_dispatcher_rd6_batch50_20261113_01"
sys.path.insert(0, str(BATCH))
from compare_entrances import EntranceTrace, body_source, readonly
from review_batch import read, sha, write
from model import load_export, normalize, value, walk

CLAIM = "PTFRS29_mq017_streetkid_ResumeClaimed"
RELEASED = "PTFRS29_mq017_streetkid_ResumePhoneReleased"
ISSUED = "PTFRS29_PHONE_kirk_Issued"
PERMIT = "PTFRS29_mq017_streetkid_Permit"
STUDIO = {"PTFRPH3_Entered": 1, "PTFRPH3_Ready": 1}
EXPECTED_EDGES = [
    (61000, "Out", 61010, "In"), (61010, "True", 61015, "In"),
    (61010, "False", 61020, "In"), (61011, "True", 61012, "In"),
    (61011, "False", 61014, "In"), (61012, "Out", 61013, "In"),
    (61013, "Out", 24, "ResumeMeetKirk"), (61014, "Out", 24, "ResumeMeetKirk"),
    (61015, "Out", 61016, "In28"), (61016, "Out28", 61017, "In"),
    (61017, "Out", 61018, "In"), (61018, "Out", 61019, "In"),
    (61019, "Out", 61011, "In"),
]
OLD_CALL = {
    "holo_kirk_calls_v_start_count": 2, "holo_kirk_calls_v_end_count": 1,
    "holo_kirk_calls_v_interrupted": 1, "holo_v_calls_kirk_start_count": 0,
    "holo_v_calls_kirk_end_count": 0, "holo_kirk_calls_v_rejected_branch": 0,
}
ENDED_CALL = {name: OLD_CALL[name] for name in OLD_CALL if name.endswith("_count")} | {"holo_kirk_calls_v_end_count": 2}


def scopes(model):
    return {row["path"]: row for row in model["graphs"]}


def nodes(scope):
    return {row["id"]: row for row in scope["nodes"]}


def type_facts(leaves):
    return {row["type"]["factName"]: row["type"]["value"] for row in leaves
            if row["$type"] == "questFactsDBCondition" and "factName" in row["type"]
            and row["type"]["comparisonType"] == "Equal"}


def condition(node):
    return node["parameters"]["condition"]


def check_counters(leaves):
    pairs = {row["type"]["factName1"]: row["type"]["factName2"] for row in leaves
             if row["$type"] == "questFactsDBCondition"
             and row["type"]["$type"] == "questVarVsVarComparison_ConditionType"
             and row["type"]["comparisonType"] == "Equal"}
    assert pairs == {"holo_kirk_calls_v_start_count": "holo_kirk_calls_v_end_count",
                     "holo_v_calls_kirk_start_count": "holo_v_calls_kirk_end_count"}


def verify_root(old, new, phone, cleanup):
    old_graphs, new_graphs = scopes(old), scopes(new)
    assert old["support"] == new["support"] and old_graphs.keys() == new_graphs.keys()
    assert all(old_graphs[key] == new_graphs[key] for key in old_graphs if key != "root")
    before, after = old_graphs["root"], new_graphs["root"]
    assert not after["unresolved_connections"]
    assert before["inputs"] == after["inputs"]
    old_nodes, current = nodes(before), nodes(after)
    assert all(current[i] == n for i, n in old_nodes.items())
    assert set(current) - set(old_nodes) == set(range(61010, 61021))
    expected = Counter(before["edges"])
    removed = (61000, "Out", "Output", 24, "ResumeMeetKirk", "Input")
    assert expected.pop(removed) == 1
    expected.update((a, out, "Output", b, inp, "Input") for a, out, b, inp in EXPECTED_EDGES)
    assert expected == Counter(after["edges"])

    clones = {61010: old_nodes[9], 61011: old_nodes[31], 61012: old_nodes[28],
              61013: old_nodes[23], 61014: old_nodes[33], 61016: cleanup[1201]}
    for i, prior in clones.items():
        assert current[i] == prior | {"id": i, "parameters": prior["parameters"] | {"id": i}, "from_any_input": True}, i
    assert value(current[61020]["parameters"]["socketName"]) == "ResumeRejected"
    assert value(current[1]["parameters"]["socketName"]) == "Out1"
    native = condition(phone[1002])
    wanted = type_facts(native["conditions"]) | {PERMIT: 0, CLAIM: 1, RELEASED: 0} | STUDIO
    pre = condition(current[61015])
    post = condition(current[61017])
    for tree in (pre, post):
        assert tree["operation"] == "AND"
    assert type_facts(pre["conditions"]) == wanted | OLD_CALL
    assert type_facts(post["conditions"]) == wanted | ENDED_CALL
    receipt = current[61018]["parameters"]["type"]
    assert (receipt["factName"], receipt["value"], receipt["setExactValue"]) == (RELEASED, 1, 1)
    assert type_facts(condition(current[61019])["conditions"]) == {CLAIM: 1, RELEASED: 1, ISSUED: 1}
    return pre, post


def verify_listener(old, new):
    old_graphs, new_graphs = scopes(old), scopes(new)
    assert old["support"] == new["support"] and old_graphs.keys() == new_graphs.keys()
    for path, scope in old_graphs.items():
        current = new_graphs[path]
        assert scope | {"nodes": current["nodes"]} == current
        before, after = nodes(scope), nodes(current)
        assert before.keys() == after.keys()
        for i, node in before.items():
            updated = after[i]
            if path != "root" or i not in (1002, 1003):
                assert updated == node
                continue
            prior, new_tree = condition(node), condition(updated)
            assert updated == node | {"parameters": node["parameters"] | {"condition": new_tree}}
            assert prior["operation"] == new_tree["operation"] == "AND"
            original_permit, = [row for row in prior["conditions"] if row["type"]["factName"] == PERMIT]
            assert new_tree["conditions"][:-1] == [row for row in prior["conditions"] if row != original_permit]
            branch = new_tree["conditions"][-1]
            assert branch["operation"] == "OR"
            fresh, resume = branch["conditions"]
            assert fresh == original_permit
            assert resume["operation"] == "AND"
            assert type_facts(resume["conditions"]) == {CLAIM: 1, RELEASED: 1, PERMIT: 0} | STUDIO
            check_counters(resume["conditions"])
    return condition(nodes(new_graphs["root"])[1003])


def evaluates(tree, facts):
    if tree["$type"] == "questLogicalCondition":
        outcomes = (evaluates(row, facts) for row in tree["conditions"])
        return all(outcomes) if tree["operation"] == "AND" else any(outcomes)
    test = tree["type"]
    assert test["comparisonType"] == "Equal"
    if "factName" in test:
        return test["factName"] in facts and facts[test["factName"]] == test["value"]
    return all(test[k] in facts for k in ("factName1", "factName2")) and facts[test["factName1"]] == facts[test["factName2"]]


def check_fixture(pre, post, listener):
    fixtures = HERE.parent / "history_capture_hs3_20261112_01/fixtures_saves_01"
    saved = read(fixtures / "ManualSave-27.json")
    assert sha(fixtures / "ManualSave-27.json") == "92290F8515EC5B3BC69EAE0F90F77881EE87FBA67D268D0FB4049E50E21B507A"
    assert all((saved["facts"][name] or 0) == expected for name, expected in OLD_CALL.items())
    for name in ("holo_setup_active", "holo_setup_started", "holo_interrupt_call", "holo_force_reset", "holo_reset"):
        assert saved["facts"][name] == 0
    # The archived save predates this adapter. Supply future owner/support
    # receipts only in this synthetic control, with the observed call facts.
    staged = type_facts(pre["conditions"])
    staged.update({name: saved["facts"][name] or 0 for name in OLD_CALL})
    assert evaluates(pre, staged) and not evaluates(post, staged) and not evaluates(listener, staged)
    checks = 0
    for name, v in staged.items():
        changed = staged | {name: v + 1}
        assert not evaluates(pre, changed), name
        missing = staged.copy()
        del missing[name]
        assert not evaluates(pre, missing), name
        checks += 2
    ended = staged | {"holo_kirk_calls_v_end_count": 2}
    assert evaluates(post, ended) and not evaluates(pre, ended)
    assert not evaluates(post, ended | {"holo_kirk_calls_v_start_count": 3, "holo_kirk_calls_v_end_count": 3})
    checks += 1
    ready = ended | {RELEASED: 1}
    assert evaluates(listener, ready) and not evaluates(pre, ready)
    for changes in ({CLAIM: 0}, {RELEASED: 0}, {ISSUED: 1}, {"PTFRPH3_Ready": 0},
                    {"holo_kirk_calls_v_end_count": 1}, {"holo_interrupt_call": 1}):
        assert not evaluates(listener, ready | changes)
        checks += 1
    assert evaluates(listener, staged | {PERMIT: 1, CLAIM: 0, RELEASED: 0})
    return checks


def check_native_owners(old, parts):
    cleanup = scopes(old[15154])["root"]
    gate = condition(nodes(cleanup)[1240])
    assert type_facts(gate["conditions"]) == {ISSUED: 1}
    assert (1240, "True", "Output", 1200, "In", "Input") in cleanup["edges"]
    assert (1200, "True", "Output", 1201, "In28", "Input") in cleanup["edges"]
    native = scopes(old[10730])["root"]
    assert (6, "Out", "Output", 0, "holo_kirk_calls_v_end", "Input") in native["edges"]
    scene = nodes(scopes(old[8977])["scene"])
    writer = scene[485]["parameters"]["questNode"]["type"]
    assert (writer["factName"], writer["setExactValue"], writer["value"]) == ("holo_kirk_calls_v_end_count", 0, 1)
    studio = scopes(old[15527])
    studio_root = nodes(studio["root"])[3]["parameters"]
    assert "$/03_night_city/ne2/#holocalls_studio" in {value(x["prefabNodeRef"]) for x in studio_root["phaseInstancePrefabs"]}
    for node, name in ((1, "PTFRPH3_Entered"), (2, "PTFRPH3_Ready")):
        assert nodes(studio["root/3"])[node]["parameters"]["type"]["factName"] == name
    hook = scopes(normalize(load_export(parts["hook"]["export"])))
    bar = nodes(hook["root/61002"])
    activate = [row for row in walk(bar[3]["parameters"]) if row["$type"] == "questSpawnSet_NodeType"]
    actors = [(value(row["reference"]), value(row["phaseName"]), row["action"]) for row in activate]
    assert actors == [("#fixer_kirk", "mq017_01_bar", "Activate"), ("#mq017_big_joe", "mq017_big_joe_bar", "Activate")]
    spawn_wait = condition(bar[4])["type"]
    assert spawn_wait["$type"] == "questCharacterSpawned_ConditionType"
    assert value(spawn_wait["objectRef"]["reference"]) == "#fixer_kirk"
    assert (3, "Out", "Output", 4, "In", "Input") in hook["root/61002"]["edges"]
    return actors


def main():
    evidence, folder = HERE / "evidence_04", HERE / "graph_05"
    assert not evidence.exists()
    pin_file = HERE / "evidence_02/provider_watch.json"
    pins = read(pin_file)
    readback_file = folder / "readback.json"
    receipt = read(readback_file)
    provider = {row["rid"]: row for row in pins["resources"]}
    assert receipt["provider_count"] == len(provider)
    assert receipt["source_sha256"] == pins["parts"]["root"]["raw_sha256"]
    old = {}
    for rid, row in provider.items():
        assert sha(row["export_path"]) == row["export_sha256"]
        old[rid] = normalize(load_export(row["export_path"]))
    actors = check_native_owners(old, pins["parts"])
    entries = {part["depot"]: part for part in pins["parts"].values()}
    entries[receipt["depot"]] = body_source(folder, "root.questphase", receipt["raw_sha256"], receipt["export_sha256"])
    phone_source = body_source(folder, "kirk.questphase", receipt["phone"]["raw_sha256"], receipt["phone"]["export_sha256"])
    prior = pins["parts"]["root"]
    assert sha(prior["export"]) == prior["export_sha256"]
    before = normalize(load_export(prior["export"]))
    after = normalize(load_export(entries[receipt["depot"]]["export"]))
    pre, post = verify_root(before, after, nodes(scopes(old[14599])["root"]), nodes(scopes(old[15154])["root"]))
    listener = verify_listener(old[14599], normalize(load_export(phone_source["export"])))
    checks = check_fixture(pre, post, listener)
    with readonly("registry") as db:
        tracer = EntranceTrace(db, entries)
        _, reached, _, boundaries = tracer.entrance(receipt["depot"], "ResumeMeetKirk")
        assert not boundaries
        footprint = tracer.footprint(reached)
        assert footprint["reward_targets"] == ["QuestRewards.mq017_done"]
        assert "mq017_started" not in footprint["fact_writes"]
        assert "holo_kirk_calls_v_start_count" not in footprint["fact_writes"]
        assert "holo_kirk_calls_v_end_count" in footprint["fact_writes"]
        assert ISSUED not in footprint["fact_writes"]
        assert {10730, 8977}.issubset({r for r, _, _ in reached})
    evidence.mkdir()
    write(evidence / "assessment.json", {
        "status": "PASS_UNREGISTERED_KIRK_HANDOFF", "provider_watch_sha256": sha(pin_file),
        "readback_sha256": sha(readback_file), "provider_count": len(provider),
        "archive_count": receipt["archive_count"], "negative_controls": checks,
        "reached_nodes": len(reached), "bar_spawn_actions": actors,
        "live_actor_ownership_qualified": False, "runtime_admitted": False,
    })
    print(f"Verified native cleanup, unchanged fresh listener branch, {checks} negative controls and {len(reached)} structurally reachable nodes.")


if __name__ == "__main__":
    main()
