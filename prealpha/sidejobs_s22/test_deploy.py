"""Workspace-only S22 mixed-install/rollback fixtures. Never targets live game."""
import datetime,hashlib,json,shutil,subprocess,sys,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
BASE=Path(sys.argv[1]).resolve();assert BASE.is_relative_to(HERE/'build')
RUN=HERE/'fixtures'/datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%S%fZ');RUN.mkdir(parents=True)
OLD=ROOT/'prealpha/sidejobs_s21/build/s21_03/SideJobsS2.reds'
RELS=[Path('archive/pc/mod/000_TowerContinued_SideJobs_S22.archive'),Path('archive/pc/mod/000_TowerContinued_SideJobs_S22.archive.xl'),Path('r6/scripts/TowerContinued_SideJobs_S22/SideJobsS22.reds'),Path('r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds')]
PWSH=shutil.which('pwsh');assert PWSH
RESULT=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8')
def fixture(name):
 p=RUN/name;build=p/'build';game=p/'game';saves=p/'saves';rec=p/'recovery'
 build.mkdir(parents=True);saves.mkdir();(game/RELS[3]).parent.mkdir(parents=True)
 (game/'archive/pc/mod').mkdir(parents=True);(game/'r6/cache').mkdir()
 for n in [r.name for r in RELS]+['build.json','tests.json','compile_result.json','resource_check.json']:shutil.copy2(BASE/n,build/n)
 shutil.copy2(OLD,game/RELS[3]);(game/'archive/pc/mod/keep.archive').write_bytes(b'protected fixture mod')
 (game/'r6/cache/final.redscripts').write_bytes(b'protected fixture cache');(saves/'sav.dat').write_bytes(b'fixture save; not actual game data')
 return dict(p=p,build=build,game=game,saves=saves,recovery=rec)
def snapshot(f):
 return {str(p.relative_to(f['p'])):digest(p) for root in [f['p']/'game',f['p']/'saves'] for p in root.rglob('*') if p.is_file() and p not in [f['p']/'game'/r for r in RELS]}
def targets(f):return {str(r):digest(f['game']/r) if (f['game']/r).is_file() else None for r in RELS}
def invoke(f,mode,success=True,extra=(),busy=False,target_may_change=False):
 args=[str(HERE/'deploy.ps1'),'-Fixture','-Mode',mode,'-Build',str(f['build']),'-GameRoot',str(f['game']),'-SaveRoot',str(f['saves']),'-RecoveryRoot',str(f['recovery']),*extra]
 before=snapshot(f);old=targets(f)
 if busy:
  quoted=' '.join("'"+a.replace("'","''")+"'" if not a.startswith('-') else a for a in args)
  cmd=[PWSH,'-NoProfile','-Command',"function global:Get-Process { param($Name) return [pscustomobject]@{Id=999} }; & "+quoted]
 else:cmd=[PWSH,'-NoProfile','-File',*args]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
 RESULT.append(dict(case=f['p'].name,mode=mode,expected_success=success,exit=r.returncode,output=r.stdout+r.stderr))
 assert (r.returncode==0)==success,(f['p'].name,mode,r.stdout,r.stderr)
 assert snapshot(f)==before,('protected drift',f['p'].name)
 if mode.startswith('Validate') or (not success and not target_may_change):assert targets(f)==old,('refusal changed targets',f['p'].name)
def repin(f):
 for n in ['tests.json','compile_result.json','resource_check.json']:
  p=f['build']/n;o=read(p);o['build_sha256']=digest(f['build']/'build.json');write(p,o)
def change(f,mut):
 p=f['build']/'build.json';o=read(p);mut(o);write(p,o);repin(f)
def txnchange(f,mut,repin_hash=True):
 p=f['recovery']/'transaction.json';o=read(p);mut(o);write(p,o)
 if repin_hash:(f['recovery']/'transaction.sha256').write_text(digest(p))
def rolled_back(f):
 assert digest(f['game']/RELS[3])==digest(OLD)
 assert all(not (f['game']/r).exists() for r in RELS[:3])
