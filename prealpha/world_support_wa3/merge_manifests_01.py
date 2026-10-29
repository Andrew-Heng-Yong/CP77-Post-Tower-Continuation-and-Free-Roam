"""Union independently reviewed support cohorts without modifying their evidence."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;C=H/'candidate_01'
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
names=['core','ep1','additional'];manifests=[];owners=[];pins=[]
for name in names:
 p=H/f'manifest_{name}_01.json';m=R(p);assert m['status']=='WA3_REVIEWED_NATIVE_SUPPORT_COHORT';manifests.append(m)
 proof_path=C/f'owner_{name}_proof_01.json';proof=R(proof_path);assert proof['status']=='PASS_WA3_PREFAB_OWNERS_BINARY_READBACK' and proof['manifest_sha256']==sha(p)
 owners.extend(proof['proofs']);pins.extend(m['pins']);pins.extend([{'path':str(p),'sha256':sha(p)},{'path':str(proof_path),'sha256':sha(proof_path)}])
groups=sorted([g for m in manifests for g in m['groups']],key=lambda g:g['id']);hashes=[h for g in groups for h in g['spawner_hashes']]
assert len({g['id']for g in groups})==len(groups);assert len(hashes)==len(set(hashes));assert len({g['prefab']for g in groups})==len(groups)
old=R(H/'identity_cohort_01.json')['existing_owners'];oldhash={h for g in old for h in g['spawner_hashes']};assert not oldhash&set(hashes)
assert not {g['id']for g in old}&{g['id']for g in groups}
assert len({p['resource']for p in owners})==len(owners)
for p in owners:assert sha(C/'source'/p['resource'])==p['sha256'] and sha(p['json'])==p['json_sha256']
pinmap={}
for p in pins:
 assert sha(p['path'])==p['sha256'],p['path']
 if p['path']in pinmap:assert pinmap[p['path']]==p['sha256']
 pinmap[p['path']]=p['sha256']
manifest={'status':'WA3_REVIEWED_NATIVE_SUPPORT_COHORT','owner_count':len(groups),'spawner_count':len(hashes),'preserved_owner_count':238,'preserved_spawner_count':len(oldhash),'groups':groups,'dispositions':[d for m in manifests for d in m.get('dispositions',[])],'pins':[{'path':p,'sha256':h}for p,h in pinmap.items()],'game_writes':0,'save_writes':0}
p=H/'manifest_01.json';assert not p.exists();p.write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
proof={'status':'PASS_WA3_PREFAB_OWNERS_BINARY_READBACK','manifest_sha256':sha(p),'owners':len(groups),'resources':len(owners),'proofs':owners,'game_writes':0,'save_writes':0};out=C/'owner_proof_01.json';assert not out.exists();out.write_text(json.dumps(proof,indent=2)+'\n',newline='\n')
print(json.dumps({'owners':len(groups),'spawners':len(hashes),'resources':len(owners)}))
