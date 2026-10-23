"""Disposable workspace-only installer fixtures; never targets the game/saves."""
import datetime, hashlib, json, shutil, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
RUN=HERE/'fixtures'/datetime.datetime.now(datetime.UTC).strftime('%Y%m%dT%H%M%S%fZ')
RUN.mkdir(parents=True)
PWSH=shutil.which('pwsh')
assert PWSH
BASE=HERE/'build'/sys.argv[1]
RESULT=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,obj):p.write_text(json.dumps(obj,indent=2))
def fixture(name):
 p=RUN/name;build=p/'build';game=p/'game';saves=p/'saves';rec=p/'recovery'
 build.mkdir(parents=True);saves.mkdir();(game/'archive/pc/mod').mkdir(parents=True)
 (game/'r6/cache').mkdir(parents=True)
 for n in ['TowerContinued_Dogtown_DT1.archive','TowerContinued_Dogtown_DT1.archive.xl','build.json','tests.json','resource_check.json']:shutil.copy2(BASE/n,build/n)
 (game/'archive/pc/mod/keep.archive').write_bytes(b'fixture protected mod')
 (game/'r6/cache/final.redscripts').write_bytes(b'fixture protected cache')
 (saves/'sav.dat').write_bytes(b'fixture protected save, not a real game save')
 return {'p':p,'build':build,'game':game,'saves':saves,'recovery':rec}
def snapshot(f):
 return {str(p.relative_to(f['p'])):digest(p) for root in [f['p']/'game',f['p']/'saves'] for p in root.rglob('*') if p.is_file() and not p.name.startswith('TowerContinued_Dogtown_DT1')}
def invoke(f,mode,success=True,extra=(),busy=False):
 args=[str(HERE/'deploy.ps1'),'-Fixture','-Mode',mode,'-Build',str(f['build']),'-GameRoot',str(f['game']),'-SaveRoot',str(f['saves']),'-RecoveryRoot',str(f['recovery']),*extra]
 before=snapshot(f)
 if busy:
  quoted=' '.join("'"+a.replace("'","''")+"'" if not a.startswith('-') else a for a in args)
  cmd=[PWSH,'-NoProfile','-Command',"function global:Get-Process { param($Name) return [pscustomobject]@{Id=999} }; & "+quoted]
 else:cmd=[PWSH,'-NoProfile','-File',*args]
 r=subprocess.run(cmd,capture_output=True,text=True,timeout=45)
 assert (r.returncode==0)==success,(f['p'].name,mode,r.stdout,r.stderr)
 assert snapshot(f)==before,('protected data changed',f['p'].name)
 RESULT.append({'case':f['p'].name,'mode':mode,'expected_success':success,'exit':r.returncode,'output':r.stdout+r.stderr})
def repin(f):
 for name in ['tests.json','resource_check.json']:
  p=f['build']/name;o=read(p);o['build_sha256']=digest(f['build']/'build.json');write(p,o)
def change(f,edit):
 p=f['build']/'build.json';m=read(p);edit(m);write(p,m);repin(f)

f=fixture('normal');invoke(f,'Validate');invoke(f,'Install');invoke(f,'Install',False);invoke(f,'ValidateRollback');invoke(f,'Rollback');invoke(f,'Rollback',False)
assert not list((f['game']/'archive/pc/mod').glob('TowerContinued_Dogtown_DT1*'))
assert len(list(f['recovery'].glob('removed_TowerContinued_Dogtown_DT1*')))==2
f=fixture('partial');invoke(f,'Install',False,['-FailAfterFirst']);invoke(f,'ValidateRollback');invoke(f,'Rollback')
assert read(f['recovery']/'rollback_receipt.json')['moved_recoverably']==1
f=fixture('busy');invoke(f,'Install',False,busy=True);assert not f['recovery'].exists()
for name,mut in [
 ('extra_file',lambda m:m['files'].append(m['files'][0].copy())),
 ('missing_file',lambda m:m['files'].pop()),
 ('path_escape',lambda m:m['files'][0].update(relative='../outside.archive')),
 ('wrong_target',lambda m:m['files'][0].update(relative='r6/cache/final.redscripts')),
 ('duplicate_target',lambda m:m['files'][1].update(relative=m['files'][0]['relative'])),
 ('wrong_status',lambda m:m.update(status='PASS')),
 ('game_writes',lambda m:m.update(game_writes=1)),
 ('save_writes',lambda m:m.update(save_writes=1)),
 ('native_override',lambda m:m.update(official_overrides=['base/unwanted.questphase'])),
 ('extra_script',lambda m:m.update(runtime_scripts_added=1)),
 ('no_readback',lambda m:m.update(packed_readback=False)),
 ('scene_patch',lambda m:m.update(native_scenes_unchanged=False)),
 ('wrong_resource_count',lambda m:m.update(resources={})),
 ('wrong_boot_count',lambda m:m.update(boots=[])),
 ('bad_hash',lambda m:m['files'][0].update(sha256='0'*64)),
 ]:
 f=fixture(name);change(f,mut);invoke(f,'Validate',False)
