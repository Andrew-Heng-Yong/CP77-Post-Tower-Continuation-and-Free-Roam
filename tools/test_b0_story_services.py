"""Exact native graph and service-scene deltas; no live-engine claims."""
import sys,json,copy,re
from plan_b0_story_services import ROOT,OUT,read,sha,scene_delta,nodes,reach
from audit_b0_deferred_vendors import walk,graph_at
from plan_b0_ordinary_vendor_batch import nm,edge_set
from test_b0_ordinary_vendor_batch import canonical,handles
from test_b0_story_zane import payload,tweak_ids

def main():
    c=read(OUT/'cohort.json');m=read(OUT/'validation/build_manifest.json');negative=0
    assert len(c['sites'])==4 and len(m['resources'])==6 and len(m['phases'])==4 and m['vanilla_replacements']==[]
    assert sha(OUT/'cohort.json')==m['cohort_sha256']
    for s in c['sites']:
        assert sha(ROOT/s['owner_json'])==s['owner_sha256'] and sha(ROOT/s['scene_json'])==s['scene_sha256']
        old=read(ROOT/s['owner_json'])['Data']['RootChunk'];oh=handles(old)
        r=read(OUT/'validation'/(s['key']+'.questphase.json'))['Data']['RootChunk'];rh=handles(r);wrapper=nm(r['graph']['Data'])
        parent,_,sid=s['route'].rpartition('/node');expected=payload(nm(graph_at(old,parent))[int(sid)],oh);expected['id']=5
        assert payload(wrapper[5],rh)==expected,(s['key'],'prefab/owner drift')
        for route in s['graphs']:
            vg=graph_at(old,route);cg=graph_at(r,route.replace(s['route'],'root/node5',1));vn=nm(vg);cn=nm(cg);inner=route==s['inner_route']
            assert set(cn)==set(vn)|({200,201,202}if inner else set())
            for i,n in vn.items():
                expected=payload(n,oh)
                if inner and i==s['scene_node'] and s['scene_copy']:expected['sceneFile']['DepotPath']['$value']='towercontinued\\b0_story_services\\'+s['key']+'.scene'
                assert payload(cn[i],rh)==expected,(s['key'],route,i,'payload')
            edges=set()
            for a,sock,b,dest in edge_set(vg,oh):
                original=(a,sock,b,dest)
                if inner:
                    if s['entry_target']==0 and a==0:a,sock=200,'Out'
                    if s['entry_target']!=0 and b==s['entry_target']:b,dest=200,'In'
                    if b==s['output_node']:b,dest=201,'In'
                    e=s['scene_edge']
                    if original==(e['source_node_id'],e['source_socket'],e['destination_node_id'],e['destination_socket']):b,dest=202,'In'
                edges.add((a,sock,b,dest))
            if inner:
                edges.add((0,'Out',200,'In')if s['entry_target']==0 else(200,'Out',s['entry_target'],'In'))
                edges|={(201,'Out',s['output_node'],'In'),(202,'Out',s['scene_node'],s['scene_edge']['destination_socket'])}
                for i,suffix in [(200,'Entries'),(201,'Exits'),(202,'SceneRequests')]:
                    t=cn[i]['type']['Data'];assert t['factName']==s['prefix']+suffix and not t['setExactValue'] and t['value']==1
            assert set(edge_set(cg,rh))==edges,(s['key'],route,'edges')
        assert set(wrapper)==set(range(7))
        assert set(edge_set(r['graph']['Data'],rh))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'Out',5,s['input_socket']),(5,s['output_socket'],6,'In'),(6,'Out',2,'In')}
        cond=wrapper[2]['condition']['Data'];assert cond['operation']=='AND'
        guards={v['factName']:(v['comparisonType'],v['value'])for v in walk(cond)if v.get('$type')=='questVarComparison_ConditionType'}
        wanted={k:('Equal',v)for k,v in c['common_guards'].items()};wanted.update({k:('Equal',0)for k in ['PTFRBASE_Suspended','PTFRB0ST_Suspended',s['prefix']+'Excluded']});wanted.update({s['prefix']+'Enabled':('Equal',1),s['gate']:('Greater',0)})
        assert guards==wanted
        def allowed(f):return all(f.get(k,0)==v if op=='Equal' else f.get(k,0)>v for k,(op,v)in guards.items())
        seed={k:v if op=='Equal'else v+1 for k,(op,v)in guards.items()};assert allowed(seed)
        for k,(op,v)in guards.items():assert not allowed({**seed,k:v+1 if op=='Equal'else v});negative+=1
        sr=read(ROOT/s['scene_json'])['Data']['RootChunk']
        if s['scene_copy']:
            expected=scene_delta(sr,s['key']);actual=read(OUT/'validation'/(s['key']+'.scene.json'))['Data']['RootChunk']
            # Full equality includes audio, animation, actors, props, outcomes,
            # choice localization and every untouched socket/event payload.
            assert tweak_ids(canonical(expected,handles(expected)))==tweak_ids(canonical(actual,handles(actual))),(s['key'],'scene delta drift')
            starts=[1]if s['key']=='fred'else[4];ns=nodes(actual);reachable=reach(ns,starts)
            assert sorted(reachable)==s['reachable']
            forbidden={52,84,528,526}if s['key']=='fred'else{65,69}
            assert not (reachable&forbidden)
            assert (6 if s['key']=='fred'else 8)in reachable
        else:actual=sr
        assert not any('johnny'in str(a).lower()for a in actual.get('actors',[]))
        for i,n in wrapper.items():
            if i!=5:
                assert all(v['factName'].startswith(s['prefix'])for v in walk(n)if v.get('$type')=='questSetVar_NodeType')
    red=ROOT/'redscript/PTFR_B0_StoryServices/StoryServiceDriver.reds';text=red.read_text()
    assert text.count('pending = this.Site(')==4 and text.count('q.SetFact(')==1 and 'q.SetFact(enabled, 1)'in text
    assert 'GetWorldPosition'not in text and '5.0, false'in text
    for k,v in c['common_guards'].items():assert f'q.GetFact(n"{k}") == {v}'in text
    for s in c['sites']:
        for key in [s['gate']]+[s['prefix']+x for x in ['Ready','Enabled','OwnerActive','Excluded']]:assert 'n"'+key+'"'in text
    for key in ['IsSavingLocked','IsTokensActivationBlocked','mount.parentId','IsInCombat','IsActorInWorkspot','IsEntityInScene','HighLevel','SceneTier']:assert key in text
    log=(ROOT/'build/B0_StoryServices/combined_compile.log').read_text(encoding='utf-8-sig');assert 'Output successfully saved'in log and 'ERROR'not in log
    lua_path=ROOT/'diagnostics/PTFR_B0_StoryServices/init.lua';source=lua_path.read_text();assert not any(k in source for k in ['SetFact','Teleport','ChangeEntryState'])
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};lines={};prints={};function print(s)table.insert(prints,s)end
      function registerForEvent(k,f)events[k]=f end;function IsDefined(x)return x~=nil end
      io={open=function()return {write=function(self,s)table.insert(lines,s);return self end,flush=function()return true end,close=function()end}end}
      q={GetFactStr=function(self,k)return 0 end};p={GetWorldPosition=function()return {x=1,y=2,z=3}end}
      Game={GetQuestsSystem=function()return q end,GetPlayer=function()return p end}''')
    mod=lua.execute(source);lua.globals().events.onInit();lua.globals().events.onUpdate(3)
    assert len(lua.globals().lines)==2 and 'PTFRB0STPEPE_Enabled=0'in mod.Observe('test') and 'x=1'in mod.Observe('position')
    lua.globals().p=None;assert mod.Observe('unloaded')=='loaded=false'
    mod.Finish();lua.execute('io.open=function()return nil,"denied"end');lua.globals().events.onInit()
    assert any('Cannot open log'in lua.globals().prints[i]for i in range(1,len(lua.globals().prints)+1))
    archive=ROOT/'build/B0_StoryServices/TowerContinued_B0_StoryServices.archive';xl=ROOT/'archive/b0_story_services/TowerContinued_B0_StoryServices.archive.xl'
    assert sha(archive)==m['sha256'] and xl.read_text().count('- path:')==4 and all(p in xl.read_text()for p in m['phases'])
    report={'status':'PASS','owners':4,'archive_sha256':sha(archive),'xl_sha256':sha(xl),'driver_sha256':sha(red),'controller_sha256':sha(lua_path),'negative_guards':negative,'checks':['all native payloads/edges and prefab ownership','exact enumerated derivative deltas','service reachability without quest progression nodes','all original local availability gates','combined 13-script compile','Lua51 durable read-only logger'],'live':'NOT_TESTED','limitation':'No claim of restored-quest concurrency or live actor/menu/reload correctness.'}
    (OUT/'validation/tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS S3 four service owners,',negative,'negative guard cases')
if __name__=='__main__':main()
