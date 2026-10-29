"""Freeze the reviewed native action cohort for full-package verification."""
from pathlib import Path
import argparse,hashlib,json
H=Path(__file__).resolve().parent
C=H/'candidate_01'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
p=argparse.ArgumentParser();p.add_argument('--semantic-proof',required=True);a=p.parse_args()
proof=Path(a.semantic_proof).resolve(); verified=read(proof)
assert str(verified['status']).startswith('PASS')
out=C/'cohort_proof_01.json';assert not out.exists()
shooting=[172,173,246,250,289]
vehicle=[98,122,199,204,242,243,251,252,253,256,275,280,287,291,305,311,318,319,342,343]
expected={f'towercontinued/world_actions_wa2/group_{g}_action.questphase' for g in shooting+vehicle}
expected.add('towercontinued/world_actions_wa2/group250_support.questphase')
resources=[{'depot':f.relative_to(C/'source').as_posix().replace('/','\\'),'sha256':digest(f)} for f in sorted((C/'source').rglob('*')) if f.is_file()]
assert {r['depot'].replace('\\','/') for r in resources}==expected
assert {r['depot'].replace('\\','/'):r['sha256'] for r in resources}=={r['depot'].replace('\\','/'):r['sha256'] for r in verified['resources']}
for pin in verified['pins']: assert digest(Path(pin['path']))==pin['sha256'],pin['path']
result={'status':'WA2_SOURCE_COHORT_READY','shooting_groups':shooting,'vehicle_groups':vehicle,
        'preserved_BA1_group':179,'new_support_groups':[250],'total_action_groups_including_BA1':26,
        'resources':resources,'semantic_proof':str(proof),'semantic_proof_sha256':digest(proof),
        'scope':'Five additional native shooting controllers, twenty native vehicle ambient controllers and one exact new support owner. Preserve all BA1/W3 resources and receipts; no encounter reset or native fact writes.',
        'runtime_status':'User confirms BA1 prototype; expanded WA2 gameplay remains unobserved',
        'game_writes':0,'save_writes':0}
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'resources':len(resources),'sha256':digest(out)}))
