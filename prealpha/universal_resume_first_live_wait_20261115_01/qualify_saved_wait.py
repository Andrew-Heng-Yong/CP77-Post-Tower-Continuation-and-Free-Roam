"""Read the current pre-ending fixture and bind direct and first-level logical waits."""

import argparse
from collections import defaultdict
from contextlib import closing
import json
from pathlib import Path
import re
import sqlite3
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
EARLIER = PREALPHA / "universal_resume_live_handoff_20261114_01"
INSTALLED = PREALPHA / "universal_resume_save_session_20261115_01/deployment_01/installed_manifest_01.json"
CONTROL = EARLIER / "run_saves_03/PointOfNoReturnSave-0.json"
BASE_SLOT = "ManualSave-30"
SAVE_SHA = "6D1EFBA83496CD1D53A6EC91F87A1E201D8AEC09B11B3BFF5B12A20A895E9146"
TOWER_CONTROL = "ManualSave-29"
TOWER_CONTROL_SHA = "33CC1F6E96B1E8ACB357A91AA5CF2BBEE924DF70D1BAC771FFC3BE623A2397DE"
CANDIDATE = "mq049_edgerunners"
WAIT_OBJECTIVE = "quests/minor_quest/mq049_edgerunners/01_el_captian/02_wait"
ORIGINAL = (0, 2, 82, 4, 9, 3, 64)
PRIVATE = (1, 35238, 64)

sys.path.insert(0, str(EARLIER))
from find_timer_fixtures import (CONTRACTS, REGISTRY, ROOTS, GAME_DELAY, REAL_DELAY, component, framed,
                                 game_records, journal_hash, paths, phase_hash, pin, read, real_records,
                                 sha, token, write)


def select_waits():
    contracts = read(pin(CONTRACTS / "analysis_07/contracts.json",
                         "02A19F25EC7478DEB667F308FF876428D78D8E91DC6ADB9732ED5B2E060FC31F"))
    scopes = read(pin(CONTRACTS / "analysis_05/owner_map.json",
                      "B64B9010580CFFE9B5B642EAC8ACB17FFCF437DC16A6B84CCCBD8C7234F9907E"))["scopes"]
    pin(REGISTRY, "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9")
    by_graph = defaultdict(list)
    with closing(sqlite3.connect(REGISTRY.as_uri() + "?mode=ro", uri=True)) as db:
        roots = dict(db.execute("SELECT id, journal_root FROM quests"))
        for rid, graph, node, raw in db.execute(
            "SELECT n.rid, n.graph, n.id, n.parameters_json FROM nodes n "
            "JOIN resources r ON r.rid=n.rid WHERE r.role='STOCK' AND "
            "n.type='questPauseConditionNodeDefinition' AND "
            "(n.parameters_json LIKE '%questGameTimeDelay_ConditionType%' OR "
            "n.parameters_json LIKE '%questRealtimeDelay_ConditionType%')"
        ):
            condition = json.loads(raw).get("condition") or {}
            logical = condition.get("$type") == "questLogicalCondition"
            children = enumerate(condition.get("conditions") or [], start=1) if logical else [(0, condition)]
            for child, entry in children:
                value = entry.get("type") if isinstance(entry, dict) else None
                if not isinstance(value, dict) or value.get("$type") not in (GAME_DELAY, REAL_DELAY):
                    continue
                seconds = sum(value.get(name, 0) * factor for name, factor in (
                    ("days", 86400), ("hours", 3600), ("minutes", 60), ("seconds", 1), ("miliseconds", 0.001)
                ))
                if seconds > 0 and 0 <= node < 0xFFFF:
                    clock = value["$type"]
                    kind = condition["$type"] if logical else clock
                    by_graph[rid, graph].append((node, child, clock, seconds, kind))
    targets = defaultdict(dict)
    journals = {}
    candidate_paths = set()
    for quest in contracts["quests"]:
        qid = quest["id"]
        if quest["whole_quest_exception"] or not roots.get(qid):
            continue
        journals[qid] = journal_hash(roots[qid])
        for scope_id in quest["scope_selectors"]["body_scope_ids"]:
            scope = scopes[scope_id]
            address = scope["address"]
            if not address or scope["kind"] != "quest":
                continue
            if qid == CANDIDATE:
                candidate_paths.add(tuple(address))
            for node, child, clock, seconds, kind in by_graph[scope["rid"], scope["graph"]]:
                key = (phase_hash(address), node, token(kind))
                identity = (qid, tuple(address), scope["sha256"], scope["graph"], child)
                targets[key][identity] = dict(quest=qid, title=quest["title"], journal_hash=journals[qid],
                                              phase_address=address, node=node, child=child, clock=clock,
                                              authored_seconds=seconds, provider_sha256=scope["sha256"],
                                              depot=scope["depot"], graph=scope["graph"],
                                              scoped_exception=quest["scoped_exception"])
    return targets, journals, candidate_paths


