"""Source-specific second Arroyo outcomes, shared phones and bindings."""
import sys,copy,argparse,json
from pathlib import Path
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
 init='towercontinued\\gig_phone_u9\\fixer_initializer.questphase';cleanup='towercontinued\\gig_phone_u9\\fixer_cleanup.questphase';rh=I.EXTRA[5];rs=I.EXTRA[6];rc=I.EXTRA[4];kh=I.EXTRA[1];ks=I.EXTRA[2];kc=I.EXTRA[0];kp=I.EXTRA[3]
 ck('actual_Rogue_initializer_owner',n(init,86)['refs']==[rh]and e(init,25,'Out1',86,'In1'),'Nasty Hangover uses Rogue, not Muamar; exact current U9 owner86')
 ck('actual_Rogue_cleanup_owner',n(cleanup,344)['refs']==[rc],{'node':344,'edges':[ed for ed in g(cleanup)['edges']if ed[2]=='344'or ed[0]=='344']})
 for inp,ack in [('holo_rogue_calls_v_start',41),('holo_rogue_calls_v_end',42),('holo_v_calls_rogue_start',43),('holo_v_calls_rogue_end',44)]:ck('real_Rogue_ack '+inp,wr(rs,ack,inp+'_done',1,'scene')and bool(path(g(rs,'scene'),g(rs,'scene')['entries'][inp],ack)),{'input':inp,'ack':ack})
 ck('Rogue_native_queued_start',e(rh,32,'Out',33,'In')and e(rh,33,'Out',34,'In')and e(rh,34,'Out',35,'In1')and e(rh,10,'Out',0,'holo_rogue_calls_v_start')and wr(rh,33,'holo_rogue_calls_v_start_activate_count',1),'exact native queued start and end retained, no acknowledgement synthesis')
 ck('Karl_PH1_actual_listener_owner',n(kp,10)['refs']==[kh]and wr(kp,4,'PTFRPH1_karl_ginsky_Issued',1),'native PH1 listener child10, existing receipt4')
 ck('Karl_PH1_before_DLC_body',any(r.get('factName')=='PTFRPH1_karl_ginsky_Issued'and r.get('value')==1 for r in n(find('sts_std_arr_06_entry.questphase'),64999)['reads']),'outer barrier precedes root/9 genuine admission and native main12')
 ck('Karl_cleanup_owned',n(cleanup,1408)['refs']==[kc],'existing native U9 phone cleanup1408')
 for inp,ack in [('audio_v_calls_karl_ginsky_start',40),('audio_v_calls_karl_ginsky_end',42)]:ck('real_Karl_outgoing_ack '+inp,wr(ks,ack,inp.replace('audio_','holo_')+'_done',1,'scene')and bool(path(g(ks,'scene'),g(ks,'scene')['entries'][inp],ack)),{'input':inp,'ack':ack,'fact':inp.replace('audio_','holo_')+'_done'})
 a5=find('sts_std_arr_05_openworld.questphase');a6=find('sts_std_arr_06_ow.questphase');a1=find('sts_std_arr_01_openworld.questphase')
 cases=[(a5,'root/3',[(160,'False',267,'In'),(160,'True',161,'Succeeded'),(161,'Out',266,'In'),(296,'End1',306,'In'),(357,'Out',355,'Active'),(355,'Out',306,'In'),(293,'End1',176,'Succeeded'),(176,'Out',305,'In'),(305,'Out',175,'In2'),(306,'Out',149,'In'),(367,'Out',364,'In'),(364,'Out',327,'In')]),(a1,'root/4',[(80,'non_optional',30,'In'),(80,'optional',79,'In'),(80,'rejected_out',94,'In'),(94,'False',92,'Active'),(94,'True',95,'Active'),(92,'Out',30,'In'),(95,'Out',79,'In'),(30,'Out',81,'In2'),(79,'Out',81,'In1'),(81,'Out1',60,'In')]),(a6,'root/5',[(31,'End 0',2,'In'),(31,'rejected_out',50,'In'),(50,'True',51,'Active'),(50,'False',52,'Active'),(51,'Out',2,'In'),(52,'Out',2,'In'),(2,'Out',19,'In'),(19,'Out',3,'In'),(30,'Out',1,'In')]),(a6,'root/3/471',[(54,'Out',55,'In'),(55,'Out',53,'In'),(45,'Out',48,'In'),(48,'Out',49,'In'),(4,'phone call end',10,'Succeeded'),(10,'Out',41,'In'),(41,'Out',6,'In')])]
 for d,p,edges in cases:
  for edge in edges:ck('specific_native_outcome '+d+p+str(edge),e(d,*edge,p),edge)
 ck('BreakingNews_native_perfect_predicate',n(a5,160,'root/3')['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'arr_05_combat','value':0}],n(a5,160,'root/3')['payload'])
 ck('SeriousSideEffects_original_optional_reward_predicate','investigation'in str(n(a1,94,'root/4')['payload'])and n(a1,81,'root/4')['type']=='questLogicalXorNodeDefinition','investigation objective state selects optional reward; do not infer eligibility from reward name pacifist')
 ck('NastyHangover_actual_native_Rogue_prerequisite',n(find('sts_std_arr_06_entry.questphase'),7,'root/9')['reads'][0]['factName']=='q103_rogue_done'and n(find('sts_std_arr_06_entry.questphase'),8,'root/9')['reads'][0]['factName']=='sts_std_rcr_tier_4','native q103 Rogue prerequisite then native cross-district tier4, preserved')
 # Each omission is classified from actual writer sockets, not title/history heuristics.
 admission=read(H/'verification_02/admission.json');omissions=[]
 for a in admission:
  for jp,rows in a['omitted_native_journal'].items():
   active=[r for r in rows if r['class']=='gameJournalQuestObjective'and any(e[3]=='Active'for e in r['incoming'])];ck('omitted_objective_has_no_native_Active_writer '+a['quest_id']+jp,not active,rows);omissions.append({'quest_id':a['quest_id'],'path':jp,'nodes':rows,'classification':'native objective cleanup-only in bounded closure; saved or external writers conditional'if any(r['class']=='gameJournalQuestObjective'for r in rows)else'original mappin/codex link, not an omitted native objective'})
 # Retired bugfix trees contain different classes. Preserve their exact evidence.
 bugrows=[]
 for q in I.Q:
  d=find(q+'_bugfixing.questphase');bugrows.append({'quest_id':q,'depot':d,'root_prefabs':M[d]['root_prefabs'],'graphs':M[d]['graphs'],'limit':'Original bugfix owners are retired by genuine main-root termination. Conditional actions are not blindly replayed; native active equivalents checked where demonstrated below.'})
 b5=find('sts_std_arr_05_bugfixing.questphase');ck('BreakingNews_same_security_predicate_active_in_body',n(b5,4,'root/15')['payload']['condition']==n(a5,347,'root/3')['payload']['condition']and bool(path(g(a5,'root/3'),0,347))and e(a5,347,'Out',341,'In','root/3'),'native body owns same SecuritySystemControllerPS predicate→combat1, so no guessed missing combat fact patch')
 for bni,cni in [(5,45),(6,46)]:ck('BreakingNews_failure_cleanup_exact_body_duplicate '+str(bni),n(b5,bni,'root/6')['payload']['actions']==n(a5,cni,'root/4/6')['payload']['actions'],{'old_bugfix_graph':'root/6','current_native_graph':'root/4/6','body_node':cni})
 ck('SeriousSideEffects_lab_receipt_retained_native_body',wr(a1,381,'sts_std_arr_01_patch_1_lab',1,'root/5'),'old bugfix CYB-629495 checks current acid inventory, while current native body owns lab receipt381; no synthetic old patch-counter reset')
 # Scene actor policy is current source, not permission to revive Johnny story.
 jv=I.C/'package/r6/scripts/PTFR_Consolidated/PTFR_JohnnyVoiceJV1.reds';txt=jv.read_text(encoding='utf8');pins.append({'path':str(jv),'sha256':sha(jv)});ck('approved_voice_only_policy_current_source',all(t in txt for t in ['Character.Silverhand','visual.TemporaryHide(true)','public func CompletedTower()','this.Hide(actor)'])and 'SetFact'not in txt and 'Despawn'not in txt,'keeps supporting scene actor voice/timing, hides attached visual components after genuine Tower; independent props/engine rendering not certified')
 assets={};stock={}
 for q in I.Q:
  assets[q]=[{'depot':d,'root_prefabs':m['root_prefabs'],'metadata_sha256':m['metadata_sha256'],'actors':m['metadata'].get('actors',[]),'workspots':m['metadata'].get('workspots',[]),'props':m['metadata'].get('props',[]),'refs':[{'depot':x,'inventory':I.IDX.get(x,{'status':'UNRESOLVED_IN_PINNED_INVENTORY'}),'decoded_here':x in M}for x in m['refs']]}for d,m in M.items()if q in d and d.startswith('base\\open_world')];p=I.W/'prealpha/quest_restoration_qr5/shared/tdb_applicability_02'/str(q+'.json');data=read(p);stock[q]={'path':str(p),'sha256':sha(p),'targets':data['targets'],'limits':data['limits']};pins.append({'path':str(p),'sha256':sha(p)});rewards=[x for x in data['targets']if any(a.startswith('QuestRewards.'+q)for a in x.get('requested_aliases',[]))];ck('stock_reward_targets_exist '+q,bool(rewards)and all(x['exists_in_stock']for x in rewards),rewards)
 # Mutate actual raw copies; compare fixed original source oracle after decoding.
 for label,d,p,ni,key in [('tier',find('sts_std_arr_05_entry.questphase'),'root',57,'sts_std_arr_tier_2_1'),('Rogue_ACK',rs,'scene',41,'holo_rogue_calls_v_start_done'),('reward',a1,'root/4',79,'QuestRewards.sts_std_arr_01_completion_pacifist')]:
  raw=copy.deepcopy(read(next(x['json']for x in pins if x.get('depot')==d)));changed=0
  for x in walk(raw):
   if label=='reward'and x.get('$type')=='TweakDBID'and x.get('$value')==key:x['$value']='QuestRewards.QR5_missing';changed+=1
   if label!='reward'and x.get('factName')==key:x['value']=987654;changed+=1
  m=Resource(raw).normalize();caught=m['graphs'][p]['nodes'][str(ni)]['payload']!=n(d,ni,p)['payload'];ck('raw_mutation_detected '+label,changed>0 and caught,{'depot':d,'graph':p,'node':ni,'changes':changed});f=O/'mutations'/str(label+'.json');write(f,raw);mut.append({'fault':label,'path':str(f),'sha256':sha(f),'caught':caught})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'journal_omissions.json',omissions);write(O/'native_bugfix_scope.json',bugrows);write(O/'asset_bindings.json',assets);write(O/'stock_applicability.json',stock);write(O/'mutations.json',mut);write(O/'summary.json',{'checks':len(tests),'mutations':len(mut),'resources':len(M)});print({'checks':len(tests),'mutations':len(mut),'out':str(O)})
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);run(Path(p.parse_args().out))
