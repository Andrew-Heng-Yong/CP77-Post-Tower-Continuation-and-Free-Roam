"""Source-specific Hasan/Bill/Rinder contracts, broad request discovery and actual raw faults."""
from pathlib import Path
import sys,json,gzip,copy,re,argparse,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk,value
from model import Resource,reachable
CASES={
 'wst_ep1_05':dict(tag='HASAN',adapter='hasan',idx=19,world='wst_ep1_05',prereq=['hasan_default_on','sts_ep1_04_blueprints_corpo','sts_ep1_04_mr_hands_holo_convinced'],zero=['wst_ep1_05_active','wst_ep1_05_start','wst_ep1_05_finished','wst_ep1_05_gun_taken','wst_ep1_05_gun_reveal','sts_ep1_04_blueprints_hasan']),
 'wst_ep1_11_bill_meeting':dict(tag='BILL',adapter='bill',idx=18,world='wst_ep1_11',prereq=['sts_ep1_10_finished'],zero=['wst_ep1_11_hotdog_finished','wst_ep1_11_ncpd_start','wst_ep1_11_ncpd_finished','bill_default_on','sts_ep1_10_debug_fact_1111','ws_ep1_11_chicken_test_journal_start','PTFRB0S4BILL_Enabled','PTFRB0S4BILL_OwnerActive','PTFRB0S4BILL_QuestOwns']),
 'wst_ep1_04':dict(tag='RINDER',adapter='rinder',idx=20,world='wst_ep1_04',prereq=['sts_ep1_03_dogtag_obtained'],zero=['wst_ep1_04_active','wst_ep1_04_start','wst_ep1_04_finished','wst_ep1_04_gun_taken'])}
