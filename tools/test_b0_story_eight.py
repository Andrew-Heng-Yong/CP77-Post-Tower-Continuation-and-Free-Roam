"""S4 offline contracts, not a simulation of REDengine actor acquisition."""
import copy,json,sys
from plan_b0_story_eight import *
from test_b0_ordinary_vendor_batch import canonical,handles
from test_b0_story_zane import payload,tweak_ids

def equal(a,b):return tweak_ids(canonical(a,handles(a)))==tweak_ids(canonical(b,handles(b)))

def main():
    c=read(OUT/'cohort.json');manifest=read(OUT/'validation/build_manifest.json');negative=0
    assert len(c['sites'])==8 and len(manifest['resources'])==16 and len(manifest['phases'])==8
    assert manifest['vanilla_replacements']==[] and sha(OUT/'cohort.json')==manifest['cohort_sha256']
    for s in c['sites']:
        key=s['key'];prefix=s['prefix']
        assert sha(ROOT/s['owner_json'])==s['owner_sha256'] and sha(ROOT/s['scene_json'])==s['scene_sha256']
        old=read(ROOT/s['owner_json'])['Data']['RootChunk'];oh=handles(old)
        actual=read(OUT/'validation'/(key+'.questphase.json'))['Data']['RootChunk'];ah=handles(actual)
        wrapper=nm(actual['graph']['Data']);assert set(wrapper)==set(range(7))
        if s['route']!='root':
            parent,_,sid=s['route'].rpartition('/node');expected=payload(nm(graph_at(old,parent))[int(sid)],oh);expected['id']=5
            assert payload(wrapper[5],ah)==expected,(key,'owner/prefab metadata')
        for route,plan in s['graphs'].items():
            og=graph_at(old,route);on=nm(og)
            g=graph_at(actual,route.replace(s['route'],'root/node5',1));nn=nm(g)
            cs=[v for v in s['counters']if v['route']==route]
            assert set(nn)==set(plan['nodes'])|set(range(200,200+len(cs))),(key,route,'nodes')
            for i in plan['nodes']:
                expected=payload(on[i],oh)
                if on[i]['$type']=='questSceneNodeDefinition':expected['sceneFile']['DepotPath']['$value']='towercontinued\\b0_story_eight\\'+key+'.scene'
                assert tweak_ids(payload(nn[i],ah))==tweak_ids(expected),(key,route,i,'payload')
            edges=set()
            for e in plan['edges']:
                a,sock,b,dest=e
                for j,v in enumerate(cs):
                    if e==v['edge']:b,dest=200+j,'In'
                edges.add((a,sock,b,dest))
            for j,v in enumerate(cs):
                edges.add((200+j,'Out',v['edge'][2],v['edge'][3]))
                t=nn[200+j]['type']['Data'];assert t['factName']==prefix+v['suffix'] and t['value']==1 and not t['setExactValue']
            assert set(edge_set(g,ah))==edges,(key,route,'connections')
        expected={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'Out',5,'In1'),(6,'Out',2,'In')}
        expected|={(5,o,6,'In')for o in s['output_sockets']}
        assert set(edge_set(actual['graph']['Data'],ah))==expected
        condition=wrapper[2]['condition']['Data'];assert condition['operation']=='AND'
        guards={v['factName']:(v['comparisonType'],v['value'])for v in walk(condition)if v.get('$type')=='questVarComparison_ConditionType'}
        wanted={k:('Equal',v)for k,v in c['common_guards'].items()}
        wanted.update({k:('Equal',0)for k in ['PTFRBASE_Suspended','PTFRB0S4_Suspended',prefix+'Excluded',prefix+'QuestOwns']})
        wanted[prefix+'Enabled']=('Equal',1);wanted.update({f:(op,v)for f,op,v in s['guards']});assert guards==wanted
        allowed=lambda f:all(f.get(k,0)==v if op=='Equal'else f.get(k,0)>v for k,(op,v)in guards.items())
        seed={k:v if op=='Equal'else v+1 for k,(op,v)in guards.items()};assert allowed(seed)
        for k,(op,v)in guards.items():assert not allowed({**seed,k:v+1 if op=='Equal'else v});negative+=1
        sr=read(ROOT/s['scene_json'])['Data']['RootChunk'];expected=scene_delta(sr,key)
        entry_ids={e['name']['$value']:e['nodeId']['id']for e in sr['entryPoints']}
        requested={v['edge'][3]for v in s['counters']if v['suffix']=='SceneRequests'}
        assert {entry_ids[e]for e in requested}==set(s['starts']),(key,'unaudited scene input')
        sc=read(OUT/'validation'/(key+'.scene.json'))['Data']['RootChunk']
        assert equal(expected,sc),(key,'full scene equality')
        ns=nodes(sc);rr=reach(ns,s['starts']);assert sorted(rr)==s['reachable']
        assert any(list(scalars(ns[i],'vendorId')) for i in rr),(key,'service not reachable')
        assert not any('questRewardManager'in ns[i].get('questNode',{}).get('Data',{}).get('$type','')for i in rr)
        for idx in s['scene_ops'].get('disable_actors',[]):
            a=sc['actors'][idx]['spawnDespawnParams'];assert not a['isEnabled'] and not a['spawnOnStart'] and not a['alwaysSpawned']
            assert not any(v.get('$type')=='scnPerformerId' and v.get('id')==((idx<<8)|1)for i in rr for v in walk(ns[i]))
        for i in rr:
            q=ns[i].get('questNode',{}).get('Data',{})
            if q.get('$type')=='questFactsDBManagerNodeDefinition':
                assert not any(f.startswith(('q0','q1','q2','q3','mq','sq','wst_','sts_ep1_'))for f in scalars(q,'factName')),(key,i)
            if q.get('$type')=='questJournalNodeDefinition':assert all('service_points/'in f for f in scalars(q,'realPath'))
        # Sources remain installed by their existing vanilla paths; the derivative's
        # self-referential event/section controls must target its OWN resource.
        assert not any(v.get('$type')=='ResourcePath' and v.get('$value')==s['scene']for v in walk(sc)),key
    red=ROOT/'redscript/PTFR_B0_StoryEight/StoryEightDriver.reds';source=red.read_text()
    assert source.count('q.SetFact(')==1 and 'q.SetFact(enabled, 1)'in source and 'GetWorldPosition'not in source
    assert source.count('pending = this.Site(')==8
    for s in c['sites']:
        assert f'n"{s["prefix"]}QuestOwns"'in source
        for f,op,v in s['guards'][1:]:assert f'q.GetFact(n"{f}") {"=="if op=="Equal"else">"} {v}'in source
    for term in ['IsSavingLocked','IsTokensActivationBlocked','mount.parentId','IsInCombat','IsActorInWorkspot','IsEntityInScene','HighLevel','SceneTier']:assert term in source
    if '--graph-only'in sys.argv:print('PASS: all eight owner/scene exports and',negative,'negative guards');return
    compile_log=(ROOT/'build/B0_StoryEight/combined_compile.log').read_text(encoding='utf-8-sig')
    assert 'Output successfully saved'in compile_log and 'ERROR'not in compile_log
    lp=ROOT/'diagnostics/PTFR_B0_StoryEight/init.lua';ls=lp.read_text()
    assert not any(t in ls for t in ['SetFact','Teleport','ChangeEntryState'])
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'));from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};lines={};prints={};function print(s)table.insert(prints,s)end
      function registerForEvent(k,f)events[k]=f end;function IsDefined(x)return x~=nil end
      io={open=function()return {write=function(self,s)table.insert(lines,s);return self end,close=function()return true end}end}
      q={GetFactStr=function(self,k)return 0 end};p={GetWorldPosition=function()return {x=1,y=2,z=3}end}
      Game={GetQuestsSystem=function()return q end,GetPlayer=function()return p end}''')
    mod=lua.execute(ls);lua.globals().events.onInit();assert len(lua.globals().lines)==1
    lua.globals().events.onUpdate(2);assert len(lua.globals().lines)==1
    lua.globals().events.onUpdate(15);assert len(lua.globals().lines)==2
    assert 'PTFRB0S4NIX_Enabled=0'in mod.Observe('combined-test')
    lua.globals().p=None;assert mod.Observe('unloaded')=='loaded=false'
    mod.Finish();lua.execute('io.open=function()return nil,"denied"end');lua.globals().events.onInit()
    assert any('LOG ERROR'in lua.globals().prints[i]for i in range(1,len(lua.globals().prints)+1))
    archive=ROOT/'build/B0_StoryEight/TowerContinued_B0_StoryEight.archive';xl=ROOT/'archive/b0_story_eight/TowerContinued_B0_StoryEight.archive.xl'
    assert sha(archive)==manifest['sha256'] and xl.read_text().count('- path:')==8
    report={'status':'PASS','owners':8,'resources':16,'archive_sha256':sha(archive),'xl_sha256':sha(xl),'driver_sha256':sha(red),'controller_sha256':sha(lp),'negative_guards':negative,'checks':['exact owner subsets and retained payloads/prefabs','full derivative scene equality','reachable service/no story progress/no rewards','disabled unrelated actor automatic spawning','self-scene references','combined 14 PTFR-script compile','Lua51 append-close/error/heartbeat mock tests'],'live':'NOT_TESTED','limitation':'Static checks do not prove live actor acquisition, menu/re-entry/reload, or future quest-owner concurrency.'}
    (OUT/'validation/tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS S4 offline:',negative,'negative guards; live pending')

if __name__=='__main__':main()
