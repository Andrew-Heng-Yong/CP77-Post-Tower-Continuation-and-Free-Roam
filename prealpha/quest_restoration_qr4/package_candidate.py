"""Package only the reviewed changed successor and verify unchanged compile inputs."""
from pathlib import Path
import sys,zipfile,hashlib
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (C/'package_manifest.json').exists(),'Preserve existing package'
b=read(C/'rebuild_01.json');assert b['status']=='PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED'
old=read(O/'source_epoch_00.json');plan=read(O/'approved_changes_01.json');expected=[r['depot'] for r in plan['resources']]
assert set(b['changed_resources'])==set(expected) and b['source_count']==len(old['source_resources'])==b['readback_count']
rows=[];changed=[]
for r in old['package_files']:
 p=C/'package'/r['path'];h=sha(p);rows.append({'path':r['path'].replace('\\','/'),'sha256':h,'bytes':p.stat().st_size})
 if h!=r['sha256']:changed.append(r['path'].replace('\\','/'))
assert changed==['archive/pc/mod/zzzz_PTFR_Combined.archive'],changed
compilep=W/'prealpha/quest_restoration_qr1/candidate_01/compile_01/result.json';cr=read(compilep);assert cr['status']=='PASS'
assert all(sha(p)==h for p,h in cr['input_pins'].items()),'Prior compiler/cache/source inputs changed'
assert all(sha(p)==v['sha256'] for p,v in cr['staged_sources'].items()),'Prior131-source compile staging changed'
managed=[]
for p in (C/'package/r6/scripts').rglob('*.reds'):
 rel=p.relative_to(C/'package/r6/scripts');prior=W/'prealpha/quest_restoration_qr1/candidate_01/compile_01/scripts/game'/rel
 assert sha(p)==cr['staged_sources'][str(prior)]['sha256'];managed.append(str(rel))
write(O/'compile_reuse.json',{'status':'PASS_EXACT_UNCHANGED_REDSCRIPT_INPUTS_REUSED','sources':len(cr['staged_sources']),'staged_managed_sources':len(managed),'managed':managed,'prior_result':str(compilep),'prior_result_sha256':sha(compilep),'input_pins_verified':len(cr['input_pins']),'compiler_and_cache_inputs_unchanged':True,'fresh_SCC_invocation':False,'reason':'Only2privateCR2Wresources changed; current131source/compiler/cache inputs hash-identical to successful QR1compile. No changed REDscript requires recompilation.'})
z=C/'PTFR_QR4_Staged_NotInstalled.zip';assert not z.exists()
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as f:
 for r in rows:f.write(C/'package'/r['path'],r['path'])
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None and len(f.namelist())==len(rows)
 for r in rows:assert hashlib.sha256(f.read(r['path'])).hexdigest().upper()==r['sha256']
manifest={'status':'STAGED_STATIC_CANDIDATE_NOT_INSTALLED','predecessor':'QR3candidate_01','paths':len(rows),'files':rows,'source_payloads':b['source_count'],'readback_payloads':b['readback_count'],'changed_resources':expected,'unchanged_resources':b['source_count']-len(expected),'archive_sha256':b['archive_sha256'],'xl_sha256':b['xl_sha256'],'zip':str(z),'zip_sha256':sha(z),'zip_bytes':z.stat().st_size,'new_unique_defects':1,'new_affected_quests':['mq007_smartgun'],'cumulative_repairs':3,'game_writes':0,'save_writes':0,'installed':False,'published':False,'limits':'Future-entry native continuation repair only. Existing saved entered/returned states, live timers/streaming and known MQ007 admission seam remain unverified/unsupported.'}
write(C/'package_manifest.json',manifest)
epoch=read(O/'source_epoch_01.json');epoch['package_files']=rows;epoch['package_state']='REBUILT_ALL_PAYLOADS_READ_BACK_STAGED_ONLY';epoch['package_manifest_sha256']=sha(C/'package_manifest.json');epoch['predecessor_source_epoch_sha256']=sha(O/'source_epoch_01.json');epoch['epoch']=2
write(O/'source_epoch_02.json',epoch)
print({'status':manifest['status'],'payloads':b['readback_count'],'paths':len(rows),'changed_resources':len(expected),'zip_sha256':manifest['zip_sha256']})
