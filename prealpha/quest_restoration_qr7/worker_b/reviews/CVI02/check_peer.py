"""Independent QR7 CVI02 actual-resource review; does not import A's proposer/checker."""
from pathlib import Path
import sys,json,hashlib,copy,collections,argparse,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from lib import *

BASE=H/'reviews/CVI02';A=W/'prealpha/quest_restoration_qr7/worker_a'
TARGET=r'towercontinued\native_gigs_u9\sts_pac_cvi_02_entry.questphase'
ACT=r'base\open_world\fixers\mr_hands\scenes\mr_hands_new_scenes_activators.questphase'
SCENE=r'ep1\openworld\fixers\mr_hands\scenes\mr_hands_combat_zone_default.scene'
MAIN=r'base\open_world\street_stories\pacifica\coastview\sts_pac_cvi_02\phases\sts_pac_cvi_02.questphase'

def eval_condition(c,facts):
 if c['$type']=='questLogicalCondition':
  vs=[eval_condition(z,facts)for z in c['conditions']]
  return all(vs)if c['operation']=='AND'else any(vs)
 if c['$type']=='questFactsDBCondition':return eval_condition(c['type'],facts)
 if c['$type']=='questVarComparison_ConditionType':
  a=facts.get(c['factName'],0);b=c['value'];op=c['comparisonType']
  return {'Equal':a==b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b}.get(op,False)
 raise ValueError(c['$type'])

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);args=ap.parse_args();out=BASE/args.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir();checks=[]
 def ck(name,ok,**ev):checks.append({'name':name,'pass':bool(ok),**ev})
 manifest=read(BASE/'readback_01/manifest.json');docs={};models={}
 for p in manifest:
  ck('raw-pin:'+p['depot'],sha(p['raw'])==p['raw_sha256'])
  ck('fresh-json-pin:'+p['depot'],sha(p['json'])==p['json_sha256'])
  docs[p['depot']]=read(p['json']);models[p['depot']]=Resource(docs[p['depot']]).normalize()
  ck('decode-structure:'+p['depot'],not models[p['depot']]['errors'])
 cur=models['NONPRODUCTION:CVI02'];old=models[TARGET];native=models[ACT]
 g=cur['graphs']['root'];og=old['graphs']['root'];child=cur['graphs']['root/65010'];donor=native['graphs']['root/9']
 ck('exact-new-local-ids',set(g['nodes'])-set(og['nodes'])=={str(z)for z in range(65007,65014)})
 ck('root-metadata-and-lease-obligations-preserved',old['metadata']==cur['metadata']and old['root_prefabs']==cur['root_prefabs'])
 ck('old-embedded-child-preserved',old['graphs']['root/2']==cur['graphs']['root/2'])
 ck('only-old-node65002-payload-changed',[i for i in og['nodes']if og['nodes'][i]['payload']!=g['nodes'][i]['payload']]==['65002'])
 ck('new-guard-retains-entire-original-AND-as-first-term',g['nodes']['65002']['payload']['condition']['conditions'][0]==og['nodes']['65002']['payload']['condition'])
 native_payloads={i:copy.deepcopy(n['payload'])for i,n in donor['nodes'].items()}
 native_payloads['13']['sceneLocation']['nodeRef']=copy.deepcopy(child['nodes']['13']['payload']['sceneLocation']['nodeRef'])
 ck('exact-native-specialized-child-with-explicit-marker-qualification',set(child['nodes'])==set(donor['nodes'])and all(child['nodes'][i]['payload']==p and child['nodes'][i]['sockets']==donor['nodes'][i]['sockets']for i,p in native_payloads.items())and child['edges']==donor['edges'])
 ck('native-scene-and-source-marker-shortname-retained',g['nodes']['65010']['refs']==[]and child['nodes']['13']['refs']==donor['nodes']['13']['refs']and child['nodes']['13']['node_refs'][0].endswith('/'+donor['nodes']['13']['node_refs'][0]))
 req=[['65002','Out','65003','In'],['65003','Out','65007','In'],['65007','True','65008','In'],['65008','Out','65009','In'],['65009','Out','65010','In1'],['65009','Out','2','In1'],['65007','False','2','In1'],['65006','Out','65011','In'],['65011','Out','65012','In'],['65012','CutSource','65010','CutDestination'],['65012','Out','65013','In']]
 for e in req:ck('new-route:'+':'.join(e),e in g['edges'])
 removed=set(map(tuple,og['edges']))-set(map(tuple,g['edges']))
 ck('only-one-original-edge-removed',removed=={('65003','Out','2','In1')})
 # all exact history predicates are tested against the serialized condition, not plan prose.
 cond=g['nodes']['65002']['payload']['condition'];facts={q['factName']:q['value']for q in walk(og['nodes']['65002']['payload']['condition'])if q.get('$type')=='questVarComparison_ConditionType'}
 facts['ep1_installed']=1
 ck('abstract-fresh-admission-true',eval_condition(cond,facts))
 plan=read(A/'proposal_03/plan.json')
 for f in plan['guarded_native_history']+['PTFRQR7_CVI02_CustomControllerIssued','PTFRU9_sts_pac_cvi_02_ParentEntered']:
  f1=dict(facts);f1[f]=1;ck('saved-or-issued1-defers:'+f,not eval_condition(cond,f1))
 facts0=dict(facts);facts0['ep1_installed']=0;facts0[plan['guarded_native_history'][0]]=1
 ck('non-EP1-original-admission-remains',eval_condition(cond,facts0))
 # source proof of the cleanup blind spot: native muted branch deliberately needs no call.
 main=models[MAIN];pg=main['graphs']['root/8/10']
 muted_route=[['200','True','201','In1'],['201','Out1','199','Active'],['199','Out','186','In1']]+path(pg,'186','84')
 ck('source-muted-no-EP1-call-route-to-original-output',all(e in pg['edges']for e in muted_route)and pg['nodes']['200']['payload']['condition']['type']['$type']=='questPhoneMuted_ConditionType')
 idle=g['nodes']['65011']['payload']['condition']['type']
 ck('cleanup-is-unscoped-EndCall-not-selected-scene-idle-proof',idle['$type']=='questPhone_ConditionType'and idle['callPhase']=='EndCall'and idle['caller']is None and idle['addressee']is None)
 actors=Resource(docs[SCENE]).root['actors'];physical=actors[0];holo=actors[1]
 ck('unchanged-global-physical-acquisition-plan-visible',physical['actorName']=='mr_hands'and physical['acquisitionPlan']=='spawnSet'and physical['spawnDespawnParams']['spawnOnStart']==1 and physical['spawnDespawnParams']['isEnabled']==1)
 ck('exact-physical-and-holo-spawnsets-distinct',val(physical['spawnSetParams']['reference'])=='#mr_hands_combat_zone'and val(holo['spawnSetParams']['reference'])=='#mr_hands_holo')
 # Fresh readback malformed mutants: change one source history leaf, not a mirrored plan list.
 mutations=[];doc=copy.deepcopy(docs['NONPRODUCTION:CVI02'])
 rr=Resource(doc);graph=rr.d(rr.root['graph']);guard=next(rr.d(z)for z in graph['nodes']if rr.d(z)['id']==65002)
 f=plan['guarded_native_history'][0]
 for q in walk(rr.d(guard['condition'])):
  if q.get('factName')==f:q['value']=1
 mg=Resource(doc).normalize()['graphs']['root'];f1=dict(facts);f1[f]=1
 mutations.append({'fault':'already-issued-native-prebrief-admitted-by-changed-source-guard','detected':eval_condition(mg['nodes']['65002']['payload']['condition'],f1),'document_path':str(out/'changed_history_guard.json')});save(out/'changed_history_guard.json',doc)
 # Scene startup uncertainty is not converted into a synthetic failing assertion.
 report={'status':'STRUCTURAL_CHECKS_PASS_REPAIR_NOT_APPROVED'if all(c['pass']for c in checks)and all(m['detected']for m in mutations)else'REVIEW_CHECK_FAILURE','source_epoch':{'path':str(W/'prealpha/quest_restoration_qr6/source_epoch_00.json'),'sha256':sha(W/'prealpha/quest_restoration_qr6/source_epoch_00.json')},
 'reviewed_plan':{'path':str(A/'proposal_03/plan.json'),'sha256':sha(A/'proposal_03/plan.json')},'reviewed_serialization_manifest':{'path':str(A/'proposal_readback_03/manifest.json'),'sha256':sha(A/'proposal_readback_03/manifest.json')},'fresh_raw_readbacks':manifest,'checks':checks,'mutations':mutations,
 'source_muted_route':{'depot':MAIN,'graph':'root/8/10','edges':muted_route,'note':'Whole-owner completion still follows native root/8→cleanup root/8/4, including authored3-game-hour waits. No new end-call request is required on this native muted branch.'},
 'not_approved':[
 {'id':'GLOBAL_SCENE_ACQUISITION','evidence':{'depot':SCENE,'physical_actor':physical,'holo_spawn_set':holo['spawnSetParams']},'missing':'Source/engine proof that selected holo entries can start while enabled global physical spawnSet actor cannot be acquired. Selected graph closure alone proves performer usage, not acquisition policy.'},
 {'id':'TERMINAL_IDLE_AND_NO_CALL_PATH','evidence':g['nodes']['65011']['payload'],'missing':'Cleanup guard is generic EndCall after OwnerFinished, not original selected-scene idle. Source no-call muted branch permits no relevant future EndCall event. Exact level/event semantics and a path-complete idle/retirement protocol are not established; unrelated future call settlement must not be treated as selected-owner acknowledgement.'},
 {'id':'SAVED_RESOURCE_TRANSITION','missing':'Original ids/fields are preserved and initial guard rejects entered histories, but a saved graph already past65003 cannot be retrofitted by fresh admission checks. Must remain explicitly deferred and live transition fixtures pending.'}],
 'decision':'Do not integrate as a complete five-contract repair. Marker placement may independently remove the old FO1-marker-lease assumption; this review does not assert marker absence or a proven engine startup failure.',
 'runtime_changes':0,'production_writes':0}
 save(out/'review.json',report);print(report['status'],len(checks),'checks',len(mutations),'document mutants')
 if not all(c['pass']for c in checks):print([c['name']for c in checks if not c['pass']]);raise SystemExit(1)
if __name__=='__main__':main()
