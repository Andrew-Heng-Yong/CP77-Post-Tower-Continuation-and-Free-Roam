"""Offline evidence, never a substitute for drinking/stand-up runtime checks."""
import hashlib,json,sys,re
from plan_b0_ordinary_vendor_batch import ROOT,read,resource,graph_at,nm,edge_set,walk
from test_b0_ordinary_vendor_batch import canonical,handles
from audit_b0_ordinary_bars import DEST
VAL=DEST/'validation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    sites=read(DEST/'cohort.json')['sites'];m=read(VAL/'build_manifest.json')
    assert len(sites)==len(m['resources'])==4
    assert sha(DEST/'cohort.json')==m['cohort_sha256']
    archive=ROOT/'build/B0_OrdinaryBars'/m['archive'];assert sha(archive)==m['sha256']
    assert m['scene_replacements']==m['vanilla_replacements']==[]
    xl=ROOT/'archive/b0_ordinary_bars/TowerContinued_B0_OrdinaryBars.archive.xl'
    assert xl.read_text().count('- path:')==4
    assert all(p.startswith('towercontinued\\b0_ordinary_bars\\') and p in xl.read_text() for p in m['resources'])
    for s in sites:
        original=resource(s['source']);oh=handles(original)
        vanilla=nm(graph_at(original,s['graph']));branch=nm(graph_at(original,'root/node'+str(s['outer'])))
        root=read(VAL/(s['id']+'.questphase.json'))['Data']['RootChunk'];rh=handles(root)
        outer=nm(root['graph']['Data']);inner=nm(outer[5]['phaseGraph']['Data'])
        assert set(outer)==set(range(12))
        for node in (s['input'],s['output'],s['scene_node'],s['spawn']['node'],s['despawn']['node'],s['close']['node']):
            assert canonical(inner[node],rh)==canonical(vanilla[node],oh),(s['id'],node)
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
            expected={k:('Equal',v) for k,v in m['common_guards'].items()}
            expected.update({s['prefix']+'Enabled':('Equal',1),s['gate']:('Greater',0)})
            assert facts==expected
        assert inner[s['far']['node']]['condition']['Data']['type']['Data']['factName']==s['prefix']+'Far'
        for v in walk(root):
            if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(s['prefix'])
        for n,suffix in ((10,'Entries'),(11,'Exits')):
            t=outer[n]['type']['Data'];assert t['factName']==s['prefix']+suffix and not t['setExactValue'] and t['value']==1
        for group,key,path in [('regional_sources','source_sha256',s['source']),(s['scene_group'],'scene_sha256',s['scene'])]:
            assert sha(ROOT/'research/b0_vendor_rollout'/group/'raw'/path)==s[key]
    red=ROOT/'redscript/PTFR_B0_OrdinaryBars/OrdinaryBarDriver.reds';r=red.read_text()
    assert '@@' not in r and r.count('this.UpdateSite(q, player, position,')==4
    assert r.count('player.GetWorldPosition()')==1 and r.count('pending = this.AutoSite(')==4
    for s in sites:
        assert f'n"{s["drinking_fact"]}"' in r
    assert r.index('if !pending')<r.index('GetSceneSystem')
    assert 'if old == 0 && value == 1 && !this.CanDepart' in r
    assert 'this.Read(q,drinking) != 0' in r and 'if !this.departureChecked' in r
    for safety in ['IsTokensActivationBlocked','IsSavingLocked','mounting.parentId','PTFRBASE_Suspended','HighLevel','SceneTier']:
        assert safety in r
    assert r.count('q.SetFact(')==1 and r.count('this.Set(q,')==3
    assert 'this.Set(q,enabled,1)' in r and 'this.Set(q,far,value)' in r and 'this.Set(q,n"PTFRB0BAR_Mode",1)' in r
    compile_log=(ROOT/'build/B0_OrdinaryBars/combined_compile.log').read_text(encoding='utf-8-sig')
    assert 'Output successfully saved' in compile_log and 'ERROR' not in compile_log
    # Explicit contract model exercises guards and hysteresis; not engine execution.
    guards={k:v for k,v in m['common_guards'].items() if k!='PTFRB0BAR_Mode'}
    def seed():return {**guards,**{s['gate']:1 for s in sites},**{s['prefix']+'Ready':1 for s in sites}}
    def tick(f,safe=True):
        if not safe or f.get('PTFRB0BAR_Suspended',0) or f.get('PTFRBASE_Suspended',0) or any(f.get(k,0)!=v for k,v in guards.items()):return []
        writes=[]
        for s in sites:
            p=s['prefix']
            if f.get(s['gate'],0)>0 and f.get(p+'Ready')==1 and all(f.get(p+k,0)==0 for k in ('Enabled','Near','Far','Excluded')):
                f[p+'Enabled']=1;writes.append(p+'Enabled')
        return writes
    f=seed();assert len(tick(f))==4 and tick(f)==[]
    for g,v in guards.items():
        f=seed();f[g]=1-v;assert not tick(f)
    assert not tick(seed(),False)
    for g in ('PTFRB0BAR_Suspended','PTFRBASE_Suspended'):
        f=seed();f[g]=1;assert not tick(f)
    for s in sites:
        for k,v in [('Enabled',1),('Near',1),('Far',1),('Excluded',1),('Ready',0)]:
            f=seed();f[s['prefix']+k]=v;assert len(tick(f))==3
        f=seed();f[s['gate']]=0;assert len(tick(f))==3
        f[s['gate']]=1;assert tick(f)==[s['prefix']+'Enabled']
        def far(old,d,near=1,gate=1,drink=0,workspot=False):
            if near!=1 and old!=1:return old
            value=1 if gate<=0 else int(d>=s['rearm_radius'] if old else d>s['exit_radius'])
            if old==0 and value==1 and (drink!=0 or workspot):return old
            return value
        assert far(0,0)==0 and far(0,120)==1 and far(0,120,near=0)==0
        assert far(1,120,near=0)==1 and far(1,0,near=0)==0
        assert far(0,120,drink=1)==0 and far(0,120,workspot=True)==0
        assert far(0,0,gate=0,drink=1)==0 and far(0,0,gate=0,workspot=True)==0
        assert far(0,0,gate=0)==1
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};facts={};logs={}
      function registerForEvent(k,f)events[k]=f end
      function IsDefined(v)return v~=nil end
      json={encode=function(x)table.insert(logs,x);return '{}'end}
      io={open=function()return {write=function()return true end,flush=function()return true end,close=function()end}end}
      q={GetFactStr=function(self,k)return facts[k] or 0 end,SetFactStr=function()error('Forbidden fact write')end}
      p={GetWorldPosition=function()return {x=0,y=0,z=0}end,GetEntityID=function()return 1 end,IsInCombat=function()return false end}
      Game={GetPlayer=function()return p end,GetQuestsSystem=function()return q end,
        GetSceneSystem=function()return {GetScriptInterface=function()return {IsEntityInScene=function()return false end}end}end,
        GetWorkspotSystem=function()return {IsActorInWorkspot=function()return false end}end}
    ''')
    controller=ROOT/'diagnostics/PTFR_B0_OrdinaryBars/init.lua';lt=controller.read_text()
    assert not any(w in lt for w in ('SetFact','Teleport','StopWorkspot','ForceReset'))
    mod=lua.execute(lt);lua.globals().events.onInit();lua.globals().events.onUpdate(3)
    assert len(lua.globals().logs)>=2
    state=mod.Observe('test');assert state.scene is False and state.workspot is False and state.runtime=='unavailable'
    lua.globals().facts[sites[0]['drinking_fact']]=1
    assert mod.Observe('drinking').sites[sites[0]['key']].drinking==1
    lua.globals().p=None;assert mod.Observe('unloaded').loaded is False
    mod.Finish();lua.globals().events.onShutdown()
    report={'status':'PASS','owners':4,'archive_sha256':sha(archive),'xl_sha256':sha(xl),'driver_sha256':sha(red),'controller_sha256':sha(controller),
            'checks':['exact original scene/spawn/close payloads and executable edges','full original scene hashes preserved','native eligibility recheck on entry',
                      'no overlapping prior vendor spawn entry','no wrapper vanilla writes','bootstrap and drink/workspot departure contract model',
                      'combined compile with 7 baseline scripts','read-only Lua 5.1 logger simulation'], 'live':'NOT_TESTED'}
    (VAL/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: four full-scene bar owners, guards, departure model, combined compile, read-only Lua diagnostics')

if __name__=='__main__':main()
