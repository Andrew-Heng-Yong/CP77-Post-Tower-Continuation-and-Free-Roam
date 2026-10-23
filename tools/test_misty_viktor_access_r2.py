"""Exact native scope, guard/yield and unchanged geometry tests. No engine writes."""
import copy
import hashlib
import json
from pathlib import Path
from audit_world_interactions import walk
from test_radio_memorial import handles, canonical, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_optin import evaluate

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/misty_viktor_world'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    m=read(BASE/'access_r2_manifest.json')
    old=read(BASE/'revision1/shell_optin.json')['Data']['RootChunk']
    r=read(BASE/'access_r2.json')['Data']['RootChunk']
    h=handles(r);n=nodes(r);oh=handles(old);on=nodes(old)
    assert len(n)==19 and not r['phasePrefabs']
    assert quest_edges(r)[0]=={(a,s,b,'In') for a,s,b in m['edges']}
    for o in walk(r):
        if 'HandleRefId' in o: assert str(o['HandleRefId']) in h
    for i in range(10):
        for key in ('type','condition'):
            if key in on[i]:assert canonical(n[i][key],h)==canonical(on[i][key],oh),(i,key)
    facts=m['guards'];entry=canonical(n[2]['condition'],h);stop=canonical(n[5]['condition'],h)
    restore=canonical(n[13]['condition'],h)
    assert len(restore['conditions'])==len(facts)-1
    assert evaluate(entry,facts) and not evaluate(stop,facts)
    assert evaluate(restore,facts|{'PTFRMV_Enabled':0})
    negative=0
    for f,v in facts.items():
        for bad in (-1,0,1,2):
            if bad==v:continue
            ff=facts|{f:bad};assert not evaluate(entry,ff) and evaluate(stop,ff)
            if f!='PTFRMV_Enabled':assert not evaluate(restore,ff)
            negative+=1
    v=read(ROOT/'research/q307_extracted/json/ep1/quest/main_quests/q307/phases/q307_06_viktor.questphase.json')['Data']['RootChunk']
    vh=handles(v);vn=nodes(v)
    for i,source,action in ((11,20,'ForceUnlock'),(14,19,'ForceCloseImmediate'),(15,20,'ForceLock')):
        expected=canonical(vn[source]['type'],vh)
        assert len(expected['params'])==1
        p=expected['params'][0];assert p['objectRef']['$value']=='#q115_misty_door_back'
        p['objectRef']['$value']=m['rear_door'];p['deviceAction']['$value']=action
        assert canonical(n[i]['type'],h)==expected
    for i,show in ((10,0),(16,1)):
        payload=canonical(n[i]['type'],h);assert len(payload['params'])==1
        p=payload['params'][0];assert p['prefabNodeRef']['$value']==m['neon_owner']
        assert len(p['variantStates'])==1 and p['variantStates'][0]['name']['$value']=='neon_hide'
        assert p['variantStates'][0]['show']==show
    # One existing entity carries both aliases: no duplicated Tower door spawn.
    world=read(ROOT/'research/phase2b_p4/variant_sectors/ep1_1_nightcity/json/base/worlds/03_night_city/_compiled/default/exterior_-25_18_0_0.streamingsector.json')['Data']['RootChunk']
    d=world['nodeData']['Data'][1540]
    assert d['QuestPrefabRefHash']['$value']==m['rear_door']+';#q307_zetatech_doors_02'
    assert world['nodes'][d['NodeIndex']]['Data']['$type']=='worldEntityNode'
    # Complete old-sign ranges contain only sign meshes/beads and their colliders.
    for index in range(3396,3516):
        o=world['nodes'][world['nodeData']['Data'][index]['NodeIndex']]['Data']
        name=o['debugName']['$value']
        assert name.startswith(('hanging_beads_module_d','quest_signage_b_mistys','VariantCollisionNode_085'))
        assert o['$type'] in ('worldStaticMeshNode','worldCollisionNode')
    assert world['nodes'][world['nodeData']['Data'][4519]['NodeIndex']]['Data']['debugName']['$value']=='VariantCollisionNode_084'
    for index in (3515,4519):
        o=world['nodes'][world['nodeData']['Data'][index]['NodeIndex']]['Data']
        assert all(a['Position']['z']['Bits']/131072>19 for a in o['compiledData']['Data']['Actors'])
    unchanged={}
    for depot in m['resources'][:-1]:
        a=ROOT/'build/MistyViktorShellOptIn/source'/depot;b=ROOT/'build/MistyViktorAccessR2/source'/depot
        assert a.read_bytes()==b.read_bytes();unchanged[depot]=hashlib.sha256(a.read_bytes()).hexdigest()
    writers={o['factName'] for o in walk(r) if o.get('$type')=='questSetVar_NodeType'}
    assert writers=={'PTFRMV_Registered','PTFRMV_Revision','PTFRMV_Applied','PTFRMV_Acquires','PTFRMV_Releases','PTFRMV_AccessRequests','PTFRMV_RestoreRequests'}
    assert not any(o.get('$type') in ('questSceneNodeDefinition','questSpawnManagerNodeDefinition','questPhaseNodeDefinition') for o in walk(r))
    archive=Path(m['archive']);assert hashlib.sha256(archive.read_bytes()).hexdigest().upper()==m['sha256']
    assert hashlib.sha256(Path(str(archive)+'.xl').read_bytes()).hexdigest().upper()==m['xl_sha256']
    # Exercise bridge against mocked CET; nothing contacts the game.
    import sys
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    probe=(ROOT/'diagnostics/PTFR_MistyViktor_World/init.lua').read_text()
    assert probe.count('SetFactStr("PTFRMV_Enabled",')==2
    lua.execute('''events={};writes={};f={};pos={x=-1658.9,y=997.4,z=23.7}
    function IsDefined(x)return x~=nil end
    function registerForEvent(n,cb)events[n]=cb end
    function print(...)end
    json={encode=function()return 'row' end}
    io={open=function(n,m)if m=='r' then return nil end;return {write=function(self)return self end,flush=function()return true end,close=function()return true end}end}
    local q={GetFactStr=function(self,k)return f[k] or 0 end,SetFactStr=function(self,k,v)f[k]=v;writes[#writes+1]={k,v}end}
    Game={GetQuestsSystem=function()return q end,GetPlayer=function()return {GetWorldPosition=function()return pos end}end}''')
    mod=lua.execute(probe);lf=lua.globals().f
    for k,v in facts.items():lf[k]=v
    lf.PTFRMV_Registered=1;lf.PTFRMV_Enabled=0
    mod.Start();assert len(lua.globals().writes)==0
    lf.PTFRMV_Revision=2;mod.Start();mod.Start();assert len(lua.globals().writes)==1
    lua.execute('pos={x=-1542,y=1210,z=16}');mod.Stop();assert lf.PTFRMV_Enabled==1
    lua.execute('pos={x=-1658.9,y=997.4,z=23.7}');mod.Stop();assert lf.PTFRMV_Enabled==0
    mod.Finish();lf.q307_active=1;mod.Start();assert len(lua.globals().writes)==2
    report={'status':'PASS_R2_OFFLINE_NOT_LIVE','archive_sha256':m['sha256'],'xl_sha256':m['xl_sha256'],
            'probe_sha256':hashlib.sha256(probe.encode()).hexdigest().upper(),'native_nodes':len(n),
            'negative_guards':negative,'geometry_unchanged':unchanged,'door_entities_added':0,
            'story_writers':0,'scene_starts':0,'live_tested':False}
    (BASE/'access_r2_tests.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
