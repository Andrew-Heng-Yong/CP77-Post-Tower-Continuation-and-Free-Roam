import sys,json,copy,argparse
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[1]));from lib import *
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True);T=[];mut=[]
def ck(n,b,e):T.append({'name':n,'status':'PASS'if b else'FAIL','evidence':e});assert b,n
prop=W/'prealpha/quest_restoration_qr5/groups/G15/actor_proposal_01/proposal.json';ck('exact_proposal_pin',sha(prop)=='90D2181311B38A58778AE8F84488ED56BC69434DF0C684A2884D31FA3BF596CE',str(prop));A=read(prop);sr=P/'source_verification_01/review.json';ck('independent_actual_raw_source_review_pin',sha(sr)=='5E576B7B2BDDE9BC638F8FBE08B8609C8BF09FE1877E822CA6B1637AA085C25D',{'path':str(sr),'checks':143,'raw_resources':10})
M={x['depot']:Resource(read(x['json'])).normalize()for x in read(P/'raw_exports_01/manifest.json')};SPY=A['resource'];BOOT=A['helper_template']['resource'];old=M[SPY]['graphs']['root/50'];base=M[BOOT]['graphs']['root/100'];actor=M[A['native_actor']]
ck('actual_before_carrier_pin',sha(next(x['raw']for x in read(P/'raw_exports_01/manifest.json')if x['depot']==SPY))==A['before'],A['before']);ck('initial_parentIDs_unused',all(str(i)not in old['nodes']for i in A['new_parent_local_ids']),A['new_parent_local_ids']);ck('helper1303_unused',str(A['helper_graph_change']['new_child_id'])not in base['nodes'],list(base['nodes']));ck('root50_nonterminating',not any(n['type']=='questOutputNodeDefinition'and n['payload'].get('type')=='Terminating'for n in old['nodes'].values()),'Owned helper sibling survives native main23 completion; no new root terminator')
ck('all_old_edges_preserved_exact_future_event_only',not A['parent_removed_edges']and A['parent_added_edges']==[[65003,'Out',1300,'In'],[1300,'True',1301,'In'],[1301,'Out',1302,'In1']],'Only original positive65003 event creates helper; no root/onattach/poll replay')
ck('initial_actual_history_fences',all(A['initial_guard_facts'].get(k)==v for k,v in {'PTFRU9_sts_ep1_08_ParentEntered':1,'PTFRU9_sts_ep1_08_Started':0,'PTFRU9_sts_ep1_08_MainFinished':0,'PTFRU9_sts_ep1_08_OwnerFinished':0,'PTFRU9_sts_ep1_08_Fault':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'PTFRS23_STEVEN_Issued':0,'PTFRS23_STEVEN_Finished':0,'PTFRS23_STEVEN_Fault':0,'steven_santos_default_on':0,'sts_ep1_08_finished':0,'sts_ep1_08_biomonitor_ana':0,A['claim_fact']:0}.items()),A['initial_guard_facts'])
ck('initial_native_followup_journal_types',len(A['initial_guard_journals'])==7 and all(x['state']=='Inactive'and not x['inverted']for x in A['initial_guard_journals']),'Exact selected followup root/phase/objective/description/invitation history, not NOTActive approximation')
def initial(f,j,event=True):
 if not event:return False
 if not all(f.get(k,0)==v for k,v in A['initial_guard_facts'].items()):return False
 if any(x['path']['realPath']not in j for x in A['initial_guard_journals']):return None
 return all(j[x['path']['realPath']]=='Inactive'for x in A['initial_guard_journals'])
def late(f,j,clauses=None):
 clauses=A['helper_graph_change']['late_guard_facts']if clauses is None else clauses
 for x in clauses:
  av=f.get(x['fact'],0);v=x['value'];op=x['comparison']
  if not {'Equal':av==v,'Greater':av>v,'GreaterOrEqual':av>=v}[op]:return False
 p=A['helper_graph_change']['late_guard_journal']['path']
 return None if p not in j else j[p]in A['helper_graph_change']['late_guard_journal']['states']
