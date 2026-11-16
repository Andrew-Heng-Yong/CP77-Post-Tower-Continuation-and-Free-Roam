"""Check the pinned engine and the compiled probe using read-only saved evidence."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image

INPUTS = HERE.parent / "universal_resume_20261114_01/evidence_04"
FIXTURE_KEY = "1361AA1A00000005"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def verify_engine(image):
    source = (HERE / "TimerProbe.cpp").read_text()
    executable_guard = re.search(r"constexpr std::uint8_t expected\[\] = \{([^}]+)\}", source)[1]
    assert bytes(int(word, 16) for word in re.findall(r"0x[0-9A-F]{2}", executable_guard)).hex().upper() == image.sha
    hooks = re.findall(r'MakeHook\((0x[0-9A-F]+), "([^"]+)", &(\w+),', source)
    assert len(hooks) == 8
    result = {}
    for rva_text, escapes, name in hooks:
        rva = int(rva_text, 16)
        prefix = bytes.fromhex(escapes.replace("\\x", ""))
        offset = image.off(rva)
        assert len(prefix) == 8 and image.data[offset:offset + 8] == prefix, name
        result[name] = {"rva": hex(rva), "prefix": prefix.hex()}

    vtables = (
        (0x31267A0, 0x10, 0x1948BC),
        (0x31267A0, 0x20, 0x194828),
        (0x30A2A90, 0x120, 0x35BCE4),
        (0x30A2A90, 0x138, 0x2AAC958),
        (0x30A2A90, 0x148, 0x1133B2C),
        (0x30A2A90, 0x1C8, 0x1AA1A0),
        (0x30A2A90, 0x1D0, 0x7C7278),
        (0x30A2A90, 0x1D8, 0x193A1C),
        (0x3695E40, 0x10, 0x1304ED8),
        (0x3695E70, 0x10, 0x1304ED8),
        (0x3699F88, 0x130, 0x2B33F0),
    )
    for table, slot, target in vtables:
        assert struct.unpack_from("<Q", image.data, image.off(table + slot))[0] == image.base + target

    checks = {
        0x2B26A4: {0x2B2745: "movups xmm0, xmmword ptr [rax + rcx*8]",
                   0x2B2778: "call 0x1402b1bc4"},
        0x156EFD0: {0x156EFFE: "mov byte ptr [rdi + rdx], al", 0x156F001: "call 0x1402b32b0"},
        0x2B32B0: {0x2B3328: "mov r8b, 2", 0x2B3343: "call 0x1402b30a0",
                   0x2B3365: "call qword ptr [rax + 0x130]"},
        0x2B33F0: {0x2B341F: "add r10, qword ptr [rcx + 0x88]",
                   0x2B3426: "mov rax, qword ptr [r10]"},
        0x2B0800: {0x2B0835: "cmp byte ptr [rdx + 1], 2", 0x2B084B: "call 0x14079cf00",
                   0x2B0855: "je 0x1402b08bf", 0x2B085E: "mov dword ptr [rax + 0x28], edx",
                   0x2B08A4: "jmp qword ptr [rax + 0x10]", 0x2B08B6: "call 0x140eb6b3c",
                   0x2B08D3: "jmp 0x1402b08ab"},
        0x194828: {0x194868: "call qword ptr [rax + 0x2c0]",
                   0x194889: "mov rdi, qword ptr [rax + 0x1d0]", 0x1948A2: "call rdi"},
        0x1948BC: {0x1948ED: "mov rdx, qword ptr [rsi + 0x38]",
                   0x1948FB: "call qword ptr [rax + 0x2c8]", 0x194907: "jne 0x1401949a8",
                   0x194914: "mov rdi, qword ptr [rax + 0x1c8]",
                   0x194920: "movss xmm3, dword ptr [rsi + 0x48]",
                   0x194959: "mov dword ptr [rsp + 0x20], 4", 0x194961: "call rdi",
                   0x19496A: "mov qword ptr [rsi + 0x40], rdx", 0x194981: "shl r8, 0x20",
                   0x19498B: "call qword ptr [rax + 0x2b8]",
                   0x1949C4: "mov rdi, qword ptr [rax + 0x1d8]", 0x1949FA: "call rdi",
                   0x194A09: "jne 0x140194991", 0x194A0B: "mov dl, 1", 0x194A10: "call 0x14088b6ac"},
        0x193A1C: {0x193A7C: "call 0x14217a590", 0x193A9E: "cmp al, 1",
                   0x193ACB: "call 0x140193b54"},
        0x1304ED8: {0x1304ED8: "mov rcx, qword ptr [rcx + 8]", 0x1304EDC: "mov dl, 1",
                    0x1304EDE: "jmp 0x14088b6ac"},
        0x7C7278: {0x7C72C0: "mov qword ptr [r8 + r10*8 + 0x49988], rdx"},
        0x35BCE4: {0x35BD91: "call 0x14035bec8", 0x35BDC4: "call 0x1401aa58c",
                   0x35BDFE: "lock cmpxchg qword ptr [rbx + 0x519c0], rcx"},
        0x1AA46C: {0x1AA4B7: "call 0x1401aa8b8", 0x1AA4D7: "jne 0x1401aa560",
                   0x1AA4F0: "call 0x1401aa634", 0x1AA576: "call 0x142aacd4c",
                   0x1AA582: "call 0x1401aa7d0", 0x1AA587: "jmp 0x1401aa4cf"},
        0x1AA7D0: {0x1AA82B: "cmp dword ptr [rbx + 0x30], eax",
                   0x1AA858: "addss xmm0, dword ptr [rcx + 0x38]",
                   0x1AA895: "call 0x1401aa3a8"},
        0x1AA3A8: {0x1AA423: "dec dword ptr [rbx + 0xc008]",
                   0x1AA449: "call 0x140195798"},
        0x1AA634: {0x1AA71A: "movss xmm0, dword ptr [rax + 0x38]",
                   0x1AA73E: "call qword ptr [rax + 0xd8]", 0x1AA77F: "call 0x1401aa7d0"},
        0x2AAC3D4: {0x2AAC43D: "jne 0x142aac47a", 0x2AAC451: "mov byte ptr [rsp + 0x3c], al",
                    0x2AAC465: "addss xmm0, dword ptr [rax + 0x38]",
                    0x2AAC46A: "movss dword ptr [rsp + 0x38], xmm0", 0x2AAC48B: "mov rax, rbx"},
        0x2AAC958: {0x2AACA81: "call 0x142aac3d4", 0x2AACA86: "mov eax, dword ptr [rsp + 0x5c]",
                    0x2AACAA3: "mov rax, qword ptr [rsp + 0x50]", 0x2AACAAD: "shl r14, 4"},
        0x1133B2C: {0x1133CF3: "cmp al, 1", 0x1133D27: "mov qword ptr [rax + 0x30], rcx",
                    0x1133D33: "mov dword ptr [rax + 0x38], ecx", 0x1133D42: "call 0x1401aa8b8"},
        0x1AA8B8: {0x1AA8F6: "cmp dword ptr [r9 + 0xc058], 0x800", 0x1AA931: "subss xmm0, xmm1",
                   0x1AA953: "call 0x1401aa2d0", 0x1AA969: "call 0x140ee2ca0"},
    }
    matching_instructions = []
    for function, expected in checks.items():
        decoded = {int(row["rva"], 16): row for row in image.disasm(function)["instructions"]}
        for rva, instruction in expected.items():
            row = decoded[rva]
            assert f'{row["mnemonic"]} {row["operands"]}' == instruction, row
            matching_instructions.append(row)
    return {"hooks": result, "vtable_slots": [[hex(value) for value in row] for row in vtables],
            "instructions": matching_instructions}


def read_fixture(image):
    capture_path = INPUTS / "timers.json"
    binding_path = INPUTS / "timer_binding.json"
    assert digest(capture_path) == "305FD3544FD009F91E90CB2F911130C3B09CC83EAC2C8D5F74E661F389F528FA"
    assert digest(binding_path) == "9BE96664F8F76BFF8E101A9EE76382AB505F336EC171F079F22059DF2E0DAA2C"
    capture = json.loads(capture_path.read_text())
    bindings = json.loads(binding_path.read_text())
    assert bindings["engine_sha256"] == image.sha and bindings["save_sha256"] == capture["source_sha256"]
    assert bindings["timer_capture_sha256"] == digest(capture_path)
    fixture, = (row for row in bindings["direct_delay_bindings"] if row["node_key"] == FIXTURE_KEY)
    assert f"ObservedNode = 0x{FIXTURE_KEY}" in (HERE / "TimerProbe.cpp").read_text()
    delay_bytes = bytes.fromhex(capture["components"]["delay_structs"]["hex"])
    assert struct.unpack_from("<5I", delay_bytes) == (24, 4, 0, 0, 9)
    assert len(delay_bytes) == 20 + 9 * 13 + 4 and delay_bytes[-4:] == bytes(4)
    rows = []
    for kind, serial, group, remaining in struct.iter_unpack("<BIIf", delay_bytes[20:-4]):
        if f"{serial:08X}{group:08X}" == fixture["timer_id"]:
            assert remaining == fixture["remaining_real_seconds"] and group == 4 and kind == 1
        rows.append(struct.pack("<IIfB3x", serial, group, remaining, kind))
    return fixture, b"".join(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", type=int, required=True)
    parser.add_argument("--attempt", type=int, required=True)
    args = parser.parse_args()
    build = HERE / f"build_{args.build:02d}"
    out = HERE / f"evidence_{args.attempt:02d}"
    assert not out.exists(), "Evidence directory already exists"
    image = Image()
    engine = verify_engine(image)
    fixture, row_bytes = read_fixture(image)
    manifest = json.loads((build / "build.json").read_text())
    artifacts = {
        "source_sha256": HERE / "TimerProbe.cpp",
        "timer_record_sha256": HERE / "TimerRecord.hpp",
        "checks_source_sha256": HERE / "TimerRecordChecks.cpp",
        "dll_sha256": build / "PTFR_QuestTimerProbe.dll",
        "checks_sha256": build / "TimerRecordChecks.exe",
    }
    assert all(digest(path) == manifest[key] for key, path in artifacts.items())
    exports = re.findall(r"(?m)^\s*\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\w+)\s*$", (build / "exports.txt").read_text())
    assert exports == ["Main", "Query", "Supports"]
    imports = re.findall(r"(?mi)^    ([\w.]+\.dll)\s*$", (build / "dependencies.txt").read_text())
    assert {name.lower() for name in imports} == {"bcrypt.dll", "kernel32.dll"}
    out.mkdir()
    input_path = out / "timer_rows.bin"
    input_path.write_bytes(row_bytes)
    fixture_run = subprocess.run([str(artifacts["checks_sha256"]), str(input_path)],
                                 cwd=out, text=True, capture_output=True, check=True)
    assert "15 passed, 0 failed" in fixture_run.stdout, fixture_run.stdout
    (out / "fixture_checks.txt").write_text(fixture_run.stdout, encoding="utf-8")
    result = {
        "status": "NATIVE_PROBE_OFFLINE_CHECKS_PASSED",
        "engine_sha256": image.sha,
        "fixture": fixture,
        "fixture_rows_sha256": digest(input_path),
        "engine_checks": engine,
        "build": manifest,
        "exports": exports,
        "imports": imports,
        "runtime_exercised": False,
        "game_writes": 0,
        "save_writes": 0,
    }
    (out / "assessment.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f'{len(engine["hooks"])} hook prefixes, {len(engine["vtable_slots"])} vtable slots, '
          f'{len(engine["instructions"])} instructions and 15 fixture checks passed')


if __name__ == "__main__":
    main()
