"""Independent synthetic-file tests of the exact frozen A installer.

Copies the reviewed script byte-for-byte into a fresh C-owned tree, supplies
explicit fixture roots/manifests, and never invokes a real game action.
No source save bytes or actual game files are used as fixture payloads.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,data):
 p=Path(p);assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
def payload(p,data):p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(data);return sha(p)
def snapshot(p):return {str(x.relative_to(p)).replace('\\','/'):sha(x)for x in p.rglob('*')if x.is_file()}

def main(out,script_sha,core_manifest,script):
 out=out.resolve();assert out.is_relative_to(HERE) and not out.exists();out.mkdir(parents=True)
 src=Path(script).resolve();assert src.is_relative_to(ROOT/'prealpha/quest_restoration_qr9/worker_a')and sha(src)==script_sha
 code=src.read_text(encoding='utf-8-sig');assert 'if($fixture)'in code and "Beneath (Join-Path $worker 'fixtures') $FixtureRoot"in code
 copied=out/src.name;shutil.copyfile(src,copied);assert sha(copied)==script_sha
 cm=read(core_manifest);checks=[];runs=[];cases=[]
 def ck(n,v,e=None):checks.append({'check':n,'pass':bool(v),'evidence':e});assert v,n
 ck('Exact frozen source copied unchanged',sha(copied)==script_sha)
 ck('Core manifest is canonical51/two-change source',cm['source_epoch']=='QR8:02'and len(cm['files'])==51 and len(cm['changing_paths'])==2)
 def fixture(name,component='Core'):
  f=out/'fixtures'/name;f.mkdir(parents=True);game=f/'game';saves=f/'saves';package=f/'package';game.mkdir();saves.mkdir();package.mkdir()
  files=[];paths=[r['path']for r in cm['files']]if component=='Core'else['bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/init.lua','bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/watch.json']
  for path in paths:
   before=('SYNTHETIC_BEFORE|'+path).encode()if component=='Core'else None
   after=('SYNTHETIC_AFTER|'+path).encode()if component=='Diagnostics'or path in cm['changing_paths']else before
   before_hash=payload(game/path,before)if before is not None else None;after_hash=payload(package/path,after)
   files.append({'path':path,'before':before_hash,'after':after_hash,'before_bytes':len(before)if before is not None else None,'after_bytes':len(after)})
  master={}
  for name in ['metadata.9.json','sav.dat','screenshot.png']:
   data=('SYNTHETIC_MASTER|'+name).encode();h=payload(saves/'ManualSave-23'/name,data);master[name]={'sha256':h,'bytes':len(data)}
  payload(saves/'OtherSave/sav.dat',b'SYNTHETIC_PREEXISTING_HUMAN_PROGRESS')
  dependency='external/mod_fixture.bin';dd=b'SYNTHETIC_EXTERNAL_DEPENDENCY';dh=payload(game/dependency,dd)
  m={'schema':'PTFR_QR9_COMPONENT_V1','component':component,'source_epoch':'QR8:02','game_root':str(game),'save_root':str(saves),'package_root':str(package),'zip':None,'zip_sha256':None,'proofs':[],'process_names':['Cyberpunk2077','REDlauncher'],'files':files,'required_files':[{'path':dependency,'sha256':dh,'bytes':len(dd),'active_only':False}]}
  if component=='Core':m['master_backup']={'slot':'ManualSave-23','files':master}
  mf=f/'manifest.json';write(mf,m);return {'root':f,'game':game,'saves':saves,'manifest':mf,'manifest_sha':sha(mf),'component':component,'before_game':snapshot(game),'before_saves':snapshot(saves),'files':files}
 def run(f,action,extra=None,want=0):
  args=['pwsh','-NoProfile','-File',str(copied),'-Component',f['component'],'-Action',action,'-FixtureRoot',str(f['root']),'-FixtureManifest',str(f['manifest']),'-FixtureManifestSHA',f['manifest_sha']]+list(extra or [])
  p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace');r={'case':f['root'].name,'action':action,'argv':args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr};runs.append(r)
  ck(f['root'].name+' '+action+' expected exit',p.returncode==want if want is not None else p.returncode!=0,{'returncode':p.returncode,'expected':want})
  return p
 def recovery(f):return f['root']/'recovery'/f['component'].lower()
 # Ground truth is actual independent file inventories, not installer success text.
 clean=fixture('clean_core');run(clean,'Preflight',['-BackupMaster']);ck('Preflight changes no fixture save/game bytes',snapshot(clean['game'])==clean['before_game']and snapshot(clean['saves'])==clean['before_saves']and not recovery(clean).exists())
 run(clean,'Install',['-BackupMaster']);ck('Exactly two existing core targets changed',[r['path']for r in clean['files']if sha(clean['game']/r['path'])!=r['before']]==[r['path']for r in clean['files']if r['before']!=r['after']])
 for r in clean['files']:ck('Installed exact expected target '+r['path'],sha(clean['game']/r['path'])==r['after'])
 ck('Synthetic original master and all saves unchanged during install',snapshot(clean['saves'])==clean['before_saves'])
 for n,h in cm['master_backup']['files'].items():
  # These fixture bytes deliberately do not equal the human's real master.
  s=clean['saves']/'ManualSave-23'/n;b=recovery(clean)/'master_before/ManualSave-23'/n;ck('Independent master backup byte equality '+n,b.read_bytes()==s.read_bytes())
 payload(clean['saves']/'ManualSave-24/sav.dat',b'SYNTHETIC_NEW_USER_PROGRESS_AFTER_INSTALL');progress=snapshot(clean['saves'])
 run(clean,'Verify');run(clean,'ValidateRollback');run(clean,'Rollback');run(clean,'Verify',['-ExpectedState','Before'])
 ck('Core rollback restores exact original game bytes',snapshot(clean['game'])==clean['before_game']);ck('Legitimate later working-slot save survives verify/rollback',snapshot(clean['saves'])==progress)
 cases.append({'case':'clean_core','result':'PASS','scope':'51inventory,2writes,3file master backup,then-current save preservation'})
 crash=fixture('crash_core');run(crash,'Install',['-BackupMaster','-FailurePoint','CrashAfterFirstReplace'],want=72)
 changed=[r['path']for r in crash['files']if sha(crash['game']/r['path'])!=r['before']];ck('Hard-crash control actually left one changed core file',len(changed)==1,changed)
 run(crash,'Recover');ck('Independent hard-crash recovery restores exact game files',snapshot(crash['game'])==crash['before_game']);ck('Hard-crash recovery leaves saves untouched',snapshot(crash['saves'])==crash['before_saves']);cases.append({'case':'crash_core','result':'PASS','scope':'actual process exit72 after one replace,then journal recovery'})
 drift=fixture('unknown_target');run(drift,'Install',['-FailurePoint','TargetDriftAfterFirstReplace'],want=None)
 first=next(r for r in drift['files']if r['before']!=r['after']);target=drift['game']/first['path'];ck('Unknown-target control actually wrote its sentinel',target.read_text()=='FIXTURE_UNKNOWN_CHANGED_BYTES')
 preserved=snapshot(drift['game']);run(drift,'Recover',want=None);ck('Recovery refuses to overwrite unknown target bytes',snapshot(drift['game'])==preserved);ck('Unknown-target failure does not touch saves',snapshot(drift['saves'])==drift['before_saves']);cases.append({'case':'unknown_target','result':'PASS','scope':'actual drift sentinel remains through recovery refusal'})
 addon=fixture('clean_addon','Diagnostics');run(addon,'Install');folder=addon['game']/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics'
 payload(folder/'QR9_capture_TEST.jsonl',b'SYNTHETIC_CAPTURE_PRESERVE');payload(folder/'unknown_user_file.txt',b'SYNTHETIC_USER_FILE_PRESERVE');run(addon,'ValidateRollback');run(addon,'Rollback')
 ck('Addon rollback removes only its two exact managed files',all(not(addon['game']/r['path']).exists()for r in addon['files']))
 ck('Addon rollback preserves generated logs and unknown files',(folder/'QR9_capture_TEST.jsonl').read_bytes()==b'SYNTHETIC_CAPTURE_PRESERVE'and(folder/'unknown_user_file.txt').read_bytes()==b'SYNTHETIC_USER_FILE_PRESERVE');ck('Addon rollback leaves all fixture saves unchanged',snapshot(addon['saves'])==addon['before_saves']);cases.append({'case':'clean_addon','result':'PASS','scope':'two added files removed,generated logs/unknowns kept'})
 ck('Reviewed real installer source remained unchanged',sha(src)==script_sha)
 write(out/'review.json',{'status':'PASS_INDEPENDENT_SYNTHETIC_FIXTURES_NO_REAL_DEPLOYMENT','checks':checks,'checks_passed':len(checks),'cases':cases,'commands':runs,'source':str(src),'source_sha256':script_sha,'source_core_manifest':str(core_manifest),'source_core_manifest_sha256':sha(core_manifest),'real_game_or_save_access':0,'real_install_rollback_recover_calls':0,'real_save_bytes_copied':0,'code_sha256':sha(__file__),'limits':['Synthetic files validate safety/recovery behavior, not actual write permissions or gameplay.','No real installer action is authorized by this report. Master backups and actual native New Save bootstrap remain future user actions.','Actual A fixture suite and separate read-only real preflight remain required inputs to readiness.']})
 print({'checks':len(checks),'cases':len(cases),'out':str(out)})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--script',type=Path,required=True);p.add_argument('--script-sha',required=True);p.add_argument('--core-manifest',type=Path,required=True);a=p.parse_args();main(a.output,a.script_sha,a.core_manifest,a.script)
