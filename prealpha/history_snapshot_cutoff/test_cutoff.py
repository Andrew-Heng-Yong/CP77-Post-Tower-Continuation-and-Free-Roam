"""Verify the pickup graph, save evidence, and the staged REDscript cutoff."""

import json
import re
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_PATH = "package/r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds"
Q307 = ROOT / "research/q307_extracted/json/ep1/quest/main_quests/q307"

# This existing reader resolves graph handles and validates nested sockets.
sys.path.insert(0, str(ROOT / "prealpha/phone_support_ph1"))
from model import model


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def method(source, name):
    start = re.search(r"(?m)^  (?:private|protected) (?:cb )?func " + name + r"\(", source)
    assert start, name
    end = source.index("\n  }", start.end())
    return source[start.start():end]


def fact_predicate(expression, facts):
    """Evaluate the conjunctions and disjunctions in the authored fact gates."""
    def check(term):
        match = re.fullmatch(r'this\.Fact\("(\w+)"\)(==|>|!=)(\d+)', term)
        assert match, term
        actual = facts.get(match[1], 0) or 0
        expected = int(match[3])
        return {"==": actual == expected, ">": actual > expected, "!=": actual != expected}[match[2]]

    groups = re.sub(r"\s+", "", expression).split("||")
    return any(all(check(term) for term in group.split("&&")) for group in groups)


def verify_native_cutoff():
    scene = read(Q307 / "scenes/q307_01_pickup.scene.json")["Data"]["RootChunk"]
    nodes = {h["Data"]["nodeId"]["id"]: h["Data"] for h in scene["sceneGraph"]["Data"]["graph"]}
    for node in (2777, 2781):
        action = nodes[node]["questNode"]["Data"]["type"]["Data"]
        assert (action["factName"], action["value"], action["setExactValue"]) == (
            "q307_point_of_no_return", 1, 1)
    targets = [target["nodeId"]["id"] for socket in nodes[2777]["outputSockets"]
               for target in socket["destinations"]]
    assert 2029 in targets
    assert nodes[2029]["questNode"]["Data"]["type"]["Data"]["factName"] == "q307_confirm_av_start"

    pickup = model(Q307 / "phases/q307_01_pickup.questphase.json")
    root = pickup["root"]
    assert (11, "Out", 43, "In") in root["edges"]
    assert (43, "Out", 56, "In") in root["edges"]
    assert (56, "Out", 47, "In") in root["edges"]
    assert (47, "False", 10, "In1") in root["edges"]
    assert (47, "True", 85, "In") in root["edges"]
    assert root["nodes"][11]["condition"]["type"]["factName"] == "q307_point_of_no_return"
    assert root["nodes"][47]["condition"]["type"]["factName"] == "q115_point_of_no_return"
    chain = pickup["root/10"]
    assert (0, "Out", 96, "In") in chain["edges"]
    for predecessor, successor in zip((96, 99, 97, 169), (99, 97, 169, 59)):
        assert (predecessor, "Out", successor, "In") in chain["edges"]
    assert chain["nodes"][99]["condition"]["type"]["factName"] == "holo_setup_started"
    assert chain["nodes"][97]["condition"]["type"]["miliseconds"] == 500
    for i, path in ((59, "quests/main_quest"), (62, "quests/minor_quest"), (128, "ep1/quests/minor_quest")):
        node = chain["nodes"][i]["type"]
        assert node["$type"] == "questJournalBulkUpdate_NodeType"
        assert node["path"]["realPath"] == path
        assert node["requiredEntryState"]["$value"] == "Active"
        assert node["newEntryState"]["$value"] == "Failed"
        assert node["propagateChange"] == 1


def verify_saved_observation():
    checkpoints = read(HERE / "evidence_01/save_checkpoints.json")["slots"]
    before, opening, hospital, later = checkpoints
    assert len({entry["playthrough"] for entry in checkpoints}) == 1
    assert before["facts"]["q307_point_of_no_return"] is None
    assert opening["facts"]["q307_point_of_no_return"] == 1
    for key in ("q307_main_game_killed", "q307_ep1_killed"):
        assert opening["facts"][key] is None and hospital["facts"][key] == 1
    assert opening["snapshot"]["origin"] == hospital["snapshot"]["origin"] == later["snapshot"]["origin"] == "pre_ending_candidate"
    assert later["snapshot"]["fileToken"] is None
    rows = read(HERE / "evidence_01/journal_comparison.json")["saves"]
    assert all(row["tracked_matches"] for row in rows)
    for path in ("quests/minor_quest/mq025_psycho_brawl",
                 "ep1/quests/minor_quest/q304_car_retrieval",
                 "quests/minor_quest/mq017_streetkid"):
        assert len(rows[0]["selected"][path]) == len(rows[1]["selected"][path]) == 1
        assert rows[0]["selected"][path][0][8:16] == "02000000"
        assert rows[1]["selected"][path][0][8:16] == "04000000"
        assert rows[2]["selected"][path] == rows[1]["selected"][path]
    return before["facts"]


