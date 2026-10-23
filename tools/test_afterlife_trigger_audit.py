"""Read-only logger checks; runs API-double scenarios when local LuaJIT is readable."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "diagnostics/PTFR_Afterlife_TriggerAudit/init.lua"


def main() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert not re.search(r"\b(SetFact\w*|Override|ObserveBefore|ObserveAfter)\s*\(", source)
    assert '"onUpdate"' not in source
    assert all(f"function M.{name}(" in source for name in ("Start", "Mark", "Stop"))
    assert "assert(output:flush())" in source and 'io.open(candidate,"a+")' in source
    assert all(f'"{name}"' in source for name in
               ("Requested", "Boot", "Guard", "Owner", "Outside", "Inside", "Exits"))
    print("Static PASS: explicit commands, no polling/gameplay setters, flushed append logging.")
    sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
    try:
        from lupa.luajit21 import LuaRuntime
    except (ImportError, OSError) as error:
        print(f"Lua syntax/API mocks NOT RUN: local LuaJIT unavailable ({error}).")
        return
    lua = LuaRuntime(unpack_returned_tuples=True)

    def native(value):
        if hasattr(value, "items"):
            data = {key: native(child) for key, child in value.items()}
            if data and set(data) == set(range(1, len(data) + 1)):
                return [data[index] for index in range(1, len(data) + 1)]
            return data
        return value

    lua.globals().py_encode = lambda row: json.dumps(native(row))
    lua.execute(r'''
      callbacks,facts,listeners,files,unregistered={}, {}, {}, {}, {}
      missingPlayer=false; failListener="q307_finished"; failCombat=false
      json={encode=py_encode}; CName={new=function(value)return value end}
      function IsDefined(value)return type(value)=="table" end
      function registerForEvent(name,fn)callbacks[name]=fn end
      function NewProxy(spec)return{Target=function()return spec end,
        Function=function()return "Callback" end}end
      io={open=function(path,mode)
        assert(mode=="a+"); files[path]=files[path] or ""
        return {seek=function()return #files[path] end,
          write=function(self,line)files[path]=files[path]..line;return self end,
          flush=function(self)return self end,close=function()return true end}
      end}
      player={GetWorldPosition=function()return{x=1,y=2,z=3}end,
        IsInCombat=function()if failCombat then error("combat getter failure")end;return false end,
        GetEntityID=function()return 42 end}
      q={GetFactStr=function(self,name)return facts[name] or 0 end,
        RegisterListener=function(self,name,proxy,fn)
          if name==failListener then error("listener failure")end
          listeners[name]=proxy.callback;return name end,
        UnregisterListener=function(self,name,id)unregistered[#unregistered+1]=name;listeners[name]=nil end}
      Game={GetPlayer=function()if not missingPlayer then return player end end,
        GetQuestsSystem=function()return q end,
        GetSceneSystem=function()return {GetScriptInterface=function()
          return{IsEntityInScene=function()return false end}end}end,
        GetWorkspotSystem=function()return{IsActorInWorkspot=function()return false end}end}
    ''')
    module = lua.execute(source)  # LuaJIT parses the complete source here.
    first = module.Start("baseline")
    globals_ = lua.globals()
    assert globals_.callbacks["onUpdate"] is None
    globals_.facts["PTFRALMA1_Inside"] = 2
    globals_.listeners["PTFRALMA1_Inside"](1)  # delivery lags current DB
    globals_.failCombat = True
    module.Mark("getter-failure")
    globals_.missingPlayer = True
    module.Mark("absent-player")
    module.Stop()
    rows = [json.loads(line) for line in globals_.files[first].splitlines()]
    assert rows[0]["event"] == "INITIAL_BASELINE"
    delivery = next(row for row in rows if row["event"] == "FACT_DELIVERY")
    assert delivery["detail"]["previous_observed"] == 0
    assert delivery["detail"]["callback_value"] == 1
    assert delivery["detail"]["current_read"] == 2
    assert delivery["detail"]["callback_differs_from_current"] is True
    assert any(row["event"] == "LISTENER_FAILED" for row in rows)
    assert any("combat" in row["state"]["errors"] for row in rows)
    assert any(row["state"]["player_exists"] is False for row in rows)
    assert len(globals_.unregistered) == 22
    assert [row["seq"] for row in rows] == list(range(1, len(rows) + 1))
    second = module.Start("next-run")
    assert first != second
    globals_.callbacks["onShutdown"]()
    assert len(globals_.unregistered) == 44
    print("LuaJIT PASS: syntax, delayed fact delivery vs DB, failed listener/getter, absent player,")
    print("unique runs, sequential JSONL, Stop/shutdown listener cleanup; mock has no gameplay writers.")


if __name__ == "__main__":
    main()
