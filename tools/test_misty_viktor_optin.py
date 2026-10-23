"""Test native private-variant controller and opt-in bridge without engine writes."""
import binascii
import hashlib
import json
import re
import sys
from pathlib import Path
from audit_world_interactions import walk
from test_streetkid_scene_load_s3 import quest_edges
from test_radio_memorial import handles,canonical,nodes

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/misty_viktor_world'

def evaluate(c,f):
    if c['$type']=='questLogicalCondition':
        vals=[evaluate(x,f) for x in c['conditions']]
        return all(vals) if c['operation']=='AND' else any(vals)
    t=c['type'];value=f.get(t['factName'],0)
    return value==t['value'] if t['comparisonType']=='Equal' else value!=t['value']

def main():
    manifest=json.loads((BASE/'optin_manifest.json').read_text())
    root=json.loads((BASE/'shell_optin.json').read_text())['Data']['RootChunk']
    h=handles(root);n=nodes(root)
    assert len(n)==10 and not root['phasePrefabs']
    assert quest_edges(root)[0]=={(a,'Out',b,'In') for a,b in ((0,1),(1,2),(2,3),(3,8),(8,4),(4,5),(5,6),(6,9),(9,7),(7,2))}
    for obj in walk(root):
        if 'HandleRefId' in obj:assert str(obj['HandleRefId']) in h
    for number,show in ((3,1),(6,0)):
        payload=canonical(n[number]['type'],h)
        assert payload['$type']=='questTogglePrefabVariant_NodeType' and len(payload['params'])==1
        param=payload['params'][0]
        assert param['prefabNodeRef']['$value']==manifest['variant_owner']
        assert param['variantStates']==[{'$type':'questVariantState',
               'name':{'$type':'CName','$storage':'string','$value':manifest['private_variant']},'show':show}]
    writes={obj['factName'] for obj in walk(root) if obj.get('$type')=='questSetVar_NodeType'}
    assert writes=={'PTFRMV_Registered','PTFRMV_Applied','PTFRMV_Acquires','PTFRMV_Releases'}
    assert not any(obj.get('$type') in ('questSceneNodeDefinition','questSpawnManagerNodeDefinition','questPhaseNodeDefinition') for obj in walk(root))
    guard=canonical(n[2]['condition'],h);stop=canonical(n[5]['condition'],h)
    facts=manifest['guards'];assert guard['operation']=='AND' and stop['operation']=='OR'
    assert len(guard['conditions'])==len(stop['conditions'])==len(facts)
    negative=0
    for fact,value in facts.items():
        for bad in (-1,0,1,2):
            if bad==value:continue
            assert not evaluate(guard,facts|{fact:bad})
            assert evaluate(stop,facts|{fact:bad});negative+=1
    assert evaluate(guard,facts) and not evaluate(stop,facts)
    path=manifest['resources'][-1];crc=binascii.crc_hqx((path+':1').encode(),65535)
    assert crc==manifest['registration_id']
    for xl in (ROOT/'archive').rglob('*.xl'):
        for registered in re.findall(r'path:\s*([^\s#]+\.questphase)',xl.read_text(encoding='utf-8-sig')):
            assert registered==path or binascii.crc_hqx((registered+':1').encode(),65535)!=crc,(xl,registered)
    archive=Path(manifest['archive'])
    assert hashlib.sha256(archive.read_bytes()).hexdigest().upper()==manifest['sha256']
    assert hashlib.sha256(Path(str(archive)+'.xl').read_bytes()).hexdigest().upper()==manifest['xl_sha256']
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    probe=(ROOT/'diagnostics/PTFR_MistyViktor_World/init.lua').read_text()
    assert probe.count('SetFactStr("PTFRMV_Enabled",')==2
    assert not any(token in probe for token in ('NewObject','Teleport(','ExecuteQuest','TogglePrefab'))
    lua.execute('''events={};writes={};logs={};f={};pos={x=-1658.9,y=997.4,z=23.7}
    function IsDefined(x) return x~=nil end
    function registerForEvent(n,cb) events[n]=cb end
    function print(...) end
    json={encode=function(row) logs[#logs+1]=row;return 'row' end}
    io={open=function(name,mode) if mode=='r' then return nil end;return {write=function(self,x)return self end,flush=function()return true end,close=function()return true end} end}
    local q={GetFactStr=function(self,k)return f[k] or 0 end,SetFactStr=function(self,k,v)f[k]=v;writes[#writes+1]={k,v} end}
    Game={GetQuestsSystem=function()return q end,GetPlayer=function()return {GetWorldPosition=function()return pos end} end}
    ''')
    mod=lua.execute(probe);lf=lua.globals().f
    for key,value in facts.items():lf[key]=value
    lf.PTFRMV_Enabled=0;lf.PTFRMV_Registered=1
    mod.Start();assert len(lua.globals().writes)==1 and lf.PTFRMV_Enabled==1
    mod.Start();assert len(lua.globals().writes)==1
    lua.execute('pos={x=-1542,y=1210,z=16}')
    mod.Stop();assert lf.PTFRMV_Enabled==1
    lua.execute('pos={x=-1658.9,y=997.4,z=23.7}')
    mod.Stop();assert lf.PTFRMV_Enabled==0 and len(lua.globals().writes)==2
    mod.Finish();events=lua.globals().events
    prior=len(lua.globals().logs);events.onUpdate(2);assert len(lua.globals().logs)==prior
    lf.q307_active=1;mod.Start();assert len(lua.globals().writes)==2
    report={'status':'PASS_OFFLINE_OPTIN_PRIVATE_VARIANT_NATIVE_AND_LUA51_NOT_LIVE',
            'negative_guards':negative,'native_nodes':10,'private_toggle_actions':2,
            'story_writers':0,'scene_starts':0,'source_geometry_test':'shell_tests.json',
            'archive_sha256':manifest['sha256'],'xl_sha256':manifest['xl_sha256'],
            'probe_sha256':hashlib.sha256(probe.encode()).hexdigest().upper(),
            'registration_id':crc,'live_tested':False}
    (BASE/'optin_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
