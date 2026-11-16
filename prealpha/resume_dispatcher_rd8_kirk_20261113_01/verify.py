"""Verify native admission, exact changes and the full private completion path."""
from collections import Counter
from pathlib import Path
from prepare import HERE, RD7, ROOT, PHASE, OBJECTIVE, read, readonly, sha, write
from compare_entrances import EntranceTrace
from model import load_export, normalize, value, walk


def load(path):
    return normalize(load_export(path))


def graph(model, path="root"):
    scope = next(g for g in model["graphs"] if g["path"] == path)
    assert not scope["unresolved_connections"]
    return {n["id"]: n for n in scope["nodes"]}, Counter(scope["edges"])


def edge(a, out, b, inp):
    return a, out, "Output", b, inp, "Input"


def signature(tree):
    entries = {}
    for leaf in tree["conditions"]:
        part = leaf["type"]
        if leaf["$type"] == "questJournalCondition":
            key = part["path"]["realPath"]
            token = part["state"]
            assert not part["inverted"]
        else:
            assert leaf["$type"] == "questFactsDBCondition" and part["comparisonType"] == "Equal"
            key, token = part["factName"], part["value"]
        assert key not in entries, key
        entries[key] = token
    return entries


def verify_wrapper(pins, output):
    original = load(pins["wrapper"]["export_path"])
    updated = load(output)
    assert updated["support"] == original["support"]
    before, old_edges = graph(original)
    after, new_edges = graph(updated)
    for i in before:
        if i not in (65003, 65004):
            assert before[i] == after[i]
    tree = after[65003]["parameters"]["condition"]
    assert tree["operation"] == "OR"
    fresh, resume = tree["conditions"]
    assert fresh == after[65004]["parameters"]["condition"]
    assert fresh["conditions"][:-1] == before[65003]["parameters"]["condition"]["conditions"]
    original_predicate = signature(before[65003]["parameters"]["condition"])
    tag = pins["tag"]
    assert signature(fresh) == original_predicate | {tag + "ResumeClaimed": 0}
    expected = {k: v for k, v in original_predicate.items() if isinstance(v, int) and not k.startswith("mq017_")}
    expected |= pins["facts"] | {
        "PTFRS29_PHONE_kirk_Issued": 0, tag + "Permit": 0, tag + "ResumeClaimed": 0, tag + "ResumePhoneReleased": 0,
        "PTFRPH3_Entered": 1, "PTFRPH3_Ready": 1, tag + "ResumePermit": 1,
    }
    expected |= {row["path"]: ("Failed" if row["live"] == 4 else "Active" if row["live"] == 2 else "Inactive")
                 for row in pins["journals"]}
    assert signature(resume) == expected
    assert after[61000]["parameters"]["condition"] == resume
    expected_edges = old_edges - Counter([edge(65003, "Out", 65004, "In")])
    expected_edges.update([
        edge(65003, "Out", 61000, "In"), edge(61000, "False", 65004, "In"), edge(61000, "True", 61001, "In"),
        edge(61001, "Out", 61002, "ResumeMeetKirk"), edge(61002, "Out1", 65007, "In"),
        edge(61002, "ResumeRejected", 61003, "In"),
    ])
    assert new_edges == expected_edges
    assert graph(original, "root/22") == graph(updated, "root/22")
    assert value(after[61002]["parameters"]["phaseResource"]["DepotPath"]) == pins["parts"]["root"]["depot"]
    assert {value(node["parameters"]["socketName"]) for node in graph(updated, "root/61002")[0].values()} == {
        "ResumeMeetKirk", "Out1", "ResumeRejected"}
    assert after[61001]["parameters"]["type"]["factName"] == tag + "ResumeClaimed"
    assert after[61003]["parameters"]["type"]["factName"] == tag + "Fault"
    return expected


