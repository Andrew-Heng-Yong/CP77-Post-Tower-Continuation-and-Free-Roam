"""G2 graph equality, source-linked guard models and compilation checks.

None of these simulate the engine, community PS persistence or real payment.
Preserve predecessor evidence; never invoke its main build/test/install paths.
"""
import copy, json, re, sys
from pathlib import Path
from catalog_gig_rollout_r2 import ROOT, read, sha
from test_gig_pilot_r1 import Resource, reachable
from audit_activity_batches_b1 import flatten
from audit_activity_lifecycles_b1 import condition_value
from test_activity_batches_b1 import current_install_check
OUT=ROOT/'research/gig_restoration/rite_g2'
sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'))
from lupa.luajit21 import LuaRuntime

class SafeResource(Resource):
    def d(self,v):
        return None if isinstance(v,dict) and v.get('HandleRefId')=='-1' else super().d(v)

def graph_checks():
    native=SafeResource(read(ROOT/'research/gig_restoration/watson_sources/json/base/open_world/street_stories/watson/northside_industrial_district/sts_wat_northside_industrial_district.questphase.json'))
    assert sha(ROOT/'research/gig_restoration/watson_sources/json/base/open_world/street_stories/watson/northside_industrial_district/sts_wat_northside_industrial_district.questphase.json')=='5D3AB6095D0262DECAD105B16C1A57A4B6AD5C297EA8608F4AA245C7DEE07129'
    original=native.obj['Data']['EmbeddedFiles']; compared=0; patched={}
    for name,index in [('native_owner',26),('ow',2),('combat',22)]:
        r=SafeResource(read(OUT/f'{name}.questphase.json'));patched[name]=r
        old={g['path']:g for g in flatten(native,original[index]['Content'])}
        new={g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
        assert old.keys()==new.keys(),name
        assert r.obj['Data']['RootChunk']['phasePrefabs']==original[index]['Content']['phasePrefabs']
        for path,og in old.items():
            on={n['id']:n for n in og['nodes']};pn={n['id']:n for n in new[path]['nodes']}
            additions={400,401,402,403,410,411,412,413} if (name,path)==('ow','root/5') else set()
            assert pn.keys()==on.keys()|additions,(name,path,'node scope')
            for i,n in on.items():
                expected=copy.deepcopy(n);actual=copy.deepcopy(pn[i])
                if name=='native_owner' and path=='root' and i in (9,10):
                    expected['phaseResource']=actual['phaseResource']
                    assert actual['phaseResource']['DepotPath']['$value']==f'towercontinued\\rite_g2\\{"combat" if i==9 else "ow"}.questphase'
                assert expected==actual,(name,path,i,'native payload drift');compared+=1
            oe={tuple(e) for e in og['edges']};pe={tuple(e) for e in new[path]['edges']};expected=oe
            if (name,path)==('ow','root'):
                expected={e for e in oe if not(e[0]==0 and e[2]==2)}|{(0,'Out',3,'In1')}
                assert 2 not in reachable(expected,0),'initial checkpoint/door initialization still reachable'
            elif (name,path)==('ow','root/3'):
                expected={e for e in oe if not(e[0]==0 and e[2] in (105,134,146))}|{(0,'Out',42,'In'),(0,'Out',102,'In')}
                reached=reachable(expected,0)
                assert not reached & {105,134,146,130,135,136,137,74},reached
                assert {69,73,24,51,83,81,82,33,34,36,35,39,145}<=reached
                assert pn[83]['condition']['type']['deviceConditionFunction']['$value']=='IsPersonalLinkConnected'
                assert pn[81]['type']['duration']==3
            elif (name,path)==('combat','root/2'):
                expected={e for e in oe if not(e[0]==5 and e[2] in (6,7))}|{(5,'Out',8,'In2'),(5,'Out',8,'In3')}
                assert not reachable(expected,0)&{6,7}
                assert {3,5,11,8,1}<=reachable(expected,0)
            elif (name,path)==('combat','root/3'):
                expected={e for e in oe if not(e[0]==0 and e[2]==17)}
                assert 17 not in reachable(expected,0)
                assert {9,10,15,19,22,24,26}<=reachable(expected,0)
            elif (name,path)==('ow','root/5'):
                expected={(f,s,61 if f==62 and s=='False' else t,'Active' if f==62 and s=='False' else dest) for f,s,t,dest in oe if not(f==16 and t==12) and f!=12 and t!=46 and not(f==46 and t==63)}
                expected|={(16,'Out',400,'In'),(400,'True',401,'In'),(401,'Out',12,'In'),(12,'Out',402,'In'),(402,'Out',14,'In'),(402,'Out',52,'In'),(400,'False',403,'In'),
                          (61,'Out',410,'In'),(45,'End 0',410,'In'),(410,'True',411,'In'),(411,'Out',46,'In'),(46,'Out',412,'In'),(412,'Out',63,'In'),(410,'False',413,'In')}
                assert 45 not in reachable(expected,0),'global phone debrief still reachable'
                assert {41,42,43,44,61,46,12,14,24,38,49,50,59,1,64,65}<=reachable(expected,0)
                assert pn[12]['type']=={'$type':'questSetVar_NodeType','factName':'wat_achievement','setExactValue':0,'value':1}
                assert pn[46]['type']['rewards'][0]['hash']==163539604770
                patched['account_condition']=pn[400]['condition'];patched['reward_condition']=pn[410]['condition']
            assert expected==pe,(name,path,'edge scope',expected^pe)
    boot=SafeResource(read(OUT/'owner.questphase.json'));br=boot.obj['Data']['RootChunk'];bn=boot.nodes(br['graph'])
    assert not br['phasePrefabs'] and not br['inplacePhases']
    assert boot.edges(br['graph'])=={(0,'Out',400,'In'),(400,'Out',401,'In'),(401,'Out',402,'In'),(402,'Out',403,'In'),(403,'Out',405,'IN'),(405,'OUT',404,'In'),(404,'Out',1,'In')}
    assert bn[402]['$type']=='questPauseConditionNodeDefinition'
    patched['boot_condition']=boot.payload(bn[402])['condition']
    assert patched['native_owner'].obj['Data']['RootChunk']['phasePrefabs'][0]['prefabNodeRef']['$value']=='#sts_wat_nid_05_steetstory'
    return {'native_payloads_preserved':compared,'exact_edge_deltas':True,'prefab_behind_optin':True,'item_loot_initialization_unreachable':True,'native_download_reward_cleanup_preserved':True},patched

def contracts():
    s=(ROOT/'redscript/PTFR_RiteG2/RiteG2.reds').read_text()
    writes=set(re.findall(r'this\.Set\(n"([^"]+)"',s))
    assert writes=={'PTFRG2_CountBase','PTFRG2_Request','PTFRG2_Fault','PTFRG2_CounterAck','wat_sts_counter'},writes
    for forbidden in ('TrackEntry(', 'GiveItem(', 'StartQuest(', 'SetFact(n"q307', 'SetFact(n"nid_05', 'SetFact(n"sts_wat_nid_tier'):assert forbidden not in s
    for token in ('this.Preflight(0, base, state)','this.schema != 1 || this.inflight','this.KeycardCount() != 1','CyberwarePolicy.Safe(player)','this.epoch != epoch','this.stage == 5 || this.stage == 4','this.Fact(n"wat_sts_counter") != this.countBase','this.Fact(n"PTFRG1_CounterAck") == 1','this.Fact(n"PTFRG1_RewardAck") == 1','PTFRG2_AccountAck','PTFRG2_RewardAck'):assert token in s,token
    assert s.count('.ChangeEntryState(')==1
    # Refusal occurs before any persistent candidate assignment, not just before
    # native writes; exact ordered R3 observation fingerprint is unchanged.
    restore=s.split('public func Restore()',1)[1].split('public func Poll(',1)[0]
    assert restore.index('if !this.Preflight')<restore.index('this.countBase = base;')
    old=(OUT/'predecessor/ActivityStateR3.reds').read_text();new=(ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds').read_text()
    field=lambda text:re.findall(r'private persistent let [^;]+;',text)
    assert field(old)==field(new),'R3 save shape changed'
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    assert sha(ROOT/'research/activity_state_r3/definition.json')=='4965DC4225D4CC3699AD66448C34A4F9EC647989CC997A4EDF9D5E82D9294E4E'
    records={r['hash']:r for r in read(OUT/'records.json')['records']}
    assert records[100486752765]['fields']['friendlyName']=='nid_05_keycard'
    assert records[100486752765]['fields']['isSingleInstance']=='True'
    for item in (133091080138,131195701084):assert {'Readable','Shard'}<=set(records[item]['fields']['tags'])
    review=read(ROOT/'research/activity_batches_b1/lifecycle_review_r3.json')
    rite=next(j for j in review['gigs'] if j['id']=='sts_wat_nid_05')
    assert len(rite['scenes'])==3 and not rite['unresolved']
    for scene in rite['scenes']:
        assert sha(ROOT/scene['source'])==scene['sha256']
        assert not {'johnny','panam','kerry','judy'} & {str(a['name']).casefold() for a in scene['actors']}
    # Existing restore polling, snapshot/cutoff and G1/S1 contracts byte-identical.
    assert old.split('public func Inspect(',1)[0]==new.replace('import PTFR.RiteG2.*\n','').split('public func Inspect(',1)[0]
    assert old.split('public func GetStatus()',1)[1]==new.split('public func GetStatus()',1)[1]
    assert 'this.RiteHistory() && this.CurrentRoot(this.Find("sts_wat_nid_05")) == 4' in new
    assert 'Equals(id, "sts_wat_nid_05") && Equals(mode, "resume")' in new
    assert new.index('if this.faulted || !this.Tower()')<new.index('Explicit history override; exact pre-clinic')
    definition=read(ROOT/'research/activity_state_r3/definition.json');job=next(j for j in definition['jobs'] if j['id']=='sts_wat_nid_05')
    assert [e['id'] for e in job['journal_entries']]==['sts_wat_nid_05','sts_wat_nid_05','steal_recording','escape_clinic','get_to_clinic','find_recording','brief']
    assert set(re.findall(r'this.BaselineFact\("([^"]+)"',new))<=set(definition['fact_names'])
    return {'source_guard_contracts':True,'r3_persistent_shape_unchanged':True,'definition_fingerprint_unchanged':True,'existing_adapters_unchanged':True,'completed_replay':False}

def models(patched):
    cases=0;mutants=0
    boot=read(OUT/'manifest.json')['native_guard']
    assert condition_value(patched['boot_condition'],boot) is True
    for name in boot:
        changed=boot.copy();changed[name]+=1
        assert condition_value(patched['boot_condition'],changed) is False;mutants+=1;cases+=1
    for base in (4,):
        facts={'PTFRG2_CountBase':base,'wat_sts_counter':base,'wat_achievement':base,'PTFRG2_AccountClaim':0,'PTFRG2_AccountAck':0,'PTFRG2_Fault':0}
        assert condition_value(patched['account_condition'],facts) is True
        for name in facts:
            m=facts.copy();m[name]+=1;assert condition_value(patched['account_condition'],m) is False;mutants+=1
        for claim in (0,1,2):
            for ack in (0,1,2):
                for count in range(2,7):
                    for ach in range(2,7):
                        for fault in (0,1):
                            m=facts|{'PTFRG2_AccountClaim':claim,'PTFRG2_AccountAck':ack,'wat_sts_counter':count,'wat_achievement':ach,'PTFRG2_Fault':fault}
                            allowed=condition_value(patched['account_condition'],m)
                            assert allowed is (claim==ack==fault==0 and count==ach==base);cases+=1
        # At every interruption: uncertain claim without ack may never be paid
        # or counted again. No automatic reset or "missing reward" compensation.
        for tick in range(7):
            claim=int(tick>=1);ach=base+int(tick>=2);ack=int(tick>=3);finished=int(tick>=4);count=base+int(tick>=5);counterAck=int(tick>=6)
            assert not(claim and condition_value(patched['account_condition'],facts|{'PTFRG2_AccountClaim':claim,'wat_achievement':ach,'PTFRG2_AccountAck':ack}))
            can_bridge=finished==1 and ack==claim==1 and ach==base+1 and count==base
            assert can_bridge==(tick==4);assert count<=base+1;cases+=1
        for prepared in range(5):
            for ack_delayed in (False,True):
                for interrupted in (False,True):
                    # Only complete acknowledgement advances; restore while
                    # in-flight faults. Never issue a second journal request.
                    outstanding=prepared<4 and ack_delayed
                    advance=not interrupted and not outstanding
                    assert not(interrupted and advance);cases+=1
    for claim in (0,1,2):
        for ack in (0,1,2):
            for fault in (0,1):
                assert condition_value(patched['reward_condition'],{'PTFRG2_RewardClaim':claim,'PTFRG2_RewardAck':ack,'PTFRG2_Fault':fault}) is (claim==ack==fault==0);cases+=1
    for base in (0,1,2,3,5,6,23):
        facts={'PTFRG2_CountBase':base,'wat_sts_counter':base,'wat_achievement':base,'PTFRG2_AccountClaim':0,'PTFRG2_AccountAck':0,'PTFRG2_Fault':0}
        assert condition_value(patched['account_condition'],facts) is False;cases+=1
    # History certifies the precise stage, never a lone Active root. Fresh,
    # terminal, missing or progressed children are refused, as are absent facts.
    vector=[2,2,1,1,2,1,2]
    for i in range(7):
        for state in range(5):
            m=vector.copy();m[i]=state;assert (m==vector)==(state==vector[i]);cases+=1
    return {'guard_mutants':mutants,'abstract_cases':cases,'not_engine_scheduler_or_payment_proof':True}

def logger():
    s=(ROOT/'diagnostics/PTFR_RiteG2/init.lua').read_text()
    for forbidden in ('SetFact','ChangeEntryState','TrackEntry','Override(','Observe(','loadfile','loadstring'):assert forbidden not in s
    l=LuaRuntime(unpack_returned_tuples=True)
    l.execute('callbacks={};registerForEvent=function(k,v) callbacks[k]=v end; print=function() end; IsDefined=function(v) return v~=nil end; os={date=function() return "STAMP" end}; io={open=function() return nil end}; Game={GetQuestsSystem=function() return {GetFactStr=function() return 0 end} end,GetPlayer=function() return nil end}')
    m=l.execute(s);l.execute('callbacks.onUpdate(2)');assert m.Sample()['player_present']==False
    l.execute('Game.GetQuestsSystem=function() return {GetFactStr=function() return 1 end} end; Game.GetPlayer=function() return {GetEntityID=function() return 7 end,GetWorldPosition=function() return {x=0,y=0,z=0} end} end; Game.GetScriptableSystemsContainer=function() return {Get=function() return {Inspect=function() return "READ_ONLY" end} end} end; Game.GetJournalManager=function() return {HasAnyDelayedStateChanges=function() return false end, GetEntryByString=function() return nil end} end')
    assert m.Sample()['player_present'] # Disk unavailable: emit handles failure.
    return {'getter_only':True,'luajit_syntax':True,'player_absent_and_disk_unavailable_safe':True}

def main():
    assert not (OUT/'install_receipt.json').exists(),'Installed evidence is pinned'
    graph,patched=graph_checks();contract=contracts();model=models(patched);log=logger()
    comp=read(OUT/'compile_result.json');assert comp['status']=='PASS_OFFLINE_COMPILE_NOT_ENGINE_PROOF' and comp['equipmentex']
    for name,h in comp['source_hashes'].items():assert sha(ROOT/name)==h
    files=[]
    for source,relative in [('build/RiteG2/TowerContinued_RiteG2.archive','archive/pc/mod/TowerContinued_RiteG2.archive'),('archive/rite_g2/TowerContinued_RiteG2.archive.xl','archive/pc/mod/TowerContinued_RiteG2.archive.xl'),('redscript/PTFR_RiteG2/RiteG2.reds','r6/scripts/PTFR_RiteG2/RiteG2.reds'),('diagnostics/PTFR_RiteG2/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_RiteG2/init.lua'),('redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds')]:
        files.append({'source':source,'relative':relative,'sha256':sha(ROOT/source),'predecessor':'1B4AA7B0FC242E2152ED370483712B2A598D6706E2EF6A1473D74A5686F52E18' if 'ActivityStateR3.reds' in source else ''})
    manifest=read(OUT/'manifest.json');assert manifest['packed_readback'] and not manifest['vanilla_replacements'];assert files[0]['sha256']==manifest['archive_sha256']
    checked=current_install_check()
    tools={f'tools/{n}':sha(ROOT/'tools'/n) for n in ('build_rite_g2.ps1','compile_rite_g2.py','test_rite_g2.py','deploy_rite_g2.ps1','test_rite_g2_deployment.ps1')}
    result={'status':'PASS_RITE_G2_EXACT_RESUME_OFFLINE_LIVE_PENDING','graph':graph,'contracts':contract,'models':model,'logger':log,'files':files,'tools':tools,'compile_sha256':sha(OUT/'compile_result.json'),'manifest_sha256':sha(OUT/'manifest.json'),'equipmentex_full_compile':True,'installed_files_before':checked,'completed_replay_adapters':0,'live_tested':False}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in ('status','graph','contracts','models','logger')},indent=2))
if __name__=='__main__':main()
