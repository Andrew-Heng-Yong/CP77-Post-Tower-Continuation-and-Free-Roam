"""Stage only verified passive support owners; withhold progress-gated families."""
from pathlib import Path
import json, hashlib, shutil
H=Path(__file__).resolve().parent;C=H/'candidate_02';S=C/'source'
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
verification=read(H/'private_sectors/verification_comprehensive_01.json')
assert verification['status']=='PASS_COMPREHENSIVE_PRIVATE_SUPPORT' and verification['group_count']==315
raw=read(H/'private_sectors/build_comprehensive_proof_09.json')
assert verification['source_proof_sha256']==sha(H/'private_sectors/build_comprehensive_proof_09.json')
private={r['group']:r for r in raw['groups']};assert len(private)==315
core=read(H/'manifest_core_01.json')['groups'];ep1=read(H/'manifest_ep1_01.json')['groups']
extra=read(H/'combat_review/identity_cohort_01.json')['groups']
life=read(H/'combat_review/lifecycle_inventory_01.json')['rows']
withheld=[r['id'] for r in life if r['owner_fact_conditions'] or any(a['preceding_fact_conditions'] for a in r['ancestors'])]
assert len(withheld)==24,len(withheld)
selected=[]
for g in core:
    if g['id']==1013:continue
    if g['id'] in private:g['owner_prefab']=private[g['id']]['prefab_ref']
    else:assert g['id']==1005 and g['owner_prefab']==g['prefab']
    selected.append(g)
selected+=ep1
for g in extra:
    if g['id'] in withheld:continue
    assert g['id'] in private
    g['owner_prefab']=private[g['id']]['prefab_ref'];g['native_admission_facts']=[];selected.append(g)
assert len(selected)==222+4+94-24,len(selected)
assert len({g['id'] for g in selected})==len(selected)
hashes=[h for g in selected for h in g['spawner_hashes']]
assert len(set(hashes))==len(hashes)
for g in selected:
    for key,digest in [('native_binary','native_binary_sha256'),('support_sector_raw','support_sector_sha256')]:
        assert sha(g[key])==g[digest]
manifest={'status':'WA3_REVIEWED_NATIVE_SUPPORT_COHORT','owner_count':len(selected),'spawner_count':len(hashes),'preserved_owner_count':238,'groups':selected,
          'dispositions':[{'id':1013,'reason':'WolvenKit cannot read dynamic worldNode sector for required trigger filter'}]+[{'id':i,'reason':'Native progress or lifetime fact gate requires exact review'} for i in withheld],
          'private_sector_proof':str(H/'private_sectors/verification_comprehensive_01.json'),'private_sector_proof_sha256':sha(H/'private_sectors/verification_comprehensive_01.json'),'game_writes':0,'save_writes':0}
p=H/'manifest_02.json';assert not p.exists();p.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
S.mkdir(parents=True,exist_ok=True)
for r in raw['resources']:
    src=H/'private_sectors/source_comprehensive_09'/r['depot'];dst=S/r['depot']
    assert sha(src)==r['sha256'] and not dst.exists()
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
for r in read(H/'private_sectors/verification_ep1_01.json')['resources']:
    src=H/'private_sectors/source_ep1_01'/r['depot'];dst=S/r['depot']
    assert sha(src)==r['sha256'] and not dst.exists()
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
print({'owners':len(selected),'spawners':len(hashes),'private_resources':len(raw['resources']),'withheld_fact_gates':len(withheld)})
