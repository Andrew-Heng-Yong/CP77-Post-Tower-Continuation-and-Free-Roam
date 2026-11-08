"""Fresh QR7 successor for independently approved native MQ060 gate repair."""
from pathlib import Path
import sys,shutil,stat
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not C.exists(),'Preserve fresh successor'
e=read(O/'source_epoch_00.json');B=Path(e['candidate']);review=O/'worker_a/reviews/nitro_01/review.json';r=read(review);proposal=O/'worker_c/nitro_authority_03/private_proposed_resource.json';evidence=O/'worker_c/nitro_authority_03/evidence.json'
assert r['status'].startswith('APPROVE_SOURCE_AUTHORITY')and sha(proposal)==r['reviewed_proposal_sha256']and sha(evidence)==r['reviewed_evidence_sha256']
for sub in ['archive_source','package']:
 src=B/sub
 assert all(not p.is_symlink()and not(getattr(p.stat(),'st_file_attributes',0)&0x400)for p in src.rglob('*')),'Unexpected source reparse point'
 shutil.copytree(src,C/sub)
assert all(sha(C/'archive_source'/d)==h for d,h in e['source_resources'].items())
pins=read(O/'worker_c/nitro_authority_03/source_pins.json');native=next(x for x in pins if x['depot']==r'base\quest\bugfixing\quest_bugfixing.questphase');current=next(x for x in pins if x['depot']==r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase')
assert sha(native['raw'])==native['raw_sha256'];assert e['source_resources'][current['depot']]==current['raw_sha256']
write(C/'nitro_plan.json',{'depot':current['depot'],'before':current['raw_sha256'],'proposal':str(proposal),'proposal_sha256':sha(proposal),'evidence':str(evidence),'evidence_sha256':sha(evidence),'review':str(review),'review_sha256':sha(review),'native':native,'guard_ids':[65003,65004],'native_parent_phase':3,'native_condition_nodes':[93,104],'scope':'Append exact registered native three-vehicle OR and purchases>=3 predicates to existing prospective pre-Issued guards only. Preserve all saved IDs/edges/downstream and eight earlier repairs. Copied package archive remains predecessor until explicitly rebuilt.'})
write(O/'adjudications/nitro_01.json',{'status':'APPROVED_MINIMAL_FUTURE_GATE_REPAIR_PENDING_TYPED_AND_PACKAGE_GATES','review':str(review),'review_sha256':sha(review),'evidence':str(evidence),'evidence_sha256':sha(evidence),'proposal':str(proposal),'proposal_sha256':sha(proposal),'source_authority':'Positive current main .gamedef and normal-edge registered root ancestry select native global root/3; standalone authored .quest unregistered alternate is not executing-owner evidence.','scope':read(C/'nitro_plan.json')['scope'],'prior_QR6_conflict_preserved':str(W/'prealpha/quest_restoration_qr6/adjudications/MQ060_source_authority_01.json')})
print({'status':'FRESH_QR7_SUCCESSOR_PREPARED_FOR_APPROVED_REPAIR','candidate':str(C),'changed_runtime_resources_yet':0,'no_ZIP_created':True})
