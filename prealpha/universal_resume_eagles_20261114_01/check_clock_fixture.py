"""Replay only bounded native clock and callback code inside a stand-alone fixture."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image

SLICES = {
    0x193B00: 0x193B54,  # Evaluate the native absolute game-time timer.
    0x193E58: 0x193E74,  # Invoke its callback.
    0x1AAB88: 0x1AABA6,  # Read the callback function object.
    0x88B6AC: 0x88B6EF,
    0x88BB74: 0x88BB93,
    0x88BC48: 0x88BC56,
    0xB79440: 0xB79449,
    0xB79130: 0xB79232,
    0xB79234: 0xB7943B,
    0xB79464: 0xB7946C,
    0xB79470: 0xB79484,
    0xB79490: 0xB794A9,
    0x2179690: 0x21796A8,
    0x21798D0: 0x21798D9,
    0x2179790: 0x21798CE,
    0x2179CA0: 0x2179D61,
    0x2179D70: 0x2179DA0,
    0x2179E50: 0x2179E7D,
    0x2179E80: 0x2179F1F,
    0x2179F20: 0x2179F53,
    0x2179AB0: 0x2179AFA,
    0x18A71C: 0x18A747,
    0x195734: 0x195788,
    0x195798: 0x1957DD,
    0x19412C: 0x194160,
    0x2179700: 0x217976A,
    0x12428A8: 0x12428B7,
    0x193B54: 0x193B87,
    0x1AAAC8: 0x1AAB3F,
    0x15702A8: 0x15702BE,
    0x258480: 0x258489,
    0x36A1D20: 0x36A1D48,
}

SIGNATURES = {
    0x30BD228 + 0x240: 0xA09BC4,  # Schedule.
    0x30BD228 + 0x250: 0x193674,  # Queue cancellation.
    0x30BD228 + 0x268: 0x193B88,  # Reattach by saved timer ID.
    0x30A75A8 + 0x120: 0x193B00,
    0x30A75A8 + 0x128: 0xB79440,
    0x30A75A8 + 0x130: 0x193E58,
    0x30A75A8 + 0x110: 0x2B0F69C,
    0x30A75A8 + 0x118: 0xA0A228,
    0x31C2388 + 0x10: 0x193C74,
    0x31C2388 + 0x20: 0x1934AC,
    0x36A1D20 + 0x10: 0x1304ED8,
    0x36A1D50 + 0x10: 0x1304ED8,
}


def digest(data):
    return sha256(data).hexdigest().upper()


def encode_native(engine):
    for slot, target in SIGNATURES.items():
        assert struct.unpack_from("<Q", engine.data, engine.off(slot))[0] == engine.base + target, hex(slot)
    instruction_pins = {
        0x7C0CA0: {0x7C0D56: "call 0x140b79234", 0x7C0D87: "call 0x140b79130",
                   0x7C0FC6: "lea r15, [r14 + 0x30130]", 0x7C1009: "call rdi"},
        0xB79130: {0xB79189: "cmp dword ptr [rcx + 0x88], esi"},
        0x2179700: {0x2179716: "mov eax, dword ptr [rbx + 0x3000]",
                    0x217973E: "add rbx, 0x18"},
        0xA0A45C: {0xA0A4B8: "mov dword ptr [r14 + 0x90], eax",
                   0xA0A4C6: "mov byte ptr [r14 + 0x94], al",
                   0xA0A4CD: "mov dword ptr [r14 + 0x40], ebx"},
        0x193B00: {0x193B11: "cmp dword ptr [rdi + 0x40], ebx",
                   0x193B14: "jle 0x140193b23", 0x193B34: "mov eax, dword ptr [rdi + 0x44]"},
        0x193B88: {0x193C3D: "lea rcx, [rsi + 0x48]"},
        0x193E58: {0x193E5C: "cmp qword ptr [rcx + 0x80], 0"},
        0x2B0F614: {0x2B0F623: "mov eax, dword ptr [rcx + 0x88]",
                    0x2B0F64C: "lea rdx, [rbx + 0x40]",
                    0x2B0F65C: "lea rdx, [rbx + 0x44]"},
        0x2B0F69C: {0x2B0F6B4: "lea rdx, [rbx + 0x94]", 0x2B0F6CB: "lea rdx, [rbx + 0x90]"},
        0xA0A4F0: {0xA0A508: "lea rdx, [rcx + 0x88]", 0xA0A520: "lea rdx, [rbx + 0x40]",
                   0xA0A530: "lea rdx, [rbx + 0x44]"},
    }
    for function, pins in instruction_pins.items():
        instructions = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}'
                        for row in engine.disasm(function)["instructions"]}
        for address, expected in pins.items():
            assert instructions.get(address) == expected, (hex(address), instructions.get(address), expected)
    packet = bytearray(struct.pack("<I", len(SLICES)))
    receipts = {}
    for rva, end in SLICES.items():
        offset = engine.off(rva)
        data = engine.data[offset:offset + end - rva]
        packet.extend(struct.pack("<II", rva, len(data)))
        packet.extend(data)
        receipts[hex(rva)] = digest(data)
    return packet, receipts, instruction_pins


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=int, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    build = HERE / f"build_{args.build:02}"
    output = HERE / f"evidence_{args.attempt:02}"
    exe = build / "GameTimeChecks.exe"
    receipt = json.loads((build / "build.json").read_bytes())
    for key, file in (("source", HERE / "GameTimeChecks.cpp"), ("header", HERE / "GameTimeWait.hpp"), ("exe", exe)):
        assert digest(file.read_bytes()) == receipt[f"{key}_sha256"]
    engine = Image()
    data, slices, instructions = encode_native(engine)
    source = HERE.parent / "universal_resume_retirement_20261114_01/wait_fixture_01/assessment.json"
    source_bytes = source.read_bytes()
    assert digest(source_bytes) == "9C65B82C44BDFA9F8933ABC190882CAAD760DE9D49692B7A43FA2D490AE8A2B0"
    fixture = json.loads(source_bytes)
    assert fixture["status"] == "OFFLINE_RESTORED_QUEST_GAME_TIME_FIXTURE"
    assert fixture["native"]["engine_sha256"] == engine.sha
    sample = fixture["sample"]
    assert sample["node_key"] == "CCF9887E00000050"
    assert sample["deadline"] - sample["game_seconds_at_save"] == sample["remaining_game_seconds"] == 171141
    assert sample["authored_game_seconds"] == 172800
    journal_bytes = (HERE / "evidence_02/journal.json").read_bytes()
    assert digest(journal_bytes) == "5DBE6AC9156633343EDC8536F2DE1010177D4D79E2330DDCDEE2E69952BCD1A5"
    original, = (row for row in json.loads(journal_bytes)["saves"] if row["slot"] == "ManualSave-26")
    assert original["save_sha256"] == sample["fixture_save_sha256"]
    assert original["journal_state"]["quests/minor_quest/mq058_semimaru_crystalcoat"] == 3
    assert original["journal_state"]["contacts/marianne/mq058_02_resolution/01a_v"] == 2
    assert original["facts"]["mq058_done"] == original["facts"]["mq058_update_applied"] == 1

    output.mkdir(exist_ok=False)
    packet = output / "native_slices.bin"
    packet.write_bytes(data)
    fields = ("game_timer_id", "game_seconds_at_save", "deadline", "authored_game_seconds")
    result = subprocess.run([str(exe), str(packet), *(str(sample[k]) for k in fields)], cwd=output,
                            capture_output=True, text=True, timeout=15)
    (output / "fixture_checks.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    print(result.stdout + result.stderr, end="")
    checks = sum(line.startswith("PASS ") for line in result.stdout.splitlines())
    assert result.returncode == 0 and checks == 29, (hex(result.returncode), checks)
    assert result.stdout.splitlines()[-1] == f"{checks} passed, 0 failed"
    assessment = {
        "status": "ISOLATED_GAME_TIME_DEADLINE_AND_CALLBACK_PASSED",
        "native_sha256": engine.sha,
        "source_evidence_sha256": digest(source_bytes),
        "journal_evidence_sha256": digest(journal_bytes),
        "fixture_is_post_completion_reply": True,
        "slice_hashes": slices,
        "instruction_checks": instructions,
        "build": receipt,
        "checks": checks,
        "runtime_installed": False,
        "gameplay_exercised": False,
    }
    (output / "clock_assessment.json").write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
