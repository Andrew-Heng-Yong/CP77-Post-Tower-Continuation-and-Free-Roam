"""Workspace-only transaction fixtures. Never invokes a real game action."""
from pathlib import Path
import hashlib,json,subprocess,shutil,concurrent.futures
HERE=Path(__file__).resolve().parent;SUITE=HERE/'fixtures/suite_02';SCRIPT=HERE/'deploy_qr9.ps1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def tree(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def writejson(p,d):p.write_text(json.dumps(d,indent=2),encoding='utf8')
def fixture(name,component='Core'):
 root=SUITE/name;root.mkdir(parents=True);game=root/'game';save=root/'saves';package=root/'package';game.mkdir();save.mkdir();package.mkdir()
 files=[];real=json.loads((HERE/'core_manifest_02.json').read_text())
 paths=[r['path'] for r in real['files']] if component=='Core' else ['bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json']
 for i,p in enumerate(paths):
  changing=component=='Diagnostics' or p in real['changing_paths'];before=(('before:'+p).encode() if changing else ('same:'+p).encode()) if component=='Core' else None;after=('after:'+p).encode() if changing else before
  if before is not None:put(game/p,before)
  put(package/p,after);files.append({'path':p,'before':hashlib.sha256(before).hexdigest().upper() if before is not None else None,'before_bytes':len(before) if before is not None else 0,'after':sha(package/p),'after_bytes':len(after)})
 dep='external/RequiredMod.bin';put(game/dep,b'EXTERNAL_REQUIRED_UNCHANGED');put(game/'unmanaged/user.ini',b'EXTERNAL_USER_CONFIG')
 put(save/'OtherSave/sav.dat',b'OTHER_ORIGINAL_SAVE');master={}
 for name in ['metadata.9.json','sav.dat','screenshot.png']:
  p=save/'ManualSave-23'/name;put(p,('MASTER:'+name).encode());master[name]={'sha256':sha(p),'bytes':p.stat().st_size}
 proof=root/'proof.json';writejson(proof,{'fixture_only':True})
 m={'schema':'PTFR_QR9_COMPONENT_V1','component':component,'source_epoch':'QR8:02','game_root':'REAL_ROOT_IGNORED_IN_FIXTURES','save_root':'REAL_SAVE_ROOT_IGNORED_IN_FIXTURES','package_root':str(package),'zip':'','zip_sha256':None,'files':files,'changing_paths':[r['path']for r in files if r['before']!=r['after']],'required_files':[{'path':dep,'sha256':sha(game/dep),'bytes':(game/dep).stat().st_size,'active_only':False}],'proofs':[{'path':str(proof),'sha256':sha(proof)}],'process_names':['Cyberpunk2077','REDprelauncher','REDlauncher'],'master_backup':{'slot':'ManualSave-23','files':master}}
 manifest=root/'manifest.json';writejson(manifest,m)
 return {'root':root,'game':game,'save':save,'package':package,'manifest':manifest,'data':m,'component':component,'before':tree(game),'saves_before':tree(save)}
def run(f,action,fail='',backup=False,state='After',process=None,okay=True,extra=None):
 args=['pwsh','-NoProfile','-File',str(SCRIPT),'-Component',f['component'],'-Action',action,'-FixtureRoot',str(f['root']),'-FixtureManifest',str(f['manifest']),'-FixtureManifestSHA',sha(f['manifest']),'-ExpectedState',state]
 if fail:args+=['-FailurePoint',fail]
 if backup:args+=['-BackupMaster']
 if process:args+=['-FixtureProcesses',process]
 if extra:args+=extra
 r=subprocess.run(args,text=True,capture_output=True);(f['root']/(action+'_'+str(len(list(f['root'].glob('*.stdout'))))+'.stdout')).write_text(r.stdout+'\nSTDERR\n'+r.stderr,encoding='utf8')
 if okay is not None:assert (r.returncode==0)==okay,(f['root'].name,action,fail,r.returncode,r.stdout,r.stderr)
 return r
def journal(f):return json.loads(json.loads((f['root']/'recovery'/f['component'].lower()/'journal.json').read_text())['payload_json'])
def after(f):return {r['path'].replace('/','\\'):r['after'] for r in f['data']['files']}
def assert_state(f,state):
 for r in f['data']['files']:
  p=f['game']/r['path'];h=r['before'] if state=='Before' else r['after'];assert (sha(p) if p.exists() else None)==h,(p,state)
