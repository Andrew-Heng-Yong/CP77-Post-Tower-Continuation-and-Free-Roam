"""Offline graph, LuaJIT logger, and parser checks. Never connects to the game."""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
from analyze_phase2b_p0 import analyze, parse, readiness_failures, STAGES


def plain(value):
    if hasattr(value, 'items'):
        items = dict(value.items())
        if items and all(isinstance(k, (int, float)) for k in items):
            return [plain(items[k]) for k in sorted(items)]
        return {str(k): plain(v) for k, v in items.items()}
    return value


def graph_checks():
    val = ROOT / 'research/phase2b_p0/validation'
    manifest = json.loads((val / 'build_manifest.json').read_text(encoding='utf-8-sig'))
    archive = Path(manifest['archive'])
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper() == manifest['sha256']
    assert len(manifest['resources']) == 2
    writers = []
    for key, expected in [('board', 31), ('final', 61)]:
        obj = json.loads((val / f'{key}.patched.json').read_text(encoding='utf-8-sig'))
        handles = {}
        def index(v):
            if isinstance(v, dict):
                if 'HandleId' in v and 'Data' in v:
                    handles[v['HandleId']] = v['Data']
                for x in v.values(): index(x)
            elif isinstance(v, list):
                for x in v: index(x)
        index(obj)
        def deref(v):
            if 'Data' in v: return v['Data']
            return handles[v['HandleRefId']]
        nodes = {deref(h)['id']: deref(h) for h in obj['Data']['RootChunk']['graph']['Data']['nodes']}
        assert len(nodes) == expected
        additions = {k: v for k, v in nodes.items() if k >= 100}
        def value(v): return v.get('$value') if isinstance(v, dict) else v
        for n in additions.values():
            if 'type' not in n: continue
            t = deref(n['type'])
            if t['$type'] == 'questSetVar_NodeType':
                name=value(t['factName']);writers.append(name)
                assert name.startswith('PTFRP0_') or name == 'PostTowerFreeRoamActive'
                assert t['value'] == 1 and t['setExactValue'] == 1
            assert t['$type'] not in ('questStartQuest_NodeType', 'questEndGame_NodeType')
        if key == 'board':
            assert deref(nodes[103]['type'])['loadPointOfNoReturnSave'] == 0
            assert deref(nodes[103]['type'])['$type'] == 'questFinalBoardsLoadPonRSave_NodeType'
        else:
            assert value(deref(nodes[111]['type'])['tier']) == 'Tier1_FullGameplay'
            assert deref(nodes[113]['type'])['show'] == 1
            for nid in (115,117,119,121,123,125):
                t=deref(nodes[nid]['type'])
                assert t['action'] == 'RemoveRestriction' and value(t['source']) == 'finalboards'
                assert len(t['restrictionIDs']) == 1
            token=deref(deref(nodes[128]['type'])['subtype'])
            assert token['action'] == 'Unblock' and value(token['source']) == 'finalboards'
            for nid in (104,107):
                assert deref(deref(nodes[nid]['condition'])['type'])['$type'] == 'questCreditsRolling_ConditionType'
            for nid in (105,106):
                delay=deref(deref(nodes[nid]['condition'])['type'])
                assert delay['$type'] == 'questRealtimeDelay_ConditionType'
                assert delay['miliseconds'] == 100 and delay['seconds'] == 0
    assert set(writers) == {x['fact'] for x in manifest['events']} | {'PostTowerFreeRoamActive'}
    # Model only the added gate's topology, not engine scheduling.
    final = next(x for x in manifest['graphs'] if x['patchedNodes'] == 61)
    edges = final['addedEdges']
    assert '104.True -> 105.In' in edges and '105.Out -> 104.In' in edges
    assert '107.True -> 105.In' in edges
    assert '107.False -> 108.In' in edges and '108.True -> 109.In' in edges
    assert not any(e.startswith('108.False') for e in edges)
    assert '27.Out -> 28.In' not in final['removedEdges']
    return manifest


