"""Read existing saves and look for a selected unfinished quest with a bound timer."""

import argparse
from collections import defaultdict
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
RESUME = PREALPHA / "universal_resume_20261114_01"
CONTRACTS = PREALPHA / "quest_resume_contracts_rc2_20261114_01"
REGISTRY = PREALPHA / "quest_resume_registry_20261112_01/registry_02/registry.sqlite3"
sys.path.insert(0, str(RESUME))
from read_timers import GAME_DELAY, REAL_DELAY, component, game_records, real_records
from read_handlers import ROOTS, framed, paths, phase_hash, pin, read, sha, token, write

sys.path.insert(0, str(CONTRACTS))
from bind_saved_state import journal_hash


def select_targets():
    contract_data = read(pin(CONTRACTS / "analysis_07/contracts.json",
                             "02A19F25EC7478DEB667F308FF876428D78D8E91DC6ADB9732ED5B2E060FC31F"))
    owner_data = read(pin(CONTRACTS / "analysis_05/owner_map.json",
                          "B64B9010580CFFE9B5B642EAC8ACB17FFCF437DC16A6B84CCCBD8C7234F9907E"))
    pin(REGISTRY, "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9")
    scopes = owner_data["scopes"]
    with closing(sqlite3.connect(REGISTRY.as_uri() + "?mode=ro", uri=True)) as db:
        quest_roots = dict(db.execute("SELECT id, journal_root FROM quests"))
        stock = {row[0] for row in db.execute("SELECT rid FROM resources WHERE role='STOCK'")}
        delays = defaultdict(list)
        for rid, graph, node, raw in db.execute(
            "SELECT rid, graph, id, parameters_json FROM nodes WHERE type='questPauseConditionNodeDefinition' "
            "AND (parameters_json LIKE '%questGameTimeDelay_ConditionType%' "
            "OR parameters_json LIKE '%questRealtimeDelay_ConditionType%')"
        ):
            condition = json.loads(raw).get("condition") or {}
            value = condition.get("type") or {}
            if not isinstance(value, dict):
                continue
            kind = value.get("$type")
            if kind in {GAME_DELAY, REAL_DELAY} and rid in stock:
                seconds = sum(value.get(name, 0) * factor for name, factor in (
                    ("days", 86400), ("hours", 3600), ("minutes", 60), ("seconds", 1), ("miliseconds", 0.001)
                ))
                if seconds > 0:
                    delays[rid, graph].append((node, kind, seconds))

    keyed = defaultdict(dict)
    for quest in contract_data["quests"]:
        root = quest_roots.get(quest["id"])
        if quest["whole_quest_exception"] or not root:
            continue
        for scope_id in quest["scope_selectors"]["body_scope_ids"]:
            scope = scopes[scope_id]
            address = scope["address"]
            if not address or scope["kind"] != "quest":
                continue
            for node, kind, authored in delays[scope["rid"], scope["graph"]]:
                key = (phase_hash(address), node, token(kind))
                ident = (quest["id"], tuple(address), scope["sha256"], scope["graph"])
                keyed[key][ident] = {"name": quest["title"], "quest": quest["id"],
                                    "journal_hash": journal_hash(root), "scoped_exception": quest["scoped_exception"],
                                    "phase_address": address, "node": node, "clock": kind,
                                    "authored_seconds": authored, "depot": scope["depot"],
                                    "provider_sha256": scope["sha256"], "graph": scope["graph"]}
    return {key: list(options.values()) for key, options in keyed.items()}


