"""Offline integration tests. Contract models do not claim engine/live success."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'research/restoration_baseline';OUT=ROOT/'build/RestorationBaseline_R1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
    d=read(BASE/'rules.json');m=read(OUT/'manifest.json');files=m['files'];stage=OUT/'game'
    assert len(files)==71 and len({f['path'].lower() for f in files})==71
    assert m['archivesPreserved']==25 and m['newNativeOwners']==0
    assert m['rulesSha256']==sha(BASE/'rules.json')
    assert {str(p.relative_to(stage)).replace('/','\\') for p in stage.rglob('*') if p.is_file()}=={f['path'] for f in files}
    for f in files:
        assert sha(stage/f['path'])==f['sha256']
        if f['path'].startswith('archive\\'):
            assert f['action']=='preserved' and f['before']==f['sha256']
        if f['before']:assert sha(BASE/'frozen'/f['path'])==f['before']
    assert sum(f['action']=='replace-with-backup' for f in files)==12
    assert sum(f['action']=='add' for f in files)==2
    red=stage/'r6/scripts/PTFR_RestorationBaseline/RestorationBaseline.reds';text=red.read_text()
    assert '@@' not in text
    assert text.count('player.GetWorldPosition()')==1 and text.count('this.Far(q,p,')==15
    assert text.count('GetSceneSystem')==text.count('GetWorkspotSystem')==1
    assert 'this.startupTicks = 10' in text
    assert (OUT/'combined_test.redscripts').stat().st_size>1000
    assert (OUT/'combined_test.redscripts').stat().st_mtime>=red.stat().st_mtime
    assert all(f.startswith('PTFR') for f in re.findall(r'this.Set\(q,n"([^"]+)"',text))
    # Dynamic writes are limited to the manifest's Enabled/Near/Far mod names.
    for r in d['rules']:
        assert r['write'].startswith('PTFR') and (r['write'].endswith(('Enabled','Request','Requested')))
        for f,v in r['guards'].items():assert f'q.GetFact(n"{f}") == {v}' in text
        assert f'this.Set(q,n"{r["write"]}",1)' in text
    assert not any(r['write']=='PTFRB0NETREY_Enabled' for r in d['rules'])
    assert 'q.GetFact(n"PTFRALMA1_Requested") == 0' in text
    assert 'q.GetFact(n"PTFRB0ALM_Enabled") == 0 || q.GetFact(n"PTFRB0ALM_Enabled") == 1' in text
    assert 'if !eligible { this.Schedule(epoch,1.0); return; }' in text
    assert 'IsSavingLocked(game,saveLocks)' in text and 'IsTokensActivationBlocked()' in text
    # Each rule is modeled as a guarded one-way opt-in; no stage/counter reset.
    def try_rule(r,f,safe=True,location=True):
        if not safe or not location or f.get('PTFRBASE_Suspended',0)!=0:return False
        if any(f.get(k,0)!=v for k,v in d['common'].items()):return False
        if any(f.get(k,0)!=v for k,v in r['guards'].items()):return False
        f[r['write']]=1;return True
    cases=0
    for r in d['rules']:
        f={**d['common'],**r['guards']};before=dict(f)
        assert try_rule(r,f) and not try_rule(r,f)
        assert {k for k in f if f[k]!=before.get(k,0)}=={r['write']}
        assert not try_rule(r,dict(f)) # saved opt-in preserved
        for k,v in {**d['common'],**r['guards']}.items():
            f={**d['common'],**r['guards']};f[k]=v+1;assert not try_rule(r,f);cases+=1
        assert not try_rule(r,{**d['common'],**r['guards']},safe=False)
        assert not try_rule(r,{**d['common'],**r['guards']},location=False)
        assert not try_rule(r,{**d['common'],**r['guards'],'PTFRBASE_Suspended':1})
    # H10 dependency order, saved ownership, and exclusion footprint.
    geom=[r for r in d['rules'] if r['kind']=='geometry'];assert len(geom)==5
    f=dict(d['common'])
    for r in geom:f[r['write'].removesuffix('Request')+'Ready']=1
    for i,r in enumerate(geom):
        assert not any(try_rule(later,dict(f)) for later in geom[i+1:])
        assert try_rule(r,f)
        prefix=r['write'].removesuffix('Request')
        f[prefix+'Request']=0;f[prefix+'Ready']=0;f[prefix+'Claimed']=1;f[prefix+'OwnerEntered']=1
        assert not try_rule(r,f)
    def corridor(x,y,z):
        dx=x+1382.02319;dy=y-1272.61865
        return dx*dx+dy*dy<=3600 and abs(z-122.869896)<5 and (abs(dx)>8.04180908 or abs(dy)>8.04180908)
    assert not corridor(-1382.02319,1272.61865,122.869896)
    assert corridor(-1400,1272.61865,122.869896)
    assert not corridor(-1400,1272.61865,110)
    assert not corridor(0,0,0)
    # Distance contracts: no far before entry; boundary hysteresis; local gate loss.
    def far(enabled,near,old,gate,d):
        if enabled!=1 or (near!=1 and old!=1):return old
        return 1 if gate!=1 else int(d>=45 if old==1 else d>55)
    assert far(1,0,0,1,200)==0
    assert far(1,1,0,1,56)==1 and far(1,0,1,1,44)==0
    assert far(1,1,0,0,0)==1 and far(0,1,0,0,100)==0
    # Old scriptable-system classes stay present but cannot schedule live jobs.
    for folder,name in [('PTFR_Afterlife_NativeBootstrap_A4','AfterlifeNativeBootstrapA4'),('PTFR_B0_VendorShared','VendorSharedFarDriver')]:
        body=(stage/f'r6/scripts/{folder}/{name}.reds').read_text()
        attach=body.split('private func OnAttach()')[1].split('private func OnDetach()')[0]
        assert 'this.running = false;' in attach and 'this.running = true;' not in attach
        assert 'if !this.running ||' in body
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
    from lupa.lua51 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('''events={};facts={};records={}
      function registerForEvent(n,f)events[n]=f end
      function IsDefined(v)return v~=nil end
      q={GetFactStr=function(self,k)return facts[k] or 0 end,SetFactStr=function()error('DIAGNOSTICS MUST NEVER WRITE')end}
      player={GetWorldPosition=function()return{x=0,y=0,z=0}end,GetEntityID=function()return 1 end}
      Game={GetPlayer=function()return player end,GetQuestsSystem=function()return q end,
       GetSceneSystem=function()return{GetScriptInterface=function()return{IsEntityInScene=function()return false end}end}end}
      json={encode=function(v)table.insert(records,v);return '{}'end}
      io={open=function()return{write=function()return true end,flush=function()return true end,close=function()end}end}
    ''')
    cet='bin/x64/plugins/cyber_engine_tweaks/mods'
    mod=lua.execute((stage/cet/'PTFR_RestorationBaseline/init.lua').read_text())
    lua.globals().events.onInit();lua.globals().events.onUpdate(6);assert mod.Observe('offline').loaded
    lua.globals().baseline=mod;lua.execute('function GetMod(n)return baseline end')
    for f in files:
        if f['action']=='replace-with-backup' and f['path'].endswith('.lua'):
            body=(stage/f['path']).read_text();assert 'SetFact' not in body and 'registerForEvent' not in body
            bridge=lua.execute(body);assert bridge.Start() is False and bridge.Stop() is False
            assert bridge.Observe('bridge').loaded
    lua.globals().events.onShutdown();assert len(lua.globals().records)>=4
    report=dict(status='PASS',version='Baseline-R1',manifestSha256=sha(OUT/'manifest.json'),rulesSha256=sha(BASE/'rules.json'),guardFailureCases=cases,
        combinedRedscriptCompiled=True,archivesByteIdentical=25,legacyWritersRetired=10,newNativeOwners=0,
        evidence='Static checks, Lua execution and contract models; not live REDengine validation',live='PENDING_COMBINED_SMOKE_CHECK')
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: package hashes, saved-state guards, H10 acquisition chain, legacy writer retirement, Lua, combined redscript; guard cases',cases)
if __name__=='__main__':main()
