"""Pin baseline/catalogues/cache candidates. Reads existing inputs, writes fresh audit outputs."""
from common import *
import collections,zipfile,datetime
def prepare(w,o,candidate):
 assert not (o/'prepared.json').exists(),'Use fresh output'
 c=w/candidate;m=read(c/'install_manifest_01.json');g=Path(m['game_root']);errors=[]
 protected=[g/r['path'] for r in m['package_files']]+[c/'package'/r['path'] for r in m['package_files']]
 for r in m['package_files']:
  for p in [g/r['path'],c/'package'/r['path']]:
   if not p.exists() or sha(p)!=r['after']:errors.append({'kind':'BASELINE_HASH_MISMATCH','path':str(p),'expected':r['after']})
 for top in ['archive_source']:
  protected.extend(p for p in (c/top).rglob('*') if p.is_file())
 for top in ['release','dist']:
  protected.extend(p for p in (w/top).rglob('*') if p.is_file() and not p.is_symlink())
 s=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077');protected.extend(p for p in s.rglob('*') if p.is_file())
 protected.append(g/'r6/scripts/virtual-atelier-full/SetupNewTab.reds')
 write(o/'protection_before.json',{'files':snapshot(protected),'game_metadata':tree_metadata(g),'save_root':str(s),'save_metadata':tree_metadata(s)})
 pointer_path=w/'research/gig_restoration/lore_whitelist_current.json';pointer=read(pointer_path);sel=w/pointer['selection_file'];active=read(sel)
 if sha(sel)!=pointer['sha256']:errors.append({'kind':'CATALOGUE_POINTER_HASH'})
 versions=[]
 for p in sorted((w/'research/gig_restoration').glob('lore_whitelist*.json')):
  try:
   q=read(p)
   if 'decision_registry'in q:versions.append({'path':str(p),'sha256':sha(p),'rows':q['decision_registry'],'selected_variant':q.get('selected_variant')})
  except (ValueError,OSError) as e:errors.append({'kind':'CATALOGUE_PARSE','path':str(p),'error':str(e)})
 rows=[];registry=active['decision_registry'];selected_variant=active['selected_variant'];names={str(x) for vs in active[selected_variant].values() for x in vs};seen=set()
 for r in registry:
  q=dict(r);q['selection_source']=str(sel);q['catalogue_sha256']=sha(sel);q['held']=bool(re.search(r'\b(?:hold|held)\b',r.get('reason','')+' '+r.get('requirements',''),re.I)) and r['decision']!='INCLUDE';q['eligibility_conditional']=bool(r.get('requirements'));q['historical_decisions']=[{'source':v['path'],'sha256':v['sha256'],'decision':s['decision']} for v in versions for s in v['rows'] if s['id']==r['id']]
  if r['id'] in seen:errors.append({'kind':'DUPLICATE_QUEST_ID','id':r['id']})
  seen.add(r['id']);q['selected_name_agrees']=(r.get('title') in names)==(r['decision']=='INCLUDE');rows.append(q)
 write(o/'catalogues.json',{'pointer':pointer,'pointer_sha256':sha(pointer_path),'active_source':str(sel),'sources':[{'path':v['path'],'sha256':v['sha256']} for v in versions],'quests':rows,'derived_counts':dict(collections.Counter(r['decision'] for r in rows)),'held_ids':[r['id'] for r in rows if r['held']],'policy_overrides':pointer.get('current_policy_overrides',{})})
 # Reuse exports only after payload and JSON hashes are verified by capture.
 cache_path=w/'diagnostics/phone_restoration_preparation_20261029_01/queries_01.json';caches=list(read(cache_path)['cache']) if cache_path.exists() else []
 invpaths=[w/'research/sidejobs_s29'/d/'inventory.json' for d in ['native_01','native_03','native_05','discovery_01','discovery_02']]
 for p in invpaths:
  if p.exists():caches.extend(read(p).get('rows',[]))
 metadata=[];mappings=[];quest_seeds=collections.defaultdict(set)
 for p in sorted(list((w/'research/gig_restoration').glob('*/manifest.json'))+list((w/'prealpha').glob('*/prepared_*/manifest.json'))+list((w/'prealpha').glob('*/prepared_*/prepared.json'))):
  try:q=read(p)
  except (ValueError,OSError):continue
  metadata.append({'path':str(p),'sha256':sha(p)})
  for a,b in q.get('mapping',{}).items():
   if isinstance(a,str) and isinstance(b,str) and a.startswith(('base\\','ep1\\')) and b.startswith('towercontinued\\'):mappings.append({'native':a,'private':b,'evidence':str(p)})
  for r in q.get('resources',[]):
   if isinstance(r,dict) and all(k in r for k in ['native','private']):mappings.append({'native':r['native'],'private':r['private'],'evidence':str(p)})
  for r in q.get('recipes',[])+q.get('jobs',[]):
   if isinstance(r,dict) and r.get('id') in seen and r.get('native'):quest_seeds[r['id']].add(r['native'])
  for k,v in q.get('quests',{}).items():
   if k in seen and isinstance(v,str):quest_seeds[k].add(v)
 # Encoded namespace is independently discoverable, without trusting manifests alone.
 source=c/'archive_source';private=[]
 for p in sorted(source.rglob('*')):
  if not p.is_file():continue
  d=str(p.relative_to(source)).replace('/','\\');h=sha(p);private.append({'depot':d,'key':fnv(d),'raw':str(p),'sha256':h})
  match=re.search(r'\\native\\((?:base|ep1)\\.+)',d)
  if match:mappings.append({'native':match[1],'private':d,'evidence':'encoded native depot in private namespace; identity candidate, not approved semantics'})
  for r in rows:
   if r['id'].lower() in d.lower():quest_seeds[r['id']].add(d)
 cache=[]
 for r in caches:
  if all(k in r for k in ['depot','raw','json','sha256','json_sha256']):cache.append({**r,'raw':str(path(w,r['raw'])),'json':str(path(w,r['json']))})
 wanted={r['depot'] for r in cache if r['depot'].endswith(('.questphase','.scene'))}
 wanted.update(x['native'] for x in mappings)
 wanted.update(d for ds in quest_seeds.values() for d in ds)
 for r in rows:
  for d in r.get('native_resources',[]):
   if isinstance(d,str) and d.startswith(('base\\','ep1\\')):wanted.add(d)
 for d in ['base\\quest\\holocalls\\holocall_initializers.questphase','ep1\\quest\\holocalls\\holocall_initializers_ep1.questphase','base\\quest\\holocalls\\holocall_cleanup.questphase','ep1\\quest\\holocalls\\holocall_cleanup_ep1.questphase']:wanted.add(d)
 write(o/'queries.json',{'wanted':sorted(wanted),'cache':cache,'private':private,'mapping_candidates':mappings,'quest_seeds':{k:sorted(v) for k,v in quest_seeds.items()},'metadata_sources':metadata})
 zproof=[]
 for zp in c.glob('*.zip'):
  with zipfile.ZipFile(zp) as z:
   bad=z.testzip();present=set(z.namelist());expected={r['path'] for r in m['package_files']};mismatch=[r['path'] for r in m['package_files'] if r['path'] not in present or hashlib.sha256(z.read(r['path'])).hexdigest().upper()!=r['after']]
   zproof.append({'path':str(zp),'sha256':sha(zp),'crc_failure':bad,'unexpected':sorted(present-expected),'missing':sorted(expected-present),'hash_mismatches':mismatch})
 write(o/'prepared.json',{'schema':SCHEMA,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate':str(c),'game':str(g),'manifest':str(c/'install_manifest_01.json'),'manifest_sha256':sha(c/'install_manifest_01.json'),'private_resources':len(private),'catalogue_records':len(rows),'errors':errors,'zip_proofs':zproof})
 print(json.dumps({'stage':'prepared','private':len(private),'quests':len(rows),'wanted':len(wanted),'caches':len(cache),'errors':len(errors)}))