f=A['initial_guard_facts'];j={x['path']['realPath']:'Inactive'for x in A['initial_guard_journals']};ck('fresh_future_event_initial_admits',initial(f,j)is True,'Positive existing owned event, zero-progress/unused helper and exact known inactive followup history')
for k,v in f.items():ck('initial_refuses_changed_'+k,initial(f|{k:0 if v else 1},j)is False,k)
for p in j:
 for bad in ['Active','Succeeded','Failed']:
  ck('initial_refuses_history '+p+bad,initial(f,j|{p:bad})is False,p)
 ck('initial_unknown_journal_not_approved '+p,initial(f,{k:v for k,v in j.items()if k!=p})is not True,'Static unknown/defer, no claim about missing scalar0 or fabricated journal history')
ck('no_retroactive_old_owner_enrollment',initial(f|{'PTFRU9_sts_ep1_08_Started':1},j)is False and initial(f,j,event=False)is False,'Old started owners and default all-zero state cannot replay new positive event')
later=f|{'PTFRU9_sts_ep1_08_Started':1,'PTFRU9_sts_ep1_08_MainFinished':1,'PTFRU9_sts_ep1_08_OwnerFinished':1,'sts_ep1_08_finished':1,'steven_santos_default_on':1,A['claim_fact']:1,'q304_stadium_escape_active':0};root=A['helper_graph_change']['late_guard_journal']['path']
for state in ['Inactive','Active']:
 for owned in [0,1]:ck('genuine_completed_future_default_dispatch_'+state+str(owned),late(later|{'PTFRU9_sts_ep1_08_OwnerFinished':owned},j|{root:state})is True,'Native Started/MainFinished1 are expected; OwnerFinished0or1 does not block followup')
ck('Ana_changed_after_entry_still_refused',initial(f,j)is True and late(later|{'sts_ep1_08_biomonitor_ana':1},j|{root:'Active'})is False,'Required actual0→1 player-choice fixture; native actor2 would otherwise choose stadium')
for state in ['Succeeded','Failed','Invalid']:
 ck('late_refuses_terminal_or_invalid_journal_'+state,late(later,j|{root:state})is False,state)
ck('late_unknown_journal_not_approved',late(later,{k:v for k,v in j.items()if k!=root})is not True,'Explicit conservative unknown, not a blanket runtime result')
for x in A['helper_graph_change']['late_guard_facts']:
 bad=0 if x['value'] else 1
 if x['comparison']=='Greater':bad=0
 ck('late_refuses_wrong_'+x['fact'],late(later|{x['fact']:bad},j|{root:'Active'})is False,x)
