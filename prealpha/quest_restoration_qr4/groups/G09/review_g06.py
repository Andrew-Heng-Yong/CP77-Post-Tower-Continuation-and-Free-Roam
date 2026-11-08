"""Independent adversarial G06 review; own model reader, never imports G06 verifier."""
from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
S=Store();B=W/'prealpha/quest_restoration_qr4/groups/G06';R=read(B/'results.json');pins=read(B/'verification_02/source_pins.json');checks=[]
def ck(name,b,e):checks.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
for row in pins:
 if row.get('depot'):
  d=row['depot'];S.load(d);mine=next(p for p in S.pins if p['depot']==d);ck('independent_raw_JSON_pin '+d,mine['resource_sha256']==row['sha256']and mine['json_sha256']==row['json_sha256'],mine)
 else:ck('independent_script_policy_pin '+row['path'],sha(row['path'])==row['sha256'],row)
PAR=r'base\quest\minor_quests\minorquests.questphase';P5=r'towercontinued\side_job_pilot_s1\owner.questphase';P13=r'towercontinued\sidejobs_s23\base_b\mq013.questphase';P2=r'towercontinued\sidejobs_s23\base_a\mq002_veterans.questphase';BODY5=r'towercontinued\side_job_pilot_s1\native_owner.questphase';N5=r'base\quest\minor_quests\mq005\mq005.questphase';N13=r'base\quest\minor_quests\mq013\mq013.questphase';N2=r'base\quest\minor_quests\mq002\mq002.questphase';n=S.n;g=S.g
def es(d,edges,gp='root'):
 for e in edges:ck('connected '+d+' '+str(e),S.edge(d,*e,gp=gp),{'graph':gp,'edge':e})
for d in [P13,P2]:
 for i,q in g(d)['nodes'].items():
  if int(i)<1000 and i!='0':ck('independent_native_ancestor '+d+' '+i,q['payload']==n(PAR,i)['payload'],i)
 for gp,gr in S.load(d)['graphs'].items():
  if gp!='root':ck('independent_inline '+d+' '+gp,gr==S.load(PAR)['graphs'][gp],gp)
es(P13,[(1002,'Out',1003,'In'),(1003,'Out',54,'In'),(54,'Out',80,'In'),(80,'Out',55,'In'),(55,'Out',1004,'In'),(1004,'True',1005,'In'),(1006,'Out',17,'In1')]);es(P2,[(1008,'True',81,'In1'),(173,'False',1100,'In'),(1100,'True',1101,'In'),(1101,'Out',12,'In1'),(1101,'Out',1010,'In'),(1010,'Out',1011,'In')])
es(P5,[(0,'Out',400,'In'),(401,'Out',402,'In'),(402,'Out',403,'In'),(403,'Out',405,'In1'),(405,'Out1',404,'In'),(404,'Out',1,'In')]);q=n(P5,402);f={x['factName']:x['value']+(1 if x['comparisonType']=='Greater'else 0)for x in q['reads']if'factName'in x};j={'quests/minor_quest/mq005_alley':'Inactive'}
ck('actual_CR1_Inactive_guard_fixture',evaluate(q['payload']['condition'],f,j)is True,'Matches OnlyPain MQ005 identity; title alias not used')
for state in ['Active','Failed','Succeeded']:ck('actual_CR1_history_refusal '+state,evaluate(q['payload']['condition'],f,{next(iter(j)):state})is False,state)
ck('unknown_MQ005_history_not_Inactive',evaluate(q['payload']['condition'],f,{})is not True,'Missing target entry does not become unstarted')
for i in [10,15]:
 actual=n(BODY5,i,'root/4')['payload']['condition'];van=n(N5,i,'root/4')['payload']['condition'];ck('bounded_cleanup_keeps_exact_native_arm '+str(i),actual['operation']=='OR'and actual['conditions'][0]==van,{'graph':'root/4','node':i,'native_arm_preserved':True})
