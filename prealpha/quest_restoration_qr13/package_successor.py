"""Package the changed QR13 successor, keeping the installed game untouched."""
from pathlib import Path
import hashlib,json,zipfile
H=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def main():
 c=H/'candidate_01';ep=H/'source_epoch_01.json';e=read(ep);b=read(c/'rebuild_01.json');base=read(H/'baseline.json')
 assert b['status']=='PASS_QR13_FULL_CONSOLIDATED_ARCHIVE_READBACK'and b['epoch_sha256']==sha(ep)
 assert {r['depot']:r['sha256']for r in b['resources']}==e['source_resources']
 rows=[{'path':p.relative_to(c/'package').as_posix(),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted((c/'package').rglob('*'))if p.is_file()]
 assert len(rows)==len(base['package_files'])==51
 changed=[r['path']for r in rows if base['package_files'][r['path']]!=r['sha256']]
 assert set(changed)=={'archive/pc/mod/zzzz_PTFR_Combined.archive',*[r['path']for r in e['scripts_changed']]}
 z=c/'PTFR_QR13_Staged_NotInstalled.zip';assert not z.exists()
 with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as f:
  for r in rows:
   # Fixed entry metadata makes ZIP wrapping reproducible for exact package bytes.
   info=zipfile.ZipInfo(r['path'],(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   f.writestr(info,(c/'package'/r['path']).read_bytes(),compresslevel=6)
 with zipfile.ZipFile(z)as f:
  assert f.testzip()is None and set(f.namelist())=={r['path']for r in rows}and len(f.infolist())==len(rows)
  for r in rows:assert hashlib.sha256(f.read(r['path'])).hexdigest().upper()==r['sha256']
 pm={'status':'STAGED_QR13_CHANGED_SUCCESSOR_NOT_INSTALLED_INDEPENDENT_PACKAGE_REVIEW_PENDING','relative_to':'QR8:02','files':rows,'paths':len(rows),'source_payloads':len(e['source_resources']),
  'changed_package_paths':changed,'changed_resources':e['resources_changed'],'changed_scripts':e['scripts_changed'],'unchanged_old_payloads':len(e['source_resources'])-len(e['resources_changed']),
  'archive_sha256':b['archive_sha256'],'xl_sha256':b['xl_sha256'],'zip':str(z),'zip_sha256':sha(z),'zip_bytes':z.stat().st_size,'compile_result':e['compile_result'],
  'scope':'Ronald prospective actual-consent enrollment/contact plus strict pre-ending-certified peaceful final-Theo continuation. No general Spray/old-clock/old-issued adapter.',
  'opaque_limits':'Machine-spot placement remains OPAQUE; exact original quest prefab referenced under independently reviewed support lifetime. Saved refresh/lease/render/UI remain LIVE_ONLY.',
  'installed':False,'published':False,'game_writes':0,'save_writes':0}
 p=c/'package_manifest.json';assert not p.exists();p.write_text(json.dumps(pm,indent=2)+'\n',encoding='utf-8')
 e.update(epoch_key='QR13:02',predecessor_epoch=str(ep),predecessor_epoch_sha256=sha(ep),package_files=rows,archive_sha256=b['archive_sha256'],zip=str(z),zip_sha256=sha(z),package_manifest_sha256=sha(p),package_state='REBUILT_AND_FULLY_READ_BACK_PENDING_INDEPENDENT_PACKAGE_REVIEW')
 dest=H/'source_epoch_02.json';assert not dest.exists();dest.write_text(json.dumps(e,indent=2)+'\n',encoding='utf-8')
 print({'status':pm['status'],'package_paths':len(rows),'payloads':len(e['source_resources']),'zip':str(z),'zip_sha256':sha(z)})
if __name__=='__main__':main()
