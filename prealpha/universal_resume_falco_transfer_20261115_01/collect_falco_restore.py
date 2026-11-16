"""Project the native owner stack, latches and queues from the two pinned saves."""

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
FIXTURE = HERE.parent / "universal_resume_first_live_wait_20261115_01"
sys.path.insert(0, str(FIXTURE))
from qualify_saved_wait import (INSTALLED, ORIGINAL, PRIVATE, REGISTRY, TOWER_CONTROL, TOWER_CONTROL_SHA,
                                WAIT_OBJECTIVE, component, framed, journal_hash, make_reader, paths,
                                phase_hash, pin, read, sha, token, write)
from bind_saved_state import fnv32

LIVE_SAVE = "ManualSave-31"
LIVE_SHA = "2E0F3C99AF3E98601CFC6363BBC068635D0C50ABB32F8E81B2A57B056B02F43D"
SOURCE = FIXTURE / "run_sources_01/source_assessment.json"
SAVED_WAIT = FIXTURE / "run_04/assessment.json"


def require(value, message):
    if not value:
        raise ValueError(message)


def native_queue(part):
    data = component(part)
    # signed VLQ prefix for a nonnegative resource-request count
    position = 4
    byte = data[position]
    require(not byte & 0x80, "Negative queued resource count")
    count, shift = byte & 0x3F, 6
    position += 1
    more = byte & 0x40
    while more:
        require(shift <= 27 and position < len(data), "Unsupported queued resource count")
        byte = data[position]
        count |= (byte & 0x7F) << shift
        more = byte & 0x80
        shift += 7
        position += 1
    end = position + count * 8
    require(end + 4 <= len(data), "Truncated resource requests")
    resources = [item for item, in struct.iter_unpack("<Q", data[position:end])]
    notifications, = struct.unpack_from("<I", data, end)
    require(len(data) == end + 4 + notifications * 4, "Unexpected native queue framing")
    slots = [slot for slot, in struct.iter_unpack("<I", data[end + 4:])]
    return {"resource_requests": resources, "notifications": slots}


