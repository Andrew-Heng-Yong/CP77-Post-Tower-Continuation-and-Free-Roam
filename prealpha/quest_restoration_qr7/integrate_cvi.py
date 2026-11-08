"""Coordinator promotion of exact peer-approved serialized CVI04, fresh candidate only."""
from pathlib import Path
import sys,shutil,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
R=C/'repair_cvi_02';assert not R.exists()
planp=O/'worker_a/proposal_04/plan.json';plan=read(planp);mp=O/'worker_a/proposal_readback_04/manifest.json';m=read(mp);rp=O/'worker_b/reviews/CVI02/verification_05/review.json';review=read(rp);gate=O/'worker_a/current_native_donors_gate_01/evidence.json';g=read(gate)
assert review['status']=='APPROVED_BOUNDED_FUTURE_ONLY_STATIC_REPAIR'
assert sha(planp)==review['proposal_plan']['sha256']and sha(mp)==review['proposal_readback_manifest']['sha256']
assert g['status']=='PASS_SIX_CURRENT_NATIVE_DONORS_BYTE_IDENTICAL_TO_APPROVED_CVI_INPUTS'and g['current_provider_count']==g['queried_depots']==6
assert all(sha(x['raw'])==x['raw_sha256']==x['approved_raw_sha256']for x in g['providers'])
src=W/m['raw'];dest=C/'archive_source'/plan['target'];before=sha(dest);assert before==plan['baseline_raw_sha256']and sha(src)==m['raw_sha256']
assert any(x['raw_sha256']==m['raw_sha256']for x in review['fresh_and_reused_raw_readback_pins'])
R.mkdir()
shutil.copyfile(dest,R/'before.questphase');shutil.copyfile(src,dest);assert sha(dest)==m['raw_sha256'];shutil.copyfile(planp,R/'approved_plan.json')
write(R/'promotion.json',{'status':'EXACT_APPROVED_SERIALIZED_CVI04_PROMOTED_NOT_INSTALLED','depot':plan['target'],'before':before,'after':sha(dest),'source_serialized_artifact':str(src),'source_manifest':str(mp),'source_manifest_sha256':sha(mp),'review':str(rp),'review_sha256':sha(rp),'current_donor_gate':str(gate),'current_donor_gate_sha256':sha(gate),'scope':review['approval_scope'],'remaining':review['remaining'],'package_state':'PENDING_REBUILD','game_writes':0,'save_writes':0})
print({'status':'PROMOTED_APPROVED_CVI04','before':before,'after':sha(dest),'package_rebuild_pending':True})
