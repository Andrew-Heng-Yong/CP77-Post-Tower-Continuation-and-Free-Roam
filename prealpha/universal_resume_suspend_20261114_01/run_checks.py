"""Copy bounded executable slices for a stand-alone synthetic scheduler fixture."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image

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
}
BOUNDS = {"decode_group": (0x1AA970, 0x1AA98A), "move_slot": (0x1957E0, 0x195823),
          "default_time": (0x37BA5C4, 0x37BA5C8), "zero_time": (0x37B9734, 0x37B9738),
          "quest_callback": (0x1304ED8, 0x1304EE3), "mark_ready": (0x88B6AC, 0x88B6EF),
          "notify_parent_slot": (0x88BB74, 0x88BB93), "event_manager_forward": (0x88BC48, 0x88BC56),
          "resolve_active_slot": (0x35371C, 0x35373D), "read_slot": (0x353708, 0x35371B),
          "contains_retired_slot": (0x214E48, 0x214E6A), "read_queue_index": (0x1EEC3C, 0x1EEC46),
          "unlock_quest_graph": (0x19417F0, 0x19417F8)}


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


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
                       ("header", HERE / "DelayHold.hpp")):
        assert digest(path.read_bytes()) == manifest[f"{name}_sha256"], name

    engine = Image()
    # A checksum on the full engine also pins these signatures, offsets and data.
    for address, fmt, expected in (
        (0x30A2A90 + 0x290, "<Q", engine.base + FUNCTIONS["remaining"]),
        (0x302B0A8 + 0xD8, "<Q", engine.base + FUNCTIONS["invoke_callback"]),
        (0x3695E40 + 0x10, "<Q", engine.base + BOUNDS["quest_callback"][0]),
        (0x30BCE78 + 0x200, "<Q", engine.base + FUNCTIONS["queue_notification"]),
        (0x30BCE78 + 0x2B0, "<Q", engine.base + FUNCTIONS["remove_notification"]),
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
    binding_path = HERE.parent / "universal_resume_20261114_01/evidence_04/timer_binding.json"
    binding_bytes = binding_path.read_bytes()
    assert digest(binding_bytes) == "9BE96664F8F76BFF8E101A9EE76382AB505F336EC171F079F22059DF2E0DAA2C"
    binding = json.loads(binding_bytes)
    fixture, = (row for row in binding["direct_delay_bindings"] if row["node_key"] == "1361AA1A00000005")
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
    assert checks == "32 passed, 0 failed", checks
    assessment = {
        "status": "ISOLATED_NATIVE_SCHEDULER_FIXTURES_PASSED",
        "engine_sha256": engine.sha,
        "slices": sources,
        "build": manifest,
        "fixture_id": f"{fixture_id:016X}",
        "fixture_seconds": fixture_seconds,
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
