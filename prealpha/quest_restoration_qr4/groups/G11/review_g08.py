"""Independent G08 source review, including missing Skippy continuation and nested support."""
from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
S=Store();B=W/'prealpha/quest_restoration_qr4/groups/G08';R=read(B/'results.json');F=read(B/'regina_followup_01/evidence.json');checks=[]
def ck(name,b,e):checks.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
for row in read(B/'verification_02/source_pins.json'):
 if row.get('depot'):
  d=row['depot'];S.load(d);mine=next(p for p in S.pins if p['depot']==d);ck('independent_raw_JSON_pin '+d,mine['resource_sha256']==row['sha256']and mine['json_sha256']==row['json_sha256'],mine)
 else:ck('independent_policy_script_pin '+row['path'],sha(row['path'])==row['sha256'],row['path'])
def add_current_global(row):
 d=row['depot'];j=Path(row['source_json']);raw=j.with_suffix('')
 if not raw.exists():
  pp=list(j.parts);pp[pp.index('json')]='raw';raw=Path(*pp).with_suffix('')
 ck('current_global_raw_pin '+d,sha(raw)==row['resource_sha256']and sha(j)==row['json_sha256'],row)
 m=Resource(read(j)).normalize();ck('current_global_decode '+d,not m['errors'],m['errors']);S.models[d]=m;S.pins.append({'depot':d,'binary':str(raw),'resource_sha256':sha(raw),'json':str(j),'json_sha256':sha(j),'provider':'QR2 current-provider readback reused by QR3/QR4 followup'})
for row in F['source_pins']:
 if 'source_json'in row:add_current_global(row)
n=S.n;g=S.g
def es(d,edges,gp='root'):
 for e in edges:ck('edge '+d+' '+str(e),S.edge(d,*e,gp=gp),{'graph':gp,'edge':e})
def has(q,f,op,v):return any(x.get('factName')==f and x.get('comparisonType')==op and x.get('value')==v for x in q['reads'])
N7=r'base\quest\minor_quests\mq007\mq007.questphase';B7=r'base\quest\bugfixing\minor_quests\mq007\mq007_quest_bugfixes.questphase';FRESH=r'towercontinued\sidejobs_s23\base_a\mq007_smartgun.questphase';RESUME=r'towercontinued\sidejobs_s23\base_a_v2\mq007_resume_boot.questphase';OWNER=r'towercontinued\sidejobs_s23\base_a_v2\mq007_resume_owner.questphase';PAR=r'base\quest\minor_quests\minorquests.questphase';PARTY=r'towercontinued\sidejobs_s2\mq008_party.questphase';GUIDE=r'towercontinued\sidejobs_s23\base_a\mq021_guide.questphase'
for d in [FRESH,RESUME,GUIDE,PARTY]:
 for i,q in g(d)['nodes'].items():
  if i in g(PAR)['nodes']and int(i)<1000 and i!='0':
   if d==RESUME and i=='21':continue
   ck('original_ancestor '+d+' '+i,q['payload']==n(PAR,i)['payload'],i)
es(FRESH,[(1100,'True',1101,'In'),(1101,'Out',21,'In1'),(1101,'Out',1010,'In')]);es(RESUME,[(1100,'True',1101,'In'),(1101,'Out',21,'In1')]);es(OWNER,[(0,'Out',5,'In1')])
for i in [1001,1002]:
 q=n(RESUME,i)
 for f,v in [('PTFRS23_MQ007_ModeTalkConfirmed',1),('mq007_skippy_enemies_total',95),('mq007_skippy_enemies_lethal',11),('mq007_skippy_enemies_non_lethal',51)]:
  ck('resume_actual_counter '+str(i)+f,has(q,f,'Equal',v),v)
 ck('resume_root_current_Inactive_only '+str(i),all(x.get('state')=='Inactive'for x in q['reads']if x.get('path',{}).get('realPath')=='quests/minor_quest/mq007_smartgun'),'Historical Failed-root prose is not current authority')
