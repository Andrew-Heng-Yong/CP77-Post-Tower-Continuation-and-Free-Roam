"""Verify the selected native boundaries and run the stand-alone successor."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "universal_resume_handoff_20261114_01"
TIMER_CHECKS = 60
RETIREMENT_CHECKS = 26
sys.path.insert(0, str(HERE.parent / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def engine_bytes(engine, rva, size):
    offset = engine.off(rva)
    return engine.data[offset:offset + size]


def verified_slices(engine):
    evidence = PRIOR / "evidence_08"
    assessment = (evidence / "assessment.json").read_bytes()
    assert digest(assessment) == "C13340A611E5D0F7F5EE0E8C4C2B3BC5DA3D443916E6351A645D44F10F482551"
    previous = json.loads(assessment)
    packet = (evidence / "engine_slices.bin").read_bytes()
    assert digest(packet) == "758E08EBDE3804CE55BF95DD10D704A952AE21611754AFE1DF1E48B5D0A54BA2"
    assert previous["engine_sha256"] == engine.sha

    count, = struct.unpack_from("<I", packet)
    slices = previous["slices"]
    assert count == len(slices) == 73
    offset = struct.calcsize("<IQf")
    for item in slices.values():
        rva, size = struct.unpack_from("<II", packet, offset)
        offset += 8
        assert (rva, size) == (int(item["rva"], 16), item["length"])
        assert packet[offset:offset + size] == engine_bytes(engine, rva, size)
        assert digest(packet[offset:offset + size]) == item["sha256"]
        offset += size
    assert offset == len(packet)

    successor = bytearray(packet)
    extra = {"native_slot_registration": 0xEB6B3C, "registration_append": 0x1CC5AC,
             "reload_free_slots": 0xCC5844}
    for name, rva in extra.items():
        start, end, _ = engine.function(rva)
        assert start == rva
        data = engine_bytes(engine, start, end - start)
        successor.extend(struct.pack("<II", rva, len(data)))
        successor.extend(data)
        slices[name] = {"rva": hex(rva), "length": len(data), "sha256": digest(data)}
    struct.pack_into("<I", successor, 0, len(slices))
    return successor, slices, previous["build"]


def verify_engine(engine):
    instructions = {
        0x3534DC: {
            0x353529: "mov rbx, qword ptr [rsi + 0x158]",
            0x353587: "and dword ptr [rsi + 0x164], 0",
            0x353583: "lea rdx, [rsi + 0x60]",
            0x353590: "xchg byte ptr [rax], cl",
            0x3535A0: "call 0x141ffad60",
            0x3535F2: "call 0x14035371c",
            0x353602: "call 0x140353708",
            0x3536DF: "call 0x1419417f0",
        },
        0x4AD5CC: {0x4AD66B: "call 0x1403534dc"},
        0x2FCFD0: {
            0x2FCFEE: "mov dword ptr [rax + 0xc], 0xffff",
            0x2FCFFC: "call qword ptr [rax + 0x2b0]",
            0x2FD002: "lea rcx, [rbx + 0x18]",
        },
        0xEB6B3C: {
            0xEB6B50: "dec dword ptr [rcx + 0x24]",
            0xEB6B5A: "mov eax, dword ptr [rax + rcx*4]",
            0xEB6B73: "movdqu xmmword ptr [rcx + rdx*8], xmm0",
        },
        0x2B0800: {0x2B08B6: "call 0x140eb6b3c"},
        0x1FFAD60: {0x1FFAD69: "mov qword ptr [rcx], rdx", 0x1FFAD6F: "call 0x1422ca300"},
        0x22CA300: {0x22CA32D: "lock cmpxchg byte ptr [rbx], sil"},
        0x2CA0568: {
            0x2CA0632: "lea rdx, [rsi + 0x150]",
            0x2CA0642: "mov eax, dword ptr [rsi + 0x164]",
            0x2CA066C: "mov rdx, qword ptr [rsi + 0x158]",
        },
        0xCC5844: {
            0xCC58B8: "cmp dword ptr [rdx + rcx*8 + 0xc], 0xffff",
            0xCC58E7: "lea rcx, [rdi + 0x18]",
            0xCC58EB: "call 0x1401e07bc",
        },
    }
    for function, expected in instructions.items():
        decoded = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}'
                   for row in engine.disasm(function)["instructions"]}
        for rva, command in expected.items():
            assert decoded.get(rva) == command, (hex(rva), decoded.get(rva), command)
    return instructions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=int, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    build = HERE / f"build_{args.build:02}"
    output = HERE / f"evidence_{args.attempt:02}"
    exe = build / "NativeDelayChecks.exe"
    receipt = json.loads((build / "build.json").read_bytes())
    assert digest(exe.read_bytes()) == receipt["exe_sha256"]
    assert digest((build / "NativeDelayChecks.cpp").read_bytes()) == receipt["staged_sha256"]
    paths = {
        "source": PRIOR / "NativeDelayChecks.cpp",
        "handoff": PRIOR / "RealTimeHandoff.hpp",
        "delay": PRIOR / "DelayHold.hpp",
        "observation": PRIOR / "CutoffObservation.hpp",
        "timer_record": HERE.parent / "universal_resume_boundary_20261114_01/TimerRecord.hpp",
        "owner": HERE.parent / "universal_resume_owner_20261114_01/OwnerTrace.hpp",
        "retirement": HERE / "RetiredQuestSlot.hpp",
        "checks": HERE / "RetiredQuestSlotChecks.cpp",
    }
    assert {key: digest(path.read_bytes()) for key, path in paths.items()} == receipt["sources"]

    engine = Image()
    packet, slices, prior_build = verified_slices(engine)
    for current, previous in (("source", "source"), ("handoff", "handoff"), ("delay", "header"),
                              ("observation", "cutoff"), ("timer_record", "record")):
        assert receipt["sources"][current] == prior_build[f"{previous}_sha256"]
    instructions = verify_engine(engine)

    output.mkdir(exist_ok=False)
    fixture = output / "engine_slices.bin"
    fixture.write_bytes(packet)
    run = subprocess.run([str(exe), str(fixture)], cwd=output, capture_output=True, text=True, timeout=20)
    (output / "fixture_checks.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
    print(run.stdout + run.stderr, end="")
    assert run.returncode == 0, f"Fixture exited with {run.returncode}"
    counts = re.findall(r"(?m)^(\d+) passed, 0 failed$", run.stdout)
    assert counts == [str(TIMER_CHECKS + RETIREMENT_CHECKS)], counts
    assessment = {
        "status": "ISOLATED_QUEST_SLOT_RETIREMENT_PASSED",
        "engine_sha256": engine.sha,
        "checked_instructions": instructions,
        "slices": slices,
        "fixture_sha256": digest(packet),
        "build": receipt,
        "timer_regression_checks": TIMER_CHECKS,
        "slot_retirement_checks": RETIREMENT_CHECKS,
        "game_runtime_exercised": False,
    }
    (output / "assessment.json").write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
