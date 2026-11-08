"""Approve actual independently reviewed bytes and prepare the single rebuild."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (O/'approved_changes_02.json').exists()
rp=O/'groups/G02/reviews/ARR12_serialized/verification_02/review.json';r=read(rp)
assert r['status'].startswith(('PASS','APPROVE')),r['status']
p=read(O/'approved_changes_01.json');p['version']=2;p['status']='APPROVED_EXACT_SERIALIZED_SUCCESSOR_FOR_PACKAGE_VALIDATION';p['resources'][0]['independent_serialized_review']=str(rp);p['resources'][0]['independent_serialized_review_sha256']=sha(rp);p['resources'][0]['tests'].append(str(rp));p['supersedes_allowlist']=str(O/'approved_changes_01.json');p['supersedes_allowlist_sha256']=sha(O/'approved_changes_01.json')
write(O/'approved_changes_02.json',p)
s=(W/'prealpha/quest_restoration_qr4/rebuild_candidate.ps1').read_text(encoding='utf-8-sig').replace('approved_changes_01.json','approved_changes_02.json')
(O/'rebuild_candidate.ps1').write_text(s,encoding='utf-8')
print({'status':p['status'],'changed_resources':len(p['resources'])})
