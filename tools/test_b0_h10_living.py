"""Offline scope, graph-path, and LuaJIT checks. Never opens the game or saves."""
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

VAL = ROOT / 'research/b0_h10_living/validation'
GUARD = dict(PostTowerFreeRoamActive=1, PTFRP0_DR13=1, q307_active=0,
             q307_done=1, q307_finished=1, q307_2079=1, q307_main_game_killed=1,
             PTFRB0H10_Claimed=1, PTFRB0H10_OwnerEntered=1,
             PTFRB0H10L_Claimed=0, PTFRB0H10L_OwnerEntered=0, PTFRB0H10L_Hold=0)
WRITERS = {'PTFRB0H10L_Ready', 'PTFRB0H10L_Request', 'PTFRB0H10L_Claimed',
           'PTFRB0H10L_Rejected', 'PTFRB0H10L_OwnerEntered'}


def walk(v):
    if isinstance(v, dict):
        yield v
        for child in v.values():
            yield from walk(child)
    elif isinstance(v, list):
        for child in v:
            yield from walk(child)


def plain(v):
    if hasattr(v, 'items'):
        data = dict(v.items())
        if data and all(isinstance(k, int) for k in data):
            return [plain(data[k]) for k in sorted(data)]
        return {k: plain(x) for k, x in data.items()}
    return v


def native_checks():
    gate = json.loads((VAL / 'gate.json').read_text(encoding='utf-8'))
    owner = json.loads((VAL / 'owner.json').read_text(encoding='utf-8'))
    manifest = json.loads((VAL / 'build_manifest.json').read_text(encoding='utf-8'))
    terms = {d['factName']: d['value'] for d in walk(gate)
             if d.get('$type') == 'questVarComparison_ConditionType'
             and d['factName'] != 'PTFRB0H10L_Request'}
    assert terms == GUARD == manifest['native_guard'], terms
    all_writers = set()
    for data in (gate, owner):
        for d in walk(data):
            if d.get('$type') == 'questSetVar_NodeType':
                assert d['setExactValue'] == 1 and d['value'] in (0, 1)
                all_writers.add(d['factName'])
            if d.get('$type') == 'questVarComparison_ConditionType':
                assert d['comparisonType'] == 'Equal'
        types = {d['$type'] for d in walk(data) if d.get('$type', '').endswith('NodeDefinition')}
        assert types <= {'questInputNodeDefinition', 'questFactsDBManagerNodeDefinition',
                         'questPauseConditionNodeDefinition', 'questConditionNodeDefinition',
                         'questPhaseNodeDefinition'}, types
        root = data['Data']['RootChunk']
        assert root['inplacePhases'] == [] and data['Data']['EmbeddedFiles'] == []
    assert all_writers == WRITERS
    assert gate['Data']['RootChunk']['phasePrefabs'] == []
    prefab = owner['Data']['RootChunk']['phasePrefabs']
    assert len(prefab) == 1 and prefab[0]['prefabNodeRef']['$value'] == '#vs_apartment_arch_living'
    refs = {d['DepotPath']['$value'] for d in walk(gate) if 'DepotPath' in d
            and d['DepotPath']['$value'] != '0'}
    assert refs == {r'towercontinued\b0_h10_living\living_owner.questphase'}, refs
    assert manifest['registration_parent'] == r'ep1\quest\ep1.quest'
    xl = (ROOT / 'archive/b0_h10_living/TowerContinued_B0_H10_Living.archive.xl').read_text()
    assert 'parent: ep1\\quest\\ep1.quest' in xl and 'node: [1]' in xl
    assert 'output:' not in xl and 'intercept:' not in xl and xl.count('path:') == 1
    sector_path = ROOT / ('research/b0_missing_content/h10_architecture/ep1_1_nightcity/json/'
                          'base/worlds/03_night_city/_compiled/default/quest_acd280b2b73c4d5b.streamingsector.json')
    sector = json.loads(sector_path.read_text())['Data']['RootChunk']
    # Nodes are inline handle definitions in this export.
    types = [n['Data']['$type'] for n in sector['nodes']]
    assert len(types) == 166 and types.count('worldStaticMeshNode') == 144 and types.count('worldCollisionNode') == 12 and types.count('worldStaticDecalNode') == 10, types

    # Execute the actual serialized edges with a deliberately small semantic model.
    def graph(data):
        handles = {d['HandleId']: d['Data'] for d in walk(data) if 'HandleId' in d and 'Data' in d}
        def deref(d):
            return d['Data'] if 'Data' in d else handles[d['HandleRefId']]
        nodes = {deref(h)['id']: deref(h) for h in data['Data']['RootChunk']['graph']['Data']['nodes']}
        return nodes, deref
    nodes, deref = graph(gate)
    edges = {}
    for edge in manifest['graphs']['gate']['edges']:
        src, dst = edge.split(' -> '); edges[src] = int(dst.split('.')[0])
    def simulate(facts):
        facts = dict(facts); at = 0
        for _ in range(20):
            n = nodes[at]; typ = n['$type']; port = 'Out'
            if typ == 'questInputNodeDefinition':
                pass
            elif typ == 'questFactsDBManagerNodeDefinition':
                op = deref(n['type']); facts[op['factName']] = op['value']
            elif typ == 'questPauseConditionNodeDefinition':
                op = deref(deref(n['condition'])['type'])
                if facts.get(op['factName'], 0) != op['value']:
                    return facts, False
            elif typ == 'questConditionNodeDefinition':
                cond = deref(n['condition']); assert cond['operation'] == 'AND'
                ok = all(facts.get((op := deref(deref(c)['type']))['factName'], 0) == op['value'] for c in cond['conditions'])
                port = 'True' if ok else 'False'
            elif typ == 'questPhaseNodeDefinition':
                assert at == 7
                return facts, True
            else:
                raise AssertionError(typ)
            at = edges[f'{at}.{port}']
        raise AssertionError('unbounded path')
    assert simulate(GUARD)[1] is False  # passive bootstrap cannot acquire floor
    facts = GUARD | {'PTFRB0H10L_Request': 1}
    after, acquired = simulate(facts)
    assert acquired and after['PTFRB0H10L_Request'] == 0 and after['PTFRB0H10L_Claimed'] == 1
    for key in GUARD:
        after, acquired = simulate(facts | {key: 1 - GUARD[key]})
        assert not acquired and after['PTFRB0H10L_Rejected'] == 1, key
    assert not simulate(after | {'PTFRB0H10L_Claimed': 1, 'PTFRB0H10L_Request': 1})[1]
    return 19


