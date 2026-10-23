"""Execute PA1's actual diagnostics API under LuaJIT with strict getter mocks."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime

SOURCE = ROOT / "prealpha/cet/init.lua"
TEXT = SOURCE.read_text(encoding="utf-8-sig")
OUT = ROOT / "research/pre_alpha_clean/entry"
METHODS = {
    "Status": ("PTFR.ActivityStateR3.PreAlphaEntry", "Status", []),
    "Arrival": ("PTFR.ActivityStateR3.PreAlphaArrivalPA1", "Status", []),
    "Gigs": ("PTFR.ActivityStateR3.NativeGigsU9", "InspectAll", []),
    "Gig": ("PTFR.ActivityStateR3.NativeGigsU9", "Inspect", ["sts_hey_rey_06"]),
    "Entry": ("PTFR.ActivityStateR3.PreAlphaEntry", "InspectAll", []),
    "Phone": ("PTFR.ActivityStateR3.GigPhoneU9", "Inspect", []),
    "Profile": ("PTFR.RestrictionsR3.ProfilePolicy", "GetStatus", []),
}
SCRIPT_PATHS = {
    "PTFR.ActivityStateR3.PreAlphaEntry": ROOT / "prealpha/entry/scripts/PreAlphaEntry.reds",
    "PTFR.ActivityStateR3.PreAlphaArrivalPA1": ROOT / "prealpha/arrival/scripts/PreAlphaArrivalPA1.reds",
    "PTFR.ActivityStateR3.NativeGigsU9": ROOT / "prealpha/entry/scripts/NativeGigsU9.reds",
    "PTFR.ActivityStateR3.GigPhoneU9": ROOT / "prealpha/phone/scripts/GigPhoneU9.reds",
    "PTFR.RestrictionsR3.ProfilePolicy": ROOT / "prealpha/entry/scripts/ProfilePolicy.reds",
}

MOCK = r'''
reads, calls, writes = {}, {}, {}
mode, generation = "ready", 1
local expected = {
  ["PTFR.ActivityStateR3.PreAlphaEntry"] = { Status = 0, InspectAll = 0 },
  ["PTFR.ActivityStateR3.PreAlphaArrivalPA1"] = { Status = 0 },
  ["PTFR.ActivityStateR3.NativeGigsU9"] = { Inspect = 1, InspectAll = 0 },
  ["PTFR.ActivityStateR3.GigPhoneU9"] = { Inspect = 0 },
  ["PTFR.RestrictionsR3.ProfilePolicy"] = { GetStatus = 0 }
}
local function forbidden(name)
  return function(...) writes[#writes + 1] = name; error("Unexpected mutation: " .. name) end
end
registerForEvent = forbidden("registerForEvent")
registerHotkey = forbidden("registerHotkey")
Observe = forbidden("Observe")
Override = forbidden("Override")
Game = {
  SetFactValue = forbidden("SetFactValue"),
  AddToInventory = forbidden("AddToInventory"),
  GetTeleportationFacility = forbidden("GetTeleportationFacility"),
  GetScriptableSystemsContainer = function()
    if mode == "container_error" then error("loading container") end
    if mode == "no_container" then return nil end
    return { Get = function(_, name)
      reads[#reads + 1] = name
      if mode == "lookup_error" then error("loading system") end
      if mode == "no_system" then return nil end
      assert(expected[name], "Unexpected system: " .. name)
      local instance = { generation = generation }
      return setmetatable(instance, { __index = function(_, method)
        if mode == "index_error" then error("RTTI lookup") end
        if mode == "no_method" then return nil end
        if mode == "wrong_method_type" then return 41 end
        local argc = expected[name][method]
        assert(argc ~= nil, "Unexpected method: " .. method)
        return function(self, ...)
          assert(self == instance, "Wrong native receiver")
          assert(select("#", ...) == argc, "Wrong argument count")
          if argc == 1 then assert(type((...)) == "string", "Gig ID is not a String") end
          if mode == "call_error" then error("runtime unavailable") end
          local args = {...}
          calls[#calls + 1] = { name = name, method = method, argc = argc,
                              argument = args[1], generation = self.generation }
          return name .. "." .. method .. ":" .. tostring(self.generation)
        end
      end
      })
    end }
  end
}
'''


def fresh(mock=True):
    lua = LuaRuntime(unpack_returned_tuples=True)
    if mock:
        lua.execute(MOCK)
    api = lua.execute(TEXT)
    return lua, api


def main():
    cases = []
    lua, api = fresh()
    assert set(api.keys()) == set(METHODS), list(api.keys())
    assert len(lua.globals().calls) == len(lua.globals().reads) == len(lua.globals().writes) == 0
    cases.append("Module import registers no event/override and calls no game API")

    for public, (system, method, args) in METHODS.items():
        lua, api = fresh()
        result = api[public](*args)
        assert result == f"{system}.{method}:1", (public, result)
        calls = lua.globals().calls
        assert len(calls) == len(lua.globals().reads) == 1
        assert calls[1]["name"] == system and calls[1]["method"] == method
        assert calls[1]["argc"] == len(args)
        assert calls[1]["argument"] == (args[0] if args else None)
        assert len(lua.globals().writes) == 0
        cases.append(f"{public}: exact system, method, receiver and argument signature")

    for mode in ("no_container", "no_system", "no_method", "wrong_method_type",
                 "container_error", "lookup_error", "index_error", "call_error"):
        for public, (_, _, args) in METHODS.items():
            lua, api = fresh(); lua.globals().mode = mode
            result = api[public](*args)
            assert isinstance(result, str) and ("unavailable" in result or "Load a save" in result)
            assert len(lua.globals().writes) == 0
            cases.append(f"{public}/{mode}: returns diagnostic without throwing or writing")

    for setup in ("Game=nil", "Game={}", "Game={GetScriptableSystemsContainer=42}"):
        for public, (_, _, args) in METHODS.items():
            lua, api = fresh(); lua.execute(setup)
            assert "Load a save" in api[public](*args)
            assert len(lua.globals().writes) == 0
            cases.append(f"{public}/{setup}: no-session diagnostic")

    for bad in (None, False, True, 7, ""):
        lua, api = fresh()
        assert "Pass a gig ID" in api.Gig(bad)
        assert len(lua.globals().reads) == len(lua.globals().calls) == len(lua.globals().writes) == 0
        cases.append(f"Gig invalid argument {bad!r}: no native call")

    lua, api = fresh()
    assert api.Status().endswith(":1")
    lua.globals().mode = "no_container"
    assert "Load a save" in api.Status()
    lua.globals().mode = "ready"; lua.globals().generation = 2
    assert api.Status().endswith(":2")
    assert len(lua.globals().writes) == 0
    cases.append("Unload/reload resolves current container; no stale system cached")

    source_hashes = {}
    for public, (system, method, args) in METHODS.items():
        source = SCRIPT_PATHS[system]
        text = source.read_text(encoding="utf-8-sig")
        module, cls = system.rsplit(".", 1)
        assert re.search(rf"\bmodule\s+{re.escape(module)}\b", text), system
        assert re.search(rf"\bclass\s+{re.escape(cls)}\s+extends\s+ScriptableSystem", text), system
        match = re.search(rf"public func {re.escape(method)}\(([^)]*)\) -> String", text)
        assert match, (system, method)
        declared = [param for param in match[1].split(",") if param.strip()]
        assert len(declared) == len(args), (public, match[1])
        if args:
            assert declared[0].strip() == "id: String"
        source_hashes[str(source.relative_to(ROOT))] = hashlib.sha256(source.read_bytes()).hexdigest().upper()
        cases.append(f"{public}: REDscript source class/module/public signature verified")

    for forbidden in ("SetFact", "AddItem", "FullNerf", '"Start"', '"Begin"',
                      "registerForEvent(", "registerHotkey(", "Observe(", "Override(",
                      "GetTeleportationFacility", 'io.open', 'os.execute'):
        assert forbidden not in TEXT, forbidden
    cases.append("Console source contains only seven read diagnostics; no writers, hooks or persistence")
    result = {
        "status": "PASS_LUAJIT_MOCK_AND_SOURCE_CONTRACTS_NOT_ENGINE_PROOF",
        "runtime": lua.eval("jit.version"),
        "cases": len(cases),
        "case_details": cases,
        "source": str(SOURCE.relative_to(ROOT)),
        "sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper(),
        "script_sources": source_hashes,
        "no_game_or_save_writes": True,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cet_tests.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("status", "runtime", "cases", "sha256")}, indent=2))


if __name__ == "__main__":
    main()
