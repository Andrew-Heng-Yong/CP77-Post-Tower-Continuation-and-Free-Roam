"""Build and exercise the isolated wait handoff against pinned engine slices."""

import argparse
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
HANDOFF = PREALPHA / "universal_resume_handoff_20261114_01"
GAME_CLOCK = PREALPHA / "universal_resume_eagles_20261114_01"
RETIREMENT = PREALPHA / "universal_resume_retirement_20261114_01"
CHECKPOINT = PREALPHA / "universal_resume_checkpoint_probe_20261114_01"
INPUT_ID = "27f5fb2228de1ee652b9aeabde09705f"
INPUT_SLOT = 2084
INPUT_NODE = 5
INPUT_PHASE = 0x1361AA1A
INPUT_ADDRESS = [0, 2, 82, 3, 19, 17, 8, 9, 2, 63, 2]
REGISTRATION = "0e428f70b3013e89"
GAME_SLOT = 10148

sys.path.insert(0, str(PREALPHA / "quest_restoration_qr15/saved_graph_state_01"))
from inspect_native import Image


def digest(data):
    return hashlib.sha256(data).hexdigest().upper()


def pinned(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"Changed input: {path}")
    return data


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def extract_wait():
    directory = WORKSPACE / "recovery/ms26_v014_reed_checkpoint_20261114_01"
    data = pinned(directory / f"checkpoint_execution_{INPUT_ID}.json",
                  "41B2D601602926C8128A480BFDAE63DBBD90C579B5CC1779947FB042104A53E9")
    live = json.loads(data)
    assert (live["id"], live["ticket"], live["route"], live["history_revision"]) == (INPUT_ID, 1, 1, 4)
    assert [row for row in live["handlers"] if row[0] == INPUT_SLOT] == [
        [INPUT_SLOT, REGISTRATION, INPUT_PHASE, INPUT_NODE, 1]
    ]
    assert [row[3] for row in live["phases"] if row[0] == INPUT_PHASE] == [INPUT_ADDRESS]
    timed, = [row for row in live["timings"] if row[0] == INPUT_SLOT]
    _, clock, timer, seconds, age = timed
    assert clock == 0 and 0 < seconds < 10

    registry = PREALPHA / "quest_resume_registry_20261112_01/registry_02/registry.sqlite3"
    with registry.open("rb") as handle:
        registry_hash = hashlib.file_digest(handle, "sha256").hexdigest().upper()
    assert registry_hash == "BE073251F63739E1C77B094B43DEF0DBCC3059549ACFEDC7F091BF4FAD7195C9"
    graph = "root/9/2/63/2"
    with sqlite3.connect(registry.resolve().as_uri() + "?mode=ro", uri=True) as db:
        depot, provider, role = db.execute(
            "SELECT depot, sha256, role FROM resources WHERE rid=8992"
        ).fetchone()
        definition, = db.execute(
            "SELECT parameters_json FROM nodes WHERE rid=8992 AND graph=? AND id=?", (graph, INPUT_NODE)
        ).fetchone()
    assert role == "STOCK"
    assert provider == "DC7393185B973C640BD66A31231D4BB24B14706AE27683E17AD7C8E010067527"
    delay = json.loads(definition)["condition"]["type"]
    assert delay == {"$type": "questRealtimeDelay_ConditionType", "hours": 0, "minutes": 0,
                     "seconds": 10, "miliseconds": 0}
    clock_type = "a384ad807139cf67"
    assert [row for row in live["handlers"] if row[0] == GAME_SLOT] == [
        [GAME_SLOT, clock_type, 0xCCF9887E, 80, 1]
    ]
    _, game_clock, game_timer, game_seconds, game_age = next(row for row in live["timings"] if row[0] == GAME_SLOT)
    assert game_clock == 1 and game_seconds == 170486
    game_evidence = json.loads(pinned(RETIREMENT / "wait_fixture_01/assessment.json",
                                      "9C65B82C44BDFA9F8933ABC190882CAAD760DE9D49692B7A43FA2D490AE8A2B0"))
    game_authored = game_evidence["sample"]["authored_game_seconds"]
    assert game_authored == 172800 and game_evidence["sample"]["node_key"] == "CCF9887E00000050"
    return {"checkpoint_sha256": digest(data), "id": INPUT_ID, "ticket": live["ticket"], "route": live["route"],
            "registry_sha256": registry_hash, "depot": depot, "provider_sha256": provider, "graph": graph,
            "address": INPUT_ADDRESS, "node": INPUT_NODE, "physical_slot": INPUT_SLOT,
            "registration_type": REGISTRATION, "timer_id": timer, "seconds": seconds, "sample_age_ms": age,
            "authored_seconds": delay["seconds"],
            "game_wait": {"source": "Where Eagles Dare pending reply, fixture only", "physical_slot": GAME_SLOT,
                          "timer_id": game_timer, "seconds": game_seconds, "authored_seconds": game_authored,
                          "sample_age_ms": game_age}}


