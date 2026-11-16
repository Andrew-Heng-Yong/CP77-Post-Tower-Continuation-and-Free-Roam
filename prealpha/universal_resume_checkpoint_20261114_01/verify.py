"""Verify the exact staged checkpoint against PE, saved controls and actual Lua."""

import argparse
import ast
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from stage import ARCHIVE_SHA, HERE, HISTORY, LUA, baseline, sha

SCC = HERE.parent
sys.path.insert(0, str(SCC / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image

sys.path.insert(0, str(SCC / "quest_restoration_qr9/worker_b/tooling"))
from lupa.luajit21 import LuaRuntime

CHECKPOINT_DLL = "red4ext/plugins/PTFR_ExecutionCheckpoint/PTFR_ExecutionCheckpoint.dll"
PINNED_SAVED_SHA = "6BEFAEE9EA1FA77A515C5A1EC9C867EA5B5DACB166D637D24B1423260E9C2AA4"
HISTORY_FIXTURE_SHA = "C27598B50A97F3B7D3DD4905CEF1EB8C0F8FB67DF2865933E022B58D5D13D8F0"
EP_PATH = [0, 2, 82, 5, 48, 79]


def read_json(path):
    return json.loads(path.read_bytes())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def native_binary():
    image = Image()
    cpp = (HERE / "NativeCheckpoint.cpp").read_text(encoding="utf-8")
    hooks = re.findall(r'MakeHook\((0x[0-9A-F]+), "((?:\\x[0-9a-fA-F]{2}){8})"', cpp)
    assert len(hooks) == 9
    for rva, text in hooks:
        address = int(rva, 16)
        offset = image.off(address)
        assert image.function(address)[0] == address
        assert image.data[offset:offset + 8] == bytes.fromhex(text.replace(r"\x", ""))
    tables = [(0x30BCE78, 0x110, 0x35F430), (0x30BCE78, 0x148, 0x739578),
              (0x306FA58, 0x10, 0x2B2270), (0x30A2A90, 0x290, 0x111894C),
              (0x3047250, 0x158, 0x9DDC68), (0x30E5E68, 0xE8, 0x9DDCB0)]
    for table, slot, target in tables:
        assert struct.unpack_from("<Q", image.data, image.off(table + slot))[0] == image.base + target
    anchors = {
        0x9DDC68: {0x9DDC6E: ("mov", "rcx, qword ptr [rcx + 0x48]"),
                   0x9DDC7D: ("call", "qword ptr [rax + 0xe8]")},
        0x3C7704: {0x3C775E: ("mov", "qword ptr [rbx + 0x18], rax"),
                   0x3C77CE: ("mov", "qword ptr [rbx + 0x28], rax")},
        0x2B3150: {0x2B3272: ("mov", "qword ptr [rbx + 0x220], rdi")},
        0x2B224C: {0x2B225E: ("mov", "rax, qword ptr [rdx + 0xf8]")},
        0x35F430: {0x35F4A0: ("mov", "qword ptr [rsi + 0x68], rdx")},
        0x156EFD0: {0x156F001: ("call", "0x1402b32b0")},
        0x2C9F364: {0x2C9F378: ("lea", "rdx, [rcx + 0x60]"),
                    0x2C9F3C2: ("lea", "rdx, [r14 + 0xa8]"),
                    0x2C9F441: ("mov", "rbx, qword ptr [r14 + 0xe8]"),
                    0x2C9F49E: ("mov", "rcx, qword ptr [r14 + 0xf0]")},
        0x2B0800: {0x2B085E: ("mov", "dword ptr [rax + 0x28], edx"),
                   0x2B0872: ("lea", "rcx, [rax + 0x98]")},
        0x2CA0568: {0x2CA05AB: ("lea", "rdx, [rsi + 0x128]"),
                    0x2CA05C5: ("mov", "rbx, qword ptr [rsi + 0x130]"),
                    0x2CA0632: ("lea", "rdx, [rsi + 0x150]"),
                    0x2CA066C: ("mov", "rdx, qword ptr [rsi + 0x158]")},
        0x3534DC: {0x353508: ("lea", "rdx, [rcx + 0x150]"),
                   0x353583: ("lea", "rdx, [rsi + 0x60]")},
        0x2CD3208: {0x2CD3222: ("call", "0x141ffad60"),
                    0x2CD324C: ("mov", "eax, dword ptr [rbx + 0x14]"),
                    0x2CD326D: ("shl", "ebp, 4"),
                    0x2CD32A2: ("mov", "rdx, qword ptr [rbx + 8]")},
        0x2CD95B4: {0x2CD9625: ("mov", "rdx, qword ptr [rsi + 8]"),
                    0x2CD963B: ("mov", "rdx, qword ptr [rsi + 0x18]")},
        0x2B2270: {0x2B228F: ("call", "0x1401b92e4"), 0x2B22B4: ("call", "0x1409bfc0c")},
        0x1948BC: {0x19496A: ("mov", "qword ptr [rsi + 0x40], rdx")},
        0x193C74: {0x193CCD: ("mov", "dword ptr [rsi + 0x40], eax")},
        0x468358: {0x46836B: ("call", "qword ptr [rax + 0xf8]")},
    }
    for rva, checks in anchors.items():
        instructions = {int(row["rva"], 16): (row["mnemonic"], row["operands"])
                        for row in image.disasm(rva)["instructions"]}
        for sub, expected in checks.items():
            assert instructions[sub] == expected, (hex(sub), instructions[sub], expected)
    return {"sha256": image.sha, "hook_count": len(hooks), "vtable_checks": len(tables),
            "instruction_checks": sum(map(len, anchors.values()))}


def saved_input(payload):
    pinned = SCC / "quest_resume_contracts_rc2_20261114_01"
    prev = read_json(pinned / "checkpoint.json")
    path = pinned / prev["saved_witness"]
    history = read_json(path)
    assert history["save_sha256"] == PINNED_SAVED_SHA
    row, = (row for row in history["saved_logical_signals"]
            if row["address"] == EP_PATH and row["node"] == 198 and row["table"] == 4)
    assert row["signaled_inputs"] == ["In2", "In3", "In7"]
    assert row["authored_input_order"] == ["In1", "In2", "In3", "In4", "In5", "In6", "In7"]
    phase, = (phase for phase in payload["phases"] if phase[3] == EP_PATH)
    key = 0x811C9DC5
    for byte in struct.pack("<Q", phase[0] << 32 | row["node"]):
        key = ((key ^ byte) * 0x01000193) & 0xFFFFFFFF
    assert [key, row["value"]] in payload["graph_facts"][row["table"] - 3]
    assert key == row["key"] and row["value"] == 70
    assert [entry[0] for entry in payload["timings"]] == [0, 1]
    assert payload["presentation"]["player_in_scene"] and payload["presentation"]["phone_manager_active"]
    assert payload["presentation"]["call_phase"] == 2 and payload["presentation"]["phone_talking_fact"] == 2
    assert payload["archive_sha256"] == ARCHIVE_SHA
    return {"saved_witness_sha256": sha(path), "historical_save_sha256": history["save_sha256"],
            "epistrophy_path": EP_PATH, "epistrophy_input_mask": row["value"],
            "interpretation": "Saved input semantics checked against the synthetic cutoff payload."}


def lua_definitions():
    previous = SCC / "history_capture_hs3_20261112_01"
    script = previous / "test_export.py"
    assert read_json(previous / "checkpoint.json")["sources"]["test_export.py"] == sha(script)
    decl, = (node for node in ast.parse(script.read_text(encoding="utf-8")).body
             if isinstance(node, ast.FunctionDef) and node.name == "fixture")
    env = {"LuaRuntime": LuaRuntime, "json": json}
    exec(compile(ast.Module(body=[decl], type_ignores=[]), str(script), "exec"), env)

    latest = SCC / "history_file_loader_hs4_20261112_01" / "test_latest.py"
    declaration, = (node for node in ast.parse(latest.read_text(encoding="utf-8")).body
                    if isinstance(node, ast.Assign) and node.targets[0].id == "ENGINE")
    return env["fixture"], ast.literal_eval(declaration.value)


def lua_checks(source, game, raw):
    native = json.loads(raw)
    path = "checkpoint_execution_" + native["id"] + ".json"
    fixture, hs4_engine = lua_definitions()
    count = 24753
    checks = []

    def setup(payload=raw):
        lua, g = fixture(source, count)
        lua.execute("""
        originalId, originalData = "", ""
        matches=0
        local s=systems[3]
        s.MayLoadLatestHS4=function() return false end
        s.ExecutionCheckpointId=function() return originalId end
        s.ExecutionCheckpointJSON=function() return originalData end
        s.MatchesExecutionCheckpoint=function(_,id,data)
          matches=matches+1;return id==originalId and data==originalData
        end
        """)
        g.originalId = json.loads(payload)["id"] if payload else ""
        g.originalData = payload
        return lua, g

    def drive(g, n=1, drain=False):
        for _ in range(n):
            if drain:
                g.drain()
            g.events.onUpdate(0.1)
        if drain:
            g.drain()

    lua, g = setup()
    drive(g)
    assert g.files[path] == raw and set(g.files.keys()) == {path}
    assert g.matches >= 3 and g.systems[3].acks == 0
    checks.append("Authoritative checkpoint exports only exact bytes verified through local identity and readback.")
    # The legacy exports finish independently, with their original schema and counts.
    drive(g, (count + 63) // 64 + 2)
    for schema, rows in ((1, 158), (3, count)):
        system = g.systems[schema]
        legacy_path = f"snapshot_hs{schema}_{system.token}.json"
        document = json.loads(g.files[legacy_path])
        assert document["schema"] == schema and len(document["rows"]) == rows and system.acks == 1
    checks.append("Both legacy recovery exports finish with their existing formats and acknowledgements.")

    _, g = setup("")
    g.files[path] = raw
    drive(g)
    assert g.files[path] == raw and g.matches == 0
    checks.append("A save without a checkpoint never becomes an exact match through a disk file.")

    _, g = setup()
    g.files[path] = '{"other_save":true}'
    drive(g)
    assert g.files[path] == '{"other_save":true}' and set(g.files.keys()) == {path}
    checks.append("A different file at the save-local ID is preserved and never verified.")

    for fault in ("failWrite", "failFlush", "failClose", "corruptReadback", "failRename"):
        _, g = setup()
        g[fault] = True
        drive(g)
        assert g.files[path] is None
        g[fault] = False
        drive(g, 56)
        assert g.files[path] == raw
        checks.append(f"{fault} leaves the save-bound record intact and retries the export.")

    lua, g = setup()
    second = dict(native, id="b" * 32)
    g.secondData = json.dumps(second, separators=(",", ":"))
    lua.execute("""
        local open=io.open
        io.open=function(name,mode)
          local file=open(name,mode)
          if file and mode=="wb" and name:match("^checkpoint_execution_") then
            local close=file.close
            file.close=function(self)
              originalId=string.rep("b",32);originalData=secondData
              return close(self)
            end
          end
          return file
        end
        """)
    drive(g, 2)
    assert g.files[path] is None and g.files["checkpoint_execution_" + second["id"] + ".json"] == g.secondData
    checks.append("A save switch with an identical epoch, route, ticket and revision cannot cross-publish.")

    _, g = setup()
    g.files[path] = raw
    drive(g, 2)
    assert set(g.files.keys()) == {path} and g.files[path] == raw
    checks.append("Identical existing recovery bytes are reused without a duplicate export.")

    export = (game / LUA).parent
    names = {1: "snapshot_hs1_20261112T193921Z_151_2.json", 3: "snapshot_hs3_20261112T193931Z_1_3.json"}
    assert sha(export / names[3]) == HISTORY_FIXTURE_SHA
    values = {channel: (export / name).read_text(encoding="utf-8") for channel, name in names.items()}
    docs = {channel: json.loads(text) for channel, text in values.items()}
    lua, g = setup("")
    for channel, name in names.items():
        definitions = [json.dumps(row["definition"], separators=(",", ":")) for row in docs[channel]["rows"]]
        g[f"defs{channel}"] = lua.table_from(definitions)
        g.files[name] = values[channel]
    g.files[path] = raw
    lua.execute(hs4_engine)
    drive(g, 650, drain=True)
    assert g.systems[3].loaded and g.begins == 1 and g.finishes == 1 and g.matches == 0
    assert g.systems[3].selected.token3 == names[3][13:-5]
    for channel in (1, 3):
        packets = g.systems[3].packets[channel]
        actual = [packet.data[i] for _, packet in packets.items() for i in range(1, len(packet.data) + 1)]
        expected = []
        for row in docs[channel]["rows"]:
            if channel == 1:
                expected.extend((int(row["stable"]), int(row["legacy_pre_ending_certificate"])))
                for name in ("states", "counters", "optional", "tracked", "facts"):
                    expected.extend(row[name])
            else:
                keys = ("state", "counter", "optional", "tracked") if row["definition"]["kind"] == "journal" else ("value",)
                expected.extend(row[key] for key in keys)
                expected.append(int(row["stable"]))
        assert actual == expected
    assert set(g.files.keys()) == set(names.values()) | {path}
    checks.append("Global latest still transfers all original HS1 and HS3 primitives and ignores the execution file.")
    return checks


def run(attempt, compiled, built):
    game, core = baseline()
    out = HERE / f"checks_{attempt:02d}"
    out.mkdir(exist_ok=False)
    native = HERE / f"build_{built:02d}"
    script = HERE / f"compile_{compiled:02d}"
    build_receipt = {row["name"]: row["sha256"] for row in read_json(native / "build.json")}
    compile_receipt = read_json(script / "receipt.json")
    assert sha(HERE / "NativeCheckpoint.cpp") == build_receipt["NativeCheckpoint.cpp"]
    assert sha(HERE / "Checkpoint.hpp") == build_receipt["Checkpoint.hpp"]
    assert sha(HERE / "CheckpointChecks.cpp") == build_receipt["CheckpointChecks.cpp"]
    assert sha(native / "CheckpointChecks.exe") == build_receipt["CheckpointChecks.exe"]
    assert sha(native / Path(CHECKPOINT_DLL).name) == build_receipt[Path(CHECKPOINT_DLL).name]
    cmd = subprocess.run([native / "CheckpointChecks.exe"], capture_output=True, text=True, timeout=45)
    (out / "native_checks.txt").write_text(cmd.stdout + cmd.stderr, encoding="utf-8")
    assert cmd.returncode == 0, cmd.stdout + cmd.stderr
    passes = [line[5:] for line in cmd.stdout.splitlines() if line.startswith("PASS ")]
    raw, = (line[8:] for line in cmd.stdout.splitlines() if line.startswith("PAYLOAD "))
    abi = native_binary()
    control = saved_input(json.loads(raw))
    lua = script / "init.lua"
    assert sha(lua) == compile_receipt["staged_lua"][LUA]
    legacy_checks = lua_checks(lua.read_text(encoding="utf-8"), game, raw)
    assert baseline() == (game, core)
    assert all(sha(game / rel) == digest for rel, digest in compile_receipt["compiler_inputs"].items())
    package = HERE / f"candidate_{attempt:02d}"
    package.mkdir(exist_ok=False)
    paths = {HISTORY: script / "scripts" / HISTORY, LUA: lua, CHECKPOINT_DLL: native / Path(CHECKPOINT_DLL).name}
    files = {}
    for relative, source in paths.items():
        target = package / "files" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files[relative] = sha(target)
        assert files[relative] == sha(source)
    assert files[HISTORY] == compile_receipt["staged_redscript"][HISTORY]
    assert not (game / CHECKPOINT_DLL).exists(), "New plugin already present in live tree"
    write_json(out / "results.json", {"native_checks": passes, "binary_checks": abi, "saved_control": control,
                                     "lua_checks": legacy_checks, "verified_installed_paths": len(core),
                                     "save_writes": 0, "game_writes": 0, "gameplay_verified": False})
    write_json(package / "receipt.json", {
        "status": "WORKSPACE_CANDIDATE", "archive_sha256": ARCHIVE_SHA, "files": files,
        "compile_receipt": script.name + "/receipt.json", "compile_receipt_sha256": sha(script / "receipt.json"),
        "build_receipt_sha256": sha(native / "build.json"), "check_receipt_sha256": sha(out / "results.json"),
        "gameplay_verified": False,
    })
    print(f"{len(passes)} native fixture checks, {sum(abi[key] for key in ('hook_count', 'vtable_checks', 'instruction_checks'))} "
          f"binary checks, {len(legacy_checks)} Lua checks and 3 staged file readbacks passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--compiled", type=int, choices=range(1, 100), required=True)
    parser.add_argument("--built", type=int, choices=range(1, 100), required=True)
    args = parser.parse_args()
    run(args.attempt, args.compiled, args.built)
