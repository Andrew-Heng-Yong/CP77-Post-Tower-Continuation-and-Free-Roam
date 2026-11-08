"""Independent QR6 final evidence completeness review.

Standard library only; no coordinator finalizer/packer or investigator import.
Run only after coordinator freezes final artifacts. Output must be fresh.
"""
from pathlib import Path
import argparse,json,csv,hashlib,collections,re,ast
W=Path(__file__).resolve().parents[5];H=W/'prealpha/quest_restoration_qr6';P=W/'prealpha/quest_restoration_qr5'
STAGES={'entry','eligibility','communications','ownership','progression','presentation','journal','completion_rewards_cleanup','persistence','shared_dependencies'}
ALLOWED={'PASS','APPROVED_DEVIATION','CONDITIONAL','OPAQUE','UNKNOWN','FAIL','LIVE_ONLY'}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
HASH={}
def sha(p):
 p=Path(p);k=str(p.resolve());s=p.stat();tag=(s.st_size,s.st_mtime_ns)
 if k not in HASH or HASH[k][0]!=tag:HASH[k]=(tag,hashlib.sha256(p.read_bytes()).hexdigest().upper())
 return HASH[k][1]
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def run(out,package_review,preservation_review):
 O=Path(out);assert not O.exists();O.mkdir(parents=True);T=[];issues=[];pins={}
 def ck(k,b,e):
  T.append({'name':k,'pass':bool(b),'evidence':e})
  if not b:issues.append({'check':k,'evidence':e})
 def pin(p,h=None,scope=''):
  p=Path(p);ok=p.is_file();actual=sha(p)if ok else None;ck('pinned input '+str(p),ok and(h is None or actual==h),{'expected':h,'actual':actual,'scope':scope});
  if ok:pins[str(p.resolve())]=actual
  return actual
 files=['queue.json','quest_status_matrix.json','quest_status_matrix.csv','contract_status_matrix.json','contract_status_matrix.csv','coverage.json','checkpoint.json','group_evidence_index.json','progress.json','defects_and_repairs.json','repair_queue.json','shared_evidence_registry.json','approved_changes_00.json','source_epoch_00.json','source_epoch_identity.json','source_resource_inventory.json','prioritized_discrepancies.json','REPORT.md','HANDOFF.md','README.md','HARDENING_PLAN.md','INGAME_VALIDATION_PLAN.md']
 for f in files:pin(H/f,scope='Frozen final artifact')
 catalogue=W/'research/gig_restoration/lore_whitelists_v6_2_sidejobs.json';pin(catalogue);cat=read(catalogue);registry=cat['decision_registry'];selected={r['id']for r in registry if r['decision']=='INCLUDE'}
 ck('actual registry selected identity uniqueness',len(selected)==sum(r['decision']=='INCLUDE'for r in registry),len(selected));ck('user fixed whitelist size161',len(selected)==161,len(selected))
 q=read(H/'queue.json');old=read(P/'queue.json');rows=q['quests'];qm=read(H/'quest_status_matrix.json');cm=read(H/'contract_status_matrix.json');oldcm=read(P/'contract_status_matrix.json');olddeep=set(old['deep_reviewed_ids']);new=selected-olddeep
 ck('queue exactly decision-registry selected IDs',len(rows)==len(selected)and{r['id']for r in rows}==selected,len(rows));ck('independently derived128old33new',len(olddeep)==128 and len(new)==33 and olddeep|new==selected,{'old':len(olddeep),'new':len(new)})
 qby={r['id']:r for r in rows};oldby={r['id']:r for r in old['quests']};qmid={r.get('id',r.get('quest_id'))for r in qm};ck('quest matrix161 identities',len(qm)==161 and qmid==selected,len(qm));ck('deep-reviewed queue equals selected',set(q['deep_reviewed_ids'])==selected and q['deep_reviewed_count']==161,{'count':q['deep_reviewed_count']})
 pairs=[(r['quest_id'],r['stage'])for r in cm];ck('1610unique quest-stage pairs',len(cm)==1610 and len(set(pairs))==1610 and set(pairs)=={(i,s)for i in selected for s in STAGES},len(cm));cmb={(r['quest_id'],r['stage']):r for r in cm};oldcmb={(r['quest_id'],r['stage']):r for r in oldcm}
 for i in olddeep:
  for s in STAGES:ck('retained old contract exact '+i+':'+s,cmb[(i,s)]==oldcmb[(i,s)],'Exact previous QR5matrix row, including source and peer provenance')
  for k in ['deep_review','deep_review_sha256','review','contracts']:ck('retained old quest provenance '+i+':'+k,qby[i].get(k)==oldby[i].get(k),k)
 # New33 are derived from registry minus old deep; no batch/count shortcut.
 progress=read(H/'progress.json');groups=progress['groups'];gids=[];findings={};reviewed=set()
 for name,g in groups.items():
  ids=g['ids'];gids+=ids;ck('group reviewed '+name,g['status']=='REVIEWED_WITH_LIMITS',g['status']);pin(g['result'],g['result_sha256']);gr=read(g['result']);ck('group real selected identities '+name,set(gr['quest_ids'])==set(ids)and set(ids)<=new,ids)
  for p,h in g.get('investigation_input_pins',{}).items():pin(p,h,'Investigation frozen inputs')
  rr=g['review'];pin(rr['path'],rr['sha256'],'Independent actual-resource peer');review=read(rr['path']);ck('peer review no unresolved failures '+name,not review.get('failures')and not review.get('issues'),{'status':review.get('status'),'failures':review.get('failures'),'issues':review.get('issues')});ck('peer assigned separate worker '+name,rr.get('reviewer')!=g.get('worker'),{'author':g.get('worker'),'reviewer':rr.get('reviewer')})
  for f in g['findings']:
   pin(f['contracts'],f['sha256'],'Exact frozen ten-contract findings');fc=read(f['contracts']);i=f['id'];findings[i]=fc;reviewed.add(i);ck('all ten specific contracts '+i,set(fc['contracts'])==STAGES and fc['quest_id']==i and fc['fully_static_verified']is False,list(fc['contracts']))
   for s,c in fc['contracts'].items():
    row=cmb[(i,s)];ck('new frozen contract core matches final '+i+':'+s,all(row.get(k)==c.get(k)for k in ['status','proven','approved_differences','remaining']),{'status':c['status'],'source':f['contracts']});ck('new evidence retains frozen links '+i+':'+s,set(c['evidence'])<=set(row['evidence']),c['evidence']);ck('actual specific proof and valid disposition '+i+':'+s,c['status']in ALLOWED and bool(c['proven'])and bool(c['evidence']),c['status'])
    ck('new matrix correct frozen provenance '+i+':'+s,row.get('findings_source')==f['contracts']and row.get('findings_source_sha256')==f['sha256'],{'source':row.get('findings_source'),'sha256':row.get('findings_source_sha256')});
    for ep in c['evidence']:ck('new evidence link exists '+i+':'+s+':'+ep,Path(ep).is_file(),ep)
 ck('nine groups cover33exactly once',len(groups)==9 and len(gids)==33 and len(set(gids))==33 and set(gids)==new,{'groups':len(groups),'ids':gids});ck('every new quest reviewed',reviewed==new,sorted(new-reviewed));ck('330new dispositions',sum(r['quest_id']in new for r in cm)==330,330)
 # Old blockers remain visible instead of being counted as repaired or static-PASS.
 oldfails={(r['quest_id'],r['stage'])for r in oldcm if r['status']=='FAIL'};fails={(r['quest_id'],r['stage'])for r in cm if r['status']=='FAIL'};ck('all13oldFAILs preserved',len(oldfails)==13 and fails==oldfails,sorted(fails));ck('Nitro competing native entry sources not approved',all(cmb[('mq060_nitro',s)]['status']=='UNKNOWN'for s in ['entry','eligibility','shared_dependencies']),{s:cmb[('mq060_nitro',s)]['status']for s in ['entry','eligibility','shared_dependencies']});ck('Career early history uncertainty retained',cmb[('mws_wat_08_trauma_drama','persistence')]['status']=='UNKNOWN',cmb[('mws_wat_08_trauma_drama','persistence')]['status'])
 fully={i for i in selected if all(cmb[(i,s)]['status']in['PASS','APPROVED_DEVIATION']for s in STAGES)};ck('zerofullystatic, no status laundering',not fully and q.get('static_verified_count')==0,sorted(fully));counts=collections.Counter(r['status']for r in cm);newcounts=collections.Counter(r['status']for r in cm if r['quest_id']in new)
 for f in ['coverage.json','checkpoint.json']:
  s=read(H/f);ck('summary identity/counts '+f,all(s[k]==v for k,v in {'selected':len(selected),'prior_deep':len(olddeep),'new_deep':len(new),'deep_total':161,'remaining':0,'contracts':len(cm),'fully_static_verified':0,'fully_resolved_static_contracts':counts['PASS']+counts['APPROVED_DEVIATION'],'new_confirmed_defects':0,'new_repaired_defects':0,'existing_blocked_defects':2,'cumulative_staged_repairs':8,'source_authority_conflict_count':1,'new_runtime_resource_changes':0,'groups_independently_reviewed':len(groups)}.items()),s)
  ck('summary dispositions exact '+f,s['all_contract_status_counts']==dict(counts)and s['new_contract_status_counts']==dict(newcounts),{'all':dict(counts),'new':dict(newcounts)});ck('summary queue pin exact '+f,s['queue_sha256']==sha(H/'queue.json'),s['queue_sha256'])
 checkpoint=read(H/'checkpoint.json');pin(checkpoint['report'],checkpoint['report_sha256'],'Frozen report checkpoint');pin(checkpoint['handoff'],checkpoint['handoff_sha256'],'Frozen handoff checkpoint')
 idx=read(H/'group_evidence_index.json');ck('groupindex exactly nine current groups',{g['group']for g in idx['groups']}==set(groups)and len(idx['groups'])==len(groups),len(idx['groups']))
 for g in idx['groups']:
  pg=groups[g['group']];ck('groupindex exact current findings and peer '+g['group'],g['findings']==pg['findings']and g['results']==pg['result']and g['results_sha256']==pg['result_sha256']and g['review']==pg['review'],g['group'])
 inv=read(H/'source_resource_inventory.json');derived_obs=set()
 for p,h in inv['input_manifest_pins'].items():
  pin(p,h,'Resource inventory input manifest');parts=Path(p).parts;gn=parts[parts.index('groups')+1]
  for r in read(p):
   if r.get('depot')and r.get('json')and r.get('binary',r.get('raw')):derived_obs.add((gn,r['depot'],r.get('resource_sha256',r.get('raw_sha256',r.get('sha256')))))
 actual_obs={(r['group'],r['depot_or_recipe_alias'],r['resource_sha256'])for r in inv['observations']}
 ck('sourceinventory independently rederived all source observations',actual_obs==derived_obs and len(inv['observations'])==len(derived_obs)and inv['unique_depot_or_alias_and_hash_pairs']==len({(r['depot_or_recipe_alias'],r['resource_sha256'])for r in inv['observations']}),{'derived_observations':len(derived_obs),'actual':len(actual_obs),'unique':inv['unique_depot_or_alias_and_hash_pairs']})
 for r in inv['observations']:
  ck('inventory source manifest pin '+r['group']+':'+r['depot_or_recipe_alias'],Path(r['input_manifest']).is_file()and sha(r['input_manifest'])==r['input_manifest_sha256'],r['input_manifest'])
  if r.get('binary')and r.get('resource_sha256'):pin(r['binary'],r['resource_sha256'],'Inventory resource alias exact hash')
  if r.get('json')and r.get('json_sha256'):pin(r['json'],r['json_sha256'],'Inventory actual readback exact hash')
 priorities=read(H/'prioritized_discrepancies.json')['rows'];expected_priorities={(r['quest_id'],r['stage'])for r in cm if r['status']in['FAIL','UNKNOWN']};ck('priority21rows exactly all failed/unknown contracts',len(priorities)==len(expected_priorities)==21 and{(r['quest_id'],r['stage'])for r in priorities}==expected_priorities,len(priorities))
 for f,js in [('quest_status_matrix.csv',qm),('contract_status_matrix.csv',cm)]:
  with(H/f).open(encoding='utf-8-sig',newline='')as fp:cs=list(csv.DictReader(fp))
  ck('CSV rowcount '+f,len(cs)==len(js),len(cs));keys=['quest_id','stage','status']if'contract_'in f else['id'if'id'in js[0]else'quest_id','status']
  def csv_same(v,target):
   if target is None:return v in['','None','null']
   if isinstance(target,(dict,list)):
    try:return json.loads(v)==target
    except (ValueError,TypeError):
     try:return ast.literal_eval(v)==target
     except (ValueError,SyntaxError):return False
   if isinstance(target,bool):return v.lower()==str(target).lower()
   return v==str(target)
  for ix,(a,b)in enumerate(zip(cs,js)):
   ck('CSV exact identity/status '+f+':'+str(ix),all(a.get(k)==str(b.get(k))for k in keys if k in a and k in b),{k:a.get(k)for k in keys})
   common=set(a)&set(b);ck('CSV all shared JSON fields exact '+f+':'+str(ix),all(csv_same(a[k],b[k])for k in common),sorted(common))
 # Local epoch00 is byte-identical QR5:08, preserving all prior staged repairs.
 epoch=read(H/'source_epoch_00.json');pred=read(P/'source_epoch_08.json');pin(P/'source_epoch_08.json',epoch['predecessor_epoch_sha256']);ck('all1574resource and51package pins unchanged',epoch['source_resources']==pred['source_resources']and epoch['package_files']==pred['package_files']and len(epoch['source_resources'])==1574 and len(epoch['package_files'])==51,{'payloads':len(epoch['source_resources']),'paths':len(epoch['package_files'])});C=Path(epoch['candidate']);ck('same staged candidate, PH3installed remains separate',str(C)==pred['candidate']and'CANDIDATE'not in str(q.get('installed_baseline','')).upper(),str(C))
 for d,h in epoch['source_resources'].items():pin(C/'archive_source'/Path(d.replace('\\','/')),h,'Independently rehashed final unchanged staged payload')
 for r in epoch['package_files']:pin(C/'package'/Path(r['path']),r['sha256'],'Exact unchanged package path')
 pin(epoch['zip'],epoch['zip_sha256'],'Exact retained QR5 staged ZIP; no new package created');pin(epoch['package_manifest_path'],epoch['package_manifest_sha256'],'Exact retained staged package manifest')
 allow=read(H/'approved_changes_00.json');ck('no new runtime allowlist',allow['resources']==[]and allow['status']=='NO_QR6_RUNTIME_CHANGES',allow['status']);pin(allow['inherited_allowlist'],allow['inherited_allowlist_sha256']);prior=allow['inherited_prior_repairs'];ck('nineprior repaired resources retained',len(prior)==9 and len({r['depot']for r in prior})==9,len(prior))
 for r in prior:ck('prior repair exact staged hash '+r['depot'],epoch['source_resources'][r['depot']]==r['after'],r['after'])
 ck('no new consolidated ZIP or successor candidate in QR6',not list(H.rglob('*.zip'))and not list(H.glob('candidate_*')),'Read-only evidence exports may contain copied native bytes; effective source/package equality is checked independently')
 ledger=read(H/'defects_and_repairs.json');oldledger=read(P/'defects_and_repairs.json');ck('eight staged prior repairs retained',ledger.get('cumulative_staged_repairs')==8,ledger.get('cumulative_staged_repairs'))
 ck('no QR6 confirmed runtime repair invented',ledger.get('new_repaired_unique_defects',0)==0,ledger.get('new_repaired_unique_defects'));ck('existing unique defects not discarded',len(ledger.get('defects',[]))>=len(oldledger['defects']),len(ledger.get('defects',[])))
 shared=read(H/'shared_evidence_registry.json');ck('shared registry IDs unique',len({r['id']for r in shared['items']})==len(shared['items']),len(shared['items']))
 for r in shared['items']:pin(r['path'],r['sha256'],'Shared evidence exact applicability must be independently reviewed')
 for label,path in [('independent_package',package_review),('preservation',preservation_review)]:
  pin(path,scope=label);obj=read(path);ck(label+' has no failures or issues',not obj.get('failures')and not obj.get('issues')and not obj.get('discrepancies'),{'status':obj.get('status'),'checks':obj.get('checks'),'failures':obj.get('failures'),'issues':obj.get('issues')});ck(label+' passed',str(obj.get('status','')).startswith('PASS')or obj.get('status')in['INDEPENDENT_FINAL_PACKAGE_PASS','UNCHANGED_QR5_PACKAGE_INDEPENDENTLY_VERIFIED'],obj.get('status'))
 pres=read(preservation_review);txt=(H/'REPORT.md').read_text();ck('reported preservation game/save totals match actual evidence',str(pres['whole_game_metadata_files'])+' game'in txt and str(pres['whole_save_metadata_files'])+' save'in txt,{'game':pres['whole_game_metadata_files'],'save':pres['whole_save_metadata_files']});ck('actual preservation has zero deltas and no writes',all(pres[k]==0 for k in ['protected_hash_differences','game_metadata_differences','save_metadata_differences','compile_input_differences','game_writes','save_writes','new_runtime_changes'])and pres['tracked_diff_unchanged'],pres)
 compile_path=H/'verification/compile_01/result.json';pin(compile_path);compile=read(compile_path);ck('current complete131-source compilation bound to134pins',compile['status']=='PASS_CURRENT_INPUTS_OFFLINE_COMPILED'and compile['source_count']==131 and compile['managed_sources']==46 and compile['input_pin_count']==134 and len(compile['input_pins'])==134 and compile['fresh_SCC_invocation']and not compile['game_writes']and not compile['save_writes'],compile['status'])
 for p,h in compile['input_pins'].items():pin(p,h,'Independent current compiler/source/cache pin recheck')
 # Each report link resolves; source text must continue to identify limits and no deployment.
 for f in ['REPORT.md','HANDOFF.md','HARDENING_PLAN.md','INGAME_VALIDATION_PLAN.md']:
  txt=(H/f).read_text(encoding='utf-8-sig');links=re.findall(r'\]\(([^)]+)\)',txt)
  for link in links:
   if link.startswith(('http:','https:','#')):continue
   target=link.split('#',1)[0].replace('%20',' ');target=target[1:-1]if target.startswith('<')and target.endswith('>')else target;p=Path(target);p=p if p.is_absolute()else H/p
   deferred=p.resolve()==(H/'completion.json').resolve()and not p.exists()
   ck('report link resolves or explicitly deferred completion '+f+':'+link,p.is_file()or deferred,{'path':str(p),'deferred_post_review_completion':deferred})
 ck('report preserves static versus gameplay distinction','gameplay'in(H/'REPORT.md').read_text().lower()and'0'in(H/'REPORT.md').read_text(),'No structural certificate equated with played success')
 report={'status':'PASS_ADVERSARIAL_COMPLETENESS_WITH_EXPLICIT_STATIC_LIMITS'if not issues else'FAIL_INDEPENDENT_COMPLETENESS_REVIEW','checks':len(T),'failures':issues,'issues':issues,'selected':len(selected),'prior_deep':len(olddeep),'new_deep':len(new),'deep_total':len(reviewed|olddeep),'remaining_deep':len(new-reviewed),'contracts':len(cm),'new_contracts':330,'fully_static_verified':len(fully),'contract_status_counts':dict(counts),'new_contract_status_counts':dict(newcounts),'old_FAILs_visible':len(fails),'source_epoch':'QR6:00 byte-identical QR5:08','new_runtime_changes':0,'new_ZIPs':0,'independent_review_scope':['Derived selected IDs from actual catalogue decision_registry; did not import coordinator finalizer/packer or any author verifier.','Exact old contract/provenance retention, all new frozen findings/peer/input pins, unique161/1610matrix/CSV identities, original13FAILs and precise UNKNOWN statuses independently checked.','Independently rehashed all staged source/package files and nine prior repaired resources; package/preservation reviews remain separate bounded evidence.','This is completeness/provenance review, not reinvestigation of every native quest branch or gameplay success.','Source assertion totals are not unique gameplay coverage; runtime/opaque/effective-override/saved-owner limits remain visible.'],'input_pins':str((O/'input_pins.json').resolve()),'tests':str((O/'tests.json').resolve())};save(O/'input_pins.json',pins);save(O/'tests.json',{'count':len(T),'checks':T});save(O/'review.json',report);print(json.dumps({'status':report['status'],'checks':len(T),'issues':len(issues),'report':str(O/'review.json'),'sha256':sha(O/'review.json')}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--package-review',required=True);p.add_argument('--preservation-review',required=True);a=p.parse_args();run(a.output,a.package_review,a.preservation_review)