def write_header(path, wait):
    address = ", ".join(map(str, wait["address"]))
    provider = ", ".join(f"0x{value:02X}" for value in bytes.fromhex(wait["provider_sha256"]))
    checkpoint = ", ".join(f"'{value}'" for value in wait["id"])
    game = wait["game_wait"]
    path.write_text(
        f"constexpr ptfr::resume::WaitAddress FixtureAddress{{"
        f"{{{{{address}}}, {len(wait['address'])}}}, {{{provider}}}, "
        f"0x{wait['registration_type']}, {wait['node']}}};\n"
        f"constexpr ptfr::resume::EndingCheckpoint FixtureEnding{{"
        f"{{{checkpoint}}}, 1, {wait['ticket']}, {wait['route']}}};\n",
        encoding="ascii",
    )
    with path.open("a", encoding="ascii") as header:
        header.write(
            f"constexpr std::uint32_t FixtureGameTimer = {int(game['timer_id'], 16)};\n"
            f"constexpr std::uint32_t FixtureGameRemaining = {game['seconds']};\n"
            f"constexpr std::uint32_t FixtureGameAuthored = {game['authored_seconds']};\n"
        )


def verify_packet(prior, wait):
    engine = Image()
    assert engine.sha == prior["engine_sha256"]
    packet = bytearray(pinned(RETIREMENT / "evidence_05/engine_slices.bin",
                              "935F83671263C262A562DD0055E8EBFD41E5C46F9AAF179FF7A50AAD360D4328"))
    assert struct.unpack_from("<I", packet)[0] == len(prior["slices"]) == 76
    offset = struct.calcsize("<IQf")
    for expected in prior["slices"].values():
        rva, size = struct.unpack_from("<II", packet, offset)
        offset += 8
        assert (rva, size) == (int(expected["rva"], 16), expected["length"])
        engine_offset = engine.off(rva)
        data = packet[offset:offset + size]
        assert data == engine.data[engine_offset:engine_offset + size]
        assert digest(data) == expected["sha256"]
        offset += size
    assert offset == len(packet)
    struct.pack_into("<Qf", packet, 4, int(wait["timer_id"], 16), wait["seconds"])

    clock_evidence = GAME_CLOCK / "evidence_17"
    clock = json.loads(pinned(clock_evidence / "clock_assessment.json",
                              "C5D63D42D6AEF033CD2B8B88ED2964A1BD2221E3F1E9225C80787AE63FB26056"))
    clock_packet = pinned(clock_evidence / "native_slices.bin",
                           "8AF0D43A09F5EDE74E5E845CCCFC9AD8AFDCB0940DF78C50C0AD31936ADABD6F")
    assert clock["native_sha256"] == engine.sha
    assert struct.unpack_from("<I", clock_packet)[0] == len(clock["slice_hashes"]) == 32
    offset = 4
    for rva_text, expected_hash in clock["slice_hashes"].items():
        rva, size = struct.unpack_from("<II", clock_packet, offset)
        offset += 8
        data = clock_packet[offset:offset + size]
        engine_offset = engine.off(rva)
        assert rva == int(rva_text, 16) and digest(data) == expected_hash
        assert data == engine.data[engine_offset:engine_offset + size]
        offset += size
    assert offset == len(clock_packet)
    return engine.sha, packet, clock_packet


