"""Bind the complete additional CE census to current native identities and spots."""
from pathlib import Path
import json,hashlib,collections
H=Path(__file__).resolve().parent; C=H/'combat_review'
R=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
core=R(H/'manifest_core_01.json');old=R(H/'identity_cohort_01.json')['existing_owners']
known=old+core['groups'];seen={g['prefab']:g['id'] for g in known};seenhash={h:g['id']for g in known for h in g['spawner_hashes']}
bindings={r['id']:(r['ref'],r['resource'])for r in R(C/'prefab_hashes_01.json')}
for r in R(C/'descriptor_aliases_01.json')['rows']:
 assert len(r['matches'])==1
 b=r['matches'][0];bindings[r['id']]=(b['prefab'],b['resource'])
sectors={};reg={};ident={}
for seq in ['01','02']:
 for s in R(C/f'decoded_{seq}/report_01.json')['rows']:
  if s['parsed']:sectors[s['resource']]=s
 rr=R(C/f'registry_{seq}/report_01.json')
 for row in rr['rows']:
  for f in row['found']:
   if f['hash']not in reg or row['archive'].startswith('ep1'):reg[f['hash']]=f
 for r in rr['identities']:ident[(r['id'],r['prefab'])]=r['candidates']
rr=R(C/'registry_03/report_01.json')
for row in rr['rows']:
 for f in row['found']:
  if f['hash']not in reg or row['archive'].startswith('ep1'):reg[f['hash']]=f
for r in rr['identities']:
 key=(r['id'],r['prefab']);ident[key]=ident.get(key,[])+r['candidates']
groups=[];dispositions=[];checks=[]
for source in R(C/'closure_01.json')['candidates']:
 i=source['id'];prefab,resource=bindings[i]
 registry_prefab=prefab
 if i==1246:
  alias=R(C/'alias1246_01.json');assert alias['status']=='PASS_EXACT_ENGINE_HASH_ALIAS' and alias['authored']==prefab and alias['resource']==resource
  prefab=alias['canonical']
 if prefab in seen:dispositions.append({'id':i,'status':'EXISTING_OWNER_COVERAGE','owner_id':seen[prefab]});continue
 s=sectors.get(resource)
 if not s:dispositions.append({'id':i,'status':'NO_CURRENT_NATIVE_SECTOR','prefab':prefab,'resource':resource});continue
 cs=[dict(c,registry=reg[c['hash']])for c in ident.get((i,registry_prefab),[])if c['hash']in reg and c['ref'].startswith(prefab+'/')]
 if not cs:dispositions.append({'id':i,'status':'NO_EXACT_CURRENT_COMMUNITY_WITHIN_PREFAB','prefab':prefab});continue
 assert not any(c['hash']in seenhash for c in cs),(i,cs)
 sector=R(s['json']);defs={n['index']:n['definition']for n in sector['nodes']};spots={p['quest_ref']:defs[p['node']]for p in sector['placements']if p['type']=='worldAISpotNode'}
 marks={m['$value']for n in spots.values()for m in n.get('markings',[])};communities=[];exclusions=[]
 for c in cs:
  path=c['registry']['json'];d=R(path);assert d['communityId']['entityId']['hash']==c['hash'];entries=[]
  for ee in d['template']['Data']['entries']:
   e=ee['Data'];em=set();explicit=[]
   for ph in e['phases']:
    for tp in ph['Data']['timePeriods']:
     em.update(m['$value']for m in tp['markings']);explicit.extend(n['$value']for n in tp['spotNodeRefs'])
   bound=[{'native_ref':r,'matches':[p for p in spots if p==r or p.endswith('/'+r.replace('~/../',''))]}for r in sorted(set(explicit)-{'0',''})]
   supported=bool(em&marks or any(len(b['matches'])==1 for b in bound))
   entries.append({'entry':e['entryName']['$value'],'markings':sorted(em),'unmapped_markings':sorted(em-marks),'explicit_spots':bound,'has_authored_local_support':supported})
   if not supported:exclusions.append({'spawner_hash':c['hash'],'entry':e['entryName']['$value'],'reason':'No authored support in selected native prefab'})
  communities.append({'hash':c['hash'],'ref':c['ref'],'registry':path,'registry_sha256':sha(path),'entries':entries})
 if all(not e['has_authored_local_support']for c in communities for e in c['entries']):
  dispositions.append({'id':i,'status':'NO_ADMISSIBLE_NATIVE_ENTRY','prefab':prefab,'communities':communities});continue
 g={k:source[k]for k in ['id','native_resource','native_binary','native_binary_sha256','source','node_path']}
 g.update(prefix=f'PTFRWA3_{i}_',prefab=prefab,native_prefab=source['authored_prefab'],identity_repaired=prefab!=source['authored_prefab'],community_refs=[c['ref']for c in cs],spawner_hashes=[c['hash']for c in cs],registry=[c['registry']for c in cs],communities=communities,entry_exclusions=exclusions,native_admission_facts=[],support_sector_resource=resource,support_sector_raw=s['winner']['raw'],support_sector_sha256=s['winner']['sha256'],support_sector_json=s['json'],support_sector_json_sha256=s['json_sha256'],spot_count=len(spots))
 assert sha(g['native_binary'])==g['native_binary_sha256'];assert sha(g['support_sector_raw'])==g['support_sector_sha256'];assert sha(g['support_sector_json'])==g['support_sector_json_sha256']
 groups.append(g);seen[prefab]=i
 for h in g['spawner_hashes']:seenhash[h]=i
for d in dispositions:
 if d.get('prefab')in seen:
  d['original_reason']=d['status'];d['status']='EXISTING_OWNER_COVERAGE';d['owner_id']=seen[d['prefab']]
report={'status':'WA3_ADDITIONAL_IDENTITIES_PENDING_PAYLOAD_REVIEW','groups':groups,'dispositions':dispositions,'source_rows':101,'owner_count':len(groups),'spawner_count':sum(len(g['spawner_hashes'])for g in groups),'game_writes':0,'save_writes':0}
out=C/'identity_cohort_01.json';out.write_text(json.dumps(report,indent=2)+'\n',newline='\n')
print(json.dumps({'owners':len(groups),'spawners':report['spawner_count'],'dispositions':[(d['id'],d['status'])for d in dispositions],'entry_exclusions':[(g['id'],[(e['entry'])for e in g['entry_exclusions']])for g in groups if g['entry_exclusions']]}))
