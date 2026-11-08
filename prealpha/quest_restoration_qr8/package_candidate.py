"""Package only the actual changed successor; no deployment or release writes."""
from pathlib import Path
import sys,zipfile,hashlib,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not(C/'package_manifest.json').exists()
ep=O/'source_epoch_01.json';e=read(ep);base=read(O/'source_epoch_00.json');a=read(O/'approved_changes_01.json');b=read(C/'rebuild_01.json')
assert b['status']=='PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED'and b['source_epoch_sha256']==sha(ep)
assert {r['depot']:r['sha256']for r in b['resources']}==e['source_resources']
peer=O/'worker_b/reviews/promoted_source/verification_01/review.json';rv=read(peer);assert str(rv['status']).startswith(('PASS','APPROVE'))and not rv.get('issues')and not rv.get('failures')
rows=[];delta=[]
for r in base['package_files']:
 f=C/'package'/r['path'];h=sha(f);rows.append({'path':r['path'].replace('\\','/'),'sha256':h,'bytes':f.stat().st_size})
 if h!=r['sha256']:delta.append(r['path'].replace('\\','/'))
assert delta==['archive/pc/mod/zzzz_PTFR_Combined.archive']and b['xl_sha256']==base['xl_sha256']
crp=W/'prealpha/quest_restoration_qr6/verification/compile_01/result.json';cr=read(crp)
assert cr['status']=='PASS_CURRENT_INPUTS_OFFLINE_COMPILED'
assert all(sha(p)==h for p,h in cr['input_pins'].items())and all(sha(p)==r['sha256']for p,r in cr['staged_sources'].items())
assert len(list((C/'package/r6/scripts').rglob('*.reds')))==len(cr['managed'])and all(sha(C/'package'/r['path'])==r['sha256']for r in cr['managed'])
compiled=Path(cr['command'][cr['command'].index('-outputCacheFile')+1]);assert sha(compiled)==cr['compiled_sha256']
write(O/'verification/compile_successor_01/result.json',{'status':'PASS_EXACT_UNCHANGED_FULL_COMPILE_INPUTS_AND_SUCCESSOR_REDS','source_epoch':str(ep),'source_epoch_sha256':sha(ep),'actual_prior_compile':str(crp),'actual_prior_compile_sha256':sha(crp),'input_pins':len(cr['input_pins']),'staged_sources':len(cr['staged_sources']),'managed_sources':len(cr['managed']),'compiled_output_sha256':sha(compiled),'fresh_QR8_SCC_invocation':False,'reason':'Only one CR2W resource changed. Complete current compiler/source/cache inputs and actual prior output rechecked; all candidate scripts exact.','game_writes':0,'save_writes':0})
z=C/'PTFR_QR8_Staged_NotInstalled.zip';assert not z.exists()
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as f:
 for r in rows:f.write(C/'package'/r['path'],r['path'])
with zipfile.ZipFile(z)as f:
 assert f.testzip()is None and len(f.infolist())==len(rows)and len(set(f.namelist()))==len(rows)
 for r in rows:assert hashlib.sha256(f.read(r['path'])).hexdigest().upper()==r['sha256']
pm={'status':'STAGED_CHANGED_RESOURCE_SUCCESSOR_NOT_INSTALLED','relative_to':'QR7:04','files':rows,'paths':len(rows),'source_payloads':len(e['source_resources']),'readback_payloads':b['readback_count'],'changed_existing_resources':[r['depot']for r in a['resources']],'added_resources':[],'unchanged_QR7_payloads':len(e['source_resources'])-len(a['resources']),'changed_package_paths':delta,'unchanged_XL':True,'archive_sha256':b['archive_sha256'],'xl_sha256':b['xl_sha256'],'zip':str(z),'zip_sha256':sha(z),'zip_bytes':z.stat().st_size,'new_staged_repairs':1,'prior_staged_repairs_or_containments':11,'source_review':str(peer),'source_review_sha256':sha(peer),'compile_reuse':str(O/'verification/compile_successor_01/result.json'),'compile_reuse_sha256':sha(O/'verification/compile_successor_01/result.json'),'limits':['Only first case evaluation with genuine future Armed1 and native sent0 is extended; actual streaming/saved-predicate refresh are LIVE_ONLY.','No first-time enrollment/contact/physical-owner extension, processed-gate replay, old timer adoption or root rearm.','The new archive/ZIP exists because one actual CR2W resource changed; diagnostic artifacts are outside the51-path package.'],'game_writes':0,'save_writes':0,'installed':False,'published':False}
write(C/'package_manifest.json',pm)
e.update(epoch=2,epoch_key='QR8:02',package_files=rows,archive_sha256=pm['archive_sha256'],xl_sha256=pm['xl_sha256'],zip=pm['zip'],zip_sha256=pm['zip_sha256'],package_manifest_sha256=sha(C/'package_manifest.json'),predecessor_epoch_path=str(ep),predecessor_epoch_sha256=sha(ep),scope='Canonical staged source/package with one approved four-guard repair. Full coordinator archive/ZIP readback passed; independent final package review follows.',package_state='REBUILT_ALL_PAYLOADS_READ_BACK_STAGED_NOT_INSTALLED');write(O/'source_epoch_02.json',e)
q=read(O/'queue.json');q.update(source_epoch=2,source_epoch_manifest=str(O/'source_epoch_02.json'),QR8_status='CANONICAL_PACKAGE_FROZEN_INDEPENDENT_REVIEW_PENDING');write(O/'queue.json',q)
c=read(O/'checkpoint.json');c.update(canonical_epoch=str(O/'source_epoch_02.json'),state='QR8_SOURCE_AND_PACKAGE_FROZEN_INDEPENDENT_REVIEW_PENDING',next_action='Independent final package check, source-specific dispositions/readiness/test-plan review and final preservation.');write(O/'checkpoint.json',c)
print({k:pm[k]for k in ['status','source_payloads','paths','archive_sha256','xl_sha256','zip_sha256']})
