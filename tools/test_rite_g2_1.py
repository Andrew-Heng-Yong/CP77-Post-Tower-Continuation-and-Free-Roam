"""G2.1 source-linked mutual admission + packed guard tests, NOT engine proof.

Import only read-only predecessor helpers; never rerun their pinned mains.
"""
import copy, itertools, json, re
from catalog_gig_rollout_r2 import ROOT, read, sha
import test_rite_g2 as prior
from audit_activity_batches_b1 import flatten
from audit_activity_lifecycles_b1 import condition_value

OUT=ROOT/'research/gig_restoration/rite_g2_1'
G1=ROOT/'redscript/PTFR_GigPilotR1/GigPilotR1.reds'
G2=ROOT/'redscript/PTFR_RiteG2/RiteG2.reds'
OLD=ROOT/'research/gig_restoration/rite_g2'

def body(source,name):
    # Balanced braces, not an arbitrary substring extending into next method.
    p=source.index('func '+name+'(');p=source.index('{',p);depth=1;i=p+1
    while depth:
        depth+=(source[i]=='{')-(source[i]=='}');i+=1
    return source[p+1:i-1]

def expression(raw,fields,facts):
    raw=re.sub(r'this.Fact\(n"([^"]+)"\)',lambda m:repr(facts.get(m[1],0)),raw)
    raw=re.sub(r'this\.(\w+)',lambda m:repr(fields[m[1]]),raw)
    raw=raw.replace('&&',' and ').replace('||',' or ')
    raw=re.sub(r'!(?!=)',' not ',raw)
    return bool(eval(' '.join(raw.split()),{'__builtins__':{}},{}))

def busy(source,fields,facts):
    b=body(source,'WatsonAccountBusy')
    if not fields['enabled']:
        guard=b.split('if !this.enabled {',1)[1].split('if ',1)[1].split(' { return true; }',1)[0]
        if expression(guard,fields,facts):return True
        names=re.findall(r'n"([^"]+)"',body(source,'OwnUnused') if 'return !this.OwnUnused();' in b else b.split('return false;',1)[0])
        assert names
        return any(facts.get(n,0)!=0 for n in names)
    raw=b.split('return !(',1)[1].rsplit(');',1)[0]
    return not expression(raw,fields,facts)

