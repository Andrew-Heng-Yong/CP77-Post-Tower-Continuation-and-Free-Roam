"""Bind the saved race timers and run the original game-clock instructions against both."""

import argparse
from contextlib import closing
import json
import sqlite3
import struct
import subprocess

from build_save_observer import HERE, PREALPHA, VCVARS, Image, digest, pinned, require
from find_timer_fixtures import REGISTRY, component, framed, game_records, paths, phase_hash, token


def bind_fixture():
    file = HERE / "run_saves_03/PointOfNoReturnSave-0.json"
    fixture = json.loads(pinned(file, "280B48DACAD17B269F649C49CCEF505E4CD5F2655A128E94CB6672A6F53A9367"))
    require(fixture["sha256"] == "4D58810110662AB54E4FA5577274B8CA16B4C29E12F373E29F7DB05BBFAA5097",
            "Wrong original save body")
    phase = (0, 2, 82, 5, 50, 77)
    phase_id = phase_hash(phase)
    parts = fixture["components"]
    require({p for p in paths(component(parts["paths"]), parts["paths"]["id"]) if phase_hash(p) == phase_id} == {phase},
            "Race phase address absent or ambiguous")
    require(fixture["phase_registrations"] == [
        [5899, f"{token('questLogicalCondition'):016x}", phase_id, 9],
        [8690, f"{token('questGameTimeDelay_ConditionType'):016x}", phase_id, 8],
    ], "Race handlers differ from the captured rows")
    require([2] in [states for key, states in fixture["journal"] if key == 4262647041], "Race journal is not Active")

    pin = "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9"
    pinned(REGISTRY, pin)
    with closing(sqlite3.connect(REGISTRY.as_uri() + "?mode=ro", uri=True)) as db:
        depot, provider = db.execute("SELECT depot,sha256 FROM resources WHERE rid=1847 AND role='STOCK'").fetchone()
        definitions = dict(db.execute("SELECT id,parameters_json FROM nodes WHERE rid=1847 AND graph='root/77'"))
        outgoing = set(db.execute("SELECT source,source_socket,destination,destination_socket FROM edges "
                                  "WHERE rid=1847 AND graph='root/77'"))
    require(provider == "F2697033D5C1C07B2EFBBEB07EAF0907222A5B26A271063DE77409751459BE76",
            "Race phase provider changed")
    direct = json.loads(definitions[8])["condition"]["type"]
    logical = json.loads(definitions[9])["condition"]
    content, child = logical["conditions"]
    require(direct["$type"] == child["type"]["$type"] == "questGameTimeDelay_ConditionType" and
            direct["hours"] == 12 and child["type"]["hours"] == 11 and logical["operation"] == "AND" and
            content["type"]["type"] == "Fixer" and {(7, "Out", 8, "In"), (7, "Out", 9, "In"),
                                                   (8, "Out", 10, "In"), (9, "Out", 1, "In")} <= outgoing,
            "Authored race wait branch changed")

    clock, = struct.unpack_from("<I", component(parts["time_core"]), 8)
    timers = game_records(component(parts["time_timers"])[4:])
    instances = dict(struct.iter_unpack("<QQ", framed(component(parts["instances"]), parts["instances"]["id"], 16)))
    samples = []
    for key, hours in ((phase_id << 32 | 8, 12), (phase_id << 32 | (2 << 16) | 9, 11)):
        identity = instances[key]
        deadline, authored = timers[identity]
        require(0 < deadline - clock <= authored == hours * 3600, "Unexpected race duration")
        samples.append({"key": f"{key:016X}", "id": identity, "deadline": deadline, "authored": authored,
                        "remaining": deadline - clock})
    require([value["remaining"] for value in samples] == [41162, 37562], "Saved durations differ")
    return {"save_sha256": fixture["sha256"], "registry_sha256": pin, "depot": depot,
            "provider_sha256": provider, "path": phase, "clock": clock, "waits": samples}


