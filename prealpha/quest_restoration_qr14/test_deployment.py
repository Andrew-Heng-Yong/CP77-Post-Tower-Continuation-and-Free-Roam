"""Actual PowerShell transaction exercised only beneath QR14/fixtures.
Broad state-machine cases use synthetic Core51 bytes; one integration case uses all actual QR8/QR13 package files. Saves/dependencies are synthetic.
"""
from pathlib import Path
import argparse, copy, hashlib, json, os, subprocess, time
H=Path(__file__).resolve().parent;SCRIPT=H/'deploy_core.ps1'
PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def put(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def snapshot(root):return{p.relative_to(root).as_posix():sha(p)for p in root.rglob('*')if p.is_file()and not p.is_symlink()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args()
    assert a.run.replace('_','').isalnum()and not (H/'fixtures'/a.run).exists()
    run=H/'fixtures'/a.run;run.mkdir(parents=True);base=read(H/'core_manifest_02.json');passed=[];commands=[];source_sha=sha(SCRIPT)
    def ck(label,v=True):
        assert v,label;passed.append(label)
        if len(passed)%5==0:print('Completed '+str(len(passed))+' checks: '+label,flush=True)
    def make(name, actual=False):
        root=run/name;root.mkdir();m=copy.deepcopy(base);m['game_root']=str(root/'game');m['save_root']=str(root/'saves');m['package_root']=str(root/'package')
        m['proofs']=[]
        m['compile_inputs']={};m['zip']='';m['zip_sha256']=None
        for row in m['files']:
            new=Path(base['package_root'])/row['path']
            old=H.parent/'quest_restoration_qr8/candidate_01/package'/row['path']
            old_data=old.read_bytes()if actual else ('SYNTHETIC_BEFORE:'+row['path']).encode()
            new_data=new.read_bytes()if actual else (('SYNTHETIC_AFTER:'if row['before']!=row['after']else'SYNTHETIC_BEFORE:')+row['path']).encode()
            put(root/'game'/row['path'],old_data);put(root/'package'/row['path'],new_data)
            row['before']=sha(root/'game'/row['path']);row['before_bytes']=len(old_data)
            row['after']=sha(root/'package'/row['path']);row['after_bytes']=len(new_data)
        for row in m['required_files']:
            data=('SYNTHETIC_DEPENDENCY:'+row['path']).encode();p=root/'game'/row['path'];put(p,data)
            row['sha256']=sha(p);row['bytes']=len(data)
        for row in m['protected_saves']+m['working_save_files']:
            data=('SYNTHETIC_SAVE:'+row['path']).encode();p=root/'saves'/row['path'];put(p,data);row['sha256']=sha(p);row['bytes']=len(data)
        put(root/'saves/OtherSave/sav.dat',b'SYNTHETIC_OTHER_SAVE')
        put(root/'game/unknown_mod/keep.txt',b'UNKNOWN_EXTERNAL_KEEP')
        put(root/'game'/Path(m['files'][0]['path']).parent/'QR9_capture_old.jsonl',b'IMMUTABLE_OLD_LOG')
        put(root/'game'/Path(m['files'][0]['path']).parent/'QR10_capture_future.jsonl',b'KEEP_FUTURE_LOG')
        mp=root/'manifest.json';mp.write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
        return root,m
    def save_manifest(root,m):(root/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
    def cmd(root,action,extra=()):return[str(PS),'-NoProfile','-File',str(SCRIPT),'-Action',action,'-FixtureRoot',str(root),'-FixtureManifest',str(root/'manifest.json'),'-FixtureManifestSHA',sha(root/'manifest.json'),*extra]
    def call(root,action,extra=(),ok=True):
        r=subprocess.run(cmd(root,action,extra),capture_output=True,text=True,timeout=35,creationflags=subprocess.CREATE_NO_WINDOW)
        commands.append({'case':root.name,'action':action,'extra':list(extra),'exit':r.returncode,'stdout':r.stdout[-6000:],'stderr':r.stderr[-5000:]})
        assert (r.returncode==0)==ok,(root.name,action,r.stdout,r.stderr)
        return r
    def state(root):return read(root/'recovery/core/journal.json')
    def managed(root,m,wanted):return all(sha(root/'game'/r['path'])==r[wanted]for r in m['files'])
    def protected(root,m):
        files=snapshot(root/'game');keys={r['path']for r in m['files']}
        return {'game':{p:v for p,v in files.items()if p not in keys},'saves':snapshot(root/'saves')}
    r,m=make('normal');before=protected(r,m)
    call(r,'Preflight');ck('preflight does not create recovery or change game/saves',not (r/'recovery').exists()and protected(r,m)==before)
    call(r,'Install');ck('normal install exact three changed leaves / Core51 + verified receipt',managed(r,m,'after')and json.loads(state(r)['payload_json'])['state']=='INSTALLED_VERIFIED')
    ck('both old/new recovery payloads exact',all(sha(r/'recovery/core'/side/x['path'])==x[field]for x in m['files']if x['before']!=x['after']for side,field in [('old','before'),('new','after')]))
    call(r,'Verify');call(r,'ValidateRollback');ck('post-install verification and rollback readiness')
    ck('normal install preserves all external/save/log bytes',protected(r,m)==before)
    call(r,'Install',ok=False);ck('repeat install refuses occupied receipt')
    call(r,'Recover',ok=False);ck('Recover refuses committed install')
    # Normal new saves are allowed before later rollback, but original master stays pinned.
    put(r/'saves/NewWorking/sav.dat',b'LEGITIMATE_NEW_WORKING_SAVE');before=protected(r,m)
    call(r,'Rollback');call(r,'Verify',['-ExpectedState','Before']);ck('rollback restores only QR8 changed leaves; newer saves/logs retained',managed(r,m,'before')and protected(r,m)==before)
    call(r,'Rollback',ok=False);ck('repeat rollback refuses restored receipt')
    for fault in ['AfterFirstBackup','AfterBackup','AfterStage','AfterFirstReplace','AfterSecondReplace','BeforeReceipt']:
        r,m=make('caught_'+fault);before=protected(r,m);call(r,'Install',['-FailurePoint',fault],ok=False)
        ck('caught interruption restores QR8:'+fault,managed(r,m,'before')and protected(r,m)==before)
        call(r,'Verify',['-ExpectedState','Before'])
    for fault in ['AfterJournal','AfterFirstBackup','AfterBackup','AfterStage','AfterFirstReplace','AfterSecondReplace','BeforeReceipt']:
        r,m=make('crash_'+fault);before=protected(r,m);call(r,'Install',['-FailurePoint','Crash'+fault],ok=False)
        call(r,'Verify',ok=False);call(r,'Recover');call(r,'Verify',['-ExpectedState','Before'])
        ck('hard interruption Recover restores QR8:'+fault,managed(r,m,'before')and protected(r,m)==before)
    for fault in ['AfterFirstRollback','CrashAfterFirstRollback','CrashAfterRollbackStage']:
        r,m=make('rollback_'+fault);call(r,'Install');before=protected(r,m);call(r,'Rollback',['-FailurePoint',fault],ok=False)
        if fault.startswith('Crash'):call(r,'Recover')
        call(r,'Verify');ck('interrupted rollback restores action-start QR13:'+fault,managed(r,m,'after')and protected(r,m)==before)
        call(r,'Rollback');ck('recovered rollback can be explicitly retried:'+fault,managed(r,m,'before'))
    for kind in ['unknown_target','missing_target','bad_source','extra_source','wrong_dependency','protected_master','working_save','game_running','launcher_running','scope','schema','device_report','escaped_report']:
        r,m=make('reject_'+kind)
        extra=[]
        if kind=='unknown_target':put(r/'game'/m['files'][0]['path'],b'UNKNOWN_CHANGED_BYTES')
        if kind=='missing_target':
            p=r/'game'/m['files'][0]['path'];assert p.resolve().is_relative_to(run.resolve());p.unlink()
        if kind=='bad_source':put(r/'package'/m['files'][1]['path'],b'BAD_SOURCE')
        if kind=='extra_source':put(r/'package/extra.txt',b'EXTRA')
        if kind=='wrong_dependency':put(r/'game'/m['required_files'][0]['path'],b'UNKNOWN_DEPENDENCY')
        if kind=='protected_master':put(r/'saves'/m['protected_saves'][0]['path'],b'CHANGED_MASTER')
        if kind=='working_save':put(r/'saves'/m['working_save_files'][0]['path'],b'CHANGED_FIXTURE')
        if kind=='game_running':extra=['-FixtureProcesses','Cyberpunk2077']
        if kind=='launcher_running':extra=['-FixtureProcesses','REDlauncher']
        if kind=='scope':m['files'][0]['path']='r6/scripts/unauthorized.reds';save_manifest(r,m)
        if kind=='schema':m['schema']='UNKNOWN_SCHEMA';save_manifest(r,m)
        if kind=='device_report':extra=['-ReportFile',str(H/'COM1.json')]
        if kind=='escaped_report':extra=['-ReportFile',str(H.parent/'escape.json')]
        before=protected(r,m);call(r,'Install',extra,ok=False)
        ck('refusal preserves unknown bytes/state:'+kind,protected(r,m)==before and not (r/'recovery').exists())
    r,m=make('game_starts');before=protected(r,m);call(r,'Install',['-FailurePoint','GameStartsAfterFirstReplace'],ok=False);call(r,'Recover')
    ck('game-start interruption blocks writes then recovers after closed',managed(r,m,'before')and protected(r,m)==before)
    r,m=make('unknown_during_write');call(r,'Install',['-FailurePoint','TargetDriftAfterFirstReplace'],ok=False);before=snapshot(r/'game');call(r,'Recover',ok=False)
    ck('unknown mixed state never overwritten by recovery',snapshot(r/'game')==before)
    r,m=make('save_changes');call(r,'Install',['-FailurePoint','SaveChangesAfterFirstReplace'],ok=False);current=(r/'saves/OtherSave/sav.dat').read_bytes();call(r,'Recover')
    ck('concurrent save change detected and never restored',current==b'FIXTURE_HUMAN_SAVE_CHANGE'and(r/'saves/OtherSave/sav.dat').read_bytes()==current and managed(r,m,'before'))
    r,m=make('external_changes');call(r,'Install',['-FailurePoint','ExternalChangesAfterFirstReplace'],ok=False);before=snapshot(r/'game');call(r,'Recover',ok=False)
    ck('changed dependency blocks recovery without editing unrelated file',snapshot(r/'game')==before)
    for which in ['journal','old_backup','new_backup']:
        r,m=make('corrupt_'+which);call(r,'Install')
        p=r/'recovery/core'/('journal.json'if which=='journal'else ('old/'if which=='old_backup'else'new/')+m['files'][0]['path'])
        put(p,b'CORRUPT');before=snapshot(r/'game');call(r,'Rollback',ok=False)
        ck('corrupt recovery evidence refuses rollback:'+which,snapshot(r/'game')==before)
    r,m=make('linked_target');p=r/'game'/m['files'][0]['path'];other=r/'old_copy.lua';other.write_bytes(p.read_bytes())
    assert p.resolve().is_relative_to(run.resolve());p.unlink();p.symlink_to(other)
    call(r,'Install',ok=False);ck('reparse target refused',p.is_symlink()and not(r/'recovery').exists())
    # Exclusive lock covers distinct recovery roots in one fixture deployment domain.
    r,m=make('lock');process=subprocess.Popen(cmd(r,'Install',['-FailurePoint','HoldAfterLock']),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    limit=time.monotonic()+20
    while not(r/'lock_ready.json').exists()and process.poll()is None and time.monotonic()<limit:time.sleep(.05)
    assert(r/'lock_ready.json').exists(),'held lock not ready'
    call(r,'Install',['-RecoveryRoot',str(r/'recovery/another')],ok=False);put(r/'release_lock',b'release');stdout,stderr=process.communicate(timeout=35)
    ck('stable lock excludes concurrent different-recovery transaction',process.returncode==0 and managed(r,m,'after'))
    r,m=make('actual_Core51',actual=True);before=protected(r,m)
    call(r,'Preflight');call(r,'Install');call(r,'Verify');call(r,'ValidateRollback')
    ck('actual full Core51 integration: exact QR13 bytes, three replacements',managed(r,m,'after')and len(list((r/'recovery/core/old').rglob('*.*')))==3)
    call(r,'Rollback');call(r,'Verify',['-ExpectedState','Before'])
    ck('actual full Core51 integration: exact QR8 rollback and all protections',managed(r,m,'before')and protected(r,m)==before)
    assert sha(SCRIPT)==source_sha,'installer changed during fixture run'
    result={'status':'PASS_DEPLOYMENT_FIXTURES','run':a.run,'installer_sha256':source_sha,'manifest_sha256':sha(H/'core_manifest_02.json'),
        'checks':passed,'command_count':len(commands),'commands':commands,'payloads':'State-machine cases synthetic Core51; separate integration case actual pinned QR8/QR13 Core51. All saves/dependencies synthetic.',
        'real_game_mutations':0,'game_launches':0,'scope':str(run)}
    output=H/(a.run+'_results.json');assert not output.exists();output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({'status':result['status'],'checks':len(passed),'commands':len(commands),'out':str(output)})

if __name__=='__main__':main()