def verify_sources(prior):
    files = {
        "source": HANDOFF / "NativeDelayChecks.cpp",
        "handoff": HANDOFF / "RealTimeHandoff.hpp",
        "delay": HANDOFF / "DelayHold.hpp",
        "observation": HANDOFF / "CutoffObservation.hpp",
        "timer_record": PREALPHA / "universal_resume_boundary_20261114_01/TimerRecord.hpp",
        "owner": PREALPHA / "universal_resume_owner_20261114_01/OwnerTrace.hpp",
        "retirement": RETIREMENT / "RetiredQuestSlot.hpp",
        "checks": RETIREMENT / "RetiredQuestSlotChecks.cpp",
        "staged": RETIREMENT / "build_05/NativeDelayChecks.cpp",
        "clock_source": GAME_CLOCK / "GameTimeChecks.cpp",
        "clock_header": GAME_CLOCK / "GameTimeWait.hpp",
    }
    hashes = prior["build"]["sources"] | {
        "staged": prior["build"]["staged_sha256"],
        "clock_source": "F898F2D5281A04DEB4FADAFBDA15EB84605B3776B9D8A8AC0D3D7BDAE65A27A9",
        "clock_header": "C578DA6C4AE25377C48C05B74806D6DB1EE0998E235EACFE9864BAE04D553F46",
    }
    for name, path in files.items():
        pinned(path, hashes[name])
    for path in (CHECKPOINT / "source_02/Checkpoint.hpp", HERE / "WaitTransfer.hpp",
                 HERE / "WaitTransferChecks.cpp", Path(__file__)):
        files[path.name] = path
        hashes[path.name] = digest(path.read_bytes())
    return files, hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("attempt", type=int)
    args = parser.parse_args()
    if not 1 <= args.attempt <= 99:
        parser.error("choose a fresh attempt in 1..99")
    out = HERE / f"run_{args.attempt:02}"
    out.mkdir()

    prior = json.loads(pinned(RETIREMENT / "evidence_05/assessment.json",
                              "B82CC608A66F4A6B917081ADFE0A449F37A35AA13BF5AE04E44F68A4A2A8CC23"))
    files, hashes = verify_sources(prior)
    wait = extract_wait()
    engine_sha, packet, clock_packet = verify_packet(prior, wait)
    slices = out / "engine_slices.bin"
    slices.write_bytes(packet)
    clock_slices = out / "game_clock_slices.bin"
    clock_slices.write_bytes(clock_packet)
    header = out / "fixture_input.hpp"
    write_header(header, wait)
    hashes[header.name] = digest(header.read_bytes())

    vcvars = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat")
    if not vcvars.is_file():
        raise ValueError(f"Missing MSVC initializer: {vcvars}")
    (out / "build.cmd").write_text(
        f'@echo off\ncall "{vcvars}" >nul\nif errorlevel 1 exit /b 1\n'
        f'cl.exe /nologo /std:c++20 /W4 /WX /O2 /EHsc /MT /I"." /I"{HANDOFF}" '
        f'"{HERE / "WaitTransferChecks.cpp"}" /link /OUT:WaitTransferChecks.exe\n', encoding="ascii",
    )
    build = subprocess.run(["cmd.exe", "/d", "/c", "build.cmd"], cwd=out, check=False,
                           capture_output=True, text=True, errors="replace")
    (out / "build.txt").write_text(build.stdout + build.stderr, encoding="utf-8")
    print(build.stdout + build.stderr, end="")
    build.check_returncode()
    for name, path in files.items():
        pinned(path, hashes[name])
    pinned(header, hashes[header.name])
    executable = out / "WaitTransferChecks.exe"
    run = subprocess.run([str(executable), str(slices), str(clock_slices)], cwd=out,
                         capture_output=True, text=True, errors="replace", timeout=30)
    (out / "fixture_checks.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
    print(run.stdout + run.stderr, end="")
    passed = sum(line.startswith("PASS ") for line in run.stdout.splitlines())
    write_json(out / "assessment.json",
               {"status": "PASS" if run.returncode == 0 and passed else "FAIL", "wait": wait,
                "game_runtime_exercised": False, "engine_sha256": engine_sha, "verified_engine_slices": [76, 32],
                "fixture_sha256": digest(packet), "game_clock_fixture_sha256": digest(clock_packet),
                "sources": hashes, "exe_sha256": digest(executable.read_bytes()),
                "passed": passed, "exit_code": run.returncode})
    if not passed:
        raise RuntimeError("No fixture checks executed")
    run.check_returncode()


if __name__ == "__main__":
    main()