def logger_checks(manifest):
    lua=LuaRuntime(unpack_returned_tuples=True)
    captured=[]
    lua.globals().capture=lambda line: captured.append(line)
    lua.globals().pyEncode=lambda value: json.dumps(plain(value), separators=(',', ':'))
    lua.globals().pyDecode=lambda value: lua.table_from(json.loads(value), recursive=True)
    lua.globals().eventJSON=json.dumps(manifest['events'])
    lua.execute((ROOT/'tools/test_phase2b_p0_mock.lua').read_text(encoding='utf-8'))
    source=(ROOT/'diagnostics/PTFR_Phase2B_P0/init.lua').read_text(encoding='utf-8')
    for forbidden in ('SetFact(', 'SetFactStr(', 'Override(', 'ApplyStatusEffect(', 'RemoveStatusEffect(', 'SetInt(', 'SetBool('):
        assert forbidden not in source, forbidden
    lua.execute(source)  # LuaJIT syntax and top-level registration.
    lua.execute('callbacks.onInit(); callbacks.onUpdate(0.2)')
    rows,errors=parse(''.join(captured))
    assert not errors and rows[0]['event']=='DR00'
    assert any(r['event']=='FACT_LISTENERS_READY' for r in rows)
    assert not any(r['event']=='LISTENERS_READY' for r in rows)
    assert rows[-1]['state']['credits_board_status']=='DEFINITION_UNEXPOSED'
    assert all(v=='UNKNOWN' for v in rows[-1]['state']['credits'].values())
    assert readiness_failures(rows, 0)==[], readiness_failures(rows, 0)
    empty_lua_error_table=copy.deepcopy(rows)
    empty_lua_error_table[-1]['read_errors']=[]
    assert readiness_failures(empty_lua_error_table, 0)==[]
    malformed_error_table=copy.deepcopy(rows)
    malformed_error_table[-1]['read_errors']=['unexpected error']
    assert 'recorder read-error payload is malformed' in readiness_failures(malformed_error_table, 0)
    assert not any(r['event']=='LOGGER_ERROR' for r in rows)
    (ROOT/'research/phase2b_p0/validation/synthetic_ready.jsonl').write_text(''.join(captured), encoding='utf-8')
    lua.execute('boardDefExposed=true; boardAvailable=true; callbacks.onUpdate(0.2)')
    rows,errors=parse(''.join(captured))
    assert not errors
    assert any(r['event']=='CREDITS_BOARD_AVAILABLE' for r in rows)
    assert any(r['event']=='LISTENERS_READY' for r in rows)
    assert rows[-1]['state']['credit_listener_count']==6
    assert isinstance(rows[-1]['state']['credits']['CredditsScrolling'], bool)
    assert readiness_failures(rows, 0)==[], readiness_failures(rows, 0)
    lua.execute('callbacks.onUpdate(0.2)')
    rows,_=parse(''.join(captured))
    assert sum(r['event']=='LISTENERS_READY' for r in rows)==1
    lua.execute('hooks["PlayerPuppet.OnDetach"]({})')
    rows,_=parse(''.join(captured))
    assert rows[-1]['state']['fact_listener_count']==0
    assert rows[-1]['state']['credit_listener_count']==6
    lua.execute('callbacks.onUpdate(0.2)')
    rows,_=parse(''.join(captured))
    assert rows[-1]['state']['fact_listener_count']==31
    assert rows[-1]['state']['credit_listener_count']==6
    # Fresh state, callbacks with real documented proxy shapes, routing then teardown.
    lua.execute('facts.q307_active=0; facts.q307_done=1; facts.q307_finished=1; credits.CredditsScrolling=true; credits.FinalBoardsOpened=true')
    by_event={e['event']: e for e in manifest['events']}
    for stage in STAGES:
        if stage=='DR02': lua.execute('credits.LoadPonRSave=false')
        if stage=='DR07':
            lua.execute('hooks["MenuScenario_FinalBoards.OnCloseFinalBoardsRequest"]({}); credits.CredditsScrolling=false; credits.FinalBoardsOpened=false; hooks["MenuScenario_Idle.OnEnterScenario"]({})')
        if stage=='DR09': lua.execute('tier=1')
        if stage=='DR10': lua.execute('visible=true')
        if stage.startswith('DR11_'):
            i=int(stage.split('_')[1])-1
            lua.globals().clearRestriction=manifest['restrictions'][i]
            lua.execute('restrictions[clearRestriction]=false')
        if stage=='DR13': lua.execute('blocked=false; facts.PostTowerFreeRoamActive=1')
        lua.globals().factName=by_event[stage]['fact']
        lua.execute('facts[factName]=1; listeners[factName](1)')
    lua.execute('callbacks.onUpdate(1.1); callbacks.onShutdown()')
    rows,errors=parse(''.join(captured))
    assert not errors
    result=analyze(rows)
    assert result['status']=='CORE_STATE_SUPPORTED_MOVEMENT_NEEDS_HUMAN_OBSERVATION', result
    assert all(r['state']['tier'] in (1,5) for r in rows)
    assert all('q307_2079' in r['state']['facts'] for r in rows)
    assert not result['logger_errors'] and not result['read_errors'], result
    # Keep sample lines for reproducible parser CLI validation. Clearly synthetic.
    sample=ROOT/'research/phase2b_p0/validation/synthetic_runtime.jsonl'
    sample.write_text(''.join(captured), encoding='utf-8')
    return rows


