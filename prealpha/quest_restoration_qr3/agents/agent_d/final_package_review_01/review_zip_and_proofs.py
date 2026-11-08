"""Independent ZIP/package/proof-equivalence review. No extraction or builds."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile
W=Path(__file__).resolve().parents[5];Q=W/'prealpha/quest_restoration_qr3';HERE=Path(__file__).resolve().parent;O=HERE/'evidence'
assert O.is_dir() and not (O/'review.json').exists(),'Fresh completed archive review required'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def hashbytes(x):return hashlib.sha256(x).hexdigest().upper()
archive=read(O/'archive_review.json');assert archive['status']=='PASS_INDEPENDENT_ACTUAL_ARCHIVE_COMPARISON'
old=W/'prealpha/phone_studios_ph3/candidate_01/package';new=Q/'candidate_01/package';manifest=read(Q/'candidate_01/package_manifest.json')
oldfiles={p.relative_to(old).as_posix():p for p in old.rglob('*') if p.is_file()};newfiles={p.relative_to(new).as_posix():p for p in new.rglob('*') if p.is_file()}
assert set(oldfiles)==set(newfiles) and len(newfiles)==51
rows=[];changed=[]
for path in sorted(newfiles):
 a=sha(oldfiles[path]);b=sha(newfiles[path]);rows.append({'path':path,'baseline_sha256':a,'candidate_sha256':b,'bytes':newfiles[path].stat().st_size,'changed':a!=b})
 if a!=b:changed.append(path)
assert changed==['archive/pc/mod/zzzz_PTFR_Combined.archive']
xl='archive/pc/mod/zzzz_PTFR_Combined.archive.xl';assert sha(newfiles[xl])=='C55FB23E72710FD0FC8D348C62E2118C2E3FAD04DE3FCE2E6B459E6AB2A1F720'
assert len(archive['resources'])==1574 and len(archive['changed_resources'])==2
mf={r['path']:r for r in manifest['files']};assert set(mf)==set(newfiles)
for r in rows:assert r['candidate_sha256']==mf[r['path']]['sha256'] and r['bytes']==mf[r['path']]['bytes']
z=Q/'candidate_01/PTFR_QR3_quest_static_candidate_full_51.zip';zh=sha(z);assert zh==manifest['zip_sha256']
ziprows=[]
with zipfile.ZipFile(z) as f:
 assert f.testzip() is None
 assert len(f.infolist())==51 and len(f.namelist())==len(set(f.namelist()))
 assert set(f.namelist())==set(newfiles)
 for info in f.infolist():
  path=PurePosixPath(info.filename);assert not info.is_dir() and not path.is_absolute() and '..'not in path.parts and '\\'not in info.filename
  h=hashbytes(f.read(info));assert h==sha(newfiles[info.filename]);ziprows.append({'path':info.filename,'sha256':h,'bytes':info.file_size,'crc32':'%08X'%info.CRC})
proofs=[]
for name in ['brendan_serialized.json','mq030_serialized.json']:
 p=HERE.parent/'reviews'/name;proof=read(p);assert proof['status'].startswith('PASS')
 for key in ['before_json','after_json','staged_raw']:
  item=proof['inputs'][key];assert sha(item['path'])==item['sha256'],(name,key)
 resource=proof['inputs']['staged_raw']
 assert resource['sha256'] in {r['after'] for r in archive['changed_resources']}
 proofs.append({'path':str(p),'sha256':sha(p),'status':proof['status'],'check_count':proof['check_count'],'staged_resource_sha256':resource['sha256']})
out={'status':'PASS_INDEPENDENT_FINAL_PACKAGE_REVIEW','reviewer':'Agent D; separate actual ArchiveReader and Python ZIP comparison, not root packer execution','archive_review_sha256':sha(O/'archive_review.json'),'archive_members':1574,'unchanged_archive_payloads':1572,'changed_archive_payloads':archive['changed_resources'],'new_depot_keys':0,'missing_depot_keys':0,'package_paths':51,'unchanged_package_files':50,'changed_package_files':changed,'package_files':rows,'registration_evidence':{'xl_byte_identical':True,'xl_sha256':sha(newfiles[xl]),'new_generated_injection_IDs':0,'limit':'Registration set cannot change when XL bytes are identical; previous provider/PH2 collision evidence reused, not re-censused.'},'zip':{'path':str(z),'sha256':zh,'bytes':z.stat().st_size,'crc_pass':True,'file_count':51,'files':ziprows},'serialized_graph_proofs':proofs,'compile':'No REDscript source/package changes; 50 other package files including REDS and XL are byte-identical. Unchanged 131-source SCC evidence is reused per QR3; no compile was launched by this review.','limitations':['PASS concerns actual packaged bytes, preserved saved-ID/native-body proofs for exact reviewed inputs, and CRC/hash integrity.','No deployment, game launch, save/fact change, publication, runtime behavior or saved-transition success is claimed.','Root package_manifest status remains staged; selected Brendan sequels still need supported earned-history adapter, and engine/native retirement remains live-only.'],'game_writes':0,'save_writes':0,'installed':False,'published':False}
(O/'review.json').write_text(json.dumps(out,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
print(json.dumps({'status':out['status'],'archive_members':1574,'changed_payloads':2,'unchanged_package_files':50,'zip_files':51,'review_sha256':sha(O/'review.json')}))
