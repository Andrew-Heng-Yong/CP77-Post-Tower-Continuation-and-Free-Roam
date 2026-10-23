"""Workspace-only LuaJIT checks; no game calls and no live binding claim."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime

SOURCE = ROOT / "research/gig_restoration/live_probe.lua"
CATALOGUE = ROOT / "research/gig_restoration/state_probe_catalogue.json"
NID = "quests/street_stories/watson/northside_industrial_district/sts_wat_nid_02"
CVI = "quests/street_stories/pacifica/coastview/sts_pac_cvi_02/sts_pac_cvi_02/get_to_the_van"


def plain(v):
    if hasattr(v, "items"):
        return {str(k): plain(x) for k, x in v.items()}
    return v


SETUP = r'''
messages={}; lookups={}; fact_reads={}; mutations={}
function forbidden(k) return function() mutations[#mutations+1]=k; error("forbidden: "..k) end end
function print(s) messages[#messages+1]=s end
function IsDefined(v) return type(v)=="table" end
function EnumInt(v) return v end
json={encode=function(v) return py_encode(v) end}
entry_meta={__index=function(_,k) return forbidden("entry."..k) end}
function entry(path,cn)
 return setmetatable({path=path,class=cn,GetId=function(self) return self.path:match("([^/]+)$") end},entry_meta)
end
jm=setmetatable({
 GetEntryByString=function(_,path,cn) lookups[#lookups+1]={path=path,className=cn}; return entry(path,cn) end,
 GetEntryState=function() return 1 end,
 GetEntryHash=function() return -984135344 end,
 IsEntryTracked=function() return false end,
 GetIsObjectiveOptional=function(_,e) assert(e.class=="gameJournalQuestObjective");return false end,
 GetTrackedEntry=function() return nil end,
 HasAnyDelayedStateChanges=function() return false end
},{__index=function(_,k) return forbidden("jm."..k) end})
qs=setmetatable({GetFactStr=function(_,n) fact_reads[#fact_reads+1]=n; return 0 end},
 {__index=function(_,k) return forbidden("qs."..k) end})
player={GetEntityID=function() return {hash="18446744073709551615"} end}
Game=setmetatable({GetJournalManager=function() return jm end,GetQuestsSystem=function() return qs end,
 GetPlayer=function() return player end},{__index=function(_,k) return forbidden("Game."..k) end})
io=setmetatable({},{__index=function(_,k) return forbidden("io."..k) end})
require=forbidden("require");registerForEvent=forbidden("registerForEvent");Observe=forbidden("Observe")
ObserveAfter=forbidden("ObserveAfter");Override=forbidden("Override");registerHotkey=forbidden("registerHotkey")
'''


def run(setup="", repeat=False, source_override=None):
    runtime = LuaRuntime(unpack_returned_tuples=True)
    runtime.globals().py_encode = lambda v: json.dumps(plain(v), allow_nan=False)
    runtime.execute(SETUP)
    runtime.execute(setup)
    runtime.execute(source_override or SOURCE.read_text(encoding="utf-8"))
    if repeat:
        runtime.execute(SOURCE.read_text(encoding="utf-8"))
    assert len(runtime.globals().mutations) == 0, plain(runtime.globals().mutations)
    rows = [json.loads(v) for _, v in runtime.globals().messages.items()]
    assert len(rows) == (2 if repeat else 1)
    assert all(r["tag"] == "PTFR_GIG_AUDIT" for r in rows)
    return rows[-1], runtime


def main():
    source = SOURCE.read_text(encoding="utf-8")
    assert len(source.splitlines()) == 1
    prohibited = r"\b(?:SetFact\w*|ChangeEntry\w*|SetEntryVisited|TrackEntry|UntrackEntry|QueueEvent|DebugShowAllPoiMappins|register\w*|Observe\w*|Override|require)\s*\("
    assert not re.search(prohibited, source)
    assert not re.search(r"\bio\s*[.:]|\bos\s*\.\s*(?:execute|remove|rename)|\b(?:loadfile|dofile)\s*\(", source)
    catalogue = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    expected = {(e["path"], e["className"]) for e in catalogue["journal_entries"]}
    row, rt = run()
    observed = {(v["path"], v["className"]) for _, v in rt.globals().lookups.items()}
    assert observed == expected and len(observed) == 22
    assert len(row["facts"]) == 25 and set(row["facts"]) <= set(catalogue["fact_names"])
    assert all(v == 0 for v in row["facts"].values())
    assert row["delayed_before"] is False and row["tracked_before"]["present"] is False
    assert row["journal"][CVI]["optional"] is False
    assert row["journal"][NID]["hash"] == -984135344
    assert row["player_before"]["id"] == "18446744073709551615"
    assert not row["errors"]
    assert row["user_label"] == "POST_TOWER" and "not save-slot detection" in row["label_source"]
    assert "absent from explicit zero" in row["fact_presence"]
    cases = ["normal/22-exact-paths/25-facts/signed-hash/zero/false/large-id"]
    assert row["probe_revision"] == 2
    old_source = (SOURCE.parent / 'live_probe_v1.lua').read_text(encoding='utf-8')
    r, _ = run('jm.GetEntryState=function() return 2ULL end', source_override=old_source)
    assert r['journal'][NID]['state'] == 'UNKNOWN' and len(r['errors']) == 22
    cases.append('v1-reproduces-22-state-failures-with-CET-uint64')
    for suffix in ('ULL', 'LL'):
        for value in range(5):
            r, _ = run(f'jm.GetEntryState=function() return {value}{suffix} end')
            assert all(e['state'] == value for e in r['journal'].values())
            assert r['journal'][NID]['state_int_type'] == 'cdata' and not r['errors']
            cases.append(f'v2-cdata-state:{value}{suffix}')
    for value in ('5ULL', '18446744073709551615ULL', '-1LL'):
        r, _ = run(f'jm.GetEntryState=function() return {value} end')
        assert r['journal'][NID]['state'] == 'UNKNOWN'
        cases.append('invalid-cdata-state:' + value)
    for returned in ("nil", "false", '"0"', "0/0", "math.huge", "-math.huge"):
        r, _ = run("qs.GetFactStr=function() return " + returned + " end")
        assert all(v == "UNKNOWN" for v in r["facts"].values())
        assert len([k for k in r["errors"] if k.startswith("fact.")]) == 25
        cases.append("invalid-fact:" + returned)
    r, _ = run('qs.GetFactStr=function(_,n) if n=="nid_02_start" then error("native unavailable") end return 0 end')
    assert r["facts"]["nid_02_start"] == "UNKNOWN" and r["facts"]["nid_02_finished"] == 0
    cases.append("per-fact-error-isolated")
    r, _ = run('jm.GetEntryByString=function() return nil end')
    assert all(v["present"] is False for v in r["journal"].values()) and not r["errors"]
    cases.append("absent-entry-not-lookup-error")
    r, _ = run('jm.GetEntryByString=function() error("lookup failure") end')
    assert all(v["present"] == "UNKNOWN" for v in r["journal"].values())
    cases.append("lookup-error-not-absence")
    r, _ = run('jm.GetIsObjectiveOptional=function() error("binding unavailable") end')
    assert r["journal"][CVI]["optional"] == "UNKNOWN" and r["journal"][CVI]["tracked"] is False
    cases.append("optional-error-not-false")
    r, _ = run('jm.IsEntryTracked=function() return nil end')
    assert r["journal"][CVI]["tracked"] == "UNKNOWN" and r["journal"][CVI]["optional"] is False
    cases.append("tracked-error-isolated")
    r, _ = run('Game.GetJournalManager=function() return nil end;Game.GetQuestsSystem=function() error("no quest service") end;Game.GetPlayer=function() return nil end')
    assert r["journal_service"] is False and r["quest_service"] == "UNKNOWN"
    assert r["player_before"]["present"] is False and all(v == "UNKNOWN" for v in r["facts"].values())
    cases.append("missing-services-player-no-false-zero")
    r, _ = run('jm.GetTrackedEntry=function() return entry("some/foreign/objective","gameJournalQuestObjective") end')
    assert r["tracked_before"] == r["tracked_after"] and r["tracked_before"]["present"] is True
    cases.append("tracked-identity-read-only")
    for value in ("nil", "-1", "5", "1.5", '"2"'):
        r, _ = run('jm.GetEntryState=function() return ' + value + ' end')
        assert r["journal"][NID]["state"] == "UNKNOWN"
        cases.append("invalid-state:" + value)
    for setup in ('json=nil', 'json.encode=function() error("encoding broke") end', 'json.encode=function() return nil end'):
        r, _ = run(setup)
        assert r["error"] == "ENCODING_FAILED" and r["reads_only"] is True
        cases.append("encoding-fallback:" + setup)
    r, _ = run('os.date=function() error("clock unavailable") end')
    assert r["utc"] == "UNKNOWN" and len(r["journal"]) == 22
    cases.append("clock-error-isolated")
    run(repeat=True)
    cases.append("repeat-no-mutation")
    result = {"status": "OFFLINE_LUAJIT_PASS_NOT_RUNTIME_PROOF", "checks": len(cases), "cases": cases,
              "lua_bytes": len(source.encode()), "journal_paths": len(expected), "facts": 25,
              "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper(),
              "catalogue_sha256": hashlib.sha256(CATALOGUE.read_bytes()).hexdigest().upper(),
              "game_writes": 0, "save_writes": 0, "installed": False}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
