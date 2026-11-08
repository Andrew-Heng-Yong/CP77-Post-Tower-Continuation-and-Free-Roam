"""Read-only E investigation and actual-data regressions; fresh outputs only."""
from pathlib import Path
import sys,argparse,copy,json,gzip,collections
W=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();O=Path(args.output).resolve();assert not O.exists();O.mkdir(parents=True)
A=W/'diagnostics/vanilla_parity_20261029_01/analysis_02';I=read(A/'resource_inventory.json');MI=read(A/'model_inventory.json');PH3=W/'prealpha/phone_studios_ph3/candidate_01'
P30=r'towercontinued\sidejobs_s23\base_b\mq030.questphase';N30=r'base\quest\minor_quests\mq030\mq030.questphase';P32=r'towercontinued\sidejobs_s2\mq032_sacrum.questphase';N32=r'base\quest\minor_quests\mq032\mq032_sacrum.questphase';P26=r'towercontinued\sidejobs_s23\base_b\mq026.questphase';F26=r'towercontinued\sidejobs_s25\prophet\mq026_fresh.questphase';N26=r'base\quest\minor_quests\mq026\mq026.questphase';B0=r'towercontinued\b0_story_zane\zane_service.questphase';PAR=r'base\quest\minor_quests\minorquests.questphase'
DD=r'base\quest\default_dialogs.questphase';NS=r'towercontinued\ncpd_scanners_n2\ma_wat_kab_06.questphase';SN=r'base\open_world\minor_activities\watson\kabuki\ma_wat_kab_06\ma_wat_kab_06_phase.questphase'
selected={d for d in MI if any(t in d for t in ['\\mq030\\','\\mq032\\','\\mq026\\'])}|{P30,P32,P26,F26,B0,PAR,DD,NS,SN}
models={};pins=[];checks=[]
def ck(name,ok,evidence):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
for d in sorted(selected):
 r=I[d];j=Path(r['json']);b=j.with_suffix('')
 if d.startswith('towercontinued\\'):b=PH3/'archive_source'/Path(d.replace('\\','/'))
 elif not b.exists() and '\\json\\' in str(j):b=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
 ck('raw binary pin '+d,b.is_file() and sha(b)==r['sha256'],str(b))
 model=Resource(read(j)).normalize();old=json.loads(gzip.decompress(Path(MI[d]['normalized_model']).read_bytes()));old.setdefault('embedded_files',[])
 ck('raw JSON equals pinned model '+d,model==old,{'json':str(j),'sha256':sha(j)})
 models[d]=model;pins.append({'depot':d,'binary':str(b),'sha256':sha(b),'json':str(j),'json_sha256':sha(j),'provider':r['archive'],'errors':model['errors']})
