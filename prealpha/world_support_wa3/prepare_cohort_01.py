"""Join exact native owner, current sector and current community identities."""
import collections,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
census={r['id']:r for r in read(H/'census_01.json')['rows']}
old=read(W/'prealpha/world_workspots_w2/manifest_03.json')['groups']
extra=read(W/'prealpha/world_actions_wa2/candidate_01/script_source/support_build_01.json')['new_group']
old.append(dict(extra,prefab=extra['community_ref'].rsplit('/',1)[0],community_refs=[extra['community_ref']],spawner_hashes=[extra['spawner_hash']]))
oldrefs={g['prefab']:g['id'] for g in old};oldhash={v:g['id'] for g in old for v in g['spawner_hashes']}
registry={};regids={};sectors={};identities=collections.defaultdict(list)
for name in ['registry_03','additional_registry_01','registry_04','registry_05']:
 d=read(H/name/'report_01.json')
 for r in d['rows']:
  for f in r['found']:
   if f['hash'] not in registry or r['archive'].startswith('ep1'):registry[f['hash']]=f
 for i in d['identities']:regids[(i['id'],i['prefab'])]=i['candidates']
for name in ['decoded_01','additional_decoded_01','additional_decoded_03','additional_decoded_04']:
 for r in read(H/name/'report_01.json')['rows']:
  if r['parsed']:sectors[r['resource']]=r
for name in ['extracted_01','additional_extracted_01','additional_extracted_03','additional_extracted_04']:
 for i in read(H/name/'report_01.json')['identities']:
  if i not in identities[i['id']]:identities[i['id']].append(i)
groups=[];dispositions=[]
for ident,r in census.items():
 if r['already_supported']:continue
 choices=[];reasons=[]
 for i in identities[ident]:
  prefab=i['ref'];s=sectors.get(i['resource'])
  if not s:reasons.append('NO_CURRENT_NATIVE_SECTOR '+prefab);continue
  candidates=regids.get((ident,prefab),i['communities'])
  cs=[dict(c,registry=registry[c['hash']]) for c in candidates if c['hash'] in registry and c['ref'].startswith(prefab+'/')]
  if not cs:reasons.append('NO_EXACT_CURRENT_COMMUNITY_WITHIN_PREFAB '+prefab);continue
  covered={oldhash[c['hash']] for c in cs if c['hash'] in oldhash}
  if prefab in oldrefs or covered:
   reasons.append('EXISTING_OWNER '+','.join(map(str,sorted(covered|({oldrefs[prefab]} if prefab in oldrefs else set())))));continue
  choices.append((prefab,s,cs))
 # Multiple alternatives from one parent cannot become independent owners without a unique identity proof.
 unique={p:(p,s,c) for p,s,c in choices}
 if len(unique)!=1:
  dispositions.append({'id':ident,'status':'WITHHELD' if not any(x.startswith('EXISTING_OWNER')for x in reasons) else 'EXISTING_OWNER_COVERAGE','reasons':reasons+(['MULTIPLE_CURRENT_PREFAB_ALTERNATIVES'] if len(unique)>1 else [])});continue
 prefab,s,cs=next(iter(unique.values()))
 g={'id':ident,'prefix':f'PTFRWA3_{ident}_','prefab':prefab,'native_prefab':r['resolved_prefab'],
    'community_refs':[c['ref'] for c in cs],'spawner_hashes':[c['hash'] for c in cs],
    'registry':[c['registry'] for c in cs], 'source':r['source'],'node_path':r['node_path'],
    'native_binary':r['native_binary'],'native_binary_sha256':r['native_binary_sha256'],
    'support_sector_resource':s['resource'],'support_sector_raw':s['winner']['raw'],'support_sector_sha256':s['winner']['sha256'],
    'support_sector_json':s['json'],'support_sector_json_sha256':s['json_sha256'],
    'identity_repaired':prefab!=r['resolved_prefab']}
 groups.append(g)
for g in read(H/'native_review/outside_cohort_01.json'):groups.append(g)
groups.append(read(H/'native_review/outside1004_cohort_spec_01.json'))
groups.append(read(H/'native_review/outside1000_cohort_spec_01.json'))
# Deduplicate same support prefab and community across source aliases, preserving the first exact owner.
seen={};clean=[]
for g in sorted(groups,key=lambda g:g['id']):
 if g['prefab'] in seen:
  dispositions.append({'id':g['id'],'status':'COALESCED_NEW_OWNER','owner_id':seen[g['prefab']]});continue
 seen[g['prefab']]=g['id'];clean.append(g)
report={'status':'WA3_IDENTITY_COHORT_PENDING_PAYLOAD_PROOF','groups':clean,'dispositions':dispositions,'existing_owners':old,'game_writes':0,'save_writes':0}
(H/'identity_cohort_01.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'groups':len(clean),'new_CE':sum(g['id']<1000 for g in clean),'outside':sum(g['id']>=1000 for g in clean),'dispositions':collections.Counter(d['status']for d in dispositions)}))
