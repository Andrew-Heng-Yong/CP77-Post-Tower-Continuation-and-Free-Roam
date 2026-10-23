"""Check exact cloned ownership, full scenes, guards and read-only logging."""
import sys,re,json,copy
from plan_b0_special_services import ROOT,OUT,read,sha,walk,graph_at
from plan_b0_ordinary_vendor_batch import nm,edge_set
from test_b0_ordinary_vendor_batch import canonical,handles
from test_b0_claire import payload
def main():
    c=read(OUT/'cohort.json');m=read(OUT/'validation/build_manifest.json');sites=c['sites']
    assert len(sites)==len(m['resources'])==19 and sha(OUT/'cohort.json')==m['cohort_sha256']
    assert c['common_guards']['q307_ep1_killed']==1
    assert m['vanilla_replacements']==m['scene_replacements']==[]
    identities=set();negative=0
    for s in sites:
        identity=(s['source'],s['phase']);assert identity not in identities;identities.add(identity)
        assert s['source'].startswith('ep1\\openworld\\vendors\\')
        assert sha(ROOT/s['owner_json'])==s['owner_sha256'] and sha(ROOT/s['scene_json'])==s['scene_sha256']
        original=read(ROOT/s['owner_json'])['Data']['RootChunk'];oh=handles(original)
        r=read(OUT/'validation'/(s['key']+'.questphase.json'))['Data']['RootChunk'];rh=handles(r);wrapper=nm(r['graph']['Data'])
        assert set(wrapper)==set(range(7))
        expected=payload(nm(original['graph']['Data'])[s['phase']],oh);expected['id']=5
        assert payload(wrapper[5],rh)==expected,'Owner prefab/metadata differs'
        for route in s['graphs']:
            vg=graph_at(original,route);cg=graph_at(r,route.replace(s['route'],'root/node5',1));vn=nm(vg);cn=nm(cg)
            for i,n in vn.items():assert payload(n,oh)==payload(cn[i],rh),(s['key'],route,i)
            inner=route==s['inner_route'];assert set(cn)==set(vn)|({200,201,202} if inner else set())
            expected_edges=set()
            for a,sock,b,dest in edge_set(vg,oh):
                if inner:
                    if a==s['input_node']:a,sock=200,'Out'
                    if b==s['output_node']:b,dest=201,'In'
                    if b==s['scene_node']:b,dest=202,'In'
                expected_edges.add((a,sock,b,dest))
            if inner:
                sockets={e[3] for e in edge_set(vg,oh) if e[2]==s['scene_node']};assert len(sockets)==1
                expected_edges|={(s['input_node'],'Out',200,'In'),(201,'Out',s['output_node'],'In'),(202,'Out',s['scene_node'],next(iter(sockets)))}
                for i,suffix in [(200,'Entries'),(201,'Exits'),(202,'SceneRequests')]:
                    t=cn[i]['type']['Data'];assert t['factName']==s['prefix']+suffix and not t['setExactValue'] and t['value']==1
            assert set(edge_set(cg,rh))==expected_edges,(s['key'],route,'edge mismatch')
        assert set(edge_set(r['graph']['Data'],rh))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'Out',5,s['input_socket']),(5,s['output_socket'],6,'In'),(6,'Out',2,'In')}
        cond=wrapper[2]['condition']['Data'];assert cond['operation']=='AND'
        f={v['factName']:(v['comparisonType'],v['value']) for v in walk(cond) if v.get('$type')=='questVarComparison_ConditionType'}
        wanted={k:('Equal',v) for k,v in c['common_guards'].items()}
        wanted.update({k:('Equal',0) for k in ['PTFRBASE_Suspended','PTFRB0SP_Suspended',s['prefix']+'Excluded']})
        wanted[s['prefix']+'Enabled']=('Equal',1)
        wanted.update({k:('Greater',0) for k in [s['gate']]+s['extra_positive']})
        assert f==wanted
        # Only inserted wrapper counters/enable facts are new. Every original
        # native local-state writer is already covered by payload equality.
        for i,n in wrapper.items():
            if i==5:continue
            for v in walk(n):
                if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(s['prefix'])
        assert not any('johnny' in a.lower() for a in s['scene_audit']['actors'])
        assert all('johnny_easter_egg' not in str(v) for v in walk(r))
        def allowed(values,safe=True):
            return safe and all(values.get(k,0)==v for k,v in c['common_guards'].items()) and all(values.get(k,0)>0 for k in [s['gate']]+s['extra_positive']) and values.get('Ready')==1 and all(values.get(k,0)==0 for k in ['Enabled','OwnerActive','Excluded','Suspended','BaseSuspended'])
        seed={**c['common_guards'],**{k:1 for k in [s['gate']]+s['extra_positive']},'Ready':1};assert allowed(seed)
        for k,v in c['common_guards'].items():assert not allowed({**seed,k:1-v});negative+=1
        for k in [s['gate']]+s['extra_positive']:assert not allowed({**seed,k:0});negative+=1
        for k in ['Enabled','OwnerActive','Excluded','Suspended','BaseSuspended']:assert not allowed({**seed,k:1});negative+=1
        assert not allowed(seed,False)
    red=ROOT/'redscript/PTFR_B0_SpecialServices/SpecialServiceDriver.reds';text=red.read_text()
    assert text.count('pending = this.Site(')==19 and text.count('q.SetFact(')==1 and 'q.SetFact(enabled, 1)' in text
    assert 'GetWorldPosition' not in text and '5.0, false' in text
    for s in sites:
        for key in [s['gate']]+s['extra_positive']+[s['prefix']+x for x in ['Enabled','Ready','OwnerActive','Excluded']]:assert 'n"'+key+'"' in text
    for k,v in c['common_guards'].items():assert f'q.GetFact(n"{k}") == {v}' in text
    for key in ['IsSavingLocked','IsTokensActivationBlocked','mount.parentId','IsInCombat','IsActorInWorkspot','IsEntityInScene','HighLevel','SceneTier']:assert key in text
    compilelog=(ROOT/'build/B0_SpecialServices/combined_compile.log').read_text(encoding='utf-8-sig');assert 'Output successfully saved' in compilelog and 'ERROR' not in compilelog
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};facts={};logs={};prints={}
      function print(s)table.insert(prints,s)end
      function registerForEvent(k,f)events[k]=f end
      function IsDefined(v)return v~=nil end
      json={encode=function(x)table.insert(logs,x);return '{}'end}
      io={open=function()return {write=function()return true end,flush=function()return true end,close=function()end}end}
      q={GetFactStr=function(self,k)return facts[k] or 0 end,SetFactStr=function()error('Forbidden')end}
      p={GetWorldPosition=function()return {x=0,y=0,z=0}end,GetEntityID=function()return 1 end}
      Game={GetPlayer=function()return p end,GetQuestsSystem=function()return q end,
        GetSceneSystem=function()return {GetScriptInterface=function()return {IsEntityInScene=function()return false end}end}end,
        GetWorkspotSystem=function()return {IsActorInWorkspot=function()return false end}end}
    ''')
    controller=ROOT/'diagnostics/PTFR_B0_SpecialServices/init.lua';source=controller.read_text();assert not any(k in source for k in ['SetFact','Teleport','ForceReset'])
    mod=lua.execute(source);lua.globals().events.onInit();lua.globals().events.onUpdate(3)
    assert mod.Observe('test').scene is False and len(lua.globals().prints)==19
    assert len(lua.globals().logs)>=3
    lua.globals().p=None;assert mod.Observe('unloaded').loaded is False
    mod.Finish();lua.globals().events.onShutdown()
    archive=ROOT/'build/B0_SpecialServices/TowerContinued_B0_SpecialServices.archive';xl=ROOT/'archive/b0_special_services/TowerContinued_B0_SpecialServices.archive.xl'
    assert sha(archive)==m['sha256'] and xl.read_text().count('- path:')==19
    assert all(p.startswith('towercontinued\\b0_special_services\\') and p in xl.read_text() for p in m['resources'])
    report={'status':'PASS','owners':19,'archive_sha256':sha(archive),'xl_sha256':sha(xl),'driver_sha256':sha(red),'controller_sha256':sha(controller),'negative_startup_cases':negative,
      'checks':['all native node payloads and graph edges','exact prefab ownership','full original scenes','no Johnny actor/egg resource','preserved local/outcome gates','no new vanilla fact writer','combined eleven-script compilation','Lua 5.1 read-only logger'],'live':'NOT_TESTED'}
    (OUT/'validation/tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',len(sites),'native service owners;',negative,'negative startup contracts; no live engine claim')
if __name__=='__main__':main()
