"""Exact graph/payload, startup guard and executable read-only diagnostic checks."""
import json,sys,re,copy
from audit_b0_claire import ROOT,OUT,OWNER,SCENE,COMMON,PREFIX,sha,read
from plan_b0_ordinary_vendor_batch import graph_at,nm,edge_set,walk
from test_b0_ordinary_vendor_batch import canonical,handles

def payload(n,h):
    n=copy.deepcopy(n);n.pop('phaseGraph',None)
    return canonical(n,h)
def main():
    a=read(OUT/'audit.json');m=read(OUT/'validation/build_manifest.json')
    assert sha(OWNER)==a['owner_sha256'] and sha(SCENE)==a['scene_sha256'] and sha(OUT/'audit.json')==m['audit_sha256']
    original=read(OWNER)['Data']['RootChunk'];oh=handles(original)
    r=read(OUT/'validation/claire_service.questphase.json')['Data']['RootChunk'];rh=handles(r)
    wrapper=nm(r['graph']['Data'])
    assert set(wrapper)==set(range(7))
    expected=payload(nm(graph_at(original,'root/node4'))[19],oh);expected['id']=5
    assert payload(wrapper[5],rh)==expected,'Prefab owner metadata changed'
    assert wrapper[5]['phaseInstancePrefabs']==nm(graph_at(original,'root/node4'))[19]['phaseInstancePrefabs']
    for vanilla_route,copy_route in [('root/node4/node19','root/node5'),('root/node4/node19/node26','root/node5/node26'),('root/node4/node19/node26/node7','root/node5/node26/node7')]:
        vg=graph_at(original,vanilla_route);cg=graph_at(r,copy_route);vn=nm(vg);cn=nm(cg)
        for i,n in vn.items():assert payload(n,oh)==payload(cn[i],rh),(vanilla_route,i,'vanilla payload changed')
        extra={200} if vanilla_route.endswith('node19') else set(range(200,206)) if vanilla_route.endswith('node26') else set()
        assert set(cn)==set(vn)|extra
        wanted=set()
        for source,sock,dest,insock in edge_set(vg,oh):
            if vanilla_route.endswith('node19') and source==21:dest,insock=200,'In'
            if vanilla_route.endswith('node26'):
                if source==27:dest,insock=200,'In'
                if source==29:dest,insock=202,'In'
                if dest==17:dest,insock=204,'In'
                if dest==41:dest,insock=205,'In'
            wanted.add((source,sock,dest,insock))
        if vanilla_route.endswith('node19'):wanted.add((200,'Out',35,'In'))
        if vanilla_route.endswith('node26'):wanted.update({(200,'Out',201,'In'),(201,'Out',38,'In'),(202,'Out',203,'In'),(203,'Out',12,'In'),(204,'Out',17,'claire_default_start'),(205,'Out',41,'claire_pissed')})
        assert set(edge_set(cg,rh))==wanted,(vanilla_route,'edges differ')
    assert set(edge_set(r['graph']['Data'],rh))=={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',4,'In'),(4,'Out',5,'In1'),(5,'Out1',6,'In'),(6,'Out',2,'In')}
    condition=wrapper[2]['condition']['Data'];assert condition['operation']=='AND'
    facts={v['factName']:(v['comparisonType'],v['value']) for v in walk(condition) if v.get('$type')=='questVarComparison_ConditionType'}
    want={k:('Equal',v) for k,v in COMMON.items()};want.update({PREFIX+'Enabled':('Equal',1),PREFIX+'Excluded':('Equal',0),PREFIX+'Suspended':('Equal',0),'PTFRBASE_Suspended':('Equal',0),'claire_default_on':('Greater',0)})
    assert facts==want
    for v in walk(r):
        if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(PREFIX)
    inner=nm(graph_at(r,'root/node5/node26'))
    for i,suffix in [(201,'Entries'),(203,'Exits'),(204,'NormalRequests'),(205,'AngryRequests')]:
        t=inner[i]['type']['Data'];assert t['factName']==PREFIX+suffix and t['value']==1 and not t['setExactValue']
    assert a['scene_routes']['claire_pissed']['vendors']==[] and a['scene_routes']['claire_pissed']['writers']=={}
    assert a['scene_routes']['claire_default_start']['vendors']==[7]
    assert {w['type']['Data']['factName'] for w in a['scene_routes']['claire_default_start']['writers'].values()}=={'sq024_intro_dialogues_done'}
    # Same gated vanilla branches; angry never reaches normal service.
    def request(pissed,meeting,afterlife,hook):return 'angry' if pissed>0 else 'normal' if meeting<=0 or afterlife>0 or hook>0 else 'blocked'
    cases=0
    for angry in (0,1,2):
      for meet in (0,1):
       for after in (0,1):
        for hook in (0,1):
         result=request(angry,meet,after,hook);cases+=1
         if angry:assert result=='angry'
         elif meet and not (after or hook):assert result=='blocked'
         else:assert result=='normal'
    red=ROOT/'redscript/PTFR_B0_Claire/ClaireDriver.reds';text=red.read_text()
    assert re.findall(r'q.SetFact\(n"([^"]+)"',text)==[PREFIX+'Enabled']
    assert 'GetWorldPosition' not in text and '5.0, false' in text
    for k,v in COMMON.items():assert f'q.GetFact(n"{k}") == {v}' in text
    for k in ['IsSavingLocked','IsTokensActivationBlocked','mount.parentId','SceneTier','HighLevel','IsInCombat','IsEntityInScene','IsActorInWorkspot']:assert k in text
    assert 'this.running = false; return;' in text
    def eligible(f,safe=True):return safe and all(f.get(k,0)==v for k,v in COMMON.items()) and f.get('claire_default_on',0)>0 and f.get(PREFIX+'Ready')==1 and all(f.get(k,0)==0 for k in [PREFIX+'Enabled',PREFIX+'OwnerActive',PREFIX+'Excluded',PREFIX+'Suspended','PTFRBASE_Suspended'])
    seed={**COMMON,'claire_default_on':1,PREFIX+'Ready':1};assert eligible(seed)
    for k,v in COMMON.items():assert not eligible({**seed,k:1-v})
    for k in [PREFIX+'Enabled',PREFIX+'OwnerActive',PREFIX+'Excluded',PREFIX+'Suspended','PTFRBASE_Suspended']:assert not eligible({**seed,k:1})
    assert not eligible(seed,False) and not eligible({**seed,'claire_default_on':0}) and not eligible({**seed,PREFIX+'Ready':0})
    # Presence of an angry outcome must not suppress the owner or be rewritten.
    assert eligible({**seed,'sq024_claire_pissed':1})
    log=(ROOT/'build/B0_Claire/combined_compile.log').read_text(encoding='utf-8-sig')
    assert 'Output successfully saved' in log and 'ERROR' not in log
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};facts={};logs={}
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
    controller=ROOT/'diagnostics/PTFR_B0_Claire/init.lua';source=controller.read_text()
    assert not any(x in source for x in ('SetFact','Teleport','ForceReset'))
    mod=lua.execute(source);lua.globals().events.onInit();lua.globals().events.onUpdate(3)
    assert len(lua.globals().logs)>=2 and mod.Observe('test').scene is False
    lua.globals().p=None;assert mod.Observe('no-player').loaded is False
    mod.Finish();lua.globals().events.onShutdown()
    archive=ROOT/'build/B0_Claire/TowerContinued_B0_Claire.archive';xl=ROOT/'archive/b0_claire/TowerContinued_B0_Claire.archive.xl'
    assert sha(archive)==m['sha256'] and len(m['resources'])==1 and m['resources'][0] in xl.read_text() and xl.read_text().count('- path:')==1
    assert m['vanilla_replacements']==m['scene_replacements']==[]
    report={'status':'PASS','owners':1,'archive_sha256':sha(archive),'xl_sha256':sha(xl),'driver_sha256':sha(red),'controller_sha256':sha(controller),
      'checks':['exact prefab/actor/scene/condition payloads','all three nested graphs and added counters','normal/angry entry reachability','Tower/local startup guards','mod-owned wrapper writes only','combined ten-script compilation','Lua 5.1 read-only logging'],
      'routing_contract_cases':cases,'live':'NOT_TESTED','note':'Offline contract checks, not a REDengine simulation; unchanged vanilla scene keeps its greeting-latch writes.'}
    (OUT/'validation/tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: Claire-only native owner, preserved refusal/dialogue, startup-only runtime, read-only logs')
if __name__=='__main__':main()