def verify_hook(pins, output):
    original = load(pins["parts"]["hook"]["raw"] + ".json")
    updated = load(output)
    assert updated["support"] == original["support"]
    assert graph(original, "root/6") == graph(updated, "root/6")
    nodes, edges = graph(updated, "root/61002")
    for actor, condition, action, wait, token in (
        ("#fixer_kirk", 12, 3, 4, "mq017_01_bar"),
        ("#mq017_big_joe", 13, 10, 11, "mq017_big_joe_bar"),
    ):
        assert edge(condition, "False", action, "In") in edges and edge(action, "Out", wait, "In") in edges
        for i in (condition, wait):
            assert value(nodes[i]["parameters"]["condition"]["type"]["objectRef"]["reference"]) == actor
        actions = [row for row in walk(nodes[action]["parameters"]) if row["$type"] == "questSpawnSet_NodeType"]
        assert [(value(a["reference"]), a["action"], value(a["phaseName"])) for a in actions] == [(actor, "Activate", token)]
    assert edge(12, "True", 13, "In") in edges and edge(13, "True", 6, "In") in edges
    root, edges = graph(updated)
    assert [root[i]["parameters"]["type"]["path"]["realPath"] for i in (61010, 61011, 61001)] == [ROOT, PHASE, OBJECTIVE]
    assert signature(root[61012]["parameters"]["condition"]) == dict.fromkeys((ROOT, PHASE, OBJECTIVE), "Active")
    assert all(edge(a, out, b, inp) in edges for a, out, b, inp in [
        (61000,"Out",61010,"Active"),(61010,"Out",61011,"Active"),(61011,"Out",61001,"Active"),
        (61001,"Out",61012,"In"),(61012,"Out",61013,"In"),(61013,"Out",61014,"In"),(61014,"Out",61002,"In1"),
    ])


def fixture(expected, pins):
    prior = HERE.parent / "history_capture_hs3_20261112_01/fixtures_saves_01/ManualSave-27.json"
    assert sha(prior) == "92290F8515EC5B3BC69EAE0F90F77881EE87FBA67D268D0FB4049E50E21B507A"
    saved = read(prior)
    for name, want in pins["facts"].items():
        assert (saved["facts"][name] or 0) == want, name
    by_path = {row["paths"][0]: row["uint32_at_4"] for row in saved["journal_matches"] if len(row["paths"]) == 1}
    assert all(by_path.get(j["path"], 1) == j["live"] for j in pins["journals"])
    guard = lambda facts: all(facts.get(key) == value for key, value in expected.items())
    assert guard(expected)
    for k, value in expected.items():
        assert not guard({**expected, k: str(value) + "_changed"})
        assert not guard({key: v for key, v in expected.items() if key != k})
    return len(expected) * 2


def main():
    e = HERE / "evidence_01"
    pins = read(e / "inputs.json")
    graph_path = HERE / "graph_02/readback.json"
    readback = read(graph_path)
    assert readback["input_sha256"] == sha(e / "inputs.json")
    outputs = {r["name"]: r for r in readback["resources"]}
    for row in outputs.values():
        assert sha(row["path"]) == row["sha256"] and sha(row["path"] + ".json") == row["export_sha256"]
    expected = verify_wrapper(pins, outputs["wrapper"]["path"] + ".json")
    verify_hook(pins, outputs["hook"]["path"] + ".json")
    controls = fixture(expected, pins)
    resources = {r["depot"]: {"export": r["raw"] + ".json"} for r in pins["parts"].values()}
    resources[outputs["hook"]["depot"]]["export"] = outputs["hook"]["path"] + ".json"
    with readonly("registry") as db:
        tracer = EntranceTrace(db, resources)
        _, reached, _, boundaries = tracer.entrance(pins["parts"]["root"]["depot"], "ResumeMeetKirk")
        assert not boundaries
        footprint = tracer.footprint(reached)
        assert footprint["reward_targets"] == ["QuestRewards.mq017_done"]
        assert "mq017_started" not in footprint["fact_writes"]
    write(e / "assessment_02.json", {
        "status": "PASS", "graph_sha256": sha(graph_path),
        "fixture_negative_controls": controls, "reached_nodes": len(reached), "gameplay": "PENDING",
    })
    print(f"Verified {controls} mutated and missing inputs, the native caller and the full completion path.")


if __name__ == "__main__":
    main()
