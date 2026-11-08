"""Independent G02 source checks; does not import the G02 verifier."""
from lib import *
import argparse,copy
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
S=Store();B=W/'prealpha/quest_restoration_qr4/groups/G02';core=read(B/'shared_core.json');checks=[]
def ck(name,b,e):checks.append({'name':name,'status':'PASS'if b else'FAIL','evidence':e});assert b,name
ck('frozen_shared_core',sha(B/'shared_core.json')=='6C7DAF85ED6345729092B3BF22EF6E1C176E95B6829824D11BD19A49D6DED4EC',sha(B/'shared_core.json'))
for d,r in core['resources'].items():
 m=S.load(d);pin=next(p for p in S.pins if p['depot']==d);ck('independent_raw_pin '+d,pin['resource_sha256']==r['sha256'] and pin['json_sha256']==r['json_sha256'] and not m['errors'],pin)
f=r'towercontinued\sidejobs_s25\families\sq025_fresh.questphase';v=r'base\quest\side_quests\sq025\sq025.questphase';p=r'base\quest\side_quests\sidequests.questphase';g=S.g;n=S.n
ck('fresh_real_fanout',all(S.edge(f,*e)for e in[(92,'Out',100,'In1'),(92,'Out',65020,'In'),(65020,'Out',94,'In1'),(92,'Out',95,'In1')]),'92 concurrent body, support/listener and return-Archer branches; no strict listener-first edge')
ip=copy.deepcopy(n(r'base\quest\holocalls\holocall_initializers.questphase',51)['payload']);ip['id']=94
ck('listener_native_template_private94_from_native51',n(f,94)['payload']==ip,{'native_initializer':51,'private_persisted_id':94,'refs':n(f,94)['refs']})
ck('support_receipt_native_writer',any(x['factName']=='PTFRS22_SQ025_SupportIssued'and x['value']==1 for x in n(f,65020)['writes']),'Receipt precedes listener94 within its branch only')
cond=n(p,154)['payload']['condition'];expected={'$type':'questLogicalCondition','conditions':[{'$type':'questContentCondition','type':{'$type':'questContentToken_ConditionType','type':'SideQuest_Standalone'}},{'$type':'questJournalCondition','type':{'$type':'questJournalEntryVisited_ConditionType','path':{'$type':'gameJournalPath','className':{'$type':'CName','$storage':'string','$value':'gameJournalPhoneMessage'},'editorPath':'','fileEntryIndex':1,'realPath':'contacts/administration/sq025_pickup_car/sq025_pickup_car'},'visited':1}}],'operation':'OR'}
ck('native_parent154_exact_token_OR_visited',cond==expected,cond);ck('parent154_connected',S.edge(p,155,'Out',154,'In')and S.edge(p,154,'Out',48,'In1'),'155→154→48.In1')
present=[(gp,i)for gp,gr in S.load(f)['graphs'].items()for i,q in gr['nodes'].items()if any(x.get('$type')=='questJournalEntryVisited_ConditionType'and x.get('path',{}).get('realPath')=='contacts/administration/sq025_pickup_car/sq025_pickup_car'for x in q['reads'])]
ck('outer_gate_is_real_unresolved_context_gap',not present and core['unresolved_parent_gate']['status']=='CONDITIONAL',{'private_visited_predicates':present,'approval_evidence':'No exact approved equivalence established; do not label eligibility PASS or write visitation facts'})
for gp,gr in S.load(v)['graphs'].items():
 cp='root/100'+gp[4:]
 if gp not in ['root','root/161']:ck('retained_nested_graph '+gp,S.load(f)['graphs'][cp]==gr,cp)
