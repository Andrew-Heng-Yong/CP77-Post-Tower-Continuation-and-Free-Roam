"""Build the save guard successor against the native dispatcher session."""

import argparse
import json
from pathlib import Path
import re
import struct
import sys


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "universal_resume_save_admission_20261115_01"
NATIVE = PRIOR / "run_01/NativeCheckpoint.cpp"
INSTALLED = PRIOR / "deployment_01/installed_manifest_01.json"
ASSESSMENT = PRIOR / "run_01/assessment.json"

sys.path.insert(0, str(PRIOR))
from build_save_admission import (BASE, Image, PINS, WORKSPACE, compile_candidate, digest, pinned,
                                  record_compile_inputs, require, run_checks, verify_engine)


def replace(source, before, after):
    require(source.count(before) == 1, f"Changed source anchor: {before}")
    return source.replace(before, after)


def revise_source(source):
    replacements = (
        ("std::atomic<bool> hooksReady{};",
         "std::atomic<bool> hooksReady{};\nstd::atomic<bool> saveAdmissionProbeRequested{};"),
        ("        gate.BeginTransition();",
         "        gate.BeginTransition();\n        saveAdmissionProbeRequested.store(false);"),
        ("    capture.epoch = gate.Epoch();\n    return true;",
         "    capture.epoch = gate.Epoch();\n    if (probe)\n        saveAdmissionProbeRequested.store(true);\n    return true;"),
        ('            const auto handoffReady = static_cast<bool>(TryBeginNativeHandoff());\n'
         '            sdk->logger->InfoF(plugin, "PTFR native save handoff admission: %s",\n'
         '                               handoffReady ? "idle" : "deferred");\n', ""),
        ("image + GameEngine, 0x140", "image + SaveSessionVtable, 0x140"),
        ("RED4EXT_V1_SEMVER(0, 1, 6)", "RED4EXT_V1_SEMVER(0, 1, 7)"),
    )
    for old, new in replacements:
        source = replace(source, old, new)
    return source


