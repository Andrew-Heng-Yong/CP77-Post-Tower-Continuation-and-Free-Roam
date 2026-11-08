"""Package the changed QR5 successor; reuse exact unchanged compile inputs."""
from pathlib import Path
import sys,hashlib,zipfile
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (C/'package_manifest.json').exists()
b=read(C/'rebuild_01.json');e=read(O/'source_epoch_00.json');a=read(O/'approved_changes_02.json');expected=[r['depot']for r in a['resources']]
assert b['status']=='PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED'and set(b['changed_resources'])==set(expected)and b['readback_count']==len(e['source_resources'])
rows=[];delta=[]
for r in e['package_files']:
 f=C/'package'/r['path'];h=sha(f);rows.append({'path':r['path'].replace('\\','/'),'sha256':h,'bytes':f.stat().st_size})
 if h!=r['sha256']:delta.append(r['path'].replace('\\','/'))
assert delta==['archive/pc/mod/zzzz_PTFR_Combined.archive']
compilep=W/'prealpha/quest_restoration_qr1/candidate_01/compile_01/result.json';cr=read(compilep);assert cr['status']=='PASS'
assert all(sha(p)==h for p,h in cr['input_pins'].items())and all(sha(p)==r['sha256']for p,r in cr['staged_sources'].items())
managed=[]
for f in (C/'package/r6/scripts').rglob('*.reds'):
 rel=f.relative_to(C/'package/r6/scripts');prior=W/'prealpha/quest_restoration_qr1/candidate_01/compile_01/scripts/game'/rel
 assert sha(f)==cr['staged_sources'][str(prior)]['sha256'];managed.append(str(rel))
write(O/'compile_reuse.json',{'status':'PASS_EXACT_UNCHANGED_REDSCRIPT_INPUTS_REUSED','sources':len(cr['staged_sources']),'staged_managed_sources':len(managed),'compiler_cache_input_pins':len(cr['input_pins']),'prior_result':str(compilep),'prior_result_sha256':sha(compilep),'fresh_SCC_invocation':False,'reason':'One private CR2W changed; exact REDscript/compiler/cache inputs unchanged'})
z=C/'PTFR_QR5_Staged_NotInstalled.zip';assert not z.exists()
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as f:
 for r in rows:f.write(C/'package'/r['path'],r['path'])
with zipfile.ZipFile(z)as f:
 assert f.testzip()is None and len(f.namelist())==len(rows)
 for r in rows:assert hashlib.sha256(f.read(r['path'])).hexdigest().upper()==r['sha256']
m={'status':'STAGED_STATIC_CANDIDATE_NOT_INSTALLED','predecessor':'QR4candidate_01canonical03','paths':len(rows),'files':rows,'source_payloads':b['source_count'],'readback_payloads':b['readback_count'],'changed_resources':expected,'unchanged_resources':b['source_count']-len(expected),'archive_sha256':b['archive_sha256'],'xl_sha256':b['xl_sha256'],'zip':str(z),'zip_sha256':sha(z),'zip_bytes':z.stat().st_size,'new_unique_defects':1,'new_affected_quests':['sts_std_arr_12'],'cumulative_repairs':4,'game_writes':0,'save_writes':0,'installed':False,'published':False,'limits':'Fresh-event monitor repair only; old entered/started save adoption, engine scheduling, world placement and gameplay outcomes remain unverified'}
write(C/'package_manifest.json',m)
e1=read(O/'source_epoch_01.json');e1['epoch']=2;e1['epoch_key']='QR5:02';e1['source_resources']={r['depot']:r['sha256']for r in b['resources']};e1['package_files']=rows;e1['archive_sha256']=m['archive_sha256'];e1['xl_sha256']=m['xl_sha256'];e1['package_state']='REBUILT_ALL_PAYLOADS_READ_BACK_STAGED_NOT_INSTALLED';e1['archive_sha256_semantics']='Canonical current package hash matches manifest and full readback';e1['package_manifest_sha256']=sha(C/'package_manifest.json');e1['predecessor_epoch_path']=str(O/'source_epoch_01.json');e1['predecessor_epoch_sha256']=sha(O/'source_epoch_01.json');e1['approved_changes_sha256']=sha(O/'approved_changes_02.json');e1['changes']=a['resources'];write(O/'source_epoch_02.json',e1)
q=read(O/'queue.json');q['source_epoch']=2;q['source_epoch_manifest']=str(O/'source_epoch_02.json');q['package_verification']='ROOT_PACKED_ALL_PAYLOADS_READ_BACK_INDEPENDENT_PACKAGE_REVIEW_PENDING';write(O/'queue.json',q)
p=read(O/'progress.json');p['repair_epochs'].append(str(O/'source_epoch_02.json'));p['new_defects'][0]['status']='INDEPENDENT_SERIALIZED_VERIFIED_PACKAGED_FINAL_PACKAGE_REVIEW_PENDING';write(O/'progress.json',p)
print({'status':m['status'],'payloads':b['readback_count'],'paths':len(rows),'changed_resources':len(expected),'archive_sha256':m['archive_sha256'],'zip_sha256':m['zip_sha256']})
