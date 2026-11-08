"""Affected-path/lock tests on the final script; unchanged controls reuse suite02."""
from pathlib import Path
import importlib.util,json,subprocess,time,concurrent.futures
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('qr9_final_helpers',H/'test_deployment.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
t.SUITE=H/'fixtures/final_01'
t.SCRIPT=H/'deploy_qr9_guarded.ps1'
def hold_case(name,drift=False):
    f=t.fixture(name)
    args=['pwsh','-NoProfile','-File',str(t.SCRIPT),'-Component','Core','-Action','Install','-FixtureRoot',str(f['root']),'-FixtureManifest',str(f['manifest']),'-FixtureManifestSHA',t.sha(f['manifest']),'-FailurePoint','HoldAfterLock']
    p=subprocess.Popen(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    ready=f['root']/'lock_ready.json';deadline=time.monotonic()+60
    while not ready.exists():
        if p.poll()is not None:raise AssertionError(('holder did not reach lock',p.communicate()))
        assert time.monotonic()<deadline,'holder lock signal timeout'
        time.sleep(.1)
    receipt=json.loads(ready.read_text());assert receipt['scope']=='FIXTURE_ROOT_SHARED_BETWEEN_RECOVERY_PATHS'
    if drift:
        t.put(f['game']/f['data']['required_files'][0]['path'],b'USER_DEPENDENCY_DRIFT_WHILE_LOCK_HELD')
    else:
        alternate=f['root']/'recovery/alternate'
        second=t.run(f,'Install',okay=False,extra=['-RecoveryRoot',str(alternate)])
        assert 'Another QR9 deployment action holds the stable installer lock' in second.stderr
        assert not alternate.exists();t.assert_state(f,'Before')
    t.put(f['root']/'release_lock',b'fixture release only')
    stdout,stderr=p.communicate(timeout=120)
    (f['root']/'held_install.stdout').write_text(stdout+'\nSTDERR\n'+stderr)
    if drift:
        assert p.returncode!=0 and 'Hash drift:'in stderr
        assert not(f['root']/'recovery').exists()
        t.assert_state(f,'Before')
        assert(f['game']/f['data']['required_files'][0]['path']).read_bytes()==b'USER_DEPENDENCY_DRIFT_WHILE_LOCK_HELD'
    else:
        assert p.returncode==0,(stdout,stderr);t.assert_state(f,'After');t.run(f,'Verify');t.run(f,'Rollback');t.assert_state(f,'Before')
    assert t.tree(f['save'])==f['saves_before']
    return dict(case=name,status='PASS',lock_independent_of_recovery_root=True,post_lock_dependency_refresh=drift)
def unknown_lock():
    f=t.fixture('unknown_lock_bytes');t.put(f['root']/'installer.lock',b'UNKNOWN_USER_FILE')
    r=t.run(f,'Install',okay=False);assert 'Unexpected installer lock contents' in r.stderr
    assert(f['root']/'installer.lock').read_bytes()==b'UNKNOWN_USER_FILE';t.assert_state(f,'Before')
    return dict(case='unknown_lock_bytes',status='PASS',unknown_bytes_preserved=True)
def main():
    assert not t.SUITE.exists();t.SUITE.mkdir(parents=True)
    jobs=[lambda:t.clean('core_clean_master','Core',True),lambda:t.clean('diagnostic_clean','Diagnostics'),lambda:t.interrupted('crash_install','CrashAfterFirstReplace'),lambda:t.interrupted('crash_rollback','CrashAfterFirstRollback',True),lambda:hold_case('different_recovery_contention'),lambda:hold_case('post_lock_dependency_drift',True),unknown_lock]
    results=[];failures=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for fut in concurrent.futures.as_completed([pool.submit(j)for j in jobs]):
            try:results.append(fut.result())
            except Exception as e:failures.append(str(e))
    result=dict(status='PASS_FINAL_AFFECTED_PATHS_AND_LOCK_FIXTURES'if not failures else'FAIL',cases=len(results),planned=len(jobs),results=results,failures=failures,script_sha256=t.sha(t.SCRIPT),test_sha256=t.sha(Path(__file__)),real_game_calls=0,real_save_calls=0)
    out=H/'final_fixture_result_01.json';assert not out.exists();t.writejson(out,result);print(json.dumps(dict(status=result['status'],passed=len(results),failures=failures[:2])));assert not failures
if __name__=='__main__':main()