def verify_script(before_pickup):
    old = (ROOT / "prealpha/quest_parity_qp2/candidate_01" / SOURCE_PATH).read_text(encoding="utf-8-sig")
    new = (HERE / "candidate_01" / SOURCE_PATH).read_text(encoding="utf-8-sig")
    assert old.split("public class SnapshotStateHS1", 1)[0] == new.split("public class SnapshotStateHS1", 1)[0]
    assert old.split("  public func Ready()", 1)[1] == new.split("  public func Ready()", 1)[1]
    persistent = r"(?m)^\s*(?:private|public) persistent let .+$"
    assert re.findall(persistent, old) == re.findall(persistent, new)

    direct = method(new, "OnTowerBoundary")
    assert 'n"q307_point_of_no_return",this,n"OnTowerBoundary"' in new
    assert "this.LivePreEndingSample()" in direct and "lastCapture" not in direct
    assert 'if this.Fact("q307_point_of_no_return")==1 { this.FinishTowerCutoff(); }' in direct
    assert "this.lastCapture>=0.0" in method(new, "LivePreEndingSample")
    assert "age<=6.0" in method(new, "OnBoundary")
    assert "this.towerCutoffPending=false;" in method(new, "OnDetach")
    restore = new.split("  public func Restored()", 1)[1].split("  private func Register()", 1)[0]
    assert "this.lastCapture=-100.0" in restore and "this.towerCutoffPending=false" in restore

    window = method(new, "TowerCutoffOpen").split("return ", 1)[1].split(";", 1)[0]
    window = window.strip().removesuffix("!this.Teardown()").rstrip().removesuffix("&&")
    teardown = method(new, "Teardown").split("return ", 1)[1].split(";", 1)[0]
    def can_retry(facts):
        return fact_predicate(window, facts) and not fact_predicate(teardown, facts)

    assert not can_retry(before_pickup)
    cutoff = before_pickup | {"q307_point_of_no_return": 1}
    assert can_retry(cutoff)
    for fact in ("q115_point_of_no_return", "q307_av_fade_out", "q307_debug_reset", "q307_2079",
                 "q307_main_game_killed", "q307_ep1_killed", "q307_done", "q307_finished", "PostTowerFreeRoamActive"):
        assert not can_retry(cutoff | {fact: 1}), fact
    assert not can_retry(cutoff | {"q307_active": 0})

    freeze = method(new, "TryFreeze")
    checks = [m.start() for m in re.finditer(r"jm\.HasAnyDelayedStateChanges\(\)", freeze)]
    assert len(checks) == 2
    assert checks[0] < freeze.index("this.ReadRow(i)") < checks[1] < freeze.index("this.rows[i].stable=stable[i]")
    assert 'ArrayFindFirst(SnapshotDataHS1.Facts(i),"q307_point_of_no_return")' in freeze
    assert "this.rows[i].stable && this.Same" in freeze
    assert "this.rows[i].states" not in freeze and "this.rows[i].facts" not in freeze
    same = method(new, "Same")
    assert "a.states[k]!=b.states[k]" in same and "a.counters[k]!=b.counters[k]" in same
    assert "a.facts[k]!=b.facts[k] && !(k==cutoffIndex && a.facts[k]==0 && b.facts[k]==1)" in same
    assert "if this.TryFreeze(true) { this.towerCutoffPending=false; }" in method(new, "FinishTowerCutoff")
    poll = new.split("  public func Poll(epoch: Int32)", 1)[1].split("  public func Ready()", 1)[0]
    assert poll.index("if this.towerCutoffPending") < poll.index("if !post && this.Boundary()")
    assert 'this.origin=n"post_ending_fallback"' in poll


if __name__ == "__main__":
    verify_native_cutoff()
    verify_script(verify_saved_observation())
    print("PASS: native pickup path, observed journal changes, cutoff and preservation checks")
