"""QR2 input checkpoint. Read-only outside this fresh successor directory."""
from pathlib import Path
import sys, json, datetime
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/parity_audit'))
from common import read,write,sha,snapshot,tree_metadata
OUT=Path(__file__).resolve().parent
assert not (OUT/'protection_before.json').exists(), 'Pinned QR2 checkpoint already exists'
old=ROOT/'prealpha/quest_restoration_qr1'
b=read(old/'baseline.json'); protected=read(old/'protection_before.json')
inputs=[Path(x) for x in protected['files']]
inputs += [old/x for x in ['queue.json','checkpoint.json','REPORT.md','HANDOFF.md','baseline.json','contract_status_matrix.json','quest_status_matrix.json']]
inputs += [ROOT/x for x in ['AGENTS.md','PROJECT.md','ROADMAP.md','README.md']]
files=snapshot(inputs)
missing=[str(p) for p in inputs if not p.is_file()]
assert not missing, missing
game=b['game']; saves=protected['save_root']
write(OUT/'prepared.json',{'game':game,'source_checkpoint':str(old),'scope':'Three Q01 quest investigations and evidence-backed repairs; no installation'})
write(OUT/'protection_before.json',{'files':files,'game_metadata':tree_metadata(game),'save_root':saves,'save_metadata':tree_metadata(saves)})
q=read(old/'queue.json')
assert q['selected_count']==161 and q['static_verified_count']==0 and q['gameplay_repairs']==0
checks={}
for n in ['candidate_01/compile_01/result.json','candidate_01/tests_01.json','candidate_01/adversarial_01.json','candidate_01/rebuild_01.json']:
 d=read(old/n); checks[n]={'sha256':sha(old/n),'status':d.get('status')}
write(OUT/'inputs.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':b['candidate'],'baseline_manifest_sha256':b['manifest_sha256'],'qr1_reused':checks,'scope':['mq045_victor_debt','mq038_neweridentity','mq035_ozob'],'full_scope':161,'protected_hashes':len(files),'missing':missing,'runtime_changes':[]})
print(json.dumps({'protected_hashes':len(files),'baseline':b['candidate'],'reused':checks}))
