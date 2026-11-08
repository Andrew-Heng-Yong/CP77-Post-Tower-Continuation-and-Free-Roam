"""Create a deployment plan only, from root's immutable QR9 baseline."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];QR9=HERE.parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def main():
 p=QR9/'baseline.json';b=read(p);assert b['status']=='PASS_EXACT_QR8_CORE_SOURCE_PACKAGE_AND_INSTALLED_PH3'
 oldp=ROOT/'prealpha/phone_studios_ph3/candidate_01/install_manifest_01.json';assert sha(oldp)=='BDF7C3FF354D158541F1D2BE4429E0C25970F7DA5753EB295363075C9E47942B';old={r['path']:r for r in read(oldp)['package_files']}
 files=[]
 for r in b['core_files']:
  assert r['before']==old[r['path']]['after'];files.append({'path':r['path'],'before':r['before'],'before_bytes':old[r['path']]['bytes'],'after':r['after'],'after_bytes':r['bytes']})
 changes=[r['path'] for r in files if r['before']!=r['after']];assert len(files)==51 and set(changes)=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'}
 manifest={'schema':'PTFR_QR9_COMPONENT_V1','component':'Core','status':'PREPARED_NOT_INSTALLED','source_epoch':'QR8:02','game_root':b['game_root'],'save_root':b['save_root'],'package_root':b['package_root'],'zip':b['zip'],'zip_sha256':b['zip_sha256'],'files':files,'changing_paths':changes,'required_files':[dict(r,active_only=False) for r in b['external_dependencies']],'proofs':[{'path':str(p),'sha256':sha(p)},b['source_epoch'],b['parent_completion'],b['package_manifest'],{'path':str(oldp),'sha256':sha(oldp)}],'process_names':['Cyberpunk2077','REDprelauncher','REDlauncher'],'save_policy':'Fresh per-transaction read-only tree snapshot; never copy, restore, reset or require preparation-date save progress.','rollback_policy':'Restore only two exact managed predecessor files. File rollback is not save rollback.','fixture_override':'Only an explicit fixture root below this worker fixtures directory may use a different manifest/game/save/recovery root.'}
 out=HERE/'core_manifest_01.json';assert not out.exists();out.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');(HERE/'core_manifest_01.json.sha256').write_text(sha(out)+'\n',encoding='ascii');print({'manifest':str(out),'sha256':sha(out),'core_paths':len(files),'changes':changes,'external_dependencies':len(manifest['required_files'])})
if __name__=='__main__':main()