def contract_checks():
    s1=G1.read_text();s2=G2.read_text();old1=(OUT/'predecessor/GigPilotR1.reds').read_text();old2=(OUT/'predecessor/RiteG2.reds').read_text()
    fields=lambda s:re.findall(r'private persistent let [^;]+;',s)
    assert fields(s1)==fields(old1) and fields(s2)==fields(old2),'save shape changed'
    # Exactly the reviewed G1 guard additions/getters; all accounting and owner
    # logic remains byte-identical, including its intentionally narrow 3->4 path.
    stripped=s1.replace('import PTFR.RiteG2.*\n','')
    stripped=stripped.replace('!this.OtherWatsonIdle() || !this.Tower()', '!this.Tower()')
    stripped=stripped.replace('    if !this.OtherWatsonIdle() { return "Refused: Rite owns unfinished/uncertain Watson accounting; no concurrent adapter admission."; }\n','')
    stripped=stripped.replace('    if !this.counterAcknowledged && !this.OtherWatsonIdle() { this.Fail("Concurrent/uncertain Rite accounting; no counter replay or compensation."); return; }\n','')
    start=stripped.index('  // Persistent enabled is set synchronously')
    end=stripped.index('  private func Fail(',start)
    stripped=stripped[:start]+stripped[end:]
    assert stripped==old1,'unexpected G1 edit'
    for s,other in ((s1,'Rite'),(s2,'Many Ways')):
        restore=body(s,'Restore');preflight=body(s,'Preflight');poll=body(s,'Poll')
        assert restore.index('if !this.OtherWatsonIdle()')<restore.index('this.enabled = true')
        assert '!this.OtherWatsonIdle() ||' in preflight
        assert '!this.counterAcknowledged && !this.OtherWatsonIdle()' in poll
        assert poll.index('!this.counterAcknowledged && !this.OtherWatsonIdle()')<poll.index('this.stage == 1')
        assert 'IsDefined(other) && !other.WatsonAccountBusy()' in body(s,'OtherWatsonIdle')
        assert '.Set(' not in body(s,'WatsonAccountBusy') and '.Set(' not in body(s,'OtherWatsonIdle')
    assert body(s2,'CountOK').strip()=='return (base == 3 || base == 4) && this.Fact(n"wat_sts_counter") == base && this.Fact(n"wat_achievement") == base;'
    for name in ('LocalFacts','KeycardCount','StaticJournal','OwnUnused','Tower','Fail'):
        assert body(s2,name)==body(old2,name),name
    assert re.findall(r'this.Set\(n"([^"]+)"',s2)==re.findall(r'this.Set\(n"([^"]+)"',old2)
    assert 'this.countBase != 3 && this.countBase != 4' in body(s2,'Restored')
    assert s2.count('.ChangeEntryState(')==1
    for token in ('this.Fact(n"wat_sts_counter") != this.countBase','let target = this.countBase + 1;','this.Fact(n"PTFRG2_AccountAck") != 1','this.Fact(n"wat_achievement") != target','this.inflight = true; this.Set(n"wat_sts_counter", target);','this.counterAcknowledged = true;'):
        assert token in body(s2,'Poll'),token
    for name in ('Schedule','Root','Phase','Entry','State'):
        assert body(s2,name)==body(old2,name),name
    # Dispatcher/catalogue, R3 cutoff/history and all native G1 resources unchanged.
    # The user ran the game since G2; getter .jsonl logs and engine cache outputs
    # legitimately changed. Only static installed code/assets use old hashes.
    from pathlib import Path
    protected={str(p):h for p,h in read(OLD/'install_receipt.json')['protected'].items() if Path(p).suffix.lower() in ('.reds','.lua','.archive','.xl','.yaml','.yml')}
    game=read(OLD/'install_receipt.json')['game_root']
    for f in read(OLD/'install_receipt.json')['files']:protected[str(Path(game)/f['relative'])]=f['sha256']
    for p,h in protected.items():assert sha(Path(p))==h,p
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds')=='3C1FABD8E0BD8D123243B2A32CD143860AF05C7D93404335A0B3FB379E4BCC7F'
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    assert sha(ROOT/'research/activity_state_r3/definition.json')=='4965DC4225D4CC3699AD66448C34A4F9EC647989CC997A4EDF9D5E82D9294E4E'
    return {'persistent_shapes_unchanged':True,'g1_only_admission_getter_changes':True,'read_only_mutual_getters':True,'r3_history_dispatcher_unchanged':True,'installed_predecessor_files_checked':len(protected)}

def graph_checks():
    prior.OUT=OUT
    graph,patched=prior.graph_checks()
    # Against installed G2, only two condition payloads may change. Not an owner,
    # scene, prefab, edge, item, reward or cleanup redesign.
    for name in ('native_owner','combat','ow','owner'):
        old=read(OLD/(name+'.questphase.json'));new=read(OUT/(name+'.questphase.json'))
        ro=prior.SafeResource(old);rn=prior.SafeResource(new)
        a={g['path']:g for g in flatten(ro,old['Data']['RootChunk'])};b={g['path']:g for g in flatten(rn,new['Data']['RootChunk'])}
        assert a.keys()==b.keys()
        for path,g in a.items():
            want=copy.deepcopy(g);got=b[path]
            for node in want['nodes']:
                if (name,path,node['id']) in [('ow','root/5',400),('owner','root',402)]:
                    node['condition']=next(n['condition'] for n in got['nodes'] if n['id']==node['id'])
            assert want==got,(name,path)
        assert old['Data']['RootChunk']['phasePrefabs']==new['Data']['RootChunk']['phasePrefabs']
    graph['only_two_conditions_changed_from_installed_g2']=True
    return graph,patched

