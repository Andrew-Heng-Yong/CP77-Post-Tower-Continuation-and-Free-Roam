"""Validate both native owners and execute optional diagnostic Lua with mocks."""
import hashlib
import json
import re
import sys
from pathlib import Path
from plan_b0_ordinary_vendor_batch import graph_at, nm, edge_set, walk
from test_b0_ordinary_vendor_batch import canonical, handles

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'research/b0_deferred_ordinary'
VAL=BASE/'validation'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    sites=read(BASE/'sites.json');manifest=read(VAL/'build_manifest.json')
    assert len(sites)==len(manifest['resources'])==2
    assert manifest['scene_replacements']==manifest['vanilla_replacements']==[]
    assert sha(Path(manifest['archive']))==manifest['sha256']
    for p,h in manifest['source_hashes'].items():assert sha(Path(p))==h
    for s in sites:
        original=read(ROOT/s['owner_json'])['Data']['RootChunk'];oh=handles(original)
        built=read(VAL/(s['key']+'.questphase.json'))['Data']['RootChunk'];bh=handles(built)
        root=nm(built['graph']['Data']);outer=nm(root[5]['phaseGraph']['Data'])
        vanilla_outer=nm(graph_at(original,s['outer_route']))
        inner=nm(outer[s['inner_phase']]['phaseGraph']['Data'])
        vanilla_inner=nm(graph_at(original,s['outer_route']+'/node'+str(s['inner_phase'])))
        for key,n in vanilla_outer.items():
            if key not in (s['far'],s['inner_phase']):assert canonical(outer[key],bh)==canonical(n,oh),(s['key'],'outer',key)
        for key,n in vanilla_inner.items():assert canonical(inner[key],bh)==canonical(n,oh),(s['key'],'inner',key)
        original_phase=nm(graph_at(original,s['parent_route']))[s['phase']]
        assert canonical(root[5]['phaseInstancePrefabs'],bh)==canonical(original_phase['phaseInstancePrefabs'],oh)
        assert inner[s['scene_node']]['sceneFile']['DepotPath']['$value']==s['scene']
        expected=set(edge_set(graph_at(original,s['outer_route']),oh))
        if s['key']=='netrunner02':expected|={(s['input'],'Out',202,'In'),(202,'Out',s['despawn'],'In')}
        assert set(edge_set(root[5]['phaseGraph']['Data'],bh))==expected
        expected=set(edge_set(graph_at(original,s['outer_route']+'/node'+str(s['inner_phase'])),oh))
        expected.remove((s['close'],'Out',s['scene_node'],s['scene_socket']))
        expected|={(s['close'],'Out',201,'In'),(201,'Out',s['scene_node'],s['scene_socket'])}
        assert set(edge_set(outer[s['inner_phase']]['phaseGraph']['Data'],bh))==expected
        assert set(edge_set(built['graph']['Data'],bh))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',9,'In'),(9,'True',4,'In'),(9,'False',2,'In'),(4,'Out',10,'In'),(10,'Out',5,'In1'),(5,'Out1',11,'In'),(11,'Out',7,'In'),(7,'Out',8,'In'),(8,'Out',2,'In')}
        for node in (2,9):
            cond=root[node]['condition']['Data'];assert cond['operation']=='AND'
            facts={v['factName']:(v['comparisonType'],v['value']) for v in walk(cond) if v.get('$type')=='questVarComparison_ConditionType'}
            expected={f:('Equal',v) for f,v in manifest['common_guards'].items()}
            expected[s['prefix']+'Enabled']=('Equal',1)
            expected.update({f:('Greater',0) for f in [s['gate'],*s['extra_positive_gates']]})
            assert facts==expected
            journals=[v for v in walk(cond) if v.get('$type')=='questJournalEntryState_ConditionType']
            assert len(journals)==(2 if s['key']=='netrunner02' else 0)
            assert all(v['inverted']==1 and v['state']=='Active' for v in journals)
        for v in walk(built):
            if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(s['prefix'])
            assert v.get('$type') not in ('SetVendorPriceMultiplierRequest','ResolveAllSkillchecksEvent')
        assert outer[s['far']]['condition']['Data']['type']['Data']['factName']==s['prefix']+'Far'
        if s['key']=='netrunner02':
            source_watch=nm(original['graph']['Data'])[68]
            assert canonical(outer[202]['condition'],bh)==canonical(source_watch['condition'],oh)
        scene=read(ROOT/s['scene_json'])['Data']['RootChunk']
        writers={v['factName'] for v in walk(scene) if v.get('$type')=='questSetVar_NodeType'}
        assert writers==(set() if s['key']=='christine' else {'wbr_jpn_netrun_02_service'})
    red=ROOT/'redscript/PTFR_B0_DeferredVendors/DeferredVendorDriver.reds'
    text=red.read_text();assert '@@' not in text and text.count('player.GetWorldPosition()')==1 and text.count('this.Site(q, position')==2
    assert (ROOT/'build/B0_DeferredOrdinary/offline_test.redscripts').is_file()
    # Diagnostic syntax and behavior under Lua 5.1. Not a REDengine test.
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''
      events={};facts={};writes={};busy=false;records={}
      function registerForEvent(k,f)events[k]=f end
      function IsDefined(v)return v~=nil end
      function ToVector4(x)return x end
      function ToEulerAngles(x)return x end
      json={encode=function(x)table.insert(records,x);return '{}'end}
      io={open=function()return {write=function()return true end,flush=function()return true end,close=function()end}end}
      q={GetFactStr=function(self,k)return facts[k] or 0 end,SetFactStr=function(self,k,v)assert(k:find('^PTFRB0DOV'));facts[k]=v;table.insert(writes,k)end}
      player={pos={x=-506.4,y=-760.19,z=7.42},GetWorldPosition=function(self)return self.pos end,GetEntityID=function()return 1 end,IsInCombat=function()return busy end}
      Game={GetPlayer=function()return player end,GetQuestsSystem=function()return q end,
        GetSceneSystem=function()return {GetScriptInterface=function()return {IsEntityInScene=function()return false end}end}end,
        GetWorkspotSystem=function()return {IsActorInWorkspot=function()return false end}end,
        GetTeleportationFacility=function()return {Teleport=function(self,p,pos)p.pos=pos end}end}
    ''')
    path=ROOT/'diagnostics/PTFR_B0_DeferredVendors/init.lua'
    mod=lua.execute(path.read_text());lua.globals().events.onInit()
    assert len(lua.globals().writes)==0
    assert mod.Go('wrong') is False
    lua.globals().busy=True;assert mod.Go('christine') is False
    lua.globals().busy=False;assert mod.Go('christine') is True
    assert mod.Stop() is False
    lua.globals().facts['PTFRB0DOVC_Near']=1
    assert mod.Go('netrunner02') is False and mod.Outside() is True and mod.Stop() is False
    lua.globals().facts['PTFRB0DOVC_Near']=0
    assert mod.Stop() is True and lua.globals().facts['PTFRB0DOV_Suspended']==1
    assert mod.Resume() is True and lua.globals().facts['PTFRB0DOV_Suspended']==0
    s=mod.Observe('test');assert s.scene is False
    before=len(lua.globals().writes);lua.globals().events.onUpdate(3);assert len(lua.globals().writes)==before
    lua.globals().events.onShutdown()
    report={'status':'PASS','owners':2,'full_original_scenes_preserved':2,'native_edges':'exact expected; nested child loops and journal exclusions preserved',
            'lua':'Lua 5.1 syntax, passive logging, gates/readings, travel guards, Stop/Resume',
            'archive_sha256':manifest['sha256'],'driver_sha256':sha(red),'controller_sha256':sha(path),'live':'unverified'}
    (VAL/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: two narrow owners, exact links, complete original scenes, story exclusion, no market replay, Lua diagnostics')

if __name__=='__main__':main()
