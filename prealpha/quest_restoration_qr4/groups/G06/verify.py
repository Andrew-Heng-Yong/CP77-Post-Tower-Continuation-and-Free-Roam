"""G06 source-specific street quest checks. Writes only NEW audit output directories."""
from pathlib import Path
import sys,json,copy,argparse,collections,re
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));import source_inputs as I
from common import read,write,sha,walk
from model import Resource,compare_graph
W=I.W
def evaluate(c,fs,js):
 t=c['$type']
 if t=='questLogicalCondition':
  r=[evaluate(x,fs,js) for x in c['conditions']]
  return all(r) if c['operation']=='AND' else any(r) if c['operation']=='OR' else not any(r) if c['operation']=='NOR' else False
 if t in ['questFactsDBCondition','questJournalCondition']:return evaluate(c['type'],fs,js)
 if t=='questVarComparison_ConditionType':
  if c['factName'] not in fs:return False
  a,b=fs[c['factName']],c['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[c['comparisonType']]
 if t=='questJournalEntryState_ConditionType':return c['path']['realPath'] in js and ((js[c['path']['realPath']]==c['state'])!=bool(c.get('inverted',0)))
 raise ValueError('Unsupported condition, never assume true: '+t)
def seed(c,fs=None,js=None):
 fs={} if fs is None else fs;js={} if js is None else js;t=c['$type']
 if t=='questLogicalCondition':
  for x in c['conditions'][:1] if c['operation']=='OR' else c['conditions']:seed(x,fs,js)
 elif t in ['questFactsDBCondition','questJournalCondition']:seed(c['type'],fs,js)
 elif t=='questVarComparison_ConditionType':
  f,v,op=c['factName'],c['value'],c['comparisonType']
  if op=='Equal':fs[f]=v
  elif op=='Greater':fs[f]=max(fs.get(f,v+1),v+1)
  elif op=='GreaterOrEqual':fs[f]=max(fs.get(f,v),v)
  elif op=='Less':fs[f]=min(fs.get(f,v-1),v-1)
  elif op=='LessOrEqual':fs[f]=min(fs.get(f,v),v)
  else:fs[f]=v+1
 elif t=='questJournalEntryState_ConditionType':js[c['path']['realPath']]=c['state']
 else:raise ValueError(t)
 return fs,js
def path(gr,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in gr['edges']:
   if x==p[-1] and s!='CutSource' and t!='CutDestination' and y not in seen:seen.add(y);q.append(p+[y])
 return None
def run(O):
 assert not O.exists(),'Fresh output directory required'
 ms={};pins=[];checks=[];mutations=[]
 def check(name,ok,evidence):
  checks.append({'name':name,'status':'PASS' if ok else 'FAIL','evidence':evidence});assert ok,name
 for d in I.selected():
  m,p=I.load(d);ms[d]=m;pins.append(p)
  check('pinned_raw_json_model '+d,True,p)
  check('decode_graph_integrity '+d,not m['errors'],m['errors'])
 scripts={}
 for name in ['PTFR_SideJobPilotS1.reds','PTFR_SideJobsS23.reds','PTFR_HistorySnapshotHS1.reds']:
  p=I.C/'package/r6/scripts/PTFR_Consolidated'/name
  if p.exists():scripts[name]=p.read_text(encoding='utf8');pins.append({'path':str(p),'sha256':sha(p),'role':'executing-source'})
 for rel in ['prealpha/consolidation_repair_cr1/donor_review/selection_01.json','research/side_job_cleanup_s1_1/assessment.json','research/side_job_cleanup_s1_1/live_result_20261010.json','docs/gig_pilot_r1_check.md','prealpha/sidejobs_s23/base_a_v2/contract.json','prealpha/sidejobs_s23/base_b/contract.json','prealpha/quest_restoration_qr4/source_epoch_00.json']:
  p=W/rel;assert p.exists();pins.append({'path':str(p),'sha256':sha(p),'role':'policy-or-historical-bounded-evidence'})
 def g(d,gp='root'):return ms[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t] in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 def cond(d,i,gp='root'):return n(d,i,gp)['payload']['condition']
 # Independent native comparison: all original nodes and edges, not selected current metadata.
 allowed={( 'root/3','4'),('root/4','10'),('root/4','15')}
 diffs=compare_graph(ms[I.N1],ms[I.P1N])
 for gp,gr in ms[I.N1]['graphs'].items():
  for i,node in gr['nodes'].items():
   if (gp,i) not in allowed:check('OnlyPain_native_node '+gp+':'+i,n(I.P1N,i,gp)['payload']==node['payload'],{'native':I.N1,'graph':gp,'node':i})
  if gp not in ['root/3','root/4']:check('OnlyPain_native_edges '+gp,g(I.P1N,gp)['edges']==gr['edges'],gp)
 check('OnlyPain_root_prefab_identity',ms[I.P1N]['root_prefabs']==ms[I.N1]['root_prefabs']==['#mq005_pr_alley'],ms[I.N1]['root_prefabs'])
 check('OnlyPain_private_combat_native_exact',not compare_graph(ms[I.N1C],ms[I.P1C]),{'native':I.N1C,'private':I.P1C,'nodes':21})
 expected=copy.deepcopy(n(I.N1,4,'root/3')['payload'])
 def relocate(x):
  if isinstance(x,dict):return {k:relocate(v)for k,v in x.items()}
  if isinstance(x,list):return [relocate(v)for v in x]
  return I.P1C if x==I.N1C else x
 check('OnlyPain_combat_binding_only_relocation',n(I.P1N,4,'root/3')['payload']==relocate(expected),'same native body, private exact combat')
 removals=[['37','Out','9','In'],['5','End_Out','9','In'],['9','Out','11','Succeeded']]
 additions=[['37','Out','400','In'],['5','End_Out','400','In'],['400','True','401','In'],['401','Out','9','In'],['9','Out','402','In'],['402','Out','11','Succeeded'],['400','False','403','In']]
 check('OnlyPain_reward_edge_delta_exact',sorted([x for x in g(I.N1,'root/3')['edges']if x not in removals]+additions)==g(I.P1N,'root/3')['edges'],{'removed':removals,'added':additions})
 for i,f in [(401,'PTFRS1_RewardClaim'),(402,'PTFRS1_RewardAck'),(403,'PTFRS1_RewardReplayRefused')]:check('OnlyPain_reward_receipt '+f,wr(I.P1N,i,f,1,'root/3'),i)
 check('OnlyPain_reward_claim_false_rejects_replay',evaluate(cond(I.P1N,400,'root/3'),{'PTFRS1_RewardClaim':0},{}) and not evaluate(cond(I.P1N,400,'root/3'),{'PTFRS1_RewardClaim':1},{}),'claim0→claim1→native reward→ack1→Succeeded; claim1→refused')
 cleanupadds=[['16','Out','440','In'],['10','Out','441','In'],['15','Out','442','In'],['13','Out','443','In'],['3','Out','444','In'],['14','Out1','445','In'],['445','Out','1','In']]
 check('OnlyPain_cleanup_edge_delta_exact',sorted([x for x in g(I.N1,'root/4')['edges']if x!=['14','Out1','1','In']]+cleanupadds)==g(I.P1N,'root/4')['edges'],cleanupadds)
 for i in [10,15]:
  c=cond(I.P1N,i,'root/4')
  check('OnlyPain_cleanup_retains_exact_native_OR_operand '+str(i),c['operation']=='OR' and len(c['conditions'])==2 and c['conditions'][0]==cond(I.N1,i,'root/4'),'native OR guarded completed-route fallback, not replacement')
  alt=c['conditions'][1];check('OnlyPain_cleanup_alt_keeps_outside_trigger '+str(i),alt['operation']=='AND' and any(x.get('$type')=='questTriggerCondition' and x['type']=='IsOutside' and x['triggerAreaRef']['$value']=='#mq005_tr_big' for x in alt['conditions']),'outside native trigger still required')
  expectedfacts={'PTFRS1_RewardClaim':1,'PTFRS1_RewardAck':1,'mq005_done':1,'mq005_police_left':1,'mq005_police_done':0,'PTFRS1_CleanupDeparture':1,'PTFRS1_OwnerFinished':0}
  actual={x['factName']:x['value']for x in walk(alt)if x.get('$type')=='questVarComparison_ConditionType'}
  check('OnlyPain_cleanup_alt_completed_reward_seam '+str(i),all(actual.get(k)==v for k,v in expectedfacts.items()),actual)
 # Check actual nested admission logic and protect completed/failed/progressed roots.
 fixtures=[]
 for d,i,q in [(I.P1,402,'mq005_alley'),(I.P13,1002,'mq013_punks'),(I.P13,1004,'mq013_punks'),(I.P2,1001,'mq002_veterans'),(I.P2,1002,'mq002_veterans'),(I.P2,1007,'mq002_veterans'),(I.P2,1008,'mq002_veterans'),(I.P2,1100,'mq002_veterans')]:
  c=cond(d,i);fs,js=seed(c);root='quests/minor_quest/'+q
  check('positive_actual_nested_guard '+d+':'+str(i),evaluate(c,fs,js),{'facts':fs,'journals':js})
  fixtures.append({'depot':d,'node':i,'condition':c,'facts':fs,'journals':js})
  for f in ['q307_done','q307_finished','q307_main_game_killed','q307_ep1_killed']:
   check('reject_missing_'+f+d+str(i),not evaluate(c,fs|{f:0},js),f)
  for st in ['Succeeded','Failed']:
   check('protect_'+st+q+str(i),not evaluate(c,fs,js|{root:st}),{'root':root,'state':st})
  # Active is accepted ONLY by the documented postclaim MQ002 RootReactivated branch.
  if d!=I.P2 or i in [1001,1002]:check('protect_Active'+q+str(i),not evaluate(c,fs,js|{root:'Active'}),'actual native journal root')
  for jp in js:
   if jp==root:continue
   check('protect_progressed_child '+q+str(i)+jp,not evaluate(c,fs,js|{jp:'Succeeded'}),jp)
 check('OnlyPain_CR1_donor_preserved',sha(I.C/'archive_source/towercontinued/side_job_pilot_s1/owner.questphase')=='C037E2C93142C7BFA9ABDAAD13E843D8DD0BF87B44C6F190239635C475A6AF4F','CR1 selected donor is Only Pain despite historical Happy Together label')
 check('OnlyPain_wrapper_claim_ack',all(e(I.P1,*x)for x in [(0,'Out',400,'In'),(400,'Out',401,'In'),(401,'Out',402,'In'),(402,'Out',403,'In'),(403,'Out',405,'In1'),(405,'Out1',404,'In'),(404,'Out',1,'In')]),'Ready→NativeRevision→guard→Started→native owner→OwnerFinished')
 # S23 native ancestor prerequisites and exact child bindings.
 ancestor_nodes=[47,52,53,54,55,59,62,70,73,76,78,80,81,82,83,84,86,89,90,173]
 for i in ancestor_nodes:check('GunMusic_native_ancestor_node '+str(i),n(I.P2,i)['payload']==n(I.PAR,i)['payload'],{'native_parent':I.PAR,'node':i})
 ancestor_edges=[e0 for e0 in g(I.PAR)['edges']if e0[0]in set(map(str,ancestor_nodes)) and e0[2]in set(map(str,ancestor_nodes))]
 check('GunMusic_all_retained_native_ancestor_edges',all(x in g(I.P2)['edges']for x in ancestor_edges),ancestor_edges)
 for i,f in [(54,'q001_done'),(80,'q005_done'),(55,'q101_enable_side_content')]:
  check('DayInLife_native_ancestor_predicate '+f,n(I.P13,i)['payload']==n(I.PAR,i)['payload'],{'native_parent':I.PAR,'node':i})
 check('DayInLife_actual_connected_entry_and_recheck',all(e(I.P13,*x)for x in [(1000,'Out',1001,'In'),(1001,'Out',1002,'In'),(1002,'Out',1003,'In'),(1003,'Out',54,'In'),(54,'Out',80,'In'),(80,'Out',55,'In'),(55,'Out',1004,'In'),(1004,'False',1002,'In'),(1004,'True',1005,'In'),(1005,'Out',1006,'In'),(1006,'Out',17,'In1'),(17,'Out1',1007,'In')]),'PA2 intermediate barrier1003 retained; native q001/q005/q101 chain')
 check('DayInLife_native_child_exact_binding',n(I.P13,17)['payload']==n(I.PAR,17)['payload'] and n(I.P13,17)['refs']==[I.N13],n(I.P13,17)['refs'])
 check('GunMusic_native_child_exact_binding',n(I.P2,12)['payload']==n(I.PAR,12)['payload'] and n(I.P2,12)['refs']==[I.N2],n(I.P2,12)['refs'])
 check('GunMusic_final_recheck_then_native',e(I.P2,173,'False',1100,'In') and e(I.P2,1100,'True',1101,'In') and e(I.P2,1101,'Out',12,'In1'),'no unguarded direct native12')
 check('GunMusic_failed_reactivation_is_guarded_not_general_reset',n(I.P2,1004)['reads'][0]['state']=='Failed' and all(not evaluate(cond(I.P2,i),seed(cond(I.P2,i))[0],seed(cond(I.P2,i))[1]|{'quests/minor_quest/mq002_veterans':'Failed'})for i in [1001,1002]),'stable Failed histories cannot pass initial Inactive guards; dormant branch not removed')
 # Native progression and real outcome alternatives, including failure/interruption.
 routes={
 'OnlyPain':[('root/3',[(3,'CombatFromInterruption',4,'In1'),(3,'Combat_out',4,'In1'),(3,'StreetKidSuccess_out',6,'In1'),(3,'Ignored_out',7,'In1'),(3,'CorpoKilledInCrossfire',19,'In1'),(5,'player_attack_corpo_out',38,'In'),(39,'True',15,'Failed')])],
 'DayInLife':[('root',[(0,'Out',8,'In1'),(8,'Out1',9,'In1'),(9,'Out1',10,'In1'),(10,'Out1',1,'In')]),('root/9',[(14,'mq013_00_shopkeep_alive_out',77,'In1'),(14,'mq013_00_shopkeep_dead_out',17,'In'),(14,'combat',52,'In1'),(14,'combat',85,'In1'),(14,'goto_combat_shop',91,'combat_shop'),(76,'mq013_00_shopkeep_alive_out',16,'In'),(76,'mq013_00_shopkeep_dead_out',17,'In'),(16,'Out',15,'In'),(15,'Out',78,'In'),(78,'Out',79,'In')])],
 'GunMusic':[('root',[(121,'to_combat',122,'In1'),(121,'to_outcome',123,'In1'),(121,'quest_fails',138,'In1'),(121,'sq027_suspension',153,'In'),(128,'sq027_suspension',153,'In'),(153,'Out',128,'In1'),(122,'Out1',123,'In1'),(122,'quest_fails',139,'In1'),(123,'quest_fails',140,'In1'),(123,'Out1',124,'Succeeded'),(124,'Out',125,'In'),(125,'Out',126,'In'),(147,'False',152,'In1'),(147,'True',146,'In1')])]}
 for key,d in [('OnlyPain',I.P1N),('DayInLife',I.N13),('GunMusic',I.N2)]:
  for gp,edges in routes[key]:
   for edge0 in edges:check(key+'_native_branch '+gp+str(edge0),e(d,*edge0,gp),{'depot':d,'graph':gp,'edge':edge0})
 check('DayInLife_native_q101_done_internal_gate',any(x.get('factName')=='q101_done' and x.get('comparisonType')=='Greater' and x.get('value')==0 for x in n(I.N13,6,'root/8')['reads']) and e(I.N13,0,'Out',6,'In','root/8'),'q101_enable_side_content ancestor does not substitute native q101_done')
 check('DayInLife_done_active_cleanup',wr(I.N13,3,'mq013_done',1,'root/10') and wr(I.N13,4,'mq013_active',0,'root/10') and e(I.N13,4,'Out',3,'In','root/10'),'native cleanup after either shopkeeper outcome')
 for d,pref in [(I.N13,'#mq013_pr_punks'),(I.N2,'#mq002_pr_factory')]:check('Native_resource_root_prefab '+pref,ms[d]['root_prefabs']==[pref],d)
 check('GunMusic_nested_camp_prefabs',n(I.N2,146)['prefabs']==['#mq002_pr_camp','#mq002_pr_new_camp'],'root factory alone is not whole support')
 # Local phone census is proof only for this actual native dependency closure.
 closure={q:[d for d in ms if (f'\\{folder}\\'in d and '\\bugfixing\\'not in d) or d in extra] for q,folder,extra in [('mq005_alley','mq005',[I.P1,I.P1N,I.P1C]),('mq013_punks','mq013',[I.P13]),('mq002_veterans','mq002',[I.P2])]}
 comm={}
 for q,ds in closure.items():
  hits=[];phonefacts=[]
  for d in ds:
   for gp,gr in ms[d]['graphs'].items():
    for i,node in gr['nodes'].items():
     if node['sms'] or 'Phone'in node['type']:hits.append({'depot':d,'graph':gp,'node':i,'type':node['type'],'paths':node['journal_paths'],'incoming':[x for x in gr['edges']if x[2]==i],'outgoing':[x for x in gr['edges']if x[0]==i]})
     phonefacts += [{'depot':d,'graph':gp,'node':i,'fact':x}for x in node['reads']+node['writes']if x.get('factName','').startswith(('audio_','holo_'))]
  comm[q]={'sms_and_phone_nodes':hits,'holo_audio_fact_nodes':phonefacts,'closure':ds}
  check('No_local_holocall_request_or_ack '+q,not phonefacts,{'bounded_closure':ds,'count':len(phonefacts)})
  if q!='mq002_veterans':check('No_local_phone_or_SMS '+q,not hits,'actual scene and nested phase payload census')
 cb='base\\quest\\minor_quests\\mq002\\phases\\mq002_combat.questphase';end='base\\quest\\minor_quests\\mq002\\phases\\mq002_ending.questphase'
 check('GunMusic_Carol_escape_message_connected',e(cb,4,'Out',20,'In') and e(cb,20,'Out',19,'In') and n(cb,20)['journal_paths']==['contacts/carol/mq002_escaped'],'questSendMessage node20, no external holocall ack invented')
 check('GunMusic_Carol_post_failure_messages',all(e(I.N2,*x,'root/152')for x in [(0,'Out',2,'Active'),(2,'Out',3,'Active'),(3,'Out',1,'In')]),{'message':n(I.N2,2,'root/152')['journal_paths'],'choice':n(I.N2,3,'root/152')['journal_paths']})
 check('GunMusic_reward_scene_and_success_connected',e(end,11,'End 0',26,'In') and e(end,26,'Out',10,'Succeeded') and 'QuestRewards.mq002_done' in str(n(end,26)['payload']),{'native':end,'reward':26})
 check('DayInLife_native_reward_record','QuestRewards.mq013_punks_done'in str(n(I.N13,78,'root/9')['payload']),{'node':78,'graph':'root/9'})
 # Actual REDscript source is pinned, with saved one-shot and delayed cleanup criteria.
 s=scripts['PTFR_SideJobPilotS1.reds'];s23=scripts['PTFR_SideJobsS23.reds']
 for name,needle in [('five_samples','this.departureSamples < 5'),('500m_horizontal','dx * dx + dy * dy >= 250000.0'),('completion_journal','this.State("quests/minor_quest/mq005_alley", "gameJournalQuest") == 3'),('request_preflight','if !this.Preflight() { this.Fail(n"AdmissionDrift_NoResetOrRetry"); return; }'),('no_requeue_enabled','if this.enabled { return this.GetStatus(); }')]:check('OnlyPain_source_'+name,needle in s,needle)
 check('OnlyPain_auto_calls_existing_adapter',all(x in s23 for x in ['SnapshotStateHS1.Admits(this.GetGameInstance(),"mq005_alley")','fresh && this.legacyFreshPrevious','pilot.RestoreFresh();']),{'source':'PTFR_SideJobsS23.reds','LegacyInactive':'current Inactive and saved HS1 admission'})
 # Deliberate mutations touch actual decoded resource copies; raw files remain untouched.
 def raw(d):return Resource(copy.deepcopy(read(I.IDX[d]['json'])))
 def rawnode(r,gp,i):
  gr=r.d(r.root['graph'])
  for child in gp.split('/')[1:]:gr=r.d(next(r.d(x)for x in gr['nodes']if str(r.d(x)['id'])==child)['phaseGraph'])
  return next(r.d(x)for x in gr['nodes']if str(r.d(x)['id'])==str(i))
 def mutate(name,d,change,predicate,desc):
  r=raw(d);change(r);mm=r.normalize();ok=not predicate(mm)
  mutations.append({'name':name,'source':d,'source_sha256':I.IDX[d]['sha256'],'mutation':desc,'actual_decoded_payload_copy':True,'detected':ok,'files_changed':False});check('Mutation '+name,ok,desc)
 def set_root_state(r):
  c=r.d(rawnode(r,'root',402)['condition'])
  for x in walk(r.clean(c)):
   pass
  # walk through dereferenced handles to the actual journal state object.
  todo=[c];seen=set()
  while todo:
   x=r.d(todo.pop())
   if not isinstance(x,(dict,list))or id(x)in seen:continue
   seen.add(id(x))
   if isinstance(x,dict):
    if x.get('$type')=='questJournalEntryState_ConditionType':x['state']='Active';return
    todo+=list(x.values())
   else:todo+=x
  raise AssertionError('journal guard missing')
 mutate('CR1_stale_Active_root_donor',I.P1,set_root_state,lambda m:m['graphs']['root']['nodes']['402']['payload']==n(I.P1,402)['payload'],'actual402 journal Inactive→Active; corrected donor regression')
 mutate('OnlyPain_missing_claim',I.P1N,lambda r:r.d(rawnode(r,'root/3',401)['type']).__setitem__('value',0),lambda m:m['graphs']['root/3']['nodes']['401']['writes'][0]['value']==1,'actual reward claim writer1→0')
 mutate('OnlyPain_missing_root_prefab',I.P1N,lambda r:r.root.__setitem__('phasePrefabs',[]),lambda m:m['root_prefabs']==['#mq005_pr_alley'],'actual resource-root phasePrefabs removed')
 mutate('GunMusic_outdated_reward_record',end,lambda r:r.d(rawnode(r,'root',26)['type'])['rewards'][0].__setitem__('$value','QuestRewards.mq005_done'),lambda m:m['graphs']['root']['nodes']['26']['payload']==n(end,26)['payload'],'actual reward pointer changed to another quest')
 # Remove both-end connection handles, not only normalized metadata.
 def remove_edge(r,gp,a,s,b,t):
  an=rawnode(r,gp,a);bn=rawnode(r,gp,b)
  sh=next(x for x in an['sockets']if r.clean(r.d(x)['name']).get('$value')==s)
  dh=next(x for x in bn['sockets']if r.clean(r.d(x)['name']).get('$value')==t)
  for node in [an,bn]:
   for sock in node['sockets']:
    sd=r.d(sock);sd['connections']=[ch for ch in sd.get('connections',[])if not(r.hid(r.d(ch)['source'])==r.hid(sh) and r.hid(r.d(ch)['destination'])==r.hid(dh))]
 mutate('DayInLife_missing_shopkeeper_dead_branch',I.N13,lambda r:remove_edge(r,'root/9',14,'mq013_00_shopkeep_dead_out',17,'In'),lambda m:['14','mq013_00_shopkeep_dead_out','17','In']in m['graphs']['root/9']['edges'],'actual native dead outcome connection removed at both sockets')
 mutate('GunMusic_missing_escape_SMS',cb,lambda r:remove_edge(r,'root',4,'Out',20,'In'),lambda m:['4','Out','20','In']in m['graphs']['root']['edges'],'actual escape-message producer connection removed')
 mutate('OnlyPain_missing_cleanup_join',I.P1N,lambda r:remove_edge(r,'root/4',14,'Out1',445,'In'),lambda m:['14','Out1','445','In']in m['graphs']['root/4']['edges'],'actual native two-branch cleanup join cannot reach receipt/output')
 # Scene declarations and actual journal socket routes, not just resource presence.
 alley='base\\quest\\minor_quests\\mq005\\scenes\\mq005_01_alley.scene';punks='base\\quest\\minor_quests\\mq013\\scenes\\mq013_00_punks.scene';deal='base\\quest\\minor_quests\\mq002\\scenes\\mq002_01_deal.scene'
 for d,names,counts in [(alley,['Police_Officer_01','Police_Officer_02','Police_Officer_03','Corpo','car_01','car_02'],(11,14)),(punks,['shopkeep','punk_01','punk_02','customer','bike'],(9,15)),(deal,['Carol','Teddy','Cassidy','Scav_leader','nomad_01','nomad_02','scav_sniper','scav_02','scav_03','scav_04','scav_01','scav_05','van'],(17,35))]:
  meta=ms[d]['metadata'];check('Native_actor_and_workspot_declarations '+d,[a['actorName']for a in meta['actors']]==names and (len(meta['workspots']),len(meta['workspotInstances']))==counts,{'actors':names,'workspots_and_instances':counts,'limit':'target-definition/placement resolution remains OPAQUE'})
 for d,edges in [(alley,[['515','0:0','97','0:3'],['97','0:0','99','0:1'],['418','0:0','240','0:3'],['424','0:0','698','0:3']]),(punks,[['622','0:0','336','0:1'],['722','0:0','338','0:1'],['339','0:0','383','0:1'],['345','0:0','347','0:3'],['156','0:0','374','0:4'],['1414','0:0','1415','0:1'],['1533','0:0','1416','0:3']])]:
  for edge0 in edges:check('Native_journal_actual_socket '+d+str(edge0),edge0 in g(d,'scene')['edges'],edge0)
 check('OnlyPain_preserves_native_optional_cash_rewards',all(token in str(n(alley,i,'scene')['payload'])for i,token in [(644,'QuestRewards.mq005_money_no_intimidation'),(658,'QuestRewards.mq005_money_intimidation')]),'native scene cash alternatives unchanged; main once receipt is separate')
 scene_evidence={d:{'metadata':m['metadata'],'graph':m['graphs']['scene']}for d,m in ms.items()if d.endswith('.scene')}
 write(O/'scene_evidence.json',scene_evidence)
 # Source-specific evidence inventory retains exact payloads and socket endpoints.
 important={I.P1:None,I.P1N:None,I.P1C:None,I.P13:None,I.P2:None,I.N1:None,I.N13:None,I.N2:None,cb:None,end:None}
 graph_evidence={d:ms[d] for d in important}
 dependency=[]
 for q,ds in closure.items():
  refs=sorted({ref for d in ds for ref in ms[d]['refs']})
  literals=[]
  for d in ds:
   for gp,gr in ms[d]['graphs'].items():
    for ni,node in gr['nodes'].items():
     for x in walk(node['payload']):
      if x.get('$type') in ['TweakDBID','NodeRef'] and str(x.get('$value'))not in ['0','None']:literals.append({'depot':d,'graph':gp,'node':ni,'type':x['$type'],'value':x.get('$value'),'status':'LITERAL_REFERENCE_NOT_TARGET_DEFINITION_PROOF'})
  dependency.append({'quest_id':q,'depots':[{'depot':x,'inventory_present':x in I.IDX,'normalized_in_this_batch':x in ms,'status':'DECODED_PINNED'if x in ms else 'REFERENCED_TARGET_NOT_INSPECTED'}for x in refs],'literals':literals,'placement':'OPAQUE: binary world definition/NodeRef target workspot/camera resolution not established by local quest/scene decoding'})
 write(O/'source_pins.json',pins);write(O/'graph_evidence.json',graph_evidence);write(O/'native_current_diff.json',diffs);write(O/'guard_fixtures.json',fixtures);write(O/'communications.json',comm);write(O/'dependencies.json',dependency)
 write(O/'tests.json',{'group':'G06','source_epoch':'QR3 candidate_01 epoch00; unchanged relevant payloads','checks':checks,'mutations':mutations,'total_checks':len(checks),'total_mutations':len(mutations),'failed':sum(t['status']!='PASS'for t in checks),'runtime_changes':[]})
 print(json.dumps({'output':str(O),'checks':len(checks),'mutations':len(mutations),'resources':len(ms),'failed':0}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
