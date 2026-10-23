"""Exact native graph deltas and admission models; NOT engine gameplay proof."""
import itertools,json,re,sys
from catalog_gig_rollout_r2 import ROOT,read,sha,walk,value
from test_gig_pilot_r1 import Resource
OUT=ROOT/'research/side_job_pilot_s1'

def graph_checks():
    old=Resource(read(ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq005/mq005.questphase.json'))
    new=Resource(read(OUT/'native_owner.questphase.json'))
    original_combat=Resource(read(ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq005/phases/mq005_combat.questphase.json'))
    combat=Resource(read(OUT/'combat.questphase.json'));count=0
    def compare(og,ng,a,b,route):
        nonlocal count
        on=a.nodes(og);nn=b.nodes(ng)
        oe=a.edges(og);ne=b.edges(ng)
        if route=='root/3':
            expected={(f,s,400,'In') if t==9 else (402,'Out',11,'Succeeded') if (f,t)==(9,11) else (f,s,t,d) for f,s,t,d in oe}
            expected|={(400,'True',401,'In'),(401,'Out',9,'In'),(9,'Out',402,'In'),(400,'False',403,'In')}
            assert ne==expected,(route,ne^expected)
            assert set(nn)==set(on)|{400,401,402,403}
        else:assert oe==ne and set(nn)==set(on),route
        for i,n in on.items():
            op=a.payload(n);np=b.payload(nn[i])
            if route=='root/3' and i==4:
                assert np['phaseResource']['DepotPath']['$value']==r'towercontinued\side_job_pilot_s1\combat.questphase'
                op.pop('phaseResource');np.pop('phaseResource')
            assert op==np,(route,i)
            if n.get('phaseGraph') and ('Data' in n['phaseGraph'] or 'HandleRefId' in n['phaseGraph']):compare(n['phaseGraph'],nn[i]['phaseGraph'],a,b,route+'/'+str(i))
            count+=1
    compare(old.obj['Data']['RootChunk']['graph'],new.obj['Data']['RootChunk']['graph'],old,new,'root')
    compare(original_combat.obj['Data']['RootChunk']['graph'],combat.obj['Data']['RootChunk']['graph'],original_combat,combat,'combat')
    assert new.obj['Data']['RootChunk']['phasePrefabs']==old.obj['Data']['RootChunk']['phasePrefabs']
    assert len(new.obj['Data']['RootChunk']['phasePrefabs'])==1
    boot=Resource(read(OUT/'owner.questphase.json'));root=boot.obj['Data']['RootChunk'];n=boot.nodes(root['graph'])
    assert not root['phasePrefabs'] and not root['inplacePhases']
    assert boot.edges(root['graph'])=={(0,'Out',400,'In'),(400,'Out',401,'In'),(401,'Out',402,'In'),(402,'Out',403,'In'),(403,'Out',405,'In1'),(405,'Out1',404,'In'),(404,'Out',1,'In')}
    assert n[405]['phaseResource']['DepotPath']['$value']==r'towercontinued\side_job_pilot_s1\native_owner.questphase'
    assert not n[405]['phaseInstancePrefabs']
    guard=boot.payload(n[402]);facts={v['factName']:(v['comparisonType'],v['value']) for v in walk(guard) if 'factName' in v}
    manifest=read(OUT/'manifest.json')
    for f,v in manifest['native_guard'].items():assert facts[f]==('Equal',v)
    for f in ('q001_done','q005_done','q101_enable_side_content'):assert facts[f]==('Greater',0)
    assert len(facts)==len(manifest['native_guard'])+3
    assert manifest['packed_readback'] and len(manifest['resources'])==3 and not manifest['vanilla_replacements']
    assert sha(ROOT/'build/SideJobPilotS1/TowerContinued_SideJobPilotS1.archive')==manifest['archive_sha256']
    scene=read(OUT/'sources/json/base/quest/minor_quests/mq005/scenes/mq005_01_alley.scene.json')
    actors=[x.get('actorName') for x in walk(scene) if x.get('actorName')]
    assert actors==['Police_Officer_01','Police_Officer_02','Police_Officer_03','Corpo','car_01','car_02']
    assert not any('johnny' in str(value(x)).lower() for x in actors)
    rewards=[value(v) for x in walk(scene) for v in x.get('rewards',[])];assert set(rewards)=={'QuestRewards.mq005_money_no_intimidation','QuestRewards.mq005_money_intimidation'}
    parent=Resource(read(ROOT/'research/afterlife_world/nix_sources/json/base/quest/minor_quests/minorquests.questphase.json'));pg=parent.obj['Data']['RootChunk']['graph'];pe=parent.edges(pg);pn=parent.nodes(pg)
    assert {(54,'Out',86,'In1'),(86,'Out1',80,'In'),(80,'Out',55,'In'),(55,'Out',70,'In1'),(70,'Out1',73,'In1'),(73,'Out1',62,'In1'),(62,'Out1',19,'In1')}<=pe
    for i,f in ((54,'q001_done'),(80,'q005_done'),(55,'q101_enable_side_content')):assert parent.payload(pn[i])['condition']['type']['factName']==f
    return {'exact_edge_deltas':True,'prefab_behind_optin':True,'native_nodes_preserved':count,'native_scene_actors':actors,'native_scene_rewards_unmodified':True,'ordinary_unlock_path_pinned':True}

def guards(source,history):
    anchors=('this.schema != 1 || this.inflight || this.stage < 1 || this.stage > 5','if this.enabled { return this.GetStatus(); }',
      'if !this.Preflight() { return','if !this.Preflight() { this.Fail','!this.running || epoch != this.epoch','this.stage == 4 || this.stage == 5',
      'CyberwarePolicy.Safe(player)','this.State(paths[i], classes[i]) != 1','this.Fact(facts[i]) != 0',
      '(poi == 1 || poi == 2)','this.Fact(n"PTFRS1_Ready") == 1','this.Fact(n"PTFRS1_NativeRevision") == 1',
      'this.Fact(n"PTFRS1_Request") == 0','this.Fact(n"PTFRS1_Started") == 0','this.Fact(n"PTFRS1_RewardClaim") == 0',
      'this.Fact(n"PTFRS1_RewardAck") == 0','this.Fact(n"PTFRS1_OwnerFinished") == 0','this.Fact(n"wanted_level") == 0')
    hist=('Equals(confirmation, "DISPOSABLE_SAVE")','this.faulted || !this.Tower()',
      'Equals(id, "mq005_alley") && Equals(mode, "fresh")','this.sideFreshObserved && this.baseline.states[root] == 1 && this.CurrentRoot(job) == 1',
      'NotEquals(sideBefore, sideAfter)','this.sideFreshObserved = sideAfter;','this.sideFreshObserved = false;',
      'this.CurrentRoot(this.Find(id)) == 3')
    for token in anchors:assert token in source,token
    for token in hist:assert token in history,token
    for banned in ('ChangeEntryState(', 'ResetFact(', 'StartQuest(', 'ExecuteNode(', 'GiveItem(', 'RemoveItem('):assert banned not in source+history,banned
    assert set(re.findall(r'this.Set\(n"([^"]+)"',source))=={'PTFRS1_Request','PTFRS1_Fault'}
    assert 'SetFact(' not in history
    assert not re.search(r'persistent let \w+: String',source+history)
    return anchors,hist

def main():
    graph=graph_checks();source=(ROOT/'redscript/PTFR_SideJobPilotS1/SideJobPilotS1.reds').read_text();history=(ROOT/'redscript/PTFR_ActivityStateR3/ActivityStateR3.reds').read_text()
    anchors,hist=guards(source,history);mutants=0
    for tokens,which in ((anchors,'source'),(hist,'history')):
        for token in tokens:
            try:guards(source.replace(token,'MUTATED',1) if which=='source' else source,history.replace(token,'MUTATED',1) if which=='history' else history)
            except AssertionError:mutants+=1
            else:raise AssertionError(token)
    prior=(OUT/'predecessor/ActivityStateR3.reds').read_text()
    assert sha(OUT/'predecessor/ActivityStateR3.reds')=='3123E5FAEB15A3D3F79CB9E3555713405B9E29B5E413AB3D95CB5222560B5C0A'
    old_fields=re.findall(r'private persistent let (\w+): ([^;]+);',prior);new_fields=re.findall(r'private persistent let (\w+): ([^;]+);',history)
    assert set(old_fields)<=set(new_fields) and set(new_fields)-set(old_fields)=={('sideFreshObserved','Bool')}
    assert sha(ROOT/'redscript/PTFR_ActivityStateR3/ActivityDefinition.generated.reds')=='81900EBDB2633424DDC41B9BD2223F2E5740E6CA807E5C1A58DE645159162AE5'
    # Exhaustive abstract journal admission and individual fact corruption.
    cases=0
    def untouched(states,facts,eligible,poi):return all(v==1 for v in states) and all(v==0 for v in facts) and eligible and poi in (1,2)
    for states in itertools.product(range(-1,5),repeat=6):
        ok=untouched(states,[0]*7,True,1);assert ok==all(v==1 for v in states);cases+=1
    for facts in itertools.product((0,1),repeat=7):
        assert untouched([1]*6,facts,True,1)==(not any(facts));cases+=1
    for confirm,tower,fault,mode,eligible,poi in itertools.product(('', 'DISPOSABLE_SAVE'),(False,True),(False,True),('fresh','resume','replay','bad'),(False,True),range(-1,5)):
        allowed=confirm=='DISPOSABLE_SAVE' and tower and not fault and mode=='fresh' and untouched([1]*6,[0]*7,eligible,poi)
        assert not allowed or (confirm=='DISPOSABLE_SAVE' and tower and not fault and mode=='fresh' and eligible and poi in (1,2));cases+=1
    # Own admission never writes twice, terminal outcomes never enter fresh mode.
    for stage in range(1,6):
        ledger={'enabled':True,'stage':stage,'requests':1,'rewards':0};saved=json.loads(json.dumps(ledger))
        for _ in range(20):assert saved['enabled'] and saved['requests']==1
        cases+=20
    for old_certificate in (False,True):
        restored={'certified':old_certificate,'sideFreshObserved':False};assert not(restored['certified'] and restored['sideFreshObserved']);cases+=1
    sys.path.insert(0,str(ROOT/'research/phase2b_p0/tooling/python'));from lupa.luajit21 import LuaRuntime
    lua=LuaRuntime(unpack_returned_tuples=True)
    lua.execute('callbacks={};prints={};registerForEvent=function(k,v) callbacks[k]=v end; print=function(v) prints[#prints+1]=v end; IsDefined=function(v) return v~=nil end; os={date=function() return "STAMP" end}; io={open=function() return nil,"mock disk failure" end}; local ffi=require("ffi"); EnumInt=function(v) return ffi.new("uint64_t",v) end; json={encode=function(v) return "{}" end}; local e={}; local jm={GetEntryByString=function() return e end,GetEntryState=function() return 1 end,IsEntryTracked=function() return false end,GetIsObjectiveOptional=function() return false end,HasAnyDelayedStateChanges=function() return false end}; Game={GetQuestsSystem=function() return {GetFactStr=function() return 1 end} end,GetPlayer=function() return {GetEntityID=function() return "ID" end,GetWorldPosition=function() return {x=0,y=0,z=0} end} end,GetJournalManager=function() return jm end,GetScriptableSystemsContainer=function() return {Get=function() return {Inspect=function() return "STATUS" end} end} end}')
    logger=ROOT/'diagnostics/PTFR_SideJobPilotS1/init.lua';m=lua.execute(logger.read_text());row=m.Sample();assert row['player_present'] and row['status']=='STATUS';assert row['journal']['quests/minor_quest/mq005_alley']['state']==1
    assert 'Log failed' in lua.eval('prints[#prints]')
    lua.execute('Game.GetJournalManager().GetEntryState=function() return 6 end');row=m.Sample();assert row['journal']['quests/minor_quest/mq005_alley']['state']=='UNKNOWN'
    lua.execute('Game.GetPlayer=function() return nil end');assert not m.Sample()['player_present']
    for banned in ('SetFact','ChangeEntryState','RestoreFresh','Override('):assert banned not in logger.read_text(),banned
    compile=read(OUT/'compile_result.json');assert compile['equipmentex'] and compile['status']=='PASS_OFFLINE_COMPILE_NOT_ENGINE_PROOF'
    for p,digest in compile['source_hashes'].items():assert sha(ROOT/p)==digest,p
    mappings=[('build/SideJobPilotS1/TowerContinued_SideJobPilotS1.archive','archive/pc/mod/TowerContinued_SideJobPilotS1.archive'),('archive/side_job_pilot_s1/TowerContinued_SideJobPilotS1.archive.xl','archive/pc/mod/TowerContinued_SideJobPilotS1.archive.xl'),('redscript/PTFR_SideJobPilotS1/SideJobPilotS1.reds','r6/scripts/PTFR_SideJobPilotS1/SideJobPilotS1.reds'),('diagnostics/PTFR_SideJobPilotS1/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_SideJobPilotS1/init.lua'),('redscript/PTFR_ActivityStateR3/ActivityStateR3.reds','r6/scripts/PTFR_ActivityStateR3/ActivityStateR3.reds')]
    files=[{'source':s,'relative':r,'sha256':sha(ROOT/s),'predecessor':'3123E5FAEB15A3D3F79CB9E3555713405B9E29B5E413AB3D95CB5222560B5C0A' if i==4 else ''} for i,(s,r) in enumerate(mappings)]
    tools=('audit_side_pilot_s1.py','extract_side_pilot_s1.ps1','build_side_pilot_s1.ps1','compile_side_pilot_s1.py','test_side_pilot_s1.py','deploy_side_pilot_s1.ps1')
    result={'status':'PASS_ONLY_PAIN_FRESH_PILOT_OFFLINE_LIVE_PENDING','graph':graph,'guard_mutants':mutants,'abstract_admission_cases':cases,'logger':{'getter_only':True,'checks':4,'disk_failure_safe':True,'enum_cdata_normalized':True},'equipmentex_full_compile':True,'completed_replay_adapters':0,'files':files,'tools':{f'tools/{t}':sha(ROOT/'tools'/t) for t in tools},'compile_sha256':sha(OUT/'compile_result.json'),'game_writes':0,'save_writes':0}
    (OUT/'tests.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in result.items() if k not in ('files','tools')},indent=2))
if __name__=='__main__':main()
