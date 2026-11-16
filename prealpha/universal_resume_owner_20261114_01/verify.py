"""Bind the phase observer to current providers and retained save projections."""

import argparse
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
sys.path.insert(0, str(PREALPHA / "universal_resume_20261114_01"))
from read_handlers import INPUTS, REGISTRY, RD10, Source, phase_hash, pin, read, saved_components, sha, token, walk, write
from model import load_export, normalize

sys.path.insert(0, str(PREALPHA / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image

STORY = r"ep1\openworld\world_stories\wst_ep1_05\wst_ep1_05.questphase"
SSC = r"towercontinued\sidejobs_s23\ep1\hasan_boot.questphase"
DIALOG = r"ep1\quest\tertiary_characters\default_dialogs\hasan_default\sts_04_hasan_default.questphase"
CORE_ARCHIVE = "archive/pc/mod/zzzz_PTFR_Combined.archive"
CORE_XL = CORE_ARCHIVE + ".xl"
S23_SCRIPT = "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds"
SUSPENDED = PREALPHA / "universal_resume_handoff_20261114_01"
MANIFEST = RD10 / "deployment_01/installed_manifest_01.json"
STOCK_ROOT = r"ep1\quest\ep1.quest"
PROVIDER_SCAN = "providers_01.json"


def watch_table():
    code = (HERE / "OwnerTrace.hpp").read_text()
    arrays = {name: tuple(map(int, content.split(","))) for name, content in
              re.findall(r"\b(Hasan\w+)\{([0-9, ]+)\};", code)}
    watches = {label: arrays[name] for label, name in re.findall(r'\{"([a-z0-9-]+)", (Hasan\w+)(?:, true)?\}', code)}
    assert len(watches) == len(arrays) == len({phase_hash(path) for path in watches.values()}) == 10
    return watches


def baseline():
    manifest = read(pin(MANIFEST, INPUTS[MANIFEST]))
    game = Path(manifest["game_root"])
    members_path = RD10 / "archive_01/readback.json"
    archive = read(pin(members_path, INPUTS[members_path]))
    expected = {row["path"]: row["sha256"] for row in manifest["core_files"]}
    for key in (CORE_ARCHIVE, CORE_XL, S23_SCRIPT):
        pin(game / key, expected[key])
    assert expected[CORE_ARCHIVE] == archive["archive_sha256"]
    xl_body = (game / CORE_XL).read_text(encoding="utf-8-sig")
    hasan = re.search(rf"(?m)^    - path: {re.escape(SSC)}\s*\n\s+parent: {re.escape(STOCK_ROOT)}\s*\n"
                      r"\s+input:\s*\n\s+node: \[1\]\s*\n\s+socket: Out\s*$", xl_body)
    assert hasan and xl_body.count(SSC) == 1
    script = (game / S23_SCRIPT).read_text()
    assert 'if i == 19 { return "PTFRS23_HASAN"; }' in script
    for variant in ("A", "B"):
        assert f"func States{variant}19() -> array<Int32> {{ return [1, 1, 1, 1, 1, 1, 1]; }}" in script
    assert 'if this.Own(i, "Issued") == 0' in script and 'this.Fact("q307_ep1_killed") == 1' in script
    bindings = [{"path": SSC, "parent": STOCK_ROOT, "input": {"node": [1], "socket": "Out"}}]
    return game, {row["depot"].lower(): row["sha256"] for row in archive["members"]}, bindings


def source_row(source, rid):
    table = source.db.execute("SELECT depot,archive,key,sha256,export_path,export_sha256 FROM resources WHERE rid=?", (rid,))
    row, = table
    return dict(zip(("depot", "archive", "key", "sha256", "export_path", "export_sha256"), row))


def owner_scopes(source, path):
    scopes = [source.scope(path[:depth]) for depth in range(1, len(path) + 1)]
    if None in scopes and path[:2] == (1, 19107) and path[2] == 100:
        # This private writer emits the unset ResourcePath as CName "none".
        # Require the embedded graph independently in the hashed export.
        rid, graph = scopes[1]
        inline = source.authored_node(rid, graph, 100)
        assert inline["phaseResource"]["DepotPath"]["$value"] == "none"
        assert source.db.execute("SELECT 1 FROM graphs WHERE rid=? AND path='root/100'", (rid,)).fetchone()
        scopes[2] = (rid, "root/100")
        if len(path) == 4:
            child = source.authored_node(rid, "root/100", path[3])
            depot = child["phaseResource"]["DepotPath"]["$value"]
            scopes[3] = (source.provider(depot), "root")
    assert all(pair is not None and pair[0] is not None for pair in scopes), (path, scopes)
    return scopes


def bind_owners(source, watches):
    owners = {}
    needed = set()
    for label, path in watches.items():
        scopes = owner_scopes(source, path)
        needed.update(rid for rid, _ in scopes)
        rid, graph = scopes[-1]
        owners[label] = {"path": path, "hash": f"{phase_hash(path):08X}", "depot": source.depots[rid], "graph": graph}
    assert all(owners[key]["depot"] == STORY for key in ("native-open-world", "native-bugfix", "s23-quest"))
    assert all(owner["depot"] == DIALOG for key, owner in owners.items() if key.endswith("-dialogue"))
    assert owners["s23-entry"]["depot"] == SSC
    needed.add(source.provider(DIALOG[:-len("questphase")] + "scene"))
    assert None not in needed
    return owners, needed


def verify_sources(source, needed):
    sources = [source_row(source, rid) for rid in sorted(needed)]
    for row in sources:
        rid = source.provider(row["depot"])
        normalized = normalize(load_export(pin(Path(row["export_path"]), row["export_sha256"])))
        support, = source.db.execute("SELECT support_json FROM resources WHERE rid=?", (rid,)).fetchone()
        assert normalized["support"] == json.loads(support), row["depot"]
        for graph in normalized["graphs"]:
            if graph["kind"] != "quest":
                continue
            path = graph["path"]
            assert all(source.authored_node(rid, path, n["id"]) == n["parameters"] for n in graph["nodes"])
            edges = source.db.execute("SELECT source,source_socket,source_type,destination,destination_socket,"
                                      "destination_type FROM edges WHERE rid=? AND graph=?", (rid, path)).fetchall()
            assert sorted(edges) == graph["edges"], (row["depot"], path)
    return sources


def graph_contract(source):
    db = source.db
    boot = source.provider(SSC)
    quest = source.provider(STORY)
    ep1, _ = source.scope((1, 0, 10))
    nodes = source.authored_node

    def edges(rid, graph, start):
        return db.execute("SELECT source_socket,destination,destination_socket FROM edges WHERE rid=? AND graph=? "
                          "AND source=? ORDER BY source_socket,destination", (rid, graph, start)).fetchall()

    assert edges(ep1, "root/10", 8) == [("Out", 9, "In")]
    cut = edges(ep1, "root/10", 9)
    assert cut == [("CutSource", 3, "CutDestination"), ("CutSource", 4, "CutDestination"),
                   ("CutSource", 5, "CutDestination"), ("Out", 10, "In")]
    assert nodes(ep1, "root/10", 10)["type"]["factName"] == "q307_ep1_killed"
    workaround = source.provider(r"ep1\openworld\vendors\vehicle_metaquest\phases\vehicle_metaquest_ep1_bugfixing.questphase")
    open_world = source.provider(r"ep1\openworld\ep1_open_world.questphase")
    assert nodes(workaround, "root/5", 3)["condition"]["type"]["factName"] == "CP77-63752"
    assert nodes(workaround, "root/5", 2)["type"]["factName"] == "CP77-63752"
    assert nodes(workaround, "root/5", 4)["condition"]["type"]["factName"] == "militech_hellhound_available"
    assert edges(workaround, "root/5", 4) == [("False", 6, "CP77-63752")]
    incoming = db.execute("SELECT source,source_socket,destination_socket FROM edges WHERE rid=? AND graph='root/5' AND destination=6",
                          (workaround,)).fetchall()
    assert incoming == [(4, "False", "CP77-63752")]
    entry = nodes(open_world, "root", 47)
    assert entry["socketName"]["$value"] == "CP77-63752" and edges(open_world, "root", 47) == [("Out", 29, "In1")]
    assert nodes(open_world, "root", 29)["phaseResource"]["DepotPath"]["$value"].endswith(r"\vehicle_metaquest_ep1.questphase")
    assert edges(open_world, "root", 29) == []
    assert ("Out1", 14, "In1") in edges(open_world, "root", 11)
    assert nodes(boot, "root", 4)["type"]["factName"] == "PTFRS23_HASAN_Issued"
    assert nodes(boot, "root", 92)["type"]["factName"] == "PTFRS23_HASAN_Entered"
    assert edges(boot, "root", 92) == [("Out", 100, "In1"), ("Out", 102, "In")]
    assert edges(boot, "root/100", 0) == [("Out", 12, "In"), ("Out", 29, "In")]
    assert edges(boot, "root/100", 29) == [("Out", 5, "In1")]
    assert edges(boot, "root/100", 12) == [("Out", 9, "In1")] and edges(boot, "root/100", 9) == [("Out1", 12, "In")]
    listener = nodes(quest, "root", 81)["condition"]["type"]
    assert listener["factName"] == "travelling_merchant_lives" and listener["value"] == 999
    assert edges(quest, "root", 81) == []
    real_time = nodes(quest, "root", 69)["condition"]["type"]
    game_time = nodes(quest, "root", 47)["condition"]["type"]
    assert real_time["$type"] == "questRealtimeDelay_ConditionType" and real_time["hours"] == 1
    assert game_time["$type"] == "questGameTimeDelay_ConditionType" and (game_time["days"], game_time["hours"]) == (3, 16)
    assert edges(quest, "root", 38) == [("Out", 61, "In"), ("Out", 62, "In"), ("Out", 69, "In")]
    assert edges(quest, "root", 69) == [("Out", 66, "In"), ("Out", 67, "In")]
    assert edges(quest, "root", 68) == [("Out1", 65, "Inactive")]
    assert edges(quest, "root", 80) == [("Out", 22, "Succeeded"), ("Out", 35, "Inactive")]
    assert nodes(quest, "root", 52)["condition"]["type"]["itemID"]["$value"] == "Items.Preset_Kenshin_Spy"
    assert nodes(quest, "root", 53)["type"]["factName"] == "wst_ep1_05_gun_taken"
    assert nodes(quest, "root", 32)["actions"][0]["type"]["spawnerReference"]["$value"] == "#wst_ep1_05_com"
    return {"ep1_cut_edges": cut, "s23_entry_edges": edges(boot, "root", 92),
            "bugfix_connected_input": "CP77-63752", "bugfix_input_destinations": [47, 29],
            "bugfix_vehicle_branch_continues_into_world_stories": False, "real_wait_node": 69,
            "game_wait_node": 47, "saved_registration_control": 81, "saved_control_condition": listener,
            "parallel_phone_waits": [61, 62], "expired_reply_edges": edges(quest, "root", 69),
            "reward_receipt_fact": "wst_ep1_05_gun_taken", "community": "#wst_ep1_05_com"}


def saved_rows(source, watches):
    hp = PREALPHA / "handler_preservation_hp1_20261112_01/saves_01"
    r5 = PREALPHA / "resume_dispatcher_rd5_gigs_20261113_01/saves_01"
    pins = {
        (hp, "ManualSave-26"): "6D914C82878C704B70A96CF5A2D94781739E94C41E2F14C7FC5ECD3553509E7D",
        (hp, "AutoSave-10"): "1DF56D4FC8A03DCA3ED7837F8F0E442F27367CFF5B409F39657E6F2E681A3B27",
        (hp, "AutoSave-11"): "46016E0BF3768CF592F0F95E58A37BF6C858AE9454F12A42B1E5E7973D31C565",
        (hp, "AutoSave-5"): "E5E65A2656C33B3D00F2FCDF4F0BD5AD81E0B3E9B1C5DA30C50167B3B42F2E96",
        (r5, "AutoSave-3"): "6238020F12F1B11C6DA1DFFC329041E22283C41CBDE6AB3931A0D0CFD8227B10",
        (r5, "AutoSave-5"): "E3E7DA3B5349BD2883CB3555C96800822090849D6D571D9F5FC7E8D68DA806D0",
    }
    results = []
    for (root, name), expected in pins.items():
        manifest_path = pin(root / name / "manifest.json", expected)
        manifest = read(manifest_path)
        sha256, index, entries, _ = saved_components(manifest_path)
        selected = {label: [] for label in watches}
        for label, path in watches.items():
            hashed = phase_hash(path)
            assert not index[hashed] or index[hashed] == {path}
            for slot, entry in enumerate(entries):
                if entry[1] != hashed:
                    continue
                assert path in index[hashed] and entry[0] and entry[2] < 0xFFFF
                phase = owner_scopes(source, path)[-1]
                definition = source.authored_node(*phase, entry[2])
                types = {record["$type"] for record in walk(definition) if "$type" in record}
                matching, = (name for name in types if token(name) == entry[0])
                selected[label].append({"slot": slot, "node": entry[2], "type": matching})
        assert [r["node"] for r in selected["s23-entry"]] == [2]
        early = root == hp and name in ("ManualSave-26", "AutoSave-10")
        assert [r["node"] for r in selected["native-open-world"]] == ([81] if early else [])
        if root == hp:
            assert {r["node"] for r in selected["native-default-dialogue"]} == ({46, 56} if early else set())
        for label in ("native-bugfix", "s23-quest", "s23-dialogue"):
            assert not selected[label]
        assert all(row["node"] not in (47, 69) for label, rows in selected.items()
                   if label in ("native-open-world", "native-bugfix", "s23-quest") for row in rows)
        result = {"name": name if root == hp else "RD5 " + name, "save_sha256": sha256, "registrations": selected,
                  "interned_phases": [label for label, path in watches.items() if path in index[phase_hash(path)]]}
        if root == hp:
            queued, = (row for row in manifest["nodes"] if row["name"] == "QueuedData")
            raw = pin(root / name / "QueuedData.bin", queued["sha256"]).read_bytes()
            # The four controls have no saved resource-request keys. Decode the
            # subsequent physical slots independently of registration membership.
            component, requests, count = struct.unpack_from("<IBI", raw)
            assert component == queued["id"] and requests == 0 and len(raw) == 9 + 4 * count, name
            slots = struct.unpack_from(f"<{count}I", raw, 9)
            assert all(slot < len(entries) for slot in slots)
            result["notification_count"] = count
            result["unique_notification_slots"] = len(set(slots))
            target_hashes = {phase_hash(path) for path in watches.values()}
            result["notifications_currently_mapped_to_watched_phase"] = [slot for slot in slots if entries[slot][1] in target_hashes]
            result["notifications_for_cleared_slots"] = sum(entries[slot] == (0, 0, 0xFFFF) for slot in slots)
        results.append(result)
    return results


def native_checks():
    engine = Image()
    probe = (HERE / "CutoffProbe.cpp").read_text()
    hooks = re.findall(r'MakeHook\((0x[0-9A-F]+), "([^"]+)", &(\w+),', probe)
    assert len(hooks) == 19
    for rva_text, escaped, name in hooks:
        offset = engine.off(int(rva_text, 16))
        assert engine.data[offset:offset + 8] == bytes.fromhex(escaped.replace("\\x", "")), name
    for table, offset, function in ((0x3040630, 0x60, 0x2B0800), (0x30BCE78, 0x110, 0x35F430),
                                    (0x31267A0, 0x10, 0x1948BC), (0x31C2388, 0x10, 0x193C74)):
        assert struct.unpack_from("<Q", engine.data, engine.off(table + offset))[0] == engine.base + function
    changes = {
        0x889C38: {0x889C76: "lea rcx, [rbx + 0x88]", 0x889CA6: "call 0x1402b1f40"},
        0x2B1F40: {0x2B1FE5: "lea rdi, [r15 + 0x70]", 0x2B2024: "lea r10, [r15 + 0x80]"},
        0xBEC890: {0xBEC8A6: "call 0x1402b1d30", 0xBEC8B5: "cmp dword ptr [rbx + 0x94], r8d",
                   0xBEC8E7: "call 0x1401cafc4"},
        0x2B0800: {0x2B0817: "mov rdx, qword ptr [rcx + 0x220]", 0x2B0831: "mov rbp, qword ptr [rdx + 0x10]",
                   0x2B085E: "mov dword ptr [rax + 0x28], edx", 0x2B0872: "lea rcx, [rax + 0x98]",
                   0x2B08A4: "jmp qword ptr [rax + 0x10]"},
        0x2B1B64: {0x2B1B74: "add rcx, 0x98"},
        0x2FCFD0: {0x2FCFE2: "add rax, qword ptr [rcx + 8]", 0x2FCFEE: "mov dword ptr [rax + 0xc], 0xffff"},
        0x1948BC: {0x1948DD: "mov r14, qword ptr [rbx + 0x18]", 0x1948F1: "mov r15, qword ptr [rbx + 0xf8]",
                   0x19496A: "mov qword ptr [rsi + 0x40], rdx"},
        0x193C74: {0x193DF0: "mov dword ptr [rsi + 0x40], eax"},
        0x88B6AC: {0x88B6C7: "lock cmpxchg dword ptr [r9 + 0x2c], ecx"},
        0x35F430: {0x35F4A0: "mov qword ptr [rsi + 0x68], rdx"},
    }
    rows = []
    for function, assertions in changes.items():
        instructions = {int(row["rva"], 16): row for row in engine.disasm(function)["instructions"]}
        for address, expected in assertions.items():
            instruction = instructions[address]
            assert f'{instruction["mnemonic"]} {instruction["operands"]}' == expected, instruction
            rows.append(instruction)
    return {"exe_sha256": engine.sha, "hook_count": len(hooks), "instructions": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=int)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--prepare-providers", action="store_true")
    args = parser.parse_args()
    watches = watch_table()
    _, archive, bindings = baseline()
    registry = REGISTRY / "registry_02/registry.sqlite3"
    with closing(sqlite3.connect(registry.as_uri() + "?mode=ro", uri=True)) as db:
        source = Source(db, archive, bindings)
        owners, needed = bind_owners(source, watches)
        sources = verify_sources(source, needed)
        if args.prepare_providers:
            out = HERE / "source_inventory_01.json"
            with out.open("x", encoding="utf-8") as stream:
                json.dump(sources, stream, indent=2)
            print(f"Prepared {len(sources)} source identities.")
            return
        contracts = graph_contract(source)
        captures = saved_rows(source, watches)
    provider_file = HERE / PROVIDER_SCAN
    providers = read(provider_file)
    assert providers["source_inventory_sha256"] == sha(HERE / "source_inventory_01.json")
    for row in sources:
        matching = [r for r in providers["providers"] if r["depot"] == row["depot"]]
        assert len(matching) == 1 and matching[0]["sha256"] == row["sha256"], row["depot"]
        assert Path(matching[0]["archive"]).resolve() == Path(row["archive"]).resolve(), row["depot"]

    assert args.build is not None
    build = HERE / f"build_{args.build:02d}"
    receipt = read(build / "build.json")
    for key, path in (("exe", build / "OwnerTraceChecks.exe"), ("source", HERE / "OwnerTraceChecks.cpp"),
                      ("header", HERE / "OwnerTrace.hpp"), ("probe", HERE / "CutoffProbe.cpp"),
                      ("dll", build / "PTFR_QuestTimerProbe.dll"), ("hold", SUSPENDED / "DelayHold.hpp"),
                      ("handoff", SUSPENDED / "RealTimeHandoff.hpp"), ("cutoff", SUSPENDED / "CutoffObservation.hpp"),
                      ("record", PREALPHA / "universal_resume_boundary_20261114_01/TimerRecord.hpp")):
        pin(path, receipt[key + "_sha256"])
    machine = native_checks()
    run = subprocess.run([str(build / "OwnerTraceChecks.exe")], cwd=build, capture_output=True, text=True, timeout=10)
    assert run.returncode == 0 and run.stdout.splitlines()[-1] == "27 passed, 0 failed", run.stdout + run.stderr
    out = HERE / f"evidence_{args.attempt:02d}"
    out.mkdir(exist_ok=False)
    (out / "fixture_checks.txt").write_text(run.stdout, encoding="utf-8")
    write(out / "assessment.json", {"status": "OWNER_PATHS_BOUND_DIAGNOSTIC_BUILT", "phases": owners,
          "source_contract": contracts, "selected_providers": len(sources), "provider_sha256": sha(provider_file),
          "archives_scanned": len(providers["archives"]), "saves": captures, "native": machine, "build": receipt,
          "checks": 27, "game_launches": 0, "game_writes": 0, "save_writes": 0, "live_probe_executed": False})
    print(run.stdout, end="")
    print(f"Verified {len(owners)} full paths, {len(sources)} exclusive providers and {len(captures)} saved projections.")


if __name__ == "__main__":
    main()