def match_waits(raw, targets):
    if not raw.get("components"):
        return []
    parts = raw["components"]
    root_data = bytes.fromhex(raw["root_array"])
    if root_data != bytes([len(ROOTS)]) + struct.pack("<QQ", *(token(name) for name in ROOTS)):
        raise ValueError("Saved resource roots differ")
    addresses = defaultdict(set)
    for address in paths(component(parts["paths"]), parts["paths"]["id"]):
        if address and address[0] < len(ROOTS):
            addresses[phase_hash(address)].add(address)
    instances = list(struct.iter_unpack("<QQ", framed(component(parts["instances"]), parts["instances"]["id"], 16)))
    node_values = dict(instances)
    if len(instances) != len(node_values):
        raise ValueError("Duplicate node-instance keys")

    game, real, clock = {}, {}, None
    clock_limits = {}
    try:
        time_core = component(parts["time_core"])
        if len(time_core) != 24:
            raise ValueError("Unexpected time-system core size")
        clock, = struct.unpack_from("<I", time_core, 8)
        game = game_records(component(parts["time_timers"])[4:])
    except (KeyError, ValueError, struct.error) as error:
        clock_limits["game"] = str(error)
    try:
        real = real_records(component(parts["delay_structs"])[4:])
    except (KeyError, ValueError, struct.error) as error:
        clock_limits["real"] = str(error)
    raw["clock_limits"] = clock_limits
    journal = {key: states for key, states in raw["journal"]}
    matches = []
    for slot, code, phase, node in raw["timed_registrations"]:
        candidates = targets.get((phase, node, int(code, 16)), [])
        if len(candidates) != 1:
            continue
        source, = candidates
        if addresses[phase] != {tuple(source["phase_address"])}:
            continue
        record = dict(source, physical_slot=slot, timer_id=None, remaining_seconds=None)
        record["journal_states"] = journal.get(source["journal_hash"], [])
        timer = node_values.get(phase << 32 | node)
        if source["clock"] == GAME_DELAY and timer in game:
            deadline, duration = game[timer]
            remaining = deadline - clock
            if 0 < remaining <= duration == source["authored_seconds"]:
                record.update(timer_id=f"{timer:016X}", remaining_seconds=remaining)
        elif source["clock"] == REAL_DELAY and timer in real:
            if 0 < real[timer] <= source["authored_seconds"]:
                record.update(timer_id=f"{timer:016X}", remaining_seconds=real[timer])
        matches.append(record)
    return matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100), metavar="1–99")
    parser.add_argument("--slots", nargs="*")
    parser.add_argument("--reuse", nargs="*", type=int, choices=range(1, 100), default=[])
    args = parser.parse_args()
    out = HERE / f"run_saves_{args.attempt:02}"
    out.mkdir()
    targets = select_targets()
    spec = {"phase_hashes": sorted({phase for phase, _, _ in targets}),
            "journal_hashes": sorted({row["journal_hash"] for rows in targets.values() for row in rows}),
            "slots": args.slots or []}
    write(out / "selection.json", spec)
    job = subprocess.run(["pwsh", "-NoProfile", "-File", str(HERE / "ReadTimerFixtures.ps1"), "-Directory", str(out)],
                         cwd=HERE, text=True, encoding="utf-8", capture_output=True, timeout=400)
    (out / "reader.log").write_text(job.stdout + job.stderr, encoding="utf-8")
    job.check_returncode()
    prior = {}
    for attempt in args.reuse:
        folder = HERE / f"run_saves_{attempt:02}"
        if folder == out:
            raise ValueError("Can only reuse an earlier capture")
        before = read(folder / "selection.json")
        if any(before[key] != spec[key] for key in ("phase_hashes", "journal_hashes")):
            raise ValueError(f"Previous capture used different targets: {folder}")
        prior.update({path.name: path for path in folder.glob("*Save-*.json")})
    prior.update({path.name: path for path in out.glob("*Save-*.json")})
    saves = []
    for path in sorted(prior.values(), key=lambda item: item.name):
        raw = read(path)
        try:
            matches = match_waits(raw, targets)
        except (ValueError, struct.error) as error:
            raw["binding_error"] = str(error)
            matches = []
        row = {key: raw[key] for key in ("slot", "sha256", "version", "decision", "facts", "clock_limits",
                                        "binding_error") if key in raw}
        row["registered_waits"] = matches
        row["capture_sha256"] = sha(path)
        saves.append(row)
        print(row["slot"], row.get("decision", ""), [
            (m["name"], m["node"], m["journal_states"], m["remaining_seconds"]) for m in matches
        ])
    if not saves:
        raise RuntimeError("No save projections were read")
    write(out / "fixture_assessment.json", {
        "status": "READ_ONLY_SAVED_WAIT_SEARCH", "registry_sha256": sha(REGISTRY), "candidate_keys": len(targets),
        "inputs": saves, "runtime_admission": 0, "save_writes": 0,
    })


if __name__ == "__main__":
    main()
