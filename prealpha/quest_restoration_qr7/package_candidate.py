"""Package approved QR7 resources; reuse only exact QR6 compiler input bytes."""
from pathlib import Path
import sys,zipfile,hashlib
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;C=O/'candidate_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
assert not (C/'package_manifest.json').exists()
b=read(C/'rebuild_01.json');e=read(O/'source_epoch_03.json');base=read(O/'source_epoch_00.json');a=read(O/'approved_changes_03.json')
assert b['status']=='PASS_FULL_CONSOLIDATED_REBUILD_NOT_INSTALLED'and b['source_epoch_sha256']==sha(O/'source_epoch_03.json')
assert {r['depot']:r['sha256']for r in b['resources']}==e['source_resources']
rows=[];delta=[]
for r in base['package_files']:
 f=C/'package'/r['path'];h=sha(f);rows.append({'path':r['path'].replace('\\','/'),'sha256':h,'bytes':f.stat().st_size})
 if h!=r['sha256']:delta.append(r['path'].replace('\\','/'))
assert set(delta)=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'}
cp=W/'prealpha/quest_restoration_qr6/verification/compile_01/result.json';cr=read(cp)
assert cr['status']=='PASS_CURRENT_INPUTS_OFFLINE_COMPILED'
assert all(sha(p)==h for p,h in cr['input_pins'].items())and all(sha(p)==r['sha256']for p,r in cr['staged_sources'].items())
for r in cr['managed']:assert sha(C/'package'/r['path'])==r['sha256']
actualmanaged=list((C/'package/r6/scripts').rglob('*.reds'));assert len(actualmanaged)==len(cr['managed'])
compiled=Path(cr['command'][cr['command'].index('-outputCacheFile')+1]);assert sha(compiled)==cr['compiled_sha256']
write(O/'compile_reuse_01.json',{'status':'PASS_EXACT_CURRENT_UNCHANGED_REDSCRIPT_INPUTS_REUSED','prior_result':str(cp),'prior_result_sha256':sha(cp),'input_pin_count':len(cr['input_pins']),'staged_source_count':len(cr['staged_sources']),'managed_sources':len(actualmanaged),'compiled_sha256':sha(compiled),'current_installed_pins_equal':True,'fresh_SCC_invocation':False,'reason':'QR7 changes only CR2W resource and XL bytes. All QR6 sources, compiler/cache inputs, staged managed sources and prior actual compiled output verified byte-identical.','game_writes':0,'save_writes':0})
z=C/'PTFR_QR7_Staged_NotInstalled.zip';assert not z.exists()
with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as f:
 for r in rows:f.write(C/'package'/r['path'],r['path'])
with zipfile.ZipFile(z)as f:
 assert f.testzip()is None and len(f.namelist())==len(rows)and len(set(f.namelist()))==len(rows)
 for r in rows:assert hashlib.sha256(f.read(r['path'])).hexdigest().upper()==r['sha256']
changed=[r['depot']for r in a['resources']if r['before']is not None];added=[r['depot']for r in a['resources']if r['before']is None]
m={'status':'STAGED_STATIC_CANDIDATE_NOT_INSTALLED','predecessor':'QR6:00=QR5:08/candidate_03','paths':len(rows),'files':rows,'source_payloads':len(e['source_resources']),'readback_payloads':len(b['resources']),'changed_existing_resources':changed,'added_resources':added,'unchanged_baseline_payloads':len(base['source_resources'])-len(changed),'changed_package_paths':delta,'archive_sha256':b['archive_sha256'],'xl_sha256':b['xl_sha256'],'zip':str(z),'zip_sha256':sha(z),'zip_bytes':z.stat().st_size,'new_unique_repairs':3,'inherited_repairs':8,'inherited_repaired_resources':9,'inherited_preservation':'Eight resource hashes unchanged; Spy all existing nodes/payloads/phone fixes preserved, only a future Armed edge splice.','compile_reuse':str(O/'compile_reuse_01.json'),'compile_reuse_sha256':sha(O/'compile_reuse_01.json'),'game_writes':0,'save_writes':0,'installed':False,'published':False,'limits':'Prospective entry/listener/news scopes only; old entered/requested/pending histories defer. Native engine scheduling, leases, delivery, concurrent saved owners and gameplay remain unverified.'}
write(C/'package_manifest.json',m)
e.update(epoch=4,epoch_key='QR7:04',package_files=rows,archive_sha256=m['archive_sha256'],xl_sha256=m['xl_sha256'],package_manifest_sha256=sha(C/'package_manifest.json'),predecessor_epoch_path=str(O/'source_epoch_03.json'),predecessor_epoch_sha256=sha(O/'source_epoch_03.json'),package_state='REBUILT_ALL_PAYLOADS_READ_BACK_STAGED_NOT_INSTALLED',scope='Canonical staged source/package, three new repairs. Independent final package review pending; no deployment or gameplay proof.')
write(O/'source_epoch_04.json',e)
q=read(O/'queue.json');q.update(source_epoch=4,source_epoch_manifest=str(O/'source_epoch_04.json'),package_verification='ROOT_COMPLETE_READBACK_INDEPENDENT_REVIEW_PENDING',current_compile=str(O/'compile_reuse_01.json'));write(O/'queue.json',q)
print({k:m[k]for k in ['status','source_payloads','paths','archive_sha256','xl_sha256','zip_sha256']})
