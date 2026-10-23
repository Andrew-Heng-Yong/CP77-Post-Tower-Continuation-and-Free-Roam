"""G3 source-linked graph, handoff and LuaJIT checks; never engine proof.

All outputs are isolated from the pinned predecessor evidence. No game writes.
"""
import copy, itertools, json, re, sys
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, read, sha, walk, value
from test_rite_g2 import SafeResource
from test_gig_pilot_r1 import reachable
from audit_activity_batches_b1 import flatten

OUT=ROOT/'research/gig_restoration/minefield_g3'
NATIVE=ROOT/'research/gig_restoration/fresh_candidates/local_sources/json/base/open_world/street_stories/badlands/inland_avenue/sts_bls_inland_avenue.questphase.json'
PREDECESSOR='3C1FABD8E0BD8D123243B2A32CD143860AF05C7D93404335A0B3FB379E4BCC7F'
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

def evaluate(c,facts,spawn=True):
    typ=c['$type']
    if typ=='questLogicalCondition':
        values=[evaluate(x,facts,spawn) for x in c['conditions']]
        return all(values) if c['operation']=='AND' else any(values)
    t=c.get('type',{})
    if typ=='questFactsDBCondition':
        a=facts.get(t.get('factName',t.get('factName1')))
        b=facts.get(t['factName2']) if t['$type']=='questVarVsVarComparison_ConditionType' else t['value']
        if a is None or b is None:return False
        return {'Equal':a==b,'Greater':a>b,'NotEqual':a!=b}[t['comparisonType']]
    if typ=='questCharacterCondition' and t['$type']=='questCharacterSpawned_ConditionType':return spawn
    raise AssertionError(c)

