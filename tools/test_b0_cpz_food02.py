"""One exact scene-location correction; all other native payloads unchanged."""
import hashlib,json,sys,copy
from plan_b0_ordinary_vendor_batch import ROOT,read,resource,graph_at,nm,edge_set,walk
from test_b0_ordinary_vendor_batch import canonical,handles
from plan_b0_cpz_food02 import DEST
VAL=DEST/'validation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    s=read(DEST/'cohort.json')['sites'][0];m=read(VAL/'build_manifest.json')
    assert m['new_sites']==1 and len(m['resources'])==1
    assert m['scene_replacements']==m['vanilla_replacements']==[]
    assert sha(DEST/'cohort.json')==m['cohort_sha256']
    archive=ROOT/'build/B0_CPZFood02'/m['archive'];assert sha(archive)==m['sha256']
    original=resource(s['source']);oh=handles(original)
    vanilla=nm(graph_at(original,s['graph']));branch=nm(graph_at(original,'root/node'+str(s['outer'])))
    root=read(VAL/(s['id']+'.questphase.json'))['Data']['RootChunk'];rh=handles(root)
    outer=nm(root['graph']['Data']);inner=nm(outer[5]['phaseGraph']['Data'])
    assert set(outer)==set(range(12))
    for node in (s['input'],s['output'],s['spawn']['node'],s['despawn']['node'],s['close']['node']):
        assert canonical(inner[node],rh)==canonical(vanilla[node],oh),node
    actual=canonical(inner[s['scene_node']],rh);expected=canonical(vanilla[s['scene_node']],oh)
    assert actual['sceneLocation']['nodeRef']['$value']==s['resolved_scene_marker']
    actual['sceneLocation']['nodeRef']=copy.deepcopy(expected['sceneLocation']['nodeRef'])
    assert actual==expected,'Unapproved additional scene-node change'
    assert canonical(outer[3]['condition'],rh)==canonical(branch[s['outer_distance']['node']]['condition'],oh)
    assert outer[5]['phaseInstancePrefabs']==branch[s['phase']]['phaseInstancePrefabs']==[]
    assert set(edge_set(root['graph']['Data'],rh))=={
        (0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',9,'In'),(9,'True',4,'In'),(9,'False',2,'In'),
        (4,'Out',10,'In'),(10,'Out',5,'In1'),(5,'Out1',6,'In'),(6,'Out',11,'In'),(11,'Out',7,'In'),(7,'Out',8,'In'),(8,'Out',2,'In')}
    assert set(edge_set(outer[5]['phaseGraph']['Data'],rh))=={
        (s['input'],'Out',s['spawn']['node'],'In'),(s['input'],'Out',102,'In'),(102,'Out',s['far']['node'],'In'),
        (s['spawn']['node'],'Out',100,'In'),(100,'Out',s['close']['node'],'In'),(s['close']['node'],'Out',101,'In'),
        (101,'Out',s['scene_node'],s['scene_socket']),(s['far']['node'],'Out',s['despawn']['node'],'In'),
        (s['despawn']['node'],'Out',103,'In'),(103,'Out',s['output'],'In')}
    for n in (2,9):
        cond=outer[n]['condition']['Data'];assert cond['operation']=='AND'
        facts={v['factName']:(v['comparisonType'],v['value']) for v in walk(cond) if v.get('$type')=='questVarComparison_ConditionType'}
        want={k:('Equal',v) for k,v in m['common_guards'].items()};want.update({s['prefix']+'Enabled':('Equal',1),s['gate']:('Greater',0)})
        assert facts==want
    for v in walk(root):
        if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(s['prefix'])
    assert inner[s['far']['node']]['condition']['Data']['type']['Data']['factName']==s['prefix']+'Far'
    for n,suffix in ((10,'Entries'),(11,'Exits')):
        t=outer[n]['type']['Data'];assert t['factName']==s['prefix']+suffix and not t['setExactValue'] and t['value']==1
    for group,key,path in [('regional_sources','source_sha256',s['source']),(s['scene_group'],'scene_sha256',s['scene'])]:
        assert sha(ROOT/'research/b0_vendor_rollout'/group/'raw'/path)==s[key]
    xl=ROOT/'archive/b0_cpz_food02/TowerContinued_B0_CPZFood02.archive.xl'
    assert xl.read_text().count('- path:')==1 and m['resources'][0] in xl.read_text()
    red=ROOT/'redscript/PTFR_B0_CPZFood02/CPZFood02Driver.reds';r=red.read_text()
    assert '@@' not in r and r.count('this.UpdateSite(q, position,')==1
    assert r.count('player.GetWorldPosition()')==1 and '2025.0, 2500.0' in r
    for k in ['PTFRBASE_Suspended','IsSavingLocked','IsTokensActivationBlocked','mounting.parentId','SceneTier','HighLevel']:
        assert k in r
    assert r.index('if !pending')<r.index('GetSceneSystem')
    assert all('PTFRB0CPZF2_' in line or 'q.SetFact(enabled,' in line or 'q.SetFact(far,' in line for line in r.splitlines() if 'q.SetFact(' in line)
    compile_log=(ROOT/'build/B0_CPZFood02/combined_compile.log').read_text(encoding='utf-8-sig')
    assert 'Output successfully saved' in compile_log and 'ERROR' not in compile_log
    # Read-only Lua executable checks; engine execution still requires user test.
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
    controller=ROOT/'diagnostics/PTFR_B0_CPZFood02/init.lua';text=controller.read_text()
    assert not any(word in text for word in ('SetFact','Teleport','ForceReset'))
    mod=lua.execute(text);lua.globals().events.onInit();lua.globals().events.onUpdate(3)
    assert len(lua.globals().logs)>=2 and mod.Observe('test').scene is False
    lua.globals().p=None;assert mod.Observe('unloaded').loaded is False
    mod.Finish();lua.globals().events.onShutdown()
    # Bootstrap/exit contract model, including saved/in-flight/no-default cases.
    guards={k:v for k,v in m['common_guards'].items() if k!='PTFRB0CPZF2_Mode'}
    def eligible(f,safe=True):return safe and all(f.get(k,0)==v for k,v in guards.items()) and f.get(s['gate'],0)>0 and f.get('Ready')==1 and all(f.get(k,0)==0 for k in ['Enabled','Near','Far','Excluded','Suspended','BaselineSuspended'])
    seed={**guards,s['gate']:1,'Ready':1};assert eligible(seed)
    for k,v in guards.items():assert not eligible({**seed,k:1-v})
    for k in ['Enabled','Near','Far','Excluded','Suspended','BaselineSuspended']:assert not eligible({**seed,k:1})
    assert not eligible(seed,False) and not eligible({**seed,'Ready':0}) and not eligible({**seed,s['gate']:0})
    for old,d,want in [(0,0,0),(0,51,1),(1,46,1),(1,44,0)]:assert int(d>=45 if old else d>50)==want
    report={'status':'PASS','owners':1,'archive_sha256':sha(archive),'xl_sha256':sha(xl),'driver_sha256':sha(red),'controller_sha256':sha(controller),
            'approved_scene_node_change':{'property':'sceneLocation.nodeRef','before':s['scene_marker'],'after':s['resolved_scene_marker']},
            'checks':['exact remaining native payloads/edges','Tower and local guard recheck','mod-only wrapper facts','exact world mappin anchor',
                      'source scene unchanged','combined 9-script compile','Lua 5.1 read-only logger','bootstrap and exit contract'], 'live':'NOT_TESTED'}
    (VAL/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: one narrow vendor owner, one approved marker correction, complete vanilla scene, combined compiler and diagnostics')

if __name__=='__main__':main()
