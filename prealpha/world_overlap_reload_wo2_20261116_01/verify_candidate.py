"""Check WO2 against exact saved owner and current installed phase evidence."""

from pathlib import Path
import json
import math

from prepare_candidate import BASE, BASE_SHA, GAME, HERE, OUT, SCRIPT, SCRIPT_SHA, check_rows, sha

WO1 = HERE.parent / "world_overlap_20261116_01"
SAVE16_XY = (-1445.5908203125, 1182.3636474609375)


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def method(source: str, name: str) -> str:
    begin = source.index(f"func {name}(")
    open_brace = source.index("{", begin)
    level = 1
    index = open_brace + 1
    while level:
        level += (source[index] == "{") - (source[index] == "}")
        index += 1
    return source[begin:index]


def fact(row: dict, name: str) -> int:
    values = row["facts"][name]
    assert len(values) <= 1, (name, values)
    return values[0] if values else 0


def main() -> None:
    checks = []
    def check(label: str, result: bool) -> None:
        if not result:
            raise AssertionError(label)
        checks.append(label)

    base = read(BASE)
    candidate = read(OUT / "core_manifest_01.json")
    compiled = read(OUT / "compile_01/assessment.json")
    saved = read(OUT / "saved_facts_01.json")
    phase = read(OUT / "saved_phase_02.json")
    check("exact installed BV1 baseline", sha(BASE) == BASE_SHA)
    check_rows(base["core_files"] + base["required_files"])
    check("one changed Core path", candidate["changed_paths"] == [SCRIPT] and len(candidate["core_files"]) == 51)
    check("archive and XL exact predecessor", all(
        a == b for a, b in zip(base["core_files"][:2], candidate["core_files"][:2])))
    check("all other Core bytes preserved", all(
        a == b for a, b in zip(base["core_files"], candidate["core_files"]) if a["path"] != SCRIPT))
    check("all registered sources compile", compiled["status"] == "PASS" and
          compiled["registered_sources"] == 149 and compiled["changed_sources"] == [SCRIPT])
    original = (GAME / SCRIPT).read_text(encoding="utf-8-sig")
    staged = (OUT / "package" / SCRIPT).read_text(encoding="utf-8-sig")
    check("script exact input and candidate", sha(GAME / SCRIPT) == SCRIPT_SHA and
          sha(OUT / "package" / SCRIPT) == candidate["script_after"])
    for name in ("Completed", "Safe", "OnDetach", "Schedule", "Poll"):
        check(f"existing {name} behavior unchanged", method(original, name) == method(staged, name))
    attach = method(staged, "OnAttach")
    street = method(staged, "SafeStreet")
    permit = method(staged, "RefreshStreetCleanupPermit")
    check("attach clears stale permit before prompt recheck", attach.index('SetFact(n"PTFRWO1_CleanupPermit", 0)') <
          attach.index("this.RefreshStreetCleanupPermit"))
    check("only street cleanup uses new near-player safety", "this.SafeStreet(p)" in permit and
          "this.SafeStreet(p)" not in method(staged, "Poll"))
    check("street safety retains gameplay locks", all(token in street for token in (
        "p.IsAttached()", "p.IsInCombat()", "scenes.IsEntityInScene", "workspots.IsActorInWorkspot",
        "EntityID.IsDefined(mounting.parentId)", "content.IsTokensActivationBlocked()",
        "GameInstance.IsSavingLocked")))
    check("street permit retains genuine and existing-owner gates", all(token in permit for token in (
        "this.Completed(q)", 'PTFRMV_Applied") == 1', 'PTFRWO1_CleanupRegistered") == 1',
        'PTFRWO1_CleanupDone") == 0')))
    check("near-player distance block removed only from street permit", "250000.0" not in permit and
          "6400.0" in method(staged, "Safe") and "6400.0" not in street)
    wo1_phase = WO1 / "work/graph_01/source/towercontinued/street_overlap_wo1/cleanup.questphase"
    check("original serialized WO1 phase preserved", sha(wo1_phase) == "C7A85861A3A98650BDCA120656BEB77310CFDA736C0BFCD05F348B329C9809F7")
    assert saved["status"] == "READ_ONLY_SERIALIZED_FACTS"
    rows = {row["slot"]: row for row in saved["rows"]}
    auto, manual, ending = (rows[name] for name in ("AutoSave-16", "ManualSave-33", "EndGameSave-106"))
    check("AutoSave-16 source hash", auto["sha256"] == "E05D03A335CE62EB6E3E728A88F3944D9D05BC1EF58AE100DD6195F34D250482")
    positive = ("PostTowerFreeRoamActive", "PTFRP0_DR13", "q307_done", "q307_finished", "q307_2079",
                "q307_main_game_killed", "q307_ep1_killed", "PTFRMV_Registered", "PTFRMV_Applied",
                "PTFRWO1_CleanupRegistered")
    zero = ("q307_active", "q305_johnny_scene_active", "q115_point_of_no_return",
            "PTFRBASE_Suspended", "PTFRWORLD_Suspended", "PTFRMV_Suspended",
            "PTFRMV_QuestOwns", "PTFRWO1_CleanupDone")
    check("AutoSave-16 genuine completion and pending cleanup facts", all(fact(auto, name) == 1 for name in positive)
          and all(fact(auto, name) == 0 for name in zero) and fact(auto, "PTFRMV_Revision") == 7)
    old_distance = math.dist(SAVE16_XY, (-1475.0, 1080.0))
    check("AutoSave-16 blocked by old 500 m street gate", old_distance < 500.0)
    check("AutoSave-16 outside preserved clinic gate", math.dist(SAVE16_XY, (-1542.0, 1210.0)) > 80.0)
    check("completed ManualSave-33 remains excluded", fact(manual, "PTFRWO1_CleanupDone") == 1)
    check("pre-restoration EndGameSave-106 remains excluded", fact(ending, "PTFRMV_Applied") == 0)
    assert phase["status"] == "READ_ONLY_SAVED_PHASE_MEMBERSHIP"
    phase_rows = {row["slot"]: row for row in phase["rows"]}
    waiting = phase_rows["AutoSave-16"]
    check("same AutoSave-16 body for phase scan", waiting["sha256"] == auto["sha256"])
    check("WO1 saved child path and waiting node retained", waiting["phase_paths_containing_42351"] == [[1, 42351]]
          and any(row["hash"] == 4174010774 and row["node"] == 2 for row in waiting["exact_event_rows"])
          and any(row["hash"] == 1236048738 and row["node"] == 42351 for row in waiting["exact_event_rows"]))
    check("completed ManualSave-33 has no WO1 handler", not phase_rows["ManualSave-33"]["exact_event_rows"])
    result = {
        "status": "PASS_OFFLINE_CANDIDATE", "checks": checks, "check_count": len(checks),
        "selected_fixture": "AutoSave-16; user reported the same street meshes on immediate fresh load",
        "old_distance_m": old_distance,
        "saved_owner_evidence": "WO1 child [1,42351] node 2 and EP1 parent node 42351 retained in AutoSave-16 EventManager",
        "limits": ["Serialized facts and handler rows do not prove current runtime dispatch or visible mesh removal.",
                   "The exact frame of world streaming versus ScriptableSystem attachment requires a live load test.",
                   "ManualSave-33's saved Done=1 is preserved; post-dispatch reload persistence remains unqualified.",
                   "Removing the final-scene variant near V may visibly settle collision onto the ordinary road; original street restoration is paired in the native action."],
        "game_writes": 0, "save_writes": 0,
    }
    path = OUT / "assessment.json"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(f"PASS: {len(checks)} source/save/owner/compile checks; old distance={old_distance:.1f} m")


if __name__ == "__main__":
    main()
