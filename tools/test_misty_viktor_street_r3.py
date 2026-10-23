"""Exact private street payload, controller and CET opt-in checks; no game execution."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical as node_canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_optin import evaluate
from test_misty_viktor_shell import canonical as world_canonical

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/misty_viktor_world'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()
def world_normalized(value):
    value=world_canonical(value)
    if isinstance(value,dict):
        if value.get('$type')=='CName' and '$value' in value:
            if value.get('$storage')=='uint64':return {'CNameHash':int(value['$value'])}
            if value.get('$storage')=='string':
                h=14695981039346656037
                for b in value['$value'].encode():h=((h^b)*1099511628211)&((1<<64)-1)
                return {'CNameHash':h}
        return {k:world_normalized(v) for k,v in value.items()}
    if isinstance(value,list):return [world_normalized(v) for v in value]
    return value
def quest_normalized(value):
    if isinstance(value,dict):
        if value.get('$type')=='NodeRef' and value.get('$storage')=='string':
            return value|{'$value':value['$value'].split(';')[0]}
        return {k:quest_normalized(v) for k,v in value.items()}
    if isinstance(value,list):return [quest_normalized(v) for v in value]
    return value

def main():
    plan=read(BASE/'street_selection_plan.json')
    m=read(BASE/'street_r3_manifest.json')
    old=read(BASE/'access_r2_manifest.json')
    assert m['status']=='BUILT_R3_PASSIVE_STREET_OPTIN_NOT_INSTALLED_OR_LIVE'
    assert m['guards']==old['guards'] and m['street_variant']!='q307_misty_alley'
    assert len(m['sectors'])==12 and m['passive_placements']==788
    assert m['actors']==m['native_scene_starts']==m['story_fact_writes']==0
    assert sha(Path(m['archive']))==m['sha256'] and sha(Path(m['archive']+'.xl'))==m['xl_sha256']
    assert m['resources'][:5]==old['resources']
    for depot in old['resources'][:-1]:
        a=ROOT/'build/MistyViktorAccessR2/source'/depot
        b=ROOT/'build/MistyViktorStreetR3/source'/depot
        assert a.read_bytes()==b.read_bytes(),depot
    ids=set();counts=Counter();checked=0
    ref_hashes=read(BASE/'street_ref_hashes.json')
    qualified_refs=0
    selected=[r for r in plan['source_ranges'] if r['selected']]
    assert len(selected)==len(m['sectors'])
    for slot,(row,record) in enumerate(zip(selected,m['sectors'])):
        raw=ROOT/row['raw_path'];assert sha(raw)==row['raw_sha256'].upper()
        source_json=str(row['raw_path']).replace('\\raw\\','\\json\\').replace('/raw/','/json/')+'.json'
        oldworld=read(ROOT/source_json)['Data']['RootChunk']
        new=read(BASE/f'street_{slot}.json')['Data']['RootChunk']
        assert new['variantIndices']==[0] and len(new['nodeData']['Data'])==len(row['selected'])
        assert record['count']==len(row['selected'])
        for newdata,item in zip(new['nodeData']['Data'],row['selected']):
            olddata=oldworld['nodeData']['Data'][item['data_index']]
            oldnode=oldworld['nodes'][item['node_index']]['Data']
            newnode=new['nodes'][newdata['NodeIndex']]['Data']
            assert newnode['$type'] in ('worldStaticMeshNode','worldStaticDecalNode','worldCollisionNode')
            assert world_normalized(newnode)==world_normalized(oldnode),(slot,item['data_index'],'payload')
            if olddata.get('UkHash1',{}).get('$storage')=='string':
                original_ref=olddata['UkHash1']['$value']
                newref=newdata['UkHash1']
                newhash=ref_hashes[newref['$value']] if newref['$storage']=='string' else int(newref['$value'])
                assert newhash==ref_hashes[original_ref]
                qualified_refs+=1
            omit=('Id','NodeIndex','QuestPrefabRefHash','UkHash1')
            assert world_normalized({k:v for k,v in newdata.items() if k not in omit})==world_normalized({k:v for k,v in olddata.items() if k not in omit}),(slot,item['data_index'],'placement')
            assert newdata['Id'] not in ids and newdata['Id']!=olddata['Id']
            assert newdata['QuestPrefabRefHash']['$value'] in ('','0')
            ids.add(newdata['Id']);counts[newnode['$type']]+=1;checked+=1
    assert checked==788
    assert qualified_refs==86 and len(ref_hashes)==7
    assert counts=={'worldStaticMeshNode':525,'worldStaticDecalNode':257,'worldCollisionNode':6}
    assert plan['facade_logo']['type']=='worldStaticMeshNode' and plan['facade_logo']['name']=='corporation_zetatech_a'
    block=read(BASE/'street_block.json')['Data']['RootChunk']
    assert len(block['descriptors'])==12
    for d,record in zip(block['descriptors'],m['sectors']):
        assert d['numNodeRanges']==1 and d['data']['DepotPath']['$value']==record['depot']
        assert len(d['variants'])==1
        v=d['variants'][0]
        assert v['name']['$value']==m['street_variant'] and v['nodeRef']['$value']==m['street_owner']
        assert v['variantId']==m['street_variant_id'] and v['rangeIndex']==0
        assert v['enabledByDefault']==0 and v['parentVariantID']==0
    assert m['street_variant_id']!=3917072701
    for path in {r['source_block'] for r in selected}:
        source=read(ROOT/path)['Data']['RootChunk']
        assert all(v['variantId']!=m['street_variant_id'] for d in source['descriptors'] for v in d.get('variants',[]))

    r2=read(BASE/'access_r2.json')['Data']['RootChunk']
    r3=read(BASE/'street_r3_phase.json')['Data']['RootChunk']
    h2=handles(r2);h3=handles(r3);n2=nodes(r2);n3=nodes(r3)
    assert len(n3)==21 and r3['phasePrefabs']==r2['phasePrefabs']==[]
    assert quest_edges(r3)[0]=={(a,s,b,'In') for a,s,b in m['edges']}
    for obj in walk(r3):
        if 'HandleRefId' in obj:assert str(obj['HandleRefId']) in h3
    for i in range(19):
        if i==18:
            assert node_canonical(n3[i]['type'],h3)['value']==3
            assert node_canonical(n2[i]['type'],h2)['value']==2
            continue
        for key in ('type','condition'):
            if key in n2[i]:assert quest_normalized(node_canonical(n3[i][key],h3))==quest_normalized(node_canonical(n2[i][key],h2)),(i,key)
    for i,show in ((19,1),(20,0)):
        payload=node_canonical(n3[i]['type'],h3)
        assert payload['$type']=='questTogglePrefabVariant_NodeType' and len(payload['params'])==1
        p=payload['params'][0]
        assert p['prefabNodeRef']['$value']==m['street_owner']
        assert len(p['variantStates'])==1
        assert p['variantStates'][0]['name']['$value']==m['street_variant']
        assert p['variantStates'][0]['show']==show
    facts=m['guards'];entry=node_canonical(n3[2]['condition'],h3)
    stop=node_canonical(n3[5]['condition'],h3);restore=node_canonical(n3[13]['condition'],h3)
    assert evaluate(entry,facts) and not evaluate(stop,facts)
    assert evaluate(restore,facts|{'PTFRMV_Enabled':0})
    negatives=0
    for fact,wanted in facts.items():
        for bad in (-1,0,1,2):
            if bad==wanted:continue
            candidate=facts|{fact:bad}
            assert not evaluate(entry,candidate) and evaluate(stop,candidate)
            if fact!='PTFRMV_Enabled':assert not evaluate(restore,candidate)
            negatives+=1
    writers={o['factName'] for o in walk(r3) if o.get('$type')=='questSetVar_NodeType'}
    assert writers=={'PTFRMV_Registered','PTFRMV_Revision','PTFRMV_Applied','PTFRMV_Acquires','PTFRMV_Releases','PTFRMV_AccessRequests','PTFRMV_RestoreRequests'}
    assert not any(o.get('$type') in ('questSceneNodeDefinition','questSpawnManagerNodeDefinition','questPhaseNodeDefinition') for o in walk(r3))
    xl=Path(m['archive']+'.xl').read_text()
    assert xl.count('street.streamingblock')==1 and xl.count('shell.streamingblock')==1
    assert xl.count('shell_optin.questphase')==1

    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    probe=(ROOT/'diagnostics/PTFR_MistyViktor_World/init.lua').read_text()
    assert probe.count('SetFactStr("PTFRMV_Enabled",')==2
    assert not any(token in probe for token in ('NewObject','Teleport(','ExecuteQuest','TogglePrefab'))
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};writes={};f={};pos={x=-1658.9,y=997.4,z=23.7}
    function IsDefined(x)return x~=nil end
    function registerForEvent(n,cb)events[n]=cb end
    function print(...)end
    json={encode=function()return 'row' end}
    io={open=function(n,m)if m=='r' then return nil end;return {write=function(self)return self end,flush=function()return true end,close=function()return true end}end}
    local q={GetFactStr=function(self,k)return f[k] or 0 end,SetFactStr=function(self,k,v)f[k]=v;writes[#writes+1]={k,v}end}
    Game={GetQuestsSystem=function()return q end,GetPlayer=function()return {GetWorldPosition=function()return pos end}end}''')
    mod=lua.execute(probe);lf=lua.globals().f
    for key,value in facts.items():lf[key]=value
    lf.PTFRMV_Registered=1;lf.PTFRMV_Enabled=0
    mod.Start();assert len(lua.globals().writes)==0
    lf.PTFRMV_Revision=3;mod.Start();mod.Start();assert len(lua.globals().writes)==1
    lua.execute('pos={x=-1542,y=1210,z=16}');mod.Stop();assert lf.PTFRMV_Enabled==1
    lua.execute('pos={x=-1658.9,y=997.4,z=23.7}');mod.Stop();assert lf.PTFRMV_Enabled==0
    mod.Finish();lf.q307_active=1;mod.Start();assert len(lua.globals().writes)==2
    report={'status':'PASS_R3_OFFLINE_PASSIVE_STREET_NOT_LIVE','archive_sha256':m['sha256'],
            'xl_sha256':m['xl_sha256'],'probe_sha256':hashlib.sha256(probe.encode()).hexdigest().upper(),
            'sectors':len(selected),'placements':checked,'passive_types':dict(counts),
            'native_nodes':len(n3),'negative_guards':negatives,'original_variants_toggled':0,
            'actors_added':0,'scene_starts':0,'story_writers':0,'live_tested':False}
    (BASE/'street_r3_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