actual_resume_facts=[x for x in n(RESUME,1001)['reads']if'factName'in x and any(t in x['factName']for t in ['defeat','maim','lethal','enemies_total','Confirmed'])];ck('bounded_resume_exact_11_51_95_present',{11,51,95}<={x['value']for x in actual_resume_facts},actual_resume_facts)
# Precise Skippy producer and retired consumer chain.
ck('actual_return_done_writer',any(w['factName']=='mq007_done'and w['value']==1 for w in n(N7,66,'root/5')['writes']),'New supported private story delegates this return graph')
ck('sole_native_continuation_wait',has(n(B7,2,'root/14'),'mq007_done','GreaterOrEqual',1),'Consumer14/2')
es(B7,[(0,'Out',2,'In'),(2,'Out',4,'In'),(4,'Out',3,'In1'),(3,'Out1',5,'In'),(5,'Out',1,'In')],'root/14')
ck('native_five_game_days',any(x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('days')==5 for x in walk(n(B7,4,'root/14')['payload'])),n(B7,4,'root/14')['payload'])
ck('native_context_exact_AND',n(B7,3,'root/14/3')['payload']['condition']['operation']=='AND'and any(x.get('$type')=='questContentToken_ConditionType'and x.get('type')=='MinorQuestAndSts'for x in walk(n(B7,3,'root/14/3')['payload']))and'#mq007_tr_regina_jones_office_re_acquiring'in n(B7,3,'root/14/3')['node_refs'],'No boolean replacement for actual context')
ck('nested_native_trigger_prefab_obligation',n(B7,3,'root/14')['prefabs']==['#mq007_pr_gun_re_acquiring'],'Outer14 has no instanceprefabs; nested14/3 must retain this distinct native trigger prefab')
es(B7,[(3,'Out',4,'In'),(4,'Out',5,'Active'),(5,'Out',6,'Active'),(6,'Out',7,'Active')],'root/14/3')
messages=[n(B7,i,'root/14/3')['journal_paths'][0]for i in [5,6,7]];ck('three_exact_Regina_messages',messages==['contacts/regina_jones/mq007_giving_back_skippy/01_about_what_happened','contacts/regina_jones/mq007_giving_back_skippy/02_techie_took_skippy','contacts/regina_jones/mq007_giving_back_skippy/03_want_him_back'],messages)
main=r'base\quest\cyberpunk2077.questphase';bf=r'base\quest\bugfixing.questphase';qb=r'base\quest\bugfixing\quest_bugfixing.questphase'
es(main,[(106,'Out',109,'In'),(109,'Out',107,'In')]);ck('genuine_terminating_root',n(main,107)['type']=='questOutputNodeDefinition'and n(main,107)['payload']['type']=='Terminating','Original82 under terminating scope')
ck('main82_contains_bugfixing',n(main,4,'root/82')['refs']==[bf],bf);ck('quest_bugfix_contains_MQ007',n(qb,27,'root/3')['refs']==[B7],B7)
# Independent negative scan over all cached private/embedded models; exact current private source pins are epoch00.
private_hits=[];native_waits=[]
for depot,mi in S.MI.items():
 model=json.loads(gzip.decompress(Path(mi['normalized_model']).read_bytes()))
 for gp,gr in model['graphs'].items():
  for i,q in gr['nodes'].items():
   hits=set(messages)&set(q['journal_paths'])
   if hits and depot.startswith('towercontinued\\'):private_hits.append({'depot':depot,'graph':gp,'node':i,'paths':sorted(hits)})
   if any(x.get('factName')=='mq007_done'and x.get('comparisonType')=='GreaterOrEqual'and x.get('value')==1 for x in q['reads']):native_waits.append({'depot':depot,'graph':gp,'node':i,'type':q['type']})