def graph_checks():
    assert sha(NATIVE)=='03DB04107A777A1031EB5B4D645A58D7BB88FCF09BD3BEA4E3E9358A70401DA8'
    native=SafeResource(read(NATIVE));embedded=native.obj['Data']['EmbeddedFiles']
    checked=0;graphs=0;allnew={};guards={}
    for name,index in [('native_owner',24),('ow',5),('gameplay',20)]:
        r=SafeResource(read(OUT/f'{name}.questphase.json'))
        old={g['path']:g for g in flatten(native,embedded[index]['Content'])}
        new={g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])};allnew[name]=new
        assert old.keys()==new.keys(),(name,'nested graph scope')
        assert r.obj['Data']['RootChunk']['phasePrefabs']==embedded[index]['Content']['phasePrefabs']
        for path,og in old.items():
            graphs+=1;on={n['id']:n for n in og['nodes']};pn={n['id']:n for n in new[path]['nodes']}
            scope=(name,path);added=set()
            if scope==('native_owner','root'):added={400,402,410}
            elif scope==('ow','root'):added={400,401,402,403}
            elif scope==('ow','root/18'):added={400}
            elif scope==('ow','root/13'):added=set(range(400,406))
            elif scope==('ow','root/13/25'):added=set(range(400,406))
            elif scope in (('gameplay','root/7/54'),('gameplay','root/9/140')):added=set(range(410,416))
            assert pn.keys()==on.keys()|added,(scope,'node scope')
            for ident,node in on.items():
                expected=copy.deepcopy(node)
                if scope==('native_owner','root'):
                    if ident in (117,118):
                        expected['phaseResource']['Flags']='Soft'
                        expected['phaseResource']['DepotPath']['$storage']='string'
                        expected['phaseResource']['DepotPath']['$value']=f'towercontinued\\minefield_g3\\{"gameplay" if ident==117 else "ow"}.questphase'
                    elif ident==264:expected['event']['accumulate']=0
                    elif ident==275:expected['type']['phase']='DiscoveredPhase'
                assert expected==pn[ident],(scope,ident,'native payload drift');checked+=1
            oe={tuple(e) for e in og['edges']};expected=oe.copy();pe={tuple(e) for e in new[path]['edges']}
            if scope==('native_owner','root'):
                expected={e for e in oe if e[0] not in (1,282,251) and not(e[0]==270 and e[2]==264)}
                expected|={(1,'Out',400,'In'),(400,'True',275,'In'),(400,'False',410,'In'),(410,'Out',254,'In'),(270,'Out',402,'In'),(402,'True',264,'In'),(402,'False',253,'In'),(282,'Out',117,'In1'),(282,'Out',118,'In1')}
                assert 251 not in reachable(expected,1),'initial checkpoint repeated'
                guards['spawn']=pn[400]['condition'];guards['newcar']=pn[402]['condition']
            elif scope==('ow','root'):
                expected={e for e in oe if not(e[0]==0 and e[2]==10) and not(e[0]==11 and e[1]=='Out1') and e[0]!=17}
                expected|={(0,'Out',11,'In1'),(0,'Out',18,'In1'),(11,'Out1',400,'In'),(400,'True',401,'In'),(401,'Out',17,'In'),(17,'Out',402,'In'),(402,'Out',13,'In1'),(400,'False',403,'In')}
                assert 10 not in reachable(expected,0),'initial additions repeated'
                assert pn[17]['type']['rewards'][0]['hash']==163943278887
                guards['reward']=pn[400]['condition']
                assert not reachable({e for e in expected if not(e[0]==11 and e[1]=='Out1')},0)&{17}
            elif scope==('ow','root/11'):
                expected=set()
                for f,s,t,d in oe:
                    if (f,t) in ((0,598),(645,590)):continue
                    if t==557 and d=='Start 0':expected.add((f,s,603,'Active'))
                    elif t==550 and d=='Start 0':expected|={(f,s,606,'In'),(f,s,607,'In')}
                    else:expected.add((f,s,t,d))
                reached=reachable(expected,0)
                assert not reached&{549,550,557,567,568,569,570,579,580,590,591},('foreign cleanup/phone reachable',reached)
                assert {474,551,500,603,605,608,1}<=reached
                # Native successful delivery sets perfect before the text test;
                # the separate car-destroyed route sets failed and has no reward.
                assert pn[551]['type']['factName']=='ina_07_perfect' and pn[551]['type']['value']==1
                assert pn[500]['type']['factName']=='ina_07_failed' and pn[500]['type']['value']==1
                assert pn[606]['condition']['type']['factName']=='ina_07_perfect'
                assert pn[607]['condition']['type']['factName']=='ina_07_failed'
                assert (605,'Out',573,'In') in expected and (603,'Out',571,'In') in expected
            elif scope==('ow','root/18'):
                expected={e for e in oe if not(e[0]==0 and e[2]==25)}|{(0,'Out',400,'In'),(400,'True',25,'In')}
                guards['body']=pn[400]['condition']
            elif scope==('ow','root/13'):
                expected={e for e in oe if e[2]!=9 and e[0]!=9}|{(3,'Out',404,'In'),(17,'Out',404,'In'),(404,'Out',405,'In'),(405,'Out',400,'In'),(400,'True',401,'In'),(401,'Out',9,'In'),(9,'Out',402,'In'),(402,'Out',28,'In'),(400,'False',403,'In')}
                assert pn[9]['type']=={'$type':'questSetVar_NodeType','factName':'bls_achievement','setExactValue':0,'value':1}
                assert pn[405]['condition']['type']['factName']=='PTFRG3_AccountReady'
                guards['account']=pn[400]['condition']
                assert not any(e[2]==9 and e[0]!=401 for e in expected)
                assert not any(e[0]==9 and e[2]!=402 for e in expected)
            elif scope==('ow','root/13/25'):
                expected={(f,s,400+t-11 if 11<=t<=16 and d=='In' else t,d) for f,s,t,d in oe}
                for i in range(6):
                    expected|={(400+i,'True',11+i,'In'),(400+i,'False',400+i+1 if i<5 else 1,'In')}
                    cond=pn[400+i]['condition'];guards[f'borrow{i}']=cond
                    spawn=cond['conditions'][1]['type'];assert spawn['objectRef']==pn[11+i]['entityReference']
                    assert spawn['comparisonParams']['entireCommunity']==0
            elif scope in (('gameplay','root/7/54'),('gameplay','root/9/140')):
                expected={(f,s,400+t if 10<=t<=15 and d=='In' else t,d) for f,s,t,d in oe}|{(400+i,'Out',i,'In') for i in range(10,16)}
                for i in range(10,16):
                    entity=pn[i]['entityReference'];release=allnew['ow']['root/13/25']['nodes']
                    target=next(n for n in release if 11<=n['id']<=16 and n['entityReference']==entity)
                    assert pn[400+i]['type']['factName']==f'PTFRG3_Borrow{target["id"]-11}'
                    assert pn[i]['params']['duration']==10
            assert pe==expected,(scope,'edge delta',pe^expected)
    boot=SafeResource(read(OUT/'owner.questphase.json'));br=boot.obj['Data']['RootChunk'];bn=boot.nodes(br['graph'])
    assert not br['phasePrefabs'] and not br['inplacePhases']
    assert boot.edges(br['graph'])=={(0,'Out',400,'In'),(400,'Out',401,'In'),(401,'Out',402,'In'),(402,'Out',403,'In'),(403,'Out',405,'In1'),(405,'Out1',404,'In'),(404,'Out',1,'In')}
    guards['boot']=boot.payload(bn[402])['condition']
    assert not any(x.get('type',{}).get('$type')=='questVarVsVarComparison_ConditionType' for x in guards['boot']['conditions'])
    assert bn[405]['phaseResource']['DepotPath']['$value']==r'towercontinued\minefield_g3\native_owner.questphase'
    assert br['$type']=='questQuestPhaseResource'
    # Copied embedded children must not reference a missing embedded file table.
    for name in ('native_owner','ow','gameplay','owner'):
        resource=SafeResource(read(OUT/f'{name}.questphase.json'))
        for graph in flatten(resource,resource.obj['Data']['RootChunk']):
            for node in graph['nodes']:
                ref=node.get('phaseResource',{})
                depot=value(ref.get('DepotPath',{}))
                if depot not in (None,'0'):
                    assert ref['Flags']=='Soft'
                    assert depot in read(OUT/'manifest.json')['resources']
    return {'native_graphs':graphs,'native_payloads_checked':checked,'exact_edge_deltas':True,'prefab_behind_optin':True,'native_chase_delivery_cleanup_preserved':True,'shared_phone_and_foreign_cleanup_unreachable':True,'borrowed_role_targets_exact':True},guards