for name,file,mut in [
 ('missing_tests','tests.json',None),
 ('unbound_tests','tests.json',lambda d:d.update(build_sha256='0'*64)),
 ('unbound_audit','resource_check.json',lambda d:d.update(build_sha256='0'*64)),
 ('audit_override','resource_check.json',lambda d:d.update(overrides=['unexpected'])),
 ('audit_official_override','resource_check.json',lambda d:d.update(official_overrides=['base/bad.questphase'])),
 ('audit_load_order','resource_check.json',lambda d:d.update(modlist_absent=False)),
 ('wrong_test_source','tests.json',lambda d:d.update(tester_sha256='0'*64)),
 ('wrong_audit_source','resource_check.json',lambda d:d.update(checker_sha256='0'*64)),
 ]:
 f=fixture(name);p=f['build']/file
 if mut is None:p.rename(p.with_suffix('.withheld'))
 else:o=read(p);mut(o);write(p,o)
 invoke(f,'Validate',False)
f=fixture('existing_target');(f['game']/'archive/pc/mod/TowerContinued_Dogtown_DT1.archive').write_bytes(b'never overwrite');invoke(f,'Install',False)
f=fixture('changed_package');(f['build']/'TowerContinued_Dogtown_DT1.archive').write_bytes(b'changed');invoke(f,'Validate',False)
f=fixture('recovery_reuse');f['recovery'].mkdir();invoke(f,'Install',False)
f=fixture('rollback_drift');invoke(f,'Install');target=f['game']/'archive/pc/mod/TowerContinued_Dogtown_DT1.archive.xl';target.write_bytes(b'user modification');invoke(f,'Rollback',False)
assert target.read_bytes()==b'user modification'
f=fixture('receipt_tamper');invoke(f,'Install');p=f['recovery']/'transaction.json';o=read(p);o['game_root']='C:\\';write(p,o);invoke(f,'Rollback',False)
f=fixture('receipt_scope');invoke(f,'Install');p=f['recovery']/'transaction.json';o=read(p);o['files'][0]['relative']='r6/cache/final.redscripts';write(p,o);(f['recovery']/'transaction.sha256').write_text(digest(p));invoke(f,'Rollback',False)
f=fixture('root_escape');f['saves']=RUN.parent.parent;invoke(f,'Validate',False)
f=fixture('installer_identity');invoke(f,'Install');p=f['recovery']/'transaction.json';o=read(p);o['installer_sha256']='0'*64;write(p,o);(f['recovery']/'transaction.sha256').write_text(digest(p));invoke(f,'Rollback',False)
f=fixture('junction');j=f['p']/'linked_game'
def quote(value):return "'"+str(value).replace("'","''")+"'"
jr=subprocess.run([PWSH,'-NoProfile','-Command','New-Item -ItemType Junction -Path '+quote(j)+' -Target '+quote(f['game'])+' | Out-Null'],capture_output=True,text=True)
assert jr.returncode==0,jr.stderr
f['game']=j;invoke(f,'Validate',False)
result={'status':'PASS_WORKSPACE_FIXTURES_NOT_LIVE','cases':len({r['case'] for r in RESULT}),'checks':len(RESULT),'installer_sha256':digest(HERE/'deploy.ps1'),'tester_sha256':digest(Path(__file__)),'build_sha256':digest(BASE/'build.json'),'results':RESULT}
write(RUN/'results.json',result)
print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2));print(RUN/'results.json')