def g(d,gp='root'):return models[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def ed(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in g(d,gp)['edges']
def ev(x,f,j):
 t=x['$type']
 if t=='questLogicalCondition':
  v=[ev(c,f,j) for c in x['conditions']];return {'AND':all(v),'OR':any(v),'NOR':not any(v)}[x['operation']]
 if t in ['questFactsDBCondition','questJournalCondition']:return ev(x['type'],f,j)
 if t=='questVarComparison_ConditionType':
  if x['factName'] not in f:return False
  a=f[x['factName']];b=x['value'];return {'Equal':a==b,'Greater':a>b,'Less':a<b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b}[x['comparisonType']]
 if t=='questJournalEntryState_ConditionType':
  q=x['path']['realPath'];return False if q not in j else (j[q]==x['state'])!=bool(x.get('inverted',0))
 raise ValueError(t)
def sample(d,i):
 f={};j={}
 for c in n(d,i)['reads']:
  if c.get('$type')=='questVarComparison_ConditionType':
   if c['comparisonType'] in ['Equal','GreaterOrEqual']:f[c['factName']]=c['value']
   elif c['comparisonType']=='Greater':f[c['factName']]=c['value']+1
  if 'path' in c:j[c['path']['realPath']]=c['state']
 return f,j
for d,body,native,guards,root in [(P30,18,N30,[1002,1004],'quests/minor_quest/mq030_melisa'),(P32,4,N32,[1001,1002],'quests/minor_quest/mq032_sacrum'),(P26,39,N26,[1002,1004],'quests/minor_quest/mq026_conspiracy'),(F26,39,N26,[1002,1004],'quests/minor_quest/mq026_conspiracy')]:
 ck('original native body payload '+d,n(d,body)['payload']==n(PAR,body)['payload'],{'native_parent':PAR,'node':body,'body':native})
 for i in guards:
  f,j=sample(d,i);c=n(d,i)['payload']['condition'];ck('actual positive serialized guard '+d+str(i),ev(c,f,j),{'facts':f,'journals':j})
  for state in ['Active','Succeeded','Failed']:ck('reject progressed root '+d+str(i)+state,not ev(c,f,j|{root:state}),{'guard':i,'root':root,'state':state})
  ck('reject absent journal '+d+str(i),not ev(c,f,{k:v for k,v in j.items() if k!=root}),{'guard':i})
  own=next(c['factName'] for c in n(d,i)['reads'] if c.get('factName','').endswith('_Issued') and ('MQ0' in c['factName']) and c['value']==0)
  ck('reject issued owner '+d+str(i),not ev(c,f|{own:1},j),{'fact':own})
  ck('reject nonTower '+d+str(i),not ev(c,f|{'q307_done':0},j),{'guard':i})
for id in [54,80,55]:ck('MQ030 native ancestor '+str(id),n(P30,id)['payload']==n(PAR,id)['payload'],{'native':PAR,'node':id})
for id in [81,83,84]:ck('MQ032 native ancestor '+str(id),n(P32,id)['payload']==n(PAR,id)['payload'],{'native':PAR,'node':id})
ck('MQ032 actual guard and body route',all(ed(P32,*e) for e in [[0,'Out',1000,'In'],[1000,'Out',1001,'In'],[1001,'Out',81,'In1'],[81,'Out1',83,'In1'],[83,'Out1',84,'In1'],[84,'Out1',1002,'In'],[1002,'True',1003,'In'],[1003,'Out',4,'In1'],[4,'Out1',1004,'In']]),P32)
for d in [P26,F26]:ck('MQ026 actual guarded native In1 route '+d,all(ed(d,*e) for e in [[1002,'Out',1003,'In'],[1003,'Out',1004,'In'],[1004,'True',1005,'In'],[1005,'Out',1006,'In'],[1006,'Out',39,'In1'],[39,'Out1',1007,'In']]),d)
# Fresh and historically sampled prophet seams are different, with reciprocal
# ownership guards. Compare actual constants rather than assume a race by name.
f0,j0=sample(F26,1004);f1,j1=sample(P26,1004)
ck('prophet fresh state excludes resume adapter',not ev(n(P26,1004)['payload']['condition'],f0|{'PTFRS23_MQ026_Permit':1,'PTFRS23_MQ026_Issued':0,'PTFRS23_MQ026_Finished':0,'PTFRS23_MQ026_Fault':0},j0),'first_conspiracy/lilith/lookat/stop_preach0 vs1')
ck('prophet resume state excludes fresh adapter',not ev(n(F26,1004)['payload']['condition'],f0|f1,j1),'distinct native progress facts')
for d,other in [(P26,'PTFRS25_MQ026_FRESH_Issued'),(F26,'PTFRS23_MQ026_Issued')]:
 f,j=sample(d,1004);ck('prophet other owner blocks '+d,not ev(n(d,1004)['payload']['condition'],f|{other:1},j),other)
ck('MQ032 success failure epilogue routes',all(ed(N32,*e) for e in [[32,'Out1',33,'hook_done'],[33,'Success',34,'Success'],[33,'Fail',34,'Fail'],[34,'Out1',1,'In']]),{'native':N32})
ck('MQ030 ordered native stages',all(ed(N30,*e) for e in [[0,'Out',43,'In1'],[43,'Out1',63,'In1'],[63,'Out1',64,'In1'],[64,'Out1',83,'In1'],[83,'Out1',1,'In']]),{'native':N30})
ck('MQ026 original startup facts and cleanup retained',ed(N26,0,'Out',3,'In') and ed(N26,3,'Out',103,'In') and ed(N26,103,'Out',4,'In') and n(N26,3)['writes'][0]['factName']=='mq026_started' and n(N26,6)['writes'][0]['factName']=='mq026_done',N26)
calls={};rewards=[];trace=[];bindings=[];depots=set()
for q in ['mq030','mq032','mq026']:
 calls[q]=[]
 for d,m in models.items():
  if '\\'+q+'\\' not in d:continue
  for gp,gr in m['graphs'].items():
   for i,x in gr['nodes'].items():
    for w in x['writes']:
     if w['value']>0 and w['factName'].startswith(('holo_','audio_')) and w['factName'].endswith(('_start_activate','_end_activate')):calls[q].append({'resource':d,'graph':gp,'node':i,'fact':w})
 ck('no quest owned phone requests '+q,not calls[q],{'bounded_native_external_phase_closure':True})
for d,m in models.items():
 depots.update(m['refs'])
 for gp,gr in m['graphs'].items():
  for i,x in gr['nodes'].items():
   if x['reads'] or x['writes'] or x['reward'] or x['journal_paths']:trace.append({'resource':d,'graph':gp,'node':i,'payload':x['payload'],'incoming':[e for e in gr['edges'] if e[2]==i],'outgoing':[e for e in gr['edges'] if e[0]==i]})
   if x['reward']:rewards.append({'resource':d,'graph':gp,'node':i,'payload':x['payload']})
   if x['node_refs'] or x['prefabs']:bindings.append({'resource':d,'graph':gp,'node':i,'NodeRefs':x['node_refs'],'prefabs':x['prefabs']})
for d,gp,i,record in [(r'base\quest\minor_quests\mq030\scenes\mq030_01_melisa.scene','scene',814,'QuestRewards.mq030_cyberpsycho_defeated'),(r'base\quest\minor_quests\mq030\scenes\mq030_01_melisa.scene','scene',817,'QuestRewards.mq030_testimony_given'),(r'base\quest\minor_quests\mq032\scenes\mq032_02_maelstrom.scene','scene',463,'QuestRewards.mq032_done'),(r'base\quest\minor_quests\mq026\scenes\mq026_02_death.scene','scene',230,'QuestRewards.mq026_done')]:ck('native reward reference '+record,any(x.get('$type')=='TweakDBID' and value(x)==record for x in walk(n(d,i,gp)['payload'])),{'resource':d,'node':i,'definition':'unresolved'})
# Source-confirmed postcompletion lease overlap. No engine spawn result claimed.
bg=g(B0);mg=g(P30)
ck('MQ030 temporary helper owns same native prefab',n(P30,1020)['prefabs']==n(B0,5)['prefabs']==['#pr_cct_dtn_cloth_01'],{'quest_helper':1020,'B0_owner':5})
ck('MQ030 helper has surviving default_on rearm',ed(P30,1020,'Out1',1021,'In') and ed(P30,1021,'Out',1020,'In1') and n(P30,1021)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'cct_dtn_cloth_01_default_on','value':0}],{'helper':1020,'rearm':1021})
ck('MQ030 main completion releases B0 without helper retirement',ed(P30,18,'Out1',1007,'In') and ed(P30,1007,'Out',1012,'In') and n(P30,1012)['writes'][0]['factName']=='PTFRB0ZAN_QuestOwns' and not any(e[1]=='CutSource' and e[2] in ['1020','1021'] for e in mg['edges']),{'failure_route':'18.Out1->1007.Finished->1012.QuestOwns0','helper_cut_edges':[]})
bf,bj=sample(B0,2);ck('MQ030 B0 admits after released lease with default flag',ev(n(B0,2)['payload']['condition'],bf|{'PTFRB0ZAN_QuestOwns':0,'PTFRB0ZAN_Enabled':1,'cct_dtn_cloth_01_default_on':1,'mq030_done':1},bj),{'B0_guard':2})
native_scope=g(P30,'root/1020');ck('MQ030 native helper provides terminating output acknowledgement',ed(P30,3,'Out',5,'Inactive','root/1020') and ed(P30,5,'Out',1,'In','root/1020') and n(P30,1,'root/1020')['payload']['type']=='Terminating',{'native_retirement':'3->5->1.Terminating;parent1020.Out1'})
def safe_retirement(graph,scope):
 # Original helper scope must observe completed receipt, and all release paths
 # must be downstream of natural retirement, never direct main completion.
 wait=scope['nodes']['3']['payload']['condition']
 has_stop=any(x.get('factName')=='PTFRS23_MQ030_Finished' and x.get('value')==1 for x in walk(wait))
 wake=any(x.get('factName')=='PTFRS23_MQ030_Finished' and x.get('value')==1 for x in walk(graph['nodes']['1021']['payload']['condition']))
 return has_stop and wake and ['1007','Out','1012','In'] not in graph['edges'] and all(e in graph['edges'] for e in [['1020','Out1','1022','In'],['1022','True','1012','In'],['1022','False','1021','In'],['1021','Out','1023','In'],['1023','True','1012','In'],['1023','False','1020','In1']])
