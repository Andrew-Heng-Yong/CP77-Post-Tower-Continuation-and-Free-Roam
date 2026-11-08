"""Fresh unpackaged successor preserving verified ARR12 candidate01."""
from pathlib import Path
import sys,shutil
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
C=O/'candidate_02';assert not C.exists()
review=O/'groups/G11/reviews/STEVEN/proposal02_verification_01/review.json';r=read(review);assert r['status'].startswith(('APPROVE','PASS')),r['status']
proposal=O/'groups/G15/actor_proposal_02/proposal.json';assert sha(proposal)=='FDA1923D9471E24E45748FAE009CB665F958BAB265BE9695D26ADD6B28266381';p=read(proposal)
assert sha(review)=='23CE232D1D3DE41174249A2AE1522A407369957BE5DB32793BC6370B190A6F48'
ep=read(O/'source_epoch_02.json');src=Path(ep['candidate']);assert sha(src/'archive_source'/p['resource'])==p['before']
fact=p['claim_fact'];assert not any(fact.encode()in f.read_bytes()for f in (src/'archive_source').rglob('*')if f.is_file())
for sub in ['archive_source','package']:
 for f in (src/sub).rglob('*'):assert not f.stat().st_file_attributes&0x400
 shutil.copytree(src/sub,C/sub)
write(C/'actor_repair_plan.json',{'proposal':str(proposal),'proposal_sha256':sha(proposal),'review':str(review),'review_sha256':sha(review),'depot':p['resource'],'before':p['before'],'template':next(x for x in p['source_pins']if x['depot'].endswith('steven_boot.questphase')),'predecessor':str(src),'predecessor_epoch':str(O/'source_epoch_02.json'),'scope':'Unpackaged staging; actor-only exact proposal02. No canonical source change until validated; preserve candidate01.'})
write(C/'staging_manifest_00.json',{'status':'UNPACKAGED_SUCCESSOR_STAGING','predecessor_epoch':str(O/'source_epoch_02.json'),'predecessor_epoch_sha256':sha(O/'source_epoch_02.json'),'pending_repairs':['STEVEN actor-only proposal02'],'game_writes':0,'save_writes':0})
print({'status':'STAGED_FRESH_SUCCESSOR_CANDIDATE02','existing_ARR12_preserved':True,'runtime_changes_so_far':0})
