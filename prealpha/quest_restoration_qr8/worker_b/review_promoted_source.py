"""B independent actual coordinator successor readback gate; no root imports."""
from lib import *
from check_late_future import comparison_errors,evaluate,CASES
import argparse,copy
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=H/'reviews/promoted_source'/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);checks=[];pins=[]
 def ck(n,v,**e):checks.append({'name':n,'pass':bool(v),**e})
 def pin(f,expected=None):
  h=sha(f);pins.append({'path':str(Path(f).resolve()),'sha256':h})
  if expected:ck('pin:'+str(f),h==expected)
  return h
 C=W/'prealpha/quest_restoration_qr8/candidate_01';prom=C/'repair_late_future_01/promotion.json';p=read(prom);plan=read(H/'proposal_late_future_03/NOT_FOR_INTEGRATION.json');cp=Path(p['source_review']);pin(cp,p['source_review_sha256']);review=read(cp)
 ck('independent-C-approved-exact-private-plan',review['status']=='APPROVED_MINIMAL_SOURCE_CONFIRMED_FOUR_GATE_REPAIR_FOR_COORDINATOR_INTEGRATION');pin(prom);pin(p['plan'],p['plan_sha256']);pin(plan['raw'],plan['raw_sha256']);pin(plan['json'],plan['json_sha256'])
 canonical=next(x for x in read(H/'readback_06/manifest.json')if x['depot']==NEWS);pin(canonical['raw'],plan['raw_sha256']);pin(canonical['json'],canonical['json_sha256']);pin(C/'repair_late_future_01/before.questphase',p['before'])
 beforepin=next(x for x in read(H/'readback_01/manifest.json')if x['depot']==NEWS);pin(beforepin['raw'],p['before']);pin(beforepin['json'],beforepin['json_sha256']);before=Resource(read(beforepin['json'])).normalize();afterdoc=read(canonical['json']);after=Resource(afterdoc).normalize();approved=Resource(read(plan['json'])).normalize()
 ck('own-fresh-actual-candidate-whole-model-equals-reviewed-prototype',after==approved and not after['errors'])
 ck('entire-resource-only-four-approved-admission-changes',not comparison_errors(before,after),errors=comparison_errors(before,after))
 oldg=before['graphs']['root/202'];newg=after['graphs']['root/202'];ids=set(map(str,read(W/'prealpha/quest_restoration_qr7/worker_b/future_protocol_spec_01.json')['kept_native_ids']))
 for i in sorted(ids,key=int):ck('native-protocol-node-'+i,oldg['nodes'][i]==newg['nodes'][i])
 for gp,graph in before['graphs'].items():
  current=after['graphs'][gp];ck('same-saved-identities-sockets-edges:'+gp,set(graph['nodes'])==set(current['nodes'])and graph['entries']==current['entries']and graph['edges']==current['edges']and all(n['sockets']==current['nodes'][i]['sockets']for i,n in graph['nodes'].items()))
 ck('same-root-entire-guard-receipt-lifecycle',before['graphs']['root']==after['graphs']['root'])
 ck('same-private-marker-leases-and-no-new-scene-support',before['root_prefabs']==after['root_prefabs']and all(n['prefabs']==after['graphs'][gp]['nodes'][i]['prefabs']for gp,g in before['graphs'].items()for i,n in g['nodes'].items()))
 rm=read(C/'repair_late_future_01/readback_01/manifest.json');pin(rm['after_json'],rm['after_json_sha256']);pin(rm['before_json'],rm['before_json_sha256']);ck('coordinator-both-typed-models-independently-agree',Resource(read(rm['after_json'])).normalize()==after and Resource(read(rm['before_json'])).normalize()==before)
 changed=[]
 for gp,g in before['graphs'].items():
  changed +=[[gp,i]for i,n in g['nodes'].items()if n['payload']!=after['graphs'][gp]['nodes'][i]['payload']]
 ck('exact-four-changed-node-payload-identities',changed==[['root/202',str(i)]for i in(200,201,202,203)],changed=changed)
 for code,gid,wait,*_ in CASES:
  f={'sts_ep1_'+code+'_done':1,'q302_msg_ronald_sts_ep1_'+code:0,'PTFRQR7_RonaldNews_Armed_sts_ep1_'+code:1,'PTFRU9_sts_ep1_'+code+'_ParentEntered':1};old=oldg['nodes'][str(gid)]['payload']['condition'];new=newg['nodes'][str(gid)]['payload']['condition'];ck('actual-successor-fail-before-pass-after:'+code,not evaluate(old,f)and evaluate(new,f))
 epoch=read(W/'prealpha/quest_restoration_qr7/source_epoch_04.json');preserved=[BO,BS,r'towercontinued\quest_restoration_qr7\ronald_news_markers.streamingblock',r'towercontinued\quest_restoration_qr7\ronald_news_markers.streamingsector',r'towercontinued\native_gigs_u9\sts_pac_cvi_02_entry.questphase']+['towercontinued\\native_gigs_u9\\sts_ep1_'+code+'_entry.questphase'for code in('01','03','08','12')]
 for d in preserved:pin(C/'archive_source'/d,epoch['source_resources'][d])
 xl=C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl';pin(xl,'F22693981B0A10DB21B47AFAD7FC8BCAEF1F021D9EA99548BA4FF80F56D18245');ck('A-static-registration-namespace-applicability-names-unchanged',p['depot']==NEWS and p['unchanged_XL_sha256']==sha(xl))
 # Actual final-export gate reversion must fail the exact source-derived four-delta contract.
 bad=copy.deepcopy(afterdoc);rr=Resource(bad);g=rr.d(next(rr.d(x)for x in rr.d(rr.root['graph'])['nodes']if rr.d(x)['id']==202)['phaseGraph']);n=next(rr.d(x)for x in g['nodes']if rr.d(x)['id']==200);cond=rr.d(n['condition']);cond['conditions'][0]=copy.deepcopy(rr.d(cond['conditions'][0])['conditions'][0]);errors=comparison_errors(before,rr.normalize());ck('actual-successor-reverted-gate-control-rejected',bool(errors));save(out/'reverted_gate_mutant.json',bad)
 result={'status':'PASS_INDEPENDENT_ACTUAL_SUCCESSOR_SOURCE_READBACK_WITH_PACKAGE_PENDING'if all(c['pass']for c in checks)else'FAIL','checks':checks,'check_count':len(checks),'reviewed_input_pins':pins,'new_raw_sha256':canonical['raw_sha256'],'changed_nodes':changed,'actual_document_negative_controls':1,'package_state':'Not assessed; successor archive build and extraction/preservation/compile gates are coordinator/A-owned.','limits':['No live game, save, phone queue, clock or lease observation.','First-enrollment menu/contact/native-bar-support failures remain held.','Existing processed case gates never reentered; changed predicate refresh on particular active saved owners requires controlled transition observation.'],'runtime_writes':0,'no_root_checker_import':True}
 save(out/'review.json',result);save(out/'hash_observations.json',list(OBS.values()));print(result['status'],len(checks),'checks')
 if result['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