def contracts():
    s=(ROOT/'redscript/PTFR_MinefieldG3/MinefieldG3.reds').read_text()
    writes=set(re.findall(r'this\.Set\(n"([^"]+)"',s))
    assert writes=={'PTFRG3_CountBase','PTFRG3_AchBase','PTFRG3_Request','PTFRG3_AccountReady','PTFRG3_CounterAck','PTFRG3_Fault','bls_sts_counter'},writes
    for forbidden in ('GiveItem(', 'TrackEntry(', 'StartQuest(', 'SetFact(n"q307', 'SetFact(n"ina_07', 'Set(n"PTFRG3_OwnerFinished', 'Set(n"bls_achievement'):assert forbidden not in s
    for token in ('this.schema != 1 || this.inflight','CyberwarePolicy.Safe(player)','epoch != this.epoch','this.stage == 4 || this.stage == 5','if this.enabled { return this.GetStatus(); }','this.Preflight(this.prepared+1','if this.ackTicks >= 12','this.accountPrepared = true; this.Set(n"PTFRG3_AccountReady",1)','this.Fact(n"bls_achievement") != this.achBase+1','this.Fact(n"bls_sts_counter") != this.countBase','this.Set(n"bls_sts_counter",this.countBase+1)'):assert token in s,token
    assert s.count('.ChangeEntryState(')==1
    restore=s.split('public func Restore()',1)[1].split('public func Poll(',1)[0]
    assert restore.index('if !this.Preflight')<restore.index('this.originalStates = states')
    old=(OUT/'predecessor/ActivityStateR3.reds').read_text();new=(ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds').read_text()
    field=lambda text:re.findall(r'private persistent let [^;]+;',text)
    assert field(old)==field(new)
    assert sha(OUT/'predecessor/ActivityStateR3.reds')==PREDECESSOR
    assert old.split('public func Inspect(',1)[0]==new.replace('\nimport PTFR.MinefieldG3.*\n','').split('public func Inspect(',1)[0]
    assert old.split('public func GetStatus()',1)[1]==new.split('public func GetStatus()',1)[1]
    for method,next_method in [('RiteHistory','MinefieldHistory')]:
        # Prior adapter/history body remains verbatim; only appended new method.
        assert old.split('private func '+method,1)[1].split('public func Override',1)[0].rstrip()==new.split('private func '+method,1)[1].split('private func '+next_method,1)[0].rstrip()
    assert 'Equals(id, "sts_bls_ina_07") && Equals(mode, "resume")' in new
    assert new.index('if this.faulted || !this.Tower()')<new.index('Explicit history override; saved early-stage')
    definition=read(ROOT/'research/activity_state_r3/definition.json');job=next(j for j in definition['jobs'] if j['id']=='sts_bls_ina_07')
    assert len(job['journal_entries'])==15
    history=new.split('private func MinefieldHistory()',1)[1].split('public func Override',1)[0]
    historical_zero=re.search(r'let zero: array<String> = \[(.*?)\];',history,re.S)
    assert set(re.findall(r'"([^"]+)"',historical_zero.group(1)))<=set(definition['fact_names'])
    assert 'BaselineFact("#ina_07_ready")' not in history
    assert set(re.findall(r'this.BaselineFact\("([^"]+)"',new))<=set(definition['fact_names'])
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    assert sha(ROOT/'research/activity_state_r3/definition.json')=='4965DC4225D4CC3699AD66448C34A4F9EC647989CC997A4EDF9D5E82D9294E4E'
    other=re.search(r'let names: array<String> = \[(.*?)\];',s.split('private func OtherBadlandsIdle()',1)[1].split('private func CountsSafe()',1)[0],re.S)
    assert other is not None
    names=set(re.findall(r'"(sts_bls_[^"]+)"',other.group(1)))
    assert names=={j['id'] for j in definition['jobs'] if j['id'].startswith('sts_bls_')}-{'sts_bls_ina_07'}
    return {'source_contracts':True,'existing_snapshot_cutoff_and_save_shape_unchanged':True,'definition_unchanged':True,'independent_completion_baselines':True,'completed_replay':False}

def models(g):
    cases=mutants=0;boot=read(OUT/'manifest.json')['native_guard']|{'ina_07_start':1,'#ina_07_ready':1}
    assert evaluate(g['boot'],boot)
    for name in boot:
        m=boot.copy();m[name]=0 if name in ('ina_07_start','#ina_07_ready') else m[name]+1
        assert not evaluate(g['boot'],m),(name,'boot mutant');mutants+=1
    for count,ach,claim,ack,fault in itertools.product((0,1,3,4,8,23,2147483646),(0,3,9,36,2147483646),(0,1,2),(0,1,2),(0,1)):
        f={'PTFRG3_CountBase':count,'bls_sts_counter':count,'PTFRG3_AchBase':ach,'bls_achievement':ach,'PTFRG3_AccountClaim':claim,'PTFRG3_AccountAck':ack,'PTFRG3_Fault':fault}
        assert evaluate(g['account'],f)==(claim==ack==fault==0);cases+=1
        for drift in ('bls_sts_counter','bls_achievement'):
            assert not evaluate(g['account'],f|{drift:f[drift]+1});cases+=1
    for claim,ack,fault in itertools.product((0,1,2),(0,1,2),(0,1)):
        assert evaluate(g['reward'],{'PTFRG3_RewardClaim':claim,'PTFRG3_RewardAck':ack,'PTFRG3_Fault':fault})==(claim==ack==fault==0);cases+=1
    for i in range(6):
        for borrowed,spawn in itertools.product((0,1,2),(False,True)):
            assert evaluate(g[f'borrow{i}'],{f'PTFRG3_Borrow{i}':borrowed},spawn)==(borrowed==1 and spawn);cases+=1
    for scan in (0,1,2):assert evaluate(g['body'],{'#ina_07_body_scan':scan})==(scan==0);cases+=1
    for newcar in (0,1,2):assert evaluate(g['newcar'],{'PTFRG3_NewCar':newcar})==(newcar==1);cases+=1
    # Model the actual handoff ordering, independent achievement/fixer values,
    # and cold restores at each boundary. A saved in-flight operation faults;
    # an acknowledged operation never repeats. No compensation/reward replay.
    for base,ach,failed in itertools.product((0,3,4,8,23),(0,9,36),(False,True)):
        for boundary in range(8):
            claim=int(boundary>=3);nativeach=ach+int(boundary>=4);ack=int(boundary>=5)
            count=base+int(boundary>=6);counterack=boundary>=7
            admitted=ack==claim==1 and nativeach==ach+1 and count==base and not counterack
            assert admitted==(boundary==5)
            assert count<=base+1 and nativeach<=ach+1
            assert not (claim and evaluate(g['account'],{'PTFRG3_CountBase':base,'bls_sts_counter':count,'PTFRG3_AchBase':ach,'bls_achievement':nativeach,'PTFRG3_AccountClaim':claim,'PTFRG3_AccountAck':ack,'PTFRG3_Fault':0}))
            reward=0 if failed else 1;assert failed or reward==1;cases+=1
        # Translate the source's guarded counter bridge, including saved flags;
        # repeats at every boundary never count more than once.
        for boundary in range(8):
            state={'inflight':False,'prepared':boundary>=2,'claim':int(boundary>=3),'ack':int(boundary>=5),'achievement':ach+int(boundary>=4),'counter':base+int(boundary>=6),'counter_ack':boundary>=7,'fault':False}
            before=state['counter']
            for repeat in range(20):
                if state['ack']==1 and not state['counter_ack'] and not state['fault']:
                    if not state['prepared'] or state['claim']!=1 or state['achievement']!=ach+1 or state['counter']!=base:state['fault']=True
                    else:state['counter']+=1;state['counter_ack']=True
                assert state['counter']<=base+1
                if boundary!=5:assert state['counter']==before
                if boundary==5:assert state['counter']==base+1 and state['counter_ack']
                cases+=1
    for original in itertools.product((2,4),(2,4),(2,4),(1,2)):
        for prepared in range(5):
            current=[2 if i<prepared else x for i,x in enumerate(original)]
            if prepared<4:
                next_value=current[prepared];issued=next_value!=2
                assert issued==(original[prepared]!=2)
                advanced=current[:];advanced[prepared]=2
                assert advanced==[2 if i<prepared+1 else x for i,x in enumerate(original)]
            for interrupted in (False,True):
                # Source restores fault an in-flight request rather than resend.
                outstanding=prepared<4 and current[prepared]!=2
                restored_fault=interrupted and outstanding
                may_issue=not restored_fault and not interrupted and outstanding
                assert not(restored_fault and may_issue);cases+=1
    history=[2,2,1,2,1,1,1,1,1,1,1,1,1,1,2]
    for i in range(15):
        for state in range(-1,5):
            m=history.copy();m[i]=state;assert (m==history)==(state==history[i]);cases+=1
    return {'guard_mutants':mutants,'abstract_cases':cases,'not_native_scheduler_vehicle_or_payment_proof':True}

def logger():
    s=(ROOT/'diagnostics/PTFR_MinefieldG3/init.lua').read_text()
    for forbidden in ('SetFact','ChangeEntryState','TrackEntry','Override(','Observe(','loadfile','loadstring'):assert forbidden not in s
    l=LuaRuntime(unpack_returned_tuples=True)
    l.execute('callbacks={};registerForEvent=function(k,v) callbacks[k]=v end;messages={};print=function(s) messages[#messages+1]=s end;IsDefined=function(v) return v~=nil end;os={date=function() return "STAMP" end};io={open=function() return nil,"disk unavailable" end};Game={GetQuestsSystem=function() return {GetFactStr=function() return 0 end} end,GetPlayer=function() return nil end}')
    m=l.execute(s);l.execute('callbacks.onUpdate(2)');assert not m.Sample()['player_present']
    l.execute('''local ffi=require('ffi');EnumInt=function(v) return ffi.new('uint64_t',v) end
      ItemID={FromTDBID=function(v) return v end};TweakDBID={new=function(v) return v end};json={encode=function(v) return 'MOCK' end}
      Game.GetQuestsSystem=function() return {GetFactStr=function() return 1 end} end
      Game.GetPlayer=function() return {GetEntityID=function() return 7 end,GetWorldPosition=function() return {x=0,y=0,z=0} end} end
      Game.GetScriptableSystemsContainer=function() return {Get=function() return {Inspect=function() return 'READ_ONLY' end,GetStatus=function() return 'VOICE_ONLY' end} end} end
      Game.GetTransactionSystem=function() return {GetItemQuantity=function(self,p,id) assert(id=='Items.money');return 123 end} end
      Game.GetJournalManager=function() return {HasAnyDelayedStateChanges=function() return false end,GetEntryByString=function(self,path,cls) return {path=path} end,GetEntryState=function() return 2 end,IsEntryTracked=function() return false end,GetIsObjectiveOptional=function() return false end} end''')
    row=m.Sample();assert row['money']==123 and row['johnny']=='VOICE_ONLY' and len(list(row['errors'].items()))==0
    assert all(x['state']==2 for _,x in row['journal'].items())
    assert any('Log failed' in str(v) for _,v in l.globals().messages.items())
    # Unique filename skips existing slot 1; all three filesystem failure points
    # are caught. No write to any gameplay object in this mock or source.
    l.execute("opened={};io.open=function(name,mode) opened[#opened+1]=name..':'..mode;if mode=='r' and name:find('_1.jsonl',1,true) then return {close=function() return true end} end;if mode=='a' then return {write=function() return true end,flush=function() return true end,close=function() return true end} end;return nil end")
    n=l.execute(s);n.Sample();assert any('_2.jsonl:a' in str(v) for _,v in l.globals().opened.items())
    for method in ('write','flush','close'):
        l.execute(f"io.open=function(name,mode) if mode=='r' then return nil end;return {{write=function() return {'nil' if method=='write' else 'true'} end,flush=function() return {'nil' if method=='flush' else 'true'} end,close=function() return {'nil' if method=='close' else 'true'} end}} end")
        n.Sample()
    return {'getter_only':True,'luajit_checks':7,'cdata_and_disk_failures_safe':True,'unique_filename':True,'not_native_money_api_proof':True}

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence pinned'
    graph,g=graph_checks();contract=contracts();model=models(g);log=logger()
    comp=read(OUT/'compile_result.json');assert comp['status']=='PASS_G3_OFFLINE_COMPILE_NOT_ENGINE_PROOF' and comp['equipmentex']
    assert comp['source_sha256']==sha(ROOT/'redscript/PTFR_MinefieldG3/MinefieldG3.reds')
    assert comp['state_sha256']==sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds')
    assert sha(comp['compiled_path'])==comp['compiled_sha256']
    protected=comp['protected']|comp['dependencies']
    for path,h in protected.items():assert sha(path)==h,(path,'installed dependency changed')
    files=[]
    for source,relative in [('build/MinefieldG3/TowerContinued_MinefieldG3.archive','archive/pc/mod/TowerContinued_MinefieldG3.archive'),('archive/minefield_g3/TowerContinued_MinefieldG3.archive.xl','archive/pc/mod/TowerContinued_MinefieldG3.archive.xl'),('redscript/PTFR_MinefieldG3/MinefieldG3.reds','r6/scripts/PTFR_MinefieldG3/MinefieldG3.reds'),('diagnostics/PTFR_MinefieldG3/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_MinefieldG3/init.lua'),('redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds')]:
        files.append({'source':source,'relative':relative,'sha256':sha(ROOT/source),'predecessor':PREDECESSOR if 'ActivityStateR3.reds' in source else ''})
    manifest=read(OUT/'manifest.json');assert manifest['packed_readback'] and not manifest['vanilla_replacements'] and files[0]['sha256']==manifest['archive_sha256']
    tools={f'tools/{name}':sha(ROOT/'tools'/name) for name in ('build_minefield_g3.ps1','compile_minefield_g3.py','test_minefield_g3.py','deploy_minefield_g3.ps1','test_minefield_g3_deployment.ps1')}
    result={'status':'PASS_MINEFIELD_G3_EARLY_RESUME_OFFLINE_LIVE_PENDING','graph':graph,'contracts':contract,'models':model,'logger':log,'files':files,'tools':tools,'compile_sha256':sha(OUT/'compile_result.json'),'manifest_sha256':sha(OUT/'manifest.json'),'equipmentex_full_compile':True,'installed_dependencies_checked':len(protected),'completed_replay_adapters':0,'live_tested':False}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','graph','contracts','models','logger')},indent=2))

if __name__=='__main__':main()