def bind_waits(raw, targets):
    parts = raw["components"]
    if bytes.fromhex(raw["root_array"]) != bytes([len(ROOTS)]) + struct.pack("<QQ", *(token(n) for n in ROOTS)):
        raise ValueError("Unexpected native root resources")
    addresses = defaultdict(set)
    for path in paths(component(parts["paths"]), parts["paths"]["id"]):
        if path and path[0] < len(ROOTS):
            addresses[phase_hash(path)].add(path)
    items = list(struct.iter_unpack("<QQ", framed(component(parts["instances"]), parts["instances"]["id"], 16)))
    instances = dict(items)
    if len(instances) != len(items):
        raise ValueError("Duplicate node-instance keys")
    core = component(parts["time_core"])
    if len(core) != 24:
        raise ValueError("Unsupported game clock record")
    clock, = struct.unpack_from("<I", core, 8)
    game = game_records(component(parts["time_timers"])[4:])
    real = real_records(component(parts["delay_structs"])[4:])
    journals = dict(raw["journal"])
    native_timers = set()
    matches = []
    for slot, kind, phase, node in raw["phase_registrations"]:
        rows = targets.get((phase, node, int(kind, 16)), {})
        for source in rows.values():
            if addresses[phase] != {tuple(source["phase_address"])}:
                continue
            node_key = phase << 32 | source["child"] << 16 | node
            timer = instances.get(node_key)
            duration = None
            if source["clock"] == GAME_DELAY and timer in game:
                deadline, authored = game[timer]
                if 0 < deadline - clock <= authored == source["authored_seconds"]:
                    duration = deadline - clock
            elif source["clock"] == REAL_DELAY and timer in real:
                if 0 < real[timer] <= source["authored_seconds"]:
                    duration = real[timer]
            if duration is not None:
                native_timers.add((source["clock"], timer))
                matches.append(dict(source, physical_slot=slot, node_key=f"{node_key:016X}",
                                    timer=f"{timer:016X}", remaining_seconds=duration,
                                    journal_states=journals.get(source["journal_hash"], [])))
    return matches, len(native_timers)


def make_reader(out):
    source = pin(EARLIER / "ReadTimerFixtures.ps1",
                 "3CAC00DA5568AEB1331031EB8B433E81B1BDC0B9B2D7C9226FEB212B5C9402C6").read_text(encoding="utf-8")
    a = source.index("        $timed = @(")
    b = source.index("        $journal = Single ", a)
    source = source[:a] + r"""        $members = @(for ($slot = 0; $slot -lt $events.Count; ++$slot) {
            $row = $events[$slot]
            if ($phaseKeys.Contains([uint32]$row.Unknown2) -and $row.Unknown4 -eq 0) {
                ,@($slot, $row.Unknown1.ToString('x16'), $row.Unknown2, $row.Unknown3)
            }
        })
        $Result.phase_registrations = $members
""" + source[b:]
    source = source.replace("'q307_visited_rooftop')", "'q307_visited_rooftop') + @($selection.fact_names)")
    a = source.index("        if ($recorded.q307_done")
    b = source.index("        $eventNode = Single ", a)
    normal_gate = "".join("    " + line if line.strip() else line for line in source[a:b].splitlines(keepends=True))
    control_gate = """        if ($selection.tower_control) {
            if ($recorded.q307_finished -ne 1 -or $recorded.q307_main_game_killed -ne 1 -or
                $recorded.q307_ep1_killed -ne 1) { throw 'Expected recorded Tower finish and cleanup' }
        } else {
"""
    source = source[:a] + control_gate + normal_gate + "        }\n\n" + source[b:]
    source = source.replace("^run_saves_[0-9]{2}$", "^run_[0-9]{2}$")
    source = source.replace("$PSScriptRoot", "(Split-Path $PSScriptRoot -Parent)")
    source = source.replace("Where-Object Name -cne 'selection.json'",
                            "Where-Object Name -cnotin @('selection.json','ReadFixture.ps1')")
    path = out / "ReadFixture.ps1"
    path.write_text(source, encoding="utf-8")
    return path