SETUP = r'''
events={}; lines={}; calls={}; facts={}; position={x=-1400,y=1272,z=123}
for k,v in pairs({PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_active=0,q307_done=1,
 q307_finished=1,q307_2079=1,q307_main_game_killed=1,
 PTFRB0H10_Claimed=1,PTFRB0H10_OwnerEntered=1,PTFRB0H10L_Ready=1}) do facts[k]=v end
function registerForEvent(n,f) events[n]=f end
function ObserveAfter(c,n,f) attach=f end
function ObserveBefore(c,n,f) detach=f end
function IsDefined(o) return o~=nil end
function print(...) end
json={encode=function(v) return py_encode(v) end}
io={open=function() if openError then return nil,'mock open failure' end
 return {write=function(self,v) if writeError then error('mock disk full') end;lines[#lines+1]=v;return self end,
 flush=function() if flushError then error('mock flush failure') end;return true end,close=function() end} end}
local qs={GetFactStr=function(self,n) if factError==n then error('mock fact error') end;return facts[n] or 0 end,
 SetFactStr=function(self,n,v) assert(n=='PTFRB0H10L_Request' and v==1,'ILLEGAL WRITE');calls[#calls+1]={name=n,value=v};
  if requestError then error('uncertain native request') end;facts[n]=v end}
local bb={GetInt=function(self,k) return tier or 1 end}
local player={GetEntityID=function() return {hash=123ULL} end,GetWorldPosition=function() return position end,
 GetPlayerStateMachineBlackboard=function() return bb end}
Game={GetPlayer=function() if noPlayer then return nil end;return player end,GetQuestsSystem=function() return qs end,
 GetSceneSystem=function() return {GetScriptInterface=function() return {IsEntityInScene=function() return inScene or false end} end} end,
 GetWorkspotSystem=function() return {IsActorInWorkspot=function() return inWorkspot or false end} end,
 GetMountingFacility=function() return {GetMountingInfoSingleWithObjects=function() return {parentId={hash=mounted and 1ULL or 0ULL}} end} end,
 GetQuestsContentSystem=function() return {IsTokensActivationBlocked=function() return blocked or false end} end,
 IsSavingLocked=function() return false end,
 GetJournalManager=function() return {GetEntryByString=function(self,p,c) return {} end,GetEntryState=function() return 'Active' end,IsEntryTracked=function() return false end} end,
 GetSpatialQueriesSystem=function() return {SyncRaycastByCollisionGroup=function()
  if rayError then error('optional ray API failure') end;return true,{position={x=-1382,y=1272,z=123}} end} end}
function GetAllBlackboardDefs() return {PlayerStateMachine={HighLevel='HighLevel',SceneTier='SceneTier'}} end
Vector4={new=function(x,y,z,w) return {x=x,y=y,z=z,w=w} end};CName={new=function(s) return s end}
'''


