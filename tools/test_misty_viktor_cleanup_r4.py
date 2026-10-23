"""Bounded R4 resource-delta and controller checks; no game execution."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical as node_canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_optin import evaluate
from test_misty_viktor_street_r3 import quest_normalized, world_normalized

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/misty_viktor_world'
R3=ROOT/'build/MistyViktorStreetR3/source'
R4=ROOT/'build/MistyViktorCleanupR4/source'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main():
    m=read(BASE/'cleanup_r4_manifest.json')
    old=read(BASE/'street_r3_manifest.json')
    plan=read(BASE/'street_selection_plan.json')
    assert m['status']=='BUILT_R4_CLEANUP_NOT_INSTALLED_OR_LIVE'
    removed_depots={f'towercontinued\\misty_viktor_world\\street_{i}.streamingsector' for i in m['removed_empty_slots']}
    assert m['removed_empty_slots']==[3]
    assert m['guards']==old['guards'] and set(m['resources'])==set(old['resources'])-removed_depots
    assert m['police_removed_count']==24 and len(m['police_removed'])==24
    assert m['passive_placements']==764 and m['actors']==m['native_scene_starts']==m['story_fact_writes']==0
    assert sha(Path(m['archive']))==m['sha256']
    assert sha(Path(m['archive']+'.xl'))==m['xl_sha256']==old['xl_sha256']
    changed=[]
    for depot in m['resources']:
        if (R3/depot).read_bytes()!=(R4/depot).read_bytes():changed.append(depot)
    allowed={'towercontinued\\misty_viktor_world\\shell_optin.questphase','towercontinued\\misty_viktor_world\\street.streamingblock'}
    allowed|={f'towercontinued\\misty_viktor_world\\street_{r["slot"]}.streamingsector' for r in m['police_removed']}
    assert set(changed)==allowed-removed_depots,(changed,allowed)
    selected=[r for r in plan['source_ranges'] if r['selected']]
    removed_by_slot={i:set() for i in range(12)}
    for r in m['police_removed']:
        i=r['slot'];j=r['ordinal'];item=selected[i]['selected'][j]
        assert r['source_data_index']==item['data_index'] and r['type']==item['type']
        assert r['name'].startswith(('megabuilding_police_tape','q307_police_signage','d_ncpd_logo'))
        assert j not in removed_by_slot[i]
        removed_by_slot[i].add(j)
    counts=Counter();total=0
    for i in range(12):
        a=read(BASE/f'street_{i}.json')['Data']['RootChunk']
        if i in m['removed_empty_slots']:
            assert len(removed_by_slot[i])==len(a['nodeData']['Data'])
            continue
        b=read(BASE/f'cleanup_r4_street_{i}.json')['Data']['RootChunk'] if removed_by_slot[i] else a
        assert b['variantIndices']==a['variantIndices']
        expected=[(j,d) for j,d in enumerate(a['nodeData']['Data']) if j not in removed_by_slot[i]]
        assert len(b['nodeData']['Data'])==len(expected)
        for (j,old_data),new_data in zip(expected,b['nodeData']['Data']):
            assert new_data['Id']==old_data['Id']
            assert world_normalized({k:v for k,v in new_data.items() if k!='NodeIndex'})==world_normalized({k:v for k,v in old_data.items() if k!='NodeIndex'}),(i,j)
            old_node=a['nodes'][old_data['NodeIndex']]['Data']
            new_node=b['nodes'][new_data['NodeIndex']]['Data']
            assert world_normalized(new_node)==world_normalized(old_node),(i,j)
            counts[new_node['$type']]+=1;total+=1
    assert total==764 and counts=={'worldStaticMeshNode':509,'worldStaticDecalNode':249,'worldCollisionNode':6},counts
    block=read(BASE/'cleanup_r4_block.json')['Data']['RootChunk']
    prior_block=read(BASE/'street_block.json')['Data']['RootChunk']
    assert len(block['descriptors'])==11
    assert [world_normalized(d) for d in block['descriptors']]==[world_normalized(d) for i,d in enumerate(prior_block['descriptors']) if i!=3]
    prior=read(BASE/'street_r3_phase.json')['Data']['RootChunk']
    current=read(BASE/'cleanup_r4_phase.json')['Data']['RootChunk']
    hp=handles(prior);hc=handles(current);np=nodes(prior);nc=nodes(current)
    assert len(np)==21 and len(nc)==22 and current['phasePrefabs']==prior['phasePrefabs']==[]
    assert quest_edges(current)[0]=={(a,s,b,'In') for a,s,b in m['edges']}
    for obj in walk(current):
        if 'HandleRefId' in obj:assert str(obj['HandleRefId']) in hc
    for i in range(21):
        for key in ('type','condition'):
            if key in np[i]:
                a=quest_normalized(node_canonical(np[i][key],hp))
                b=quest_normalized(node_canonical(nc[i][key],hc))
                if i==18 and key=='type':
                    assert a['value']==3 and b['value']==4
                else:assert a==b,(i,key)
    p=node_canonical(nc[21]['type'],hc)
    assert p['$type']=='questTogglePrefabVariant_NodeType' and len(p['params'])==1
    p=p['params'][0]
    assert p['prefabNodeRef']['$value']==m['native_hide_owner']
    assert len(p['variantStates'])==1 and p['variantStates'][0]['name']['$value']=='q307_hide_misty'
    assert p['variantStates'][0]['show']==0
    vanilla=read(ROOT/'research/q307_extracted/json/ep1/quest/main_quests/q307/phases/q307_cleanup.questphase.json')
    originals=nodes(vanilla['Data']['RootChunk'])
    v=node_canonical(originals[22]['type'],handles(vanilla['Data']['RootChunk']))
    matching=[x for x in v['params'] if x['prefabNodeRef']['$value']=='#loc_mystic_mistys_ripperdoc_interior']
    assert len(matching)==1 and matching[0]['variantStates']==p['variantStates']
    facts=m['guards'];entry=node_canonical(nc[2]['condition'],hc)
    stop=node_canonical(nc[5]['condition'],hc)
    restore=node_canonical(nc[13]['condition'],hc)
    assert evaluate(entry,facts) and not evaluate(stop,facts)
    assert evaluate(restore,facts|{'PTFRMV_Enabled':0})
    negatives=0
    for fact,wanted in facts.items():
        for bad in (-1,0,1,2):
            if bad==wanted:continue
            cand=facts|{fact:bad}
            assert not evaluate(entry,cand) and evaluate(stop,cand)
            if fact!='PTFRMV_Enabled':assert not evaluate(restore,cand)
            negatives+=1
    assert {o['factName'] for o in walk(current) if o.get('$type')=='questSetVar_NodeType'}=={'PTFRMV_Registered','PTFRMV_Revision','PTFRMV_Applied','PTFRMV_Acquires','PTFRMV_Releases','PTFRMV_AccessRequests','PTFRMV_RestoreRequests'}
    assert not any(o.get('$type') in ('questSceneNodeDefinition','questSpawnManagerNodeDefinition','questPhaseNodeDefinition') for o in walk(current))
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    probe=(ROOT/'diagnostics/PTFR_MistyViktor_World/init.lua').read_text()
    assert probe.count('SetFactStr("PTFRMV_Enabled",')==2
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
    lf.PTFRMV_Revision=4;mod.Start();mod.Start();assert len(lua.globals().writes)==1
    lua.execute('pos={x=-1542,y=1210,z=16}');mod.Stop();assert lf.PTFRMV_Enabled==1
    lua.execute('pos={x=-1658.9,y=997.4,z=23.7}');mod.Stop();assert lf.PTFRMV_Enabled==0
    mod.Finish();lf.q307_active=1;mod.Start();assert len(lua.globals().writes)==2
    report={'status':'PASS_R4_OFFLINE_NOT_INSTALLED_OR_LIVE','archive_sha256':m['sha256'],'xl_sha256':m['xl_sha256'],'probe_sha256':sha(ROOT/'diagnostics/PTFR_MistyViktor_World/init.lua'),'changed_resources':changed,'removed_police_placements':24,'remaining_passive_placements':total,'native_nodes':22,'negative_guards':negatives,'vanilla_hide_action_matched':True,'live_tested':False}
    (BASE/'cleanup_r4_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