def engine_slices():
    engine = Image()
    key_trace = {
        0x2B1B64: {0x2B1B7B: "shr eax, 0x10", 0x2B1BA6: "movzx eax, bx", 0x2B1BBA: "mov edx, ebx",
                   0x2B1BBF: "call qword ptr [rax + 0x38]"},
        0x124214C: {0x12421B6: "shl rcx, 0x20", 0x12421BA: "add rcx, rax", 0x12421BD: "mov qword ptr [r15 + 0x38], rcx"},
        0x193C74: {0x193CA7: "mov rdx, qword ptr [rsi + 0x38]", 0x193CB5: "call qword ptr [rax + 0x2c8]"},
    }
    for rva, checks in key_trace.items():
        operations = {int(row["rva"], 16): f'{row["mnemonic"]} {row["operands"]}'
                      for row in engine.disasm(rva)["instructions"]}
        require(all(operations.get(address) == operation for address, operation in checks.items()),
                f"Native key semantics changed at {rva:X}")
    baseline = PREALPHA / "universal_resume_eagles_20261114_01/evidence_17"
    packet = pinned(baseline / "native_slices.bin", "8AF0D43A09F5EDE74E5E845CCCFC9AD8AFDCB0940DF78C50C0AD31936ADABD6F")
    count, = struct.unpack_from("<I", packet)
    require(count == 32, "Unexpected native slice count")
    position = 4
    for _ in range(count):
        rva, size = struct.unpack_from("<II", packet, position)
        position += 8
        start = engine.off(rva)
        require(packet[position:position + size] == engine.data[start:start + size], "Native slice differs")
        position += size
    require(position == len(packet), "Unexpected packet bytes")
    return engine.sha, key_trace, packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", type=int, required=True, choices=range(1, 100), metavar="1–99")
    args = parser.parse_args()
    out = HERE / f"run_pair_{args.attempt:02}"
    out.mkdir()

    sample = bind_fixture()
    engine, key_checks, slices = engine_slices()
    native = out / "game_clock.bin"
    native.write_bytes(slices)
    pins = {
        PREALPHA / "universal_resume_eagles_20261114_01/GameTimeChecks.cpp":
            "F898F2D5281A04DEB4FADAFBDA15EB84605B3776B9D8A8AC0D3D7BDAE65A27A9",
        PREALPHA / "universal_resume_eagles_20261114_01/GameTimeWait.hpp":
            "C578DA6C4AE25377C48C05B74806D6DB1EE0998E235EACFE9864BAE04D553F46",
    }
    source = HERE / "PairedGameWaitChecks.cpp"
    header = out / "paired_input.hpp"
    header.write_text(
        f"constexpr std::uint32_t SavedClock = {sample['clock']};\n" +
        "".join(f"constexpr std::uint32_t {prefix}{suffix} = {wait[key]};\n"
                for prefix, wait in zip(("Direct", "Child"), sample["waits"], strict=True)
                for suffix, key in (("Id", "id"), ("Deadline", "deadline"), ("Authored", "authored"))),
        encoding="ascii",
    )
    pins.update({file: digest(file.read_bytes()) for file in (source, header)})
    for file, pin in pins.items():
        pinned(file, pin)
    (out / "build.cmd").write_text(
        f'@echo off\ncall "{VCVARS}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /I"." "{source}" /link /OUT:PairedGameWaitChecks.exe\n',
        encoding="ascii",
    )
    compiler = subprocess.run(["cmd.exe", "/d", "/c", "build.cmd"], cwd=out, capture_output=True, text=True, timeout=60)
    (out / "compile.txt").write_text(compiler.stdout + compiler.stderr, encoding="utf-8")
    print(compiler.stdout + compiler.stderr, end="")
    compiler.check_returncode()
    exe = out / "PairedGameWaitChecks.exe"
    run = subprocess.run([str(exe), str(native)], cwd=out, capture_output=True, text=True, timeout=20)
    (out / "fixture_checks.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
    print(run.stdout + run.stderr, end="")
    run.check_returncode()
    passed = sum(line.startswith("PASS ") for line in run.stdout.splitlines())
    require(passed == 10, f"Unexpected fixture check count {passed}")
    for file, pin in pins.items():
        pinned(file, pin)
    (out / "assessment.json").write_text(json.dumps({
        "status": "PAIRED_SAVED_GAME_CLOCK_WAITS_FIXTURE_PASS", "fixture": sample, "engine_sha256": engine,
        "native_key_checks": key_checks, "verified_slices": 32, "passed": passed,
        "sources": {str(file): pin for file, pin in pins.items()}, "exe_sha256": digest(exe.read_bytes()),
        "game_runtime_exercised": False,
    }, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
