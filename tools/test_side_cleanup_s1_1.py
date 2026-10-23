"""Exact cleanup-only deltas and bounded fallback models; not engine proof."""
import itertools,json,math,re,sys
from catalog_gig_rollout_r2 import ROOT,read,sha,walk
from test_gig_pilot_r1 import Resource
OUT=ROOT/'research/side_job_cleanup_s1_1'

def graphs():
    old=Resource(read(ROOT/'research/side_job_pilot_s1/native_owner.questphase.json'))
    new=Resource(read(OUT/'native_owner.questphase.json'));manifest=read(OUT/'manifest.json');count=0
    def compare(og,ng,path):
        nonlocal count
        on=old.nodes(og);nn=new.nodes(ng);oe=old.edges(og);ne=new.edges(ng)
        if path=='root/4':
            assert set(nn)==set(on)|set(range(440,446))
            expected=oe-{(14,'Out1',1,'In')}|{(14,'Out1',445,'In'),(445,'Out',1,'In'),(16,'Out',440,'In'),(10,'Out',441,'In'),(15,'Out',442,'In'),(13,'Out',443,'In'),(3,'Out',444,'In')}
            assert ne==expected,(ne^expected)
            for i,f in enumerate(('PTFRS1_CleanupEntered','PTFRS1_CorpoDepartureAck','PTFRS1_CarsDepartureAck','PTFRS1_CorpoCleanupAck','PTFRS1_CarsCleanupAck','PTFRS1_CleanupJoined'),440):
                p=new.payload(nn[i]);assert p['$type']=='questFactsDBManagerNodeDefinition' and p['type']=={'$type':'questSetVar_NodeType','factName':f,'setExactValue':1,'value':1}
        else:assert set(nn)==set(on) and ne==oe,path
        for i,n in on.items():
            op=old.payload(n);np=new.payload(nn[i])
            if path=='root/4' and i in (10,15):
                cond=np.pop('condition');original=op.pop('condition')
                assert cond['$type']=='questLogicalCondition' and cond['operation']=='OR' and len(cond['conditions'])==2
                assert cond['conditions'][0]==original
                fallback=cond['conditions'][1];assert fallback['operation']=='AND'
                facts={x['type']['factName']:(x['type']['comparisonType'],x['type']['value']) for x in fallback['conditions'] if x['$type']=='questFactsDBCondition'}
                assert facts=={k:('Equal',v) for k,v in manifest['native_guard'].items()}
                outside=[x for x in fallback['conditions'] if x['$type']=='questTriggerCondition'];assert len(outside)==1
                assert outside[0]==old.payload(on[15])['condition']['conditions'][0]
                assert len(fallback['conditions'])==len(facts)+1
            assert np==op,(path,i)
            if n.get('phaseGraph'):compare(n['phaseGraph'],nn[i]['phaseGraph'],path+'/'+str(i))
            count+=1
    compare(old.obj['Data']['RootChunk']['graph'],new.obj['Data']['RootChunk']['graph'],'root')
    assert old.obj['Data']['RootChunk']['phasePrefabs']==new.obj['Data']['RootChunk']['phasePrefabs']
    for depot,digest in manifest['resources'].items():
        assert sha(ROOT/'build/SideJobCleanupS1_1/source'/depot.replace('\\','/'))==digest
        if depot!=manifest['changed_resource']:assert digest==manifest['predecessor_resources'][depot]
    assert sha(ROOT/'build/SideJobCleanupS1_1/TowerContinued_SideJobPilotS1.archive')==manifest['archive_sha256']
    return {'original_nodes_preserved':count,'changed_waits':2,'ack_nodes_added':6,'original_conditions_retained':True,'outside_trigger_retained':True,'reward_and_journal_graphs_unchanged':True,'other_resources_byte_identical':True}