def read_selected(slot, tower, out, addresses, latches):
    write(out / "selection.json", {
        "phase_hashes": sorted({phase_hash(addr) for addr in addresses}),
        "journal_hashes": [journal_hash(WAIT_OBJECTIVE), 692629639],
        "slots": [slot], "tower_control": tower, "fact_names": ["mq049_started", "mq049_falco_done"],
        "latches": {str(table): sorted(keys) for table, keys in latches.items()},
    })
    reader = make_reader(out)
    source = reader.read_text(encoding="utf-8")
    anchor = "        $Result.facts = $recorded\n"
    require(source.count(anchor) == 1, "Unexpected save reader facts anchor")
    source = source.replace(anchor, anchor + r"""        $Result.latches = [ordered]@{}
        foreach ($item in $selection.latches.PSObject.Properties) {
            $index = [int]$item.Name
            $wanted = [Collections.Generic.HashSet[uint32]]::new()
            foreach ($key in $item.Value) { [void]$wanted.Add([uint32]$key) }
            $stored = $facts.Children[$index - 1].Value
            if ($stored -isnot [WolvenKit.RED4.Save.FactsTable]) { throw 'Unsupported latch store' }
            $Result.latches[$item.Name] = @(foreach ($entry in $stored.FactEntries) {
                $key = [uint32]$toHash.Invoke($null, [object[]]@($entry.FactName))
                if ($wanted.Contains($key)) { ,@($key, [uint32]$entry.Value) }
            })
        }
""")
    anchor = "            paths = $paths\n"
    require(source.count(anchor) == 1, "Unexpected save reader components anchor")
    reader.write_text(source.replace(anchor, anchor + "            queue = Single $root.Children 'QueuedData'\n"),
                      encoding="utf-8")
    result = subprocess.run(["pwsh", "-NoProfile", "-File", str(reader), "-Directory", str(out)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
    (out / "reader.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    result.check_returncode()
    raw = read(out / f"{slot}.json")
    require(raw.get("decision") == "read_for_binding", f"Save projection deferred: {raw.get('binding_error')}")
    return raw


def review(raw, addresses, latch_plan):
    queue = native_queue(raw["components"]["queue"])
    part = raw["components"]["paths"]
    decoded = defaultdict(set)
    for path in paths(component(part), part["id"]):
        if path:
            decoded[phase_hash(path)].add(path)
    selected = {}
    for path in addresses:
        hash_value = phase_hash(path)
        resolved = decoded[hash_value]
        require(not resolved or resolved == {path}, f"Path hash conflict {path}")
        if resolved:
            selected[hash_value] = path
    watched_paths = sorted(path for matches in decoded.values() for path in matches
                           if path[:len(ORIGINAL)] == ORIGINAL or path[:len(PRIVATE)] == PRIVATE)
    require(all(path in addresses for path in watched_paths), "Unreviewed saved body path")
    entries = defaultdict(list)
    for slot, kind, phase, node in raw["phase_registrations"]:
        if phase in selected:
            entries[selected[phase]].append({"slot": slot, "node": node, "type": kind})
    part = raw["components"]["instances"]
    values = []
    for key, value in struct.iter_unpack("<QQ", framed(component(part), part["id"], 16)):
        if key >> 32 in selected:
            values.append({"key": f"{key:016X}", "value": f"{value:016X}"})
    latches = []
    for table, rows in raw["latches"].items():
        require(len(rows) == len(dict(rows)), f"Duplicate entries in native store {table}")
        for key, value in rows:
            latches.append(dict(latch_plan[int(table), key], key=key, value=value, table=int(table)))
    return entries, values, latches, queue, watched_paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100))
    parser.add_argument("--tower-control", action="store_true")
    args = parser.parse_args()
    slot, save_sha = (TOWER_CONTROL, TOWER_CONTROL_SHA) if args.tower_control else (LIVE_SAVE, LIVE_SHA)
    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()
    pin(FIXTURE / "qualify_saved_wait.py", "CF3F74FCD08ECD6BDAC28FD13DC51B9A9632B3D4BB27CD5E0F8D5D0F81B6D12D")
    wait = read(pin(SAVED_WAIT, "FEAA8527FA62476056C3AC207613549985CEBA6D97D22C83D990A3FA6157CCB2"))
    source = read(pin(SOURCE, "5905BCE8AFCC83AFA58BA4868AD45B01E0999741BD50A64C31DE3631264DE009"))
    baseline = read(pin(INSTALLED, "57A78D066D6B7465572FB5F61AA0644AC6D247308C00E4AD1A7E07F59A4AB5C4"))
    pin(Path(baseline["game_root"]) / "bin/x64/Cyberpunk2077.exe",
        "D36E74C47592E9C656AE250078CB40B2BE63C782AF5BFBEFF2280D43E653FAB4")
    before = pin(Path(baseline["save_root"]) / slot / "sav.dat", save_sha)
    registry = pin(REGISTRY, "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9")
    ancestry = [tuple(address) for address in reversed(source["native_ancestry"])]
    siblings = [ORIGINAL + (11,), ORIGINAL + (12,)]
    prior_setup = ORIGINAL + (6,)
    addresses = [*ancestry, siblings[0], prior_setup, PRIVATE, PRIVATE + (11,), PRIVATE + (12,)]
    latch_keys = {4: [], 5: []}
    latch_plan = {}
    with closing(sqlite3.connect(registry.as_uri() + "?mode=ro", uri=True)) as db:
        for path, resource in zip([ORIGINAL, *siblings], [7568, 5822, 7070], strict=True):
            for node, kind, sockets in db.execute(
                "SELECT id,type,sockets_json FROM nodes WHERE rid=? AND graph='root' "
                "AND type IN ('questLogicalAndNodeDefinition','questLogicalXorNodeDefinition')", (resource,)
            ):
                table = 4 if kind == "questLogicalAndNodeDefinition" else 5
                key = fnv32(struct.pack("<II", node, phase_hash(path)))
                require((table, key) not in latch_plan, "Logical latch key collision")
                latch_keys[table].append(key)
                latch_plan[table, key] = {
                    "phase": path, "node": node, "kind": kind,
                    "inputs": [sock["name"] for sock in json.loads(sockets) if sock["type"] == "Input"],
                }
    raw = read_selected(slot, args.tower_control, out, addresses, latch_keys)
    require(raw["sha256"] == save_sha, "Save differs between input and projection")
    pin(before, save_sha)
    entries, values, latches, queue, watched_paths = review(raw, addresses, latch_plan)
    require(not entries[prior_setup], "Another original quest branch still has active registrations")
    body = {path: entries[path] for path in [ORIGINAL, *siblings]}
    if not args.tower_control:
        require(all(body[tuple(row["address"])] == row["handlers"] for row in wait["falco_stage"]["registrations"]),
                "The five pinned original body registrations differ")
        require(all(not entries[path] for path in (PRIVATE, PRIVATE + (11,), PRIVATE + (12,))),
                "Competing private owner")
    parents = []
    for path, child in zip(ancestry, ancestry[1:]):
        found = [row for row in entries[path] if row["node"] == child[-1]]
        if found:
            require(len(found) == 1 and int(found[0]["type"], 16) == token("questPhaseNodeDefinition"),
                    f"Unexpected ancestor handler {path}")
        parents.append({"phase": path, "child_node": child[-1], "registrations": found})
    body_slots = {row["slot"] for rows in body.values() for row in rows}
    result = {
        "status": "READ_ONLY_RESTORE_SELECTION", "slot": slot, "save_sha256": save_sha,
        "tower_control": args.tower_control, "parents": parents,
        "body": [{"phase": path, "registrations": rows} for path, rows in body.items()],
        "saved_body_paths": watched_paths,
        "additional_original_path": {"phase": prior_setup, "registrations": entries[prior_setup]},
        "node_instances": values, "logical_latches": latches, "queue": queue,
        "notifications_for_selected_body": [slot for slot in queue["notifications"] if slot in body_slots],
    }
    write(out / "selection_assessment.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
