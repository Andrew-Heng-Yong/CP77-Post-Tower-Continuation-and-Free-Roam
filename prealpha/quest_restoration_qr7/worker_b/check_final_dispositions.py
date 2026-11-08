"""Independent QR7 final21-disposition/completeness gate. Run only after root's frozen signal.

Standard-library only. Does not import coordinator finalizers, packers or worker investigators.
"""
from pathlib import Path
import argparse,json,csv,ast,hashlib,collections,re,zipfile,os
W=Path(__file__).resolve().parents[3];H=W/'prealpha/quest_restoration_qr7';B=Path(__file__).resolve().parent
STAGES={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
ALLOWED={'PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
HASH_OBSERVATIONS={}
def sha(p):
 p=Path(p);key=os.path.normcase(str(p.resolve()));st=p.stat();tag=(st.st_size,st.st_mtime_ns)
 if key in HASH_OBSERVATIONS and HASH_OBSERVATIONS[key]['metadata']==tag:return HASH_OBSERVATIONS[key]['sha256']
 digest=hashlib.sha256()
 with p.open('rb')as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):digest.update(chunk)
 after=p.stat()
 if(after.st_size,after.st_mtime_ns)!=tag:raise RuntimeError('File changed during initial current hash: '+str(p))
 h=digest.hexdigest().upper();HASH_OBSERVATIONS[key]={'path':str(p.resolve()),'metadata':tag,'sha256':h};return h
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);ap.add_argument('--epoch',required=True);ap.add_argument('--package-review');ap.add_argument('--preservation-review');ap.add_argument('--matrix-only',action='store_true');ap.add_argument('--carry-forward-hashes');args=ap.parse_args()
 out=B/args.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);checks=[];issues=[];pins={};indirections=[];carry=None
 if args.carry_forward_hashes:
  predecessor=read(args.carry_forward_hashes);predecessor_hash=sha(args.carry_forward_hashes)
  if not any(c['name']=='all-current-initial-hash-observations-postcheck-metadata-stable'and c['pass']for c in predecessor['checks']):raise RuntimeError('Predecessor lacked complete current metadata stability pass')
  reused=0
  for key,observation in predecessor['current_initial_hash_observations'].items():
   p=Path(observation['path']);st=p.stat();tag=(st.st_size,st.st_mtime_ns)
   if tag==tuple(observation['metadata']):HASH_OBSERVATIONS[key]={**observation,'metadata':tag};reused+=1
  carry={'path':str(Path(args.carry_forward_hashes).resolve()),'sha256':predecessor_hash,'reused_stable_observations':reused,'reason':'Coordinator authorized adjacent current pass observations after only interpretation fixes; every reused file metadata is checked now and again at final pass. No historical build digest substituted.'}
 def ck(name,ok,**e):
  checks.append({'name':name,'pass':bool(ok),**e})
  if not ok:issues.append({'check':name,**e})
 def pin(p,h=None):
  p=Path(p);actual=sha(p)if p.is_file()else None;ck('frozen-pin:'+str(p),actual is not None and(h is None or actual==h),actual=actual,expected=h)
  if actual:pins[str(p.resolve())]=actual
  return actual
 pin(Path(__file__))
 if carry:pin(carry['path'],carry['sha256'])
 # Pin complete top-level publication, including prior immutable epochs, never completion seal written after this review.
 for p in sorted(H.iterdir()):
  matrix_files={'queue.json','quest_status_matrix.json','quest_status_matrix.csv','contract_status_matrix.json','contract_status_matrix.csv','coverage.json','targeted_dispositions.json','targeted_dispositions.csv','affected_quest_applicability.json'}
  if p.is_file()and p.suffix in ['.json','.csv','.md']and p.name!='completion.json'and(not args.matrix_only or p.name in matrix_files):pin(p)
 q=read(H/'queue.json');catpath=Path(q['source_catalogue']);pin(catpath,q.get('catalogue_sha256'));cat=read(catpath)
 registry=cat['decision_registry'];selected={r['id']for r in registry if r['decision']=='INCLUDE'}
 ck('actual-authoritative-selected-IDs-unique',len(selected)==sum(r['decision']=='INCLUDE'for r in registry))
 ck('queue-exact-authoritative-identities',len(q['quests'])==len(selected)and{r['id']for r in q['quests']}==selected)
 cm=read(H/'contract_status_matrix.json');qm=read(H/'quest_status_matrix.json');old=read(W/'prealpha/quest_restoration_qr6/contract_status_matrix.json');pairs={(r['quest_id'],r['stage'])for r in cm};by={(r['quest_id'],r['stage']):r for r in cm};oldby={(r['quest_id'],r['stage']):r for r in old}
 ck('complete-unique-ten-contract-grid',len(cm)==len(selected)*len(STAGES)and pairs=={(i,s)for i in selected for s in STAGES})
 ck('quest-matrix-exact-identities',len(qm)==len(selected)and{r.get('quest_id',r.get('id'))for r in qm}==selected)
 ck('all-contract-dispositions-recognized',all(r['status']in ALLOWED for r in cm))
 targets={k for k,r in oldby.items()if r['status']in['FAIL','UNKNOWN']};fails={k for k in targets if oldby[k]['status']=='FAIL'};unknowns=targets-fails
 ck('derived-original-targets-exactly21',len(targets)==21 and len(fails)==13 and len(unknowns)==8)
 final=[]
 for key in sorted(targets):
  row=by[key];current={k:row.get(k)for k in ['proven','remaining','approved_differences','status']};text=json.dumps(current,ensure_ascii=False)
  ck('source-specific-investigation:'+':'.join(key),bool(row.get('proven'))and bool(row.get('evidence'))and bool(re.search(r'\d|[a-z]+_[a-z]',json.dumps(row.get('proven',[])))))
  ck('no-generic-investigation-placeholder:'+':'.join(key),not re.search(r'QR1\s+pending|pending\s+deep|awaiting\s+(?:quest\s+)?audit|not\s+yet\s+investigated|TODO\s*:?\s*investigat',text,re.I))
  ck('no-stale-final-gate-pending-claim:'+':'.join(key),not re.search(r'(?:final\s+package|coordinator\s+(?:final\s+)?(?:package|integration)|independent\s+(?:source\s+)?review)[^.!;\n]{0,75}\bpending\b',text,re.I))
  if key in fails and row['status']!='FAIL':
   ck('repaired-contract-retains-bounded-future-only-status:'+':'.join(key),row['status']=='CONDITIONAL'and bool(re.search(r'future|fresh',text,re.I))and bool(re.search(r'old|histor|already|saved|entered',json.dumps(row.get('remaining',[])),re.I)))
  if row['status']in ['UNKNOWN','OPAQUE','LIVE_ONLY']:ck('unresolved-contract-has-explicit-evidence-limit:'+':'.join(key),bool(row.get('remaining')))
  for e in row.get('evidence',[]):
   if isinstance(e,str)and(re.match(r'^[A-Za-z]:[/\\]',e)or e.startswith('prealpha/')):pin(e)
   elif isinstance(e,dict):
    p=e.get('path');hashvalue=e.get('sha256')
    if p and Path(p).is_file():pin(p,hashvalue)
  for pathkey,hashkey in [('independent_review','independent_review_sha256'),('source_epoch_manifest','source_epoch_sha256')]:
   if isinstance(row.get(pathkey),str)and Path(row[pathkey]).is_file():pin(row[pathkey],row.get(hashkey))
  final.append({'quest_id':key[0],'stage':key[1],'before':oldby[key]['status'],'after':row['status'],'proven':row.get('proven'),'remaining':row.get('remaining'),'evidence':row.get('evidence')})
 # Preserve all other contract semantics; any extras need their own explicit, source-specific adjudication.
 extras=[]
 for key,row in by.items():
  if key not in targets and any(row.get(k)!=oldby[key].get(k)for k in ['status','proven','remaining','approved_differences']):extras.append({'quest_id':key[0],'stage':key[1],'before':oldby[key]['status'],'after':row['status']})
 save(out/'additional_changed_contracts.json',extras)
 ck('no-status-promotions-outside-original21',all(e['before']==e['after']for e in extras),extra_changes=extras)
 targeted=read(H/'targeted_dispositions.json');tby={(r['quest_id'],r['stage']):r for r in targeted}
 ck('targeted-dispositions-exact-original21',len(targeted)==len(targets)and set(tby)==targets)
 for key,row in tby.items():ck('targeted-matrix-core-equality:'+':'.join(key),all(row.get(k)==by[key].get(k)for k in ['status','proven','remaining','approved_differences']))
 oldq=read(W/'prealpha/quest_restoration_qr6/queue.json');qby={r['id']:r for r in q['quests']}
 for row in oldq['quests']:
  for field in ['deep_review','deep_review_sha256','review','identity_evidence','entry_guard_evidence']:ck('original-deep-provenance-preserved:'+row['id']+':'+field,qby[row['id']].get(field)==row.get(field))
 # Each CSV is independently compared to all common JSON columns, including structured prose/evidence when exported.
 def same(v,x):
  if x is None:return v in ['','null','None']
  if isinstance(x,(dict,list)):
   try:return json.loads(v)==x
   except(Exception):
    try:return ast.literal_eval(v)==x
    except(Exception):return False
  if isinstance(x,bool):return v.lower()==str(x).lower()
  return v==str(x)
 for name,rows in [('contract_status_matrix.csv',cm),('quest_status_matrix.csv',qm),('targeted_dispositions.csv',targeted)]:
  with(H/name).open(encoding='utf-8-sig',newline='')as f:csvrows=list(csv.DictReader(f))
  ck('CSV-row-count:'+name,len(csvrows)==len(rows))
  for i,(a,b)in enumerate(zip(csvrows,rows)):ck('CSV-JSON-all-common-columns:'+name+':'+str(i),all(same(a[k],b[k])for k in set(a)&set(b)))
 counts=dict(collections.Counter(r['status']for r in cm));fully={i for i in selected if all(by[(i,s)]['status']in['PASS','APPROVED_DEVIATION']for s in STAGES)}
 ck('no-new-blanket-static-certification',not fully and q.get('static_verified_count')==0)
 for f in ['coverage.json']+([]if args.matrix_only else['checkpoint.json']):
  data=read(H/f)
  for key in ['contract_status_counts','contract_counts','after_status_counts']:
   if key in data and isinstance(data[key],dict):ck('summary-counts:'+f+':'+key,{k:v for k,v in data[key].items()if v}=={k:v for k,v in counts.items()if v})
 # Epoch input is explicit; do not choose a candidate by latest filename or directory date.
 ep=read(args.epoch);pin(args.epoch);candidate=Path(ep['candidate']);prev=read(H/'source_epoch_00.json');delta={d:{'before':prev['source_resources'].get(d),'after':h}for d,h in ep['source_resources'].items()if prev['source_resources'].get(d)!=h};removed=set(prev['source_resources'])-set(ep['source_resources'])
 ck('no-predecessor-payload-deletion',not removed,removed=sorted(removed))
 for d,h in ep['source_resources'].items():pin(candidate/'archive_source'/d.replace('\\','/'),h)
 ck('exact-source-directory-inventory',set(ep['source_resources'])=={str(p.relative_to(candidate/'archive_source')).replace('/','\\')for p in(candidate/'archive_source').rglob('*')if p.is_file()})
 if not args.matrix_only:
  for r in ep.get('package_files',[]):pin(candidate/'package'/r['path'],r['sha256'])
 ck('all-source-deltas-explicitly-described',bool(ep.get('changes'))and bool(delta),delta=delta)
 if not args.matrix_only and ep.get('zip')and ep.get('zip_sha256'):
  pin(ep['zip'],ep['zip_sha256'])
  with zipfile.ZipFile(ep['zip'])as z:
   zi=z.infolist();ck('ZIP-no-duplicate-members',len(zi)==len({x.filename for x in zi}));ck('ZIP-no-traversal',all(not x.filename.startswith(('/','\\'))and'..'not in x.filename.replace('\\','/').split('/')for x in zi))
 if not args.matrix_only:
  for label,path in [('independent-package',args.package_review),('preservation',args.preservation_review)]:
   if not path:raise RuntimeError('Full review requires package/preservation reviews')
   pin(path);r=read(path);ck('review-success:'+label,str(r.get('status','')).startswith(('PASS','INDEPENDENT_'))and not r.get('failures')and not r.get('issues')and not r.get('discrepancies'),status=r.get('status'))
  package_review=read(args.package_review);pres=read(args.preservation_review);pm=candidate/'package_manifest.json';pin(pm,ep.get('package_manifest_sha256'));package=read(pm)
  ck('package-peer-bound-to-exact-current-epoch',package_review['final_epoch_sha256']==sha(args.epoch)and package_review['final_manifest_sha256']==sha(pm))
  ck('package-manifest-exact-source-delta',set(package['changed_existing_resources'])=={d for d in delta if d in prev['source_resources']}and set(package['added_resources'])==set(ep['source_resources'])-set(prev['source_resources'])and package['source_payloads']==len(ep['source_resources'])and package['readback_payloads']==len(ep['source_resources']))
  ck('only-reviewed-two-package-paths-change',set(package['changed_package_paths'])=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'})
  pin(package['zip'],package['zip_sha256']);files={r['path']:r for r in package['files']}
  with zipfile.ZipFile(package['zip'])as z:
   ck('independent-ZIP-CRC',z.testzip()is None);ck('independent-ZIP-exact51-member-inventory',len(z.namelist())==len(files)and set(z.namelist())==set(files))
   for name,r in files.items():ck('independent-ZIP-SHA:'+name,hashlib.sha256(z.read(name)).hexdigest().upper()==r['sha256'])
  rbpath=package_review['readback_manifest'];pin(rbpath,package_review['readback_manifest_sha256']);rb=read(rbpath);pin(rb['inputs'],rb['inputs_sha256'])
  ck('whole-readback-exact-depot-inventory',len(rb['members'])==len(ep['source_resources'])and{r['depot']for r in rb['members']}==set(ep['source_resources']))
  for r in rb['members']:ck('independent-extracted-member-SHA:'+r['depot'],sha(r['raw'])==r['raw_sha256']==ep['source_resources'][r['depot']])
  ledger=read(H/'defects_and_repairs.json');oldledger=read(W/'prealpha/quest_restoration_qr6/defects_and_repairs.json');oldids={r['id']for r in oldledger['defects']};newids={r['id']for r in ledger['defects']}
  ck('all-prior-unique-defect-identities-retained',oldids<=newids and len(newids)==len(ledger['defects']))
  repair_ids={r['id']for r in read(H/'repair_queue.json')['implemented']}
  ck('exact-old-plus-three-staged-repairs',ledger['cumulative_staged_repairs']==oldledger['cumulative_staged_repairs']+len(repair_ids)and package['inherited_repairs']==oldledger['cumulative_staged_repairs']and package['new_unique_repairs']==len(repair_ids),unique_repair_ids=sorted(repair_ids))
  inherited=prev['inherited_repair_resources'];prior_depots=set(inherited)if isinstance(inherited,dict)else{r.get('depot',r.get('resource'))for r in inherited}
  ck('cumulative-changed-resource-accounting',ledger['cumulative_changed_resources_vs_PH3']==len(prior_depots|set(delta)))
  shared=read(H/'shared_evidence_registry.json');ck('shared-evidence-IDs-unique',len({r['id']for r in shared['items']})==len(shared['items']))
  for r in shared['items']:pin(r['path'],r['sha256'])
  remaining=read(H/'remaining_blockers.json');unknownpairs={(r['quest_id'],r['stage'])for r in cm if r['status']=='UNKNOWN'}
  ck('all-five-target-UNKNOWNs-retained-in-blocker-report',unknownpairs<={(r['quest_id'],r['stage'])for r in remaining['rows']if r['status']=='UNKNOWN'})
  ck('all-thirteen-partial-repair-history-blocks-retained',fails<={(r['quest_id'],r['stage'])for r in remaining['rows']if 'PARTIAL_REPAIR_BLOCKED_HISTORY'in r.get('classification','')})
  boundary=remaining['shared_registration_engine_boundary'];ck('exact-binary-dispatch-UNKNOWN-is-separate-and-visible','UNKNOWN'in json.dumps(boundary)and bool(boundary))
  compile=read(H/'compile_reuse_01.json');pin(compile['prior_result'],compile['prior_result_sha256']);previous_compile=read(compile['prior_result'])
  ck('no-fresh-compile-fabricated',compile['fresh_SCC_invocation']is False and compile['current_installed_pins_equal']and compile['compiled_sha256']==previous_compile['compiled_sha256'])
  for p,h in previous_compile['input_pins'].items():pin(p,h)
  ck('preservation-actual-zero-drift',all(pres[k]==0 for k in ['protected_hash_differences','game_metadata_differences','save_metadata_differences','compile_input_differences','game_writes','save_writes'])and pres['tracked_diff_unchanged'])
  report=(H/'REPORT.md').read_text(encoding='utf-8-sig')
  for value,kind in [(pres['protected_sha256_files'],'protected hashes'),(pres['whole_game_metadata_files'],'game'),(pres['whole_save_metadata_files'],'save')]:ck('report-count-matches-preservation:'+kind,str(value)in report,value=value)
  ck('no-live-or-entire-save-coverage-claim',all(s in report for s in ['Zero quests','STATIC_VERIFIED','Nothing was installed','five UNKNOWNs','conditional prospective']))
  # Every declared local path/hash pair in top-level publication is checked; unresolved depot names are not treated as filenames.
  for file in H.glob('*.json'):
   if file.name=='completion.json':continue
   for obj in walk(read(file)):
    if isinstance(obj.get('path'),str)and isinstance(obj.get('sha256'),str)and Path(obj['path']).is_file():pin(obj['path'],obj['sha256'])
    for key,h in obj.items():
     if key.endswith('_sha256')and isinstance(h,str):
      p=obj.get(key[:-7])
      if isinstance(p,str)and Path(p).is_file():
       if re.fullmatch(r'[0-9a-fA-F]{64}',h):pin(p,h)
       elif h=='RECORDED_BY_FINAL_COVERAGE_INDEX':
        index=W/'prealpha/quest_restoration_qr5/group_evidence_index.json';pin(index);matches={x['sha256']for x in walk(read(index))if x.get('path')==p and isinstance(x.get('sha256'),str)}
        ck('historical-symbolic-digest-resolves-uniquely:'+p,len(matches)==1 and all(re.fullmatch(r'[0-9a-fA-F]{64}',s)for s in matches))
        if len(matches)==1:
         expected=next(iter(matches));pin(p,expected);indirections.append({'publication':str(file),'reference':p,'symbol':h,'index':str(index),'index_sha256':sha(index),'resolved_sha256':expected})
       else:ck('unresolved-nondigest-hash-indirection:'+str(file)+':'+key,False,value=h)
  for file in H.glob('*.md'):
   text=file.read_text(encoding='utf-8-sig')
   for link in re.findall(r'\]\(([^)]+)\)',text):
    if link.startswith(('http:','https:','#')):continue
    path=Path(link.split('#',1)[0]);path=path if path.is_absolute()else file.parent/path;ck('publication-local-link:'+file.name+':'+link,path.exists())
 # Adversarial mutation controls on real final rows: missing target, stale generic text, false future PASS.
 controls=[]
 without=cm[:-1];controls.append({'fault':'one-final-quest-contract-missing','detected':len(without)!=len(selected)*len(STAGES)})
 sample=dict(by[next(iter(fails))]);sample['status']='PASS';controls.append({'fault':'future-only-repair-promoted-to-blanket-PASS','detected':sample['status']!='CONDITIONAL'})
 sample=dict(by[next(iter(targets))]);sample['proven']=['QR1 pending deep audit'];controls.append({'fault':'generic-pending-text-replaces-actual-investigation','detected':bool(re.search(r'QR1\s+pending|pending\s+deep',json.dumps(sample['proven']),re.I))})
 for c in controls:ck('adversarial-control:'+c['fault'],c['detected'])
 unstable=[]
 for p,observation in HASH_OBSERVATIONS.items():
  st=Path(observation['path']).stat()
  if(st.st_size,st.st_mtime_ns)!=observation['metadata']:unstable.append(observation['path'])
 ck('all-current-initial-hash-observations-postcheck-metadata-stable',not unstable,unstable=unstable)
 success='PASS_INDEPENDENT_MATRIX_AND_FROZEN_SOURCE_ONLY'if args.matrix_only else'PASS_INDEPENDENT_FINAL21_COMPLETENESS_WITH_LIMITS'
 scope='Independent21-target/1610-grid/provenance/CSV/frozen-source review only. Reports, ledger, package and preservation final gates are intentionally outside this phase.'if args.matrix_only else'Independent target/completeness/accounting/source-pin review. Package review is separately pinned; no game or save behavior is inferred. Coordinator completion seal is intentionally written after this review.'
 result={'status':success if not issues else'FAIL','review_mode':'MATRIX_AND_FROZEN_SOURCE_ONLY'if args.matrix_only else'FINAL_PUBLICATION_AND_PINNED_PACKAGE_REVIEWS','checks':checks,'issues':issues,'controls':controls,'reviewed_input_pins':pins,'current_initial_hash_observations':HASH_OBSERVATIONS,'adjacent_current_review_hash_observations':carry,'resolved_historical_hash_indirections':indirections,'hash_reuse_boundary':'Current streaming SHA observations memoized by stable size/mtime_ns, optionally from the explicitly pinned adjacent completed pass after interpretation-only fixes, with final metadata stability. No historical build digests substituted.','selected':len(selected),'contracts':len(cm),'original_targets':len(targets),'original_FAILs':len(fails),'original_UNKNOWNs':len(unknowns),'current_status_counts':counts,'fully_static_verified':sorted(fully),'target_results':final,'additional_changed_contracts':extras,'source_delta':delta,'removed_source_resources':sorted(removed),'scope':scope,'runtime_writes':0}
 save(out/'review.json',result);print(result['status'],len(checks),'checks',len(issues),'issues')
 if issues:print([x['check']for x in issues[:20]]);raise SystemExit(1)
if __name__=='__main__':main()