class Fixture:
    def __init__(self, before=''):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.globals().py_encode = lambda v: json.dumps(plain(v))
        self.lua.execute(SETUP + before)
        self.mod = self.lua.execute((ROOT / 'diagnostics/PTFR_B0_H10_Living/init.lua').read_text())
        self.run('events.onInit();if attach then attach() end;events.onUpdate(6)')

    def run(self, code):
        return self.lua.execute(code)

    def count(self):
        return len(self.lua.globals().calls)

    def rows(self):
        return [json.loads(x) for _, x in self.lua.globals().lines.items()]


def lua_checks():
    count = 0
    f = Fixture(); f.run('events.onUpdate(60)')
    assert f.count() == 0
    assert f.mod.Inspect('baseline') is True
    assert f.count() == 0 and f.mod.Restore() is True and f.count() == 1
    assert f.mod.Restore() is False and f.count() == 1
    f.run('events.onUpdate(35)')
    assert len([r for r in f.rows() if r['event'] == 'AFTER_REQUEST']) == 3
    assert f.mod.Report('yes', 'no', 'unknown', 'no') is True
    assert f.mod.Report('yes', 'yes', 'yes', 'maybe') is False
    count += 7
    for bad in ['noPlayer=true', 'inScene=true', 'inWorkspot=true', 'mounted=true',
                'blocked=true', 'tier=2', 'position.x=-1382', 'position.x=0',
                'position.x=0/0', 'factError="q307_done"', 'facts.PTFRB0H10L_Ready=0',
                'facts.PTFRB0H10L_Request=1', 'facts.PTFRB0H10L_Claimed=1',
                'facts.PTFRB0H10L_OwnerEntered=1', 'facts.PTFRB0H10L_Hold=1',
                'facts.PTFRB0H10L_Rejected=1']:
        f = Fixture(bad); assert not f.mod.Inspect(), bad
        assert not f.mod.Restore() and f.count() == 0, bad
        count += 1
    for k, v in GUARD.items():
        f = Fixture(f'facts.{k}={1-v}'); f.mod.Inspect()
        assert not f.mod.Restore() and f.count() == 0, k
        count += 1
    for bad in ['openError=true', 'writeError=true', 'flushError=true']:
        f = Fixture(bad); f.mod.Inspect();assert not f.mod.Restore() and f.count() == 0
        count += 1
    f = Fixture(); assert not f.mod.Restore() and f.count() == 0;count += 1
    f = Fixture();f.mod.Inspect();f.run('events.onUpdate(121)');assert not f.mod.Restore();count += 1
    f = Fixture();f.mod.Inspect();f.run('detach();attach();events.onUpdate(6)');assert not f.mod.Restore();count += 1
    f = Fixture();f.mod.Inspect();f.run('inScene=true');assert not f.mod.Restore();count += 1
    f = Fixture('rayError=true');assert f.mod.Inspect() and f.mod.Restore();count += 1
    f = Fixture('requestError=true');f.mod.Inspect();assert not f.mod.Restore()
    assert not f.mod.Restore() and f.count() == 1;count += 1
    f = Fixture();f.mod.Inspect();f.mod.Restore()
    f.run('detach();attach();events.onUpdate(60)')
    assert f.count() == 1 and not any(r['event'] == 'AFTER_REQUEST' for r in f.rows());count += 1
    return count


if __name__ == '__main__':
    native = native_checks()
    lua = lua_checks()
    result = dict(status='PASS', native_scope_and_path_checks=native, lua_checks=lua,
                  runtime_tested=False, note='Mocks and serialized-graph checks do not prove native streaming/persistence.',
                  tested_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [ROOT / 'diagnostics/PTFR_B0_H10_Living/init.lua',
                                           VAL / 'gate.json', VAL / 'owner.json', VAL / 'build_manifest.json',
                                           ROOT / 'archive/b0_h10_living/TowerContinued_B0_H10_Living.archive.xl']})
    (VAL / 'test_results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