def guards(source):
    anchors=('this.enabled && this.schema == 1 && this.stage == 3 && !this.inflight && this.Tower()',
      'this.Fact(n"PTFRS1_Request") == 1 && this.Fact(n"PTFRS1_Started") == 1',
      'this.Fact(n"PTFRS1_Fault") == 0 && this.Fact(n"PTFRS1_RewardReplayRefused") == 0',
      'this.Fact(n"PTFRS1_RewardClaim") == 1 && this.Fact(n"PTFRS1_RewardAck") == 1',
      'this.Fact(n"mq005_done") == 1 && this.Fact(n"mq005_police_left") == 1 && this.Fact(n"mq005_police_done") == 0',
      '"gameJournalQuest") == 3','"gameJournalQuestPhase") == 3',
      'mq005_main/02_check_on_corpo", "gameJournalQuestObjective") == 3',
      'mq005_main/03_talk_to_corpo", "gameJournalQuestObjective") == 3',
      'position.X > -10000000.0 && position.X < 10000000.0 && position.Y > -10000000.0 && position.Y < 10000000.0',
      'dx * dx + dy * dy >= 250000.0',
      'this.Fact(n"PTFRS1_CleanupDeparture") != 0',
      '!this.CompletedPoliceLeftRoute() || !CyberwarePolicy.Safe(player) || !this.FarFromEncounter(player)',
      'this.departureSamples = 0; return;','this.departureSamples < 5',
      'this.Fact(n"PTFRS1_OwnerFinished") == 1')
    for a in anchors:assert a in source,a
    assert set(re.findall(r'this.Set\(n"([^"]+)"',source))=={'PTFRS1_Request','PTFRS1_Fault','PTFRS1_CleanupDeparture'}
    for b in ('ChangeEntryState(', 'SetFactStr(', 'GiveReward', 'ExecuteNode(', 'StartQuest(', 'Set(n"mq005_', 'Set(n"PTFRS1_OwnerFinished"'):assert b not in source,b
    return anchors

