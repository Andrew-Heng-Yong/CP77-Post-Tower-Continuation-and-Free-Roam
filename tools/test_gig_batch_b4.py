"""Actual Lua dispatcher tests + source regression. Not native gameplay proof."""
import json,re,sys,copy
from collections import Counter
from catalog_gig_batch_b4 import ROOT,OUT
from catalog_gig_rollout_r2 import read,sha,normalize
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime
LUA=ROOT/'diagnostics/PTFR_GigBatchB4/init.lua'
CAT=ROOT/'diagnostics/PTFR_GigBatchB4/catalogue.json'
STATE=ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds'
OLD='67F3C725B2778A459B904601C179A43C212FF9BEECD6A2B472EDC8E6C1BC2E2F'

def native_regression():
    prior=(OUT/'predecessor/ActivityStateR3.reds').read_text(encoding='utf-8-sig');new=STATE.read_text(encoding='utf-8-sig')
    assert sha(OUT/'predecessor/ActivityStateR3.reds')==OLD
    start=new.index('  // B4 can request one GIG');end=new.index('  private func BaselineFact(',start)
    assert new[:start]+new[end:]==prior,'Original R3 byte-normalized code drift'
    assert re.findall(r'private persistent let [^;]+;',new)==re.findall(r'private persistent let [^;]+;',prior)
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    assert sha(ROOT/'research/activity_state_r3/definition.json')=='4965DC4225D4CC3699AD66448C34A4F9EC647989CC997A4EDF9D5E82D9294E4E'
    block=new[start:end]
    for needle in ('job < 0 || job >= 71','!this.Tower()','!this.frozen','!this.certified','this.faulted','!this.ready',
                   'ArraySize(this.baseline.states) != ActivityDefinition.EntryCount()', 'old == 3 || current == 3','old == 4',
                   '!this.RiteHistory()','!this.MinefieldHistory()','old != 2 || current != 4'):
        assert needle in block,needle
    for forbidden in ('SetFact(', 'ChangeEntryState(', 'RestoreFresh(', 'sideFreshObserved','persistent let','CaptureBeforeEnding(', 'Freeze('):assert forbidden not in block,forbidden
    assert block.count('.Restore()')==3
    definition=read(ROOT/'research/activity_state_r3/definition.json')
    old_gigs={j['id'] for j in definition['jobs'][:71]}
    cat=read(CAT);assert {j['id'] for j in cat['jobs'] if j['legacy_history']}==old_gigs
    assert len(old_gigs)==71 and all(j['id'].startswith('sts_') for j in definition['jobs'][:71])
    policy=read(ROOT/'research/gig_restoration/lore_whitelists_v4_cast.json')['ignore_two_year_gap']['gigs']
    assert {normalize(j['title']) for j in cat['jobs']}=={normalize(t) for t in policy}
    assert [j['id'] for j in cat['jobs'] if not j['legacy_history']]==['sts_wat_lch_05']
    assert {j['id'] for j in cat['jobs'] if j.get('adapter_mode')}=={'sts_wat_nid_02','sts_wat_nid_05','sts_bls_ina_07'}
    review=read(OUT/'source_review.json');assert len(review['jobs'])==72 and sum(review['counts'].values())==72
    for p,h in review['source_inputs'].items():assert sha(ROOT/p)==h,p
    # Missing references and malformed selected graphs stay explicit gaps.
    assert review['counts']=={'SOURCE_CLOSED_REQUIRES_STAGE_REWARD_ACCOUNT_AUDIT':69,'SOURCE_CLOSURE_PENDING':3}
    assert all(r.get('unresolved') for r in review['jobs'] if r['disposition']=='SOURCE_CLOSURE_PENDING')
    for f in ('SetFact','ChangeEntryState','GiveReward','AddToInventory','LaunchQuest','loadfile','dofile'):
        assert f not in LUA.read_text(encoding='utf-8'),f
    return {'predecessor_code_unchanged':True,'persistent_fields_definition_cutoff_unchanged':True,'selected':72,'source_graphs':sum(len(q['graphs']) for r in review['jobs'] for q in r.get('resources',[])),
            'phase_resources':sum(len(r.get('resources',[])) for r in review['jobs']),'scene_references':sum(len(r.get('scenes',[])) for r in review['jobs']),
            'new_native_adapters':0,'pending_adapters':69,'source_closure_gaps':3,'no_direct_lua_native_writes':True}

