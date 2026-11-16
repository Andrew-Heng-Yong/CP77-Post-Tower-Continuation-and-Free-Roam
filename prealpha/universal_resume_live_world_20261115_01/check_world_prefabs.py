"""Pin the native prefab query and exercise the readback on synthetic objects."""

import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PREALPHA = HERE.parent
WORKSPACE = PREALPHA.parent
sys.path.insert(0, str(PREALPHA / "universal_resume_falco_transfer_20261115_01"))
from build_restore_fixture import Image, VCVARS


PINS = {
    0x699498: {0x6994EC: "mov rcx, qword ptr [rsi + 0xc8]", 0x6994F9: "call 0x140699520"},
    0x69B1FC: {0x69B25A: "lea rbx, [rdi - 0x48]", 0x69B269: "call 0x14069b738",
               0x69B271: "call 0x14069b450"},
    0x69B450: {0x69B477: "lea rbx, [rcx + 0x2e8]", 0x69B499: "lea rdx, [rsi + 0x2d8]",
               0x69B4F0: "lea rcx, [rsi + 0x128]", 0x69B709: "mov r8d, 2"},
    0x69B9D0: {0x69B9DC: "lea rbx, [rcx + 0x2a0]", 0x69BA05: "call 0x1401adf8c",
               0x69BA1D: "mov rax, qword ptr [rdx + 0x10]", 0x69BA21: "mov ecx, dword ptr [rdx + 0x1c]",
               0x69BA33: "mov rcx, qword ptr [rsi + 0x50]", 0x69BA3A: "cmp byte ptr [rcx + rdx*8 + 0x82], dil"},
    0x69BA68: {0x69BA7C: "cmp qword ptr [rcx + 0x28], rdx", 0x69BAAA: "cmp byte ptr [r8 + 0x80], dl",
               0x69BAB3: "test byte ptr [r10 + 0x25], 8", 0x69BACC: "test byte ptr [r10 + 0x25], 4",
               0x69BAD3: "mov r11, qword ptr [r10 + 8]", 0x69BADF: "test byte ptr [r11 + 0x8c], 0x20"},
    0x8B8244: {0x8B826E: "mov qword ptr [rdi + 0x48], rax", 0x8B8279: "mov qword ptr [rdi], rcx",
               0x8B8283: "mov qword ptr [rdi + 0x58], rbp", 0x8B828B: "mov qword ptr [rdi + 0x50], rsi"},
    0x8B8CFC: {0x8B8E75: "lea rcx, [rdi + 0x50]", 0x8B8E79: "call 0x1408b8eb0"},
    0x8B8EB0: {0x8B8EB6: "cmp dword ptr [rcx + 8], 0", 0x8B8EBF: "mov edx, dword ptr [rcx + 0xc]",
               0x8B8ECE: "mov edx, 0x90"},
    0x1ADF8C: {0x1ADFDD: "mov dword ptr [r8], edx", 0x1ADFE2: "mov qword ptr [rbx], rcx"},
    0x88AFCC: {0x88AFF8: "cmp qword ptr [rbx + 0x58], 0", 0x88B006: "cmp sil, 2",
               0x88B011: "xchg byte ptr [rbx + 0x50], al", 0x88B0AD: "call 0x140dd5270",
               0x88B104: "call 0x140dd514c"},
    0x2B13F0: {0x2B1568: "call 0x140699f78", 0x2B1571: "mov dword ptr [rcx + 0x84], eax"},
    0x2FCF0C: {0x2FCF77: "call qword ptr [rax + 0x20]", 0x2FCF90: "call 0x1402fd024"},
    0x249934: {0x249947: "mov rdx, qword ptr [rbx + 0x38]", 0x24994B: "call qword ptr [rax + 0x1d0]",
               0x249953: "xchg dword ptr [rbx + 0x30], eax"},
    0x24995C: {0x249970: "lea rbx, [rcx + 0x208]", 0x249980: "call 0x1420027c0",
               0x24998E: "mov rdx, qword ptr [rsi + 0x210]", 0x2499CD: "dec dword ptr [rsi + 0x21c]"},
    0x654C0C: {0x654E4B: "lea rdx, [rsi + 0x208]", 0x654E56: "call 0x1426079fc",
               0x654E7C: "call qword ptr [rax + 0x10]", 0x654E89: "xchg byte ptr [rcx], dil"},
    0x26079FC: {0x2607A0B: "call 0x1420027c0"},
    0x88AFA0: {0x88AFBD: "call qword ptr [rax + 0x30]", 0x88AFC2: "xchg dword ptr [rbx + 0x30], eax"},
    0x88B32C: {0x88B348: "call 0x1401b92e4", 0x88B3E0: "call 0x14088bb94", 0x88B3FA: "jmp 0x1409bfc0c"},
    0x21F9AA0: {0x21F9ABF: "call 0x1401b92e4", 0x21F9B52: "call 0x14088b2c4", 0x21F9B6C: "jmp 0x1409bfc0c"},
    0x24DDEAE: {0x24DDEC8: "call qword ptr [rax]"},
    0x1934AC: {0x1934EF: "call qword ptr [rax + 0x2c0]", 0x193502: "call qword ptr [rax + 0x250]",
               0x193508: "xchg dword ptr [rbx + 0x30], edi"},
    0x7C0CA0: {0x7C0D19: "call 0x140b79234", 0x7C0D56: "call 0x140b79234", 0x7C0D87: "call 0x140b79130"},
}

