"""Fresh successor from QR3, only after independent scoped repair approval."""
from pathlib import Path
import sys,shutil
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
C=O/'candidate_01';assert not C.exists(),'Fresh candidate required'
review=O/'groups/G10/reviews/MQ007_followup_addendum.json';r=read(review)
assert r['status']=='APPROVED_PREIMPLEMENTATION_FUTURE_EVENT_ONLY_PRESERVE_NATIVE_HELPER'
e=read(O/'source_epoch_00.json');src=Path(e['candidate'])
for sub in ['archive_source','package']:
 for p in (src/sub).rglob('*'):assert not(p.stat().st_file_attributes & 0x400),'Reparse input refused'
 shutil.copytree(src/sub,C/sub)
write(O/'baseline.json',{'candidate':str(src),'game':read(O/'prepared.json')['game'],'private_resources':e['source_resources'],'package_files':[{'path':f['path'],'after':f['sha256']} for f in e['package_files']],'scope':'Working predecessor is staged QR3, not installed PH3; preserve QR3MQ030/MQ037 fixes'})
write(C/'repair_plan.json',{'proposal':str(O/'groups/G08/regina_proposal_01/proposal.json'),'proposal_sha256':sha(O/'groups/G08/regina_proposal_01/proposal.json'),'review':str(review),'review_sha256':sha(review),'node_ids':[1200,1201,1202,1203],'shared_claim':'PTFRQR4_MQ007_ReacquisitionIssued','owned_finish':'PTFRQR4_MQ007_ReacquisitionFinished','scope':'Future1101event before done/reacquiring only. No retroactive adoption, reset, prefab invention, sector or item change.'})
print('STAGED_QR3_SUCCESSOR_WITH_BOTH_PRIOR_REPAIRS')
