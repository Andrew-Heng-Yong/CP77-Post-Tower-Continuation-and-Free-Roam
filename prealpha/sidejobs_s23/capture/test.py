"""Execute the actual capture module under LuaJIT with read-only API doubles."""
import copy
import json
import re
import sys
from pathlib import Path
from build import HERE, ROOT, read, sha
sys.path.insert(0, str(ROOT / "research/phase2b_p0/tooling/python"))
from lupa.luajit21 import LuaRuntime


def main(revision):
    out = HERE / "build" / revision
    manifest = read(out / "build.json")
    data = read(out / "data.json")
    source = (out / "init.lua").read_text(encoding="utf-8")
    for p, h in manifest["source_pins"].items():
        assert sha(ROOT / p) == h, p
    for p, h in manifest["files"].items():
        assert sha(out / p) == h, p
    assert manifest["jobs"] == 58 and manifest["root_only"] == []
    assert len(data["jobs"]) == len({r["id"] for r in data["jobs"]}) == 58
    assert next(r for r in data["jobs"] if r["id"] == "mq306_dumpster")["journals"]
    for token in ["SetFact", "ChangeEntryState", "Queue", "registerEvent", "registerForEvent", "Observe", "Override", "Execute", "AutoSave", "LoadSave", "os.execute", "io.popen"]:
        assert token not in source, token
    reports = []
    cases = 0

    def run(config=None, custom_data=None, calls=1):
        nonlocal cases
        cases += 1
        lua = LuaRuntime(unpack_returned_tuples=True)

        def to_python(v):
            if hasattr(v, "items"):
                items = dict(v.items())
                if items and set(items) == set(range(1, len(items) + 1)):
                    return [to_python(items[i]) for i in range(1, len(items) + 1)]
                return {k: to_python(x) for k, x in items.items()}
            return v

        def encode(v):
            p = to_python(v)
            reports.append(p)
            return json.dumps(p)

        lua.globals().pyDecode = lambda text: lua.table_from(json.loads(text), recursive=True)
        lua.globals().pyEncode = encode
        lua.globals().catalogueText = json.dumps(custom_data or data)
        lua.globals().config = lua.table_from(config or {}, recursive=True)
        lua.execute(r'''
          files = {['data.json'] = catalogueText}; reads = 0; writes = 0; enums = {}
          gameJournalEntryState = {}; for _,n in ipairs({'Inactive','Active','Succeeded','Failed'}) do gameJournalEntryState[n] = {name=n} end
          json = {decode=pyDecode, encode=pyEncode}
          os = {date=function(fmt) return '20261016T010203Z' end}
          io = {open=function(name, mode)
            if mode == 'r' then
              if config.noData and name == 'data.json' then return nil end
              if not files[name] then return nil end
              return {read=function() return files[name] end, close=function() return true end}
            end
            assert(mode == 'w' and name:match('^capture_s23_[A-Za-z0-9_]+%.json$'))
            assert(not files[name], 'report overwrite')
            if config.writeFail then return nil end
            writes = writes + 1
            return {write=function(_, text) files[name]=text; return true end, close=function() return true end}
          end}
          local qm = {GetFactStr=function(_,name)
            if config.factError then error('fact getter failure') end
            if config.badFact then return nil end
            return (config.facts and config.facts[name]) or 0
          end}
          local jm = {
            HasAnyDelayedStateChanges=function() return config.pending or false end,
            GetEntryByString=function(_,path,class)
              if path == config.missing then return nil end
              return {path=path,class=class}
            end,
            GetEntryState=function(_,entry)
              reads = reads + 1
              if config.unknown then return {} end
              if config.changing and reads > config.changing then return gameJournalEntryState.Active end
              local key = (config.states and config.states[entry.path]) or 'Inactive'
              return gameJournalEntryState[key]
            end
          }
          local function deny(_, name) error('Unapproved game API: '..tostring(name)) end
          setmetatable(qm, {__index=deny}); setmetatable(jm, {__index=deny})
          Game = {
            GetPlayer=function() if config.noPlayer then return nil end; return {} end,
            GetQuestsSystem=function() if config.noSystem then return nil end; return qm end,
            GetJournalManager=function() if config.noJournal then return nil end; return jm end
          }
          setmetatable(Game, {__index=deny})
        ''')
        start = len(reports)
        module = lua.execute(source)
        assert lua.globals().reads == lua.globals().writes == 0, "load caused activity"
        answers = [module.Capture() for _ in range(calls)]
        return answers, reports[start:], lua.globals().writes

    answers, results, writes = run()
    assert writes == 1 and results[0]["status"] == "STABLE_READ_ONLY_CAPTURE"
    assert results[0]["rootCounts"]["Inactive"] == 58 and len(results[0]["first"]["jobs"]) == 58
    assert results[0]["first"]["unknownJournalRows"] == 0
    states = {data["jobs"][0]["root"]: "Active", data["jobs"][1]["root"]: "Succeeded", data["jobs"][2]["root"]: "Failed"}
    _, results, _ = run({"states": states, "facts": {"mq306_quest_accepted": 1}})
    assert results[0]["rootCounts"] == {"Inactive": 55, "Active": 1, "Succeeded": 1, "Failed": 1, "Unknown": 0}
    assert next(r for r in results[0]["first"]["jobs"] if r["id"] == "mq306_dumpster")["facts"]["mq306_quest_accepted"] == 1
    for config in [{"pending": True}, {"changing": 700}]:
        _, results, _ = run(config)
        assert results[0]["status"] == "UNSETTLED_DO_NOT_USE_FOR_ADMISSION"
    _, results, _ = run({"missing": data["jobs"][0]["root"]})
    assert results[0]["rootCounts"]["Unknown"] == 1 and results[0]["first"]["jobs"][0]["rootState"] == "Missing"
    _, results, _ = run({"unknown": True})
    assert results[0]["rootCounts"]["Unknown"] == 58
    for config in [{"noPlayer": True}, {"noSystem": True}, {"noJournal": True}, {"noData": True}, {"factError": True}, {"badFact": True}, {"writeFail": True}]:
        answers, _, writes = run(config)
        assert answers[0].startswith("S23 capture unavailable;") and writes == 0
    for mutation in ["count", "duplicate", "missingroot", "badfact", "kind"]:
        d = copy.deepcopy(data)
        if mutation == "count": d["jobs"].pop()
        if mutation == "duplicate": d["jobs"][1]["id"] = d["jobs"][0]["id"]
        if mutation == "missingroot": d["jobs"][0]["root"] = "wrong/path"
        if mutation == "badfact": d["jobs"][0]["facts"].append("bad;name")
        if mutation == "kind": d["kind"] = "OTHER"
        answers, _, writes = run(custom_data=d)
        assert answers[0].startswith("S23 capture unavailable;") and writes == 0
    answers, results, writes = run(calls=3)
    assert writes == 3 and len(set(answers)) == 3
    for result in results:
        assert result["nativeWrites"] == result["saveWrites"] == 0
    report = {"status": "PASS_LUAJIT_NOT_LIVE", "build_sha256": sha(out / "build.json"), "tester_sha256": sha(Path(__file__)),
              "cases": cases, "jobs": 58, "journals": manifest["journals"], "facts": manifest["facts"],
              "native_writes": 0, "automatic_callbacks": 0, "limitations": "Native delivery and live catalogue availability require the user's manual capture."}
    target = out / "tests.json"
    assert not target.exists()
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main(sys.argv[1])