def lua_checks():
    catalogue=read(CAT);tests=[]
    def session(case,mutate=None):
        l=LuaRuntime(unpack_returned_tuples=True)
        def table(v):
            if isinstance(v,dict):return l.table_from({k:table(x) for k,x in v.items()})
            if isinstance(v,list):return l.table_from([table(x) for x in v])
            return v
        l.globals().cat=table(copy.deepcopy(catalogue));l.globals().case=case
        l.execute('''
          logs,events,calls={}, {}, {}; epoch=1; facts={}; states={}; files={}; printed={}; diskfail=false; lookupfail=false
          function IsDefined(v) return v~=nil and v~=false end
          function EnumInt(v) return v end
          local p={GetEntityID=function()return {hash="18446744073709550000"}end}
          player=p; jm={HasAnyDelayedStateChanges=function()return delayed==true end,
            GetEntryByString=function(_,path,cls) if lookupfail then error("lookup error")end;return {path=path}end,
            GetEntryState=function(_,e)return states[e.path] or 1 end}
          local tower={PostTowerFreeRoamActive=1,PTFRP0_DR13=1,q307_done=1,q307_finished=1,q307_2079=1,q307_main_game_killed=1,q307_ep1_killed=1}
          qs={GetFactStr=function(_,name)if facts[name]~=nil then return facts[name] end;return tower[name] or 0 end}
          sys={BatchEpoch=function()return epoch end, Inspect=function(_,id)return "read:"..id end,
            RestoreGig=function(_,id) calls[#calls+1]={id=id,mode="history"};if backendfail then error("ambiguous backend error")end;return "Refused: unknown history"end,
            Override=function(_,id,mode,confirm) calls[#calls+1]={id=id,mode=mode,confirmation=confirm};return "Explicit history override; Refused: unsupported live stage"end}
          local container={Get=function(_,name)if name~="PTFR.ActivityStateR3.ActivityState" then error("wrong system")end;return sys end}
          Game={GetPlayer=function()return player end,GetQuestsSystem=function()return qs end,GetJournalManager=function()return jm end,GetScriptableSystemsContainer=function()return container end}
          json={decode=function()return cat end,encode=function(v)logs[#logs+1]=v;return "encoded"end}
          print=function(v)printed[#printed+1]=v end
          io={open=function(name,mode)
            if name=="catalogue.json" then return {read=function()return "catalogue"end,close=function()return true end}end
            if mode=="r" then return nil end
            if diskfail then return nil,"disk failure"end
            return {write=function()return true end,flush=function()return true end,close=function()return true end}
          end}
          function registerForEvent(n,f)events[n]=f end
        ''')
        if mutate:l.execute(mutate)
        m=l.execute(LUA.read_text(encoding='utf-8'))
        return l,m
    def run(l):
        for _ in range(76):l.globals().events['onUpdate']()
    for mode in ('plan','history','override'):
        l,m=session(mode);start=getattr(m,{'plan':'PlanAll','history':'RestoreAll','override':'OverrideAll'}[mode])(*(['DISPOSABLE_SAVE'] if mode=='override' else []));assert 'queued' in start,start;run(l)
        r=m.Results();assert r['reviewed']==72 and r['all_whitelisted_restored'] is False
        assert len(l.globals().calls)==(0 if mode=='plan' else 3)
        assert r['pending_adapters']==69 and r['unknown']==0
        assert all(c['id'] in ('sts_wat_nid_02','sts_wat_nid_05','sts_bls_ina_07') for c in l.globals().calls.values())
        if mode=='override':assert all(c['confirmation']=='DISPOSABLE_SAVE' and c['mode']=='resume' for c in l.globals().calls.values())
        tests.append(mode+'_72_rows_only_known_gig_adapters')
    l,m=session('ack');assert 'Refused' in m.OverrideAll('yes');run(l);assert len(l.globals().calls)==0;tests.append('wrong_ack_no_requests')
    l,m=session('completed','for _,j in ipairs(cat.jobs)do states[j.path]=3 end');m.OverrideAll('DISPOSABLE_SAVE');run(l);assert m.Results()['preserved']==72 and len(l.globals().calls)==0;tests.append('all_completed_preserved')
    l,m=session('terminal','for _,j in ipairs(cat.jobs)do for _,f in ipairs(j.terminal_facts)do facts[f]=1 end end');m.OverrideAll('DISPOSABLE_SAVE');run(l);assert len(l.globals().calls)==0;tests.append('nonzero_terminal_markers_no_requests')
    for value in ('facts.q307_done=0','delayed=true','player=nil'):
        l,m=session(value,value);assert 'Refused' in m.OverrideAll('DISPOSABLE_SAVE');run(l);assert len(l.globals().calls)==0;tests.append(value+'_before_requests')
    l,m=session('session');m.RestoreAll();l.execute('epoch=2');run(l);assert m.Results()['reviewed']==0 and len(l.globals().calls)==0;tests.append('same_entity_id_new_epoch_cancelled')
    l,m=session('disk');m.RestoreAll();l.execute('diskfail=true');run(l);assert len(l.globals().calls)==0;tests.append('intent_log_failure_no_backend')
    l,m=session('backend');m.RestoreAll();l.execute('backendfail=true');run(l);assert len(l.globals().calls)==1 and m.Results()['backend_requests']==1;tests.append('ambiguous_backend_no_retry_or_false_undo')
    l,m=session('cancel');m.RestoreAll();m.Cancel();run(l);assert len(l.globals().calls)==0;tests.append('cancel_before_request')
    l,m=session('shutdown');m.RestoreAll();l.globals().events['onShutdown']();run(l);assert len(l.globals().calls)==0;tests.append('shutdown_cancels_remaining')
    l,m=session('lookup','lookupfail=true');m.RestoreAll();run(l);assert len(l.globals().calls)==0 and m.Results()['reviewed']==0;tests.append('native_lookup_exception_aborts')
    for mutation in ('cat.count=71','cat.jobs[2].id=cat.jobs[1].id','cat.jobs[1].adapter_mode="replay"','cat.fingerprint="bad"','cat.jobs[1].path="quests/main_quest/q307"'):
        l,m=session('invalid',mutation);assert 'Refused' in m.RestoreAll();run(l);assert len(l.globals().calls)==0;tests.append(mutation+'_refused')
    l,m=session('inspect');assert 'Outside' in m.Inspect('mq005_alley');assert 'no fabricated' in m.Inspect('sts_wat_lch_05');assert len(l.globals().calls)==0;tests.append('inspect_readonly_and_new_id_unknown_history')
    return {'actual_luajit_cases':len(tests),'cases':tests,'model_not_native_engine':True}

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    regression=native_regression();lua=lua_checks();compile=read(OUT/'compile_result.json')
    assert compile['status']=='PASS_B4_COMPILE_NOT_ENGINE_PROOF' and compile['source_sha256']==sha(STATE) and compile['equipmentex']
    for p,h in {**compile['protected'],**compile['dependencies']}.items():assert sha(p)==h,p
    files=[{'source':'diagnostics/PTFR_GigBatchB4/init.lua','relative':'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigBatchB4/init.lua','sha256':sha(LUA),'predecessor':''},
           {'source':'diagnostics/PTFR_GigBatchB4/catalogue.json','relative':'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_GigBatchB4/catalogue.json','sha256':sha(CAT),'predecessor':''},
           {'source':'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','relative':'r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds','sha256':sha(STATE),'predecessor':OLD}]
    tools=['tools/catalog_gig_batch_b4.py','tools/audit_gig_batch_b4.py','tools/prepare_gig_batch_b4.py','tools/compile_gig_batch_b4.py','tools/test_gig_batch_b4.py','tools/deploy_gig_batch_b4.ps1','tools/test_gig_batch_b4_deployment.ps1']
    result={'status':'PASS_B4_DISPATCHER_OFFLINE_NOT_ALL_GIG_RESTORATION','regression':regression,'lua':lua,'equipmentex_full_compile':True,
            'compile_sha256':sha(OUT/'compile_result.json'),'manifest_sha256':sha(OUT/'manifest.json'),'files':files,'tools':{t:sha(ROOT/t) for t in tools},
            'new_native_adapters':0,'runtime_gig_adapters':3,'pending_gig_adapters':69,'completed_replay_adapters':0}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k in ('status','regression','lua')},indent=2))
if __name__=='__main__':main()
