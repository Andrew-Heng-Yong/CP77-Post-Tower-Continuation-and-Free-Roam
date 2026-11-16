"""Verify the Moving Heat save, Tower retirement and installed-owner contracts."""

import argparse
import json
import sqlite3
from pathlib import Path

from build import HERE, INSTALL, INSTALL_SHA, PREALPHA, load, pin, require, verify_baseline, write_json
from project_travel import CAPTURES

CLAIMS = (
    ("PTFRS22_Q304", "towercontinued\\sidejobs_s22\\moving_heat_boot.questphase", [1, 52640],
     "32a217281fb7d5fb", 9),
    ("PTFRS24_Q304_FRESH", "towercontinued\\sidejobs_s24\\ep1\\q304_fresh_boot.questphase", [1, 38682],
     "7b776e8bfb7737df", 90),
)
Q304 = "ep1/quests/minor_quest/q304_car_retrieval"
DOOR = f"{Q304}/01_car_retrieval/01_reach_the_door"
REPLY = f"{Q304}/01_car_retrieval/01_answer_to_ashlay_message"


def mandatory(condition, fact, expected):
    if condition["$type"] == "questLogicalCondition":
        children = condition["conditions"]
        require(children, "Empty logical gate")
        return {"OR": all, "AND": any}[condition["operation"]](
            mandatory(child["Data"], fact, expected) for child in children)
    if condition["$type"] != "questFactsDBCondition":
        return False
    body = condition["type"]["Data"]
    return (body["$type"] == "questVarComparison_ConditionType" and body["factName"] == fact
            and body["comparisonType"] == "Equal" and body["value"] == expected)


def verify_claims(baseline, db):
    rd10 = PREALPHA / "resume_dispatcher_rd10_kirk_20261113_01/archive_01/readback.json"
    combined = load(rd10, "5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81")
    require(combined["archive_sha256"] == baseline["archive_sha256"], "Wrong consolidated archive")
    members = {member["depot"]: member["sha256"] for member in combined["members"]}
    rd1 = PREALPHA / "resume_dispatcher_rd1_20261112_01/archive_04"
    s22 = load(rd1 / "moving_heat_boot.questphase.json",
               "EAAB7E974992F90B91AF046793B1D03414151DB6F3FEF6F070CA8717A11AE55B")
    pin(rd1 / "archive_source" / CLAIMS[0][1].replace("\\", "/"), members[CLAIMS[0][1]])
    s24_key = CLAIMS[1][1]
    sha, export, export_sha = db.execute(
        "SELECT sha256, export_path, export_sha256 FROM resources WHERE depot=?", (s24_key,)).fetchone()
    require(sha == members[s24_key], "Installed S24 payload differs from inspected provider")
    s24 = load(Path(export), export_sha)
    result = []
    game = Path(baseline["game_root"])
    history = game / "bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1"
    for doc, (tag, depot, address, key, late_node) in zip((s22, s24), CLAIMS, strict=True):
        graph = doc["Data"]["RootChunk"]["graph"]["Data"]
        nodes = {row["Data"]["id"]: row["Data"] for row in graph["nodes"]}
        for gate in (2, 3):
            require(mandatory(nodes[gate]["condition"]["Data"], tag + "_Permit", 1),
                    f"Permit does not fence every path in {depot}:{gate}")
        require(mandatory(nodes[late_node]["condition"]["Data"], tag + "_Issued", 1),
                f"Post-claim check lacks issued receipt: {depot}")
        if tag == "PTFRS22_Q304":
            refs = [entry["prefabNodeRef"]["$value"] for entry in nodes[1200]["phaseInstancePrefabs"]]
            require(refs == ["#q304_pr_car_retrieval"], "Scoped wrapper prefab changed")
        for filename, digest in CAPTURES.items():
            data = load(history / filename, digest)
            phase, = [row for row in data["phases"] if row[3] == address and row[1] == key]
            require(not any(row[3][:2] == address and len(row[3]) > 2 for row in data["phases"]),
                    f"Existing private descendant at cutoff: {depot}")
            handler, = [row for row in data["handlers"] if row[2] == phase[0]]
            require(handler[1] == "a135c358ccdc56c9" and handler[3:] == [2, 1],
                    f"Private owner is past its pre-claim listener: {depot}")
        result.append(dict(depot=depot, sha256=members[depot], address=address, permit_nodes=[2, 3],
                           issued_recheck=late_node, cutoff_state="PRE_CLAIM_ONLY"))
    return result


def verify_retirement(db):
    def edge(source, source_socket, target, target_socket):
        found = db.execute(
            "SELECT 1 FROM edges WHERE rid=13133 AND graph='root/10' AND source=? AND source_socket=? "
            "AND destination=? AND destination_socket=?", (source, source_socket, target, target_socket),
        ).fetchone()
        require(found, f"EP1 cleanup edge changed: {source} to {target}")

    edge(9, "CutSource", 4, "CutDestination")
    edge(9, "Out", 10, "In")
    node, = db.execute("SELECT parameters_json FROM nodes WHERE rid=13133 AND graph='root/10' AND id=10").fetchone()
    writer = json.loads(node)["type"]
    require(writer["factName"] == "q307_ep1_killed" and writer["setExactValue"] == writer["value"] == 1,
            "EP1 cleanup fact writer changed")
    return dict(graph="ep1/quest/ep1.questphase root/10", cut=9, retired_owner=4,
                killed_fact="q307_ep1_killed", fact_writer=10,
                admission_requirement="Prove the scoped cut/removal and separately observe the subsequent cleanup fact.")


def verify_saves():
    source = PREALPHA / "handler_preservation_hp1_20261112_01/analysis_01/save_comparison.json"
    snapshots = load(source, "705D5C51EC5277CEB439DE2D64701074F82B3B1EA0DA2A622E9198CEF52473A0")
    result = {}
    for name, state, count in (("ManualSave-26", 2, 7), ("AutoSave-10", 4, 7),
                               ("AutoSave-11", 4, 0), ("AutoSave-5", 4, 0)):
        saved = snapshots[name]
        rows = {row["path"]: row["state_u32"] for row in saved["journals"]}
        interrupted = [rows[p] for p in (Q304, Q304 + "/01_car_retrieval", DOOR)]
        require(interrupted == [state] * 3 and rows[REPLY] == 3 and
                saved["cases"]["q304_car_retrieval"]["handler_count"] == count, f"Unexpected state in {name}")
        result[name] = dict(save_sha256=saved["source_sha256"], journal=interrupted,
                            earlier_reply=rows[REPLY], registrations=count)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, choices=range(1, 100), required=True)
    args = parser.parse_args()
    baseline = load(INSTALL, INSTALL_SHA)
    verify_baseline(baseline)
    database = PREALPHA / "quest_resume_registry_20261112_01/registry_02/registry.sqlite3"
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        report = dict(status="SOURCE_AND_SAVED_CONTROLS_PASS", runtime_admission="DEFERRED",
                      installed_claims=verify_claims(baseline, db), ep1_cleanup=verify_retirement(db),
                      journals_and_registrations=verify_saves())
    output = HERE / f"review_{args.attempt:02}"
    output.mkdir()
    write_json(output / "assessment.json", report)
    print(f"Saved travel lifecycle assessment to {output}")


if __name__ == "__main__":
    main()