def falco_stage(raw, matches, parent_journal, paths_for_quest):
    by_hash = defaultdict(set)
    part = raw["components"]["paths"]
    for address in paths(component(part), part["id"]):
        if address:
            by_hash[phase_hash(address)].add(address)
    rows = {addr: [] for addr in sorted(paths_for_quest)}
    target_by_hash = {phase_hash(addr): addr for addr in rows if by_hash[phase_hash(addr)] == {addr}}
    for slot, kind, phase, node in raw["phase_registrations"]:
        if phase in target_by_hash:
            rows[target_by_hash[phase]].append({"slot": slot, "type": kind, "node": node})
    journal = dict(raw["journal"])
    target = [row for row in matches if row["quest"] == CANDIDATE and row["node"] == 28]
    facts = raw["facts"]
    active_journal = journal.get(parent_journal, [])
    wait_journal = journal.get(journal_hash(WAIT_OBJECTIVE), [])
    other_owner = any(entries for addr, entries in rows.items() if addr[:len(PRIVATE)] == PRIVATE)
    reyes = rows.get(ORIGINAL + (11,), [])
    bound = (len(target) == 1 and tuple(target[0]["phase_address"]) == ORIGINAL + (12,)
             and 0 < target[0]["remaining_seconds"] < target[0]["authored_seconds"])
    matched = (bound and active_journal == [2] and wait_journal == [2] and facts["q307_ready"] == 1
               and facts["mq049_started"] == 1 and not any(facts[key] for key in (
                   "mq049_done", "mq049_finished", "mq049_falco_done", "mq049_jacket_looted"))
               and any(row["node"] == 23 for row in reyes) and not other_owner)
    return {
        "saved_stage": "BOUND_ORIGINAL_PENDING_FALCO_WAIT" if matched else "UNQUALIFIED",
        "original_wait_bound": bound, "additional_private_owner_rows": other_owner,
        "parent_journal_states": active_journal, "wait_objective_states": wait_journal,
        "registrations": [{"address": addr, "handlers": entries} for addr, entries in rows.items() if entries],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100))
    parser.add_argument("--slot", default=BASE_SLOT)
    parser.add_argument("--tower-control", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"ManualSave-[0-9]+", args.slot):
        parser.error("Expected a normal ManualSave-N slot")
    if args.tower_control and args.slot != TOWER_CONTROL:
        parser.error(f"The Tower control uses the verified {TOWER_CONTROL}")
    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    baseline = read(pin(INSTALLED, "57A78D066D6B7465572FB5F61AA0644AC6D247308C00E4AD1A7E07F59A4AB5C4"))
    sample = Path(baseline["save_root"]) / args.slot / "sav.dat"
    if args.tower_control:
        expected = TOWER_CONTROL_SHA
    else:
        expected = SAVE_SHA if args.slot == BASE_SLOT else sha(sample)
    pin(sample, expected)
    for group in ("core_files", "companion_files", "required_files"):
        for file in baseline[group]:
            pin(Path(baseline["game_root"]) / file["path"], file["sha256"])
    targets, journals, paths_for_quest = select_waits()
    control = read(pin(CONTROL, "280B48DACAD17B269F649C49CCEF505E4CD5F2655A128E94CB6672A6F53A9367"))
    controls, _ = bind_waits(control, targets)
    checks = {(row["node"], row["child"], row["remaining_seconds"]) for row in controls
              if row["quest"] == "07_nc_underground" and row["phase_address"] == [0, 2, 82, 5, 50, 77]}
    if checks != {(8, 0, 41162), (9, 2, 37562)}:
        raise ValueError("Direct and logical child control failed")
    reader = make_reader(out)
    write(out / "selection.json", dict(phase_hashes=sorted({key[0] for key in targets}
                                                            | {phase_hash(addr) for addr in paths_for_quest}),
                                       journal_hashes=sorted(set(journals.values()) | {journal_hash(WAIT_OBJECTIVE)}),
                                       slots=[args.slot], tower_control=args.tower_control,
                                       fact_names=["q101_enable_side_content", "mq049_started", "mq049_done",
                                                   "mq049_finished", "mq049_falco_done", "mq049_jacket_looted"]))
    result = subprocess.run(["pwsh", "-NoProfile", "-File", str(reader), "-Directory", str(out)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    (out / "reader.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    result.check_returncode()
    projection = out / f"{args.slot}.json"
    raw = read(projection)
    if raw.get("sha256") != expected or raw.get("decision") != "read_for_binding":
        raise ValueError(f"Unqualified projection: {raw.get('decision')}, {raw.get('binding_error')}")
    pin(sample, expected)
    matches, count = bind_waits(raw, targets)
    leads = [row for rows in targets.values() for row in rows.values()
             if row["quest"] == CANDIDATE and row["node"] == 28]
    report = {
        "status": "READ_ONLY_SAVED_WAIT_PROJECTION",
        "save": args.slot, "save_sha256": expected, "save_version": raw["version"], "tower_control": args.tower_control,
        "projection_sha256": sha(projection), "fact_projection": raw["facts"],
        "direct_and_child_control": sorted(checks), "matched_native_timers": count, "matches": matches,
        "falco_source_lead": leads, "falco_stage": falco_stage(raw, matches, journals[CANDIDATE], paths_for_quest),
    }
    write(out / "assessment.json", report)
    print(f"{args.slot}: {count} bound native timers. Positive direct and child control passed.")
    print(json.dumps({"facts": raw["facts"], "matches": matches, "falco": report["falco_stage"]}, indent=2))


if __name__ == "__main__":
    main()
