"""Check Career Opportunities' native owner and the installed continuation."""

import argparse
import json
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
sys.path.insert(0, str(WORKSPACE / "tools" / "parity_audit"))
from common import fnv, read, sha, value
from model import Resource, reachable

STORIES = r"base\open_world\mini_world_stories"
WATSON = STORIES + r"\watson\watson_mini_world_stories.questphase"
CAREER = STORIES + r"\watson\mws_wat_08\mws_wat_08.questphase"
PRIVATE = "\\".join((r"towercontinued\sidejobs_s30\native", CAREER))
ENTRY = r"towercontinued\sidejobs_s30\entries\mws_wat_08_trauma_drama.questphase"
MAIN = r"base\quest\cyberpunk2077.quest"
MAIN_PHASE = MAIN + "phase"
ELEMENTS = r"base\quest\additional_game_elements.questphase"
OPEN_WORLD = r"base\open_world\phases\open_world_content.questphase"
TOWER = r"ep1\quest\main_quests\q307\q307.questphase"
CLEANUP = r"ep1\quest\main_quests\q307\phases\q307_cleanup.questphase"
EARLY = ("6", "68", "7", "57", "56", "8", "9", "66")


def fnv32(data, seed=2166136261):
    for byte in data:
        seed = ((seed ^ byte) * 16777619) & 0xFFFFFFFF
    return seed


