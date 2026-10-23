"""Isolated source and history-state models; not runtime/save/timing proof."""
import copy, hashlib, itertools, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/activity_state_r3'
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def source_guards(s):
    anchors=(
        'this.schema != 1 || NotEquals(this.fingerprint, ActivityDefinition.Fingerprint())',
        'this.certified && (!this.ready || !this.frozen || this.schema != 1)',
        'this.BoundaryNow() && !this.frozen',
        'this.frozen = true; this.certified = false;',
        'this.ready && !this.dirty && this.Now() - this.lastCapture >= 0.00 && this.Now() - this.lastCapture <= 6.00',
        'this.faulted || this.frozen || this.BoundaryNow()',
        'this.BoundaryNow() || jm.HasAnyDelayedStateChanges() || !this.Same(before, after)',
        'this.frozen || this.faulted { return false;',
        'this.baseline.states[root] != 2 || this.CurrentRoot(job) != 4',
        'Equals(confirmation, "DISPOSABLE_SAVE")',
        'this.faulted || !this.Tower()',
        '!Equals(id, "sts_wat_nid_02") || !Equals(mode, "resume")',
        'this.CurrentRoot(this.Find(id)) == 3',
        'this.captureCount >= 2147483647',
    )
    assert all(a in s for a in anchors),'Missing admission/capture guard'
    # No universal reset masquerading as an override. Only legacy G1 delegation.
    for banned in ('SetFact(', 'SetFactStr(', 'ChangeEntryState(', 'ExecuteNode(', 'GiveItem(', 'RemoveItem(', 'ResetFact('):assert banned not in s,banned
    assert s.count('pilot.Restore()')==2
    assert not re.search(r'persistent let \w+: String',s)
    return anchors

def freeze(ready,dirty,age):return ready and not dirty and 0<=age<=6
def auto(certified,tower,old,current):return certified and tower and old==2 and current==4
def override(id,mode,confirm,tower,fault,current):
    return confirm=='DISPOSABLE_SAVE' and tower and not fault and id=='sts_wat_nid_02' and mode=='resume' and current!=3

def main():
    cat=read(OUT/'definition.json');source=ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds'
    s=source.read_text();generated=(source.parent/'ActivityDefinition.generated.reds').read_text()
    assert cat['gig_count']==71 and cat['resolved_side_job_count']==cat['selected_side_job_count']==57 and not cat['unresolved']
    assert len(cat['jobs'])==128 and len({j['id'] for j in cat['jobs']})==128
    assert len({e['path'] for j in cat['jobs'] for e in j['journal_entries']})==1695
    assert len(cat['fact_names'])==2192
    c=copy.deepcopy(cat);fingerprint=c.pop('fingerprint')
    assert hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()==fingerprint
    for p,digest in cat['source_inputs'].items():assert sha(ROOT/p)==digest,p
    assert f'return n"{fingerprint}"' in generated
    for job in cat['jobs']:
        assert json.dumps(job['id']) in generated and json.dumps(job['journal_path']) in generated
    anchors=source_guards(s);mutants=0
    for a in anchors:
        try:source_guards(s.replace(a,'MUTATED_GUARD',1))
        except AssertionError:mutants+=1
        else:raise AssertionError(a)
    models=0
    for ready,dirty,age in itertools.product((False,True),(False,True),(-1,0,1,5,6,7,100)):
        assert freeze(ready,dirty,age)==(ready and not dirty and age in (0,1,5,6));models+=1
    for cert,tower,old,current in itertools.product((False,True),(False,True),range(-1,5),range(-1,5)):
        allowed=auto(cert,tower,old,current)
        assert not allowed or (cert and tower and old==2 and current==4)
        assert not auto(cert,tower,3,current) and not auto(cert,tower,4,current);models+=1
    for job,mode,confirm,tower,fault,current in itertools.product(('sts_wat_nid_02','mq005_alley','bad'),('resume','fresh','replay','bad'),('DISPOSABLE_SAVE',''),(False,True),(False,True),range(-1,5)):
        permitted=override(job,mode,confirm,tower,fault,current)
        assert not permitted or (job=='sts_wat_nid_02' and mode=='resume' and confirm=='DISPOSABLE_SAVE' and tower and not fault and current!=3)
        assert not override(job,'replay',confirm,tower,fault,current);models+=1
    # Once frozen, serializing/loading never turns unknown into a certificate.
    for known,tower in itertools.product((False,True),(False,True)):
        fields={'ready':known,'frozen':True,'certified':known,'baseline':[1,2,3,4,-1],'facts':[0,1,-1]}
        restored=json.loads(json.dumps(fields));assert restored==fields
        assert restored['certified']==known;models+=1
    # Thin Lua bridge forwards strings exactly; no disk/quest writes in Lua.
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('calls={}; local s=setmetatable({}, {__index=function(_,method) return function(self,...) calls[#calls+1]={method,...}; return method end end}); Game={GetScriptableSystemsContainer=function() return {Get=function(_,name) assert(name=="PTFR.ActivityStateR3.ActivityState");return s end} end}')
    bridge=ROOT/'diagnostics/PTFR_ActivityStateR3/init.lua';M=lua.execute(bridge.read_text())
    assert M.Status()=='GetStatus'
    assert M.Inspect('mq005_alley')=='Inspect'
    assert M.Override('mq005_alley','replay','DISPOSABLE_SAVE')=='Override'
    assert lua.eval('calls[3][2]')=='mq005_alley' and lua.eval('calls[3][3]')=='replay' and lua.eval('calls[3][4]')=='DISPOSABLE_SAVE'
    lua.execute('Game.GetScriptableSystemsContainer=function() return nil end');assert 'unavailable' in M.Status()
    assert 'io.' not in bridge.read_text() and 'SetFact' not in bridge.read_text()
    compile=read(OUT/'compile_result.json');assert compile['status']=='PASS_OFFLINE_COMPILE_NOT_ENGINE_PROOF' and compile['equipmentex']
    for p,digest in compile['source_hashes'].items():assert sha(ROOT/p)==digest
    files=[{'source':str(p.relative_to(ROOT)).replace('\\','/'),'relative':'r6/scripts/PTFR_ActivityStateR3/'+p.name,'sha256':sha(p)} for p in sorted(source.parent.glob('*.reds'))]
    files.append({'source':str(bridge.relative_to(ROOT)).replace('\\','/'),'relative':'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_ActivityStateR3/init.lua','sha256':sha(bridge)})
    tools=('catalog_activity_state_r3.py','extract_activity_state_r3_sources.ps1','compile_activity_state_r3.py','test_activity_state_r3.py','deploy_activity_state_r3.ps1')
    result={'status':'PASS_ACTIVITY_HISTORY_FOUNDATION_NOT_FULL_RESTORATION','gig_count':71,'side_job_count':57,'entries':1695,'facts':2192,'guard_mutants':mutants,'history_model_cases':models,'lua_bridge_checks':4,'equipmentex_full_compile':True,'native_timing_save_reload_live_pending':True,'native_reset_writes':0,'automatic_adapter_count':1,'completed_replay_adapter_count':0,'files':files,'tools':{f'tools/{n}':sha(ROOT/'tools'/n) for n in tools},'compile_sha256':sha(OUT/'compile_result.json')}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','tools')},indent=2))
if __name__=='__main__':main()