def main():
    graph=graphs();source=(ROOT/'redscript/PTFR_SideJobPilotS1/SideJobPilotS1.reds').read_text();prior=(OUT/'predecessor/SideJobPilotS1.reds').read_text()
    anchors=guards(source);mutants=0
    for a in anchors:
        try:guards(source.replace(a,'MUTATED',1))
        except AssertionError:mutants+=1
        else:raise AssertionError(a)
    assert re.findall(r'private persistent let (\w+): ([^;]+);',prior)==re.findall(r'private persistent let (\w+): ([^;]+);',source)
    # Original admission and stage/reward logic remain intact outside the scoped
    # helper call. Counter is volatile and reset on restore, never a refund/replay.
    assert 'this.epoch += 1; this.warmup = 4; this.departureSamples = 0;' in source
    assert source.count('this.Set(n"PTFRS1_CleanupDeparture", 1)')==1
    cases=0
    for legacy,outside,route,far,safe in itertools.product((False,True),repeat=5):
        released=legacy or(route and far and safe and outside)
        if legacy:assert released
        if not legacy and not outside:assert not released
        if not route and not legacy:assert not released
        cases+=1
    def arm(samples):
        count=0;writes=0
        for valid in samples:
            if writes:continue
            count=count+1 if valid else 0
            if count>=5:writes+=1
        return writes
    for samples in itertools.product((False,True),repeat=12):
        expected=any(all(samples[i:i+5]) for i in range(8));assert arm(samples)==int(expected);cases+=1
    for distance in (0,149.99,150,499.99,500,500.01,757.3856,1000):
        assert (distance*distance>=250000)==(distance>=500);cases+=1
    for coord in (math.nan,math.inf,-math.inf,1e7,-1e7):assert not(-1e7<coord<1e7);cases+=1
    # Stage/save-local scope: departure recovery cannot arm before completion,
    # on a foreign/disabled save, during admission, or on an interrupted journal.
    def eligible(enabled,schema,stage,inflight,tower,owned,claim,ack,done,left,police,journals):
        return enabled and schema==1 and stage==3 and not inflight and tower and owned and claim==1 and ack==1 and done==1 and left==1 and police==0 and all(s==3 for s in journals)
    for enabled,schema,stage,inflight,tower in itertools.product((False,True),(0,1,2),range(6),(False,True),(False,True)):
        ok=eligible(enabled,schema,stage,inflight,tower,True,1,1,1,1,0,[3]*4)
        assert ok==(enabled and schema==1 and stage==3 and not inflight and tower);cases+=1
    for states in itertools.product(range(-1,5),repeat=4):
        assert eligible(True,1,3,False,True,True,1,1,1,1,0,states)==all(s==3 for s in states);cases+=1
    for owned,claim,ack,done,left,police in itertools.product((False,True),range(-1,3),range(-1,3),range(-1,3),range(-1,3),range(-1,3)):
        assert eligible(True,1,3,False,True,owned,claim,ack,done,left,police,[3]*4)==(owned and claim==ack==done==left==1 and police==0);cases+=1
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'));from lupa.luajit21 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('callbacks={};prints={};registerForEvent=function(k,v) callbacks[k]=v end; print=function(v) prints[#prints+1]=v end; IsDefined=function(v) return v~=nil end; os={date=function() return "STAMP" end}; io={open=function() return nil,"mock disk failure" end}; local ffi=require("ffi"); EnumInt=function(v) return ffi.new("uint64_t",v) end; json={encode=function(v) return "{}" end}; local e={}; local jm={GetEntryByString=function() return e end,GetEntryState=function() return 3 end,IsEntryTracked=function() return false end,GetIsObjectiveOptional=function() return false end,HasAnyDelayedStateChanges=function() return false end}; Game={GetQuestsSystem=function() return {GetFactStr=function() return 1 end} end,GetPlayer=function() return {GetEntityID=function() return "ID" end,GetWorldPosition=function() return {x=0,y=0,z=0} end} end,GetJournalManager=function() return jm end,GetScriptableSystemsContainer=function() return {Get=function() return {Inspect=function() return "STATUS" end} end} end}')
    logger=ROOT/'diagnostics/PTFR_SideJobPilotS1/init.lua';m=lua.execute(logger.read_text());row=m.Sample()
    for f in ('PTFRS1_CleanupDeparture','PTFRS1_CleanupEntered','PTFRS1_CorpoDepartureAck','PTFRS1_CarsDepartureAck','PTFRS1_CorpoCleanupAck','PTFRS1_CarsCleanupAck','PTFRS1_CleanupJoined'):assert row['facts'][f]==1
    assert 'Log failed' in lua.eval('prints[#prints]')
    assert row['journal']['quests/minor_quest/mq005_alley']['state']==3
    for b in ('SetFact','ChangeEntryState','RestoreFresh','Override('):assert b not in logger.read_text(),b
    compile=read(OUT/'compile_result.json');assert compile['equipmentex'] and compile['source_sha256']==sha(ROOT/'redscript/PTFR_SideJobPilotS1/SideJobPilotS1.reds')
    receipt=read(ROOT/'research/side_job_pilot_s1/install_receipt.json')
    mappings=[('build/SideJobCleanupS1_1/TowerContinued_SideJobPilotS1.archive',receipt['files'][0]),('redscript/PTFR_SideJobPilotS1/SideJobPilotS1.reds',receipt['files'][2]),('diagnostics/PTFR_SideJobPilotS1/init.lua',receipt['files'][3])]
    files=[{'source':s,'relative':f['relative'],'sha256':sha(ROOT/s),'predecessor':f['sha256']} for s,f in mappings]
    result={'status':'PASS_S1_1_GUARDED_CLEANUP_OFFLINE_LIVE_PENDING','graph':graph,'guard_mutants':mutants,'abstract_cases':cases,'persistent_fields_unchanged':True,'native_completion_reward_reset':False,'direct_owner_finished_write':False,'equipmentex_full_compile':True,'files':files,'tools':{f'tools/{n}':sha(ROOT/'tools'/n) for n in ('build_side_cleanup_s1_1.ps1','compile_side_cleanup_s1_1.py','test_side_cleanup_s1_1.py')},'compile_sha256':sha(OUT/'compile_result.json'),'manifest_sha256':sha(OUT/'manifest.json')}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('files','tools')},indent=2))
if __name__=='__main__':main()