def parser_checks(rows):
    def run_edit(event):
        data=copy.deepcopy(rows)
        first=next(r for r in data if r['event']=='DR07')
        first['event']=event
        return analyze(data)
    assert run_edit('DR16')['same_session']=='NOT_RETAINED_OR_TRANSITION_OBSERVED'
    assert run_edit('DR17')['same_session']=='NOT_RETAINED_OR_TRANSITION_OBSERVED'
    assert run_edit('PLAYER_DETACH')['same_session']=='NOT_RETAINED_OR_TRANSITION_OBSERVED'
    assert run_edit('PREEXISTING_MARKER')['status']=='INVALID_OR_STALE_TRACE'
    missing=copy.deepcopy(rows);missing.pop(2)
    assert analyze(missing)['status']=='INVALID_OR_STALE_TRACE'
    no_callback=copy.deepcopy(rows)
    for r in no_callback:
        if r['event']=='CLOSE_REQUEST':r['event']='NOT_OBSERVED'
    assert analyze(no_callback)['same_session']=='UNKNOWN'
    unknown=copy.deepcopy(rows)
    for r in unknown:
        r['state']['credits']['FinalBoardsOpened']='UNKNOWN'
    assert analyze(unknown)['same_session']=='UNKNOWN'
    unexposed=copy.deepcopy(rows)
    for r in unexposed:
        r['state']['credits']={name:'UNKNOWN' for name in r['state']['credits']}
        r['state']['credits_board_status']='DEFINITION_UNEXPOSED'
    idle_index=next(i for i,r in enumerate(unexposed) if r['event']=='IDLE_ENTER')
    teardown=copy.deepcopy(unexposed[idle_index])
    teardown['event']='CREDITS_UNINITIALIZE'
    unexposed.insert(idle_index,teardown)
    for seq,r in enumerate(unexposed,1):r['seq']=seq
    fallback=analyze(unexposed)
    assert fallback['credits_teardown_evidence']=='INFERRED_UI_CLOSE_UNINITIALIZE_IDLE'
    assert fallback['same_session'].startswith('INFERRED_RETAINED')
    early=copy.deepcopy(rows)
    next(r for r in early if r['event']=='DR08')['state']['credits']['CredditsScrolling']=True
    assert analyze(early)['status']=='REJECT_GATE_PRESENTATION_STILL_ACTIVE'
    later=copy.deepcopy(rows)
    last=copy.deepcopy(later[-1]);last['seq']+=1;last['event']='DR16';later.append(last)
    assert analyze(later)['same_session'].startswith('INFERRED_RETAINED')
    mixed=copy.deepcopy(rows)
    r=copy.deepcopy(rows[0]);r['run_id']='newest-empty-run';mixed.append(r)
    assert analyze(mixed)['same_session']=='UNKNOWN'
    assert analyze([])['status']=='NO_VALID_TRACE'
    assert parse('[PTFR] invalid')[1]
    assert analyze(rows, [{'line':1,'error':'malformed'}])['same_session']=='UNKNOWN'
    return 14


if __name__=='__main__':
    m=graph_checks();rows=logger_checks(m);n=parser_checks(rows)
    report={'graph_checks':'PASS','lua_runtime':'LuaJIT 2.1 (lupa); mocked APIs, not live CET',
            'logger_mock':'PASS','parser_cases':n,'runtime_validated':False,
            'archive_sha256':m['sha256'],'synthetic_events':len(rows)}
    (ROOT/'research/phase2b_p0/validation/preflight.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
