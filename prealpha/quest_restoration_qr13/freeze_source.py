"""Freeze the reviewed staged source/script set before the one archive rebuild."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def main():
 c=H/'candidate_01';base=read(H/'baseline.json');p=read(c/'promotion.json');assert p['status']=='SOURCE_CHANGES_APPROVED_PENDING_PACKAGE'and not p.get('pending_component')
 assert len(p['resources'])==3 and len(p['changed_script_paths'])==2
 expected=dict(base['source_resources'])
 for r in p['resources']:
  assert str(read(r['source_review'])['status']).startswith(('APPROVE','PASS'))and sha(r['source_review'])==r['source_review_sha256'];expected[r['depot']]=r['after']
 actual={str(f.relative_to(c/'archive_source')):sha(f)for f in(c/'archive_source').rglob('*')if f.is_file()};assert actual==expected
 pkg={f.relative_to(c/'package').as_posix():sha(f)for f in(c/'package').rglob('*')if f.is_file()};want=dict(base['package_files'])
 for r in p['changed_script_paths']:want[r['path']]=r['sha256']
 assert pkg==want
 cr=read(H/'verification/compile_01/result.json');assert cr['status']=='PASS_COMPLETE_INPUT_OFFLINE_COMPILE'
 for r in p['changed_script_paths']:
  staged=[v for k,v in cr['staged_sources'].items()if Path(k).name==Path(r['path']).name];assert staged==[r['sha256']]
 epoch={'epoch_key':'QR13:01','candidate':str(c),'relative_to':base['source_epoch'],'relative_to_sha256':base['source_epoch_sha256'],'source_resources':actual,
  'package_prebuild_sha256':pkg,'resources_changed':p['resources'],'scripts_changed':p['changed_script_paths'],'new_depots':[],'new_registrations':0,'xl_sha256':base['package_files']['archive/pc/mod/zzzz_PTFR_Combined.archive.xl'],
  'compile_result':str(H/'verification/compile_01/result.json'),'compile_result_sha256':sha(H/'verification/compile_01/result.json'),'package_state':'SOURCE_AND_SCRIPTS_VERIFIED_PACKAGE_PENDING','installed':False}
 dest=H/'source_epoch_01.json';assert not dest.exists();dest.write_text(json.dumps(epoch,indent=2)+'\n',encoding='utf-8');print({'source_payloads':len(actual),'changed_resources':3,'changed_scripts':2,'package':'READY_FOR_ONE_REBUILD'})
if __name__=='__main__':main()
