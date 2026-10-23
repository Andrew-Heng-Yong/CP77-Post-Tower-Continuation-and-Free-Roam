"""B5.1 regression: source-derived classifier/LuaJIT + compiled persistence metadata.

Serializer filtering and recovery handoffs are models, not native save/owner proof.
"""
import itertools, json, re, sys
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, sha
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

OUT = ROOT / 'research/gig_restoration/fresh_b5_1'
FILES = [
    ('redscript/PTFR_FreshGigsB5/FreshGigsB5.reds', 'r6/scripts/PTFR_FreshGigsB5/FreshGigsB5.reds', 'FreshGigsB5.reds'),
    ('redscript/PTFR_ActivityStateR3/ActivityStateR3.reds', 'r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds', 'ActivityStateR3.reds'),
    ('diagnostics/PTFR_FreshGigsB5/init.lua', 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_FreshGigsB5/init.lua', 'init.lua'),
]
OLD = ['C1D2454935E0E3A02EC8BDB915E67EEB6FE56928202F79DAAC7104A4081F641A', 'D8C3F11A4CA8276392EDA64760ABE2F7900A1266B23B5460968A2A761557AD87', 'C7A6E907E6A16441E9BBCAC07ED7515668A55D2E0960278787CF23CE7D813C36']


def body(text, name):
    start = re.search(r'\bfunc ' + name + r'\([^\n]*\)\s*->[^\n{]+\{', text).end()
    pos, depth = start, 1
    while depth:
        depth += (text[pos] == '{') - (text[pos] == '}')
        pos += 1
    return text[start:pos - 1]


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()


def main():
    assert not (OUT / 'install_receipt.json').exists(), 'Installed revision pinned'
    source = (ROOT / FILES[0][0]).read_text()
    state = (ROOT / FILES[1][0]).read_text()
    lua = (ROOT / FILES[2][0]).read_text()
    oldsource, oldstate, oldlua = [(OUT / 'predecessor' / f[2]).read_text() for f in FILES]
    for f, h in zip(FILES, OLD):
        assert sha(OUT / 'predecessor' / f[2]) == h
    compiled = json.loads((OUT / 'compile_result.json').read_text())
    assert compiled['source_sha256'] == sha(ROOT / FILES[0][0]) and compiled['state_sha256'] == sha(ROOT / FILES[1][0]) and compiled['equipmentex']
    for p, h in (compiled['protected'] | compiled['dependencies']).items():
        assert sha(p) == h, p
    assert normalize(state.replace('public persistent let', 'public let')) == normalize(oldstate), 'R3 only adds nested persistence flags; no history/capture/cutoff/schema mutation'
    saved = re.search(r'public struct FreshSlotB5 \{(.*?)\n\}', source, re.S)[1]
    fields = re.findall(r'public persistent let (\w+): (\w+);', saved)
    assert fields == [('stage', 'Int32'), ('inflight', 'Bool'), ('countBase', 'Int32'), ('achBase', 'Int32'), ('accountPrepared', 'Bool'), ('counterAck', 'Bool')]
    # The previous declaration serializes an empty nested object; current metadata
    # retains all six values, including queued stage1 and saved inflight markers.
    original = {'stage': 4, 'inflight': False, 'countBase': 1, 'achBase': 3, 'accountPrepared': True, 'counterAck': True}
    assert not re.findall(r'public persistent let (\w+):', re.search(r'public struct FreshSlotB5 \{(.*?)\n\}', oldsource, re.S)[1])
    serialized = {name: original[name] for name, _ in fields}
    assert serialized == original
    for name, typ in fields:
        assert re.search(r'public persistent let ' + name + ':', (OUT / 'compiled_flat.script').read_text()), name
    unchanged = []
    altered = {'Restored', 'Poll', 'PollSlot', 'Inspect'}
    for name in re.findall(r'\bfunc (\w+)\(', oldsource):
        if name not in altered:
            assert normalize(body(source, name)) == normalize(body(oldsource, name)), name
            unchanged.append(name)
    adopt = body(source, 'AdoptSavedOwner')
    assert not re.search(r'this\.(Set|Write|Fail)\(|ChangeEntryState|RestoreFresh\(', adopt), 'Adoption must only read facts and assign owned slots'
    assert 'slot.stage!=0 || slot.inflight || slot.accountPrepared || slot.counterAck || slot.countBase!=0 || slot.achBase!=0' in adopt
    assert 'slot.accountPrepared=f.accountReady==1;slot.counterAck=f.counterAck==1;' in adopt
    assert 'if slot.accountPrepared { slot.countBase=f.countBase;slot.achBase=f.achBase; }' in adopt
    assert 'this.recoveryChecked=[false,false]' in source and source.index('this.AdoptSavedOwner(r)') < source.index('this.PollSlot(i,p)')
    assert 'HasAnyDelayedStateChanges()' in body(source, 'Poll') and 'this.warmup>0' in body(source, 'Poll')
    # Source-linked classifier translation: exactly its guard expressions, not a
    # separately maintained approximation. Only this deliberately pure subset.
    lines = []
    for line in body(source, 'RecoveryStage').splitlines():
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        m = re.fullmatch(r'if (.+) \{ return (\d+); \}', line)
        if m:
            expr = m[1].replace('!=', '~=').replace('&&', ' and ').replace('||', ' or ')
            lines.append('if ' + expr + ' then return ' + m[2] + ' end')
        else:
            assert re.fullmatch(r'return \d+;', line), line
            lines.append(line[:-1])
    rt = LuaRuntime(unpack_returned_tuples=True)
    classify = rt.execute('return function(f)\n' + '\n'.join(lines) + '\nend')
    names = re.findall(r'public let (\w+): Int32;', re.search(r'public struct RecoveryFactsB5 \{(.*?)\n\}', source, re.S)[1])
    blank = dict.fromkeys(names, 0) | {'ready': 1, 'revision': 1, 'root': 1}
    cases = []
    def check(name, data, expected):
        assert classify(rt.table_from(data)) == expected, name
        cases.append(name)
    check('unused is not resurrected or certified', blank, 0)
    pending = blank | {'request': 1, 'count': 2, 'ach': 4}
    check('existing unstarted request is monitored, not reissued', pending, 2)
    running = pending | {'started': 1}
    check('reported H1 native boot survives with inactive encounter journal', running, 3)
    credited = running | {'accountRequest': 1, 'accountReady': 1, 'accountClaim': 1, 'accountAck': 1, 'counterAck': 1, 'countBase': 1, 'achBase': 3, 'rewardClaim': 1, 'rewardAck': 1, 'root': 3, 'nativeFinished': 1}
    terminal = credited | {'finished': 1}
    check('reported H7 adopts terminal without credit repeat', terminal, 4)
    check('credited cleanup remains stage3 until native finish', credited, 3)
    check('later legitimate fixer/achievement growth is not overwritten', terminal | {'count': 12, 'ach': 20}, 4)
    check('pending account handoff remains live', running | {'accountRequest': 1}, 3)
    check('unready draft baselines can be recaptured before native claim', running | {'accountRequest': 1, 'countBase': 1, 'achBase': 3}, 3)
    prepared = running | {'accountRequest': 1, 'accountReady': 1, 'countBase': 2, 'achBase': 4}
    check('ready baseline survives without preparing twice', prepared, 3)
    check('native achievement in progress is not replayed', prepared | {'accountClaim': 1}, 3)
    check('acknowledged achievement with untouched fixer baseline permits original one credit', prepared | {'accountClaim': 1, 'accountAck': 1, 'ach': 5}, 3)
    check('unacknowledged fixer increment cannot be inferred as ours', prepared | {'accountClaim': 1, 'accountAck': 1, 'ach': 5, 'count': 3}, 5)
    for name, delta in {
        'missing native completion': {'nativeFinished': 0}, 'nonterminal completed root': {'root': 1},
        'missing completed payout': {'rewardAck': 0}, 'missing completed counter ack': {'counterAck': 0},
        'achievement credit absent': {'ach': 3}, 'fixer credit absent': {'count': 1},
        'native fault': {'fault': 1}, 'wrong revision': {'revision': 2}, 'missing request': {'request': 0},
        'missing archive': {'ready': 0}, 'missing root': {'root': -1}, 'failed terminal root unsupported': {'root': 4},
        'overflow base': {'countBase': 2147483647}, 'negative base': {'achBase': -1},
        'missing account request': {'accountRequest': 0}, 'missing ready': {'accountReady': 0},
        'missing account claim': {'accountClaim': 0}, 'missing account ack': {'accountAck': 0},
        'boot never started': {'started': 0}, 'invalid ack': {'rewardAck': 2},
    }.items():
        check(name, terminal | delta, 5)
    # Full boolean ledger enumeration enforces dependency chains on all admitted
    # owned states. Numerical/native-outcome mutants above exercise other gates.
    flags = ['started', 'finished', 'rewardClaim', 'rewardAck', 'accountRequest', 'accountReady', 'accountClaim', 'accountAck', 'counterAck']
    enumerated = 0
    for values in itertools.product((0, 1), repeat=len(flags)):
        for count, ach, root in itertools.product((1, 2, 3), (3, 4, 5), (1, 2, 3)):
            f = running | dict(zip(flags, values)) | {'countBase': 1, 'achBase': 3, 'count': count, 'ach': ach, 'root': root, 'nativeFinished': 1}
            stage = classify(rt.table_from(f))
            if stage != 5:
                assert f['accountReady'] <= f['accountRequest'] and f['accountClaim'] <= f['accountReady'] and f['accountAck'] <= f['accountClaim'] and f['counterAck'] <= f['accountAck'] and f['rewardAck'] <= f['rewardClaim']
                if stage == 4:
                    assert f['finished'] == f['counterAck'] == f['rewardClaim'] == f['rewardAck'] == 1 and root == 3 and count >= 2 and ach >= 4
                if f['accountAck'] and not f['counterAck']:
                    assert count == 1 and ach >= 4
            enumerated += 1
    # Recovery only restores tracking. Original acknowledged-credit guard is
    # unchanged; reloaded acknowledged slots cannot enter its counter writer.
    assert 'if this.Own(i,"AccountAck")==1 && !slot.counterAck {' in source
    assert 'if slot.stage==0 || slot.stage==4 || slot.stage==5 { return; }' in source
    # Actual LuaJIT bridge regressions with new boxed EntityID each getter call.
    lua_cases = []
    def runtime():
        l = LuaRuntime(unpack_returned_tuples=True)
        l.execute('''calls={};events={};epoch=1;hash="18446744073709550001ULL";registerForEvent=function(k,f) events[k]=f end
          IsDefined=function(x) return x~=nil end;json={encode=function() return "{}" end};Game={};local s={BatchEpoch=function() return epoch end}
          for _,n in ipairs({"Inspect","Override","RestoreGig"}) do s[n]=function(self,...) table.insert(calls,{n,...});if backendFail then error("backend failed") end;if bump then epoch=epoch+1 end;if changeHash then hash="2ULL" end;return "OK" end end
          Game.GetScriptableSystemsContainer=function() return {Get=function() return s end} end
          Game.GetPlayer=function() if missingPlayer then return nil end;return {GetEntityID=function() return {hash=hash} end} end
          Game.GetQuestsSystem=function() return {GetFactStr=function() return 0 end} end
          Game.GetJournalManager=function() return {HasAnyDelayedStateChanges=function() return false end,GetEntryByString=function() return nil end} end''')
        return l, l.execute(lua)
    l, m = runtime()
    assert 'acknowledgement' in m.OverrideAll('wrong') and len(l.globals().calls) == 0
    lua_cases.append('invalid confirmation no dispatch')
    l, m = runtime()
    assert 'Cancelled' not in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls) == 2
    assert all(l.globals().calls[k][3] == 'fresh' for k in (1, 2))
    lua_cases.append('fresh boxed IDs with stable UInt64 hash dispatch both once')
    l, m = runtime()
    assert '67' in m.RestoreAll() and len(l.globals().calls) == 5
    lua_cases.append('five implemented adapters only')
    for change in ('bump', 'changeHash', 'backendFail'):
        l, m = runtime()
        l.globals()[change] = True
        assert 'Cancelled without retry' in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls) == 1
        lua_cases.append(change + ' cancels remaining requests without retry')
    l, m = runtime()
    l.globals().missingPlayer = True
    assert 'Cancelled before dispatch' in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls) == 0
    lua_cases.append('missing player no dispatch')
    l, m = runtime()
    l.globals().hash = None
    assert 'entity hash missing' in m.OverrideAll('DISPOSABLE_SAVE') and len(l.globals().calls) == 0
    lua_cases.append('missing hash no dispatch')
    l, m = runtime()
    m.Sample()
    assert all(l.globals().calls[k][1] == 'Inspect' for k in range(1, len(l.globals().calls) + 1))
    lua_cases.append('snapshot getters only')
    assert 'tostring(p:GetEntityID())' not in lua and 'return tostring(id.hash)' in lua
    assert normalize(lua[lua.index('local function snapshot()'):].replace(',"hil_07_finished","hil_01_finished"', '')) == normalize(oldlua[oldlua.index('local function snapshot()'):])
    assert not re.search(r'SetFact|ChangeEntryState', '\n'.join(x for x in lua.splitlines() if not x.startswith('--')))
    original = json.loads((ROOT / 'research/gig_restoration/fresh_b5/tests.json').read_text())
    unchanged_assets = [f for f in original['files'] if f['relative'].endswith(('.archive', '.xl'))]
    for f in unchanged_assets:
        assert sha(ROOT / f['source']) == f['sha256']
    tools = ['compile_fresh_gigs_b5_1.py', 'test_fresh_gigs_b5_1.py']
    result = {'status': 'PASS_B5_1_OFFLINE_NATIVE_RELOAD_PENDING', 'files': [{'source': f[0], 'relative': f[1], 'sha256': sha(ROOT / f[0]), 'predecessor': h} for f, h in zip(FILES, OLD)], 'tools': {'tools/' + p: sha(ROOT / 'tools' / p) for p in tools}, 'compile_sha256': sha(OUT / 'compile_result.json'), 'equipmentex_full_compile': True, 'compiled_nested_persistence_verified': True, 'source_linked_recovery_cases': cases, 'source_linked_ledger_enumerations': enumerated, 'actual_luajit_cases': lua_cases, 'unchanged_b5_methods': unchanged, 'r3_only_nested_persistence_flags_changed': True, 'r3_history_not_reconstructed': True, 'archive_xl_unchanged': unchanged_assets, 'recovery_writes_native_fact_journal_owner_reward_credit': False, 'native_save_reload_proven': False, 'new_gig_adapters': 0, 'total_gig_adapters': 5, 'pending_gig_adapters': 67, 'completed_replay_adapters': 0}
    (OUT / 'tests.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k in ('status', 'source_linked_ledger_enumerations', 'actual_luajit_cases')}, indent=2))


if __name__ == '__main__':
    main()
