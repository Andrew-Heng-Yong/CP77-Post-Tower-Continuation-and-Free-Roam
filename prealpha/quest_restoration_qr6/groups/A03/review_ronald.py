"""Independent QR6 Ronald blocker review, actual raw resources; no coordinator checker imports."""
from pathlib import Path
import sys,copy,collections
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'A01'));from source_lib import *
from verify import semantic,edge,node,fact
P=W/'prealpha/quest_restoration_qr6/blockers/ronald_01';O=H/'reviews/RONALD';R=read(P/'evidence.json')
def reach(g,start):
 todo=[str(start)];seen=set()
 while todo:
  u=todo.pop()
  if u in seen:continue
  seen.add(u);todo+=[e[2]for e in g['edges']if e[0]==u and e[1]!='CutSource'and e[3]!='CutDestination']
 return seen
def run(out):
 assert not out.exists();tests=[];issues=[];pins=[];M={};raw={}
 def ck(k,v,e):
  tests.append(dict(name=k,status='PASS'if v else'FAIL',evidence=e))
  if not v:issues.append(k)
 for p in read(P/'source_pins.json'):
  ck('coordinator pinned source identity '+p['depot'],sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'],p);M[p['depot']]=Resource(read(p['json'])).normalize();pins.append(p)
 for p in read(O/'readback_01/manifest.json'):
  ck('fresh actual native/current serialized resource '+p['depot'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);raw[p['depot']]=read(p['json']);m=Resource(raw[p['depot']]).normalize();ck('fresh original model correspondence '+p['depot'],canon(m)==canon(M[p['depot']]),'all graphs/metadata; typed TDB/derived digest normalization');M[p['depot']]=m;pins.append(p)
 rn=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase';ns=r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene';bo=r'towercontinued\b0_story_eight\ronald.questphase';bs=bo.replace('.questphase','.scene');ng=M[ns]['graphs']['scene'];bg=M[bs]['graphs']['scene']
 ck('current B0 exact actual Ronald scene input',edge(M[bo],2,'Out',200,'In','root/5')and edge(M[bo],200,'Out',3,'q302_05_ronald_in','root/5'),'not whole-scene presence as execution proof')
 ck('same original1755 enrollment payload retained',node(M[bs],1755,'scene')['writes']==node(M[ns],1755,'scene')['writes']and any(w['factName']=='q302_ronald_messages_enabled'and w['value']==1 for w in node(M[bs],1755,'scene')['writes']),node(M[bs],1755,'scene')['writes'])
 ingress={k:dict(entry=i,writer1755_reachable='1755'in reach(bg,i))for k,i in bg['entries'].items()};ck('all actual current7scene inputs exclude enrollment writer',len(ingress)==7 and not any(x['writer1755_reachable']for x in ingress.values()),ingress)
 ck('native actual Ronald input can MAY reach1755','1755'in reach(ng,ng['entries']['q302_05_ronald_in']),'source-native topology only, exact choices/context still required')
 path=R['native_earned_enrollment_route'];ck('reported exact original path consists only original edges',all(e in ng['edges']for e in path)and path[0][0]==ng['entries']['q302_05_ronald_in']and path[-1][2]=='1755',path);lost=next(e for e in path if e not in bg['edges']);ck('first lost native enrollment edge exact',lost==['839','0:4','1451','0:0']==R['first_lost_native_enrollment_route_edge'],lost)
 ck('native news exact positive earned enrollment gate',fact(M[rn],12,'q302_ronald_messages_enabled',1,comp='GreaterOrEqual'),'zero/unknown pre-Tower subscription not fabricated')
 ck('current service has no native news successor',not any(rn in n['refs']for g in M[bo]['graphs'].values()for n in g['nodes'].values())and'root/5/11'not in M[bo]['graphs'],'original11news/12enrollment absent; copied1755 alone cannot replace listener')
 ck('original shared bar lease retained at native root','#q302_pr_bar'in M[rn]['root_prefabs'],'required original marker/prefab ownership scope')
 ck('current B0 lacks actual root or nested bar lease',not M[bo]['root_prefabs']and not any(n['prefabs']for g in M[bo]['graphs'].values()for n in g['nodes'].values()),'does not imply placed world markers are absent or no other owner exists')
 owners=[]
 for d,m in M.items():
  if'#q302_pr_bar'in m['root_prefabs']:owners.append(d)
 ck('multiple original shared bar root owners actually observed',len(owners)==4,owners)
 lifecycle=[]
 for q,sent,delay,normal,alt,child,release in [('sts_ep1_12',35,110,111,123,11,106),('sts_ep1_08',45,115,125,127,39,107),('sts_ep1_03',55,117,130,132,49,108),('sts_ep1_01',65,119,134,136,59,109)]:
  g=M[rn]['graphs']['root/11'];sf='q302_msg_ronald_'+q;ck('original durable sent1 before native clock '+q,fact(M[rn],sent,sf,1,'root/11')and str(delay)in reach(g,sent),{'sent_node':sent,'delay_node':delay});t=node(M[rn],delay,'root/11')['payload']['condition']['type'];ck('two actual game days '+q,t=={'$type':'questGameTimeDelay_ConditionType','days':2,'hours':0,'minutes':0,'seconds':0},t)
  ck('both actual delivery gates need original area02 '+q,all('#q302_tr_ronald_area_02'in node(M[rn],i,'root/11')['node_refs']for i in[normal,alt]),[normal,alt]);ck('real SMS child output releases pause '+q,edge(M[rn],child,'Out1',release,'In','root/11')and fact(M[rn],release,'q302_ronald_message_pause',0,'root/11'),{'child':child,'real_release':release});ck('sent fact is never a delivered-only receipt '+q,not any(w['factName']==sf and w['value']==0 for n in g['nodes'].values()for w in n['writes'])and str(release)in reach(g,delay),'sent1 remains through pending and delivered positions; owner/timer/journal differ')
  lifecycle.append(dict(quest=q,sent_node=sent,delay_node=delay,delay=t,callback=release,not_a_delivery_receipt=sf))
 ck('four selected affected jobs and no unique-defect inflation',set(R['affected_quests'])=={'sts_ep1_12','sts_ep1_08','sts_ep1_03','sts_ep1_01'}and R['not_a_new_unique_defect']and R['preserved_prior_defect_id']=='QR5-RONALD-POST-GIG-NEWS-OWNER','same prior family, not four new defects')
 ck('blocker conclusion does not authorize repair',not R['repair_approved']and not R['runtime_changes']and len(R['blockers'])==3,R['blockers'])
 # Independent actual raw controls: marker lease, actual pause release, synthetic enrollment route.
 mutants=[]
 def mu(d,change,pred,label):
  x=copy.deepcopy(raw[d]);change(x);m=Resource(x).normalize();caught=pred(M[d])and not pred(m);ck('independent raw fault detected '+label,caught,d);mutants.append(dict(fault=label,depot=d,detected=caught))
 mu(rn,lambda x:x['Data']['RootChunk'].update(phasePrefabs=[]),lambda m:'#q302_pr_bar'in m['root_prefabs'],'native bar lease removed')
 def paused(x):
  rr=Resource(x);root=rr.d(rr.root['graph']);parent=next(rr.d(h)for h in root['nodes']if rr.d(h).get('id')==11);gg=rr.d(parent['phaseGraph']);n=next(rr.d(h)for h in gg['nodes']if rr.d(h).get('id')==107);rr.d(n['type'])['value']=1
 mu(rn,paused,lambda m:fact(m,107,'q302_ronald_message_pause',0,'root/11'),'real Spy SMS callback no longer releases pause')
 def enroll(x):
  n=next(z for z in walk(x)if z.get('$type')=='scnStartNode'and z.get('nodeId',{}).get('id')==920);n['outputSockets'][0]['destinations'][0]['nodeId']['id']=1755
 mu(bs,enroll,lambda m:'1755'not in reach(m['graphs']['scene'],'920'),'synthetic current enrollment route introduced')
 write(out/'tests.json',tests);write(out/'source_pins.json',pins);write(out/'ingress.json',ingress);write(out/'lifecycles.json',lifecycle);write(out/'mutations.json',mutants);write(out/'review.json',dict(status='PASS_INDEPENDENT_BLOCKER_REVIEW'if not issues else'REVIEW_ISSUES',reviewer='qr6_a',checks=len(tests),mutations=len(mutants),issues=issues,fresh_readbacks=len(read(O/'readback_01/manifest.json')),reviewed_result=str(P/'evidence.json'),reviewed_result_sha256=sha(P/'evidence.json'),repair_approved=False,confirmed_defect='QR5-RONALD-POST-GIG-NEWS-OWNER',scope='Independent actual-source enrollment/lease/timer/callback review. No safe repair proven.',limits=['MAY source-native reachability is not earned dialogue execution or saved subscription proof.','sent1 alone is not delivery proof; entire save/journal/timer states are not asserted identical.','No marker-only provider/old-owner arbitration or isolated future queue adapter established.','No game/save/fact/package/runtime writes.']));print(read(out/'review.json'))
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--output');a=ap.parse_args()
 if a.prepare:
  ps=[dict(depot=p['depot'],binary=p['raw'],sha256=p['raw_sha256'],json=p['json'],json_sha256=p['json_sha256'])for p in read(P/'source_pins.json')];write(O/'readback_inputs.json',ps);print(len(ps))
 else:run(Path(a.output))
