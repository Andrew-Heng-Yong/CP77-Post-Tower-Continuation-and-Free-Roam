"""Offline validation of the serialized staged H10 archive and manual CET gate."""
import collections
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

VAL = ROOT / 'research/b0_h10_architecture/validation'
TARGETS = {
    'entrance': ('PTFRB0H10A_E_', '#vs_apartment_arch_entrance', 'quest_3509076113f76078.streamingsector.json'),
    'bedroom': ('PTFRB0H10A_B_', '#vs_apartment_arch_bedroom', 'quest_2467054678ccf8f6.streamingsector.json'),
    'bathroom': ('PTFRB0H10A_W_', '#vs_apartment_arch_bathroom', 'quest_2be595b225125038.streamingsector.json'),
}
BASE = dict(PostTowerFreeRoamActive=1, PTFRP0_DR13=1, q307_active=0,
            q307_done=1, q307_finished=1, q307_2079=1, q307_main_game_killed=1,
            PTFRB0H10_Claimed=1, PTFRB0H10_OwnerEntered=1,
            PTFRB0H10L_Claimed=1, PTFRB0H10L_OwnerEntered=1)
DEPEND = {'entrance': {},
          'bedroom': dict(PTFRB0H10A_E_Claimed=1, PTFRB0H10A_E_OwnerEntered=1),
          'bathroom': dict(PTFRB0H10A_B_Claimed=1, PTFRB0H10A_B_OwnerEntered=1)}


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
    manifest = json.loads((VAL / 'build_manifest.json').read_text())
    assert len(manifest['resources']) == 6 and not manifest['vanilla_replacements']
    assert len(set(manifest['registration_ids'].values())) == 3
    assert set(manifest['registration_ids'].values()).isdisjoint({9908, 19904})
    xl = (ROOT / 'archive/b0_h10_architecture/TowerContinued_B0_H10_Architecture.archive.xl').read_text()
    assert xl.count('parent: ep1\\quest\\ep1.quest') == 3
    assert xl.count('node: [1]') == 3 and 'intercept:' not in xl and 'output:' not in xl
    expected_edges = sorted(['0.Out -> 1.In', '1.Out -> 2.In', '2.Out -> 3.In',
                             '3.Out -> 4.In', '4.True -> 5.In', '5.Out -> 6.In',
                             '6.Out -> 7.In1', '4.False -> 8.In', '8.Out -> 2.In'])
    for key, (prefix, prefab, sector) in TARGETS.items():
        gate = json.loads((VAL / f'{key}_gate.json').read_text())
        owner = json.loads((VAL / f'{key}_owner.json').read_text())
        assert sorted(manifest['graphs'][key + '_gate']['edges']) == expected_edges
        assert sorted(manifest['graphs'][key + '_owner']['edges']) == ['0.Out -> 1.In', '1.Out -> 2.In']
        assert gate['Data']['RootChunk']['phasePrefabs'] == []
        assert [x['prefabNodeRef']['$value'] for x in owner['Data']['RootChunk']['phasePrefabs']] == [prefab]
        for data in (gate, owner):
            assert data['Data']['RootChunk']['inplacePhases'] == [] and data['Data']['EmbeddedFiles'] == []
            types = {x['$type'] for x in walk(data) if x.get('$type', '').endswith('NodeDefinition')}
            assert types <= {'questInputNodeDefinition', 'questFactsDBManagerNodeDefinition',
                             'questPauseConditionNodeDefinition', 'questConditionNodeDefinition',
                             'questPhaseNodeDefinition'}, (key, types)
        guard = BASE | DEPEND[key] | {prefix+'Claimed': 0, prefix+'OwnerEntered': 0, prefix+'Hold': 0}
        terms = {x['factName']: x['value'] for x in walk(gate)
                 if x.get('$type') == 'questVarComparison_ConditionType'
                 and x['factName'] != prefix+'Request'}
        assert terms == guard == manifest['guards'][key], (key, terms)
        writers = {x['factName'] for x in list(walk(gate)) + list(walk(owner))
                   if x.get('$type') == 'questSetVar_NodeType'}
        assert writers == {prefix+x for x in ('Ready', 'Request', 'Claimed', 'Rejected', 'OwnerEntered')}
        refs = {x['DepotPath']['$value'] for x in walk(gate) if 'DepotPath' in x and x['DepotPath']['$value'] != '0'}
        assert refs == {rf'towercontinued\b0_h10_architecture\{key}_owner.questphase'}
        sector_path = (ROOT / 'research/b0_missing_content/h10_architecture/ep1_1_nightcity/json/'
                       'base/worlds/03_night_city/_compiled/default' / sector)
        nodes = json.loads(sector_path.read_text())['Data']['RootChunk']['nodes']
        counts = collections.Counter(x['Data']['$type'] for x in nodes)
        if key == 'entrance':
            assert counts == {'worldStaticMeshNode': 92, 'worldCollisionNode': 12}
        elif key == 'bedroom':
            assert counts == {'worldStaticMeshNode': 211, 'worldStaticDecalNode': 210,
                              'worldCollisionNode': 31, 'worldEntityNode': 30}
            templates = {x['Data']['entityTemplate']['DepotPath']['$value'] for x in nodes
                         if x['Data']['$type'] == 'worldEntityNode'}
            assert all('vending' in x for x in templates), templates
        else:
            assert counts == {'worldStaticMeshNode': 57, 'worldStaticDecalNode': 22,
                              'worldEntityNode': 12, 'worldCollisionNode': 10,
                              'worldClothMeshNode': 6, 'worldStaticParticleNode': 2}
            templates = {x['Data']['entityTemplate']['DepotPath']['$value'] for x in nodes
                         if x['Data']['$type'] == 'worldEntityNode'}
            assert templates == {r'base\quest\minor_quests\mq000\entities\mq000_shower.ent',
                                 r'base\gameplay\devices\home_appliances\toilet\toilet.ent'}
    return 3


