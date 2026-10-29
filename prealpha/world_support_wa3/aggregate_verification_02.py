"""Bind independent owner, sector and controller reviews to candidate02 resources."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;C=H/'candidate_02'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
resources={};pins={};components=[]
def pin(p):
    p=Path(p).resolve();pins[str(p)]={'path':str(p),'sha256':sha(p)}
def add(proof,rows,count):
    pin(proof)
    for r in rows:
        depot=r['depot'].replace('/','\\');source=C/'source'/depot
        assert depot not in resources and sha(source)==r['sha256'],depot
        resources[depot]={'depot':depot,'sha256':r['sha256']}
    components.append({'proof':str(proof),'resources':len(rows),'checks':count})
owners=C/'independent_owners_01.json';o=read(owners);assert o['status']=='PASS' and o['owners']==296
add(owners,o['resources'],o['checks_passed'])
for p in o['pins']:assert sha(p['path'])==p['sha256'];pin(p['path'])
private=H/'private_sectors/verification_comprehensive_01.json';v=read(private)
build=H/'private_sectors/build_comprehensive_proof_09.json';b=read(build)
assert v['status']=='PASS_COMPREHENSIVE_PRIVATE_SUPPORT' and v['source_proof_sha256']==sha(build) and v['group_count']==315
add(private,b['resources'],v['checks']);pin(build)
ep=H/'private_sectors/verification_ep1_01.json';e=read(ep);assert e['status'].startswith('PASS')
add(ep,e['resources'],len(e['checks']))
for p in e.get('pins',[]):assert sha(p['path'])==p['sha256'];pin(p['path'])
for file in [H/'environment_variants/independent_01.json',H/'greeting/independent_01.json']:
    d=read(file);assert d['status'].startswith('PASS')
    add(file,d['resources'],d.get('checks_passed',len(d.get('checks',[]))))
    for p in d.get('pins',[]):assert sha(p['path'])==p['sha256'];pin(p['path'])
cohort=C/'cohort_proof_01.json';d=read(cohort);assert d['status']=='WA3_SOURCE_COHORT_READY'
assert {r['depot'].replace('/','\\'):r['sha256']for r in d['resources']}=={k:r['sha256']for k,r in resources.items()}
actual={str(p.relative_to(C/'source')).replace('/','\\'):sha(p) for p in (C/'source').rglob('*') if p.is_file()}
assert actual=={k:r['sha256']for k,r in resources.items()}
for p in [cohort,H/'manifest_02.json',C/'owner_proof_02.json',H/'combat_review/payload_assessment_02.json',H/'combat_review/filters_core_spec_01.json',H/'combat_review/filters_additional_spec_01.json',H/'native_review/npc_fight_assessment_01.json',H/'computer_independent_01.json',H/'dependencyqueries_02.json']:
    pin(p)
result={'status':'PASS_INDEPENDENT_WA3_COHORT','resources':list(resources.values()),'resource_count':len(resources),'component_reviews':components,'pins':list(pins.values()),'runtime_verified':False,'game_writes':0,'save_writes':0}
out=C/'independent_semantic_01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n',newline='\n')
print({'status':result['status'],'resources':len(resources),'pins':len(pins)})
