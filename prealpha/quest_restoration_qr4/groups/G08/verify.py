"""G08 exact native contracts; outputs only fresh audit evidence."""
from pathlib import Path
import sys,copy,json,argparse,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
def cmp(a,op,b):return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[op]
def ev(c,f,j,inv):
 t=c['$type']
 if t=='questLogicalCondition':
  r=[ev(x,f,j,inv)for x in c['conditions']];return all(r)if c['operation']=='AND'else any(r)if c['operation']=='OR'else not any(r)if c['operation']=='NOR'else False
 if t in ['questFactsDBCondition','questJournalCondition','questObjectCondition']:return ev(c['type'],f,j,inv)
 if t=='questVarComparison_ConditionType':return c['factName']in f and cmp(f[c['factName']],c['comparisonType'],c['value'])
 if t=='questJournalEntryState_ConditionType':return c['path']['realPath']in j and ((j[c['path']['realPath']]==c['state'])!=bool(c.get('inverted',0)))
 if t=='questInventory_ConditionType':return c['itemID']['$value']in inv and cmp(inv[c['itemID']['$value']],c['comparisonType'],c['quantity'])
 raise ValueError('Not evaluated as true: '+t)
def seed(c,f=None,j=None,inv=None):
 f={}if f is None else f;j={}if j is None else j;inv={}if inv is None else inv;t=c['$type']
 if t=='questLogicalCondition':
  for x in c['conditions'][:1]if c['operation']=='OR'else c['conditions']:seed(x,f,j,inv)
 elif t in ['questFactsDBCondition','questJournalCondition','questObjectCondition']:seed(c['type'],f,j,inv)
 elif t=='questVarComparison_ConditionType':
  k,v,op=c['factName'],c['value'],c['comparisonType']
  if op=='Equal':f[k]=v
  elif op=='Greater':f[k]=max(f.get(k,v+1),v+1)
  elif op=='GreaterOrEqual':f[k]=max(f.get(k,v),v)
  elif op=='Less':f[k]=min(f.get(k,v-1),v-1)
  elif op=='LessOrEqual':f[k]=min(f.get(k,v),v)
  else:f[k]=v+1
 elif t=='questJournalEntryState_ConditionType':j[c['path']['realPath']]=c['state']
 elif t=='questInventory_ConditionType':inv[c['itemID']['$value']]=c['quantity']
 else:raise ValueError(t)
 return f,j,inv
def path(g,a,b):
 q=collections.deque([[str(a)]]);seen={str(a)}
 while q:
  p=q.popleft()
  if p[-1]==str(b):return p
  for x,s,y,t in g['edges']:
   if x==p[-1]and s!='CutSource'and t!='CutDestination'and y not in seen:seen.add(y);q.append(p+[y])
 return None