INPUTS = {
    PREALPHA / "universal_resume_first_live_wait_20261115_01/run_sources_01/source_assessment.json":
        "5905BCE8AFCC83AFA58BA4868AD45B01E0999741BD50A64C31DE3631264DE009",
    PREALPHA / "quest_resume_registry_20261112_01/registry_02/registry.sqlite3":
        "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9",
}

VTABLE_SLOTS = {
    0x308F3B8 + 0x18: 0x69B1FC,
    0x310C838 + 0xD8: 0x3625C4,
    0x302BEC8 + 0xD8: 0x351660,
    0x3048D60 + 0x20: 0x249934,
    0x30467A8 + 0x20: 0x88AFA0,
    0x3679E48 + 0x1D0: 0x24995C,
    0x306FA58 + 0x30: 0x88B314,
}


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def require(condition, label):
    if not condition:
        raise ValueError(label)


def verify_authored_support():
    source, registry = INPUTS
    for path, expected in INPUTS.items():
        require(digest(path.read_bytes()) == expected, f"Changed source evidence {path.name}")
    resources = json.loads(source.read_bytes())["resources"]
    by_depot = {row["depot"]: row for row in resources}
    parent = by_depot[r"base\quest\minor_quests\mq049\mq049.questphase"]
    bugfixing = by_depot[r"base\quest\bugfixing\quest_bugfixing.questphase"]
    reyes = by_depot[r"base\quest\minor_quests\mq049\phases\mq049_messages_reyes.questphase"]
    falco = by_depot[r"base\quest\minor_quests\mq049\phases\mq049_messages_falco.questphase"]
    prefabs = [item["prefabNodeRef"]["$value"] for item in parent["root_support"]["phasePrefabs"]]
    require(prefabs == ["#mq049_pr_main", "#mq049_pr_reyes"], "Changed prefab ordering")

    with closing(sqlite3.connect(registry.as_uri() + "?mode=ro", uri=True)) as db:
        def node(resource, key, graph="root"):
            found, = db.execute("SELECT parameters_json FROM nodes WHERE rid=? AND graph=? AND id=?",
                                (resource["rid"], graph, key)).fetchone()
            return json.loads(found)

        phase = node(bugfixing, 64, "root/3")
        require(phase["phaseInstancePrefabs"] == [] and phase["unfreezingTriggerNodeRef"]["$value"] == "0" and
                phase["phaseResource"]["DepotPath"]["$value"] == parent["depot"], "Changed owner preload shape")
        choice = node(reyes, 18)["condition"]["type"]
        fact = node(reyes, 23)["condition"]["type"]
        require(choice["$type"] == "questJournalEntryState_ConditionType" and choice["state"] == "Succeeded" and
                fact["$type"] == "questVarComparison_ConditionType" and fact["factName"] == "mq049_falco_done",
                "Changed original listener types or targets")
        require(node(falco, 28)["condition"]["type"]["$type"] == "questGameTimeDelay_ConditionType",
                "Changed original clock type")
        trigger = node(falco, 2)["condition"]
        content, outside = trigger["conditions"]
        require(trigger["operation"] == "AND" and content["type"]["type"] == "SideQuest_MainPath" and
                outside["type"] == "IsOutside" and outside["isPlayerActivator"] == 1 and
                outside["triggerAreaRef"]["$value"] == "#mq049_tr_reyes_place", "Changed first expiry gate")
        gift = node(falco, 19)["type"]
        params, = gift["params"]
        require(gift["$type"] == "questTogglePrefabVariant_NodeType" and
                params["prefabNodeRef"]["$value"] == "#mq049_pr_gift" and
                [(v["name"]["$value"], v["show"]) for v in params["variantStates"]] == [("var_case", 1)],
                "Changed authored gift variant path")
        edges = set(db.execute("SELECT source,source_socket,destination,destination_socket FROM edges "
                               "WHERE rid=? AND graph='root'", (falco["rid"],)))
        require({(28, "Out", 2, "In"), (2, "Out", 19, "In"), (2, "Out", 29, "In")} <= edges,
                "Changed first timer expiry fanout")
    return {"prefabs": prefabs, "original_mode_2_trigger_ref": phase["unfreezingTriggerNodeRef"]["$value"],
            "journal_choice": choice["path"]["realPath"], "fact": fact["factName"],
            "wait_actor_bindings": [], "expiry_trigger": outside["triggerAreaRef"]["$value"],
            "expiry_gift": params["prefabNodeRef"]["$value"], "expiry_variant": "var_case"}


