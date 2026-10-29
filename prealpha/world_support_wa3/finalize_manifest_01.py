"""Freeze reviewed identities and selected filtered payloads for binary building."""
import json,hashlib,shutil,argparse
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_01'
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
parser=argparse.ArgumentParser();parser.add_argument('--output',default='manifest_01.json');args=parser.parse_args()
d=R(H/'identity_cohort_01.json');p=R(H/'payload_review_01.json');assert p['status']=='PASS_NATIVE_SUPPORT_PAYLOAD_REVIEW' and all(c['pass']for c in p['checks'])
private_path=H/'private_sectors/verification_06.json';private=R(private_path);assert private['status'].startswith('PASS')
filtered={g['group']:g for g in private['groups']};payload={r['id']:r for r in p['rows']}
for g in d['groups']:
 g['native_admission_facts']=g.get('native_admission_facts',[])
 g['identity_repaired']=g.get('identity_repaired',False)
 g['owner_prefab']=filtered[g['id']]['prefab_ref'] if g['id']in filtered else g['prefab']
 g['entry_exclusions']=[{'spawner_hash':c['hash'],'entry':e['entry'],'reason':'No authored support in selected prefab'}for c in payload[g['id']]['communities']for e in c['entries']if not e['has_authored_local_support']]
 # Two unsupported vehicle entries cannot be admitted by the NPCPuppet observer;
 # the one unsupported robot is explicitly rejected by the new-owner guard.
 assert all((g['id']==258 and e['entry']in ['car1','pickup'])or(g['id']==475 and e['entry']=='robot')for e in g['entry_exclusions']),g['entry_exclusions']
 g['support_sector_json_sha256']=sha(g['support_sector_json'])
 g['payload_review']=str((H/'payload_review_01.json').resolve())
 assert sha(g['native_binary'])==g['native_binary_sha256']
 assert sha(g['support_sector_raw'])==g['support_sector_sha256']
 if g['id']in filtered:assert g['support_sector_sha256']==filtered[g['id']]['native_sha256']
assert len({g['id']for g in d['groups']})==len(d['groups'])
old_hash={h for g in d['existing_owners']for h in g['spawner_hashes']};new_hash=[h for g in d['groups']for h in g['spawner_hashes']]
assert len(new_hash)==len(set(new_hash)) and not old_hash&set(new_hash)
old_prefabs={g['prefab']for g in d['existing_owners']};assert not old_prefabs&{g['prefab']for g in d['groups']}
paths=[H/'identity_cohort_01.json',H/'payload_review_01.json',private_path,H/'native_review/conversation_assessment_01.json',H/'native_review/party_assessment_01.json',H/'native_review/corpse_assessment_01.json',H/'native_review/outside_support_assessment_01.json',H/'native_review/border_support_assessment_01.json',H/'native_review/outside1004_filter_spec_01.json']
for g in d['groups']:
 paths.extend([Path(g['native_binary']),Path(g['support_sector_raw']),Path(g['support_sector_json'])])
 for c in payload[g['id']]['communities']:paths.append(Path(c['registry']))
paths=list(dict.fromkeys(p.resolve()for p in paths));assert all(p.is_file()for p in paths)
manifest={'status':'WA3_REVIEWED_NATIVE_SUPPORT_COHORT','owner_count':len(d['groups']),'new_CE_owner_count':sum(g['id']<1000 for g in d['groups']),'outside_owner_count':sum(g['id']>=1000 for g in d['groups']),'spawner_count':len(new_hash),'preserved_owner_count':238,'preserved_spawner_count':len(old_hash),'groups':d['groups'],'dispositions':d['dispositions'],'private_sector_proof':str(private_path.resolve()),'private_sector_proof_sha256':sha(private_path),'pins':[{'path':str(p),'sha256':sha(p)}for p in paths],'game_writes':0,'save_writes':0}
out=H/args.output;assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n',newline='\n')
for r in private['resources']:
 source=H/'private_sectors/source_06'/r['depot'];dest=C/'source'/r['depot'];assert sha(source)==r['sha256'] and not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
print(json.dumps({k:manifest[k]for k in ['owner_count','new_CE_owner_count','outside_owner_count','spawner_count']}))
