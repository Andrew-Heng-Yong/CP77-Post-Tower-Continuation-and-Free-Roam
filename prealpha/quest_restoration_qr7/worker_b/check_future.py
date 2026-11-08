"""Source-pinned, read-only Ronald future-event/lease validator; no builder imports.

python -X utf8 -B prealpha/quest_restoration_qr7/worker_b/check_future.py --out future_check_01
"""
from lib import *
import argparse,copy,struct
from check_bar import fnv

def graph_raw(rr,ids):
 g=rr.d(rr.root['graph'])
 for i in ids:g=rr.d(next(rr.d(z)for z in g['nodes']if rr.d(z)['id']==i)['phaseGraph'])
 return g

def source_family(g):
 errors=[]
 def need(v,k):
  if not v:errors.append(k)
 rows=[]
 for case,done,pre,sent,pause,clock,select,normal,alt,hub,child,release,join in [('12',2,None,35,10,110,122,111,123,124,11,106,68),('08',37,112,45,38,115,126,125,127,128,39,107,69),('03',47,113,55,48,117,131,130,132,133,49,108,70),('01',57,114,65,58,119,135,134,136,137,59,109,71)]:
  node=lambda i:g['nodes'][str(i)];edge=lambda a,s,b,d:[str(a),s,str(b),d]in g['edges']
  need(node(done)['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'GreaterOrEqual','factName':f'sts_ep1_{case}_done','value':1}],case+':native-done-listener')
  need(node(sent)['writes']==[{'$type':'questSetVar_NodeType','factName':f'q302_msg_ronald_sts_ep1_{case}','setExactValue':1,'value':1}],case+':native-sent-claim')
  need(node(clock)['payload']['condition']['type']=={'$type':'questGameTimeDelay_ConditionType','days':2,'hours':0,'minutes':0,'seconds':0},case+':two-game-days')
  need(edge(sent,'Out',pause,'In')and edge(pause,'Out',clock,'In'),case+':sent-before-pause-before-clock')
  need(edge(done,'Out',pre if pre else sent,'In')and(pre is None or edge(pre,'Out',sent,'In')),case+':exact-preclaim-route')
  if pre:need(node(pre)['payload']['condition']['type']=={'$type':'questRealtimeDelay_ConditionType','hours':0,'miliseconds':0,'minutes':0,'seconds':{'08':1,'03':2,'01':3}[case]},case+':preclaim-real-seconds')
  need(edge(clock,'Out',select,'In')and edge(select,'False',normal,'In')and edge(select,'True',alt,'In'),case+':standalone-branch-sockets')
  for gate,token in [(normal,'MinorQuestAndSts'),(alt,'EP1_Minor')]:
   p=node(gate)['payload']['condition'];need(p['operation']=='AND'and p['conditions'][0]['type']['type']==token and p['conditions'][1]['type']=='IsOutside',case+':AND-token-outside:'+str(gate))
   need(edge(gate,'Out',hub,'In2'if gate==normal else'In1'),case+':gate-convergence:'+str(gate))
  need(edge(hub,'Out1',child,'In1')and edge(child,'Out1',release,'In')and edge(release,'Out',join,'In1'),case+':true-SMS-callback-release')
  need(node(release)['writes']==[{'$type':'questSetVar_NodeType','factName':'q302_ronald_message_pause','setExactValue':1,'value':0}],case+':native-release0')
  rows.append({'quest_id':'sts_ep1_'+case,'done':done,'preclaim':pre,'sent':sent,'pause':pause,'clock':clock,'standalone':select,'normal_gate':normal,'alternate_gate':alt,'child':child,'release':release,'terminal_hub':join})
 return rows,errors

def future_errors(m,native,spec,markers,guard_expected):
 err=[];g=m['graphs']['root'];b=m['graphs'].get('root/202',{});nodes=b.get('nodes',{})
 def need(v,k):
  if not v:err.append(k)
 if not nodes:return ['missing-new-private-owner-body']
 keep=set(map(str,spec['kept_native_ids']));need(set(nodes)==keep|{'0','200','201','202','203','210','211','212','213','220'},'exact-selected-native-plus-nine-admission-nodes')
 for i in keep:
  exp=copy.deepcopy(native['nodes'][i]['payload'])
  if i=='67':exp['inputSocketCount']=4
  for z in walk(exp):
   if z.get('$type')=='NodeRef'and val(z)=='#q302_tr_ronald_area_02':z['$value']=markers['private_refs'][0]
  need(nodes[i]['payload']==exp,'native-body-payload:'+i)
  socks=[s for s in native['nodes'][i]['sockets']if not(i=='67'and s['name']=='In5')]
  need(nodes[i]['sockets']==socks,'native-body-sockets:'+i)
 expected=set(map(tuple,spec['kept_edges']));expected.add(('0','Out','220','In'))
 for c in spec['case_gates']:
  i=str(c['id']);wait=str(c['id']+10);arm='PTFRQR7_RonaldNews_Armed_'+c['quest'];parent='PTFRU9_'+c['quest']+'_ParentEntered'
  want={'$type':'questLogicalCondition','operation':'AND','conditions':[{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':f,'value':0}}for f in [c['done_fact'],c['sent_fact']]]+[{'$type':'questLogicalCondition','operation':'OR','conditions':[{'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':f,'value':v}}for f,v in [(parent,0),(arm,1)]]}]}
  need(nodes[i]['payload']['condition']==want,'explicit-unstarted-or-positive-future-arm:'+c['quest'])
  need(nodes[wait]['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':arm,'value':1}],'actual-future-producer-wait:'+c['quest'])
  expected.update([('220','Out',i,'In'),(i,'True',wait,'In'),(wait,'Out',str(c['hub']),'In1'),(i,'False',str(c['skip_hub']),'In1')])
 need(set(map(tuple,b['edges']))==expected,'all-native-edges-and-only-reviewed-admission-splices')
 loaded=nodes['220']['payload']['condition'];need(loaded=={'$type':'questLogicalCondition','conditions':[{'$type':'questNodeLoadingCondition','inverted':0,'objectRef':{'$type':'NodeRef','$storage':'string','$value':v}}for v in markers['private_refs']],'operation':'AND'},'private-triggers-actually-loaded-before-listening')
 need(g['nodes']['202']['prefabs']==[markers['private_parent']]and not m['root_prefabs'],'nested-private-two-trigger-lease-only')
 need(g['nodes']['201']['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRQR7_RonaldNews_Issued','setExactValue':1,'value':1}]and g['nodes']['203']['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRQR7_RonaldNews_Retired','setExactValue':1,'value':1}],'private-once-issued-and-retirement')
 need(g['nodes']['200']['payload']['condition']==guard_expected,'entire-retained-session-enrollment-contact-idle-and-once-admission')
 need(g['edges']==[['0','Out','200','In'],['200','Out','201','In'],['201','Out','202','In1'],['202','Out1','203','In'],['203','Out','204','In']],'exact-root-lifecycle')
 need(nodes['1']['payload'].get('type')=='Terminating'and g['nodes']['204']['payload'].get('type')=='Terminating','child-and-outer-terminating-release')
 need(not any(q.get('$type')in ['questAddRemoveContact_NodeType','questChangeContactList_NodeTypeParams','questSetHUDEntryForcedVisibility_NodeType']for q in walk(m['metadata'])),'no-contact-notification-replay')
 _,family=source_family(b);err+=family
 return err

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args();out=H/args.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir();checks=[];mutants=[]
 def ck(name,ok,**e):checks.append({'name':name,'pass':bool(ok),**e})
 manifest=read(H/'experiments/future_owner_04/NOT_FOR_INTEGRATION.json');markers=read(manifest['markers']);spec=read(manifest['spec']);sourcePins=read(H/'readback_01/manifest.json')
 nativeModels={p['depot']:Resource(read(p['json'])).normalize()for p in sourcePins};ng=nativeModels[RN]['graphs']['root/11']
 ck('stored-inspection-models-reproduced-from-every-pinned-source-JSON',nativeModels==read(H/'inspection_01/models.json'))
 guards=['PostTowerFreeRoamActive','PTFRP0_DR13','q307_active','q307_done','q307_finished','q307_2079','q307_main_game_killed','q305_johnny_scene_active','q115_point_of_no_return','q000_done','q307_ep1_killed','q302_done','q302_ronald_tree']
 donor=nativeModels[BO]['graphs']['root']['nodes']['2']['payload']['condition']['conditions']
 parts=[copy.deepcopy(next(c for c in donor if c.get('$type')=='questFactsDBCondition'and c['type']['factName']==f))for f in guards]
 parts.append(copy.deepcopy(nativeModels[RN]['graphs']['root']['nodes']['12']['payload']['condition']))
 parts.extend({'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':f,'value':0}}for f in ['q302_ronald_message_pause','PTFRQR7_RonaldNews_Issued'])
 parts.append({'$type':'questJournalCondition','type':{'$type':'questJournalEntryState_ConditionType','inverted':0,'path':copy.deepcopy(ng['nodes']['121']['payload']['type']['path']),'state':'Active'}})
 guard_expected={'$type':'questLogicalCondition','conditions':parts,'operation':'AND'}
 for p in sourcePins:ck('native-current-raw-json-pin:'+p['depot'],sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'])
 for p in [manifest,*manifest['arming_producers']]:ck('private-serialized-readback-pin:'+p.get('quest_id','owner'),sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256'])
 d=read(manifest['json']);m=Resource(d).normalize();err=future_errors(m,ng,spec,markers,guard_expected);ck('future-only-exact-source-delta',not err,errors=err)
 family,err=source_family(ng);ck('native-four-source-family-contracts',not err,errors=err)
 # All original entry code and saved node/socket identities are preserved except a new positive arming writer.
 entry_models={}
 for p in manifest['arming_producers']:
  before=nativeModels[p['intended_depot']];after=Resource(read(p['json'])).normalize();entry_models[p['quest_id']]=after
  ck('entry-graph-and-metadata-preservation:'+p['quest_id'],set(before['graphs'])==set(after['graphs'])and before['metadata']==after['metadata'])
  for gp,g in before['graphs'].items():
   ag=after['graphs'][gp]
   ck('all-old-node-payload-socket-identities:'+p['quest_id']+':'+gp,all(ag['nodes'][i]==n for i,n in g['nodes'].items()))
   if gp!='root/50':ck('unaffected-graph-edges:'+p['quest_id']+':'+gp,g['edges']==ag['edges'])
   else:
    expected=set(map(tuple,g['edges']));expected.remove(('65002','Out','65003','In'));expected.update([('65002','Out','65007','In'),('65007','Out','65003','In')])
    ck('exact-post-native-admission-arming-splice:'+p['quest_id'],set(ag['nodes'])-set(g['nodes'])=={'65007'}and set(map(tuple,ag['edges']))==expected)
    ck('only-positive-private-arming-write:'+p['quest_id'],ag['nodes']['65007']['writes']==[{'$type':'questSetVar_NodeType','factName':p['private_fact'],'setExactValue':1,'value':1}])
    ck('original-fresh-admission-requires-parent0:'+p['quest_id'],{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRU9_'+p['quest_id']+'_ParentEntered','value':0}in g['nodes']['65002']['reads'])
 # Current stock producers independently match the exact pinned vanilla bytes and actual source graph nodes.
 producers=read(H/'producer_readback_01/manifest.json')['producers'];producer_evidence=[]
 for p in producers:
  sm=Resource(read(p['json'])).normalize();g=sm['graphs'][p['graph']];n=g['nodes'][p['node']]
  ck('current-pinned-native-real-done-producer:'+p['quest_id'],p['current_matches_pinned']and sha(p['raw'])==p['raw_sha256']and n['writes']==[{'$type':'questSetVar_NodeType','factName':p['quest_id']+'_done','setExactValue':1,'value':1}])
  producer_evidence.append({**p,'incoming':[e for e in g['edges']if e[2]==p['node']],'outgoing':[e for e in g['edges']if e[0]==p['node']]})
 # Independently compare exact serialized marker buffers and complete trigger payloads, never old typed indices.
 nativeSector=Resource(read(markers['native']['json']));privateSector=Resource(read(markers['json']));oldbuf=Path(read(H/'bar_buffer_01/manifest.json')['buffer']).read_bytes();buf=Path(markers['buffer']).read_bytes()
 ck('only-two-private-trigger-definitions',len(privateSector.root['nodes'])==2 and len(privateSector.root['nodeData']['Data'])==2 and len(buf)==288)
 for slot,oldslot in enumerate([1,3]):
  ck('exact-native-trigger-shape-and-notifier:'+str(slot),nativeSector.clean(nativeSector.d(nativeSector.root['nodes'][oldslot]))==privateSector.clean(privateSector.d(privateSector.root['nodes'][slot])))
  exp=bytearray(oldbuf[oldslot*144:(oldslot+1)*144]);struct.pack_into('<Q',exp,0x58,fnv(markers['private_refs'][slot]));packed=struct.unpack_from('<Q',exp,0x70)[0];struct.pack_into('<Q',exp,0x70,(packed&~0x7ffff)|slot)
  ck('144bytes-preserved-except-new-global-and-packed-index:'+str(slot),buf[slot*144:(slot+1)*144]==exp)
 block=Resource(read(markers['block_json'])).root;desc=block['descriptors'][0]
 ck('private-descriptor-only-and-scoped-lease',len(block['descriptors'])==1 and desc['category']=='Quest'and val(desc['questPrefabNodeRef'])==markers['private_parent']and not desc['variants']and desc['numNodeRanges']==1 and val(desc['data']['DepotPath'])==markers['intended_sector_depot'])
 # Representative deliberately faulty readback documents are independently re-normalized.
 for name,nid,edit in [('sent-claim-lost',35,lambda n,rr:rr.d(n['type']).__setitem__('value',0)),('clock-shortened',110,lambda n,rr:rr.d(rr.d(n['condition'])['type']).__setitem__('days',1)),('cleanup-pause-release-lost',106,lambda n,rr:rr.d(n['type']).__setitem__('value',1)),('future-arm-wait-bypassed',210,lambda n,rr:rr.d(rr.d(n['condition'])['type']).__setitem__('value',0)),('terminal-still-waits-fluff',67,lambda n,rr:n.__setitem__('inputSocketCount',5))]:
  mut=copy.deepcopy(d);rr=Resource(mut);g=graph_raw(rr,[202]);n=next(rr.d(z)for z in g['nodes']if rr.d(z)['id']==nid);edit(n,rr);errors=future_errors(Resource(mut).normalize(),ng,spec,markers,guard_expected);save(out/(name+'.json'),mut);mutants.append({'fault':name,'detected':bool(errors),'errors':errors})
 mut=copy.deepcopy(d);rr=Resource(mut);g=graph_raw(rr,[]);n=next(rr.d(z)for z in g['nodes']if rr.d(z)['id']==202);n['phaseInstancePrefabs']=[];errors=future_errors(Resource(mut).normalize(),ng,spec,markers,guard_expected);save(out/'lost-private-marker-lease.json',mut);mutants.append({'fault':'lost-private-marker-lease','detected':bool(errors),'errors':errors})
 mut=copy.deepcopy(d);rr=Resource(mut);g=graph_raw(rr,[]);n=next(rr.d(z)for z in g['nodes']if rr.d(z)['id']==200);condition=rr.d(n['condition']);condition['conditions']=[z for z in condition['conditions']if not any(q.get('factName')=='q307_ep1_killed'for q in walk(rr.d(z)))];errors=future_errors(Resource(mut).normalize(),ng,spec,markers,guard_expected);save(out/'missing-native-owner-retirement-guard.json',mut);mutants.append({'fault':'missing-native-owner-retirement-guard','detected':bool(errors),'errors':errors})
 for z in mutants:ck('actual-readback-mutant:'+z['fault'],z['detected'])
 # Native unsafety counterexample: sent>=1 rearm checks do not dominate initial done listeners.
 start_path=path(ng,'121','35');ck('native-blind-rehost-can-reclock-old-done-history',bool(start_path)and not any(ng['nodes'][e[2]]['reads']and any(q.get('factName')=='q302_msg_ronald_sts_ep1_12'for q in ng['nodes'][e[2]]['reads'])for e in start_path))
 report={'status':'STRUCTURAL_PROPOSAL_CHECKS_PASS'if all(c['pass']for c in checks)else'FAIL','checks':checks,'mutations':mutants,'source_pins':sourcePins,'proposal_manifest':{'path':str(H/'experiments/future_owner_04/NOT_FOR_INTEGRATION.json'),'sha256':sha(H/'experiments/future_owner_04/NOT_FOR_INTEGRATION.json')},'marker_manifest':{'path':str(Path(manifest['markers'])),'sha256':sha(manifest['markers'])},'native_producers':producer_evidence,'native_selected_family':family,'blind_native_rehost_counterexample':start_path,
 'source_and_lifecycle_limits':['This validates a concrete private serialized future-event proposal; coordinator integration/registration/complete provider and ID collision gates are pending.','Generic contactActive predicate with exact native contact path conservatively avoids AddContact notification replay; applicability remains independently reviewable, not certified by constructor serialization.','Existing done1/sent1 or ParentEntered1 without QR7 Armed history is deferred. No saved native clock is adopted or reset.','Marker streaming, engine callbacks/queue, cold reload and future-version transitions remain LIVE_ONLY.'],
 'production_changes':0,'registered':False,'scope':'Current exact four-gig producer routes, native selected news protocol and private resource/lease delta. Does not claim gameplay success or repair approval.'}
 save(out/'evidence.json',report);print(report['status'],len(checks),'checks',len(mutants),'actual readback document mutants')
 if not all(c['pass']for c in checks):print([c['name']for c in checks if not c['pass']]);raise SystemExit(1)
if __name__=='__main__':main()