def clean(name,component='Core',master=False):
 f=fixture(name,component);run(f,'Preflight',backup=master);assert not(f['root']/'recovery').exists();run(f,'Install',backup=master);assert_state(f,'After');run(f,'Verify');run(f,'ValidateRollback');assert tree(f['save'])==f['saves_before']
 if master:
  for n in f['data']['master_backup']['files']:assert sha(f['root']/'recovery/core/master_before/ManualSave-23'/n)==sha(f['save']/'ManualSave-23'/n)
 put(f['save']/'ManualSave-working/sav.dat',b'GENUINE_LATER_USER_PROGRESS_FIXTURE');current=tree(f['save'])
 if component=='Diagnostics':put(f['game']/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/QR9_capture_LATER.jsonl',b'USER_RUNTIME_LOG_RETAIN')
 run(f,'Rollback');assert_state(f,'Before');run(f,'Verify',state='Before');assert tree(f['save'])==current
 if component=='Diagnostics':assert (f['game']/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/QR9_capture_LATER.jsonl').read_bytes()==b'USER_RUNTIME_LOG_RETAIN'
 return {'case':name,'status':'PASS','game_writes':'workspace fixture only','save_writes_by_installer':0}
def interrupted(name,point,rollback=False):
 f=fixture(name);run(f,'Preflight')
 if rollback:run(f,'Install');result=run(f,'Rollback',fail=point,okay=False)
 else:result=run(f,'Install',fail=point,okay=False)
 if point.startswith('Crash'):assert result.returncode==72,(point,'did not reach hard interruption',result.stderr)
 elif point=='GameStartsAfterFirstReplace':assert 'Fixture game-start interruption' in result.stderr
 else:assert ('Fixture interruption: '+point) in result.stderr,(point,'failed before intended injection',result.stderr)
 if point.startswith('Crash') or point=='GameStartsAfterFirstReplace':run(f,'Recover')
 expected='After' if rollback else 'Before';assert_state(f,expected);assert tree(f['save'])==f['saves_before']
 assert not list((f['root']/'recovery/core/stage').rglob('*.*')) if (f['root']/'recovery/core/stage').exists() else True
 return {'case':name,'status':'PASS','interruption':point,'consistent_state':expected}
def blocked(name,kind):
 f=fixture(name)
 if kind in ['rollback_target','backup','journal','master_changed']:run(f,'Install',backup=(kind=='master_changed'))
 if kind=='before':put(f['game']/f['data']['files'][0]['path'],b'UNKNOWN_USER_CORE_BYTES')
 elif kind=='package':put(f['package']/f['data']['files'][0]['path'],b'UNREVIEWED_SOURCE')
 elif kind=='extra_package':put(f['package']/'extra_unknown.txt',b'UNLISTED_PACKAGE_FILE')
 elif kind=='external':put(f['game']/f['data']['required_files'][0]['path'],b'NEW_EXTERNAL_VERSION')
 elif kind=='occupied':(f['root']/'recovery/core').mkdir(parents=True);put(f['root']/'recovery/core/user.txt',b'UNKNOWN_RECOVERY_DATA')
 elif kind=='rollback_target':put(f['game']/f['data']['files'][-1]['path'],b'UNKNOWN_AFTER_USER_EDIT')
 elif kind=='backup':put(f['root']/'recovery/core/old'/f['data']['files'][0]['path'],b'CORRUPT_BACKUP')
 elif kind=='journal':put(f['root']/'recovery/core/journal.json',b'{partial')
 elif kind=='master_changed':put(f['save']/'ManualSave-23/sav.dat',b'USER_OVERWROTE_MASTER_STOP_DO_NOT_RESTORE')
 elif kind=='traversal':f['data']['files'][0]['path']='../outside.bin';writejson(f['manifest'],f['data'])
 before=tree(f['game']);saves=tree(f['save'])
 action='ValidateRollback' if kind in ['rollback_target','backup','master_changed'] else 'Recover' if kind=='journal' else 'Preflight'
 run(f,action,okay=False);assert tree(f['game'])==before and tree(f['save'])==saves
 return {'case':name,'status':'PASS','blocked':kind,'unknown_bytes_preserved':True}
def process_case(name,process):
 f=fixture(name);r=run(f,'Preflight',process=process,okay=False);assert 'Game or REDlauncher must be closed naturally' in r.stderr and process in r.stderr;assert tree(f['game'])==f['before'];return {'case':name,'status':'PASS','blocked_process':process}
def drift_case(name,point):
 f=fixture(name);run(f,'Install',fail=point,okay=False)
 if point=='TargetDriftAfterFirstReplace':
  p=f['game']/f['data']['files'][0]['path'];assert p.read_bytes()==b'FIXTURE_UNKNOWN_CHANGED_BYTES';run(f,'Recover',okay=False);put(p,(f['package']/f['data']['files'][0]['path']).read_bytes())
 elif point=='ExternalChangesAfterFirstReplace':
  p=f['game']/f['data']['required_files'][0]['path'];assert p.read_bytes()==b'FIXTURE_EXTERNAL_MOD_CHANGE';run(f,'Recover',okay=False);put(p,b'EXTERNAL_REQUIRED_UNCHANGED')
 elif point=='SaveChangesAfterFirstReplace':assert (f['save']/'OtherSave/sav.dat').read_bytes()==b'FIXTURE_HUMAN_SAVE_CHANGE'
 current=tree(f['save']);run(f,'Recover');assert_state(f,'Before');assert tree(f['save'])==current
 return {'case':name,'status':'PASS','drift':point,'no_unknown_or_save_restore':True}
def junction_case():
 f=fixture('game_parent_junction');p=f['game']/'archive/pc/mod';dst=f['root']/'parked_mod';assert p.resolve().is_relative_to(f['root'].resolve()) and dst.parent.resolve()==f['root'].resolve();p.rename(dst)
 cmd=['pwsh','-NoProfile','-Command',"New-Item -ItemType Junction -Path $args[0] -Target $args[1] | Out-Null",str(p),str(dst)]
 # -Command positional parsing is not shell-concatenated with paths; use literal
 # structured script via a fixture-local script instead to avoid quoting ambiguity.
 ps=f['root']/'make_junction.ps1';ps.write_text('param([string]$Link,[string]$Target)\nNew-Item -ItemType Junction -Path $Link -Target $Target | Out-Null\n',encoding='utf8')
 r=subprocess.run(['pwsh','-NoProfile','-File',str(ps),'-Link',str(p),'-Target',str(dst)],capture_output=True,text=True);assert r.returncode==0,r.stderr
 before=tree(dst);run(f,'Preflight',okay=False);assert tree(dst)==before;return {'case':'game_parent_junction','status':'PASS','reparse_refused':True}
def main():
 assert not SUITE.exists();SUITE.mkdir(parents=True)
 jobs=[lambda:clean('core_clean_master','Core',True),lambda:clean('diagnostic_clean','Diagnostics'),junction_case]
 for point in ['AfterBackup','AfterStage','AfterFirstReplace','BeforeReceipt','CrashAfterBackup','CrashAfterFirstReplace','CrashBeforeReceipt','GameStartsAfterFirstReplace']:jobs.append(lambda p=point:interrupted('install_'+p,p))
 for point in ['AfterFirstRollback','CrashAfterFirstRollback']:jobs.append(lambda p=point:interrupted('rollback_'+p,p,True))
 for kind in ['before','package','extra_package','external','occupied','rollback_target','backup','journal','master_changed','traversal']:jobs.append(lambda k=kind:blocked('blocked_'+k,k))
 for proc in ['Cyberpunk2077','REDprelauncher','REDlauncher']:jobs.append(lambda p=proc:process_case('process_'+p,p))
 for point in ['TargetDriftAfterFirstReplace','ExternalChangesAfterFirstReplace','SaveChangesAfterFirstReplace']:jobs.append(lambda p=point:drift_case('drift_'+p,p))
 results=[];fail=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  for fut in concurrent.futures.as_completed([pool.submit(j) for j in jobs]):
   try:results.append(fut.result())
   except Exception as e:fail.append(str(e))
 result={'status':'PASS_WORKSPACE_ONLY_TRANSACTION_FIXTURES' if not fail else 'FAIL','cases':len(results),'planned':len(jobs),'results':sorted(results,key=lambda r:r['case']),'failures':fail,'real_game_install_or_rollback_calls':0,'real_save_copies_or_writes':0,'script_sha256':sha(SCRIPT),'test_sha256':sha(Path(__file__))};out=HERE/'fixture_result_02.json';assert not out.exists();writejson(out,result);print(json.dumps({'status':result['status'],'passed':len(results),'planned':len(jobs),'failures':fail[:2]},indent=2));assert not fail,'Fixture failures preserved; correct code and rerun into a fresh suite/output'
if __name__=='__main__':main()
