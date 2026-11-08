"""Rancho native branch, journal, lifecycle and binding controls."""
from pathlib import Path
import sys,copy,argparse
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));import source_inputs as I
from common import read,write,sha,walk
from model import Resource
from verify import path
def run(O):
 assert not O.exists();M={};pins=[];tests=[];mut=[]
 def ck(name,ok,e):tests.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':e});assert ok,name
 for d in I.selected():M[d],p=I.load(d);pins.append(p)
 def find(t):return next(d for d in M if d.endswith('\\'+t))
 def g(d,p='root'):return M[d]['graphs'][p]
 def n(d,k,p='root'):return g(d,p)['nodes'][str(k)]
 def e(d,a,s,b,t,p='root'):return [str(a),s,str(b),t]in g(d,p)['edges']
 def wr(d,k,f,v,p='root'):return any(w.get('factName')==f and w.get('value')==v for w in n(d,k,p)['writes'])
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cl='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';rh=I.EXTRA[1];rs=I.EXTRA[2];ck('Union_Rogue_actual_owner',n(init,86)['refs']==[rh]and e(init,25,'Out1',86,'In1'),'Union uses Rogue, other three use Muamar');ck('Union_Rogue_cleanup',n(cl,344)['refs']==[I.EXTRA[0]],'separate native shared owner344')
 for kind,ack in [('start',41),('end',42)]:ck('Union_Rogue_real_ACK '+kind,wr(rs,ack,'holo_rogue_calls_v_'+kind+'_done',1,'scene'),'native actual scene ACK, not synthetic success')
 a2=find('sts_std_rcr_02_phase.questphase');a5=find('sts_std_rcr_05_openworld.questphase');a1=find('sts_std_rcr_01_openworld.questphase');a3=find('sts_std_rcr_03_openworld.questphase')
 cases=[(a2,'root/9/6',[(23,'Out',22,'In'),(22,'Out',30,'In')]),(a5,'root/5',[(11,'End 0',5,'In'),(11,'rejected_out',27,'Active'),(27,'Out',5,'In'),(5,'Out',7,'In'),(7,'Out',6,'In'),(32,'False',10,'In'),(32,'True',15,'In')]),(a1,'root/5',[(101,'False',133,'In'),(101,'True',131,'In'),(131,'False',112,'In'),(131,'True',113,'In'),(133,'False',134,'In'),(133,'True',132,'In'),(129,'False',130,'In'),(129,'True',120,'In'),(122,'End 0',17,'In'),(17,'Out',72,'Succeeded'),(147,'Out',153,'In'),(153,'Out',71,'In')]),(a3,'root/5',[(74,'False',72,'In'),(74,'True',116,'In'),(72,'Out',116,'In'),(113,'True',112,'Active'),(113,'False',114,'Active'),(116,'Out',58,'In'),(127,'True',128,'In'),(128,'Out',85,'In')])]
 for d,p,edges in cases:
  for edge in edges:ck('native_outcome '+d+p+str(edge),e(d,*edge,p),edge)
 ck('GoingAway_no_reward_on_native_death',n(a3,74,'root/5')['reads'][0]['factName']=='sts_std_rcr_03_flavio_dead'and e(a3,74,'True',116,'In','root/5'),'dead Flavio bypasses reward72 but still reaches native after-call cleanup')
 ck('Union_separate_outcome_predicates',n(a1,101,'root/5')['reads'][0]['factName']=='rcr_01_deliver_failed'and all(n(a1,x,'root/5')['reads'][0]['factName']=='rcr_01_hurt_civilians'for x in [129,131,133]),'failed-delivery/kill/subdue/casualties remain separate native debrief receipts')
 # Actual Active omitted objective is explicitly investigated, never relabelled cleanup-only.
 gr=g(a3,'root/4');without=copy.deepcopy(gr);without['edges']=[ed for ed in gr['edges']if ed[0]!='197'];ck('GoingAway_unlisted_Active_objective_start_dominance',bool(path(gr,0,195))and path(without,0,195)is None and wr(a3,197,'rcr_03_start',1,'root/4'),{'objective':'get_flavio_out_of_town','active_node':195,'normal_path':path(gr,0,195),'without_start_writer_path':None,'limit':'native current history fenced by start fact; external/historical writers still conditional'})
 admissions=read(H/'verification_02/admission.json');omissions=[]
 for a in admissions:
  for jp,rows in a['omitted_native_journal'].items():
   active=[r for r in rows if r['class']=='gameJournalQuestObjective'and any(ed[3]=='Active'for ed in r['incoming'])];expected=a['quest_id']=='sts_std_rcr_03'and jp.endswith('/get_flavio_out_of_town');ck('exact_omitted_Active_writer_classification '+jp,bool(active)==expected,rows);omissions.append({'quest_id':a['quest_id'],'path':jp,'rows':rows,'classification':'native Active writer195 dominated by start197; old/external provenance conditional'if expected else'locally cleanup-only objective or mappin; exact class recorded'})
 ck('GoingAway_saved_alias_preserved',any(r['id']=='sts_std_rcr_03'and r['depot'].endswith('_entry_alias1.questphase')for r in I.RECIPES),'salted installed entry path is persisted baseline; no cosmetic rename')
 # Original LOOP retains a Union waiter with no outgoing credit edge; do not invent one.
 ck('Union_native_LOOP_credit_branch_is_disconnected',any(r.get('factName')=='rcr_01_finished'for r in n(I.LOOP,7,'root/2/3')['reads'])and not any(ed[0]=='7'for ed in g(I.LOOP,'root/2/3')['edges'])and not any(r['id']=='sts_std_rcr_01'and r['kind']=='credit'for r in I.RECIPES),'Original LOOP contains rcr01 finished waiter7 but NO outgoing credit edge; no native active credit route to invent')
 b3=find('sts_std_rcr_03_bugfixing.questphase');ck('GoingAway_old_force_end_is_snapshot_migration',n(b3,4,'root/8')['type']=='questConditionNodeDefinition'and n(b3,16,'root/8')['type']=='questConditionNodeDefinition'and n(b3,18,'root/8')['type']=='questConditionNodeDefinition','old CYB618414 path tests already Succeeded talk_hayashi and phase not Succeeded/Failed; not a future listener waiting a fresh quest')
 ck('GoingAway_old_nomad_fix_is_snapshot_and_normal_writer_exists',n(b3,14,'root/37')['type']=='questConditionNodeDefinition'and wr(a3,44,'rcr_03_nomad_scene_concluded',1,'root/3/110'),'old CYB662871 tests already Succeeded talk_to_nomad before old scene/timer fix; native current normal completion writer44 retained')
 b1=find('sts_std_rcr_01_bugfixing.questphase');bugscope=[]
 for q in I.Q:
  ds=[d for d in M if q in d and d.endswith('_bugfixing.questphase')];bugscope.extend({'quest_id':q,'depot':d,'root_prefabs':M[d]['root_prefabs'],'graphs':M[d]['graphs'],'classification':'exact source retained; patch guards, immediate conditions and future waits distinguished, no unfiltered replay'}for d in ds)
 # Stock definitions are limited captures; missing Dixon pointer is already separately classified UNKNOWN.
 stock={};assets={}
 for q in I.Q:
  p=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');s=read(p);pins.append({'path':str(p),'sha256':sha(p)});targets=[r for r in s['targets']if any(a.startswith('QuestRewards.'+q)for a in r.get('requested_aliases',[]))];ck('stock_reward_record_exists '+q,bool(targets)and all(t['exists_in_stock']for t in targets),targets);stock[q]={'path':str(p),'sha256':sha(p),'targets':s['targets'],'limits':s['limits']};assets[q]=[{'depot':d,'root_prefabs':m['root_prefabs'],'metadata_sha256':m['metadata_sha256'],'actors':m['metadata'].get('actors',[]),'workspots':m['metadata'].get('workspots',[]),'props':m['metadata'].get('props',[]),'refs':[{'depot':r,'inventory':I.IDX.get(r,{'status':'NOT_IN_INVENTORY'}),'definition_decoded_here':r in M}for r in m['refs']]}for d,m in M.items()if q in d and d.startswith('base\\open_world')]
 # Meaningful copies remove the native death reward exclusion and change native debrief receipt identity.
 for label,d,p,ni,fact in [('death_reward_exclusion',a3,'root/5',74,'sts_std_rcr_03_flavio_dead'),('delivery_branch',a1,'root/5',101,'rcr_01_deliver_failed'),('Family_reward',a5,'root/5',5,'QuestRewards.sts_std_rcr_05_completion')]:
  raw=copy.deepcopy(read(next(pn['json']for pn in pins if pn.get('depot')==d)));changed=0
  for x in walk(raw):
   if label=='Family_reward'and x.get('$type')=='TweakDBID'and x.get('$value')==fact:x['$value']='QuestRewards.QR5_missing';changed+=1
   elif label!='Family_reward'and x.get('factName')==fact:x['factName']='QR5_deliberate_missing_request';changed+=1
  mm=Resource(raw).normalize();caught=mm['graphs'][p]['nodes'][str(ni)]['payload']!=n(d,ni,p)['payload'];ck('raw_fault_detected '+label,changed>0 and caught,{'depot':d,'graph':p,'node':ni,'changes':changed});fp=O/'mutations'/str(label+'.json');write(fp,raw);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'caught':caught})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'journal_omissions.json',omissions);write(O/'native_bugfix_scope.json',bugscope);write(O/'asset_bindings.json',assets);write(O/'stock_applicability.json',stock);write(O/'mutations.json',mut);print({'checks':len(tests),'mutations':len(mut),'out':str(O)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))
