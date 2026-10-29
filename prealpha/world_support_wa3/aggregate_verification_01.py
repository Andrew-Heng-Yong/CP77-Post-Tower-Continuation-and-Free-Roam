"""Bind independent binary audits to every and only final WA3 resource."""
from pathlib import Path
from hashlib import sha256
import argparse,json
H=Path(__file__).resolve().parent;C=H/'candidate_01'
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
parser=argparse.ArgumentParser();parser.add_argument('--evidence',action='append',default=[]);args=parser.parse_args()
out=C/'independent_semantic_01.json';assert not out.exists(),'Preserve semantic proof'
proofs=[C/'independent_owners_01.json',H/'private_sectors/verification_06.json',H/'private_sectors/verification_ep1_01.json',H/'environment_variants/independent_01.json',H/'greeting/independent_01.json']
resources={};pins={};counts=[]
def pin(path,expected=None):
    path=Path(path).resolve();actual=digest(path)
    assert expected is None or actual==expected,'Changed semantic input: '+str(path)
    pins[str(path)]={'path':str(path),'sha256':actual}
for proof in proofs:
    d=read(proof);assert d['status'].startswith('PASS'),proof
    pin(proof)
    for p in d['pins']:pin(p['path'],p['sha256'])
    for r in d['resources']:
        depot=r['depot'].replace('/','\\');assert depot not in resources,'Duplicate semantic resource '+depot
        assert digest(C/'source'/depot)==r['sha256'],depot
        resources[depot]={'depot':depot,'sha256':r['sha256']}
    counts.append({'proof':str(proof),'resources':len(d['resources']),'checks':d.get('checks_passed',d.get('check_count',len(d.get('checks',[]))))})
cohort=C/'cohort_proof_01.json';d=read(cohort);assert d['status']=='WA3_SOURCE_COHORT_READY';pin(cohort)
assert {r['depot'].replace('/','\\'):r['sha256'] for r in d['resources']}=={k:v['sha256'] for k,v in resources.items()}
actual={p.relative_to(C/'source').as_posix().replace('/','\\'):digest(p) for p in (C/'source').rglob('*') if p.is_file()}
assert actual=={k:v['sha256'] for k,v in resources.items()},'Unreviewed/absent source files'
evidence=[H/'private_sectors/selection_06.json',H/'private_sectors/selection_ep1_01.json',H/'native_review/ep1_ambient_scene_assessment_01.json',H/'native_review/ep1_passive_filter_assessment_01.json',H/'native_review/monument_support_assessment_01.json',H/'native_review/outside1004_assessment_01.json',H/'native_review/border_support_assessment_01.json',H/'environment_variants/assessment_01.json',H/'greeting/assessment_01.json',H/'computer_independent_01.json']
evidence.extend(Path(p).resolve() for p in args.evidence)
for proof in evidence:
    d=read(proof);assert d['status'].startswith(('PASS','SELECTED')),proof
    pin(proof)
    for p in d.get('pins',[]):pin(p['path'],p['sha256'])
pin(Path(__file__))
result={'status':'PASS_INDEPENDENT_WA3_COHORT','resources':list(resources.values()),'resource_count':len(resources),'component_reviews':counts,'evidence':[str(p.resolve()) for p in evidence],'pins':list(pins.values()),'runtime_verified':False,'game_writes':0,'save_writes':0}
out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'status':result['status'],'resources':len(resources),'pins':len(pins)}))
