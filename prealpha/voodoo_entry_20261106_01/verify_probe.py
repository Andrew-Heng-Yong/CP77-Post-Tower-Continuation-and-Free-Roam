"""Verify exact known source bindings and exercise the CET command in LuaJIT mocks."""

import hashlib
import json
import re
import struct
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parents[1]
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077")
QR15 = HERE.parent / "quest_restoration_qr15"
sys.path[:0] = [
    str(QR15 / "saved_graph_state_01"),
    str(HERE.parent / "quest_restoration_qr9/worker_b/tooling"),
]
from inspect_native import Image
from lupa.luajit21 import LuaRuntime


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest().upper()


def main():
    output = HERE / "verification.json"
    assert not output.exists()
    cmd_path = HERE / "CHECK.command.txt"
    cmd = cmd_path.read_text(encoding="utf-8").strip()
    game_pins = {
        "archive/pc/mod/zzzz_PTFR_Combined.archive": "2988A138B7AA529714BA1762A338C89D624C3C11D1C8F7449C6BF9571F216A2B",
        "archive/pc/mod/zzzz_PTFR_Combined.archive.xl": "F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245",
        "r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds": "8B62F4BA6A81AE558D88311A307934A790528875CE76A4EE751988D76664F3EC",
        "red4ext/plugins/Codeware/Codeware.dll": "808D8BCE11641073091DDA33830D06AB98BD9AC710A9A47ECD7EC56E6193440C",
        "red4ext/plugins/Codeware/Scripts/Codeware.Global.reds": "83CEBFDAF60443608ACD211B1AC6253AE6C67295BAB97275B4961506EB878A76",
        "bin/x64/plugins/cyber_engine_tweaks.asi": "ACB12B25CFCF77C3F5A84DF7CD4F4AE5074B8269E7C7389F349E12B237F88D6E",
    }
    for relative, expected in game_pins.items():
        assert sha(GAME / relative) == expected, relative
    stage = HERE.parent / "voodoo_treasure_20261106_01"
    pins = json.loads((stage / "nov06_autosave_pins.json").read_text(encoding="utf-8-sig"))
    fixture, = (row for row in pins if row["slot"] == "AutoSave-14")
    assert sha(Path(fixture["source"])) == fixture["source_sha256"]
    assert sha(Path(fixture["metadata"])) == fixture["metadata_sha256"]
    placements = json.loads((stage / "bindings_01.json").read_text(encoding="utf-8-sig"))
    door, = (row for sector in placements for row in sector["matches"] if row["ref"].endswith("/#q304_dvc_slider_stash_door"))
    assert door["global_node_id"] == "4332298668526107917"
    assert door["global_node_id"] + "ULL" in cmd and "\n" not in cmd
    assert not re.search(r"SetFact|Queue|GetConstAccessToPSObject|Teleport|Execute", cmd)
    image = Image()

    def qword(rva):
        return struct.unpack_from("<Q", image.data, image.off(rva))[0] - image.base

    assert qword(0x31C8A90 + 0xF0) == 0x2CA9AA0
    assert qword(0x3126AC0 + 0xF0) == 0x802218
    addresses = (
        0x1262ECC, 0xE71A14, 0x2CA9AA0, 0x14CB0B8, 0x802218, 0x802790,
        0x8022D0, 0x2AC4FC, 0x351030, 0x2AC524, 0x18ACEC4, 0x8138D8,
        0x21B6FC, 0x11B3EF4, 0x2FB0E4, 0x2FB150,
    )
    functions = {rva: image.disasm(rva) for rva in addresses}
    for rva in (0x14CB0B8, 0x802790):
        calls = {i["operands"] for i in functions[rva]["instructions"] if i["mnemonic"] == "call"}
        assert {"0x1402ac4fc", "0x140351030"} <= calls
    assert any(i["mnemonic"] == "call" and i["operands"] == "0x14021b6fc" for i in functions[0x8138D8]["instructions"])
    assert any(i["operands"] == "rdx, [rcx + 0x98]" for i in functions[0x2FB0E4]["instructions"])

    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute(
        r'''
        lines={}
        function print(line) lines[#lines+1]=line end
        function IsDefined(o) return o ~= nil end
        q={GetFactStr=function(_,n)
          assert(n:match("^PTFRS23_VOODOO_"))
          return n:match("_Permit$") and 1 or 0
        end}
        system={Inspect=function(_,id) assert(id=="q304_splinter_stash"); return "currentMatch=true safe=true" end}
        container={Get=function(_,id) assert(id=="PTFR.SideJobsS23.SideJobsS23"); if mode ~= "no-system" then return system end end}
        EntityID={FromHash=function(n) assert(tostring(n)=="4332298668526107917ULL"); return n end}
        Game={
          GetQuestsSystem=function() return q end,
          GetScriptableSystemsContainer=function() return container end,
          FindEntityByID=function(id)
            assert(tostring(id)=="4332298668526107917ULL")
            if mode=="error" then error("fixture error") end
            if mode=="missing" then return nil end
            return {
              IsAttached=function() return mode~="detached" end,
              GetDevicePS=function()
                if mode=="no-controller" then return nil end
                return {IsOpen=function() return mode=="open" end, IsDisabled=function() return false end}
              end
            }
          end
        }
        '''
    )
    controls = {}
    for mode, expected in {
        "closed": "Door=ATTACHED open=false disabled=false",
        "open": "Door=ATTACHED open=true disabled=false",
        "missing": "Door=UNRESOLVED",
        "detached": "Door=DETACHED",
        "no-controller": "Door=CONTROLLER_UNAVAILABLE",
        "error": "Door=ERROR ",
        "no-system": "Door=ATTACHED open=false disabled=false",
    }.items():
        lua.globals().mode = mode
        lua.execute("lines={}")
        lua.execute(cmd)
        lines = list(lua.globals().lines.values())
        assert lines[0] == "[VT01] Permit=1 Issued=0 Entered=0 Finished=0 Fault=0"
        assert lines[1].startswith("[VT01] " + expected)
        assert lines[2] == "[VT01] " + ("S23 unavailable" if mode == "no-system" else "currentMatch=true safe=true")
        controls[mode] = lines
    with output.open("x", encoding="utf-8") as stream:
        json.dump({
            "status": "READ_ONLY_PROBE_OFFLINE_VERIFIED",
            "command_sha256": sha(cmd_path), "fixture": fixture, "game_pins": game_pins,
            "exe_sha256": image.sha, "native_trace": functions, "offline_controls": controls,
            "game_api_calls": 0, "scope": "Mocks validate the command, not live CET delivery or graph predicate equivalence.",
        }, stream, indent=2)
    print(f"{len(controls)} probe controls passed")


if __name__ == "__main__":
    main()