def run():
 f=fixture('normal');invoke(f,'Validate');invoke(f,'Install')
 assert all(digest(f['game']/r)==digest(BASE/r.name) for r in RELS)
 assert digest(f['recovery']/'before_SideJobsS2.reds')==digest(OLD)==digest(f['recovery']/'displaced.reds')
 invoke(f,'Install',False);invoke(f,'ValidateRollback');invoke(f,'Rollback');invoke(f,'Rollback',False);rolled_back(f)
 assert digest(f['recovery']/'rollback_displaced.reds')==digest(BASE/'SideJobsS2.reds')
 for flag in ['-FailAfterBackup','-FailAfterFirst','-FailAfterReplace']:
  f=fixture('partial'+flag);invoke(f,'Install',False,[flag],target_may_change=True);invoke(f,'ValidateRollback');invoke(f,'Rollback');rolled_back(f)
 f=fixture('busy');invoke(f,'Install',False,busy=True);assert not f['recovery'].exists()
 for name,mut in [
  ('wrong_status',lambda m:m.update(status='PASS')),
  ('path_escape',lambda m:m['files'][0].update(relative='../outside.archive')),
  ('wrong_target',lambda m:m['files'][3].update(relative='r6/cache/final.redscripts')),
  ('wrong_old',lambda m:m['files'][3].update(old_sha256='0'*64)),
  ('wrong_new',lambda m:m['files'][3].update(sha256='0'*64)),
  ('same_version',lambda m:m['files'][3].update(sha256=m['files'][3]['old_sha256'])),
  ('short_files',lambda m:m['files'].pop()),
  ('extra_file',lambda m:m['files'].append(m['files'][0])),
  ('duplicate_file',lambda m:m['files'][1].update(relative=m['files'][0]['relative'])),
  ('unordered',lambda m:m['files'].reverse()),
  ('addition_replace',lambda m:m['files'][0].update(old_sha256='0'*64)),
  ('not_packed',lambda m:m.update(packed_readback=False)),
  ('no_resources',lambda m:m.update(resources={})),
  ('no_boots',lambda m:m.update(boots=[])),
  ('no_pins',lambda m:m.update(source_pins={})),
  ('source_pin_drift',lambda m:m.update(source_pins={'prealpha/sidejobs_s22/deploy.ps1':'0'*64})),
 ]:
  f=fixture(name);change(f,mut);invoke(f,'Validate',False)
 for name,file,mut in [
  ('missing_tests','tests.json',None),('missing_compile','compile_result.json',None),('missing_resources','resource_check.json',None),
  ('unbound_tests','tests.json',lambda o:o.update(build_sha256='0'*64)),
  ('weak_tests','tests.json',lambda o:o.update(policy_cases=0)),
  ('weak_native','tests.json',lambda o:o.update(native_payload_checks=0)),
  ('wrong_tester','tests.json',lambda o:o.update(tester_sha256='0'*64)),
  ('unbound_compile','compile_result.json',lambda o:o.update(build_sha256='0'*64)),
  ('wrong_compiler','compile_result.json',lambda o:o.update(compiler_sha256='0'*64)),
  ('no_full_scc','compile_result.json',lambda o:o.update(full_scc=False)),
  ('no_cli','compile_result.json',lambda o:o.update(combined_cli=False)),
  ('no_equipmentex','compile_result.json',lambda o:o.update(equipmentex=False)),
  ('no_body_readback','compile_result.json',lambda o:o.update(body_readback=False)),
  ('changed_live','compile_result.json',lambda o:o.update(live_files_unchanged=False)),
  ('unbound_resources','resource_check.json',lambda o:o.update(build_sha256='0'*64)),
  ('wrong_checker','resource_check.json',lambda o:o.update(checker_sha256='0'*64)),
  ('weak_resource_proof','resource_check.json',lambda o:o.update(official_comparisons=0)),
  ('unexpected_collision','resource_check.json',lambda o:o.update(collisions=[{'depot':'base\\quest\\unrelated.questphase'}])),
  ('official_override','resource_check.json',lambda o:o.update(official_overrides=['base\\quest\\unrelated.questphase'])),
  ('modlist_present','resource_check.json',lambda o:o.update(modlist_absent=False)),
 ]:
  f=fixture(name);p=f['build']/file
  if mut is None:p.rename(p.with_suffix('.withheld'))
  else:o=read(p);mut(o);write(p,o)
  invoke(f,'Validate',False)
 for i in range(4):
  f=fixture('source_drift_'+str(i));(f['build']/RELS[i].name).write_bytes(b'changed source');invoke(f,'Install',False)
 f=fixture('target_drift');(f['game']/RELS[3]).write_bytes(b'user changes');invoke(f,'Install',False)
 f=fixture('target_missing');(f['game']/RELS[3]).rename((f['game']/RELS[3]).with_suffix('.withheld'));invoke(f,'Install',False)
 for i in range(3):
  f=fixture('addition_exists_'+str(i));p=f['game']/RELS[i];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'user file');invoke(f,'Install',False)
 f=fixture('recovery_reuse');f['recovery'].mkdir();invoke(f,'Install',False)
 for i in range(4):
  f=fixture('rollback_target_drift_'+str(i));invoke(f,'Install');(f['game']/RELS[i]).write_bytes(b'user changes after install');invoke(f,'Rollback',False)
 f=fixture('rollback_missing_replacement');invoke(f,'Install');(f['game']/RELS[3]).rename((f['game']/RELS[3]).with_suffix('.withheld'));invoke(f,'Rollback',False)
 f=fixture('bad_backup');invoke(f,'Install');(f['recovery']/'before_SideJobsS2.reds').write_bytes(b'bad backup');invoke(f,'Rollback',False)
 f=fixture('bad_staged');invoke(f,'Install');(f['recovery']/'SideJobsS22.reds').write_bytes(b'bad staged');invoke(f,'Rollback',False)
 f=fixture('txn_tamper');invoke(f,'Install');txnchange(f,lambda o:o.update(game_root='C:\\'),False);invoke(f,'Rollback',False)
 for name,mut in [('txn_scope',lambda o:o['files'][0].update(relative='r6/cache/final.redscripts')),('txn_old',lambda o:o['files'][3].update(old_sha256='0'*64)),('txn_status',lambda o:o.update(status='PASS')),('txn_game',lambda o:o.update(game_root='C:\\')),('txn_save',lambda o:o.update(save_root='C:\\'))]:
  f=fixture(name);invoke(f,'Install');txnchange(f,mut);invoke(f,'Rollback',False)
 f=fixture('root_escape');f['saves']=RUN.parent.parent;invoke(f,'Validate',False)
 for case,which in [('junction_game','game'),('junction_recovery','recovery'),('junction_source','build')]:
  f=fixture(case);link=f['p']/('linked_'+which);dest=f[which]
  if which=='recovery':dest.mkdir()
  cmd=f"New-Item -ItemType Junction -Path '{str(link).replace(chr(39),chr(39)*2)}' -Target '{str(dest).replace(chr(39),chr(39)*2)}' | Out-Null"
  r=subprocess.run([PWSH,'-NoProfile','-Command',cmd],capture_output=True,text=True);assert r.returncode==0,r.stderr
  f[which]=link;invoke(f,'Validate' if which!='recovery' else 'Install',False)
try:
 run()
 result={'status':'PASS_WORKSPACE_FIXTURES_NOT_LIVE','cases':len({r['case'] for r in RESULT}),'checks':len(RESULT),'installer_sha256':digest(HERE/'deploy.ps1'),'tester_sha256':digest(Path(__file__)),'build_sha256':digest(BASE/'build.json'),'results':RESULT}
 write(RUN/'results.json',result);print(json.dumps({k:v for k,v in result.items() if k!='results'}))
except BaseException:
 write(RUN/'failure.json',{'status':'FIXTURE_FAILURE','traceback':traceback.format_exc(),'results':RESULT});raise