def verify(capture):
    manifest = read(capture / "manifest.json")
    checks = []

    def check(name, ok, detail=None):
        if not ok:
            raise ValueError(f"{name}: {detail}")
        checks.append({"name": name, "detail": detail})

    rows = manifest["resources"]
    models = {}
    for row in rows:
        check("captured provider hash and depot identity", (
            sha(capture / row["raw"]) == row["sha256"] and fnv(row["depot"]) == row["id"]
        ), row["depot"])
        if "json" not in row:
            continue
        check("captured export hash", sha(capture / row["json"]) == row["json_sha256"], row["depot"])
        if row["depot"] in models:
            raise ValueError(f"Ambiguous provider for {row['depot']}")
        models[row["depot"]] = Resource(read(capture / row["json"])).normalize()
    check("bounded index and content search completed", not manifest["extraction_failures"], {
        "archive_indexes": len(manifest["archives"]),
        "scanned_resources": sum(archive["scanned"] for archive in manifest["archives"]),
        "decode_errors": [row["depot"] for row in rows if "decode_error" in row],
    })

    def graph(depot, name="root"):
        return models[depot]["graphs"][name]

    # Authoritative phase references and their actual wired inputs.
    chain = [
        (MAIN, "root", "2", "Start", MAIN_PHASE),
        (MAIN_PHASE, "root/82", "3", "Input", ELEMENTS),
        (ELEMENTS, "root", "19", "In1", OPEN_WORLD),
        (OPEN_WORLD, "root", "93", "In1", STORIES + r"\ow_mini_world_stories.questphase"),
        (STORIES + r"\ow_mini_world_stories.questphase", "root", "7", "In1", WATSON),
        (WATSON, "root", "63", "Input", CAREER),
    ]
    for depot, graph_name, node, socket, child in chain:
        parent = graph(depot, graph_name)
        check("wired native owner ancestry", (
            parent["nodes"][node]["refs"] == [child]
            and node in parent["reachable"]
            and any(edge[2:] == [node, socket] for edge in parent["edges"])
        ), [depot, graph_name, node, socket, child])
    main = graph(MAIN_PHASE)
    check("owner and ending termination share the same main-game phase", (
        ["0", "Out", "82", "In1"] in main["edges"]
        and ["108", "Out1", "106", "In"] in main["edges"]
        and ["106", "Out", "109", "In"] in main["edges"]
        and ["109", "Out", "107", "In"] in main["edges"]
        and main["nodes"]["106"]["reads"][0]["path"]["realPath"] == "ep1/quests/main_quest/q307_before_tomorrow"
        and main["nodes"]["106"]["reads"][0]["state"] == "Succeeded"
        and main["nodes"]["109"]["writes"][0]["factName"] == "q307_main_game_killed"
        and main["nodes"]["107"]["payload"]["type"] == "Terminating"
    ), "native main phase 106 → 109 → 107")
    check("The Tower has a later, separate native completion write", (
        graph(TOWER)["nodes"]["30"]["refs"] == [CLEANUP]
        and graph(CLEANUP)["nodes"]["20"]["writes"][0]["factName"] == "q307_finished"
    ))
    check("the installed private owner enters under the genuine completion gate", (
        graph(ENTRY)["nodes"]["64000"]["refs"] == [PRIVATE]
        and ["65006", "Out", "64000", "Input"] in graph(ENTRY)["edges"]
        and all(
            {"$type": "questVarComparison_ConditionType", "comparisonType": "Equal",
             "factName": name, "value": 1} in graph(ENTRY)["nodes"][node]["reads"]
            for node in ("65003", "65004")
            for name in ("PostTowerFreeRoamActive", "q307_main_game_killed", "q307_finished")
        )
    ))

    vanilla, restored = graph(CAREER), graph(PRIVATE)
    check("original early route and identities match the installed copy", (
        all(vanilla["nodes"][node] == restored["nodes"][node] for node in (*EARLY, "64", "83"))
        and all(edge in restored["edges"] for edge in vanilla["edges"] if edge[0] in EARLY)
        and vanilla["nodes"]["6"]["reads"][0]["factName"] == "shooter_appeared_on_leaderboard"
        and vanilla["nodes"]["8"]["reads"][0]["factName"] == "shooter_position_1"
    ), list(EARLY))
    check("first-place rewards are downstream of the original first-place gate", (
        "64" in reachable(vanilla["nodes"], vanilla["edges"], ["8"])
        and not any(
            edge[2] == "9" and edge[0] != "8" for edge in vanilla["edges"]
        )
        and value(vanilla["nodes"]["64"]["payload"]["type"]["rewards"][0]) == "QuestRewards.trauma_drama_place_1"
    ))

    # Reuse a frozen post-Tower extract. The registered root index is an ID,
    # while the selected physical graph-store keys only bound saved evidence.
    prior = WORKSPACE / "prealpha" / "quest_restoration_qr15"
    binding = read(prior / "saved_graph_state_01/inspector_review_01/root_binding_decode_01.json")
    saved = read(prior / "stores_autosave8_01/facts.json")
    root_capture = read(prior / "root_saved_resource_array_01/extraction.json")
    check("existing save extracts bind the same snapshot and production root", (
        root_capture["source_sha256"] == saved["sha256"]
        and root_capture["gap_sha256"] == binding["gap_sha256"]
        and any(row["index"] == 0 and row["depot"] == MAIN and row["resource_path_u64"] == fnv(MAIN)
                for row in binding["members"])
        and not any(row["depot"].endswith(r"\mws_wat_08.quest") for row in binding["members"])
    ), saved["sha256"])
    stores = {
        table["physical_child_ordinal"]: {int(row["key_u32"]): row["value_u32"] for row in table["entries"]}
        for table in saved["tables"]
    }
    phase_path = [0, 2, 82, 3, 19, 93, 7, 63]
    phase_seed = int(binding["seed_values"]["0"], 16)
    phase_hash = fnv32(struct.pack("<" + "H" * len(phase_path), *phase_path), phase_seed)
    selected = {node: fnv32(struct.pack("<II", int(node), phase_hash)) for node in EARLY}
    existing = {node: {idx: store[key] for idx, store in stores.items() if idx > 1 and key in store}
                for node, key in selected.items()}
    facts = {
        name: stores[1].get(fnv32(name.encode()))
        for name in ("q307_finished", "q307_main_game_killed", "shooter_appeared_on_leaderboard", "shooter_position_1")
    }
    check("frozen post-Tower sample lacks an earned-score transition fixture", (
        facts["q307_finished"] == facts["q307_main_game_killed"] == 1
        and facts["shooter_appeared_on_leaderboard"] is None
        and facts["shooter_position_1"] is None
        and all(not hits for hits in existing.values())
    ), {"named_saved_facts": facts, "phase_path": phase_path, "node_keys": selected, "matches": existing})

    return {"checks": checks, "runtime_changes": [], "remaining": [
        "Genuine pre-first-place fixture with observed manufacturer contact and message state.",
        "Actual queued timer/listener retirement and one-time notifications/reward across the retained transition.",
    ]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = verify(args.capture)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, indent=2) + "\n")
    print(f"{len(report['checks'])} checks passed")
