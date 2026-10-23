"""Focused native preservation + read-only Lua51 probe checks; no engine test."""
import hashlib
import json
import sys
from pathlib import Path
from audit_world_interactions import walk

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/radio_memorial_validation'
BATCH=ROOT/'research/b0_world_interactions/batch'


def load(name):
    return json.loads((BATCH/(name+'.json')).read_text(encoding='utf-8-sig'))['Data']['RootChunk']


def handles(root):
    return {str(o['HandleId']):o['Data'] for o in walk(root) if 'HandleId' in o}


def canonical(value,h):
    if isinstance(value,list):return [canonical(v,h) for v in value]
    if not isinstance(value,dict):return value
    if 'HandleId' in value or 'HandleRefId' in value:
        return canonical(h[str(value.get('HandleId',value.get('HandleRefId')))],h)
    return {k:canonical(v,h) for k,v in value.items() if k!='sockets'}


def nodes(root):
    h=handles(root)
    return {n['id']:n for n in (h[str(o.get('HandleId',o.get('HandleRefId')))]
                               for o in root['graph']['Data']['nodes'])}


def native():
    before,after=load('Radio_original'),load('Radio_owner')
    b,a=nodes(before),nodes(after);bh,ah=handles(before),handles(after)
    old,new=canonical(b[17]['phaseGraph'],bh),canonical(a[17]['phaseGraph'],ah)
    old_stop=next(n for n in old['nodes'] if n['id']==12)
    new_stop=next(n for n in new['nodes'] if n['id']==12)
    assert new_stop['condition']['operation']=='OR'
    assert new_stop['condition']['conditions'][0]==old_stop['condition']
    old_stop['condition']=new_stop['condition']
    assert old==new, 'Radio scheduling/outcome selection changed'
    assert canonical(b[19],bh)==canonical(a[19],ah)
    assert a[20]['condition']['Data']['type']['Data']['factName']=='PTFRWORLD_Radio_Applied'
    assert a[21]['type']['Data']['factName']=='PTFRWORLD_Radio_Applied'
    assert before['phasePrefabs']==after['phasePrefabs']==[]
    original,installed=load('Memorial_original'),load('Memorial_owner')
    original_actions=[o for o in walk(original) if o.get('$type')=='questTogglePrefabVariant_NodeTypeParams']
    actions=[o for o in walk(installed) if o.get('$type')=='questTogglePrefabVariant_NodeTypeParams']
    assert actions==original_actions and len(actions)==34
    assert not any(o.get('$type')=='questSpawnManagerNodeDefinition' for o in walk(installed))
    assert {o['factName'] for o in walk(installed) if o.get('$type')=='questSetVar_NodeType'}=={'PTFRWORLD_Memorial_Registered'}
    assert not installed['phasePrefabs']
    refs={o['prefabNodeRef']['$value'] for o in actions}
    assert refs=={'#loc_q204_columbarium_devices'}
    manifest=json.loads((BATCH/'manifest.json').read_text())
    for key in ('Radio','Memorial'):
        gate=load(key+'_gate');n=nodes(gate)
        cond=n[1]['condition']['Data']
        assert cond['operation']=='AND' and not gate['phasePrefabs']
        actual={o['Data']['type']['Data']['factName']:o['Data']['type']['Data'] for o in cond['conditions']}
        expected=manifest['guards']|{f'PTFRWORLD_{key}_Suspended':0,f'PTFRWORLD_{key}_QuestOwns':0}
        assert set(actual)==set(expected)
        assert all(actual[f]['comparisonType']=='Equal' and actual[f]['value']==v for f,v in expected.items())
    return dict(radio_child_preserved=True,memorial_actions=34,memorial_refs=list(refs),
                variants=[dict(reference=o['prefabNodeRef']['$value'],states=o['variantStates']) for o in actions],
                facts=sorted({o['factName'] for o in walk(original) if o.get('factName')}),
                no_memorial_outcome_writers_or_actor_spawn=True)