SETUP = r'''
events={}; lines={}; calls={}; facts={}; position={x=-1400,y=1272,z=123}
for k,v in pairs({PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_active=0,q307_done=1,
 q307_finished=1,q307_2079=1,q307_main_game_killed=1,
 PTFRB0H10_Claimed=1,PTFRB0H10_OwnerEntered=1,PTFRB0H10L_Claimed=1,PTFRB0H10L_OwnerEntered=1,
 PTFRB0H10A_E_Ready=1,PTFRB0H10A_B_Ready=1,PTFRB0H10A_W_Ready=1}) do facts[k]=v end
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
 SetFactStr=function(self,n,v) assert((n=='PTFRB0H10A_E_Request' or n=='PTFRB0H10A_B_Request' or
 n=='PTFRB0H10A_W_Request') and v==1,'ILLEGAL WRITE');calls[#calls+1]={name=n,value=v};
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
 GetJournalManager=function() return {GetEntryByString=function() return {} end,GetEntryState=function() return 'Active' end,IsEntryTracked=function() return false end} end}
function GetAllBlackboardDefs() return {PlayerStateMachine={HighLevel='HighLevel',SceneTier='SceneTier'}} end
'''


class Fixture:
    def __init__(self, before=''):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.globals().py_encode = lambda v: json.dumps(plain(v))
        self.lua.execute(SETUP + before)
        self.mod = self.lua.execute((ROOT / 'diagnostics/PTFR_B0_H10_Architecture/init.lua').read_text())
        self.run('events.onInit();if attach then attach() end;events.onUpdate(6)')

    def run(self, code):
        return self.lua.execute(code)

    def count(self):
        return len(self.lua.globals().calls)


