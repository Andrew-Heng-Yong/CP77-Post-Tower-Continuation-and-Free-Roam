"""Stock catalogue, LuaJIT read-only collector and conservative pair checks."""
import copy,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/gig_restoration/rollout_r2'
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
from analyze_gig_rollout_r2 import assess,classify_markers
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def plain(v):
    if hasattr(v,'items'):
        values=dict(v.items())
        if values and all(isinstance(k,(float,int)) for k in values):return [plain(values[k]) for k in sorted(values)]
        return {str(k):plain(x) for k,x in values.items()}
    return v
def main():
    cat=json.loads((OUT/'catalogue.json').read_text());pin=cat.pop('fingerprint')
    assert hashlib.sha256(json.dumps(cat,sort_keys=True,separators=(',',':')).encode()).hexdigest().upper()==pin
    cat['fingerprint']=pin
    assert len(cat['jobs'])==cat['count']==71 and len({j['id'] for j in cat['jobs']})==71
    assert all(j['native_resources'] and j['journal_entries'] for j in cat['jobs'])
    for p,d in cat['source_inputs'].items():assert sha(ROOT/p)==d,p
    assert cat['runtime_ready'] is False
    source=(ROOT/'diagnostics/PTFR_GigAuditR2/init.lua').read_text()
    for forbidden in ('SetFact','ChangeEntryState','TrackEntry','StartQuest','GiveItem','Override(','Observe(','loadfile','loadstring','Teleport('):assert forbidden not in source,forbidden
    assert 'tonumber(EnumInt(raw))' in source and 'tostring(p:GetEntityID().hash)' in source
    cases=0
    def run(mutate='',expected=True):
        nonlocal cases
        lua=LuaRuntime(unpack_returned_tuples=True);logs=[]
        lua.globals().py_encode=lambda v:json.dumps(plain(v))
        lua.globals().py_decode=lambda _:lua.table_from(cat,recursive=True)
        lua.globals().capture=logs.append
        lua.execute(r'''
          callbacks={};messages={};files={};mutations=0;clock=0
          print=function(s) messages[#messages+1]=s end
          registerForEvent=function(k,v) callbacks[k]=v end
          IsDefined=function(v) return type(v)=='table' end
          EnumInt=function(v) return require('ffi').new('uint64_t',v) end
          json={encode=py_encode,decode=py_decode};os={date=function() return 'STAMP' end}
          io={open=function(name,mode)
            if name=='catalogue.json' then return {read=function() return 'CAT' end,close=function() return true end} end
            if mode=='r' then return files[name] and {close=function() return true end} or nil end
            return {write=function(_,line) capture(line);files[name]=true;return true end,flush=function() return true end,close=function() return true end}
          end}
          player={GetEntityID=function() return {hash=require('ffi').new('uint64_t',18446744073709551615ULL)} end}
          factValue=function() return 0 end;entryState=function() return 1 end;pending=false
          readonly={__index=function(_,k) return function() mutations=mutations+1;error('forbidden '..k) end end}
          qs=setmetatable({GetFactStr=function(_,name) return factValue(name) end},readonly)
          jm=setmetatable({HasAnyDelayedStateChanges=function() return pending end,
            GetEntryByString=function(_,path,cn) return {path=path,class=cn} end,
            GetEntryState=function(_,e) return entryState(e.path) end,
            IsEntryTracked=function() return false end,GetIsObjectiveOptional=function() return false end},readonly)
          Game=setmetatable({GetPlayer=function() return player end,GetQuestsSystem=function() return qs end,GetJournalManager=function() return jm end},readonly)
        ''')
        module=lua.execute(source)
        assert 'queued' in module.Capture()
        if mutate:lua.execute(mutate)
        for _ in range(300):lua.execute('clock=clock+1;callbacks.onUpdate(0.02)')
        rows=[json.loads(x) for x in logs];finished=[x['detail'] for x in rows if x['event']=='CAPTURE_COMPLETE']
        assert lua.globals().mutations==0
        if expected:
            assert len(finished)==1 and finished[0]['stable'],rows[-1]
            assert len(finished[0]['facts'])==len(cat['fact_names'])
            assert len(finished[0]['journal'])==970
            assert finished[0]['player_id']=='18446744073709551615ULL'
        else:assert not finished or finished[0]['stable'] is False
        cases+=1
    run()
    run("entryState=function() return 7 end",False)
    run("factValue=function(name) if clock>60 then return 1 else return 0 end end",False)
    run("player=nil",False)
    job=cat['jobs'][0]
    entries={e['path']:{'present':True,'state':1} for e in job['journal_entries']}
    facts={f:0 for f in cat['fact_names']}
    pre={'journal':copy.deepcopy(entries),'facts':facts};post=copy.deepcopy(pre)
    for state,label in ((3,'PRESERVE_COMPLETED'),(4,'PRESERVE_PRIOR_FAILURE')):
        pre['journal'][job['journal_path']]['state']=state
        assert assess(job,pre,post)['classification']==label;cases+=1
    pre['journal'][job['journal_path']]['state']=1
    assert assess(job,pre,post)['classification']=='FRESH_JOURNAL_BASELINE_NATIVE_UNLOCK_REVIEW_PENDING';cases+=1
    pre['journal'][job['journal_path']]['state']=2;post['journal'][job['journal_path']]['state']=4
    obj=next(e for e in job['journal_entries'] if e['className']=='gameJournalQuestObjective')
    pre['journal'][obj['path']]['state']=2;post['journal'][obj['path']]['state']=4
    assert assess(job,pre,post)['classification']=='STARTED_TOWER_CLEANUP_PATTERN_STAGE_ADAPTER_REQUIRED';cases+=1
    post['journal'][obj['path']]['state']='UNKNOWN'
    assert assess(job,pre,post)['classification']=='UNKNOWN_REFUSE';cases+=1
    assert all(not assess(job,pre,post)['runtime_admitted'] for _ in range(3))
    assert classify_markers({})=='UNKNOWN_WORLD';cases+=1
    result={'status':'PASS_71_GIG_READONLY_AUDIT_NOT_RESTORATION','selected_count':71,'source_coverage':71,'entries':970,'fact_count':len(cat['fact_names']),'cases':cases,'native_binding_live_pending':True,'gameplay_writes':0,
      'files':[{'source':s,'relative':t,'sha256':sha(ROOT/s)} for s,t in [
      ('diagnostics/PTFR_GigAuditR2/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigAuditR2/init.lua'),
      ('research/gig_restoration/rollout_r2/catalogue.json','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigAuditR2/catalogue.json')]],
      'tools':{f'tools/{n}':sha(ROOT/f'tools/{n}') for n in ('catalog_gig_rollout_r2.py','extract_gig_rollout_r2_sources.ps1','analyze_gig_rollout_r2.py','test_gig_rollout_r2.py','deploy_gig_audit_r2.ps1')}}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','tools')},indent=2))
if __name__=='__main__':main()
