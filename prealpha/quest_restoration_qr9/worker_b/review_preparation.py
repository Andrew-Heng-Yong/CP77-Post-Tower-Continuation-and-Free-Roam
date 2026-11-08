"""Source + private helper fixtures for root's read-only preparation checker; never calls its main."""
from pathlib import Path
import sys,json,hashlib,importlib.util,ast,argparse
H=Path(__file__).resolve().parent;Q=H.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();out=H/a.out
 if out.exists():raise RuntimeError('Fresh output required')
 out.mkdir(parents=True);src=Q/'check_preparation.py';before=sha(src);s=importlib.util.spec_from_file_location('b_preparation_review',src);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);checks=[];pins=[{'path':str(src),'sha256':before}]
 def ck(n,v):checks.append({'name':n,'pass':bool(v)})
 tree=ast.parse(src.read_text());calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)];text=src.read_text();imports={n.names[0].name for n in ast.walk(tree)if isinstance(n,ast.Import)}
 ck('no-CET-game-loader-GUI-or-network-import',not imports&{'ctypes','pyautogui','socket','requests'})
 ck('no-installer-import-or-invocation',not any(isinstance(n,ast.ImportFrom)and n.module and 'deploy'in n.module for n in ast.walk(tree))and 'subprocess.run(["pwsh", "-NoProfile", "-Command", process_code]'in text and not any(t in text for t in['Install-','Start-Process','Stop-Process','Remove-Item','Invoke-Expression']))
 ck('only-process-inventory-command-not-game-control','Get-Process -ErrorAction SilentlyContinue'in text and "Cyberpunk2077"in text and "REDprelauncher"in text and "REDlauncher"in text)
 ck('no-file-delete-move-replacement-or-bytes-write',not any(isinstance(n.func,ast.Attribute)and n.func.attr in('unlink','rename','replace','rmdir','write_bytes')for n in calls))
 ck('only-end-of-check-JSON-evidence-write',len([n for n in calls if isinstance(n.func,ast.Attribute)and n.func.attr=='write_text'])==1 and '(out / "result.json").write_text'in text)
 ck('fresh-contained-nonreparse-output-and-proof-before-report','out.resolve().is_relative_to(H)'in text and 'not out.exists()'in text and text.index('for p in m["proofs"]')<text.index('out.mkdir'))
 coreproofs=[]
 for name,(fn,h)in m.MANIFESTS.items():
  p=Q/'worker_a'/fn;ck('exact-pinned-component-manifest:'+name,sha(p)==h);pins.append({'path':str(p),'sha256':sha(p)});j=json.loads(p.read_text());ck('correct-component-source-version-and-process-guard:'+name,j['component']==name and j['source_epoch']=='QR8:02'and set(j['process_names'])=={'Cyberpunk2077','REDprelauncher','REDlauncher'})
  if name=='Core':coreproofs=[Path(x['path']).name for x in j['proofs']]
 ck('baseline-and-selected-master-indirectly-pinned-in-core-proofs','baseline.json'in coreproofs and 'selected_master.json'in coreproofs)
 ck('recovery-is-checked-fresh-not-created','assert not recovery.exists()'in text and 'game.drive == recovery.drive'in text and 'recovery.mkdir'not in text)
 fake=(out/'fixtures').resolve();fake.mkdir();f=fake/'sample';f.write_bytes(b'private fixture');m.check_file(f,sha(f),15);ck('actual-private-hash-and-size-helper-success',True)
 rejected=[]
 for rel in('../escape','/absolute','C:/other','a//b','a\\b','./dot'):
  try:m.child(fake,rel)
  except AssertionError:rejected.append(rel)
 ck('unsafe-relative-path-helper-controls',len(rejected)==6)
 try:m.check_file(f,None);bad=False
 except AssertionError:bad=True
 ck('unexpected-existing-absent-baseline-control',bad)
 old=sha(f);f.write_bytes(b'changed fixture')
 try:m.check_file(f,old);bad=False
 except AssertionError:bad=True
 ck('changed-byte-control-rejected',bad)
 ck('script-input-unchanged-after-helper-fixtures',sha(src)==before)
 result={'status':'APPROVE_READONLY_PREPARATION_CHECKER_SOURCE_WITH_FIXTURES'if all(x['pass']for x in checks)else'FAIL','checks':checks,'assertion_count':len(checks),'reviewed_input_pins':pins,'manual_disposition':['Script checks exact manifests and their baseline/master/proof pins, all managed/current/source/dependency bytes, absent diagnostics, fresh recovery, same volume and whole master file inventory before creating only evidence output.','Its only subprocess is fixed Get-Process inventory through pwsh -NoProfile; no installer import/invocation, GUI/game launch, process stop, save parsing or state API.','Root must supply the frozen final installer SHA after A/C gates; this review never calls main or reads real game/save bodies.','A later actual installer Preflight/Install remains separately authorized and rechecks then-current state. This script result must not be described as an actual installer invocation or successful write-permission test.','Assertions require ordinary nonoptimized Python, as the supplied invocation uses; no -O mode is approved.'],'real_installer_invocations':0,'real_game_or_save_writes':0,'actual_game_API_calls':0,'main_executed':False}
 (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],len(checks),'source/helper assertions')
 if result['status']=='FAIL':raise SystemExit(1)
if __name__=='__main__':main()
