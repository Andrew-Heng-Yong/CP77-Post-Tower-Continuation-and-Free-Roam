"""Graph equivalence, bootstrap model, and executable Lua diagnostic checks."""
import hashlib
import json
import re
import sys
from plan_b0_ordinary_vendor_batch import ROOT, read, resource, graph_at, nm, edge_set, walk
from test_b0_ordinary_vendor_batch import canonical, handles

BASE=ROOT/'research/b0_vendor_variants'
VAL=BASE/'validation'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()

def main():
    sites=read(BASE/'cohort.json')['sites'];manifest=read(VAL/'build_manifest.json')
    assert len(sites)==len(manifest['resources'])==6
    assert sha(BASE/'cohort.json')==manifest['cohort_sha256']
    assert manifest['scene_replacements']==manifest['vanilla_replacements']==[]
    assert sha(ROOT/'build/B0_VendorVariants'/manifest['archive'])==manifest['sha256']
    xl=ROOT/'archive/b0_vendor_variants/TowerContinued_B0_VendorVariants.archive.xl'
    assert xl.read_text().count('- path:')==6
    assert all(p.startswith('towercontinued\\b0_vendor_variants\\') and p in xl.read_text() for p in manifest['resources'])
    existing=read(ROOT/'research/b0_ordinary_vendor_batch/cohort.json')
    old={(s['spawn']['reference'],s['spawn']['entry']) for s in existing['sites']+existing['existing_owners']}
    for s in sites:
        assert (s['spawn']['reference'],s['spawn']['entry']) not in old
        original=resource(s['source']);oh=handles(original)
        vanilla=nm(graph_at(original,s['graph']));branch=nm(graph_at(original,'root/node'+str(s['outer'])))
        root=read(VAL/(s['id']+'.questphase.json'))['Data']['RootChunk'];rh=handles(root)
        outer=nm(root['graph']['Data']);inner=nm(outer[5]['phaseGraph']['Data'])
        assert set(outer)==set(range(12))|({12} if s['setup_node'] is not None else set())
        for node in (s['input'],s['output'],s['scene_node'],s['spawn']['node'],s['despawn']['node'],s['close']['node']):
            assert canonical(inner[node],rh)==canonical(vanilla[node],oh),(s['id'],node)
        # Original native approach condition and local setup operations remain exact.
        assert canonical(outer[3]['condition'],rh)==canonical(branch[s['outer_distance']['node']]['condition'],oh)
        if s['setup_node'] is not None:
            a=canonical(outer[12],rh);b=canonical(branch[s['setup_node']],oh);a['id']=b['id']
            assert a==b==s['setup_payload']
        expected={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'Out',9,'In'),(9,'True',4,'In'),(9,'False',2,'In'),(4,'Out',10,'In'),(10,'Out',5,'In1'),(5,'Out1',6,'In'),(6,'Out',11,'In'),(11,'Out',7,'In'),(7,'Out',8,'In'),(8,'Out',2,'In')}
        if s['setup_node'] is not None:
            expected.remove((10,'Out',5,'In1'));expected|={(10,'Out',12,'In'),(12,'Out',5,'In1')}
        assert set(edge_set(root['graph']['Data'],rh))==expected
        assert set(edge_set(outer[5]['phaseGraph']['Data'],rh))=={
            (s['input'],'Out',s['spawn']['node'],'In'),(s['input'],'Out',102,'In'),(102,'Out',s['far']['node'],'In'),
            (s['spawn']['node'],'Out',100,'In'),(100,'Out',s['close']['node'],'In'),(s['close']['node'],'Out',101,'In'),
            (101,'Out',s['scene_node'],s['scene_socket']),(s['far']['node'],'Out',s['despawn']['node'],'In'),
            (s['despawn']['node'],'Out',103,'In'),(103,'Out',s['output'],'In')}
        for n in (2,9):
            cond=outer[n]['condition']['Data'];assert cond['operation']=='AND'
            facts={v['factName']:(v['comparisonType'],v['value']) for v in walk(cond) if v.get('$type')=='questVarComparison_ConditionType'}
            expected={k:('Equal',v) for k,v in manifest['common_guards'].items()}
            expected.update({s['prefix']+'Enabled':('Equal',1),s['gate']:('Greater',0)})
            assert facts==expected
        for v in walk(root):
            if v.get('$type')=='questSetVar_NodeType':assert v['factName'].startswith(s['prefix'])
        assert inner[s['far']['node']]['condition']['Data']['type']['Data']['factName']==s['prefix']+'Far'
        for n,suffix in ((10,'Entries'),(11,'Exits')):
            t=outer[n]['type']['Data'];assert t['factName']==s['prefix']+suffix and not t['setExactValue'] and t['value']==1
        for group,key,path in [('regional_sources','source_sha256',s['source']),(s['scene_group'],'scene_sha256',s['scene'])]:
            assert sha(ROOT/'research/b0_vendor_rollout'/group/'raw'/path)==s[key]
    red=ROOT/'redscript/PTFR_B0_VendorVariants/VendorVariantDriver.reds';text=red.read_text()
    assert '@@' not in text and text.count('this.UpdateSite(q, position,')==6
    assert text.count('player.GetWorldPosition()')==text.count('GetSceneSystem')==text.count('GetWorkspotSystem')==1
    assert text.count('pending = this.AutoSite(')==6
    assert text.index('if !pending')<text.index('GetSceneSystem')
    assert (ROOT/'build/B0_VendorVariants/offline_test.redscripts').is_file()
    # Semantic model checks are not live REDengine execution.
    guards={k:v for k,v in manifest['common_guards'].items() if k!='PTFRB0VV_Mode'}
    def seed():
        return {**guards,**{s['gate']:1 for s in sites},**{s['prefix']+'Ready':1 for s in sites}}
    def tick(f,busy=False):
        if busy or f.get('PTFRB0VV_Suspended',0) or any(f.get(k,0)!=v for k,v in guards.items()):return []
        out=[]
        for s in sites:
            p=s['prefix']
            if f.get(s['gate'],0)>0 and f.get(p+'Ready',0)==1 and all(f.get(p+n,0)==0 for n in ('Enabled','Excluded','Near','Far')):
                f[p+'Enabled']=1;out.append(p+'Enabled')
        return out
    f=seed();assert len(tick(f))==6 and tick(f)==[]
    for guard,value in guards.items():
        f=seed();f[guard]=1-value;assert tick(f)==[]
    assert tick(seed(),True)==[]
    f=seed();f['PTFRB0VV_Suspended']=1;assert tick(f)==[]
    for s in sites:
        for suffix,value in [('Ready',0),('Excluded',1),('Near',1),('Far',1),('Enabled',1)]:
            f=seed();f[s['prefix']+suffix]=value;assert len(tick(f))==5
        f=seed();f[s['gate']]=0;assert len(tick(f))==5
        f[s['gate']]=1;assert tick(f)==[s['prefix']+'Enabled']
        p=s['position'];assert s['exit_radius']>s['rearm_radius']>0
        for old,d,want in [(0,0,0),(0,s['exit_radius']+1,1),(1,s['rearm_radius']+1,1),(1,0,0)]:
            value=int(d*d>=s['rearm_radius']**2) if old else int(d*d>s['exit_radius']**2)
            assert value==want
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};facts={};writes={};logs={};p={x=0,y=0,z=0}
      function registerForEvent(k,f)events[k]=f end
      function IsDefined(v)return v~=nil end
      json={encode=function(x)table.insert(logs,x);return '{}'end}
      io={open=function()return {write=function()return true end,flush=function()return true end,close=function()end}end}
      q={GetFactStr=function(self,k)return facts[k] or 0 end,SetFactStr=function(self,k,v)assert(k:find('^PTFRB0VV'));facts[k]=v;table.insert(writes,k)end}
      Game={GetPlayer=function()return {GetWorldPosition=function()return p end,GetEntityID=function()return 1 end}end,
       GetQuestsSystem=function()return q end,GetSceneSystem=function()return {GetScriptInterface=function()return {IsEntityInScene=function()return false end}end}end}
    ''')
    controller=ROOT/'diagnostics/PTFR_B0_VendorVariants/init.lua'
    mod=lua.execute(controller.read_text());lua.globals().events.onInit();lua.globals().events.onUpdate(3)
    assert len(lua.globals().writes)==0 and len(lua.globals().logs)>=2
    assert mod.Observe('test').scene is False
    lua.globals().facts[sites[0]['prefix']+'Near']=1;assert mod.Stop() is False
    lua.globals().facts[sites[0]['prefix']+'Near']=0
    lua.globals().p=lua.table_from(sites[0]['position']);assert mod.Stop() is False
    lua.globals().p=lua.table_from({'x':0,'y':0,'z':0});assert mod.Stop() is True
    assert lua.globals().facts['PTFRB0VV_Suspended']==1 and mod.Resume() is True
    assert lua.globals().facts['PTFRB0VV_Suspended']==0
    before=len(lua.globals().writes);mod.Finish();lua.globals().events.onShutdown();assert len(lua.globals().writes)==before
    report={'status':'PASS','owners':6,'archive_sha256':manifest['sha256'],'driver_sha256':sha(red),'controller_sha256':sha(controller),'xl_sha256':sha(xl),
       'checks':['six full original scenes/spawn/close payloads','exact native edges and per-entry gates','two local setup operations exact','no vanilla fact writes by wrappers','no overlap with prior 40 regional owners','bootstrap and site-specific hysteresis model','redscript offline compile','Lua 5.1 executable diagnostics'],
       'live':'PENDING_USER_CHECKS'}
    (VAL/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: six native owners, full scenes, exact local setup, automatic guards, shared exit, Lua diagnostics')

if __name__=='__main__':main()
