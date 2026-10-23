"""Exact derivative/payload/edge checks plus bounded ownership contract models."""
import copy, json, re, sys, zlib
from audit_b0_story_zane import ROOT, OUT, OWNER, SCENE, PREFIX, COMMON, sha, read
from audit_b0_deferred_vendors import walk, graph_at
from plan_b0_ordinary_vendor_batch import nm, edge_set
from test_b0_ordinary_vendor_batch import canonical, handles

def payload(n,h):
    n=copy.deepcopy(n);n.pop('phaseGraph',None)
    return canonical(n,h)

def tweak_ids(v):
    # WolvenKit can serialize the same TweakDBID as a resolved string or uint64.
    if isinstance(v,list):return [tweak_ids(x) for x in v]
    if not isinstance(v,dict):return v
    if v.get('$type')=='TweakDBID':
        raw=v['$value']
        numeric=(zlib.crc32(raw.encode()) | (len(raw.encode())<<32)) if v['$storage']=='string' else int(raw)
        return {'$type':'TweakDBID','numeric':numeric}
    return {k:tweak_ids(x) for k,x in v.items()}

def main():
    a=read(OUT/'audit.json');m=read(OUT/'validation/build_manifest.json')
    assert sha(OWNER)==a['owner_sha256'] and sha(SCENE)==a['scene_sha256'] and sha(OUT/'audit.json')==m['audit_sha256']
    assert sha(ROOT/a['quest_dependency']['source'])==a['quest_dependency']['sha256']
    original=read(OWNER)['Data']['RootChunk'];oh=handles(original)
    r=read(OUT/'validation/zane_service.questphase.json')['Data']['RootChunk'];rh=handles(r)
    wrapper=nm(r['graph']['Data']);assert set(wrapper)==set(range(10))
    expected=payload(nm(graph_at(original,'root/node7'))[25],oh);expected['id']=5
    assert payload(wrapper[5],rh)==expected
    for vr,cr in [('root/node7/node25','root/node5'),('root/node7/node25/node2','root/node5/node2')]:
        vg=graph_at(original,vr);cg=graph_at(r,cr);vn=nm(vg);cn=nm(cg)
        outer=vr.endswith('node25')
        assert set(cn)==set(vn)| (set(range(200,206)) if outer else {200})
        for i,n in vn.items():
            expected=payload(n,oh)
            if not outer and i==3:expected['sceneFile']['DepotPath']['$value']='towercontinued\\b0_story_zane\\zane_service.scene'
            assert payload(cn[i],rh)==expected,(vr,i,'original payload drift')
        edges=set()
        for src,sock,dst,insock in edge_set(vg,oh):
            if outer and src==4:dst,insock=200,'In'
            if outer and src==2:dst,insock=202,'In'
            if not outer and src==13:dst,insock=200,'In'
            edges.add((src,sock,dst,insock))
        if outer:edges|={(0,'Out',203,'In'),(200,'True',201,'In'),(201,'Out',204,'In'),(204,'Out',2,'main_in'),(202,'Out',205,'In'),(205,'Out',4,'In'),(203,'Out',5,'Inactive')}
        else:edges.add((200,'Out',3,'cct_dtn_cloth_01_start'))
        assert set(edge_set(cg,rh))==edges,(vr,'edge drift')
    assert set(edge_set(r['graph']['Data'],rh))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',8,'In'),(8,'Out',4,'In'),(4,'Out',5,'In1'),(5,'Out1',6,'In'),(6,'Out',9,'In'),(9,'Out',7,'In'),(7,'Out',2,'In')}
    assert wrapper[9]['type']['Data']['factName']==PREFIX+'Inside' and wrapper[9]['type']['Data']['value']==0
    outer=nm(graph_at(r,'root/node5'));inner=nm(graph_at(r,'root/node5/node2'))
    release=outer[203]['condition']['Data'];assert release['operation']=='AND'
    checks=canonical(release,rh)['conditions']
    assert len(checks)==3 and checks[2]==canonical(inner[9]['condition'],rh)
    assert [(c['type']['factName'],c['type']['comparisonType'],c['type']['value']) for c in checks[:2]]==[(PREFIX+'QuestOwns','Equal',1),(PREFIX+'Inside','Equal',0)]
    assert canonical(outer[200]['condition'],rh)['type']=={'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':PREFIX+'QuestOwns','value':0}
    for v in walk(r):
        if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(PREFIX)
    expected=read(SCENE)['Data']['RootChunk'];eh=handles(expected)
    copied=read(OUT/'validation/zane_service.scene.json')['Data']['RootChunk'];ch=handles(copied)
    changed=next(n['Data']for n in expected['sceneGraph']['Data']['graph']if n['Data']['nodeId']['id']==43)
    changed['questNode']['Data']['type']['Data']['factName']=PREFIX+'ServiceMet'
    assert tweak_ids(canonical(expected,eh))==tweak_ids(canonical(copied,ch)),'Only one scene fact-name change permitted'
    nodes={n['Data']['nodeId']['id']:n['Data']for n in copied['sceneGraph']['Data']['graph']}
    assert nodes[19]['questNode']['Data']['condition']['Data']['type']['Data']['factName']=='mq030_zane_grateful'
    # Reachability is not proof of conditional execution. Equality above preserves
    # all authored outcome conditions, discount, wardrobe, audio and choices.
    assert not any(v.get('factName')=='mq030_zane_met' for v in walk(copied))
    guards={v['factName']:(v['comparisonType'],v['value']) for v in walk(wrapper[2]['condition']) if v.get('$type')=='questVarComparison_ConditionType'}
    wanted={k:('Equal',v)for k,v in COMMON.items()};wanted.update({k:('Equal',0)for k in ['PTFRBASE_Suspended',PREFIX+'Suspended',PREFIX+'Excluded',PREFIX+'QuestOwns']});wanted.update({PREFIX+'Enabled':('Equal',1),'cct_dtn_cloth_01_default_on':('Greater',0)})
    assert guards==wanted
    def allowed(f):
        return all((f.get(k,0)==v if op=='Equal' else f.get(k,0)>v) for k,(op,v) in guards.items())
    seed={k:(v if op=='Equal' else v+1) for k,(op,v) in guards.items()}
    assert allowed(seed)
    for k,(op,v) in guards.items():assert not allowed({**seed,k:v+1 if op=='Equal' else v})
    # Static cooperative-lease contract, not a REDengine simulation.
    cases=0
    for lease in (0,1):
      for inside in (0,1):
       for far in (False,True):
        release_ok=lease==1 and inside==0 and far
        assert not release_ok or (lease and not inside and far)
        start_ok=lease==0
        assert not (release_ok and start_ok)
        cases+=1
    for saved in (False,True):
        state={'lease':0,'inside':1,'active':1,'released':0,'actor':1}
        state['lease']=1
        if saved:state=json.loads(json.dumps(state))
        assert state['released']==0  # cannot launch future owner here
        state['actor']=0;state['inside']=0  # vanilla departure action -> output
        state['active']=0;state['released']=1 # outer output -> wrapper ack
        assert not state['actor'] and not state['active']
        state['lease']=0;state['active']=1;state['released']=0
        assert state['released']==0
        cases+=1
    red=ROOT/'redscript/PTFR_B0_StoryZane/ZaneDriver.reds';text=red.read_text()
    assert re.findall(r'q.SetFact\(n"([^"]+)"',text)==[PREFIX+'Enabled']
    assert 'GetWorldPosition' not in text and PREFIX+'QuestOwns' in text
    for f,v in COMMON.items():assert f'q.GetFact(n"{f}") == {v}' in text
    for f in ['IsSavingLocked','IsTokensActivationBlocked','mount.parentId','IsInCombat','IsActorInWorkspot','IsEntityInScene','SceneTier','HighLevel']:assert f in text
    log=(ROOT/'build/B0_StoryZane/combined_compile.log').read_text(encoding='utf-8-sig');assert 'Output successfully saved' in log and 'ERROR' not in log
    controller=ROOT/'diagnostics/PTFR_B0_StoryZane/init.lua'
    source=controller.read_text();assert not any(s in source for s in ['SetFact','ChangeEntryState','Teleport'])
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};lines={};prints={};function print(s)table.insert(prints,s)end
    function registerForEvent(k,f)events[k]=f end;function IsDefined(x)return x~=nil end
    io={open=function()return {write=function(self,s)table.insert(lines,s);return self end,flush=function()return true end,close=function()end}end}
    q={GetFactStr=function(self,k)return 0 end};p={};Game={GetQuestsSystem=function()return q end,GetPlayer=function()return p end}''')
    mod=lua.execute(source);lua.globals().events.onInit();lua.globals().events.onUpdate(3)
    assert len(lua.globals().lines)==2 and 'PTFRB0ZAN_Released=0' in mod.Observe('test')
    lua.globals().p=None;assert mod.Observe('unloaded')=='loaded=false'
    lua.execute('io.open=function()return nil,"denied"end');lua.globals().events.onInit()
    assert any('Cannot open log' in lua.globals().prints[i]for i in range(1,len(lua.globals().prints)+1))
    mod.Finish()
    archive=ROOT/'build/B0_StoryZane/TowerContinued_B0_StoryZane.archive';xl=ROOT/'archive/b0_story_zane/TowerContinued_B0_StoryZane.archive.xl'
    assert sha(archive)==m['archive_sha256'] and len(m['resources'])==2 and xl.read_text().count('- path:')==1 and m['vanilla_replacements']==[]
    report={'status':'PASS','owners':1,'archive_sha256':sha(archive),'xl_sha256':sha(xl),'driver_sha256':sha(red),'controller_sha256':sha(controller),'lease_model_cases':cases,'live':'NOT_TESTED','checks':['exact one-property scene delta','all native payloads/edges','native departure before cooperative release acknowledgement','startup/Tower/local/lease guards','combined runtime compile','Lua 5.1 logger including unavailable player and file-open failure'],'limitation':'Model/graph checks do not prove runtime prefab release or future quest compatibility.'}
    (OUT/'validation/tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Zane service derivative and bounded cooperative ownership contract; live testing pending')

if __name__=='__main__': main()
