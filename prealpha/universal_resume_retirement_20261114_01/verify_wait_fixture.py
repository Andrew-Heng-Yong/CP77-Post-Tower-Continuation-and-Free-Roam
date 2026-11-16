"""Qualify the saved Where Eagles Dare timer as an offline fixture."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import sys


HERE = Path(__file__).resolve().parent
RESUME = HERE.parent / "universal_resume_20261114_01"
REGISTRY = HERE.parent / "quest_resume_registry_20261112_01"
INSTALLED = HERE.parent / "resume_dispatcher_rd10_kirk_20261113_01"
sys.path.insert(0, str(RESUME))
from read_handlers import Source, phase_hash
from read_timers import component, framed, game_records
from inspect_native import Image


QUEST = "mq058_semimaru_crystalcoat"
STOCK = r"base\quest\minor_quests\mq058\phases\mq058_quest_resolution.questphase"
PRIVATE = "towercontinued\\sidejobs_s29\\native\\" + STOCK
ADDRESS = (0, 2, 82, 4, 9, 3, 98, 103)
NODE = 80


def sha(path):
    with path.open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest().upper()


def pinned(path, digest):
    assert sha(path) == digest, path
    return path


def read_pinned(path, digest):
    return json.loads(pinned(path, digest).read_bytes())


def original_wait():
    owners = read_pinned(RESUME / "evidence_02/assessment.json",
                         "5A3A48EFF64B82B2EAEBE69ED15BB65A44109CAF638E4A4DA0E294329CD1968D")
    timers = read_pinned(RESUME / "evidence_04/timers.json",
                         "305FD3544FD009F91E90CB2F911130C3B09CC83EAC2C8D5F74E661F389F528FA")
    original = owners["fixtures"]["ManualSave-26"]
    assert original["save_sha256"] == timers["source_sha256"] and timers["save_version"] == 277
    assert timers["save_writes"] == 0

    registrations = {}
    for name, saved in owners["fixtures"].items():
        rows = [row for row in saved["delay_handlers"] if row["depot"] == STOCK and row["node"] == NODE]
        assert all(tuple(row["address"]) == ADDRESS and row["graph"] == "root" and
                   row["registration_type"] == "questGameTimeDelay_ConditionType" for row in rows)
        registrations[name] = len(rows)
    assert registrations["ManualSave-26"] == registrations["AutoSave-10"] == 1
    assert all(count == 0 for name, count in registrations.items() if name not in ("ManualSave-26", "AutoSave-10"))

    parts = timers["components"]
    instance = parts["instances"]
    framed_map = framed(component(instance), instance["id"], 16)
    pairs = list(struct.iter_unpack("<QQ", framed_map))
    by_node = dict(pairs)
    assert len(by_node) == len(pairs)
    node = (phase_hash(ADDRESS) << 32) | NODE
    timer_id = by_node[node]
    time = component(parts["time_core"])
    assert len(time) == 24
    clock, = struct.unpack_from("<I", time, 8)
    deadline, scheduled = game_records(component(parts["time_timers"])[4:])[timer_id]
    seconds = deadline - clock
    assert node == 0xCCF9887E00000050 and 0 < seconds < scheduled
    assert (seconds, scheduled) == (171141, 172800)
    return {"address": ADDRESS, "node": NODE, "node_key": f"{node:016X}",
            "game_timer_id": timer_id, "game_seconds_at_save": clock, "deadline": deadline,
            "remaining_game_seconds": seconds, "authored_game_seconds": scheduled,
            "fixture_save_sha256": original["save_sha256"], "registrations_by_fixture": registrations}


def check_graph(seconds):
    manifest = read_pinned(INSTALLED / "deployment_01/installed_manifest_01.json",
                           "AB279745469DEE08EC9A816EE9F04C9F9750456DE26A9C6CC8940E15FAFE56D8")
    archive = Path(manifest["game_root"]) / "archive/pc/mod/zzzz_PTFR_Combined.archive"
    pinned(archive, manifest["archive_sha256"])
    readback = read_pinned(INSTALLED / "archive_01/readback.json",
                           "5BBD9BB8F04AA5CC235B9845BDE691E2D6105B70E98083B36D7A8F54A3B29B81")
    assert readback["archive_sha256"] == manifest["archive_sha256"]
    members = {row["depot"]: row["sha256"] for row in readback["members"]}
    db_file = pinned(REGISTRY / "registry_02/registry.sqlite3",
                     "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9")
    with closing(sqlite3.connect(db_file.as_uri() + "?mode=ro", uri=True)) as db:
        title, selection = db.execute("SELECT title, selection FROM quests WHERE id=?", (QUEST,)).fetchone()
        assert title == "Where Eagles Dare" and selection == "INCLUDE"
        source = Source(db, members, [])
        stock = source.provider(STOCK)
        private = source.provider(PRIVATE)
        assert stock is not None and private is not None and source.scope(ADDRESS) == (stock, "root")
        graphs = {}
        for depot, resource in ((STOCK, stock), (PRIVATE, private)):
            binary, export, export_hash = db.execute(
                "SELECT sha256, export_path, export_sha256 FROM resources WHERE rid=?", (resource,)).fetchone()
            exported = read_pinned(Path(export), export_hash)
            definition, = (handle["Data"] for handle in exported["Data"]["RootChunk"]["graph"]["Data"]["nodes"]
                           if handle.get("Data", {}).get("id") == NODE)
            assert definition["$type"] == "questPauseConditionNodeDefinition"
            duration = definition["condition"]["Data"]["type"]["Data"]
            assert duration["$type"] == "questGameTimeDelay_ConditionType"
            assert (duration["days"], duration["hours"], duration["minutes"], duration["seconds"]) == (2, 0, 0, 0)
            assert duration["days"] * 86400 == seconds
            edges = db.execute("SELECT source,source_socket,destination,destination_socket FROM edges "
                               "WHERE rid=? AND graph='root' AND (source=? OR destination=?) ORDER BY source",
                               (resource, NODE, NODE)).fetchall()
            assert edges == [(80, "Out", 201, "Inactive"), (188, "Out2", 80, "In"),
                             (190, "CutSource", 80, "CutDestination")]
            group = source.authored_node(resource, "root", 201)["type"]["path"]
            assert group["className"]["$value"] == "gameJournalPhoneChoiceGroup"
            assert group["realPath"] == "contacts/marianne/mq058_02_resolution/01a_v"
            graphs[depot] = {"source_sha256": binary, "export_sha256": export_hash,
                             "timer_edges": edges, "expiry_choice_group": group["realPath"]}
    installed_hash = sha(archive)
    assert installed_hash == manifest["archive_sha256"]
    return {"quest": QUEST, "title": title, "provider_evidence": graphs, "installed_archive_sha256": installed_hash}


def check_engine():
    engine = Image()
    expected = {
        0x193C74: {0x193CAB: "mov r15, qword ptr [rbx + 0xe8]",
                   0x193CD3: "mov rdi, qword ptr [rax + 0x268]",
                   0x193D6B: "mov rdi, qword ptr [rax + 0x240]",
                   0x193DAB: "mov r8d, dword ptr [rsi + 0x44]",
                   0x193DF0: "mov dword ptr [rsi + 0x40], eax",
                   0x193E06: "call qword ptr [rax + 0x2b8]",
                   0x193E16: "call 0x14088b6ac"},
        0x1934AC: {0x1934EF: "call qword ptr [rax + 0x2c0]", 0x193502: "call qword ptr [rax + 0x250]"},
    }
    for function, instructions in expected.items():
        decoded = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}'
                   for row in engine.disasm(function)["instructions"]}
        for address, text in instructions.items():
            assert decoded.get(address) == text, (hex(address), text)
    return {"engine_sha256": engine.sha, "game_time_instruction_checks": expected}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    output = HERE / f"wait_fixture_{args.attempt:02}"
    wait = original_wait()
    result = {
        "status": "OFFLINE_RESTORED_QUEST_GAME_TIME_FIXTURE",
        "sample": wait,
        "graph": check_graph(wait["authored_game_seconds"]),
        "native": check_engine(),
        "gameplay_resume_verified": False,
    }
    output.mkdir(exist_ok=False)
    (output / "assessment.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f'Where Eagles Dare: {wait["remaining_game_seconds"]} of {wait["authored_game_seconds"]} game seconds remain.')


if __name__ == "__main__":
    main()