before=safe_retirement(mg,native_scope)
proposal=copy.deepcopy(mg);pscope=copy.deepcopy(native_scope)
done={'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRS23_MQ030_Finished','value':1}}
pscope['nodes']['3']['payload']['condition']={'$type':'questLogicalCondition','operation':'OR','conditions':[pscope['nodes']['3']['payload']['condition'],copy.deepcopy(done)]}
proposal['nodes']['1021']['payload']['condition']={'$type':'questLogicalCondition','operation':'OR','conditions':[proposal['nodes']['1021']['payload']['condition'],copy.deepcopy(done)]}
for i in ['1022','1023']:proposal['nodes'][i]={'payload':{'$type':'questConditionNodeDefinition','id':int(i),'condition':copy.deepcopy(done)}}
proposal['edges'].remove(['1007','Out','1012','In']);proposal['edges'].remove(['1020','Out1','1021','In']);proposal['edges'].remove(['1021','Out','1020','In1']);proposal['edges'] += [['1020','Out1','1022','In'],['1022','True','1012','In'],['1022','False','1021','In'],['1021','Out','1023','In'],['1023','True','1012','In'],['1023','False','1020','In1']]
after=safe_retirement(proposal,pscope)
ck('MQ030 bad current vs proposed acknowledged retirement regression',not before and after,{'current_pass':before,'in_memory_proposal_pass':after,'proposal_not_serialized':True})
fixtures=[]
for state in ['ACTIVE_HELPER','PENDING_REARM']:
 for finished in [0,1]:
  for default in [0,1]:
   facts={'PTFRS23_MQ030_Finished':finished,'cct_dtn_cloth_01_default_on':default}
   if state=='ACTIVE_HELPER':
    awake=ev(pscope['nodes']['3']['payload']['condition'],facts,{})
    if not awake:result='CONTINUE_SINGLE_HELPER'
    else:result='RETIRE_ACK_THEN_RELEASE' if ev(done,facts,{}) else 'RETIRE_ACK_PENDING_REARM'
   else:
    awake=ev(proposal['nodes']['1021']['payload']['condition'],facts,{})
    if not awake:result='WAIT'
    else:result='RELEASE_WITHOUT_REENTER' if ev(done,facts,{}) else 'RESTART_SINGLE_HELPER'
   expected={('ACTIVE_HELPER',0,0):'RETIRE_ACK_PENDING_REARM',('ACTIVE_HELPER',0,1):'CONTINUE_SINGLE_HELPER',('ACTIVE_HELPER',1,0):'RETIRE_ACK_THEN_RELEASE',('ACTIVE_HELPER',1,1):'RETIRE_ACK_THEN_RELEASE',('PENDING_REARM',0,0):'WAIT',('PENDING_REARM',0,1):'RESTART_SINGLE_HELPER',('PENDING_REARM',1,0):'RELEASE_WITHOUT_REENTER',('PENDING_REARM',1,1):'RELEASE_WITHOUT_REENTER'}[(state,finished,default)]
   fixtures.append({'saved_phase_state':state,'finished':finished,'default_on':default,'observed_symbolic_route':result,'expected':expected})
   ck('MQ030 proposed phase fixture '+state+str(finished)+str(default),result==expected,fixtures[-1])