def lua_tests():
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    source=(ROOT/'diagnostics/PTFR_RadioMemorial_Audit/init.lua').read_text()
    assert not any(x in source for x in ('SetFact','NewObject','SendDebug','QueueEvent','Teleport','Spawn','SetEntry','ChangeEntry'))
    setup='''
    events={};rows={};writes=0;flushes=0;closes=0;reads=0;failOpen=false;failWrite=false
    function print(s) end
    function registerForEvent(n,f)events[n]=f end
    function IsDefined(p)return p~=nil end
    json={encode=function(r)table.insert(rows,r);return '{}' end}
    io={open=function(n,m)
      if m=='r' or failOpen then return nil end
      return {write=function(self,s)if failWrite then return nil,'disk full' end;writes=writes+1;return self end,
        flush=function()flushes=flushes+1;return true end,
        close=function()closes=closes+1;return true end} end}
    radio={IsActive=function()return true end,IsRestricted=function()return false end,
      GetStation=function()return 1 end,GetStationName=function()return 'station' end,GetTrackName=function()return 'track' end}
    player={GetWorldPosition=function()return{x=0,y=0,z=0}end,IsInCombat=function()return false end,
      GetEntityID=function()return{}end,GetPocketRadio=function()return radio end,GetMountedVehicle=function()return nil end}
    q={GetFactStr=function(self,f)reads=reads+1;return 1 end,SetFactStr=function()error('FORBIDDEN')end}
    Game={GetPlayer=function()return player end,GetQuestsSystem=function()return q end,
      GetSceneSystem=function()return{GetScriptInterface=function()return{IsEntityInScene=function()return false end}end}end,
      GetWorkspotSystem=function()return{IsActorInWorkspot=function()return false end}end}
    '''
    def fresh():
        rt=LuaRuntime(unpack_returned_tuples=True);rt.execute(setup);return rt,rt.execute(source)
    rt,m=fresh();m.Mark('idle');assert rt.eval('writes')==0
    m.Start();m.Start();assert rt.eval('writes')==1
    rt.execute('events.onUpdate(2)');m.Mark('radio-on');m.Stop()
    assert rt.eval('writes')==rt.eval('flushes')==rt.eval('closes')==4
    assert rt.eval('rows[1].pocket_radio.active') and not rt.eval('rows[1].vehicle_radio.mounted')
    reads=rt.eval('reads');rt.execute('events.onUpdate(3)');assert reads==rt.eval('reads')
    rt,m=fresh();rt.execute('player=nil');m.Start();m.Stop();assert not rt.eval('rows[1].player_present')
    rt,m=fresh();rt.execute("q.GetFactStr=function()error('unavailable')end");m.Start();m.Stop()
    assert rt.eval("rows[1].facts.errors.radio_on") is not None
    rt,m=fresh();m.Start();rt.execute("radio.GetTrackName=function()error('no metadata')end");m.Mark('missing')
    assert rt.eval('rows[2].pocket_radio.track_name')=='UNAVAILABLE';m.Stop()
    for failure in ('failOpen','failWrite'):
        rt,m=fresh();rt.execute(failure+'=true');m.Start();reads=rt.eval('reads')
        rt.execute('events.onUpdate(3)');assert rt.eval('reads')==reads
    rt,m=fresh();m.Start();rt.execute('events.onUpdate(601)');reads=rt.eval('reads')
    rt.execute('events.onUpdate(3)');assert rt.eval('reads')==reads
    rt,m=fresh();m.Start();rt.execute('events.onShutdown()');assert rt.eval('closes')==2
    return 'PASS_LUA51_READ_ONLY_LIFECYCLE_AND_FAILURE_MOCKS_NOT_ENGINE'


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    result=native();result['lua']=lua_tests()
    result['status']='STATIC_NATIVE_PRESERVATION_AND_PROBE_PASS_LIVE_OUTPUT_UNVERIFIED'
    result['probe_sha256']=hashlib.sha256((ROOT/'diagnostics/PTFR_RadioMemorial_Audit/init.lua').read_bytes()).hexdigest()
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('variants','facts')},indent=2))
