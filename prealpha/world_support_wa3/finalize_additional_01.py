"""Freeze the closed CE extension after payload review and private filtering."""
from pathlib import Path
import json,hashlib,shutil,argparse
H=Path(__file__).resolve().parent;C=H/'candidate_01'
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
ap=argparse.ArgumentParser();ap.add_argument('--private-proof',required=True);ap.add_argument('--private-source',required=True);args=ap.parse_args()
paths=[H/'combat_review/identity_cohort_01.json',H/'combat_review/payload_assessment_02.json',Path(args.private_proof),H/'combat_review/alias1246_01.json',H/'combat_review/registry_03/report_01.json']
identity=R(paths[0]);review=R(paths[1]);private=R(paths[2]);assert review['status'].startswith('PASS') and private['status'].startswith('PASS')
assert all(c['pass']for c in review['checks']);assert all(c['pass']for c in private['checks'])
assert set(review['approved_ids'])=={g['id']for g in identity['groups']}
filtered={g['group']:g for g in private['groups']};assert set(filtered)==set(review['private_filter_ids'])
reviewed={g['id']:g for g in review['rows']};groups=identity['groups']
for g in groups:
 g['native_admission_facts']=reviewed[g['id']]['native_admission_facts'];g['owner_prefab']=g['prefab']
 if g['id']in filtered:
  f=filtered[g['id']];assert f['native_sha256']==g['support_sector_sha256'];g['owner_prefab']=f['prefab_ref']
 for key,digest in [('native_binary','native_binary_sha256'),('support_sector_raw','support_sector_sha256'),('support_sector_json','support_sector_json_sha256')]:assert sha(g[key])==g[digest];paths.append(Path(g[key]))
 for c in g['communities']:assert sha(c['registry'])==c['registry_sha256'];paths.append(Path(c['registry']))
pins=[{'path':str(p.resolve()),'sha256':sha(p)}for p in dict.fromkeys(paths)]
for p in review['pins']:assert sha(p['path'])==p['sha256'];pins.append(p)
manifest={'status':'WA3_REVIEWED_NATIVE_SUPPORT_COHORT','owner_count':len(groups),'spawner_count':sum(len(g['spawner_hashes'])for g in groups),'groups':groups,'dispositions':identity['dispositions'],'pins':pins,'game_writes':0,'save_writes':0}
out=H/'manifest_additional_01.json';assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
for r in private['resources']:
 source=Path(args.private_source)/r['depot'];dest=C/'source'/r['depot'];assert sha(source)==r['sha256'] and not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
print(json.dumps({'owners':len(groups),'spawners':manifest['spawner_count']}))
