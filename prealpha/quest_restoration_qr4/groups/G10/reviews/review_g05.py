"""G05 independent raw-source peer review; no G05 code/models imported."""
from pathlib import Path
import sys,json,argparse,collections
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable
IDX=read(W/'diagnostics/vanilla_parity_20261029_01/analysis_02/resource_inventory.json');WORK=W/'prealpha/quest_restoration_qr3/candidate_01/archive_source'
WK=r'base\quest\main_quests\prologue\q001\phases\q101_wakako_reward.questphase';WF=r'towercontinued\sidejobs_s24\services\the_gig_fresh.questphase';WR=r'towercontinued\sidejobs_s22\the_gig_reward_resume.questphase';WG=r'towercontinued\fixer_offices_fo1\wakako.questphase';CA=r'towercontinued\b0_story_services\cassius.questphase'
GN=r'base\quest\main_quests\prologue\q001\phases\q001_wilson.questphase';GF=r'towercontinued\sidejobs_s25\services\gun_fresh.questphase';GO=r'towercontinued\sidejobs_s25\services\gun_order.scene';VB=r'towercontinued\b0_wilson_vendor\body.questphase';VO=r'towercontinued\b0_wilson_vendor\owner.questphase';VN=r'base\open_world\vendors\watson\little_china\wat_lch_gunsmith_01\wat_lch_gunsmith_01.scene'
MQ11=r'towercontinued\sidejobs_s23\base_b\mq011.questphase';N11=r'base\quest\minor_quests\mq011\mq011.questphase';MQ12=r'towercontinued\sidejobs_s23\base_a\mq012_stud.questphase';N12=r'base\quest\minor_quests\mq012\mq012.questphase';SH=r'towercontinued\gig_phone_u9\fixer_cleanup.questphase';INIT=r'base\quest\holocalls\holocall_initializers.questphase'
def run(O):
 assert not O.exists();tests=[];pins=[];M={}
 def check(name,ok,e):tests.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,name
 # Use the review's declared inputs only for selection, then independently read
 # authoritative current bytes and raw JSON through the common handle decoder.
 inventory=read(H.parents[1]/'G05/verification_02/source_pins.json')
 for row in inventory:
  d=row['depot'];r=IDX[d];j=Path(r['json']);raw=WORK/d.replace('\\','/') if d.startswith('towercontinued\\') else j.with_suffix('')
  if not raw.is_file():raw=Path(str(j).replace('\\json\\','\\raw\\')).with_suffix('')
  check('actual current binary '+d,sha(raw)==r['sha256'],str(raw));M[d]=Resource(read(j)).normalize();check('actual raw decoding '+d,not M[d]['errors'],M[d]['errors']);pins.append(dict(depot=d,binary=str(raw),sha256=sha(raw),json=str(j),json_sha256=sha(j)))
 def g(d,gp='root'):return M[d]['graphs'][gp]
 def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
 def edge(d,e,gp='root'):return list(map(str,e)) in g(d,gp)['edges']
 def wr(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['writes'])
 def has(d,i,f,v,gp='root'):return any(x.get('factName')==f and x.get('value')==v for x in n(d,i,gp)['reads'])
 def record(d,i,r,gp='root'):return any(x.get('$type')=='TweakDBID' and value(x)==r for x in walk(n(d,i,gp)['payload']))
 # The Gig: independent fresh-v-earned cash/SMS split and original tattoo proof.
 for d in [WF,WR]:
  for i,nn in g(d)['nodes'].items():
   if int(i)<1000 and i!='0' and i in g(WK)['nodes']:check('TheGig native payload '+d+':'+i,nn['payload']==n(WK,i)['payload'],dict(resource=d,native=WK,node=i))
 check('TheGig fresh cash reward after real wait',record(WF,11,'QuestRewards.sq_q001_wakako_done') and edge(WF,[3,'Out',11,'In']) and has(WF,3,'q001_wakako_reward_given',0),dict(resource=WF,nodes=[3,11]))
 check('TheGig earned resume omits cash and SMS',all(i not in g(WR)['nodes'] for i in ['11','12','13']) and has(WR,1001,'q001_wakako_reward_given',1) and has(WF,1002,'q001_wakako_reward_given',0),dict(fresh=WF,resume=WR))
 check('TheGig two tattoo alternatives exact',any(x.get('$type')=='questLogicalCondition' and x.get('operation')=='OR' for x in walk(n(WK,29)['payload'])) and all(any(x.get('$type')=='TweakDBID' and value(x)==r for x in walk(n(WK,29)['payload'])) for r in ['Items.YakuzaTattoo','Items.AdvancedYakuzaTattoo']),dict(resource=WK,node=29))
 check('TheGig genuine success and active release/done',all(edge(WK,e) for e in [(18,'Out',4,'Succeeded'),(4,'Out',26,'In'),(26,'Out',27,'In')]) and wr(WK,26,'sq_q001_active',0) and wr(WK,27,'sq_q001_done',1),dict(nodes=[18,4,26,27]))
 check('TheGig native prefab obligation remains unresolved',bool(M[WK]['root_prefabs']) and not M[WF]['root_prefabs'] and not M[WR]['root_prefabs'] and n(WK,30)['type']=='questDeletionMarkerNodeDefinition' and 24 in n(WK,30)['payload']['deletedNodeIds'],dict(native_prefabs=M[WK]['root_prefabs'],fresh=M[WF]['root_prefabs'],resume=M[WR]['root_prefabs'],deletion_marker=n(WK,30)['payload']))
 check('Wakako and Cassius distinct native actor scopes','#wakako_okada_default' in n(WG,100)['prefabs'] and '#pr_wat_nid_ripperdoc_01' in n(CA,5)['prefabs'],dict(wakako=n(WG,100)['prefabs'],cassius=n(CA,5)['prefabs']))
 # The Gun: native vendor route, item entitlement and completion receipt.
 check('Gun native vendor item/tag path retained',all(edge(GO,e,'scene') for e in [(42,'0:0',305,'0:0'),(430,'0:0',209,'0:3')]) and record(GO,281,'Items.Preset_Q001_Lexington','scene') and record(GO,361,'Items.Preset_Q001_Lexington','scene'),dict(resource=GO,nodes=[42,305,281,361,430,209]))
 check('Gun actual inventory predicate retained',n(GO,281,'scene')['payload']==n(VN,281,'scene')['payload'] and n(GO,361,'scene')['payload']==n(VN,361,'scene')['payload'],dict(original=VN,private=GO,nodes=[281,361]))
 check('Gun Finished waits real root Succeeded',any(x.get('state')=='Succeeded' for x in n(GF,1008)['reads']) and edge(GF,[1008,'Out',1007,'In']),dict(resource=GF,nodes=[1008,1007]))
 check('Gun order selects existing B0 physical body',GO in n(VB,101)['refs'] and edge(VB,[100,'True',101,'wilson_default_in']) and edge(VB,[100,'False',5,'wilson_default_in']),dict(resource=VB,nodes=[100,101,5]))
 # Shoot to Thrill: exact live handoff branches, not unused legacy waits.
 check('MQ011 real listener pause before native prerequisites',n(MQ11,1003)['type']=='questPauseConditionNodeDefinition' and has(MQ11,1003,'PTFRS23_PHONE_WILSON_Issued',1) and edge(MQ11,[1002,'Out',1003,'In']) and edge(MQ11,[1003,'Out',54,'In']),dict(resource=MQ11,node=1003))
 for wait,claim in [(1112,1005),(1122,1105)]:
  cond=n(MQ11,wait)['payload'];check('MQ011 actual release wait '+str(wait),n(MQ11,wait)['type']=='questPauseConditionNodeDefinition' and all(has(MQ11,wait,f,v) for f,v in [('PTFRB0WV_Released',1),('PTFRB0WV_Near',0),('PTFRB0WV_SpawnActionOut',0),('PTFRB0WV_ActorDistanceGate',0)]) and not any(x.get('factName')=='PTFRB0WV_QuestOwns' for x in n(MQ11,wait)['reads']),dict(wait=wait,claim=claim,condition=cond))
 check('MQ011 real quest completion releases service authority',edge(MQ11,[15,'Out1',1007,'In']) and edge(MQ11,[1007,'Out',1012,'In']) and wr(MQ11,1012,'PTFRB0WV_QuestOwns',0) and M[N11]['root_prefabs']==['#mq011_pr_wilson'],dict(resource=MQ11,native=N11,nodes=[15,1007,1012]))
 # Night Moves: native MR_STUD; no invented Dennis dependency/failed restart.
 check('MQ012 actual native full body retained',n(MQ12,16)['refs']==[N12],dict(resource=MQ12,node=16))
 check('MQ012 rootSucceeded observer completion',any(r.get('state')=='Succeeded' for r in n(MQ12,1010)['reads']) and edge(MQ12,[1010,'Out',1011,'In']),dict(resource=MQ12,nodes=[1010,1011]))
 check('MQ012 native main/cleanup and prefab binding',edge(N12,[0,'Out',12,'In1']) and edge(N12,[12,'Out1',8,'In1']) and edge(N12,[8,'Out1',13,'In1']) and edge(N12,[8,'Out2',13,'In1']) and '#mq012_pr_stud' in n(N12,8)['prefabs'] and '#mq012_pr_stud' in n(N12,13)['prefabs'],dict(resource=N12,nodes=[12,8,13]))
 phone_review={}
 for q,p,priv,init in [('mq011_wilson','wilson',r'towercontinued\sidejobs_s23\phone\wilson.questphase',99),('mq012_stud','mr_stud',r'towercontinued\sidejobs_s23\phone\mrstud.questphase',74)]:
  native='base\\quest\\holocalls\\'+p+'\\'+p+'_holocall.questphase';scene=native.replace('.questphase','.scene');cleanup=native.replace('_holocall','_cleanup');check('native initializer exact '+q,n(priv,init)['payload']==n(INIT,init)['payload'],dict(private=priv,node=init))
  ack=[]
  for suf,ai in [('start',41),('end',42)]:
   f='holo_'+p+'_calls_v_'+suf+'_done';check('real native phone acknowledgement '+q+suf,wr(scene,ai,f,1,'scene'),dict(scene=scene,node=ai,fact=f));ack.append(dict(scene=scene,node=ai,fact=f))
  phone_review[q]=dict(native=native,scene=scene,cleanup=cleanup,acks=ack,limit='Receipt prerequisites/source routes establish static order, not completed engine listener activation or delivered calls')
 outcome=dict(status='APPROVE_G05_SCOPED_FINDINGS_WITH_EXPLICIT_OPAQUE_OBLIGATIONS',reviewer='qr4_worker_a',independent=True,checks=len(tests),tests=tests,source_pins=pins,not_imported=['G05/verify.py','G05/lib.py','G05/inspection.json'],quest_ids=['sq_q001_wakako','sq_q001_wilson','mq011_wilson','mq012_stud'],ten_contract_review={q:{k:'Targeted raw-source/entitlement/handoff checks agree with bounded finding; existing named limits retained' for k in ['entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies']} for q in ['sq_q001_wakako','sq_q001_wilson','mq011_wilson','mq012_stud']},phone_review=phone_review,qualifications=['The Gig original root prefab differs from Wakako/Cassius actor prefabs. Both reward adapters omit it. Native deletion marker30 removes24 and there is no demonstrated active native consumer, so this is OPAQUE ownership/content evidence, not approved omission, automatic defect or a reason to attach a speculative new owner.','The Gun native UI/inventory/tag path is retained; exact stock/free-item entitlement and target definition/provider are not established by preserved item references.','PhoneIssued barrier orders a receipt prerequisite; native initializer activation completion and lease release scene scheduling are engine-dependent. Existing saved owner/reward/timer transitions remain conditional/live-only.','MQ012 native active1 allowance and historic Failed-reactivation path do not authorize arbitrary failed-quest reset. Complete world bindings/target payouts remain unresolved.'],runtime_changes=[])
 write(O/'G05.json',outcome);return dict(checks=len(tests),sources=len(pins),status=outcome['status'])
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))