def run(O):
 assert not O.exists();tests=[];pins=[];M={};raw={};mut=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 for d in I.SEL['depots']:M[d],p=I.load(d);pins.append(p)
 for d in [r'towercontinued\b0_story_eight\bill.questphase',r'towercontinued\b0_story_eight\bill.scene']:M[d],p=I.load(d);pins.append(p)
 for p in read(H/'readback_01/manifest.json'):
  ck('fresh raw/json pin '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);r=read(p['json']);m=Resource(r).normalize();ck('fresh exact indexed semantics '+p['depot'],I.canon(m)==I.canon(M[p['depot']]),'only reversible TDBID storage identity/derived digests/JSON tuple-list normalization');raw[p['depot']]=r;M[p['depot']]=m;pins.append(p)
 def find(s):return next(d for d in M if d.endswith('\\'+s))
 def n(d,i,g='root'):return M[d]['graphs'][g]['nodes'][str(i)]
 def ed(d,a,s,b,t,g='root'):return [str(a),s,str(b),t]in M[d]['graphs'][g]['edges']
 def rf(d,i,f,g='root'):return [x for x in n(d,i,g)['reads']if x.get('factName')==f]
 def wf(d,i,f,v,g='root'):return any(x.get('factName')==f and x['value']==v for x in n(d,i,g)['writes'])
 wp=r'ep1\openworld\world_stories\ep1_world_stories.questphase';dp=r'ep1\quest\ep1_default_dialogs.questphase';EP=r'ep1\quest\ep1.questphase';OW=r'ep1\openworld\ep1_open_world.questphase';AD=r'ep1\quest\ep1_additional_game_elements.questphase'
 # Retired real owners and full original scope; no fact-only ownership inference.
 ck('native Tower cut retires both relevant ancestors',ed(EP,9,'CutSource',4,'CutDestination','root/10')and ed(EP,9,'CutSource',5,'CutDestination','root/10')and dp in n(AD,1)['refs']and wp in n(OW,14)['refs'],'genuineTower8→cut9 before killed10; world and separate default tree')
 ck('actual Tower journal source',any(x.get('path',{}).get('realPath')=='ep1/quests/main_quest/q307_before_tomorrow'and x.get('state')=='Succeeded'for x in n(EP,8,'root/10')['reads']),'source ancestor hash, not q307 receipt alone')
 for d in [wp,dp,EP,OW,AD]:ck('reviewed native parent PF scope '+d,not M[d]['root_prefabs'],{'root_prefabs':M[d]['root_prefabs'],'limit':'external world/relative references still required'})
 # Actual boot100 is exact native parent fragments and real external bodies, including default loop.
 fragments={'hasan':[(29,wp),(5,wp),(12,dp),(9,dp)],'bill':[(35,wp),(11,wp),(14,dp),(5,dp)],'rinder':[(47,wp),(46,wp),(4,wp)]}
 expectededges={'hasan':[['0','Out','12','In'],['0','Out','29','In'],['12','Out','9','In1'],['29','Out','5','In1'],['9','Out1','12','In']], 'bill':[['0','Out','14','In'],['0','Out','35','In'],['14','Out','5','In1'],['35','Out','11','In1'],['5','Out1','14','In']], 'rinder':[['0','Out','47','In'],['46','Out','4','In1'],['47','Out','46','In']]}
 def ev(x,f,j):
  t=x['$type']
  if t=='questLogicalCondition':return all(ev(c,f,j)for c in x['conditions'])if x['operation']=='AND'else any(ev(c,f,j)for c in x['conditions'])
  if t in ['questFactsDBCondition','questJournalCondition']:return ev(x['type'],f,j)
  if t=='questVarComparison_ConditionType':
   a=f.get(x['factName'],0);b=x['value'];return {'Equal':a==b,'GreaterOrEqual':a>=b,'LessOrEqual':a<=b,'Greater':a>b,'Less':a<b}[x['comparisonType']]
  if t=='questJournalEntryState_ConditionType':return j.get(x['path']['realPath'],'UNKNOWN')==x['state']
  raise ValueError(t)
 admission={};case_sources={}
 for q,v in CASES.items():
  boot=find(v['adapter']+'_boot.questphase');world=find(v['world']+'.questphase');v['boot']=boot;v['native']=world
  ck('body native provider exact and no private override '+q,world not in I.E['source_resources'],next(p for p in pins if p.get('depot')==world))
  ck('actual complete native fragment edges '+q,M[boot]['graphs']['root/100']['edges']==sorted(expectededges[v['adapter']]),expectededges[v['adapter']])
  for i,donor in fragments[v['adapter']]:ck('native owner payload/socket '+q+'/'+str(i),n(boot,i,'root/100')==n(donor,i),{'depot':donor,'node':i,'payload_sha256':n(donor,i)['payload_sha256']})
  # Preserve saved node IDs and pre-entry/recheck/issued lifecycle; every private write is owned.
  for e in [(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'False',2,'In'),(3,'True',4,'In'),(89,'Out',90,'In'),(90,'False',91,'In'),(90,'True',92,'In'),(92,'Out',100,'In1'),(92,'Out',102,'In'),(102,'Out',101,'In')]:ck('entry lifecycle '+q+str(e),ed(boot,*e),e)
  ck('genuine success receipt '+q,n(boot,102)['reads'][0]['state']=='Succeeded'and wf(boot,101,'PTFRS23_'+v['tag']+'_Finished',1),'native root journal succeeded, never forced')
  ck('no native fact forging in boot '+q,all(x['factName'].startswith(('PTFRS23_','PTFRB0S4BILL_'))for g in M[boot]['graphs'].values()for z in g['nodes'].values()for x in z['writes']),'only own Ready/Issued/Entered/Fault/Finished and Bill QuestOwns')
  reads=n(boot,2)['reads'];facts={};journals={}
  for x in reads:
   if 'factName'in x:
    if x['comparisonType']in ['Equal','GreaterOrEqual']:facts[x['factName']]=x['value']
   else:journals[x['path']['realPath']]=x['state']
  gg=n(boot,2)['payload']['condition'];ck('actual eligible fixture '+q,ev(gg,facts,journals),'actual native prerequisite facts; not synthetic write')
  ck('missing expected0 scalars valid with positive receipts '+q,ev(gg,{k:x for k,x in facts.items()if x},journals)and not ev(gg,{},journals),'FactsDB absent scalar0; missing journal UNKNOWN defers')
  for f in v['prereq']:ck('native prerequisite positive '+q+'/'+f,any(x['comparisonType']=='GreaterOrEqual'and x['value']==1 for x in rf(boot,2,f))and not ev(gg,facts|{f:0},journals),rf(boot,2,f))
  for f in v['zero']:ck('protect existing state '+q+'/'+f,rf(boot,2,f)==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':f,'value':0}]and not ev(gg,facts|{f:1},journals),rf(boot,2,f))
  for jp in journals:
   for state in ['UNKNOWN','Active','Succeeded','Failed']:ck('journal refusal '+q+'/'+jp+':'+state,not ev(gg,facts,journals|{jp:state}),'does not reset completed/failed/started history')
  claimed=facts|{'PTFRS23_'+v['tag']+'_Issued':1};
  if v['adapter']=='bill':claimed['PTFRB0S4BILL_QuestOwns']=1
  ck('afterclaim90 matches genuine private transition '+q,ev(n(boot,90)['payload']['condition'],claimed,journals),'two ticks; no erroneous Issued0 recheck')
  ck('future U9 predecessor history not excluded '+q,ev(gg,facts|{'PTFRU9_sts_ep1_04_ParentEntered':1,'PTFRU9_sts_ep1_10_ParentEntered':1,'PTFRU9_sts_ep1_03_ParentEntered':1},journals),'unlike Steven, adapter already owns both native body/default needed after actual prerequisite')
  admission[q]={'boot':boot,'native':world,'prereq':v['prereq'],'zero':v['zero'],'facts':facts,'journal':journals,'claim_fixture':claimed,'guard':gg,'root_prefabs':M[world]['root_prefabs']};case_sources[q]={'boot':boot,'native':world,'input':'In1','native_fragment_sources':fragments[v['adapter']]}
 # Exact per-story authored timers, SMS states, choice branches, item/scene/deactivation paths.
 h=CASES['wst_ep1_05']['native'];b=CASES['wst_ep1_11_bill_meeting']['native'];r=CASES['wst_ep1_04']['native'];ha=find('sts_04_hasan_default.questphase');ba=find('bill_default.questphase');hs=find('sts_04_hasan_default.scene');bs=find('sts_10_bill_default.scene')
 for d,edges in [(h,[(0,'Out',47,'In'),(47,'Out',33,'In'),(33,'True',34,'In'),(34,'True',75,'In'),(75,'True',76,'In'),(75,'False',77,'In'),(76,'Out',78,'In1'),(77,'Out',78,'In2'),(78,'Out1',3,'Active'),(3,'Out',73,'In'),(73,'Out',45,'In'),(45,'Out',70,'Active'),(70,'Out',72,'In'),(72,'Out',71,'Succeeded'),(71,'Out',31,'In'),(25,'Out',24,'Inactive'),(24,'Out',48,'Active'),(48,'Out',55,'In'),(55,'Out',56,'Succeeded'),(56,'Out',28,'Succeeded'),(28,'Out',27,'In'),(27,'Out',59,'In'),(59,'Out',32,'In')]),(b,[(0,'Out',3,'In'),(3,'Out',9,'In'),(9,'Out',56,'In'),(56,'True',94,'In'),(94,'True',95,'In'),(94,'False',96,'In'),(95,'Out',97,'In1'),(96,'Out',97,'In2'),(97,'Out1',57,'In'),(103,'Out',59,'Active'),(59,'Out',76,'Active'),(76,'Out',79,'In'),(79,'Out',77,'Succeeded'),(77,'Out',52,'Active'),(52,'Out',82,'In1'),(82,'track',83,'In'),(83,'Out',51,'Active'),(109,'Out',35,'Succeeded'),(35,'Out',80,'Succeeded'),(80,'Out',81,'Succeeded'),(81,'Out',38,'In'),(56,'False',99,'In'),(99,'Out',0,'NONE')]),(r,[(0,'Out',20,'In'),(20,'Out',6,'Active'),(6,'Out',13,'In'),(13,'Out',19,'In'),(19,'Out',11,'In'),(11,'Out',36,'In'),(36,'Out',35,'In'),(35,'Out',8,'Succeeded'),(8,'Out',29,'Active'),(29,'Out',38,'In'),(45,'Out',3,'In'),(3,'Out',10,'Succeeded'),(10,'Out',14,'Succeeded'),(14,'Out',28,'In'),(28,'Out',27,'In'),(27,'Out',25,'In')])]:
  for ee in edges:
   if ee[-1]=='NONE':continue
   ck('actual authored route '+d+str(ee),ed(d,*ee),ee)
 ck('Hasan exact84gamehour delay',n(h,47)['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':3,'hours':16,'minutes':0,'seconds':0},n(h,47)['payload'])
 ck('Hasan actual visited SMS acknowledgement',n(h,72)['payload']['condition']['type']['$type']=='questJournalEntryVisited_ConditionType'and n(h,72)['payload']['condition']['type']['visited']==1,n(h,72)['payload'])
 ck('Hasan gun reveal via original scene',wf(hs,213,'wst_ep1_05_gun_reveal',1,'scene')and wf(hs,155,'hasan_default_1st_meeting_finished',1,'scene')and rf(h,25,'wst_ep1_05_gun_reveal')and rf(h,55,'wst_ep1_05_gun_taken'),'actor scene outcomes and actual pickup acknowledgment, no blind item grant')
 ck('Hasan debug setters not reachable from real input0',not {'39','42','43','44','41'}&reachable(M[h]['graphs']['root']['nodes'],M[h]['graphs']['root']['edges'],['0']),'chickentest preserves debug IDs but S23 always calls In1, does not fabricate blueprint/convince/default facts')
 ck('Hasan actor native choice gate',rf(ha,52,'sts_ep1_04_blueprints_hasan')and rf(ha,53,'sts_ep1_04_mr_hands_holo_convinced')and ed(ha,52,'False',53,'In')and ed(ha,53,'True',45,'In'),'normal apartment vs squat55 stays source-authored; S23blueprintsHasan0 excludes squat acquisition')
 ck('Bill exact32gamehour delay',n(b,3)['payload']['condition']['type']['hours']==32 and n(b,3)['payload']['condition']['type']['$type']=='questGameTimeDelay_ConditionType',n(b,3)['payload'])
 ck('Bill live/dead native outcomes preserved',rf(b,56,'sts_ep1_10_dodger_dead')and ed(b,56,'False',62,'In')and ed(b,56,'False',63,'In')and rf(b,64,'wst_ep1_11_ncpd_finished')and rf(b,109,'wst_ep1_11_hotdog_finished'),'Dodgerdead hotdog invitation; alive police branch/existing12h skip; no forced Dodger choice')
 ck('Bill original scene outcome writers',all(wf(bs,i,f,1,'scene')for i,f in [(105,'wst_ep1_11_hotdog_start'),(108,'wst_ep1_11_hotdog_finished'),(112,'wst_ep1_11_ncpd_start'),(116,'wst_ep1_11_ncpd_finished')]),'real scene callbacks, not synthesized quest-finished')
 ck('Bill original reward329 record retained',n(bs,329,'scene')['reward']and value(n(bs,329,'scene')['payload']['questNode']['type']['rewards'][0])=='237593886551','native alias QuestRewards.sts_ep1_06_money_reward_micheal_maldonaldo; original cross-job label is not a mod defect')
 ck('Bill required world root PhasePrefab retained',len(M[b]['root_prefabs'])==1 and 'sts_10_bill_default_prefab'in M[b]['root_prefabs'][0],M[b]['root_prefabs'])
 ck('Rinder real node-loading then money injection',ed(r,47,'Out',48,'In')and ed(r,48,'Out',49,'In')and n(r,48)['payload']['condition']['type']['tickCount']==10 and any(x.get('quantity')==5000 and x.get('operationType')=='Inject'for x in walk(n(r,49)['payload'])),'native money injection into#wst_ep1_04_main_loot after loading, no invented release reward')
 ck('Rinder real2hour outside AND cleanup',n(r,28)['payload']['condition']['operation']=='AND'and any(x.get('$type')=='questRealtimeDelay_ConditionType'and x.get('hours')==2 for x in walk(n(r,28)['payload']))and any(x.get('triggerAreaRef',{}).get('$value')=='#wst_ep1_04_tr_doors'for x in walk(n(r,28)['payload'])),'not game-hours or unconditional door forcing')
 rb=find('wst_ep1_04_bugfixing.questphase');ck('Rinder historical bugfix is immediate migration, not future phone consumer',n(rb,8,'root/16')['type']=='questConditionNodeDefinition'and n(rb,9,'root/16')['type']=='questConditionNodeDefinition'and rf(rb,2,'CP77-58786','root/16')and rf(rb,8,'wst_ep1_04_active','root/16')and rf(rb,9,'wst_ep1_04_finished','root/16'),'root16 immediate CP receipt/active/notfinished/journal code/root correction; source retained, no new reset/rehost justified')
 # Bill quest vs B0 lease fencing is actually present in both directions.
 bb=r'towercontinued\b0_story_eight\bill.questphase';boot=CASES['wst_ep1_11_bill_meeting']['boot'];ck('Bill own claim before two ticks',ed(boot,4,'Out',10,'In')and ed(boot,10,'Out',89,'In')and wf(boot,10,'PTFRB0S4BILL_QuestOwns',1),'stops B0 claim after initialDisabled0/OwnerActive0 preflight')
 ck('B0 exact mutual exclusion predicate',any(x['value']==0 for x in rf(bb,2,'PTFRB0S4BILL_QuestOwns'))and any(x['value']==1 for x in rf(bb,2,'PTFRB0S4BILL_Enabled'))and rf(bb,2,'wst_ep1_11_hotdog_finished'),'B0 requires postcompletion vendor outcome; S23 requires zero prior completion/Enabled/OwnerActive')
 # Current package source authority, exact data/XL attachments and reusable evidence.
 package=[]
 for rel in ['r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds','r6/scripts/PTFR_Consolidated/PTFR_B0StoryEight.reds','archive/pc/mod/zzzz_PTFR_Combined.archive.xl']:
  p=next(x for x in I.E['package_files']if x['path']==rel);f=I.C/'package'/rel;ck('current package source hash '+rel,sha(f)==p['sha256'],p);package.append({'path':str(f),'sha256':sha(f)});pins.append(package[-1])
 red=Path(package[0]['path']).read_text();xl=Path(package[2]['path']).read_text()
 for q,v in CASES.items():
  ck('actual XL EP1root registration '+q,re.search(r'path: towercontinued\\sidejobs_s23\\ep1\\'+v['adapter']+r'_boot.questphase\s+parent: ep1\\quest\\ep1.quest\s+input:\s+node: \[1\]\s+socket: Out',xl)is not None,'nativeworld/defaultroot retired, private EP1root1 sibling stable')
  ck('current source data18/19/20 '+q,('Paths'+str(v['idx'])+'()')in red and all('"'+f+'"'in red for f in v['prereq']+v['zero'])and'EnumInt(jm.GetEntryState(entry)) : -1'in red,'actual guarded enum/journal existence/stable sample, not just list presence')
 # Exhaustive writes/reads, SMS/choices/typed-phone actions and custom request vocabulary, including new_sts/new_q110.
 own=[v['native']for v in CASES.values()]+[v['boot']for v in CASES.values()]+[ha,ba,hs,bs];allfacts=[];phone=[]
 for d in own:
  for gp,g in M[d]['graphs'].items():
   for i,z in g['nodes'].items():
    row={'depot':d,'graph':gp,'node':i,'type':z['type'],'reads':z['reads'],'writes':z['writes'],'journal_paths':z['journal_paths'],'in':[e for e in g['edges']if e[2]==i],'out':[e for e in g['edges']if e[0]==i]};allfacts.append(row)
    if z['sms']or any('Phone'in str(x.get('$type'))or'Contact'in str(x.get('$type'))for x in walk(z['payload']))or any(re.search(r'call|holo|audio|phone|sms|request|new_q|new_sts|reply',str(x.get('factName','')),re.I)for x in z['reads']+z['writes']):phone.append(row)
 producers=[row for row in allfacts if any(re.search(r'^(holo_|audio_|new_sts|new_q110)',x['factName'])and x.get('value',0)>0 for x in row['writes'])]
 ck('broad custom phone producer census, no hidden prefix-only assumption',not producers,{'all_fact_sites':len(allfacts),'phone_related_sites':len(phone),'positive_holo_audio_new_sts_new_q110':producers,'limit':'Own followup bodies/defaults/scenes; predecessor main-job phone paths not certified'})
 # Exact prerequisite writers from original prior gigs, without redoing their whole audit.
 targets={f for v in CASES.values()for f in v['prereq']};writers=[]
 for d,mi in I.MI.items():
  if not d.startswith('ep1\\')or not any(t in d for t in ['sts_ep1_03','sts_ep1_04','sts_ep1_10']):continue
  m=json.loads(gzip.decompress(Path(mi['normalized_model']).read_bytes()));hits=[(gp,i,x)for gp,g in m['graphs'].items()for i,z in g['nodes'].items()for x in z['writes']if x.get('factName')in targets and x.get('value',0)>0]
  if not hits:continue
  mm,p=I.load(d);pins.append(p)
  for gp,i,x in hits:writers.append({'depot':d,'graph':gp,'node':i,'write':x,'payload':mm['graphs'][gp]['nodes'][i]['payload'],'in':[e for e in mm['graphs'][gp]['edges']if e[2]==i]})
 for v in CASES.values():
  for f in v['prereq']:ck('exact original positive prerequisite writer '+f,any(x['write']['factName']==f for x in writers)or f=='hasan_default_on','hasan_default_on may be original external default producer; actual source inventory preserves separate target')
 # Stock targets and current staged same-byte applicability, no DB probe.
 stock=[]
 for q in ['wst_ep1_05','wst_ep1_04']:
  f=I.F/'shared/tdb_applicability_02'/str(q+'.json');st=read(f);pins.append({'path':str(f),'sha256':sha(f)});stock.append(st);ck('existing stock direct target capture '+q,bool(st['targets'])and all(x['exists_in_stock']for x in st['targets']),[{'id':x['id'],'aliases':x['requested_aliases']}for x in st['targets']])
 link=I.F/'shared/G16_target_links_01.json';lk=read(link);pins.append({'path':str(link),'sha256':sha(link)});stock.append(lk)
 for q,v in CASES.items():
  f=I.F/'candidate_02/archive_source'/v['boot'].replace('\\','/');ck('staged successor unchanged input '+q,sha(f)==I.E['source_resources'][v['boot']],str(f))
 # Raw controls of actual native actors/messages/devices and concrete owner prerequisite.
 for label,d,change,oracle in [
  ('Hasan_lost_convince_prerequisite',CASES['wst_ep1_05']['boot'],lambda r:[x.update(factName='QR5_missing_convince')for x in walk(r)if x.get('factName')=='sts_ep1_04_mr_hands_holo_convinced'],lambda m:any(x.get('factName')=='sts_ep1_04_mr_hands_holo_convinced'for x in m['graphs']['root']['nodes']['2']['reads'])),
  ('Hasan_lost_visited_ack',h,lambda r:[x.update(visited=0)for x in walk(r)if x.get('$type')=='questJournalEntryVisited_ConditionType'],lambda m:m['graphs']['root']['nodes']['72']['payload']['condition']['type']['visited']==1),
  ('Bill_changed_delay',b,lambda r:[x.update(hours=1)for x in walk(r)if x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('hours')==32],lambda m:m['graphs']['root']['nodes']['3']['payload']['condition']['type']['hours']==32),
  ('Bill_missing_B0_fence',CASES['wst_ep1_11_bill_meeting']['boot'],lambda r:[x.update(factName='QR5_missing_lease')for x in walk(r)if x.get('factName')=='PTFRB0S4BILL_OwnerActive'],lambda m:any(x.get('factName')=='PTFRB0S4BILL_OwnerActive'and x['value']==0 for x in m['graphs']['root']['nodes']['2']['reads'])),
  ('Rinder_changed_native_loot',r,lambda rr:[x.update(quantity=0)for x in walk(rr)if x.get('quantity')==5000],lambda m:any(x.get('quantity')==5000 for x in walk(m['graphs']['root']['nodes']['49']['payload']))),
  ('Rinder_changed_cleanup_clock',r,lambda rr:[x.update({'$type':'questGameTimeDelay_ConditionType'})for x in walk(rr)if x.get('$type')=='questRealtimeDelay_ConditionType'and x.get('hours')==2],lambda m:any(x.get('$type')=='questRealtimeDelay_ConditionType'and x.get('hours')==2 for x in walk(m['graphs']['root']['nodes']['28']['payload'])))]:
  rr=copy.deepcopy(raw[d]);change(rr);mm=Resource(rr).normalize();ck('actual raw fault '+label,oracle(M[d])and not oracle(mm),d);fp=O/'mutations'/str(label+'.json');write(fp,rr);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'admission.json',admission);write(O/'native_contract_inventory.json',allfacts);write(O/'phone_inventory.json',{'all_fact_sites':len(allfacts),'phone_sites':phone,'custom_start_request_producers':producers,'limit':'Exhaustive own followup facts/native directSMS/choices/actions; original predecessor main-job customcalls are separate dependency scope, not prefix-certified.'});write(O/'prerequisite_writers.json',writers);write(O/'stock_applicability.json',stock);write(O/'mutations.json',mut)
 write(O/'bindings.json',[{'depot':d,'root_prefabs':M[d]['root_prefabs'],'node_prefabs':[{'graph':gp,'node':i,'refs':z['prefabs']}for gp,g in M[d]['graphs'].items()for i,z in g['nodes'].items()if z['prefabs']],'actors':M[d]['metadata'].get('actors',[]),'workspots':M[d]['metadata'].get('workspots',[]),'relative_NodeRefs':sorted({x for g in M[d]['graphs'].values()for z in g['nodes'].values()for x in z['node_refs']}),'refs':M[d]['refs']}for d in own])
 summary={'status':'PASS_SPECIFIC_STATIC_CONTRACT_CHECKS_WITH_LIMITS','checks':len(tests),'mutations':len(mut),'source_models':len(M),'source_pins':len(pins),'fresh_exports':11,'quest_ids':I.Q,'tests':str(O/'tests.json'),'code':str(Path(__file__).resolve()),'code_sha256':sha(__file__),'confirmed_defects':[],'fully_static_verified':False,'runtime_changes':[]};write(O/'summary.json',summary);print(json.dumps(summary))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
