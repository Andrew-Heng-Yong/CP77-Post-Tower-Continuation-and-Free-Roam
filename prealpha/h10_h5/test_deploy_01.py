from pathlib import Path
import json,hashlib,shutil,subprocess
H=Path(__file__).resolve().parent;O=H/'candidate_01';M=json.loads((O/'install_manifest_01.json').read_text());ROOT=O/'deploy_fixtures'
PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.is_file() else None
def fixture(name):
 f=ROOT/name;f.mkdir(parents=True,exist_ok=False);game=f/'game';game.mkdir()
 for x in M['files']:
  if x['before']:
   p=game/x['target'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(O/'before'/x['target'],p)
 sentinel=game/'sentinel.txt';sentinel.write_text('unrelated fixture state')
 d=dict(M);d['game_root']=str(game);d['backup_root']=str(f/'backup');d['protected']=[{'path':str(sentinel),'sha256':sha(sentinel),'kind':'fixture'}]
 p=f/'install_manifest_01.json';p.write_text(json.dumps(d,indent=2)+'\n');Path(str(p)+'.sha256').write_text(sha(p)+'\n')
 return f,game
cases=[]
def run(f,action,success=True,extra=None):
 args=[str(PS),'-NoProfile','-File',str(H/'deploy_01.ps1'),'-Action',action,'-FixtureRoot',str(f)]
 if extra:args+=extra
 r=subprocess.run(args,capture_output=True,text=True,timeout=90)
 (f/(f'{len(cases):02}_{action}.log')).write_text(r.stdout+r.stderr)
 assert (r.returncode==0)==success,(f,action,r.stdout,r.stderr)
 cases.append({'case':f.name,'action':action,'expected_success':success,'exit_code':r.returncode})
def targets(game):return {x['target']:sha(game/x['target']) for x in M['files']}
f,g=fixture('normal');run(f,'Validate');run(f,'Install');run(f,'Verify');run(f,'ValidateRollback')
runtime=g/'user_note.txt';runtime.write_text('user snapshot evidence')
run(f,'Rollback');assert all(sha(g/x['target'])==x['before'] for x in M['files']);assert runtime.read_text()=='user snapshot evidence'
f,g=fixture('baseline_drift');p=g/M['files'][0]['target'];p.write_text('later edit');before=targets(g);run(f,'Install',False);assert targets(g)==before and not (f/'backup').exists()
f,g=fixture('protected_drift');(g/'sentinel.txt').write_text('changed');before=targets(g);run(f,'Install',False);assert targets(g)==before and not (f/'backup').exists()
f,g=fixture('interrupted_after_replacement');run(f,'Install',False,['-TestFailAfter','4']);run(f,'ValidateRollback');run(f,'Rollback');assert all(sha(g/x['target'])==x['before'] for x in M['files'])
f,g=fixture('later_target_edit');run(f,'Install');(g/M['files'][0]['target']).write_text('later owned change');before=targets(g);run(f,'Rollback',False);assert targets(g)==before
f,g=fixture('manifest_tamper');p=f/'install_manifest_01.json';p.write_text(p.read_text()+' ');before=targets(g);run(f,'Validate',False);assert targets(g)==before
f,g=fixture('relative_escape');p=f/'install_manifest_01.json';m=json.loads(p.read_text());m['files'][0]['target']='../../outside';p.write_text(json.dumps(m));Path(str(p)+'.sha256').write_text(sha(p));before=targets(g);run(f,'Install',False);assert targets(g)==before
out={'status':'PASS_REAL_INSTALLER_FIXTURES','cases':cases,'count':len(cases),'unrelated_user_file_preserved_on_rollback':True,'game_writes':0,'save_writes':0,'deployer_sha256':sha(H/'deploy_01.ps1'),'manifest_sha256':sha(O/'install_manifest_01.json')}
p=O/'deployment_tests_01.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='cases'}))
