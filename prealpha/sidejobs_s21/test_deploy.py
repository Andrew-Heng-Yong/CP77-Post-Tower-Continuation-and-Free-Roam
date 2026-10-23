"""Workspace-only replacement/rollback fixtures. Never targets actual game/saves."""
import datetime, hashlib, json, shutil, subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
RUN=HERE/'fixtures'/datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%S%fZ')
RUN.mkdir(parents=True)
BASE=HERE/'build/s21_03'
OLD=ROOT/'prealpha/sidejobs_s2/build/s2_02/SideJobsS2.reds'
REL=Path('r6/scripts/TowerContinued_SideJobs_S2/SideJobsS2.reds')
PWSH=shutil.which('pwsh');assert PWSH
RESULT=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,o):p.write_text(json.dumps(o,indent=2),encoding='utf-8')
def fixture(name):
 p=RUN/name;build=p/'build';game=p/'game';saves=p/'saves';rec=p/'recovery'
 build.mkdir(parents=True);saves.mkdir();(game/REL).parent.mkdir(parents=True)
 (game/'archive/pc/mod').mkdir(parents=True);(game/'r6/cache').mkdir()
 for n in ['SideJobsS2.reds','build.json','tests.json','compile_result.json']:shutil.copy2(BASE/n,build/n)
 shutil.copy2(OLD,game/REL)
 (game/'archive/pc/mod/keep.archive').write_bytes(b'protected fixture mod')
 (game/'r6/cache/final.redscripts').write_bytes(b'protected fixture cache')
 (saves/'sav.dat').write_bytes(b'protected fixture save, not a game save')
 return {'p':p,'build':build,'game':game,'saves':saves,'recovery':rec}
def snapshot(f):
 return {str(p.relative_to(f['p'])):digest(p) for root in [f['p']/'game',f['p']/'saves'] for p in root.rglob('*') if p.is_file() and p!=f['p']/'game'/REL}
def invoke(f,mode,success=True,extra=(),busy=False,target_may_change=False):
 args=[str(HERE/'deploy.ps1'),'-Fixture','-Mode',mode,'-Build',str(f['build']),'-GameRoot',str(f['game']),'-SaveRoot',str(f['saves']),'-RecoveryRoot',str(f['recovery']),*extra]
 before=snapshot(f);target=f['p']/'game'/REL;target_before=digest(target) if target.exists() else None
 if busy:
  quoted=' '.join("'"+a.replace("'","''")+"'" if not a.startswith('-') else a for a in args)
  cmd=[PWSH,'-NoProfile','-Command',"function global:Get-Process { param($Name) return [pscustomobject]@{Id=999} }; & "+quoted]
 else:cmd=[PWSH,'-NoProfile','-File',*args]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
 assert (r.returncode==0)==success,(f['p'].name,mode,r.stdout,r.stderr)
 assert snapshot(f)==before,('protected drift',f['p'].name)
 if mode.startswith('Validate') or not success and not target_may_change:
  assert (digest(target) if target.exists() else None)==target_before,('refusal changed target',f['p'].name)
 RESULT.append({'case':f['p'].name,'mode':mode,'expected_success':success,'exit':r.returncode,'output':r.stdout+r.stderr})
def repin(f):
 for n in ['tests.json','compile_result.json']:
  p=f['build']/n;o=read(p);o['build_sha256']=digest(f['build']/'build.json');write(p,o)
def change(f,mut):
 p=f['build']/'build.json';o=read(p);mut(o);write(p,o);repin(f)
def txnchange(f,mut,repin_hash=True):
 p=f['recovery']/'transaction.json';o=read(p);mut(o);write(p,o)
 if repin_hash:(f['recovery']/'transaction.sha256').write_text(digest(p))

f=fixture('normal');invoke(f,'Validate');invoke(f,'Install');assert digest(f['game']/REL)==digest(BASE/'SideJobsS2.reds')
assert digest(f['recovery']/'before.reds')==digest(OLD)==digest(f['recovery']/'displaced.reds')
invoke(f,'Install',False);invoke(f,'ValidateRollback');invoke(f,'Rollback');invoke(f,'Rollback',False)
assert digest(f['game']/REL)==digest(OLD) and digest(f['recovery']/'rollback_displaced.reds')==digest(BASE/'SideJobsS2.reds')
for name,flag in [('partial_backup','-FailAfterBackup'),('partial_replace','-FailAfterReplace')]:
 f=fixture(name);invoke(f,'Install',False,[flag],target_may_change=name=='partial_replace');invoke(f,'ValidateRollback');invoke(f,'Rollback');assert digest(f['game']/REL)==digest(OLD)
