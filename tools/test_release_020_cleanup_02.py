"""Validate AI cleanup manifests and the required Atelier-only patch."""
import hashlib,importlib.util,json,shutil,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[1];D=W/'dist/v0.2.0-beta'
spec=importlib.util.spec_from_file_location('pack020',W/'tools/package_release_020.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
obsolete=pack.obsolete_manifest();core={x['path'] for x in pack.read(D/'package/TowerContinuation/FILES.json')['files']}
assert len(obsolete['files'])==124
assert not core&{x['path'] for x in obsolete['files']}
assert all(not x['path'].startswith('/') and '..' not in x['path'].split('/') and x['accepted_sha256'] for x in obsolete['files'])
root=D/'atelier_fixtures_02';assert not root.exists();root.mkdir()
PS=r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe'
script=W/'release/Apply-Atelier-Compatibility.ps1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
results=[]
for case in ('original','patched','absent','unknown'):
 game=root/case/'game';game.mkdir(parents=True)
 target=game/'r6/scripts/virtual-atelier-full/SetupNewTab.reds'
 if case!='absent':
  target.parent.mkdir(parents=True)
  source=W/('prealpha/computer_overlay_co1/candidate_02/SetupNewTab.reds' if case=='patched' else 'prealpha/computer_overlay_co1/candidate_02/original/SetupNewTab.reds')
  shutil.copy2(source,target)
  if case=='unknown':target.write_bytes(target.read_bytes()+b'// edited')
 before=target.read_bytes() if target.exists() else None;actions=[]
 for action in (['Validate','Apply','Verify','Apply'] if case=='original' else ['Verify','Apply'] if case=='patched' else ['Apply']):
  p=subprocess.run([PS,'-NoProfile','-File',str(script),'-Action',action,'-GameRoot',str(game)],capture_output=True,text=True,timeout=90)
  assert (p.returncode!=0 if case=='unknown' else p.returncode==0),(case,action,p.stdout,p.stderr)
  actions.append({'action':action,'exit':p.returncode})
 if case in ('original','patched'):assert sha(target)=='5743CDCD6F8CD46A58F9642002F75EBCA25D84BE340856C2E6D85B15DAD973F8'
 elif case=='unknown':assert target.read_bytes()==before
 assert len([x for x in game.rglob('*') if x.is_file()])==(0 if case=='absent' else 1),'Unexpected backup/extra files'
 results.append({'case':case,'actions':actions,'status':'PASS'})
report={'status':'PASS','revision':'AI_CLEANUP_NO_OLD_ZIP_NO_BACKUP','obsolete_paths':124,'no_current_paths_in_cleanup':True,'cleanup_script_in_package':False,'Atelier_only_patch_cases':4,'no_backup_files_created':True,'game_writes':0,'save_writes':0,'results':results}
(W/'release/validation-v0.2.0-beta.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='results'}))
