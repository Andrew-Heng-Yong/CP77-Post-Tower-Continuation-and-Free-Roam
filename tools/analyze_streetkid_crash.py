"""Verify the actor-index fault against both local S2/S3 minidumps.

Build-specific offsets are from Cyberpunk 2.31's fault and caller disassembly.
This does not export heap contents or claim a symbolized call stack.
"""
import json
from pathlib import Path
import struct
from inspect_native_crash import Dump

ROOT = Path(__file__).resolve().parent.parent
REPORTS = Path(r"C:\Users\Ayong\AppData\Local\REDEngine\ReportQueue")


def analyze(name):
    d = Dump(REPORTS / name / "Cyberpunk2077.dmp")
    report = d.report()
    assert report["fault"] == "Cyberpunk2077.exe+0x545d0b"
    assert report["exception_parameters"] == ["0x0", "0x34"]
    r = {k: int(v, 16) for k, v in report["registers"].items()}
    store = d.read(r["r12"], 0x30)
    count = struct.unpack_from("<I", store, 0x14)[0]
    player_base = struct.unpack_from("<Q", store, 0x18)[0]
    player_count = struct.unpack_from("<I", store, 0x24)[0]
    index, remainder = divmod(r["r15"] - player_base, 0xB0)
    assert remainder == 0
    slot = d.read(r["r15"], 0x10)
    definition = struct.unpack_from("<Q", slot, 8)[0]
    valid_definition = struct.unpack("<Q", d.read(player_base + 8, 8))[0]
    valid_actor_id = struct.unpack("<I", d.read(valid_definition, 4))[0]
    assert (count, player_count, index, definition, valid_actor_id) == (2, 1, 1, 0, 3)
    assert r["r8"] == 0x28 and r["rbx"] == 0
    return {"report": name, "fault_rva": "0x545d0b", "ordinary_actor_count": count,
            "player_count": player_count, "requested_player_index": index,
            "player_definition_actor_id": valid_actor_id,
            "out_of_bounds_definition_is_null": definition == 0,
            "fault": "NULL player definition + 0x28 + 0x0c -> read 0x34",
            "repair": "player actorId3 ->2; packed actor performer769 ->513"}


def main():
    result = {"status": "MATCHED_BOTH_DUMPS", "build_specific": "Cyberpunk 2.31 / P4CL9778208",
              "crashes": [analyze(n) for n in (
                  "Cyberpunk2077-20260925-234522-36088-39172",
                  "Cyberpunk2077-20260926-001324-28428-11624")],
              "instructions": [
                  "0x74d1da: compare actorId with ordinary actor count",
                  "0x74d1e3: subtract ordinary actor count",
                  "0x74d1e8: index player entries by stride 0xb0",
                  "0x74d210: load definition from slot+8",
                  "0x12259c1: add definition +0x28",
                  "0x545d0b: cmp dword ptr [r8+0xc],0"],
              "limitation": "Fixes this reproduced native fault; seating/action/return still require live validation."}
    path = ROOT / "research/b0_streetkid_scene_load_s3/crash_actor_index_evidence.json"
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