def run(O):
 assert not O.exists();M={};pins=[];tests=[];mut=[]
 def ck(name,ok,evidence):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':evidence});assert ok,name
 for d in I.selected():m,p=I.load(d);M[d]=m;pins.append(p);ck('pinned_source_model '+d,True,p);ck('decoded_graph_integrity '+d,not m['errors'],m['errors'])
 historical=['research/sidejobs_s23/base_a_v2/assessment_01.json','research/sidejobs_s23/base_a_v2/resume_02/manifest.json','prealpha/sidejobs_s23/base_a_v2/contract.json','prealpha/skippy_ambient_sc3/candidate_02/assessment_01.json','diagnostics/skippy_vanilla_wiki_audit_20261028_01/assessment_01.json','docs/skippy_vanilla_wiki_review_20261028.md','prealpha/quest_restoration_qr4/source_epoch_00.json']
 for rel in historical:p=I.W/rel;assert p.exists();pins.append({'path':str(p),'sha256':sha(p),'role':'existing bounded procedure/observation/policy evidence; no rerun'})
 scripts={}
 for name in ['PTFR_SideJobsS23.reds','PTFR_SideJobsS2.reds','PTFR_HistorySnapshotHS1.reds']:
  p=I.C/'package/r6/scripts/PTFR_Consolidated'/name
  if p.exists():pins.append({'path':str(p),'sha256':sha(p),'role':'current REDscript'});scripts[name]=p.read_text(encoding='utf8')
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def e(d,a,s,b,t,gp='root'):return [str(a),s,str(b),t]in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 # Native ancestry, selected by actual referenced target, never a historical count.
 for d,target in [(I.P7,21),(I.B7,21),(I.P8,29),(I.P21,8)]:
  ns=g(d)['nodes'];retained=[i for i in ns if i in g(I.PAR)['nodes']and int(i)<1000 and int(i)!=0 and int(i)!=target]
  for i in retained:ck('native_parent_payload '+d+':'+i,n(d,i)['payload']==n(I.PAR,i)['payload'],{'parent':I.PAR,'node':i})
  ne=[x for x in g(I.PAR)['edges']if x[0]in retained and x[2]in retained];ck('native_retained_ancestor_edges '+d,all(x in g(d)['edges']for x in ne),ne)
  if d!=I.B7:ck('native_target_binding '+d,n(d,target)['payload']==n(I.PAR,target)['payload'],n(d,target)['refs'])
 # Exact current guard trees, including inventory and journal protection.
 fixtures=[]
 for d,q,ids in [(I.P7,'mq007_smartgun',[1001,1002,1007,1008,1100]),(I.B7,'mq007_smartgun',[1001,1002,1007,1008,1100]),(I.P8,'mq008_party',[1002]),(I.P21,'mq021_guide',[1001,1002,1007,1008,1100])]:
  for ni in ids:
   c=n(d,ni)['payload']['condition'];f,j,inv=seed(c);root='quests/minor_quest/'+q
   ck('positive_actual_guard '+d+str(ni),ev(c,f,j,inv),{'facts':f,'journals':j,'inventory':inv});fixtures.append({'depot':d,'node':ni,'condition':c,'facts':f,'journals':j,'inventory':inv})
   for fact in ['q307_done','q307_finished','PTFRPA2_Finished']:ck('missing_Tower_'+fact+d+str(ni),not ev(c,f|{fact:0},j,inv),fact)
   for state in ['Succeeded','Failed']:ck('protect_terminal_'+state+d+str(ni),not ev(c,f,j|{root:state},inv),root)
   for jp in j:
    if jp!=root:ck('protect_progressed_child '+d+str(ni)+jp,not ev(c,f,j|{jp:'Succeeded'},inv),jp)
   if d==I.B7:
    for key,value in [('mq007_skippy_enemies_lethal',12),('mq007_skippy_enemies_non_lethal',52),('mq007_skippy_enemies_total',97),('PTFRS23_MQ007_ModeTalkConfirmed',0),('PTFRS23_MQ007_Issued',1)]:ck('resume_exact_unsupported_state_rejected '+str(ni)+key,not ev(c,f|{key:value},j,inv),{'counter_or_owned_history':key,'changed_to':value})
    ck('resume_requires_original_skippy '+str(ni),not ev(c,f,j,{'Items.mq007_skippy':0}),inv)
   if d==I.P7:ck('fresh_refuses_existing_skippy '+str(ni),not ev(c,f,j,{'Items.mq007_skippy':1}),inv)
 # Resume continues immediately AFTER native mode conversation; no counter/mode reset.
 for gp,gr in M[I.R7]['graphs'].items():
  for i,node in gr['nodes'].items():ck('resume_exact_native_node '+gp+':'+i,node['payload']==n(I.N7,i,gp)['payload'],{'native':I.N7,'graph':gp,'node':i})
  if gp!='root':ck('resume_exact_native_edges '+gp,gr['edges']==g(I.N7,gp)['edges'],gp)
 resume_edges=[['0','Out','11','In'],['0','Out','5','In1'],['11','Out','3','In1'],['12','Out','3','In1'],['3','TurnOff','12','In'],['5','Out1','7','In1'],['5','RetroSkipCleanup','1','In'],['7','Out1','1','In']]
 ck('resume_exact_scoped_native_root_edges',g(I.R7)['edges']==sorted(resume_edges),'native4.Out1→5 seam; pickup2,mode4,debug8,initcleanup10 omitted')
 ck('resume_native_return_preconditions',any(x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('days')==2 for x in walk(n(I.R7,83,'root/5')['payload']))and any(x.get('$type')=='questContentToken_ConditionType'and x.get('type')=='SideQuest_Standalone'for x in walk(n(I.R7,83,'root/5')['payload'])),'native2 game days, SideQuest_Standalone, inventory>=1 and not vehicle state83 retained')
 for edge0 in [(51,'Out1',13,'Succeeded'),(13,'Out',10,'In'),(10,'Out',66,'In'),(66,'Out',62,'In')]:ck('Skippy_native_reward_tail '+str(edge0),e(I.R7,*edge0,'root/5'),edge0)
 ck('Skippy_reward_and_real_done',wr(I.R7,66,'mq007_done',1,'root/5')and'QuestRewards.mq007_done'in str(n(I.R7,10,'root/5')['payload']),'native reward then done, no new private payout')
 # Freeze previous SC3 results by current raw hash instead of repeating ambient investigations.
 old=read(I.W/'diagnostics/skippy_vanilla_wiki_audit_20261028_01/assessment_01.json')
 ck('SC3_reused_exact_audited_resource',I.IDX[I.SC3]['sha256']==old['sc3_owner_sha256'],'ambient source exact E9A06A80…156B19; old observed speech does not prove return quest')
 s23=scripts['PTFR_SideJobsS23.reds']
 for needle in ['(i == 1 || i == 8) && this.Fact("PTFRSKIP_SC3_Claimed") == 1 && this.Fact("PTFRSKIP_SC3_Stopped") == 0','this.Fact("PTFRS23_MQ007_ModeTalkConfirmed") == 1 && this.Read(8).valid','qs.SetFactStr("PTFRSKIP_SC3_Stop", 1);']:
  ck('SC3_story_retirement_current_driver '+needle,needle in s23,needle)
 # Later Regina retrieval lives in an original bugfix owner, separate from S23 return.
 bf7='base\\quest\\bugfixing\\minor_quests\\mq007\\mq007_quest_bugfixes.questphase'
 ck('Regina_later_reacquisition_native_owner_separate',wr(bf7,5,'mq007_skippy_re_acquiring_done',1,'root/14')and all(e(bf7,*x,'root/14/3')for x in [(4,'Out',5,'Active'),(5,'Out',6,'Active'),(6,'Out',7,'Active')]),'nativebugfix14: done wait→context+office wait→variant→three Regina messages; no new S23 owner for it')
 # Stadium Love actual competition, tally, drink, outcomes and independent combat alternative.
 sc='base\\quest\\minor_quests\\mq008\\phases\\mq008_02_shooting_contest.questphase';scs='base\\quest\\minor_quests\\mq008\\scenes\\mq008_02_shooting_contest.scene';cl='base\\quest\\minor_quests\\mq008\\phases\\mq008_cleanup.questphase'
 for x in [(2,'combat_out',11,'In1'),(2,'no_competition_out',8,'In1'),(2,'quest_fails',8,'In2'),(3,'Out1',8,'In1'),(3,'quest_fails',8,'In2'),(3,'v_offends_boss_out',11,'In1'),(3,'v_won_and_left_out',8,'In2'),(42,'Out1',43,'In1'),(8,'Out1',43,'In2')]:ck('Stadium_native_outcome '+str(x),e(I.N8,*x),x)
 ck('Stadium_root_support',M[I.N8]['root_prefabs']==['#mq008_pr_6th_street_hood'],M[I.N8]['root_prefabs'])
 f,j,inv=seed(n(I.P8,1002)['payload']['condition'])
 ck('Stadium_second_authorized_route',ev(n(I.P8,1002)['payload']['condition'],f|{'PTFRS2_MQ008_AuthorizedRoute':2,'mq008_active':1,'mq008_quest_comm_on':1},j,inv),'route2 with bounded active/quest_comm_on1, untouched journals and progress facts')
 for bout,done,slot in [(3,102,1),(27,101,2),(49,100,3),(70,99,4)]:
  gp='root/48';ck('Stadium_round_completion '+str(slot),wr(sc,done,'mq008_shooting'+str(slot)+'_done',1,gp)and e(sc,bout,'Out1',done,'In',gp)and e(sc,done,'Out',107,'In'+str(slot),gp),{'round_phase':bout,'done':done,'score_join':107})
  tally=[(i,node)for i,node in g(sc,gp+'/'+str(bout))['nodes'].items()if any(x.get('factName')=='mq008_final_score'for x in node['writes'])]
  ck('Stadium_native_tally_nonreset '+str(slot),bool(tally)and all(x['value']==1 and x['setExactValue']==0 for i,node in tally for x in node['writes']if x.get('factName')=='mq008_final_score'),{'tally_nodes':[i for i,node in tally],'count':len(tally),'increment':1})
 for prod,writer in [(77,4264),(90,4267),(142,4270),(156,4273)]:ck('Stadium_authored_drink '+str(writer),wr(scs,writer,'player_drunk',1,'scene')and e(scs,prod,'0:0',writer,'0:1','scene'),{'native_scene_section':prod,'drunk_writer':writer})
 ck('Stadium_native_winning_score',n(I.N8,16,'root/42')['reads'][0]['factName']=='mq008_final_score'and n(I.N8,16,'root/42')['reads'][0]['comparisonType']=='Greater'and n(I.N8,16,'root/42')['reads'][0]['value']==43,'score>43, no guessed threshold')
 ck('Stadium_reward_pickup_native_inventory_alias',any(x.get('$type')=='questInventory_ConditionType'and x.get('itemID',{}).get('$value')=='Items.mq008_golden_knuckledusters'and x.get('quantity')==1 for x in walk(n(I.N8,7,'root/42')['payload'])),'internal item name is literal evidence; weapon definition/name not resolved')
 for ni,token in [(69,'QuestRewards.mq008_shooting_win'),(70,'QuestRewards.mq008_done'),(85,'QuestRewards.mq008_shooting_win')]:ck('Stadium_native_reward '+str(ni),token in str(n(sc,ni)['payload']),{'reward_node':ni,'pointer':token})
 ck('Stadium_native_win_loss_rewards_connected',e(sc,68,'True',69,'In')and e(sc,68,'False',70,'In')and e(sc,48,'v_won_and_left_out',85,'In'),'native outcomes not flattened')
 for ni,f,v in [(2,'mq008_active',0),(3,'mq008_done',1),(28,'mq008_active',0),(29,'mq008_done',1),(14,'mq008_quest_comm_on',0),(39,'mq008_quest_comm_on',0),(65,'mq008_quest_item_tags_cleaned',1)]:ck('Stadium_cleanup_receipt '+str(ni),wr(cl,ni,f,v),f)
 # Fortunate Son original Bob/Panam/camp, medical choice and message lifecycle.
 brief='base\\quest\\minor_quests\\mq021\\phases\\mq021_briefing.questphase';out='base\\quest\\minor_quests\\mq021\\phases\\mq021_outcome.questphase';meet='base\\quest\\minor_quests\\mq021\\phases\\mq021_hospital_meeting.questphase';hs='base\\quest\\minor_quests\\mq021\\scenes\\mq021_02_hospital_meeting.scene';ending='base\\quest\\minor_quests\\mq021\\scenes\\mq021_03_ending.scene'
 ck('FortunateSon_native_sq027_done_ancestor',n(I.P21,56)['reads'][0]['factName']=='sq027_done'and n(I.P21,56)['reads'][0]['comparisonType']=='Greater','original Panam job completion, plus q103_rogue/q104/sq004')
 for x in [(2,'Out',90,'In'),(90,'Out',115,'In'),(115,'False',96,'In1'),(115,'True',114,'Inactive'),(96,'sq027_failed',114,'Inactive'),(96,'Out1',103,'In'),(103,'Out',97,'In1'),(97,'Out1',98,'In1'),(98,'Out1',99,'In1'),(98,'combat_escaped',99,'Skip_combat'),(99,'Out1',110,'In'),(110,'Out',104,'In'),(104,'Out',105,'In'),(105,'Out',112,'In')]:ck('FortunateSon_native_branch '+str(x),e(I.N21,*x),x)
 ck('FortunateSon_Bob_default_lease',wr(brief,14,'bob_default_on',0)and wr(I.N21,7,'bob_default_on',1,'root/102'),'original briefing suppresses Bob default; final native cleanup restores')
 ck('FortunateSon_phase_support',M[brief]['root_prefabs']==['#mq021_pr_camp']and M[meet]['root_prefabs']==M[out]['root_prefabs']==['#mq021_pr_hospital','#mq021_pr_camp'],'empty parent root does not remove child support')
 options=n(hs,33,'scene')['payload']['options'];net=options[2]['bluelineCondition']['type']['scriptCondition']
 ck('FortunateSon_medical_choice_build_prerequisite',[x['caption']['$value']for x in options]==['let_kill','dont_kill','net']and net['buildId']['$value']=='PlayerBuilds.Netrunner'and net['comparisonType']=='CO_GreaterEq'and net['difficulty']=='MEDIUM'and net['questAssignment']['$value']=='DeviceContentAssignment.mq021',options)
 for prod,writer in [(78,42),(84,42),(246,45)]:ck('FortunateSon_native_happy_outcome '+str(prod),wr(hs,writer,'mq021_happy_ending',1,'scene')and any(x[0]==str(prod)and x[2]==str(writer)for x in g(hs,'scene')['edges']),{'scene_section':prod,'native_writer':writer})
 for x in [(62,'True',88,'In'),(62,'False',63,'In'),(88,'Out',65,'In'),(63,'Out',65,'In'),(65,'Out',67,'Succeeded'),(67,'Out',68,'Active'),(68,'Out',66,'In'),(66,'Out',47,'Succeeded'),(65,'Out',80,'In'),(80,'Out',108,'Inactive'),(108,'Out',79,'In'),(79,'CutSource',66,'CutDestination')]:ck('FortunateSon_real_message_ack_cleanup '+str(x),e(out,*x),x)
 ck('FortunateSon_real_read_ack',any(x.get('$type')=='questJournalEntryVisited_ConditionType'and x['visited']==1 for x in walk(n(out,66)['payload'])),'actual message visited condition, not fabricated done fact')
 ck('FortunateSon_native_reward_pointer','QuestRewards.mq021_minor_done'in str(n(I.N21,110)['payload']),'root110 native reward, no private duplicate')
 # Scene declarations are inspected without claiming the target world records resolve.
 scene_inventory=[]
 for d in [x for x in M if x.endswith('.scene')]:
  meta=M[d]['metadata'];actors=[{'id':x['actorId']['id'],'name':x['actorName'],'acquisition':x['acquisitionPlan'],'binding':x.get(x['acquisitionPlan']+'Params',{}).get('reference',{}).get('$value')}for x in meta.get('actors',[])]
  scene_inventory.append({'depot':d,'sha256':I.IDX[d]['sha256'],'actors':actors,'workspots':len(meta.get('workspots',[])),'workspot_instances':len(meta.get('workspotInstances',[])),'entries':g(d,'scene')['entries'],'status':'DECLARATIONS_PINNED_TARGET_DEFINITIONS_NOT_RESOLVED'})
 for d,names,counts in [('base\\quest\\minor_quests\\mq007\\scenes\\mq007_04_skippy_return.scene',['Skippy','Reggie','Daisy','SkippyVoice'],(4,7)),(hs,['Doctor','Security_01','van'],(8,18)),('base\\quest\\minor_quests\\mq021\\scenes\\mq021_01_briefing.scene',['Bob','Wife','Scooter'],(4,5))]:
  meta=M[d]['metadata'];ck('exact_native_scene_cast '+d,[x['actorName']for x in meta['actors']]==names and(len(meta['workspots']),len(meta['workspotInstances']))==counts,{'names':names,'workspots_and_instances':counts})
 # Communication census includes separate original corrective handlers; no blanket phone proof.
 communications={}
 for q,folder in [('mq007_smartgun','mq007'),('mq008_party','mq008'),('mq021_guide','mq021')]:
  ds=[d for d in M if '\\'+folder+'\\'in d];hits=[];facts=[]
  for d in ds:
   for gp,gr in M[d]['graphs'].items():
    for i,node in gr['nodes'].items():
     if node['sms']or'Phone'in node['type']:hits.append({'depot':d,'graph':gp,'node':i,'paths':node['journal_paths'],'in':[x for x in gr['edges']if x[2]==i],'out':[x for x in gr['edges']if x[0]==i]})
     facts += [{'depot':d,'graph':gp,'node':i,'fact':x}for x in node['reads']+node['writes']if x.get('factName','').startswith(('holo_','audio_','phonecall_'))]
  ck('No_local_holocall_requests '+q,not facts,{'closure':ds,'literal_phone_fact_count':len(facts)});communications[q]={'closure':ds,'message_nodes':hits,'holocall_fact_nodes':facts}
 # Real decoded-resource mutations, all in memory.
 def raw(d):return Resource(copy.deepcopy(read(I.IDX[d]['json'])))
 def rn(r,gp,ni):
  gr=r.d(r.root['graph'])
  for part in gp.split('/')[1:]:gr=r.d(next(r.d(x)for x in gr['nodes']if str(r.d(x)['id'])==part)['phaseGraph'])
  return next(r.d(x)for x in gr['nodes']if str(r.d(x)['id'])==str(ni))
 def edit_fact(r,gp,ni,name,value):
  stack=[rn(r,gp,ni)];seen=set()
  while stack:
   x=r.d(stack.pop())
   if not isinstance(x,(dict,list))or id(x)in seen:continue
   seen.add(id(x))
   if isinstance(x,dict):
    if x.get('factName')==name:x['value']=value;return
    stack+=list(x.values())
   else:stack+=x
  raise AssertionError(name)
 def cut(r,gp,a,s,b,t):
  an,bn=rn(r,gp,a),rn(r,gp,b);sh=next(x for x in an['sockets']if r.d(x)['name']['$value']==s);dh=next(x for x in bn['sockets']if r.d(x)['name']['$value']==t)
  for node in [an,bn]:
   for h in node['sockets']:
    sd=r.d(h);sd['connections']=[ch for ch in sd.get('connections',[])if not(r.hid(r.d(ch)['source'])==r.hid(sh)and r.hid(r.d(ch)['destination'])==r.hid(dh))]
 def mutation(name,d,change,predicate):
  r=raw(d);change(r);m=r.normalize();ok=not predicate(m);mut.append({'name':name,'source':d,'sha256':I.IDX[d]['sha256'],'detected':ok,'actual_decoded_copy':True,'files_mutated':False});ck('Mutation '+name,ok,d)
 mutation('Skippy_exact_counter_changed',I.B7,lambda r:edit_fact(r,'root',1002,'mq007_skippy_enemies_total',97),lambda m:m['graphs']['root']['nodes']['1002']['payload']==n(I.B7,1002)['payload'])
 mutation('Skippy_return_reward_ack_route_removed',I.R7,lambda r:cut(r,'root/5',51,'Out1',13,'Succeeded'),lambda m:['51','Out1','13','Succeeded']in m['graphs']['root/5']['edges'])
 mutation('Stadium_round4_missing_completion',sc,lambda r:cut(r,'root/48',70,'Out1',99,'In'),lambda m:['70','Out1','99','In']in m['graphs']['root/48']['edges'])
 mutation('Stadium_changed_score_threshold',I.N8,lambda r:edit_fact(r,'root/42',16,'mq008_final_score',42),lambda m:m['graphs']['root/42']['nodes']['16']['reads'][0]['value']==43)
 mutation('Stadium_missing_root_support',I.N8,lambda r:r.root.__setitem__('phasePrefabs',[]),lambda m:m['root_prefabs']==['#mq008_pr_6th_street_hood'])
 mutation('FortunateSon_missing_message_cleanup',out,lambda r:cut(r,'root',79,'CutSource',66,'CutDestination'),lambda m:['79','CutSource','66','CutDestination']in m['graphs']['root']['edges'])
 mutation('FortunateSon_missing_camp_support',meet,lambda r:r.root.__setitem__('phasePrefabs',[]),lambda m:m['root_prefabs']==['#mq021_pr_hospital','#mq021_pr_camp'])
 # All exact scene actors/choices/journals and literals retained as evidence, not resolved targets.
 dependencies=[]
 for q,folder in [('mq007_smartgun','mq007'),('mq008_party','mq008'),('mq021_guide','mq021')]:
  ds=[d for d in M if '\\'+folder+'\\'in d];refs=sorted({x for d in ds for x in M[d]['refs']});dependencies.append({'quest_id':q,'refs':[{'depot':x,'in_inventory':x in I.IDX,'decoded_this_batch':x in M,'status':'PINNED_DECODED'if x in M else'LITERAL_TARGET_NOT_RESOLVED'}for x in refs],'root_prefabs':{d:M[d]['root_prefabs']for d in ds if M[d]['root_prefabs']},'limits':['No world placement proof from a NodeRef literal','No TweakDB reward/item/build definition proof from a pointer','No saved executing-owner or engine scheduler proof']})
 write(O/'source_pins.json',pins);write(O/'graph_evidence.json',{d:m for d,m in M.items()if d!=I.PAR});write(O/'guard_fixtures.json',fixtures);write(O/'communications.json',communications);write(O/'dependencies.json',dependencies);write(O/'scene_inventory.json',scene_inventory)
 write(O/'tests.json',{'group':'G08','checks':tests,'mutations':mut,'total_checks':len(tests),'total_mutations':len(mut),'failed':sum(t['status']!='PASS'for t in tests),'runtime_changes':[],'reused_SC3_evidence':old})
 print(json.dumps({'output':str(O),'checks':len(tests),'mutations':len(mut),'resources':len(M),'failed':0}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);run(Path(p.parse_args().output).resolve())
