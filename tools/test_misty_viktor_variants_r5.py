"""R5 private-sector range correction, exact payload and guard tests."""
import hashlib
import json
import sys
from pathlib import Path

from audit_world_interactions import walk
from test_radio_memorial import canonical as node_canonical, handles, nodes
from test_streetkid_scene_load_s3 import quest_edges
from test_misty_viktor_optin import evaluate
from test_misty_viktor_street_r3 import quest_normalized, world_normalized

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'research/misty_viktor_world'
R4=ROOT/'build/MistyViktorCleanupR4/source'
R5=ROOT/'build/MistyViktorVariantsR5/source'

def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def main():
    m=read(BASE/'variants_r5_manifest.json')
    prior=read(BASE/'cleanup_r4_manifest.json')
    assert m['status']=='BUILT_R5_PRIVATE_VARIANT_FIX_NOT_INSTALLED_OR_LIVE'
    assert m['resources']==prior['resources'] and m['guards']==prior['guards']
    assert m['private_sector_count']==14 and m['private_block_count']==2
    assert m['actors']==m['native_scene_starts']==m['story_fact_writes']==0
    assert sha(Path(m['archive']))==m['sha256']
    assert sha(Path(m['archive']+'.xl'))==m['xl_sha256']==prior['xl_sha256']
    sectors=[p for p in m['resources'] if p.startswith('towercontinued\\misty_viktor_world\\') and p.endswith('.streamingsector')]
    blocks=[p for p in m['resources'] if p.startswith('towercontinued\\misty_viktor_world\\') and p.endswith('.streamingblock')]
    phase='towercontinued\\misty_viktor_world\\shell_optin.questphase'
    assert len(sectors)==14 and len(blocks)==2
    assert {p for p in m['resources'] if (R4/p).read_bytes()!=(R5/p).read_bytes()}==set(sectors+blocks+[phase])
    for depot in sectors:
        name=Path(depot).stem
        if name.startswith('shell_'):
            a=read(BASE/f'{name}.json')['Data']['RootChunk']
        else:
            slot=int(name.split('_')[1])
            file=BASE/f'cleanup_r4_{name}.json'
            a=read(file if file.exists() and slot!=3 else BASE/f'{name}.json')['Data']['RootChunk']
        b=read(BASE/f'variants_r5_{name}.json')['Data']['RootChunk']
        assert b['variantIndices']==[0,0],name
        assert a['variantIndices']==[0],name
        assert len(b['variantNodes']) in (1,2),name
        omit={'variantIndices','variantNodes'}
        assert world_normalized({k:v for k,v in a.items() if k not in omit})==world_normalized({k:v for k,v in b.items() if k not in omit}),name
        assert len(b['nodeData']['Data'])>0,name
    for depot in blocks:
        name=Path(depot).stem
        a=read(BASE/('shell_block.json' if name=='shell' else 'cleanup_r4_block.json'))['Data']['RootChunk']
        b=read(BASE/f'variants_r5_{name}.json')['Data']['RootChunk']
        assert len(a['descriptors'])==len(b['descriptors'])
        for old,new in zip(a['descriptors'],b['descriptors']):
            assert old['numNodeRanges']==1 and new['numNodeRanges']==2
            assert len(old['variants'])==len(new['variants'])==1
            assert old['variants'][0]['rangeIndex']==0 and new['variants'][0]['rangeIndex']==1
            old=world_normalized({k:v for k,v in old.items() if k not in ('numNodeRanges','variants')})
            new=world_normalized({k:v for k,v in new.items() if k not in ('numNodeRanges','variants')})
            assert old==new
    p4=read(BASE/'cleanup_r4_phase.json')['Data']['RootChunk']
    p5=read(BASE/'variants_r5_phase.json')['Data']['RootChunk']
    h4=handles(p4);h5=handles(p5);n4=nodes(p4);n5=nodes(p5)
    assert len(n4)==len(n5)==22 and quest_edges(p4)[0]==quest_edges(p5)[0]
    for i in range(22):
        for key in ('type','condition'):
            if key not in n4[i]:continue
            a=quest_normalized(node_canonical(n4[i][key],h4))
            b=quest_normalized(node_canonical(n5[i][key],h5))
            if i==18 and key=='type':assert a['value']==4 and b['value']==5
            else:assert a==b,(i,key)
    facts=m['guards'];entry=node_canonical(n5[2]['condition'],h5)
    stop=node_canonical(n5[5]['condition'],h5)
    restore=node_canonical(n5[13]['condition'],h5)
    assert evaluate(entry,facts) and not evaluate(stop,facts)
    assert evaluate(restore,facts|{'PTFRMV_Enabled':0})
    negatives=0
    for fact,wanted in facts.items():
        for bad in (-1,0,1,2):
            if bad==wanted:continue
            f=facts|{fact:bad}
            assert not evaluate(entry,f) and evaluate(stop,f)
            if fact!='PTFRMV_Enabled':assert not evaluate(restore,f)
            negatives+=1
    assert {o['factName'] for o in walk(p5) if o.get('$type')=='questSetVar_NodeType'}=={'PTFRMV_Registered','PTFRMV_Revision','PTFRMV_Applied','PTFRMV_Acquires','PTFRMV_Releases','PTFRMV_AccessRequests','PTFRMV_RestoreRequests'}
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
    lf.PTFRMV_Revision=5;mod.Start();mod.Start();assert len(lua.globals().writes)==1
    lua.execute('pos={x=-1542,y=1210,z=16}');mod.Stop();assert lf.PTFRMV_Enabled==1
    lua.execute('pos={x=-1658.9,y=997.4,z=23.7}');mod.Stop();assert lf.PTFRMV_Enabled==0
    mod.Finish();lf.q307_active=1;mod.Start();assert len(lua.globals().writes)==2
    report={'status':'PASS_R5_OFFLINE_NOT_INSTALLED_OR_LIVE','archive_sha256':m['sha256'],'xl_sha256':m['xl_sha256'],'probe_sha256':sha(ROOT/'diagnostics/PTFR_MistyViktor_World/init.lua'),'private_sector_count':14,'private_block_count':2,'controlled_range_index':1,'default_range_node_count':0,'native_nodes':22,'negative_guards':negatives,'original_hide_outcome_unverified':True,'live_tested':False}
    (BASE/'variants_r5_tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