def checked_engine():
    image = Image()
    for start, expectation in PINS.items():
        view = image.disasm(start)
        if int(view["begin_rva"], 16) != start:
            raise ValueError(f"Unexpected native boundary at {start:08X}")
        instructions = {int(i["rva"], 16): i["mnemonic"] + " " + i["operands"] for i in view["instructions"]}
        for where, need in expectation.items():
            if instructions.get(where) != need:
                raise ValueError(f"Unexpected native instruction at {where:08X}")
    for slot, expected in VTABLE_SLOTS.items():
        pointer, = struct.unpack_from("<Q", image.data, image.off(slot))
        require(pointer == image.base + expected, f"Changed native virtual slot {slot:08X}")
    byte_slices = {}
    for start, end in ((0x1ADF8C, 0x1AE002), (0x69BB3C, 0x69BB98)):
        offset = image.off(start)
        byte_slices[hex(start)] = image.data[offset:offset + end - start]
    return image, byte_slices


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100))
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()
    image, raw = checked_engine()
    authored_support = verify_authored_support()
    native = out / "native.bin"
    native.write_bytes(b"".join(raw.values()))
    batch = out / "build.cmd"
    batch.write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /sourceDependencies deps.json '
        f'"{HERE / "WorldPrefabChecks.cpp"}" /link /OUT:WorldPrefabChecks.exe\n', encoding="ascii",
    )
    build = subprocess.run(["cmd.exe", "/d", "/c", batch.name], cwd=out, capture_output=True, text=True,
                           errors="replace", timeout=60)
    log = build.stdout + build.stderr
    (out / "build.txt").write_text(log, encoding="utf-8")
    print(log, end="")
    build.check_returncode()
    exe = out / "WorldPrefabChecks.exe"
    test = subprocess.run([str(exe), native.name], cwd=out, capture_output=True, text=True, errors="replace", timeout=20)
    log = test.stdout + test.stderr
    (out / "checks.txt").write_text(log, encoding="utf-8")
    print(log, end="")
    test.check_returncode()
    checks = sum(line.startswith("PASS ") for line in log.splitlines())
    if checks != 21:
        raise ValueError("Unexpected fixture check count")
    deps = json.loads((out / "deps.json").read_bytes())["Data"]
    inventory = [Path(path).resolve() for path in [deps["Source"], *deps["Includes"], __file__]]
    report = {
        "status": "WORLD_PREFAB_READBACK_FIXTURE_PASS", "engine_sha256": image.sha, "checks_passed": checks,
        "game_runtime_exercised": False, "fixture_exe_sha256": digest(exe.read_bytes()),
        "slices": {name: digest(data) for name, data in raw.items()}, "native_instructions": PINS,
        "native_virtual_slots": VTABLE_SLOTS, "authored_support": authored_support,
        "inputs": {str(path.relative_to(WORKSPACE) if path.is_relative_to(WORKSPACE) else path): digest(path.read_bytes())
                   for path in [*inventory, *INPUTS]},
    }
    (out / "assessment.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
