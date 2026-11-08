"""Targeted QR6 Ronald ownership/enrollment investigation, exact pinned inputs."""
from pathlib import Path
import sys,argparse,collections,copy
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk
from model import Resource,reachable
ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();O=Path(a.output).resolve();assert not O.exists();O.mkdir(parents=True)
P=W/'prealpha/quest_restoration_qr5/groups/G21/reviews/RONALD';e=read(H/'source_epoch_00.json');C=Path(e['candidate']);checks=[];pins=[];M={};R={}
def ck(name,ok,evidence):
 checks.append({'name':name,'status':'PASS'if ok else'FAIL','evidence':evidence});assert ok,name
rows=read(P/'raw_readback_01/manifest.json')+read(P/'raw_extra_01/manifest.json')
for r in rows:
 ck('exact prior raw/export pin '+r['depot'],sha(r['raw'])==r['raw_sha256']and sha(r['json'])==r['json_sha256'],r)
 if r['depot'].startswith('towercontinued\\'):
  raw=C/'archive_source'/r['depot'];ck('current QR5candidate03 exact bytes '+r['depot'],sha(raw)==r['raw_sha256']==e['source_resources'][r['depot']],str(raw))
 R[r['depot']]=read(r['json']);M[r['depot']]=Resource(R[r['depot']]).normalize();ck('raw graph diagnostics '+r['depot'],not M[r['depot']]['errors'],M[r['depot']]['errors']);pins.append(r)
RN=r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase';NS=r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene';BO=r'towercontinued\b0_story_eight\ronald.questphase';BS=BO.replace('.questphase','.scene')
def g(d,gp='root'):return M[d]['graphs'][gp]
def n(d,i,gp='root'):return g(d,gp)['nodes'][str(i)]
def path_to(graph,start,end):
 todo=collections.deque([(str(start),[])]);seen=set()
 while todo:
  u,p=todo.popleft()
  if u in seen:continue
  seen.add(u)
  if u==str(end):return p
  for ed in graph['edges']:
   if ed[0]==u and ed[1]!='CutSource'and ed[3]!='CutDestination':todo.append((ed[2],p+[ed]))
 return None
