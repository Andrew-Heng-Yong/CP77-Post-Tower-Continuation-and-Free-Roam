"""Mock the read-only CET boundary of the Serial Suicide probe."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime

SOURCE = ROOT / "research/gig_restoration/fresh_candidates/serial_suicide_probe.lua"
CONSOLE = ROOT / "research/gig_restoration/fresh_candidates/serial_suicide_console.lua"


def plain(value):
    if hasattr(value, "items"):
        return {str(key): plain(item) for key, item in value.items()}
    return value


SETUP = r'''
messages={}; lookups={}; fact_reads={}; mutations={}
function forbidden(name)
  return function() mutations[#mutations+1]=name; error("forbidden "..name) end
end
function print(value) messages[#messages+1]=value end
function IsDefined(value) return type(value)=="table" end
function EnumInt(value) return value end
json={encode=function(value) return py_encode(value) end}
local function entry(path,class)
  return setmetatable({path=path,class=class,
    GetId=function(self) return self.path:match("([^/]+)$") end},
    {__index=function(_,name) return forbidden("entry."..name) end})
end
jm=setmetatable({
  GetEntryByString=function(_,path,class)
    lookups[#lookups+1]={path=path,class=class}
    return entry(path,class)
  end,
  GetEntryState=function() return 1 end,
  GetEntryHash=function() return -14568 end,
  IsEntryTracked=function() return false end,
  GetIsObjectiveOptional=function(_,value)
    assert(value.class=="gameJournalQuestObjective")
    return false
  end,
  GetTrackedEntry=function() return nil end,
  HasAnyDelayedStateChanges=function() return false end
}, {__index=function(_,name) return forbidden("journal."..name) end})
qs=setmetatable({GetFactStr=function(_,name)
  fact_reads[#fact_reads+1]=name
  return 0
end}, {__index=function(_,name) return forbidden("quests."..name) end})
player={GetEntityID=function() return {hash="18446744073709551615"} end}
Game=setmetatable({
  GetJournalManager=function() return jm end,
  GetQuestsSystem=function() return qs end,
  GetPlayer=function() return player end
}, {__index=function(_,name) return forbidden("Game."..name) end})
io=setmetatable({}, {__index=function(_,name) return forbidden("io."..name) end})
require=forbidden("require"); dofile=forbidden("dofile")
registerForEvent=forbidden("registerForEvent")
Observe=forbidden("Observe"); Override=forbidden("Override")
'''


def run(extra="", source_path=SOURCE):
    runtime = LuaRuntime(unpack_returned_tuples=True)
    runtime.globals().py_encode = lambda value: json.dumps(plain(value), allow_nan=False)
    runtime.execute(SETUP)
    if extra:
        runtime.execute(extra)
    runtime.execute(source_path.read_text(encoding="utf-8"))
    messages = [value for _, value in runtime.globals().messages.items()]
    assert len(messages) == 1
    assert not list(runtime.globals().mutations.items())
    return json.loads(messages[0]), runtime


def main():
    source = SOURCE.read_text(encoding="utf-8")
    console = CONSOLE.read_text(encoding="utf-8").strip()
    compact = " ".join(line.strip() for line in source.splitlines()
                       if line.strip() and not line.lstrip().startswith("--"))
    assert console == compact and "\n" not in console
    prohibited = r"\b(?:SetFact\w*|ChangeEntry\w*|SetEntryVisited|TrackEntry|UntrackEntry|QueueEvent|register\w*|Observe\w*|Override|require|dofile|loadfile)\s*\("
    assert not re.search(prohibited, source)
    assert not re.search(r"\bio\s*[.:]|\bos\s*\.\s*(?:execute|remove|rename)", source)
    row, runtime = run(source_path=CONSOLE)
    assert row["tag"] == "PTFR_CPZ01_AUDIT" and row["revision"] == 1
    assert len(row["journal"]) == 11 and len(row["facts"]) == 17
    assert not row["errors"]
    assert row["player_before"] == row["player_after"]
    assert row["tracked_before"] == row["tracked_after"]
    assert row["delayed_before"] is False and row["delayed_after"] is False
    assert all(value["state"] == 1 for value in row["journal"].values())
    assert len(list(runtime.globals().lookups.items())) == 11
    assert len(list(runtime.globals().fact_reads.items())) == 17
    assert all("sts_cct_cpz_01" in path for path in row["journal"])
    source_row, _ = run()
    assert {k: v for k, v in row.items() if k != "utc"} == {
        k: v for k, v in source_row.items() if k != "utc"}
    row, _ = run("jm.GetEntryState=function() return 4ULL end", CONSOLE)
    assert all(value["state"] == 4 for value in row["journal"].values())
    assert not row["errors"]
    row, _ = run("jm.GetEntryByString=function() return nil end", CONSOLE)
    assert all(value["present"] is False for value in row["journal"].values())
    row, _ = run('qs.GetFactStr=function(_,name) if name=="cpz_01_start" then error("unavailable") end return 0 end', CONSOLE)
    assert row["facts"]["cpz_01_start"] == "UNKNOWN"
    assert row["facts"]["cpz_01_finished"] == 0
    print("Serial Suicide console probe: exact one-line copy, read-only mock, eleven journal paths, seventeen facts, cdata states, absent entries and isolated getter errors PASS")


if __name__ == "__main__":
    main()