retained=set(g(v)['nodes'])&set(g(f,'root/100')['nodes']);changed=[i for i in retained if n(v,i)['payload']!=n(f,i,'root/100')['payload']]
ck('all_shared_retained_root_payloads_exact',not changed,{'count':len(retained),'changed':changed,'removed_later_resurgence_not_silently_certified':sorted(set(g(v)['nodes'])-set(g(f,'root/100')['nodes']))})
owner=r'towercontinued\sidejobs_s22\delamain\owner.questphase';q=n(owner,1003);facts={(x['factName'],x.get('comparisonType'),x.get('value'))for x in q['reads']if'factName'in x}
for fact,val_ in [('sq025_scans_done',3),('sq025_sad_done',1),('sq025_mean_done',1),('sq025_suicidal_done',1),('sq025_angry_done',0),('sq025_manic_done',0),('sq025_scared_done',0),('sq025_deep_done',0),('sq025_briefing_scene_done',1)]:ck('progressed_actual_seam '+fact,(fact,'Equal',val_)in facts,'Exact earned state; no reset proposed')
scan=r'base\quest\side_quests\sq025\scenes\sq025_05_scan.scene';controller=r'base\quest\holocalls\delamain\delamain_holocall.questphase';scene=controller.replace('.questphase','.scene')
for tag,start,end,wa,wb,aa,ab,reader,clear in [('scared',7350,7354,7347,7351,1047,1048,38,42),('suicidal',7271,7275,7268,7272,779,780,22,26)]:
 for writer,wait,ack,part in [(start,wa,aa,'start'),(end,wb,ab,'end')]:
  fact='holo_delamain_'+tag+'_calls_v_'+part
  ck('independent_request_wait '+tag+part,any(w['factName']==fact+'_activate'and w['value']==1 for w in n(scan,writer,'scene')['writes'])and any(e[2]==str(wait)for e in g(scan,'scene')['edges']if e[0]==str(writer))and any(x.get('factName')==fact+'_done'for x in n(scan,wait,'scene')['reads']),{'producer':writer,'wait':wait,'fact':fact})
  ck('independent_real_ack '+tag+part,any(w['factName']==fact+'_done'and w['value']==1 for w in n(scene,ack,'scene')['writes']),{'native_scene':scene,'node':ack})
 gate=114 if tag=='scared' else 106
 ck('independent_native_listener '+tag,S.edge(controller,reader,'Out',gate,'In')and S.edge(controller,gate,'False',clear,'In')and S.edge(controller,clear,'Out',21,'holo_delamain_'+tag+'_calls_v_start'),{'reader':reader,'gate':gate,'clear':clear,'scene':21})
for row in core['shared_protocols']:
 path=row['ack_path'];ck('actual_ack_path '+row['case']+row['type'],all(any(e[0]==a and e[2]==b for e in g(scene,'scene')['edges'])for a,b in zip(path,path[1:])),path)
def connected(gr,a,b):return any(e[0]==str(a)and e[2]==str(b)for e in gr['edges'])
bad=copy.deepcopy(g(f));bad['edges'].remove(['65020','Out','94','In1']);mut=[{'fault':'missing_Delamain_listener_connection','detected':not connected(bad,65020,94)}]
bad=copy.deepcopy(cond);bad['operation']='AND';mut.append({'fault':'changed_native_token_mail_OR_to_AND','detected':bad!=expected})
for x in mut:ck('mutation '+x['fault'],x['detected'],x)
save(O/'tests.json',{'count':len(checks),'checks':checks,'mutations':mut});save(O/'source_pins.json',S.pins)
summary={'status':'INDEPENDENT_SOURCE_REVIEW_ACCEPTS_CONDITIONAL_FINDINGS_WITH_CONCURRENCY_CORRECTION','reviewer_group':'G05','reviewed_group':'G02','shared_core_sha256':sha(B/'shared_core.json'),'checks':len(checks),'mutations':mut,'source_pins':str(O/'source_pins.json'),'tests':str(O/'tests.json'),'verified':['Exact frozen raw/JSON/model source pins independently reopened; no G02 verifier imported','Real fresh92.Out body100 and65020→94 listener branches are concurrent','Native154 OR(SideQuest_Standalone, administration pickup-car message visited) is exact and connected; private direct entry does not reproduce it','All retained root payloads and retained nested native body graphs independently equal original; omitted later resurgence/debug nodes not mislabeled parity','Exact progressed counter3 / sad-mean-suicidal done1 seam; no synthetic reset','Both scared/suicidal real request/wait/listener/ack paths checked'], 'remaining':['CONDITIONAL: Parent154 replacement equivalence/approval remains unestablished; no eligibility PASS or synthetic visited fact is justified','LIVE_ONLY: Concurrent listener startup is not strict happens-before, and does not itself prove a request loss bug','OPAQUE: World/prefab target/TDB/localization closure and exact saved executing owners remain open','Historical native cleanup alias discrepancies remain uncertainty, not permission for counter resets'],'runtime_defects_confirmed':[],'runtime_changes':[]}
save(O/'review.json',summary)
frozen=Path(__file__).parent/'reviews/G02.json'
if not frozen.exists():save(frozen,summary)
print(json.dumps({'checks':len(checks),'sources':len(S.pins),'mutations':len(mut)}))
