"""Freeze reviewed EP1 support with independently verified filtered sectors."""
from pathlib import Path
import json,hashlib,shutil
H=Path(__file__).resolve().parent;C=H/'candidate_01'
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
paths=[H/'native_review/ep1_cohort_01.json',H/'native_review/ep1_support_assessment_01.json',H/'native_review/ep1_ambient_scene_assessment_01.json',H/'private_sectors/verification_ep1_01.json']
groups=R(paths[0]);private=R(paths[-1]);filtered={g['group']:g for g in private['groups']}
for p in paths[1:]:assert R(p)['status'].startswith('PASS'),p
core=R(H/'manifest_core_01.json');old=R(H/'identity_cohort_01.json')['existing_owners'];known=core['groups']+old
assert not {h for g in groups for h in g['spawner_hashes']}&{h for g in known for h in g['spawner_hashes']}
assert not {g['native_binary_sha256']for g in groups}&{g['native_binary_sha256']for g in core['groups']}
for g in groups:
 f=filtered[g['id']];assert f['native_sha256']==g['support_sector_sha256']
 g['owner_prefab']=f['prefab_ref'];g['identity_repaired']=False;g['entry_exclusions']=[{'spawner_hash':c['hash'],'entry':e['entry'],'reason':'No authored support in selected native prefab'}for c in g['communities']for e in c['entries']if not e['eligible']]
 for key,digest in [('native_binary','native_binary_sha256'),('support_sector_raw','support_sector_sha256')]:assert sha(g[key])==g[digest];paths.append(Path(g[key]))
 g['support_sector_json_sha256']=sha(g['support_sector_json']);paths.append(Path(g['support_sector_json']))
 for c in g['communities']:assert sha(c['registry'])==c['registry_sha256'];paths.append(Path(c['registry']))
manifest={'status':'WA3_REVIEWED_NATIVE_SUPPORT_COHORT','owner_count':len(groups),'spawner_count':sum(len(g['spawner_hashes'])for g in groups),'groups':groups,'pins':[{'path':str(p.resolve()),'sha256':sha(p)}for p in dict.fromkeys(paths)],'game_writes':0,'save_writes':0}
out=H/'manifest_ep1_01.json';assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
for r in private['resources']:
 source=H/'private_sectors/source_ep1_01'/r['depot'];dest=C/'source'/r['depot'];assert sha(source)==r['sha256'] and not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
print(json.dumps({'owners':len(groups),'spawners':manifest['spawner_count'],'entry_exclusions':[(g['id'],g['entry_exclusions'])for g in groups if g['entry_exclusions']]}))