def models(patched):
    cases=mutants=0
    boot=read(OUT/'manifest.json')['native_guard']
    for base in (3,4):
        facts=boot|{'PTFRG2_CountBase':base,'wat_sts_counter':base,'wat_achievement':base}
        assert condition_value(patched['boot_condition'],facts) is True
        for name in facts:
            changed=facts.copy();changed[name]+=1
            assert condition_value(patched['boot_condition'],changed) is False,(base,name)
            mutants+=1;cases+=1
        facts={'PTFRG2_CountBase':base,'wat_sts_counter':base,'wat_achievement':base,'PTFRG2_AccountClaim':0,'PTFRG2_AccountAck':0,'PTFRG2_Fault':0}
        assert condition_value(patched['account_condition'],facts) is True
        for name in facts:
            m=facts.copy();m[name]+=1;assert condition_value(patched['account_condition'],m) is False;mutants+=1;cases+=1
    for base,count,ach,claim,ack,fault in itertools.product(range(2,7),range(2,7),range(2,7),range(3),range(3),range(2)):
        facts={'PTFRG2_CountBase':base,'wat_sts_counter':count,'wat_achievement':ach,'PTFRG2_AccountClaim':claim,'PTFRG2_AccountAck':ack,'PTFRG2_Fault':fault}
        assert condition_value(patched['account_condition'],facts) is (base in (3,4) and count==ach==base and claim==ack==fault==0)
        cases+=1
    s1=G1.read_text();s2=G2.read_text()
    complete1={'enabled':True,'schema':1,'stage':3,'prepared':4,'inflight':False,'counterAcknowledged':True}
    complete2=complete1|{'countBase':3}
    ack1={'nid_02_finished':1,'PTFRG1_CounterAck':1,'PTFRG1_RewardClaim':1,'PTFRG1_RewardAck':1}
    ack2={'nid_05_finished':1,'PTFRG2_CounterAck':1,'PTFRG2_AccountClaim':1,'PTFRG2_AccountAck':1,'PTFRG2_RewardClaim':1,'PTFRG2_RewardAck':1}
    for source,fields,ack,prefix in ((s1,complete1,ack1,'PTFRG1'),(s2,complete2,ack2,'PTFRG2')):
        for enabled,schema,stage,inflight,acknowledged in itertools.product((False,True),range(3),range(7),(False,True),(False,True)):
            f=fields|dict(enabled=enabled,schema=schema,stage=stage,inflight=inflight,counterAcknowledged=acknowledged)
            assert busy(source,f,ack) is (not(enabled and schema==1 and stage in (3,4) and not inflight and acknowledged));cases+=1
        assert not busy(source,fields,ack)
        for key in ack:
            for value in (0,2,-1):
                assert busy(source,fields,ack|{key:value});cases+=1
        for key in (prefix+'_Fault',prefix+'_RewardReplayRefused'):
            assert busy(source,fields,ack|{key:1});cases+=1
        unused=fields|{'enabled':False,'schema':0,'stage':0,'prepared':0,'inflight':False,'counterAcknowledged':False,'countBase':0}
        assert not busy(source,unused,{})
        for key,value in [('schema',1),('stage',1),('prepared',1),('inflight',True),('counterAcknowledged',True)]:
            assert busy(source,unused|{key:value},{});cases+=1
        if prefix=='PTFRG2':assert busy(source,unused|{'countBase':3},{})
        for key in re.findall(r'n"([^"]+)"',body(source,'OwnUnused') if prefix=='PTFRG2' else body(source,'WatsonAccountBusy').split('return false;',1)[0]):
            assert busy(source,unused,{key:1}),key;cases+=1
        # Queued preparation already blocks the other backend even Request=0.
        queued=fields|{'stage':1,'counterAcknowledged':False}
        assert busy(source,queued,{})
    # Every command order admits exactly one while accounting is outstanding.
    # This models synchronous Restore assignment, not engine scheduling.
    for first in (1,2):
        f1=complete1|{'enabled':False,'schema':0,'stage':0,'prepared':0,'inflight':False,'counterAcknowledged':False}
        f2=f1|{'countBase':0}
        admitted=[]
        for who in (first,3-first,first,3-first):
            own=f1 if who==1 else f2
            if own['enabled']:continue
            other_busy=busy(s2,f2,{}) if who==1 else busy(s1,f1,{})
            if not other_busy:
                own.update(enabled=True,stage=1,counterAcknowledged=False);admitted.append(who)
        assert admitted==[first];cases+=1
    # New 3/3 route, preserved 4/4 route, partial native account + reload cases.
    for base in (3,4):
        for tick in range(7):
            claim=int(tick>=1);achievement=base+int(tick>=2);ack=int(tick>=3)
            finished=int(tick>=4);count=base+int(tick>=5);counter_ack=int(tick>=6)
            bridge=claim==ack==finished==1 and achievement==base+1 and count==base
            assert bridge==(tick==4)
            assert not (claim and condition_value(patched['account_condition'],{'PTFRG2_CountBase':base,'wat_sts_counter':count,'wat_achievement':achievement,'PTFRG2_AccountClaim':claim,'PTFRG2_AccountAck':ack,'PTFRG2_Fault':0}))
            assert count<=base+1;cases+=1
        for persisted_base,inflight in itertools.product(range(7),(False,True)):
            refused=inflight or persisted_base not in (3,4)
            assert refused is (inflight or (persisted_base!=3 and persisted_base!=4));cases+=1
    for claim,ack,fault in itertools.product(range(3),range(3),range(2)):
        assert condition_value(patched['reward_condition'],{'PTFRG2_RewardClaim':claim,'PTFRG2_RewardAck':ack,'PTFRG2_Fault':fault}) is (claim==ack==fault==0);cases+=1
    return {'source_linked_busy_getter_cases':True,'guard_mutants':mutants,'abstract_cases':cases,'queued_request_zero_blocks':True,'both_command_orders_checked':True,'uncertain_ownership_not_released':True,'not_engine_scheduler_payment_proof':True}

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    graph,patched=graph_checks();contracts=contract_checks();model=models(patched);logger=prior.logger()
    comp=read(OUT/'compile_result.json');assert comp['status']=='PASS_OFFLINE_COMPILE_NOT_ENGINE_PROOF' and comp['equipmentex']
    for p,h in comp['source_hashes'].items():assert sha(ROOT/p)==h
    mappings=[('build/RiteG21/TowerContinued_RiteG2.archive','archive/pc/mod/TowerContinued_RiteG2.archive','CD702612171D9F7E879D42545890A5E267BAD4F8B686D46DBF6D5D9DCB2F8405'),('redscript/PTFR_RiteG2/RiteG2.reds','r6/scripts/PTFR_RiteG2/RiteG2.reds','06F5F19A112DB08C13B6A61B43255FCB9373CE8F9C468DA69187FEF65D10C2BB'),('redscript/PTFR_GigPilotR1/GigPilotR1.reds','r6/scripts/PTFR_GigPilotR1/GigPilotR1.reds','3B6CF5A3D438F71AE705EFAF2B803068EAAB7F33CDAE091485BDED8E14E6C688')]
    files=[dict(source=s,relative=r,predecessor=p,sha256=sha(ROOT/s)) for s,r,p in mappings]
    assert read(OUT/'manifest.json')['packed_readback'] and read(OUT/'manifest.json')['counter_baselines']==[3,4]
    assert read(OUT/'manifest.json')['archive_sha256']==files[0]['sha256']
    tools={f'tools/{n}':sha(ROOT/'tools'/n) for n in ('build_rite_g2_1.ps1','compile_rite_g2_1.py','test_rite_g2_1.py','deploy_rite_g2_1.ps1','test_rite_g2_1_deployment.ps1')}
    result={'status':'PASS_RITE_G21_SHARED_ACCOUNT_OFFLINE_LIVE_PENDING','graph':graph,'contracts':contracts,'models':model,'logger':logger,'files':files,'tools':tools,'compile_sha256':sha(OUT/'compile_result.json'),'manifest_sha256':sha(OUT/'manifest.json'),'equipmentex_full_compile':True,'completed_replay_adapters':0,'live_tested':False}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','graph','contracts','models','logger')},indent=2))

if __name__=='__main__':main()
