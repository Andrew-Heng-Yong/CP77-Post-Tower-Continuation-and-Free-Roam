"""Workspace-only exercise of the actual add-only S24 installer and rollback.

Proof environment maps and the manifest's installed-XL environment pins are
rebound to isolated fixture dependencies/archives/XL. Proof build digests are
then rebound to that fixture manifest. Real aggregate artifact bytes, tool
hashes and source pins stay bound. No real game/save/cache writes or launch.
"""
import datetime,json,hashlib,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
REL=[Path('archive/pc/mod/00000_TowerContinued_SideJobs_S24.archive'),Path('archive/pc/mod/00000_TowerContinued_SideJobs_S24.archive.xl'),Path('r6/scripts/TowerContinued_SideJobs_S24/SideJobsS24.reds')]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def quote(s):return "'"+str(s).replace("'","''")+"'"
def main(revision):
 source=HERE/'build'/revision
 assert source.is_dir() and (source/'resource_check.json').is_file()
 suite=HERE/'fixtures'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 suite.mkdir(parents=True,exist_ok=False)
 cases=[];checks=0
 def fixture(name):
  p=suite/name;game=p/'game';saves=p/'saves';build=p/'build';recovery=p/'recovery'
  for d in [game/'archive/pc/mod',game/'r6/scripts',game/'r6/cache',game/'engine/config',saves,build]:d.mkdir(parents=True,exist_ok=True)
  names=['build.json','tests.json','compile_result.json','resource_check.json']+[r.name for r in REL]
  for name in names:shutil.copy2(source/name,build/name)
  seeds={game/'r6/scripts/protected.reds':b'untouched script',game/'r6/cache/final.redscripts':b'untouched cache',game/'engine/config/user.ini':b'untouched settings',saves/'ManualSave-1/sav.dat':b'untouched save'}
  for q,v in seeds.items():q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(v)
  archive_pins={};xl_pins={}
  for name in ['0000_TowerContinued_SideJobs_S23.archive','000_TowerContinued_SideJobs_S22.archive','00_TowerContinued_Courier_C1.archive','0_TowerContinued_NCPD_N1.archive','TowerContinued_PreAlpha.archive']:
   q=game/'archive/pc/mod'/name;q.write_bytes(('fixture '+name).encode());archive_pins[str(q)]=sha(q)
   x=game/'archive/pc/mod'/(name+'.xl');x.write_bytes(('fixture XL '+name).encode());xl_pins[str(x)]=sha(x)
  x=game/'archive/pc/mod/preexisting_injections.xl';x.write_bytes(b'fixture standalone XL');xl_pins[str(x)]=sha(x)
  manifest=read(build/'build.json');manifest['installed_xl_pins']=xl_pins;write(build/'build.json',manifest)
  plugin=game/'plugins/Scripts';plugin.mkdir(parents=True);(plugin/'include.reds').write_bytes(b'unchanged include')
  config=build/'compile_paths.txt';config.write_text('unused\nunused\n'+str(plugin)+'\n',encoding='utf-8')
  toolchain=build/'toolchain';toolchain.mkdir()
  for name in ['redscript-cli.exe','scc.exe']:(toolchain/name).write_bytes(('fixture '+name).encode())
  compiled=read(build/'compile_result.json');compiled['dependencies']={str(p):sha(p) for p in [game/'r6/scripts/protected.reds',plugin/'include.reds']};compiled['protected']={str(game/'r6/cache/final.redscripts'):sha(game/'r6/cache/final.redscripts')}
  compiled['script_roots']=[str(game/'r6/scripts'),str(plugin)]
  compiled['compiler_inputs']={str(p):sha(p) for p in [config,toolchain/'redscript-cli.exe',toolchain/'scc.exe']}
  write(build/'compile_result.json',compiled)
  audit=read(build/'resource_check.json');audit['archive_pins']=archive_pins;audit['xl_pins']=xl_pins;write(build/'resource_check.json',audit)
  for proof in ['tests.json','compile_result.json','resource_check.json']:
   q=build/proof;data=read(q);data['build_sha256']=sha(build/'build.json');write(q,data)
  return {'root':p,'game':game,'saves':saves,'build':build,'recovery':recovery,'sentinels':list(seeds)}
 def invoke(f,mode='Validate',expected=True,busy=False,extra='',**changes):
  nonlocal checks
  before={str(p):sha(p) for p in f['sentinels'] if p.is_file()}
  args={'Mode':mode,'Build':f['build'],'RecoveryRoot':f['recovery'],'GameRoot':f['game'],'SaveRoot':f['saves']}|changes
  proc="[pscustomobject]@{Id=123;ProcessName='Cyberpunk2077'}" if busy else 'return'
  command='function Get-Process { param([string]$Name) '+proc+' }; & '+quote(HERE/'deploy.ps1')+' -Fixture '
  command+=' '.join('-'+k+' '+quote(v) for k,v in args.items())+' '+extra
  result=subprocess.run(['pwsh','-NoProfile','-Command',command],capture_output=True,text=True,timeout=90)
  (f['root']/(mode+'_'+str(len(list(f['root'].glob('*.log'))))+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
  assert (result.returncode==0)==expected,(f['root'].name,mode,result.stdout,result.stderr)
  for p,h in before.items():assert sha(Path(p))==h,p
  checks+=1
  return result
 def mutate(f,name,change,rebind=False):
  p=f['build']/name;d=read(p);change(d);write(p,d)
  if rebind:
   for proof in ['tests.json','compile_result.json','resource_check.json']:
    q=f['build']/proof;o=read(q);o['build_sha256']=sha(p);write(q,o)
 def failcase(name,file,change,rebind=False):
  f=fixture(name);mutate(f,file,change,rebind);invoke(f,expected=False);assert not any((f['game']/r).exists() for r in REL);cases.append(name)
 f=fixture('normal');invoke(f);assert not any((f['game']/r).exists() for r in REL)
 invoke(f,'Install')
 for r in REL:assert sha(f['game']/r)==sha(source/r.name)
 invoke(f,'ValidateRollback');invoke(f,'Rollback')
 assert not any((f['game']/r).exists() for r in REL)
 for r in REL:assert sha(f['recovery']/('removed_'+r.name))==sha(source/r.name)
 invoke(f,'Rollback',expected=False);cases.append('normal_recoverable_add_only_no_repeat')
 manifest_cases=[
  ('metadata_manifest_path',lambda p:p.update(journal_metadata_proof='wrong.json')),
  ('wrong_status',lambda m:m.update(status='RESTORE_ALL')),
  ('packed_not_bool',lambda m:m.update(packed_readback='true')),
  ('wrong_order',lambda m:m['files'].reverse()),
  ('extra_file',lambda m:m['files'].append({'relative':'other','sha256':'0'*64})),
  ('replacement_metadata',lambda m:m['files'][0].update(old_sha256='0'*64)),
  ('file_escape',lambda m:m['files'][0].update(relative='../escape.archive')),
  ('empty_resources',lambda m:m.update(resources={})),
  ('official_resource',lambda m:m['resources'].update({'base\\forbidden.questphase':'0'*64})),
  ('official_override',lambda m:m.update(official_overrides=['base\\forbidden.questphase'])),
  ('unexpected_mod_override',lambda m:m['mod_overrides'].append('towercontinued\\other.questphase')),
  ('source_escape',lambda m:m['source_pins'].update({'../outside':'0'*64})),
  ('source_hash_drift',lambda m:m['source_pins'].update({next(iter(m['source_pins'])):'0'*64})),
  ('manifest_xl_missing',lambda m:m.pop('installed_xl_pins')),
  ('manifest_xl_empty',lambda m:m.update(installed_xl_pins={})),
  ('manifest_xl_hash_drift',lambda m:m['installed_xl_pins'].update({next(iter(m['installed_xl_pins'])):'0'*64})),
 ]
 for name,fn in manifest_cases:failcase(name,'build.json',fn,True)
 proof_cases=[
  ('tests_status','tests.json',lambda p:p.update(status='FAIL')),
  ('tests_build_binding','tests.json',lambda p:p.update(build_sha256='0'*64)),
  ('tests_tester_binding','tests.json',lambda p:p.update(tester_sha256='0'*64)),
  ('tests_no_native','tests.json',lambda p:p.update(native_payload_checks=0)),
  ('tests_no_policy','tests.json',lambda p:p.update(policy_cases=0)),
  ('tests_string_count','tests.json',lambda p:p.update(policy_cases='100')),
  ('compiler_status','compile_result.json',lambda p:p.update(status='FAIL')),
  ('compiler_binding','compile_result.json',lambda p:p.update(build_sha256='0'*64)),
  ('compiler_source','compile_result.json',lambda p:p.update(compiler_sha256='0'*64)),
  ('compiler_script','compile_result.json',lambda p:p.update(script_sha256='0'*64)),
  ('compiler_dependencies','compile_result.json',lambda p:p.update(dependencies={})),
  ('compiler_protected','compile_result.json',lambda p:p.update(protected={})),
  ('resource_status','resource_check.json',lambda p:p.update(status='FAIL')),
  ('resource_binding','resource_check.json',lambda p:p.update(build_sha256='0'*64)),
  ('resource_checker','resource_check.json',lambda p:p.update(checker_sha256='0'*64)),
  ('metadata_path','resource_check.json',lambda p:p.update(metadata_variant_proof='wrong.json')),
  ('metadata_binding','resource_check.json',lambda p:p.update(metadata_variant_proof_sha256='0'*64)),
  ('metadata_variants_missing','resource_check.json',lambda p:p.update(metadata_variants={})),
  ('metadata_variant_drift','resource_check.json',lambda p:p['metadata_variants'].update({next(iter(p['metadata_variants'])):'0'*64})),
  ('metadata_exact_byte_count','resource_check.json',lambda p:p.update(exact_byte_resources=0)),
  ('resource_comparisons','resource_check.json',lambda p:p.update(official_comparisons=0)),
  ('resource_priority','resource_check.json',lambda p:p.update(new_overrides_first=False)),
  ('resource_modlist','resource_check.json',lambda p:p.update(modlist_absent=False)),
  ('resource_official','resource_check.json',lambda p:p.update(official_overrides=['base\\no.questphase'])),
  ('collision_scope','resource_check.json',lambda p:p['collisions'][0].update(depot='towercontinued\\wrong.questphase')),
  ('collision_donor','resource_check.json',lambda p:p['collisions'][0].update(archive='unreviewed.archive')),
  ('collision_missing','resource_check.json',lambda p:p.update(collisions=[])),
  ('archive_pins_empty','resource_check.json',lambda p:p.update(archive_pins={})),
  ('xl_pins_empty','resource_check.json',lambda p:p.update(xl_pins={})),
  ('xl_pins_missing','resource_check.json',lambda p:p.pop('xl_pins')),
 ]
 for name,file,fn in proof_cases:failcase(name,file,fn)
 for flag in ['full_scc','combined_cli','body_readback','equipmentex','live_files_unchanged','script_environment_complete']:
  failcase('compiler_'+flag,'compile_result.json',lambda p,k=flag:p.update({k:False}))
 for i,r in enumerate(REL):
  f=fixture('existing_target_'+str(i));p=f['game']/r;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'user content');invoke(f,expected=False);assert p.read_bytes()==b'user content';cases.append('existing_target_'+str(i))
 f=fixture('artifact_drift');(f['build']/REL[0].name).write_bytes(b'drift');invoke(f,expected=False);cases.append('artifact_drift')
 f=fixture('dependency_drift');(f['game']/'r6/scripts/protected.reds').write_bytes(b'user changed dependency');invoke(f,expected=False);cases.append('dependency_drift')
 f=fixture('script_added');(f['game']/'r6/scripts/added.reds').write_bytes(b'uncompiled');invoke(f,expected=False);cases.append('script_added')
 f=fixture('include_added');(f['game']/'plugins/Scripts/added.reds').write_bytes(b'uncompiled include');invoke(f,expected=False);cases.append('include_added')
 f=fixture('include_config_drift');(f['build']/'compile_paths.txt').write_text('unused\nunused\n',encoding='utf-8');invoke(f,expected=False);cases.append('include_config_drift')
 f=fixture('compiler_tool_drift');(f['build']/'toolchain/scc.exe').write_bytes(b'changed compiler');invoke(f,expected=False);cases.append('compiler_tool_drift')
 failcase('compiler_roots_missing','compile_result.json',lambda p:p.update(script_roots=[]))
 failcase('compiler_inputs_missing','compile_result.json',lambda p:p.update(compiler_inputs={}))
 f=fixture('archive_set_drift');(f['game']/'archive/pc/mod/extra.archive').write_bytes(b'new');invoke(f,expected=False);cases.append('archive_set_drift')
 f=fixture('xl_added');(f['game']/'archive/pc/mod/extra.xl').write_bytes(b'new standalone injection');invoke(f,expected=False);cases.append('xl_added')
 f=fixture('xl_changed');(f['game']/'archive/pc/mod/00_TowerContinued_Courier_C1.archive.xl').write_bytes(b'changed injection');invoke(f,expected=False);cases.append('xl_changed')
 f=fixture('xl_removed');p=f['game']/'archive/pc/mod/00_TowerContinued_Courier_C1.archive.xl';p.rename(f['root']/p.name);invoke(f,expected=False);cases.append('xl_removed')
 f=fixture('modlist_present');(f['game']/'archive/pc/mod/modlist.txt').write_text('custom');invoke(f,expected=False);cases.append('modlist_present')
 f=fixture('busy');invoke(f,expected=False,busy=True);cases.append('busy')
 f=fixture('relative_build');invoke(f,expected=False,Build='build');cases.append('relative_build')
 f=fixture('wrong_root');invoke(f,expected=False,GameRoot=ROOT);cases.append('wrong_root')
 f=fixture('recovery_exists');f['recovery'].mkdir();invoke(f,'Install',expected=False);cases.append('recovery_exists')
 for name,switch in [('after_backup','-FailAfterBackup'),('after_first','-FailAfterFirst')]:
  f=fixture(name);invoke(f,'Install',expected=False,extra=switch);invoke(f,'ValidateRollback');invoke(f,'Rollback');assert not any((f['game']/r).exists() for r in REL);cases.append(name+'_recoverable')
 f=fixture('target_drift');invoke(f,'Install');p=f['game']/REL[2];p.write_bytes(b'user change');invoke(f,'Rollback',expected=False);assert p.read_bytes()==b'user change';cases.append('target_drift_refused')
 f=fixture('transaction_drift');invoke(f,'Install');(f['recovery']/'transaction.json').write_text('{}');invoke(f,'Rollback',expected=False);cases.append('transaction_drift')
 f=fixture('staged_drift');invoke(f,'Install');(f['recovery']/REL[0].name).write_bytes(b'drift');invoke(f,'Rollback',expected=False);cases.append('staged_drift')
 f=fixture('removed_exists');invoke(f,'Install');(f['recovery']/('removed_'+REL[0].name)).write_bytes(b'previous');invoke(f,'Rollback',expected=False);cases.append('removed_exists')
 f=fixture('extra_user_file');invoke(f,'Install');p=f['game']/REL[2].parent/'user_notes.txt';p.write_bytes(b'keep');invoke(f,'Rollback');assert p.read_bytes()==b'keep';cases.append('extra_user_file_preserved')
 def junction(link,target):
  r=subprocess.run(['pwsh','-NoProfile','-Command','New-Item -ItemType Junction -Path '+quote(link)+' -Target '+quote(target)+' | Out-Null'],capture_output=True,text=True)
  assert r.returncode==0,r.stderr
 f=fixture('junction_game');j=f['root']/'linked_game';junction(j,f['game']);invoke(f,expected=False,GameRoot=j);cases.append('junction_game_refused')
 f=fixture('junction_save');j=f['root']/'linked_saves';junction(j,f['saves']);invoke(f,expected=False,SaveRoot=j);cases.append('junction_save_refused')
 f=fixture('junction_build');j=f['root']/'linked_build';junction(j,f['build']);invoke(f,expected=False,Build=j);cases.append('junction_build_refused')
 f=fixture('junction_target_parent');j=f['game']/REL[2].parent;target=f['root']/'elsewhere';target.mkdir();junction(j,target);invoke(f,expected=False);cases.append('junction_target_parent_refused')
 f=fixture('junction_protected');j=f['game']/'r6/scripts/junction';target=f['root']/'protected_elsewhere';target.mkdir();junction(j,target);invoke(f,expected=False);cases.append('junction_protected_refused')
 # Real relative log symlink allowed by pinned safety helper; unsafe links denied.
 for name,target,allowed in [('relative_log','current.log',True),('escaping_log','../outside.log',False)]:
  f=fixture(name);folder=f['game']/'bin/x64/plugins/test';folder.mkdir(parents=True);(folder/'current.log').write_bytes(b'log');link=folder/'latest.log'
  r=subprocess.run(['pwsh','-NoProfile','-Command','New-Item -ItemType SymbolicLink -Path '+quote(link)+' -Target '+quote(target)+' | Out-Null'],capture_output=True,text=True)
  assert r.returncode==0,r.stderr
  invoke(f,expected=allowed)
  if allowed:invoke(f,'Install');invoke(f,'Rollback');assert link.is_symlink() and (folder/'current.log').read_bytes()==b'log'
  cases.append(name)
 report={'status':'PASS_WORKSPACE_FIXTURES_NOT_LIVE','cases':len(cases),'checks':checks,'case_names':cases,'build_sha256':sha(source/'build.json'),'installer_sha256':sha(HERE/'deploy.ps1'),'tester_sha256':sha(Path(__file__)),'game_writes':0,'save_writes':0,'fixtures_only':True}
 write(suite/'results.json',report);print(json.dumps(report))
if __name__=='__main__':main(sys.argv[1])

