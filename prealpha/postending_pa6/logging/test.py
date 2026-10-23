"""Quiet PA6 logging integration checks. Does not run the game or mutate saves."""
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def main():
    out = Path(sys.argv[1]).resolve()
    assert out.is_relative_to(ROOT / 'research/postending_pa6/logging')
    assert not out.exists(), 'Use a fresh output; do not overwrite evidence.'
    source = Path(__file__).parent
    old = (ROOT / 'prealpha/postending_pa5/cet/init.lua').read_text(encoding='utf-8-sig')
    new = (source / 'init.lua').read_text(encoding='utf-8-sig')
    oldentry = (ROOT / 'prealpha/postending_pa5/scripts/PreAlphaEntry.reds').read_text(encoding='utf-8-sig')
    entry = (source / 'PreAlphaEntry.reds').read_text(encoding='utf-8-sig')
    checks = []

    def check(ok, name):
        assert ok, name
        checks.append(name)

    oldapi = old[:old.index('-- Read-only, bounded transition trace')]
    newapi = new[:new.index('-- PA6: verbose diagnostics')].replace('-- PA6 diagnostics', '-- PA5 diagnostics')
    check(oldapi == newapi, 'All prior manual diagnostic and RepairCamera API bodies unchanged')
    expected = oldentry.replace('if NotEquals(this.results[i], result) { this.results[i] = result; ModLog(n"PTFR_PreAlpha", id + " | " + result); }', '// PA6: keep admission results for explicit Inspect/Entry diagnostics, not console spam.\n      if NotEquals(this.results[i], result) { this.results[i] = result; }')
    check(expected.rstrip() == entry.rstrip(), 'PreAlphaEntry exact delta: remove dispatch log only')
    check('private func Fail(message: String) -> Void { this.faulted = true; this.fault = StringToName(message); ModLog(n"PTFR_PreAlpha", message); }' in entry, 'Coordinator fault logging preserved')
    check(new.count('registerForEvent(') == 1, 'One existing update callback, no gameplay observers or hooks')
    check(not any(x in new for x in ('SetFact', 'SaveGame(', 'LoadGame(', 'io.open', 'os.execute', 'Observe(', 'Override(')), 'No gameplay, save, settings, global-console or other-mod mutation')
    check('local traceUntil, traceRows, previous = nil, 0, nil' in new, 'Verbose trace off at startup')
    check(new.index('if not traceUntil then return end') < new.index('local state = api.Camera()'), 'No verbose system getters called in default update')
    check('"PTFRPA2_Fault", "PTFRPA5O_Fault"' in new, 'Only exact owned transition/optics faults automatically monitored')
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
      events={}; logs={}; calls={}; facts={}; ticks=0;
      registerForEvent=function(k,f) events[k]=f end
      print=function(s) logs[#logs+1]=s end
      query={GetFactStr=function(_,name) return facts[name] or 0 end}
      systems={Get=function(_,name) return setmetatable({}, {__index=function(_,method)
        return function(_,...) calls[#calls+1]=name..'.'..method; return method..':'..tostring(ticks) end
      end}) end}
      Game={GetQuestsSystem=function() return query end,
        GetScriptableSystemsContainer=function() return systems end}
      advance=function(n) for i=1,n do ticks=ticks+1;events.onUpdate(1) end end
    ''')
    api = lua.execute(new)
    lua.execute('advance(600)')
    check(lua.eval('#logs') == 0, 'Ten minutes quiet default with available live systems')
    check(lua.eval('#calls') == 0, 'No automatic camera/status/H10/gig diagnostic reads by default')
    lua.execute('facts.PTFRPA2_Finished=1;facts.PTFRPA5O_Done=1;advance(600)')
    check(lua.eval('#logs') == 0, 'Ten minutes quiet after acknowledged completion')
    for method in ('Status', 'Arrival', 'Gigs', 'Entry', 'Phone', 'Profile', 'Optics', 'H10', 'GigSummary', 'GigVisibility', 'Camera'):
        check(isinstance(api[method](), str), 'Manual getter retained: ' + method)
    check('Pass a' in api.GigVisibility(4), 'Invalid gig argument refused without call')
    check('Pass a' in api.Gig(''), 'Empty gig argument refused without call')
    check(not any('.Repair' in str(v) for v in lua.globals().calls.values()), 'Manual getters never call Repair')
    check('Repair:' in api.RepairCamera(), 'Explicit camera repair forwarding retained')
    lua.execute('facts.PTFRPA2_Fault=1;advance(400)')
    check(lua.eval('#logs') == 1, 'New handoff fault printed exactly once, not 400 times')
    lua.execute('facts.PTFRPA2_Fault=0;advance(2);facts.PTFRPA2_Fault=2;advance(10)')
    check(lua.eval('#logs') == 1, 'Same fault owner stays deduplicated across value changes')
    lua.execute('facts.PTFRPA5O_Fault=3;advance(400)')
    check(lua.eval('#logs') == 2, 'Optics fault printed once independently')
    check(all('Restoration fault:' in str(v) for v in lua.globals().logs.values()), 'Default output restricted to concise fault notices')
    for invalid in (0, -1, 181, '60', float('inf'), float('-inf'), float('nan')):
        check('Pass a duration' in api.Trace(invalid), 'Invalid duration safely refused: ' + str(invalid))
    check('off' in api.TraceStatus(), 'Invalid duration never arms trace')
    lua.execute('logs={};facts={}')
    check('180' in api.Trace(180), 'Explicit maximum trace accepted')
    lua.execute('advance(180)')
    check(lua.eval('#logs') == 222, 'Explicit maximum trace bounded to 180+36+6 items')
    lua.execute('advance(600)')
    check(lua.eval('#logs') == 222 and 'off' in api.TraceStatus(), 'Trace expires and remains quiet')
    check('60' in api.Trace(), 'Explicit default trace duration is 60 seconds')
    lua.execute('advance(5)')
    check(lua.eval('#logs') > 222, 'Explicit trace still gathers diagnostics after prior expiry')
    count = lua.eval('#logs')
    check('stopped' in api.TraceStop(), 'Explicit stop supported')
    lua.execute('advance(600)')
    check(lua.eval('#logs') == count, 'Manual stop remains quiet')
    api.Trace(60)
    lua.execute('Game.GetQuestsSystem=function() return nil end;advance(1)')
    check('off' in api.TraceStatus(), 'Trace cancels when loaded systems disappear')
    lua.execute('Game.GetQuestsSystem=function() return query end;advance(100)')
    check(lua.eval('#logs') == count, 'Trace never resumes automatically after loading')
    lua.execute('facts.PTFRPA2_Fault=1;advance(10)')
    check(lua.eval('#logs') == count + 1, 'Fault notice can report a new loaded session once')
    lua.execute('Game=nil;advance(10)')
    check('Load a save first' in api.Status(), 'Manual getter safely handles no game')
    lua.execute('events.onUpdate(-1);events.onUpdate(0/0);events.onUpdate(math.huge);events.onUpdate("bad")')
    check('off' in api.TraceStatus(), 'Invalid frame deltas do not throw or start trace')
    lua.execute('Game={GetQuestsSystem=function() error("not ready") end};advance(10)')
    check('off' in api.TraceStatus(), 'Quest getter error safely cancels trace')
    out.parent.mkdir(parents=True, exist_ok=True)
    result = {'status': 'PASS_OFFLINE_NOT_LIVE', 'checks': len(checks), 'details': checks,
              'files': {p.name: sha(p) for p in (source / 'init.lua', source / 'PreAlphaEntry.reds')},
              'test_source_sha256': sha(__file__),
              'limitations': 'LuaJIT mocks and exact redscript source-delta checks only; root must compile integrated candidate. Native one-shot camera/profile logging and unrelated FactFinder are unchanged.'}
    out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': result['status'], 'checks': len(checks), 'out': str(out)}))


if __name__ == '__main__':
    main()