def verify_session(root):
    engine = Image()
    table = root / "bin/x64/cyberpunk2077_addresses.json"
    table_sha = "EAB304F38074145AB5EF53E2AA741576BA00674138761FAFFF23252005948FD4"
    data = pinned(table, table_sha)
    match = re.search(rb'\{"hash": "2549221846"[^{}]*\}', data)
    require(match is not None and json.loads(match[0])["offset"] == "0003:002bcb38",
            "RED4ext CGameEngine binding changed")
    data_rva = next(rva for name, rva, _, _ in engine.sections if name == ".data")
    require(data_rva + 0x2BCB38 == 0x3BBFB38, "CGameEngine singleton slot moved")

    owners = (
        ("gsmState_Session", 0x3283678, 0x30C3790, 0x19606F0, 0x3BCD678, 0x3CC094, 0x16550F0),
        ("gsmState_PreGameSession", 0x3283570, 0x3229740, 0x1960710, 0x3BCD688, 0xF64074, 0x1654F84),
        ("CGameEngine", 0x3029808, 0x36DCB00, 0x1960D90, 0x3BCD798, 0x878B80, 0x15BB188),
    )
    for name, string, vtable, type_reader, class_slot, update, registration in owners:
        prefix = name.encode("ascii") + b"\0"
        start = engine.off(string)
        require(engine.data[start:start + len(prefix)] == prefix, f"Changed type name: {name}")
        for slot, method in ((0, type_reader), (0x140, update)):
            address, = struct.unpack_from("<Q", engine.data, engine.off(vtable + slot))
            require(address == engine.base + method, f"Changed vtable {name} at {slot:X}")
        reader = engine.disasm(type_reader)["instructions"][0]
        blob = bytes.fromhex(reader["bytes"])
        require(blob[:3] == b"\x48\x8b\x05" and type_reader + 7 + struct.unpack_from("<i", blob, 3)[0] == class_slot,
                f"Changed type reader: {name}")
        references = {}
        for row in engine.disasm(registration)["instructions"]:
            blob = bytes.fromhex(row["bytes"])
            if blob[:3] in (b"\x48\x8d\x15", b"\x48\x89\x3d"):
                target = int(row["rva"], 16) + len(blob) + struct.unpack_from("<i", blob, 3)[0]
                references[target] = row["mnemonic"]
        require(references.get(string) == "lea" and references.get(class_slot) == "mov",
                f"Changed class registration: {name}")
    for entry, source, jump in ((0xF64074, 0xF640A1, "0x1403cc094"),
                                (0x258DAEA, 0x258DB18, "0x140f64091")):
        expected = ("jmp", jump)
        rows = {int(row["rva"], 16): (row["mnemonic"], row["operands"])
                for row in engine.disasm(entry)["instructions"]}
        require(rows.get(source) == expected, "Pre-game session no longer delegates to the session dispatcher")
    return {"address_table_sha256": table_sha, "sdk_singleton_slot": "03BBFB38",
            "owners": {name: {"vtable": f"{vtable:08X}", "update": f"{update:08X}"}
                       for name, _, vtable, _, _, update, _ in owners}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=int, choices=range(1, 100), metavar="1–99")
    out = HERE / f"run_{parser.parse_args().attempt:02}"
    out.mkdir()

    pins = PINS | {
        NATIVE: "985BA498D5EEC1DC3F179160C691CD9176E0E0F1144DF2673A824777A9ED0E49",
        INSTALLED: "7971F2E6AE7AF81E3B276FCBDDDD2DD0C25DB42069FAEE30000CE6DE92B16636",
        ASSESSMENT: "5628381E92033F72738C9FE00ECA84F17EE7ECA090F53FBFA5DFB9CC1E273173",
        PRIOR / "SaveAdmission.hpp": "F9288E0F4A6B1CE6845FFAAE2372C126C0447AB6DDECDE81D1CB23A0EC17233E",
        PRIOR / "SaveAdmissionChecks.cpp": "5BC802F85E4CFA880B33EB19D6ED284AD06E0E4924B0C89FDF7E33EB4980A4AE",
        PRIOR / "build_save_admission.py": "C297F3030E1A10501B3AE45885B91A57C6EA09073FAAD62690498E50BBD34AF9",
    }
    inputs = {path: pinned(path, sha) for path, sha in pins.items()}
    baseline = json.loads(inputs[INSTALLED])
    root = Path(baseline["game_root"])
    groups = ("core_files", "companion_files", "required_files")
    for group in groups:
        for row in baseline[group]:
            pinned(root / row["path"], row["sha256"])
    target, = baseline["companion_files"]
    require(target["sha256"] == json.loads(inputs[ASSESSMENT])["target"]["candidate_sha256"],
            "Installed v0.1.6 differs from the observed candidate")
    engine = verify_engine()
    engine["session"] = verify_session(root)

    native = out / "NativeCheckpoint.cpp"
    native.write_text(revise_source(inputs[NATIVE].decode("utf-8-sig").replace("\r\n", "\n")), encoding="utf-8")
    fixture = out / "CheckpointChecks.cpp"
    fixture_text = inputs[BASE / "source_02/CheckpointChecks.cpp"].decode("utf-8-sig").replace("\r\n", "\n")
    fixture.write_text(replace(fixture_text, "    if (check.failures)",
                               '#include "SessionProbeChecks.inc"\n    if (check.failures)'), encoding="utf-8")
    for name in ("NativeSaveAdmission.inc", "SessionProbeChecks.inc"):
        new = HERE / name
        staged = out / name
        staged.write_bytes(new.read_bytes())
        pins[new] = pins[staged] = digest(staged.read_bytes())
    for path in (native, fixture, Path(__file__)):
        pins[path] = digest(path.read_bytes())

    compile_candidate(out)
    counts = record_compile_inputs(out)
    checks = {name: run_checks(out, name, count) for name, count in (
        ("SaveAdmissionChecks", 12), ("CheckpointChecks", 60), ("RegistrationChecks", 15)
    )}
    for path, sha in pins.items():
        pinned(path, sha)
    dll = out / Path(target["path"]).name
    report = {
        "status": "WORKSPACE_SESSION_SAVE_ADMISSION_BUILD_AND_FIXTURES_PASS",
        "game_runtime_exercised": False, "mutating_handoff_enabled": False,
        "engine": engine,
        "verified_baseline": {group: len(baseline[group]) for group in groups},
        "compile_input_counts": counts,
        "compile_inputs_sha256": digest((out / "compile_inputs.json").read_bytes()),
        "sources": {path.relative_to(WORKSPACE).as_posix(): sha for path, sha in pins.items()},
        "checks": checks,
        "target": {"path": target["path"], "previous_sha256": target["sha256"],
                   "candidate_sha256": digest(dll.read_bytes()), "bytes": dll.stat().st_size},
    }
    (out / "assessment.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
