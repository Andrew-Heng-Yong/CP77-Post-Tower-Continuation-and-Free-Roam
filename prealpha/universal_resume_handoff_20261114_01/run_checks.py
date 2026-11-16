"""Copy bounded executable slices for a stand-alone synthetic scheduler fixture."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image
sys.path.insert(0, str(HERE.parent / "universal_resume_20261114_01"))
from read_handlers import Source, phase_hash

# Preserve each RVA so the native relative calls go to the listed slices.
FUNCTIONS = {
    "remaining": 0x111894C,
    "remove": 0x1AA7D0,
    "insert": 0x1AA8B8,
    "erase": 0x1AA3A8,
    "insert_before": 0x1AA2D0,
    "append": 0xEE2CA0,
    "append_from_insert": 0x242F7D8,
    "insert_at_capacity": 0x242F96C,
    "move_reference": 0x195734,
    "release": 0x195798,
    "dispatch_due": 0x1AA634,
    "alternate_clock": 0x242F952,
    "append_expired": 0x189AF8,
    "release_expired_vector": 0x189B90,
    "invoke_callback": 0x1AAB6C,
    "callback_thunk": 0x1AAB88,
    "queue_notification": 0x88BC58,
    "remove_notification": 0x2FD1BC,
    "find_queued_slot": 0x2FCD04,
    "erase_queued_slot": 0x50CC28,
    "append_queued_slot": 0x1E07BC,
    "lock_notification_queue": 0x1FFAD60,
    "acquire_spinlock": 0x22CA300,
    "retire_event_slot": 0x2FCFD0,
    "drain_quest_notifications": 0x3534DC,
    "construct_saved_delay": 0x1133EEC,
    "attach_saved_delay": 0x193A1C,
    "find_attach_delay": 0x217A590,
    "pin_attach_delay": 0x193694,
    "release_attach_reference": 0x19DCD4,
    "move_attach_callback": 0x1AAAC8,
    "assign_attach_callback": 0x193B54,
    "destroy_attach_callback": 0x1AAB14,
    "read_node_mapping": 0x194AC4,
    "insert_node_mapping": 0x194718,
    "remove_node_mapping": 0x194C24,
    "erase_node_mapping": 0x194C78,
    "find_node_mapping": 0x194B84,
    "end_node_mapping": 0x194B4C,
    "ensure_node_mapping_order": 0x2CD31CC,
    "insert_node_mapping_at": 0x1947B0,
    "append_node_mapping": 0x99F710,
    "lock_node_mapping_for_read": 0x1FFADA0,
    "acquire_read_spinlock": 0x22CA420,
    "collect_saved_real_delays": 0x2AAC3D4,
    "append_saved_delay": 0x961264,
    "initialize_real_delay_handler": 0x1948BC,
    "initialize_handler_state": 0x88BB20,
    "construct_delay_tag": 0x194A1C,
    "unpack_saved_id": 0x2C7EEC8,
    "unpack_saved_id_words": 0x274E8C0,
}
BOUNDS = {"decode_group": (0x1AA970, 0x1AA98A), "move_slot": (0x1957E0, 0x195823),
          "default_time": (0x37BA5C4, 0x37BA5C8), "zero_time": (0x37B9734, 0x37B9738),
          "quest_callback": (0x1304ED8, 0x1304EE3), "mark_ready": (0x88B6AC, 0x88B6EF),
          "notify_parent_slot": (0x88BB74, 0x88BB93), "event_manager_forward": (0x88BC48, 0x88BC56),
          "resolve_active_slot": (0x35371C, 0x35373D), "read_slot": (0x353708, 0x35371B),
          "contains_retired_slot": (0x214E48, 0x214E6A), "read_queue_index": (0x1EEC3C, 0x1EEC46),
          "unlock_quest_graph": (0x19417F0, 0x19417F8),
          "attach_predicate": (0x12FD7EC, 0x12FD7F8),
          "destroy_predicate_dispatch": (0x2004BA0, 0x2004BAE),
          "clone_saved_callback": (0x153D590, 0x153D5A6),
          "destroy_saved_callback": (0x258480, 0x258489),
          "saved_delay_type": (0x7B2AD0, 0x7B2AD3),
          "lower_bound_node_mapping": (0x194D34, 0x194D7B),
          "unlock_node_mapping_for_read": (0x1FFADC0, 0x1FFADCD),
          "copy_saved_id_words": (0x2749654, 0x2749662),
          "real_delay_resume_admission": (0x664F00, 0x664F03)}


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def read_owner(fixture):
    registry = HERE.parent / "quest_resume_registry_20261112_01/registry_02/registry.sqlite3"
    qualified = HERE.parent / "universal_resume_20261114_01/evidence_02/assessment.json"
    capture = qualified.read_bytes()
    assert digest(capture) == "5A3A48EFF64B82B2EAEBE69ED15BB65A44109CAF638E4A4DA0E294329CD1968D"
    path = tuple(fixture["address"])
    node = fixture["node"]
    assert f"{(phase_hash(path) << 32) | node:016X}" == fixture["node_key"]
    assert path[:3] == (0, 2, 82)
    assert fixture["graph"] == "root/9/2/63/2"
    depot = fixture["depot"]
    fixtures = json.loads(capture)["fixtures"]
    counts = {slot: sum(row["depot"] == depot for row in saved["delay_handlers"])
              for slot, saved in fixtures.items()}
    assert counts.pop("ManualSave-26") == 2 and all(count == 0 for count in counts.values())

    # Compare the two provider hashes recorded in the registry. The saved
    # address comparisons are independently pinned above.
    with closing(sqlite3.connect(registry.as_uri() + "?mode=ro", uri=True)) as db:
        source = Source(db, {}, [])
        phase = r"base\quest\cyberpunk2077.questphase"
        root = source.provider(phase)
        kabuki = source.provider(depot)
        assert root is not None and kabuki is not None
        assert source.scope(path) == (kabuki, fixture["graph"])
        checks = {
            root: "78D8AFD0784575216B090F003610CA973BE9D1781BAB948C9E4DC12006D750B2",
            kabuki: "DC7393185B973C640BD66A31231D4BB24B14706AE27683E17AD7C8E010067527",
        }
        for rid, sha256 in checks.items():
            assert db.execute("SELECT sha256 FROM resources WHERE rid = ?", (rid,)).fetchone() == (sha256,)
        condition = source.authored_node(root, "root", 106)["condition"]["type"]
        assert condition["path"]["realPath"] == "ep1/quests/main_quest/q307_before_tomorrow"
        assert condition["state"] == "Succeeded"
        assert source.authored_node(root, "root", 109)["type"]["factName"] == "q307_main_game_killed"
        assert source.authored_node(root, "root", 107)["type"] == "Terminating"
        root_edges = db.execute("SELECT source, destination FROM edges WHERE rid=? AND graph='root' "
                                "AND source IN (106,109) ORDER BY source", (root,)).fetchall()
        assert root_edges == [(106, 109), (109, 107)]
        graph = fixture["graph"]
        delay = source.authored_node(kabuki, graph, node)["condition"]["type"]
        assert delay["$type"] == "questRealtimeDelay_ConditionType" and delay["seconds"] == 10
        prefab, = source.authored_node(kabuki, "root/9", 2)["phaseInstancePrefabs"]
        prefab_ref = prefab["prefabNodeRef"]["$value"]
        voiceset, = source.authored_node(kabuki, graph, 4)["type"]["params"]
        assert voiceset["puppetRef"]["reference"]["$value"].startswith(prefab_ref + "/")
        assert voiceset["puppetRef"]["names"][0]["$value"] == "civilian_dying"
        loop = db.execute("SELECT source, destination FROM edges WHERE rid=? AND graph=? "
                          "AND source IN (2,4,5,6) ORDER BY source", (kabuki, graph)).fetchall()
        assert loop == [(2, 5), (4, 6), (5, 4), (6, 2)]
        next_fixtures = review_quest_waits(source, fixtures)
    return ({"address": path, "node": node, "depot": depot, "graph": graph,
             "root_retirement_edges": root_edges, "prefab": prefab_ref, "voiceset_loop": loop,
             "later_saved_registrations": counts, "gameplay_admission": "OUTSIDE_RESTORED_QUESTS"}, next_fixtures)


def review_quest_waits(source, fixtures):
    db = source.db
    questions = [
        ("mq028_stalker", r"base\quest\minor_quests\mq028\mq028.questphase",
         "F6159E11E4489DC7454009F4FA9310143FC1398D363DBAC9F5EDAE453C471A37",
         "root/23", 36, [(0, 2, 82, 6, 41, 23)]),
        ("wst_ep1_05", r"ep1\openworld\world_stories\wst_ep1_05\wst_ep1_05.questphase",
         "E9A807F12205D7482C0B743763311529A0BA873AFAF37BDD03C4831B810E4CEA",
         "root", 69, [(1, 0, 10, 5, 14, 5), (1, 0, 10, 2, 3, 16, 5, 6, 14, 5)]),
    ]
    reviewed = []
    for quest, depot, provider, graph, node, addresses in questions:
        rid = source.provider(depot)
        assert db.execute("SELECT sha256 FROM resources WHERE rid = ?", (rid,)).fetchone() == (provider,)
        title, selection = db.execute("SELECT title, selection FROM quests WHERE id = ?", (quest,)).fetchone()
        assert selection == "INCLUDE"
        delay = source.authored_node(rid, graph, node)["condition"]["type"]
        assert delay["$type"] == "questRealtimeDelay_ConditionType" and delay["hours"] == 1
        keys = {}
        for path in addresses:
            assert source.scope(path) == (rid, graph)
            keys[f"{(phase_hash(path) << 32) | node:016X}"] = path
        hits = [slot for slot, saved in fixtures.items() if any(
            row["depot"] == depot and row["graph"] == graph and row["node"] == node
            for row in saved["delay_handlers"])]
        assert not hits
        reviewed.append({"title": title, "depot": depot, "provider_sha256": provider, "graph": graph,
                         "node": node, "authored_real_seconds": 3600, "logical_addresses": keys,
                         "saved_active_waits": hits, "status": "SOURCE_CANDIDATE"})
    ep1, graph = source.scope((1, 0, 10))
    cut = set(db.execute("SELECT destination FROM edges WHERE rid=? AND graph=? AND source=9 "
                         "AND destination_socket='CutDestination'", (ep1, graph)).fetchall())
    assert (5,) in cut and (2,) not in cut
    assert db.execute("SELECT source, destination FROM edges WHERE rid=? AND graph=? AND "
                      "((source=8 AND destination=9) OR (source=9 AND destination=10)) ORDER BY source",
                      (ep1, graph)).fetchall() == [(8, 9), (9, 10)]
    reviewed[1]["ep1_cut_parent_nodes"] = sorted(item[0] for item in cut)
    reviewed[1]["separate_bugfix_parent"] = 2
    return reviewed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=int, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    build = HERE / f"build_{args.build:02d}"
    out = HERE / f"evidence_{args.attempt:02d}"
    manifest = json.loads((build / "build.json").read_text())
    exe = build / "NativeDelayChecks.exe"
    for name, path in (("exe", exe), ("source", HERE / "NativeDelayChecks.cpp"),
                       ("header", HERE / "DelayHold.hpp"), ("handoff", HERE / "RealTimeHandoff.hpp"),
                       ("cutoff", HERE / "CutoffObservation.hpp"),
                       ("record", HERE.parent / "universal_resume_boundary_20261114_01/TimerRecord.hpp"),
                       ("probe", HERE / "CutoffProbe.cpp"), ("dll", build / "PTFR_QuestTimerProbe.dll")):
        assert digest(path.read_bytes()) == manifest[f"{name}_sha256"], name

    engine = Image()
    probe = (HERE / "CutoffProbe.cpp").read_text(encoding="utf-8")
    hooks = re.findall(r'MakeHook\((0x[0-9A-F]+), "([^"]+)", &(\w+),', probe)
    assert len(hooks) == 14
    hook_prefixes = {}
    for rva_text, escapes, name in hooks:
        rva = int(rva_text, 16)
        prefix = bytes.fromhex(escapes.replace("\\x", ""))
        offset = engine.off(rva)
        assert len(prefix) == 8 and engine.data[offset:offset + 8] == prefix, name
        hook_prefixes[name] = {"rva": hex(rva), "prefix": prefix.hex()}
    # A checksum on the full engine also pins these signatures, offsets and data.
    for address, fmt, expected in (
        (0x30A2A90 + 0x290, "<Q", engine.base + FUNCTIONS["remaining"]),
        (0x31267A0 + 0x10, "<Q", engine.base + 0x1948BC),
        (0x302B0A8 + 0xD8, "<Q", engine.base + FUNCTIONS["invoke_callback"]),
        (0x302B0A8 + 0xE0, "<Q", engine.base + BOUNDS["saved_delay_type"][0]),
        (0x3695E70 + 8, "<Q", engine.base + BOUNDS["clone_saved_callback"][0]),
        (0x3695E70 + 0x20, "<Q", engine.base + BOUNDS["destroy_saved_callback"][0]),
        (0x3950258, "<Q", engine.base + BOUNDS["attach_predicate"][0]),
        (0x3695E40 + 0x10, "<Q", engine.base + BOUNDS["quest_callback"][0]),
        (0x30BCE78 + 0x200, "<Q", engine.base + FUNCTIONS["queue_notification"]),
        (0x30BCE78 + 0x2B0, "<Q", engine.base + FUNCTIONS["remove_notification"]),
        (0x30BCE78 + 0x2B8, "<Q", engine.base + FUNCTIONS["insert_node_mapping"]),
        (0x30BCE78 + 0x2C0, "<Q", engine.base + FUNCTIONS["remove_node_mapping"]),
        (0x30BCE78 + 0x2C8, "<Q", engine.base + FUNCTIONS["read_node_mapping"]),
        (0x306F9A0 + 8, "<Q", engine.base + BOUNDS["event_manager_forward"][0]),
        (0x37B9734, "<f", 0.0),
        (0x37BA5C4, "<f", -1.0),
    ):
        assert struct.unpack_from(fmt, engine.data, engine.off(address))[0] == expected
    ranges = {}
    for name, rva in FUNCTIONS.items():
        begin, end, _ = engine.function(rva)
        assert begin == rva
        ranges[name] = (begin, end)
    ranges.update(BOUNDS)

    # Verify dequeue, graph admission and native callback ordering together.
    order = {0x353508: "lea rdx, [rcx + 0x150]", 0x353529: "mov rbx, qword ptr [rsi + 0x158]",
             0x353556: "cmp dword ptr [rax], edx", 0x35356C: "call 0x1401e07bc",
             0x353587: "and dword ptr [rsi + 0x164], 0", 0x353590: "xchg byte ptr [rax], cl",
             0x3535A0: "call 0x141ffad60", 0x3535CA: "lea rcx, [rsi + 0x168]",
             0x3535DB: "call 0x140214e48", 0x3535F2: "call 0x14035371c",
             0x353602: "call 0x140353708", 0x353690: "call qword ptr [rax + 0xe8]"}
    instructions = {int(row["rva"], 16): row for row in engine.disasm(FUNCTIONS["drain_quest_notifications"])["instructions"]}
    for address, expected in order.items():
        row = instructions[address]
        assert f'{row["mnemonic"]} {row["operands"]}' == expected, row
    quest_job = next(row for row in engine.disasm(0x4AD5CC)["instructions"] if row["rva"] == "0x4ad66b")
    assert quest_job["mnemonic"] == "call" and quest_job["operands"] == "0x1403534dc"
    handler_constructor = {int(row["rva"], 16): row for row in engine.disasm(0xE7111C)["instructions"]}
    for address, expected in {0xE71176: "mov qword ptr [rsi + 0x38], rdx",
                              0xE7117A: "and dword ptr [rsi + 0x40], 0",
                              0xE7118D: "mov dword ptr [rsi + 0x44], 0x80000000"}.items():
        row = handler_constructor[address]
        assert f'{row["mnemonic"]} {row["operands"]}' == expected, row
    binding_path = HERE.parent / "universal_resume_20261114_01/evidence_04/timer_binding.json"
    binding_bytes = binding_path.read_bytes()
    assert digest(binding_bytes) == "9BE96664F8F76BFF8E101A9EE76382AB505F336EC171F079F22059DF2E0DAA2C"
    binding = json.loads(binding_bytes)
    fixture, = (row for row in binding["direct_delay_bindings"] if row["node_key"] == "1361AA1A00000005")
    assert "0x" + fixture["node_key"] in probe
    owner, next_fixtures = read_owner(fixture)
    serial, group = struct.unpack(">II", bytes.fromhex(fixture["timer_id"]))
    fixture_id = (group << 32) | serial
    fixture_seconds = fixture["remaining_real_seconds"]
    packet = bytearray(struct.pack("<IQf", len(ranges), fixture_id, fixture_seconds))
    sources = {}
    for name, (begin, end) in ranges.items():
        data = engine.data[engine.off(begin):engine.off(begin) + end - begin]
        packet.extend(struct.pack("<II", begin, len(data)))
        packet.extend(data)
        sources[name] = {"rva": hex(begin), "length": len(data), "sha256": digest(data)}

    out.mkdir(exist_ok=False)
    slices = out / "engine_slices.bin"
    slices.write_bytes(packet)
    result = subprocess.run([str(exe), str(slices)], cwd=out, capture_output=True, text=True, timeout=10)
    (out / "fixture_checks.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    print(result.stdout, end="")
    if result.returncode:
        raise SystemExit(f"Fixture process exited with {result.returncode}. See {out}")
    checks, = (line for line in result.stdout.splitlines() if line.endswith("passed, 0 failed"))
    assert checks == "60 passed, 0 failed", checks
    assessment = {
        "status": "ISOLATED_NATIVE_SCHEDULER_FIXTURES_PASSED",
        "engine_sha256": engine.sha,
        "hook_prefixes": hook_prefixes,
        "slices": sources,
        "build": manifest,
        "fixture_id": f"{fixture_id:016X}",
        "fixture_seconds": fixture_seconds,
        "fixture_owner": owner,
        "restored_quest_wait_candidates": next_fixtures,
        "check_count": int(checks.split()[0]),
        "quest_drain_order": [instructions[address] for address in order],
        "quest_tick_drain_call": quest_job,
        "game_launches": 0,
        "game_writes": 0,
        "save_writes": 0,
        "game_runtime_exercised": False,
    }
    (out / "assessment.json").write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