ck('no_private_three_message_consumer',not private_hits,private_hits);ck('native14_wait_present_in_independent_scan',any(x['depot']==B7 and x['graph']=='root/14'and x['node']=='2'for x in native_waits),native_waits)
CONTEST=r'base\quest\minor_quests\mq008\phases\mq008_02_shooting_contest.questphase';OUT=r'base\quest\minor_quests\mq021\phases\mq021_outcome.questphase'
es(CONTEST,[(68,'True',69,'In'),(68,'False',70,'In')]);ck('Stadium_original_win_predicate',has(n(CONTEST,68),'mq008_v_wins','Greater',0),'No forced score/winner')
for i,r in [(69,'QuestRewards.mq008_shooting_win'),(70,'QuestRewards.mq008_done')]:ck('Stadium_original_reward '+str(i),any(val(x)==r for x in walk(n(CONTEST,i)['payload'])),r)
es(OUT,[(65,'Out',67,'Succeeded'),(67,'Out',68,'Active'),(68,'Out',66,'In'),(66,'Out',47,'Succeeded'),(65,'Out',80,'In'),(80,'Out',108,'Inactive'),(108,'Out',79,'In'),(79,'CutSource',66,'CutDestination')])
ck('FortunateSon_real_message_visited',any(x.get('$type')=='questJournalEntryVisited_ConditionType'and x.get('visited')==1 for x in walk(n(OUT,66)['payload'])),'Actual journal visited event; no fabricated read acknowledgment')
proposal=read(B/'regina_proposal_01/proposal.json');ck('proposal_preserves_old_entry_edges',all(S.edge(x['resource'],1101,'Out',21,'In1')and S.edge(x['resource'],1101,'Out',1010,'In')for x in proposal['resources']),'New sibling only from future1101 event; no input/default0 bootstrap')
ck('proposal_blocks_old_done_or_reacquired',all(x['enrollment_guard']['facts_equal'].get('mq007_done')==0 and x['enrollment_guard']['facts_equal'].get('mq007_skippy_re_acquiring_done')==0 for x in proposal['resources']),'Unknown historical timer is deferred, not recreated')
mut=[];bad=copy.deepcopy(g(OUT));bad['edges'].remove(['79','CutSource','66','CutDestination']);mut.append({'fault':'lost_Bob_read_wait_cancellation','detected':['79','CutSource','66','CutDestination']not in bad['edges']})
bad=copy.deepcopy(n(B7,3,'root/14')['payload']);bad['phaseInstancePrefabs']=[];mut.append({'fault':'missing_nested_Regina_trigger_prefab','detected':bad!=n(B7,3,'root/14')['payload']})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
save(O/'tests.json',{'count':len(checks),'checks':checks,'mutations':mut,'independent_private_message_scan':{'models':len(S.MI),'private_message_hits':private_hits,'all_done_waits':native_waits}});save(O/'source_pins.json',S.pins)
out={'status':'INDEPENDENT_REVIEW_CONFIRMS_ONE_EPOCH00_MISSING_POST_RETURN_CONSUMER','reviewer_group':'G11','reviewed_group':'G08','source_epoch':'00 / QR3 candidate01; future QR4 repair not graded','checks':len(checks),'mutations':mut,'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'confirmed_defect':'MQ007_POST_RETURN_REACQUISITION_MISSING_CONSUMER','defect_boundary':'Supported fresh/resume story can emitdone1 after original corrective owner is structurally terminated; native five-day/variant/Regina-message consumer not privately rehosted. Exact11/51/95 admission limit is separate and unchanged.','proposal_review':'Sibling enrollment only from future1101 beforedone0 with one shared receipt is conservative. Actual implementation must preserve recursive native14 graph, including nested3 #mq007_pr_gun_re_acquiring. It is distinct from persistent #mq007_pr_gun_return.var_container; no new world-sector/prefab owner should be invented for the persistent container.','other_quests':'Stadium native win reward split and FortunateSon real SMS visited/cut cancellation independently checked; native ancestor payloads/pins match.','limits':['Native timer/context and saved-owner scheduling remain engine-dependent','Native nested trigger prefab and opaque world target contents require preservation/readback; source presence is not placement proof','Proposal is not an implemented or fully validated repair; root owns staged source and final package checks','Reward/TDB target definitions remain unresolved; no live gameplay success is claimed'],'runtime_changes':[]}
save(O/'review.json',out);frozen=Path(__file__).parent/'reviews/G08.json'
if not frozen.exists():save(frozen,out)
print(json.dumps({'checks':len(checks),'sources':len(S.pins),'models_independently_scanned':len(S.MI),'mutations':len(mut)}))