es(BODY5,[(37,'Out',400,'In'),(5,'End_Out',400,'In'),(400,'True',401,'In'),(401,'Out',9,'In'),(9,'Out',402,'In'),(402,'Out',11,'Succeeded'),(400,'False',403,'In')],'root/3')
ck('original_MQ005_reward_pointer',n(BODY5,9,'root/3')['payload']==n(N5,9,'root/3')['payload'],'QuestRewards.mq005_done unchanged; private claim fencing separate')
# Explicit direct communications classification: MQ005/MQ013 no phone, MQ002 native message.
for qid,ds in [('mq005_alley',[N5,BODY5,r'base\quest\minor_quests\mq005\phases\mq005_combat.questphase',r'base\quest\minor_quests\mq005\scenes\mq005_01_alley.scene',r'base\quest\minor_quests\mq005\scenes\mq005_02_passout.scene']),('mq013_punks',[P13,N13,r'base\quest\minor_quests\mq013\scenes\mq013_00_punks.scene'])]:
 candidates=[(d,gp,i)for d in ds for gp,gr in S.load(d)['graphs'].items()for i,q in gr['nodes'].items()if any(x.get('factName','').startswith(('holo_','audio_'))for x in q['reads']+q['writes'])or any('Phone'in x.get('$type','')or'SendMessage'in x.get('$type','')for x in walk(q['payload']))]
 ck('no_external_phone_required '+qid,not candidates,candidates)
COM=r'base\quest\minor_quests\mq002\phases\mq002_combat.questphase';END=r'base\quest\minor_quests\mq002\phases\mq002_ending.questphase';es(COM,[(4,'Out',20,'In'),(20,'Out',19,'In')]);ck('MQ002_native_message_target',any('contacts/carol/mq002_escaped'in str(z)for z in walk(n(COM,20)['payload'])),'Actual sendMessage, not a holo request')
es(END,[(11,'End 0',26,'In'),(26,'Out',10,'Succeeded')]);ck('MQ002_original_reward',any(val(z)=='QuestRewards.mq002_done'for z in walk(n(END,26)['payload'])),'Original reward record pointer retained, contents not certified')
es(N2,[(147,'True',146,'In1'),(147,'False',152,'In1')]);es(N2,[(0,'Out',2,'Active'),(2,'Out',3,'Active')],'root/152')
ck('MQ013_native_completed_story_gate',any(x.get('factName')=='q101_done'and x.get('comparisonType')=='Greater'and x.get('value')==0 for x in n(N13,6,'root/8')['reads']),'Outer side-content flag does not replace completed q101 prerequisite')
mut=[];bad=copy.deepcopy(q['payload']['condition']);next(z for z in walk(bad)if z.get('$type')=='questJournalEntryState_ConditionType')['state']='Failed';mut.append({'fault':'old_wrong_CR1_admission_state','detected':evaluate(bad,f,j)is False and evaluate(bad,f,{next(iter(j)):'Failed'})is True})
bad=copy.deepcopy(g(COM));bad['edges'].remove(['4','Out','20','In']);mut.append({'fault':'lost_escape_message_connection','detected':['4','Out','20','In']not in bad['edges']})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
save(O/'tests.json',{'count':len(checks),'checks':checks,'mutations':mut});save(O/'source_pins.json',S.pins)
out={'status':'INDEPENDENT_SOURCE_REVIEW_ACCEPTS_BOUNDED_G06_FINDINGS','reviewer_group':'G09','reviewed_group':'G06','reviewed_result_sha256':sha(B/'results.json'),'checks':len(checks),'mutations':mut,'source_pins':str(O/'source_pins.json'),'tests':str(O/'tests.json'),'verified':['Native ancestors, inline graphs and actual intermediate entry routes independently compared','MQ005 exact CR1 Inactive guard rejects Active/Failed/Succeeded and unknown; serialized identity is OnlyPain, not historical HappyTogether label','MQ005 reward fencing retains original reward pointer and cleanup OR retains exact original arm','MQ005/MQ013 have no local holo/audio request or Phone/SMS dependency; MQ002 native escape message and failed post-message are connected','MQ013 retained q101_done gate, MQ002 original reward path and primary/succeeded observer separation'],'limits':['Static eligibility PASS is restricted to exact decoded predicates and current pinned script coverage, not save history/target definition or original owner liveness','Reward record pointers do not resolve TDB contents or entitlement','World placement, cleanup departure observations and saved actor/controller/vehicle retirement remain OPAQUE/LIVE_ONLY','No source-confirmed defect or repair approval established'],'runtime_changes':[]}
save(O/'review.json',out)
frozen=Path(__file__).parent/'reviews/G06.json'
if not frozen.exists():save(frozen,out)
print(json.dumps({'checks':len(checks),'mutations':len(mut),'sources':len(S.pins)}))