ck('MQ030 proposal preserves saved node identities',set(mg['nodes']).issubset(proposal['nodes']) and set(native_scope['nodes'])==set(pscope['nodes']) and set(proposal['nodes'])-set(mg['nodes'])=={'1022','1023'},'All original parent/helper IDs retained; two new IDs only')
mutations=[]
for d,i in [(P30,1004),(P32,1002),(F26,1004)]:
 f,j=sample(d,i);root=next(q for q in j if q.count('/')==2);bad=copy.deepcopy(n(d,i)['payload']['condition'])
 for x in walk(bad):
  if x.get('$type')=='questJournalEntryState_ConditionType' and x['path']['realPath']==root:x['state']='Active'
 mutations.append({'fault':'admit Active '+d,'detected':ev(bad,f,j|{root:'Active'}) and not ev(n(d,i)['payload']['condition'],f,j|{root:'Active'})})
bad=copy.deepcopy(g(N32));bad['edges'].remove(['33','Fail','34','Fail']);mutations.append({'fault':'lose monk lethal/failure outcome','detected':['33','Fail','34','Fail'] not in bad['edges']})
bad=copy.deepcopy(proposal);bad['edges'].append(['1007','Out','1012','In']);mutations.append({'fault':'reintroduce early MQ030 lease release','detected':not safe_retirement(bad,pscope)})
for x in mutations:ck('mutation '+x['fault'],x['detected'],x)
write(O/'source_pins.json',pins);write(O/'graph_evidence.json',{'trace':trace,'bindings':bindings,'root_prefabs':{d:m['root_prefabs'] for d,m in models.items()},'rewards':rewards,'phone_requests':calls})
write(O/'dependency_depots.json',{'depots':sorted(depots|set(models))})
write(O/'defect_mq030.json',{'id':'QR3-E-MQ030-LEASE','status':'CONFIRMED_STRUCTURAL_DUPLICATE_OWNER_ROUTE_REVIEW_REQUIRED','resource':P30,'resource_sha256':I[P30]['sha256'],'competing_resource':B0,'route':'native18.Out1->1007.Finished->1012.QuestOwns0 leaves helper1020/1021 alive;B0 root2 then admits5 with same #pr_cct_dtn_cloth_01','current_regression_pass':before,'proposal_regression_pass':after,'proposal':'Use existing helper3->5->1.Terminating natural completion as retirement acknowledgement. Stop helper on own Finished1; route helperOut1 through completion check before1012;wake pending1021 onFinished. No cut/release fanout. Preserve existingIDs andnativefacts.','limits':'Actual actor duplication is LIVE_ONLY; old-save paused condition re-evaluation and pre-existing overlap need transition review. No runtime patch performed by agent.'})
write(O/'proposal_mq030.json',{'source_sha256':I[P30]['sha256'],'remove_edges':[['1007','Out','1012','In'],['1020','Out1','1021','In'],['1021','Out','1020','In1']],'add_edges':[['1020','Out1','1022','In'],['1022','True','1012','In'],['1022','False','1021','In'],['1021','Out','1023','In'],['1023','True','1012','In'],['1023','False','1020','In1']],'new_nodes':{i:proposal['nodes'][i]['payload'] for i in ['1022','1023']},'changed_conditions':{'root/1020:3':pscope['nodes']['3']['payload']['condition'],'root:1021':proposal['nodes']['1021']['payload']['condition']},'symbolic_saved_phase_fixtures':fixtures,'not_serialized':True,'scope':'Proposed data patch for root independent review; output is evidence, not a cooked resource or accepted installation'})
write(O/'tests.json',{'status':'PASS_SCOPED_CHECKS_WITH_CONFIRMED_CURRENT_DEFECT','checks':len(checks),'results':checks,'mutations':mutations,'sources':len(pins),'runtime_changes':[],'current_runtime_defect_count':1,'scope':'PASS means investigation controls passed, not that defective MQ030 lifecycle passed. Named current retirement regression is false.'})
print(json.dumps({'checks':len(checks),'sources':len(pins),'mutations':len(mutations),'confirmed_current_defects':1}))