# Finished>=1 is an actual mandatory native route condition, not a guessed overrestriction.
S=Store();body=S.n(SPY,23,'root/50')['refs'][0];gr=S.g(body)
ck('native_finished_writer312_positive',any(x['factName']=='sts_ep1_08_finished'and x['value']==1 for x in S.n(body,312)['writes']),'Actual native main writer before Out1')
for e in [['312','Out','314','In'],['314','Out','326','In'],['326','Out','342','In'],['342','Out','482','In'],['482','Out','1','In']]:ck('native_finish_exit_chain '+str(e),e in gr['edges'],e)
ck('native_finished312_dominates_exit1',all([e for e in gr['edges']if e[2]==b]==[[a0,s,b,t]]for a0,s,b,t in [['312','Out','314','In'],['314','Out','326','In'],['326','Out','342','In'],['342','Out','482','In'],['482','Out','1','In']]),'Unique incoming suffix to terminating native output1; source-qualified native finished>=1 check')
ck('MainFinished65005_same_native_completion_event',any(x['factName']=='PTFRU9_sts_ep1_08_MainFinished'and x['value']==1 for x in old['nodes']['65005']['writes'])and['23','Out1','65005','In']in old['edges'],'Same actual main23.Out1 pulse that owns native cleanup64000')
# Build only a non-runtime model fixture of exact helper scope, preserve old bodies unchanged.
retained={str(i)for i in A['helper_template']['retain_nodes']};helper=copy.deepcopy(base);helper['nodes']={i:n for i,n in helper['nodes'].items()if i in retained};helper['edges']=[e for e in helper['edges']if e!=['0','Out','501','In1']];helper['edges'].remove(['19','Out','17','In1']);helper['edges'] +=[['19','Out','1303','In'],['1303','Out','17','In1']];helper['nodes']['1303']={'review_fixture_only':True,'type':'questPauseConditionNodeDefinition','guard':A['helper_graph_change']['late_guard_facts']}
ck('actor_only_retained_scope',set(helper['nodes'])=={'0','17','19','1303'}and not any('501'in e for e in helper['edges']),'No SMS/timer/journal message subtree501 or children copied')
for i in ['17','19']:ck('native_actor_nodes_unchanged_'+i,helper['nodes'][i]==base['nodes'][i],'Exact native/current actor reference and default/escape waiter metadata')
ck('every_dispatch_has_late_fence',[e for e in helper['edges']if e[2]=='17']==[['1303','Out','17','In1']]and['17','Out1','19','In']in helper['edges'],'No19 direct route around late fence; original return loop retained')
ck('no_new_native_fact_reward_SMS_writer',not any(n.get('writes')or n.get('reward')or n.get('sms')for n in helper['nodes'].values()),'Only parent1301 writes NEW private claim; external original actor cleanup remains authorized')
ck('S23_source_exclusion_untouched',A['helper_template']['resource']==BOOT and A['parent_removed_edges']==[],'One carrier resource only; no S23 or native actor resource edit')
# Adversarial fixtures for the precise source risks.
noana=[x for x in A['helper_graph_change']['late_guard_facts']if x['fact']!='sts_ep1_08_biomonitor_ana'];mut.append({'fault':'Ana_guard_only_at_initial_event','detected':late(later|{'sts_ep1_08_biomonitor_ana':1},j|{root:'Active'},noana)is True and late(later|{'sts_ep1_08_biomonitor_ana':1},j|{root:'Active'})is False})
wrong=[dict(x,value=0)if x['fact']=='PTFRU9_sts_ep1_08_Started'else x for x in A['helper_graph_change']['late_guard_facts']];mut.append({'fault':'late_started0_overrestriction','detected':late(later,j|{root:'Active'},wrong)is False and late(later,j|{root:'Active'})is True})
bad=copy.deepcopy(helper);bad['edges'].append(['19','Out','17','In1']);mut.append({'fault':'direct_native19_bypasses_late_fence','detected':len([e for e in bad['edges']if e[2]=='17'])>1})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
report={'status':'APPROVE_EXACT_FUTURE_U9_ACTOR_ONLY_STEVEN_PROPOSAL_FOR_ROOT_IMPLEMENTATION','proposal':str(prop),'proposal_sha256':sha(prop),'checks':len(T),'mutations':len(mut),'source_review':str(sr),'source_review_sha256':sha(sr),'native_body_source_pins':S.pins,'approved_scope':{'resource':SPY,'graph':'root/50','parent_added_ids':[1300,1301,1302],'existing_edges_removed':[],'helper_child_nodes':[0,17,19,1303],'actor_resource_changed':False,'S23_changed':False,'native_cleanup_SMs_timer_changed':False,'late_guard':'Every dispatch19→1303 requires actual completed owned main/nativeFinished,default_on>0,Ana0,escape0,private claim/support/S23 state; no late zero-progress requirement','no_messages_rewards_default_on1_new_writers':True},'limits':['Source/model proposal approval only; actual serialized readback/package needs independent review','Native world community/scene/notifier/vehicle placements and arbitrary saved/engine listener state remain opaque/live-only','Initial allInactive journal narrowing supports only known fresh followup histories; invalid/missing target evidence cannot be turned into approval','Already entered/started U9 saved owners are not retroactively adopted','Unrelated sourceJSON/model disagreement observed for sts_ep1_08_gameplay.questphase during exploratory wider load; not used in this positive guard proof. Native phase body containing mandatory312→exit suffix itself is separately pinned/normalized; investigate gameplay discrepancy separately before claiming its parity'],'runtime_changes':[],'tests':str(O/'tests.json')};save(O/'review.json',report);save(O/'tests.json',{'checks':T,'mutations':mut});save(O/'actor_only_model_fixture.json',{'runtime_resource':False,'helper':helper});print(json.dumps({'checks':len(T),'mutations':len(mut),'review_sha256':sha(O/'review.json')}))
