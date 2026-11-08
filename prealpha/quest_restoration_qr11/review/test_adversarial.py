"""Independent bounded QR11 fixture cases; no real game/save/install action."""
from pathlib import Path
import copy,hashlib,json,subprocess
H=Path(__file__).resolve().parent;Q=H.parent
PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
SCRIPT=Q/'deploy_diagnostics.ps1'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def snap(root):return{p.relative_to(root).as_posix():sha(p)for p in root.rglob('*')if p.is_file()}

def main():
 run=Q/'fixtures/review_02';assert not run.exists();run.mkdir()
 assert run.resolve().is_relative_to((Q/'fixtures').resolve())
 script_hash=sha(SCRIPT);base=json.loads((Q/'diagnostics_manifest_01.json').read_text());commands=[];checks=[]
 def make(name):
  r=run/name;r.mkdir();m=copy.deepcopy(base)
  m.update(game_root=str(r/'game'),save_root=str(r/'saves'),package_root=str(r/'package'))
  proof=r/'proof.txt';put(proof,b'KNOWN_REVIEW_PROOF');m['proofs']=[{'path':str(proof),'sha256':sha(proof)}]
  for row in m['files']:
   old=Q.parent/'quest_restoration_qr9/worker_b/addon'/row['path']
   put(r/'game'/row['path'],old.read_bytes());put(r/'package'/row['path'],(Path(base['package_root'])/row['path']).read_bytes())
  for row in m['required_files']:
   p=r/'game'/row['path'];put(p,('SYNTHETIC_REVIEW_DEP:'+row['path']).encode());row['sha256']=sha(p);row['bytes']=p.stat().st_size
  for row in m['protected_saves']+m['working_save_files']:
   p=r/'saves'/row['path'];put(p,('SYNTHETIC_REVIEW_SAVE:'+row['path']).encode());row['sha256']=sha(p);row['bytes']=p.stat().st_size
  put(r/'game/unknown_mod/keep.log',b'IMMUTABLE_UNKNOWN_MOD')
  mp=r/'manifest.json';mp.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
  return r,m
 def call(r,action,extra=(),ok=True):
  cmd=[str(PS),'-NoProfile','-File',str(SCRIPT),'-Action',action,'-FixtureRoot',str(r),'-FixtureManifest',str(r/'manifest.json'),'-FixtureManifestSHA',sha(r/'manifest.json'),*extra]
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=40,creationflags=subprocess.CREATE_NO_WINDOW)
  commands.append({'case':r.name,'action':action,'extra':list(extra),'exit_code':p.returncode,'stdout':p.stdout[-1200:],'stderr':p.stderr[-1800:]})
  assert (p.returncode==0)==ok,(action,p.stdout,p.stderr)
 r,m=make('changed_working_save');call(r,'Install')
 for row in m['working_save_files']:put(r/'saves'/row['path'],('LEGITIMATE_LATER_PLAY:'+row['path']).encode())
 saves=snap(r/'saves');unmanaged=(r/'game/unknown_mod/keep.log').read_bytes()
 call(r,'Verify');checks.append('Verify accepts later changed working24 while retaining pinned master23')
 call(r,'ValidateRollback');checks.append('rollback preflight accepts later changed working24')
 call(r,'Rollback');call(r,'Verify',('-ExpectedState','Before'))
 assert snap(r/'saves')==saves;checks.append('rollback preserves every later changed working24 byte and master23')
 assert all(sha(r/'game'/row['path'])==row['before']for row in m['files']);checks.append('rollback restores actual exact B04 diagnostic leaves')
 assert (r/'game/unknown_mod/keep.log').read_bytes()==unmanaged;checks.append('unmanaged game file preserved')
 r,m=make('proof_drift');put(r/'proof.txt',b'UNKNOWN_PROOF_CHANGE');before=(snap(r/'game'),snap(r/'saves'))
 call(r,'Install',ok=False)
 assert (snap(r/'game'),snap(r/'saves'))==before and not(r/'recovery').exists();checks.append('proof hash drift refuses before journal or game/save mutation')
 r,m=make('broken_report_link');link=r/'report_link.json';target=r/'never_create_unknown_report.json';link.symlink_to(target)
 before=(snap(r/'game'),snap(r/'saves'))
 call(r,'Preflight',('-ReportFile',str(link)),ok=False)
 assert link.is_symlink()and not target.exists()and(snap(r/'game'),snap(r/'saves'))==before
 checks.append('optimized ancestor guard refuses broken report link without creating its target')
 assert sha(SCRIPT)==script_hash;checks.append('review exercised one exact unchanged installer source')
 result={'status':'PASS_INDEPENDENT_BOUNDED_DEPLOYMENT_FIXTURES','installer_sha256':script_hash,
  'manifest_sha256':sha(Q/'diagnostics_manifest_01.json'),'checks':checks,'commands':commands,
  'real_game_mutations':0,'game_launches':0,'save_writes':'Synthetic fixture save bytes only; no real save read or write',
  'limits':'Actual diagnostic payload bytes, synthetic dependencies and saves; no real deployment, access-right check, engine dispatch or gameplay proof.'}
 dest=H/'adversarial_results_02.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print({'status':result['status'],'checks':len(checks),'commands':len(commands),'installer_sha256':script_hash})

if __name__=='__main__':main()
