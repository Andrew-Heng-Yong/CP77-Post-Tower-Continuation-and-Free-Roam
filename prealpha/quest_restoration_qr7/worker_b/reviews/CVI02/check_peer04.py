"""Independent CVI04 review of source callbacks, fresh typed proposal and existing actor support."""
from pathlib import Path
import sys,copy,struct,zlib,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lib import *
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_peer import eval_condition,TARGET,ACT,SCENE,MAIN

BASE=H/'reviews/CVI02';A=W/'prealpha/quest_restoration_qr7/worker_a'
FLIGHTS=['PTFRQR7_CVI02_PrebriefInFlight','PTFRQR7_CVI02_FailedInFlight','PTFRQR7_CVI02_PerfectInFlight']
ROUTES=[('17','prebrief_in',21,24,['prebrief_out','prebrief_rejected_out']),('16','debrief_failed_in',22,25,['debrief_failed_end_out','debrief_rejected_failed_out']),('18','debrief_perfect_in',23,26,['debrief_perfect_end_out','debrief_rejected_perfect_out'])]

def flight_errors(m,scene):
 errors=[];g=m['graphs']['root'];c=m['graphs']['root/65010']
 def need(ok,e):
  if not ok:errors.append(e)
 for j,(listener,inp,start,clear,outs)in enumerate(ROUTES):
  f=FLIGHTS[j]
  for n,v in [(start,1),(clear,0)]:need(c['nodes'][str(n)]['writes']==[{'$type':'questSetVar_NodeType','factName':f,'setExactValue':1,'value':v}],f'flight-write:{n}')
  need([listener,'Out',str(start),'In']in c['edges']and[str(start),'Out','13',inp]in c['edges'],f'flight-before-scene:{inp}')
  for out in outs:
   need(['13',out,str(clear),'In']in c['edges'],f'flight-clear-real-output:{out}')
   ix=next(x for x in scene.root['exitPoints']if val(x['name'])==out)['nodeId']['id']
   need(scene.normalize()['graphs']['scene']['nodes'][str(ix)]['payload'].get('type')=='Terminating',f'nonterminating-callback:{out}')
 idle=g['nodes']['65011']['payload']['condition'];need(idle.get('$type')=='questLogicalCondition'and idle.get('operation')=='AND','idle-must-be-three-way-AND')
 got=[(x.get('factName'),x.get('comparisonType'),x.get('value'))for x in walk(idle)if x.get('$type')=='questVarComparison_ConditionType']
 need(sorted(got)==sorted((f,'Equal',0)for f in FLIGHTS),'idle-exact-three-private-zero-conditions')
 return errors

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args();out=BASE/args.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir();checks=[];pins=[]
 def ck(name,ok,**ev):checks.append({'name':name,'pass':bool(ok),**ev})
 oldma=read(BASE/'readback_01/manifest.json');oldmodels={z['depot']:Resource(read(z['json'])).normalize()for z in oldma if not z['depot'].startswith('NONPRODUCTION')}
 for p in oldma:
  if p['depot'].startswith('NONPRODUCTION'):continue
  ck('retained-source-pins:'+p['depot'],sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256']);pins.append(p)
 p=read(BASE/'readback_04/manifest.json');ck('independent-fresh04-readback-pin',sha(p['raw'])==p['raw_sha256']and sha(p['json'])==p['json_sha256']);pins.append(p)
 doc=read(p['json']);r=Resource(doc);m=r.normalize();g=m['graphs']['root'];c=m['graphs']['root/65010'];old=oldmodels[TARGET];native=oldmodels[ACT]['graphs']['root/9']
 scene=Resource(read(next(z['json']for z in oldma if z['depot']==SCENE)))
 ck('proposal-no-structural-errors',not m['errors'])
 ck('exact-eight-new-root-ids',set(g['nodes'])-set(old['graphs']['root']['nodes'])=={str(i)for i in range(65007,65015)})
 ck('all-original-root-ids-preserved',set(old['graphs']['root']['nodes'])<=set(g['nodes']))
 ck('old-embedded-owner-byte-normalized-unchanged',old['graphs']['root/2']==m['graphs']['root/2'])
 ck('root-metadata-prefab-saved-binding-preserved',old['metadata']==m['metadata']and old['root_prefabs']==m['root_prefabs'])
 ck('only-old-payload65002-changed',[i for i,n in old['graphs']['root']['nodes'].items()if n['payload']!=g['nodes'][i]['payload']]==['65002'])
 ck('entire-original-admission-retained',g['nodes']['65002']['payload']['condition']['conditions'][0]==old['graphs']['root']['nodes']['65002']['payload']['condition'])
 facts={z['factName']:z['value']for z in walk(old['graphs']['root']['nodes']['65002']['payload']['condition'])if z.get('$type')=='questVarComparison_ConditionType'};facts['ep1_installed']=1
 cond=g['nodes']['65002']['payload']['condition'];ck('fresh-abstract-admission-allowed',eval_condition(cond,facts))
 histories=['new_sts_pac_cvi_02_holocall_prebrief','new_sts_pac_cvi_02_holocall_debrief_failed','new_sts_pac_cvi_02_holocall_debrief_perfect','new_q110_prebrief_rejected_or_end','new_q110_debrief_failed_end','new_q110_debrief_perfect_end','new_q110_rejected_failed_out','new_q110_rejected_perfect_out']
 for f in histories+FLIGHTS+['PTFRQR7_CVI02_CustomControllerIssued','PTFRU9_sts_pac_cvi_02_ParentEntered']:
  bad=dict(facts);bad[f]=1;ck('old-state-positive-defers:'+f,not eval_condition(cond,bad))
 ck('exact-six-private-inflight-local-ids',set(c['nodes'])-set(native['nodes'])=={str(i)for i in range(21,27)})
 for i,n in native['nodes'].items():
  expected=copy.deepcopy(n['payload'])
  if i=='13':expected['sceneLocation']['nodeRef']=copy.deepcopy(c['nodes']['13']['payload']['sceneLocation']['nodeRef'])
  ck('native-specialized-payload-and-sockets:'+i,c['nodes'][i]['payload']==expected and c['nodes'][i]['sockets']==n['sockets'])
 expected_edges=set(map(tuple,native['edges']))
 for j,(listener,inp,start,clear,outs)in enumerate(ROUTES):
  expected_edges.remove((listener,'Out','13',inp));expected_edges.update([(listener,'Out',str(start),'In'),(str(start),'Out','13',inp)])
  for o in outs:
   # Native ACK callback edges stay direct; the same terminating output clears the private flight in parallel.
   expected_edges.add(('13',o,str(clear),'In'))
 ck('all-specialized-edges-exact-with-start-splices-and-parallel-terminal-clears',set(map(tuple,c['edges']))==expected_edges)
 ck('native-RET-INT-never-clear-flight',['13','Holocall RET','7','In']in c['edges']and['13','Holocall INT','8','In']in c['edges']and all(not(e[0]=='13'and e[1]in ['Holocall RET','Holocall INT']and e[2]in ['24','25','26'])for e in c['edges']))
 ck('real-six-terminating-callbacks-and-scoped-flight-protocol',not flight_errors(m,scene),errors=flight_errors(m,scene))
 for e in [['65006','Out','65014','In'],['65014','True','65011','In'],['65011','Out','65012','In'],['65012','CutSource','65010','CutDestination'],['65012','Out','65013','In']]:ck('scoped-cleanup-edge:'+str(e),e in g['edges'])
 ck('only-issued-owner-enters-cleanup',g['nodes']['65014']['reads']==[{'$type':'questVarComparison_ConditionType','comparisonType':'Equal','factName':'PTFRQR7_CVI02_CustomControllerIssued','value':1}]and not any(e[0]=='65014'and e[1]=='False'for e in g['edges']))
 ck('all-three-flights-zero-no-call-route-is-idle',eval_condition(g['nodes']['65011']['payload']['condition'],{}))
 for f in FLIGHTS:ck('any-single-inflight-blocks-cleanup:'+f,not eval_condition(g['nodes']['65011']['payload']['condition'],{f:1}))
 ck('no-unrelated-EndCall-condition-remains',not any(q.get('$type')=='questPhone_ConditionType'for q in walk(g['nodes']['65011']['payload'])))
 # Accepted parser scope is proven by native refusal, not by the empty marker event's fields.
 defaults=read(A/'default_members_01/evidence.json');dr=defaults['records'];ck('exact-current-source-default-probe-pin',sha(defaults['source'])==defaults['source_sha256'])
 ck('all11-default-members-proven-by-prefix-refusal',len(dr)==12 and all(z['accepted_before_refusal']==i and z['event_count']==i+1 and z['exact_refused_member_error']=='Invalid default val for: "communityCommunityTemplateData.entries"'for i,z in enumerate(dr[:11]))and dr[11]['status']=='NoError'and dr[11]['event_count']==11)
 exports=read(A/'actor_provider_exports_01/manifest.json');ep=next(z for z in exports['records']if z['source_pin']['raw'].endswith('provider_3.streamingsector'));ar=Resource(read(W/ep['json']));ab=Path(W/ep['buffer']).read_bytes()
 ck('exact-current-actor-provider-and-export-and-buffer-pins',sha(ep['source_pin']['raw'])==ep['source_pin']['raw_sha256']and sha(W/ep['json'])==ep['json_sha256']and sha(W/ep['buffer'])==ep['buffer_sha256'])
 registry=ar.d(ar.root['nodes'][3495]);ck('actual-community-registry-type',registry['$type']=='worldCommunityRegistryNode')
 for name,ix,area,setup,cid,spot in [('physical',7,3096,7785,'9917420432923748660','#ws_mr_hands_default'),('holo',374,3463,8152,'11987357043163412073','#mr_hands_holocall_workspot')]:
  community=registry['communitiesData'][ix];template=ar.d(community['template']);character=ar.d(template['entries'][0]);phase=ar.d(character['phases'][0]);area_node=ar.d(ar.root['nodes'][area]);word=struct.unpack_from('<Q',ab,setup*144+0x70)[0]
  ck('actual-area-binding:'+name,word&0x7ffff==area and str(area_node['sourceObjectId']['hash'])==cid and str(community['communityId']['entityId']['hash'])==cid)
  ck('populated-correct-native-character-and-workspot:'+name,len(template['entries'])==1 and int(val(character['characterRecordId']))==((len('Character.mr_hands')<<32)|zlib.crc32(b'Character.mr_hands'))and val(phase['timePeriods'][0]['spotNodeRefs'][0])==spot)
  ck('initial-community-not-forced-active:'+name,community['entriesInitialState'][0]['entryActiveOnStart']==0)
 # Source-bound support and no omitted original ancestor PIP, with the current preserved generic studio.
 native_ep=oldmodels[r'ep1\quest\ep1.questphase'];native_ow=oldmodels[r'ep1\openworld\ep1_open_world.questphase'];act=oldmodels[ACT]
 ck('specialized-owner-all-actual-ancestors-no-omitted-PIP',all(not z['root_prefabs']for z in [native_ep,native_ow,act])and not native_ep['graphs']['root']['nodes']['10']['prefabs']and not native_ep['graphs']['root/10']['nodes']['5']['prefabs']and not native_ow['graphs']['root']['nodes']['28']['prefabs']and not act['graphs']['root']['nodes']['9']['prefabs'])
 ck('actual-native-ancestor-caller-bindings',native_ep['graphs']['root/10']['nodes']['5']['refs']==[r'ep1\openworld\ep1_open_world.questphase']and native_ow['graphs']['root']['nodes']['28']['refs']==[ACT])
 supports=read(A/'actor_context_01/support_pins.json')
 for s in supports:ck('preserved-generic-support-pin:'+s['depot'],sha(s['raw'])==s['sha256']and sha(s['json'])==s['json_sha256'])
 support_models={s['depot']:Resource(read(s['json'])).normalize()for s in supports}
 ck('current-U9-generic-Hands-parent-binding',support_models[r'towercontinued\gig_phone_u9\fixer_initializer.questphase']['graphs']['root']['nodes']['73']['refs']==[r'base\quest\holocalls\mr_hands\mr_hands_holocall.questphase'])
 ck('current-PH3-both-original-studio-prefabs-retained',support_models[r'towercontinued\phone_studios_ph3\studio_support.questphase']['graphs']['root']['nodes']['3']['prefabs']==['$/03_night_city/c_pacifica/#holocalls_studio_ep1','$/03_night_city/ne2/#holocalls_studio'])
 # Mutate independently fresh actual JSON and re-normalize; do not call A's tests.
 mutations=[]
 for name,nid,value in [('lost-flight-before-scene',21,0),('premature-stuck-flight-clear',24,1)]:
  d=copy.deepcopy(doc);rr=Resource(d);graph=rr.d(rr.root['graph']);cn=next(rr.d(z)for z in graph['nodes']if rr.d(z)['id']==65010);cg=rr.d(cn['phaseGraph']);node=next(rr.d(z)for z in cg['nodes']if rr.d(z)['id']==nid);rr.d(node['type'])['value']=value
  err=flight_errors(Resource(d).normalize(),scene);save(out/(name+'.json'),d);mutations.append({'fault':name,'detected':bool(err),'errors':err})
 d=copy.deepcopy(doc);rr=Resource(d);graph=rr.d(rr.root['graph']);node=next(rr.d(z)for z in graph['nodes']if rr.d(z)['id']==65011);rr.d(node['condition'])['operation']='OR';err=flight_errors(Resource(d).normalize(),scene);save(out/'unsafe-OR-idle.json',d);mutations.append({'fault':'unsafe-OR-idle','detected':bool(err),'errors':err})
 for mu in mutations:ck('actual-resource-mutant:'+mu['fault'],mu['detected'])
 report={'status':'APPROVED_BOUNDED_FUTURE_ONLY_STATIC_REPAIR'if all(z['pass']for z in checks)else'FAIL','checks':checks,'mutations':mutations,'fresh_and_reused_raw_readback_pins':pins,
 'proposal_plan':{'path':str(A/'proposal_04/plan.json'),'sha256':sha(A/'proposal_04/plan.json')},'proposal_readback_manifest':{'path':str(A/'proposal_readback_04/manifest.json'),'sha256':sha(A/'proposal_readback_04/manifest.json')},
 'support_pins':supports,'default_members_evidence':{'path':str(A/'default_members_01/evidence.json'),'sha256':sha(A/'default_members_01/evidence.json')},'actor_export_manifest':{'path':str(A/'actor_provider_exports_01/manifest.json'),'sha256':sha(A/'actor_provider_exports_01/manifest.json')},
 'approval_scope':'The serialized04 proposal supplies the missing original specialized listener only for future fresh EP1 CVI02 admission; all8 old native requests/outcomes,3 private flights and Issued must be0 before original ParentEntered. Native callback facts/RET/INT and existing old owner ids remain. No older entered/requested state is repaired or adopted.',
 'supersession':'proposal03 review correctly rejected generic EndCall cleanup;04 replaces it with real terminating outputs controlling scoped flights. Exact current AlwaysLoaded actor/marker/studio ownership resolves the earlier omitted-static-support hypothesis; metadata alone was insufficient either to prove startup or to assert a missing physical-default owner.',
 'remaining':['Coordinator must prove effective providers and final archive/ZIP delta/preservation before staging approval.','Old entered/pending-request/saved-owner fixtures defer; no retrospective adoption and no all-save restoration claim.','Actual scene acquisition/render, call scheduling, interrupts and save reload remain LIVE_ONLY native engine properties. The source structure is consistent; gameplay success is not inferred.'],
 'runtime_writes':0,'source_epoch_base':'QR6:00; affected inputs unchanged at QR7:01'}
 save(out/'review.json',report);print(report['status'],len(checks),'checks',len(mutations),'actual JSON mutants')
 if not all(z['pass']for z in checks):print([z['name']for z in checks if not z['pass']]);raise SystemExit(1)
if __name__=='__main__':main()