f=fixture('busy');invoke(f,'Install',False,busy=True);assert not f['recovery'].exists()
for name,mut in [
 ('wrong_status',lambda m:m.update(status='PASS')),
 ('path_escape',lambda m:m.update(relative='../outside.reds')),
 ('wrong_target',lambda m:m.update(relative='r6/cache/final.redscripts')),
 ('wrong_old',lambda m:m.update(old_sha256='0'*64)),
 ('wrong_new',lambda m:m.update(sha256='0'*64)),
 ('same_version',lambda m:m.update(sha256=m['old_sha256'])),
 ('wrong_count',lambda m:m.update(runtime_replacements=2)),
 ('extra_file',lambda m:m.update(additions=1)),
 ('archive_change',lambda m:m.update(archives_changed=1)),
 ('owner_change',lambda m:m.update(owners_changed=1)),
 ('supplement_change',lambda m:m.update(native_guards_unchanged=False)),
 ('table_change',lambda m:m.update(generated_table_unchanged=False)),
 ('wrong_dataset',lambda m:m['dataset'].pop()),
]:
 f=fixture(name);change(f,mut);invoke(f,'Validate',False)
for name,file,mut in [
 ('missing_tests','tests.json',None),
 ('missing_compile','compile_result.json',None),
 ('unbound_tests','tests.json',lambda o:o.update(build_sha256='0'*64)),
 ('weak_tests','tests.json',lambda o:o.update(policy_cases=1)),
 ('wrong_tester','tests.json',lambda o:o.update(tester_sha256='0'*64)),
 ('wrong_policy_tester','tests.json',lambda o:o.update(policy_tester_sha256='0'*64)),
 ('table_unverified','tests.json',lambda o:o.update(generated_table_unchanged=False)),
 ('owners_unverified','tests.json',lambda o:o.update(owners_unchanged=False)),
 ('unbound_compile','compile_result.json',lambda o:o.update(build_sha256='0'*64)),
 ('wrong_compiler','compile_result.json',lambda o:o.update(compiler_sha256='0'*64)),
 ('wrong_compiled_source','compile_result.json',lambda o:o.update(script_sha256='0'*64)),
 ('no_full_scc','compile_result.json',lambda o:o.update(full_scc=False)),
 ('no_cli','compile_result.json',lambda o:o.update(combined_cli=False)),
 ('no_equipmentex','compile_result.json',lambda o:o.update(equipmentex=False)),
 ('no_body_readback','compile_result.json',lambda o:o.update(body_readback=False)),
 ('changed_live','compile_result.json',lambda o:o.update(live_files_unchanged=False)),
]:
 f=fixture(name);p=f['build']/file
 if mut is None:p.rename(p.with_suffix('.withheld'))
 else:o=read(p);mut(o);write(p,o)
 invoke(f,'Validate',False)
f=fixture('target_drift');(f['game']/REL).write_bytes(b'user changes');invoke(f,'Install',False)
f=fixture('target_missing');(f['game']/REL).rename((f['game']/REL).with_suffix('.withheld'));invoke(f,'Install',False)
f=fixture('source_drift');(f['build']/'SideJobsS2.reds').write_bytes(b'changed source');invoke(f,'Install',False)
f=fixture('recovery_reuse');f['recovery'].mkdir();invoke(f,'Install',False)
f=fixture('rollback_drift');invoke(f,'Install');(f['game']/REL).write_bytes(b'user changes after install');invoke(f,'Rollback',False)
f=fixture('rollback_missing');invoke(f,'Install');(f['game']/REL).rename((f['game']/REL).with_suffix('.withheld'));invoke(f,'Rollback',False)
f=fixture('bad_backup');invoke(f,'Install');(f['recovery']/'before.reds').write_bytes(b'bad backup');invoke(f,'Rollback',False)
f=fixture('bad_staged');invoke(f,'Install');(f['recovery']/'after.reds').write_bytes(b'bad staged');invoke(f,'Rollback',False)
f=fixture('txn_tamper');invoke(f,'Install');txnchange(f,lambda o:o.update(game_root='C:\\'),False);invoke(f,'Rollback',False)
for name,mut in [('txn_scope',lambda o:o.update(relative='r6/cache/final.redscripts')),('txn_old',lambda o:o.update(old_sha256='0'*64)),('txn_status',lambda o:o.update(status='PASS'))]:
 f=fixture(name);invoke(f,'Install');txnchange(f,mut);invoke(f,'Rollback',False)
f=fixture('root_escape');f['saves']=RUN.parent.parent;invoke(f,'Validate',False)
f=fixture('junction_game');link=f['p']/'linked_game'
cmd=f"New-Item -ItemType Junction -Path '{str(link).replace(chr(39),chr(39)*2)}' -Target '{str(f['game']).replace(chr(39),chr(39)*2)}' | Out-Null"
r=subprocess.run([PWSH,'-NoProfile','-Command',cmd],capture_output=True,text=True);assert r.returncode==0,r.stderr
f['game']=link;invoke(f,'Validate',False)
result={'status':'PASS_WORKSPACE_FIXTURES_NOT_LIVE','cases':len({r['case'] for r in RESULT}),'checks':len(RESULT),'installer_sha256':digest(HERE/'deploy.ps1'),'tester_sha256':digest(Path(__file__)),'build_sha256':digest(BASE/'build.json'),'results':RESULT}
write(RUN/'results.json',result);print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2));print(RUN/'results.json')