ck('actual current B0 caller socket',any(x==['2','Out','200','In']for x in g(BO,'root/5')['edges'])and any(x==['200','Out','3','q302_05_ronald_in']for x in g(BO,'root/5')['edges']),'Root5 nested service attaches only q302_05_ronald_in')
NG=g(NS,'scene');BG=g(BS,'scene');start=NG['entries']['q302_05_ronald_in'];nativepath=path_to(NG,start,1755)
ck('native earned subscription has actual caller route',bool(nativepath),nativepath)
ck('current copied writer remains in resource',n(BS,1755,'scene')['writes']==n(NS,1755,'scene')['writes'],'Presence alone is not an executing earned enrollment')
ck('current writer unreachable from actual service caller',path_to(BG,BG['entries']['q302_05_ronald_in'],1755)is None,'No route from920 to1755, even without branch predicates')
entry_results={name:{'start':s,'writer1755_path':path_to(BG,s,1755)}for name,s in BG['entries'].items()}
ck('no other current scene input reaches subscription',all(x['writer1755_path']is None for x in entry_results.values()),entry_results)
first_lost=next(x for x in nativepath if x not in BG['edges'])
ck('precise native first lost route edge',bool(first_lost),first_lost)
ck('native news requires genuine positive enrollment',n(RN,12)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':'q302_ronald_messages_enabled','value':1}],'Do not replace missing earned history with synthetic1')
ck('news listener not present under current B0',not any(z['refs']==[RN]for gg in M[BO]['graphs'].values()for z in gg['nodes'].values())and 'root/5/11'not in M[BO]['graphs'],'B0 excludes native11 and12; does not replace them')
owners=[]
for d,m in M.items():
 if '#q302_pr_bar'in m['root_prefabs']:owners.append({'depot':d,'root_prefabs':m['root_prefabs'],'nested_prefab_users':[{'graph':gp,'node':i,'prefabs':z['prefabs']}for gp,gg in m['graphs'].items()for i,z in gg['nodes'].items()if z['prefabs']]})
ck('native bar is shared beyond Ronald',len(owners)>=3,owners)
ck('current B0 does not itself acquire native bar lease',not M[BO]['root_prefabs']and not any(z['prefabs']for gg in M[BO]['graphs'].values()for z in gg['nodes'].values()),'Neither Ready nor OwnerActive is acquisition acknowledgment')
cases={'sts_ep1_12':(35,110,122,111,123,124,11,106),'sts_ep1_08':(45,115,126,125,127,128,39,107),'sts_ep1_03':(55,117,131,130,132,133,49,108),'sts_ep1_01':(65,119,135,134,136,137,59,109)}; histories=[]
for qid,(sent,delay,stand,normal,alt,hub,child,release)in cases.items():
 ng=g(RN,'root/11');nn=ng['nodes'];fact='q302_msg_ronald_'+qid
 ck('sent before pending native clock '+qid,nn[str(sent)]['writes'][0]['factName']==fact and nn[str(sent)]['writes'][0]['value']==1 and nn[str(delay)]['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':2,'hours':0,'minutes':0,'seconds':0},[sent,delay])
 ck('both delivery gates preserve native area '+qid,all('#q302_tr_ronald_area_02'in nn[str(i)]['node_refs']for i in [normal,alt]),[normal,alt])
 ck('real SMS callback clears shared pause '+qid,[''+str(child),'Out1',str(release),'In']in ng['edges']and nn[str(release)]['writes'][0]['factName']=='q302_ronald_message_pause'and nn[str(release)]['writes'][0]['value']==0,release)
 # Two positions in the SAME native graph after sent1 have identical writes to
 # that durable sent fact. Distinguish them only by owner/timer/actual journal.
 future=path_to(ng,sent,delay);delivered=path_to(ng,delay,release)
 ck('two distinct native sent1 lifecycle positions '+qid,bool(future)and bool(delivered)and not any(x.get('factName')==fact and x.get('value')==0 for z in nn.values()for x in z['writes']),{'pending_path':future,'delivery_path':delivered})
 histories.append({'quest_id':qid,'durable_fact':fact,'pending_node':delay,'sent_already':1,'real_callback':release,'requires':'Saved active-owner/elapsed timer, actual journal message/reply state and marker/queue lease; sent1 alone does not encode these.'})
mut=[]
def mutated(name,change,predicate):
 raw=copy.deepcopy(R[RN]);change(Resource(raw));m=Resource(raw).normalize();ok=predicate(M[RN])and not predicate(m);ck('raw document control '+name,ok,'Mutations change only fresh in-memory raw export, never resource binaries');p=O/'mutations'/(name+'.json');write(p,raw);mut.append({'name':name,'path':str(p),'sha256':sha(p),'detected':ok})
mutated('lost_bar_root_lease',lambda z:z.root.update(phasePrefabs=[]),lambda z:'#q302_pr_bar'in z['root_prefabs'])
def change_delay(z):
 for x in walk(z.obj):
  if x.get('$type')=='questGameTimeDelay_ConditionType'and x.get('days')==2:x['days']=0
mutated('wrong_game_timer_units',change_delay,lambda z:z['graphs']['root/11']['nodes']['115']['payload']['condition']['type']['days']==2)
def change_sent(z):
 for x in walk(z.obj):
  if x.get('$type')=='questSetVar_NodeType'and x.get('factName')=='q302_msg_ronald_sts_ep1_08':x['value']=0
mutated('sent_history_reset',change_sent,lambda z:z['graphs']['root/11']['nodes']['45']['writes'][0]['value']==1)
write(O/'source_pins.json',pins);write(O/'checks.json',checks);write(O/'mutations.json',mut)
out={'status':'CONFIRMED_FAMILY_REMAINS_REPAIR_BLOCKED_WITH_ADDITIONAL_EXACT_ENROLLMENT_AND_LIFECYCLE_EVIDENCE','source_epoch':'QR6:00','checks':len(checks),'mutations':len(mut),'source_raw_export_pairs_revalidated':len(rows),'new_raw_exports':0,'reuse_boundary':'Current raw bytes equal exact prior WK9.1 readbacks; no historical source conclusions accepted without graph inspection.','affected_quests':list(cases),'native_earned_enrollment_route':nativepath,'current_all_scene_ingress_routes':entry_results,'first_lost_native_enrollment_route_edge':first_lost,'native_bar_root_owners_in_target_capture':owners,'history_ambiguity':histories,'not_a_new_unique_defect':True,'preserved_prior_defect_id':'QR5-RONALD-POST-GIG-NEWS-OWNER','runtime_changes':[],'repair_approved':False,'blockers':[{'id':'EXACT_SCOPED_BAR_MARKER_PROVIDER','missing':'Decoded placement/provider scope of area_02_closer/area_02 versus full #q302_pr_bar and existing B0/native ownership. Several native whole bar owners are present in reference set; no extracted marker-only safe successor established.'},{'id':'ISOLATED_FUTURE_SHARED_NEWS_OWNER','missing':'Source-reviewed future-event dispatcher preserving positive earned enrollment, native pause/cancel/rearm, sent-before-clock order, true child outputs and termination without old timer adoption or nonselected fluff replay.'},{'id':'EARNED_CURRENT_ENROLLMENT','missing':'B0 writer1755 exists but is unreachable from every current scene input. Replaying removed native dialogue is not approved; existing genuine pre-Tower enrollment may qualify future messages, missing history cannot be fabricated.'}],'verification_limits':['MAY topology proves no current route to writer; native route availability still depends on exact scene choices and prerequisites.','Native sent fact is demonstrably written before delay; report does not assert two whole save states/journals are identical.','Marker missing ownership is not proof that placed world markers are absent. No gameplay, scheduling, saved timer or lease acquisition is certified.']}
write(O/'evidence.json',out);print({'checks':len(checks),'mutations':len(mut),'first_lost_edge':first_lost,'repair_approved':False})
