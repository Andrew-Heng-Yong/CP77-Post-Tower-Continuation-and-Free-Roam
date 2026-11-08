"""Read-only MQ037 timed handoff and native repair-input check."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
QR13 = HERE.parent / "quest_restoration_qr13"
QR15 = HERE.parent / "quest_restoration_qr15"
sys.path[:0] = [str(WORK / "tools/parity_audit"), str(QR15 / "event_stage_01"), str(QR15 / "latest_save_01")]
from analyze_components import decode_paths, phase_hash
from analyze_native_layout import native_records
from compare import CURRENT_BODY, fact_key, pin, pin_save, read
from model import Resource

STATUS = "MQ037_EARLY_REPAIR_INPUTS_CLASSIFIED_CONTINUATION_HELD"
BODY = r"base\quest\minor_quests\mq037\mq037_brendan.questphase"
BUGFIX = r"base\quest\bugfixing\minor_quests\mq037\mq037_quest_bugfixes.questphase"
PRIVATE = r"towercontinued\sidejobs_s23\base_b\mq037.questphase"
BASE = r"base\quest\cyberpunk2077.quest"
MAIN = BASE + "phase"
MINOR = r"base\quest\minor_quests\minorquests.questphase"
FIX_ROOT = r"base\quest\bugfixing.questphase"
FIX_QUEST = r"base\quest\bugfixing\quest_bugfixing.questphase"
SCENE = r"base\quest\minor_quests\mq037\scenes\mq037_01_brendan_scenes.scene"

TIMERS = [
    ("early introduction route", "root/10", "11", 6),
    ("alternate Dumpster route", "root/15", "20", 12),
    ("Dumpster follow-up", "root/19", "24", 8),
    ("Theo handoff into Spray Paint", "root/23", "15", 12),
    ("Theo interaction cleanup", "root/23/5", "26", 1),
    ("Spray Paint completion into Coin Operated Boy", "root/25", "38", 6),
    ("Spray Paint retry branch", "root/25/18", "2", 6),
]


def checked_route(graphs, graph, *edges):
    actual = graphs[graph]["edges"]
    for edge in edges:
        assert actual.count(list(edge)) == 1, (graph, edge)
    return {"graph": graph, "edges": edges}


def seam_checks(body, bug, scene):
    route = checked_route
    clock_reentry = [
        route(bug, "root/14", ("21", "False", "13", "CYB-640323")),
        route(body, "root", ("61", "Out", "23", "CYB-640323")),
        route(body, "root/23", ("25", "Out", "5", "CYB-640323")),
        route(body, "root/23/5", ("47", "Out", "54", "In"), ("54", "False", "17", "In"),
              ("54", "False", "26", "In"), ("54", "False", "44", "In")),
    ]
    theo_cut = [
        route(bug, "root/38", ("12", "Out1", "7", "CYB-661474_girl")),
        route(body, "root", ("62", "Out", "23", "CYB-661474_girl"),
              ("23", "CYB-661474_girl_out", "66", "In"), ("66", "CutSource", "23", "CutDestination")),
        route(body, "root/23", ("27", "Out", "5", "CYB-661474_girl"), ("5", "Out3", "28", "In")),
        route(body, "root/23/5", ("55", "Out", "16", "CYB-661474_kill_signal_in"),
              ("16", "CYB-661474_kill_signal__out", "56", "In"), ("56", "CutSource", "16", "CutDestination"),
              ("56", "Out", "57", "In")),
        route(scene, "scene", ("1716", "0:0", "1717", "0:0")),
    ]
    hooligan_cut = [
        route(bug, "root/38", ("10", "Out", "8", "CYB-661474_hooligan")),
        route(body, "root", ("63", "Out", "25", "CYB-661474_hooligan_in"),
              ("25", "CYB-661474_hooligan_out", "67", "In"), ("67", "CutSource", "25", "CutDestination")),
        route(body, "root/25", ("128", "Out", "62", "CYB-661474_hooligan_in"),
              ("62", "CYB-661474_hooligan_out", "131", "In"), ("131", "CutSource", "105", "CutDestination"),
              ("131", "CutSource", "13", "CutDestination"), ("131", "CutSource", "78", "CutDestination"),
              ("131", "Out", "132", "In")),
        route(body, "root/25/62", ("18", "Out", "19", "In"), ("19", "CutSource", "2", "CutDestination"),
              ("19", "CutSource", "8", "CutDestination"), ("19", "Out", "20", "In")),
    ]
    for graph, node in (("root/25", "132"), ("root/25/62", "20")):
        assert body[graph]["nodes"][node]["payload"]["type"] == "Terminating"
    assert scene["scene"]["entries"]["CYB-661474_kill_signal_in"] == "1716"
    assert scene["scene"]["nodes"]["1717"]["payload"]["type"] == "Terminating"
    assert not any(e[0] == "1717" for e in scene["scene"]["edges"])
    return {"CYB-640323": clock_reentry, "CYB-661474_girl": theo_cut, "CYB-661474_hooligan": hooligan_cut}


def source_analysis(load_provider, private):
    body, bug, scene = (load_provider(x) for x in (BODY, BUGFIX, SCENE))
    routes = seam_checks(body, bug, scene)
    clocks = []
    for label, path, node_id, hours in TIMERS:
        graph = body[path]
        node = graph["nodes"][node_id]
        payload = node["payload"]["condition"]["type"]
        assert node["type"] == "questPauseConditionNodeDefinition"
        assert payload == {"$type": "questGameTimeDelay_ConditionType", "days": 0, "hours": hours, "minutes": 0, "seconds": 0}
        clocks.append({"label": label, "graph": path, "node": node_id, "payload": payload,
                       "edges": [edge for edge in graph["edges"] if node_id in (edge[0], edge[2])]})
    post_spray = checked_route(body, "root/25", ("51", "Out", "52", "Succeeded"), ("52", "Out", "37", "In"),
                              ("37", "Out", "38", "In"), ("38", "Out", "39", "In"), ("39", "Out", "40", "In"),
                              ("40", "Out", "36", "Inactive"), ("36", "Out", "1", "In"))
    assert body["root/25"]["nodes"]["52"]["journal_paths"] == ["quests/minor_quest/mq037_brendan_hooligan001"]
    checked_route(body, "root", ("25", "Out1", "28", "In1"))
    # POI inactivity also has an incoming route independent of the clock.
    alternate_poi = checked_route(body, "root/25", ("101", "Out1", "36", "Inactive"))
    fix_markers = []
    for graph, gate, writer, name, exact, downstream in (
        ("root/14", "4", "5", "CYB-640323", 0, ("8",)),
        ("root/38", "2", "3", "CYB-661474", 1, ("5", "11", "23")),
    ):
        assert bug[graph]["nodes"][gate]["reads"] == [
            {"$type": "questVarComparison_ConditionType", "comparisonType": "Greater", "factName": name, "value": 0}
        ]
        assert bug[graph]["nodes"][writer]["writes"] == [
            {"$type": "questSetVar_NodeType", "factName": name, "setExactValue": exact, "value": 1}
        ]
        assert [e for e in bug[graph]["edges"] if e[0] == gate] == [[gate, "False", writer, "In"]]
        fix_markers.append({"fact": name, "gate": gate, "writer": writer, "set_exact": exact,
                            "route": checked_route(bug, graph, *((writer, "Out", node, "In") for node in downstream))})
    controls = []
    for phase, edge in (
        ("root/23/5", ["54", "False", "26", "In"]),
        ("root/23/5", ["56", "CutSource", "16", "CutDestination"]),
        ("root/25", ["131", "CutSource", "105", "CutDestination"]),
    ):
        mutated = body | {phase: body[phase] | {"edges": [e for e in body[phase]["edges"] if e != edge]}}
        try:
            seam_checks(mutated, bug, scene)
        except AssertionError:
            controls.append({"graph": phase, "removed_edge": edge, "detected": True})
        else:
            raise AssertionError(f"Missing route was not detected: {edge}")
    p = private["root"]
    wrapper = p["nodes"]["34"]
    assert BODY in wrapper["refs"]
    incoming = [e for e in p["edges"] if e[2] == "34" and e[3] != "CutDestination"]
    assert incoming == [["1006", "Out", "34", "In1"], ["1106", "Out", "34", "CYB-661474_reinject"]]
    checked_route(private, "root", ("1004", "True", "1100", "In"), ("1100", "False", "1008", "In"),
                  ("1100", "True", "1110", "In1"))

    primary_owner = (
        (BASE, "root", "2", MAIN), (MAIN, "root", "82", None),
        (MAIN, "root/82", "6", MINOR), (MINOR, "root", "34", BODY),
    )
    bugfix_owner = primary_owner[:2] + (
        (MAIN, "root/82", "4", FIX_ROOT), (FIX_ROOT, "root", "9", FIX_QUEST),
        (FIX_QUEST, "root", "3", None), (FIX_QUEST, "root/3", "55", BUGFIX),
    )
    for owner in (primary_owner, bugfix_owner):
        for depot, graph, node, reference in owner:
            node_info = load_provider(depot)[graph]["nodes"][node]
            assert node_info["type"] == "questPhaseNodeDefinition"
            if reference is not None:
                assert node_info["refs"] == [reference], node_info
    return {"timers": clocks, "repair_input_routes": routes, "ordinary_post_spray": post_spray,
            "alternate_poi_input": alternate_poi, "native_bugfix_markers": fix_markers,
            "private_wrapper_incoming": incoming, "native_owners": [primary_owner, bugfix_owner],
            "selected_native_guards": {
                "bugfix_cyb640323": [bug["root/14"]["nodes"][n]["payload"] for n in ("4", "8", "10", "11", "12", "21", "23")],
                "bugfix_hooligan": bug["root/38"]["nodes"]["10"]["payload"],
                "body_cyb640323": body["root/23/5"]["nodes"]["54"]["payload"],
            }, "mutation_controls": controls}


def saved_records(inputs, owners, timers):
    compare_path = QR15 / "latest_save_01/compare_01/result.json"
    inputs.append(pin(compare_path))
    selected = read(compare_path)["selected_save"]
    assert selected["inputs"][0]["sha256"] == CURRENT_BODY
    for row in selected["inputs"]:
        pin_save(Path(row["path"]), row["sha256"])
    root_path = QR15 / "root_saved_resource_array_01/extraction.json"
    inputs.append(pin(root_path))
    root = read(root_path)
    inputs.append(pin(root["gap_path"], root["gap_sha256"]))
    assert root["source_sha256"] == CURRENT_BODY
    # Existing source proof binds this exact 17-byte root array and base ordinal.
    assert root["gap_sha256"] == "089255A038FA4296830F5C79DFB1F6871A33018839E59A39F0E813B7246DAE2E"
    manifest = QR15 / "event_stage_01/components_01/manifest.json"
    inputs.append(pin(manifest))
    capture = read(manifest)
    assert capture["source_sha256"] == CURRENT_BODY

    def component(name):
        row, = (r for r in capture["nodes"] if r["name"] == name)
        inputs.append(pin(row["path"], row["sha256"]))
        return Path(row["path"]).read_bytes(), row["id"]

    _, paths = decode_paths(*component("customArray"))
    events = native_records(*component("eventManager"))
    by_hash = defaultdict(set)
    for path in paths:
        by_hash[phase_hash(path)].add(path)

    def inspect_owner(chain):
        prefix = (0, *(int(link[2]) for link in chain))
        descendants = [path for path in paths if path[:len(prefix)] == prefix]
        addresses = {(prefix[:-1], prefix[-1])}
        if chain[-1][-1] == BODY:
            for timer in timers:
                path = prefix + tuple(map(int, timer["graph"].split("/")[1:]))
                addresses.add((path, int(timer["node"])))
        contexts = set(descendants) | {p for p, _ in addresses}
        for path in contexts:
            assert not by_hash[phase_hash(path)].difference({path}), ("phase hash collision", path)
        by_path = {phase_hash(path): path for path in contexts}
        matches = []
        for i, (token, h, node) in enumerate(events):
            if not token or node == 0xFFFF or h not in by_path:
                continue
            path = by_path[h]
            if path[:len(prefix)] == prefix or (path, node) in addresses:
                matches.append({"slot": i, "phase_path": path, "hash": f"0x{h:08X}", "node": node, "type": f"0x{token:016X}"})
        return {"owner_path": prefix, "interned_descendants": descendants,
                "queried_addresses": sorted(addresses), "saved_registrations": matches}

    fact_path = QR15 / "stores_autosave8_01/facts.json"
    inputs.append(pin(fact_path))
    fact_capture = read(fact_path)
    assert fact_capture["sha256"] == CURRENT_BODY and fact_capture["metadata_sha256"] == selected["inputs"][1]["sha256"]
    store, = (row for row in fact_capture["tables"] if row["physical_child_ordinal"] == 1)
    facts = {int(row["key_u32"]): row["value_u32"] for row in store["entries"]}
    assert len(facts) == len(store["entries"])
    names = ("CYB-640323", "CYB-661474", "mq037_brendan_introduced", "mq037_01_05Sure",
             "mq037_vandal_painted_brendan", "mq037_clerk_convinced", "mq037_done", "mq037_post_girl_scene_on",
             "PTFRS23_MQ037_Ready", "PTFRS23_MQ037_Issued", "PTFRS23_MQ037_Entered", "PTFRS23_MQ037_Finished")
    named = {name: {"key": fact_key(name), "value": facts.get(fact_key(name))} for name in names}
    assert named["CYB-640323"]["value"] == named["CYB-661474"]["value"] == 1
    result = {"selected_save": selected, "native_owner_queries": [inspect_owner(chain) for chain in owners],
              "named_facts": named, "missing_fact_value": "null denotes no saved record"}
    for row in selected["inputs"]:
        pin_save(Path(row["path"]), row["sha256"])
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    out = HERE / parser.parse_args().out
    if out.parent != HERE or out.exists():
        raise ValueError("Use a fresh output directory next to this script")
    providers = [QR13 / "brendan_provider_validation_01/manifest.json", QR15 / "root_binding_providers_01/manifest.json"]
    inputs = [pin(path) for path in providers]
    rows = [row for path in providers for row in read(path)["resources"]]
    models = {}

    def load_provider(depot):
        if depot not in models:
            row, = (r for r in rows if r["depot"] == depot)
            inputs.extend([pin(row["raw"], row["sha256"]), pin(row["json"], row["json_sha256"])])
            model = Resource(read(row["json"])).normalize()
            assert not model["errors"], model["errors"]
            models[depot] = model["graphs"]
        return models[depot]

    installed_path = HERE.parent / "quest_restoration_qr14/deployment_01/installed_manifest_01.json"
    inputs.append(pin(installed_path))
    installed = read(installed_path)
    assert installed["core_epoch"] == "QR13:02"
    source = pin(installed["core_source_epoch"], installed["core_source_epoch_sha256"])
    inputs.append(source)
    epoch = read(source["path"])
    archive, = (row for row in installed["core_files"] if row["path"].endswith("zzzz_PTFR_Combined.archive"))
    assert archive["sha256"] == epoch["archive_sha256"]
    inputs.append(pin(Path(installed["game_root"]) / archive["path"], archive["sha256"]))
    manifest = QR13 / "coordinator/brendan_06/serialized_01/manifest.json"
    inputs.append(pin(manifest))
    wrapper, = read(manifest)["resources"]
    assert wrapper["depot"] == PRIVATE and wrapper["raw_sha256"] == epoch["source_resources"][PRIVATE]
    inputs.extend([pin(wrapper["raw"], wrapper["raw_sha256"]), pin(wrapper["readback_json"], wrapper["readback_json_sha256"])])
    private = Resource(read(wrapper["readback_json"])).normalize()
    assert not private["errors"]

    evidence = source_analysis(load_provider, private["graphs"])
    saves = saved_records(inputs, evidence["native_owners"], evidence["timers"])
    assert not any(query["saved_registrations"] for query in saves["native_owner_queries"])
    inventory = QR15.parent / "quest_restoration_qr12/analysis_final_02/verified_fixture_inventory.json"
    inputs.append(pin(inventory, "8046C8E580AD007AED9E94A6655B08BBB1955A8569A974EC95FBA15E1950AB81"))
    rows_by_hash = {row["sha256"]: row for row in read(inventory)["rows"]}
    matches = []
    queried = ("mq037_brendan_introduced", "mq037_01_05Sure", "mq037_vandal_painted_brendan", "mq037_done")
    record_counts = dict.fromkeys(queried, 0)
    for digest, row in rows_by_hash.items():
        facts = row["saved_parse"]["facts"]
        names = {name: facts.get(name, []) for name in queried}
        for name, values in names.items():
            record_counts[name] += len(values)
        if any(v["value_u32"] > 0 for values in names.values() for v in values):
            matches.append({"save_sha256": digest, "source": row["source"]})
    assert not matches
    result = {"status": STATUS, "inputs": inputs, "source": evidence, "selected_saved_evidence": saves,
              "historical_fixture_projection": {"distinct_bodies": len(rows_by_hash), "retained_records_by_name": record_counts,
                                                "positive_rows": matches, "scope": "Prior QR12 selected fact tables only"},
              "runtime_candidate": None, "ready_tests": [], "game_calls": 0, "save_writes": 0}
    out.mkdir()
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{STATUS} | {len(evidence['timers'])} timers, {len(evidence['repair_input_routes'])} repair inputs, "
          f"{len(rows_by_hash)} prior save projections")


if __name__ == "__main__":
    main()