def lua_checks():
    f = Fixture()
    assert f.mod.Inspect('bedroom') is False and f.count() == 0
    assert f.mod.Inspect('bathroom') is False and f.count() == 0
    assert f.mod.Inspect('entrance') is True and f.count() == 0
    assert f.mod.Restore('entrance') is True and f.count() == 1
    assert f.mod.Restore('entrance') is False and f.count() == 1
    f.run('facts.PTFRB0H10A_E_Request=0;facts.PTFRB0H10A_E_Ready=0;facts.PTFRB0H10A_E_Claimed=1;facts.PTFRB0H10A_E_OwnerEntered=1;events.onUpdate(31)')
    assert f.mod.Inspect('bedroom') is True
    assert f.mod.Restore('bedroom') is True and f.count() == 2
    f.run('facts.PTFRB0H10A_B_Request=0;facts.PTFRB0H10A_B_Ready=0;facts.PTFRB0H10A_B_Claimed=1;facts.PTFRB0H10A_B_OwnerEntered=1;events.onUpdate(31)')
    assert f.mod.Inspect('bathroom') is True
    assert f.mod.Restore('bathroom') is True and f.count() == 3
    assert f.mod.Report('bathroom','yes','unknown','unknown','no') is True
    assert f.mod.Report('bathroom','yes','no','maybe','no') is False
    assert f.mod.Inspect('invalid') is False and f.mod.Restore('invalid') is False
    count = 14
    for bad in ['noPlayer=true', 'inScene=true', 'inWorkspot=true', 'mounted=true',
                'blocked=true', 'tier=2', 'position.x=-1382', 'position.x=0',
                'position.x=0/0', 'factError="q307_done"',
                'facts.PTFRB0H10A_E_Ready=0', 'facts.PTFRB0H10A_E_Request=1',
                'facts.PTFRB0H10A_E_Claimed=1', 'facts.PTFRB0H10A_E_OwnerEntered=1',
                'facts.PTFRB0H10A_E_Hold=1', 'facts.PTFRB0H10A_E_Rejected=1']:
        f = Fixture(bad)
        assert not f.mod.Inspect('entrance'), bad
        assert not f.mod.Restore('entrance') and f.count() == 0, bad
        count += 1
    for k,v in BASE.items():
        f = Fixture(f'facts.{k}={1-v}')
        assert not f.mod.Inspect('entrance') and not f.mod.Restore('entrance') and f.count() == 0
        count += 1
    for bad in ['openError=true', 'writeError=true', 'flushError=true']:
        f = Fixture(bad)
        f.mod.Inspect('entrance')
        assert not f.mod.Restore('entrance') and f.count() == 0
        count += 1
    f = Fixture(); assert not f.mod.Restore('entrance') and f.count() == 0; count += 1
    f = Fixture(); f.mod.Inspect('entrance'); f.run('events.onUpdate(121)')
    assert not f.mod.Restore('entrance') and f.count() == 0; count += 1
    f = Fixture(); f.mod.Inspect('entrance'); f.run('detach();attach();events.onUpdate(6)')
    assert not f.mod.Restore('entrance') and f.count() == 0; count += 1
    f = Fixture('requestError=true'); f.mod.Inspect('entrance')
    assert not f.mod.Restore('entrance') and not f.mod.Restore('entrance') and f.count() == 1; count += 1
    return count


if __name__ == '__main__':
    native = native_checks()
    lua = lua_checks()
    result = dict(status='PASS', native_scope_checks=native, lua_checks=lua, runtime_tested=False,
                  note='Offline checks do not prove streaming, collision, interaction, saved style, or persistence.',
                  tested_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in [ROOT / 'diagnostics/PTFR_B0_H10_Architecture/init.lua',
                                           ROOT / 'archive/b0_h10_architecture/TowerContinued_B0_H10_Architecture.archive.xl',
                                           VAL / 'build_manifest.json']
                                 + [p for key in TARGETS for p in (VAL / f'{key}_gate.json', VAL / f'{key}_owner.json')]})
    (VAL / 'test_results.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
