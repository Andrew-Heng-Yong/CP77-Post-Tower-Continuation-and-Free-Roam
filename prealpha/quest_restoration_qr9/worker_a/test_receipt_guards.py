"""Final receipt boundary and same-process lock-disposal fixtures."""
from pathlib import Path
import importlib.util,json,subprocess,concurrent.futures,hashlib
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('qr9_receipt_helpers',H/'test_deployment.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
t.SUITE=H/'fixtures/receipt_guards_01';t.SCRIPT=H/'deploy_qr9_guarded_final.ps1'
def committed():
    f=t.fixture('committed_recovery_refusal');t.run(f,'Install');before=(f['root']/'recovery/core/journal.json').read_bytes()
    r=t.run(f,'Recover',okay=False);assert 'Recover requires an interrupted transaction'in r.stderr;t.assert_state(f,'After');assert(f['root']/'recovery/core/journal.json').read_bytes()==before
    t.run(f,'Rollback');before=(f['root']/'recovery/core/journal.json').read_bytes();r=t.run(f,'Recover',okay=False);assert 'Recover requires an interrupted transaction'in r.stderr;t.assert_state(f,'Before');assert(f['root']/'recovery/core/journal.json').read_bytes()==before
    return dict(case='committed_recovery_refusal',status='PASS',states=['INSTALLED_VERIFIED','ROLLED_BACK_VERIFIED'])
def bad_journal():
    f=t.fixture('unknown_journal_operation');t.run(f,'Install');p=f['root']/'recovery/core/journal.json';envelope=json.loads(p.read_text());j=json.loads(envelope['payload_json']);j['operation']='UNKNOWN_CARRIER';envelope['payload_json']=json.dumps(j,separators=(',',':'));envelope['payload_sha256']=hashlib.sha256(envelope['payload_json'].encode()).hexdigest().upper();t.writejson(p,envelope);before=p.read_bytes()
    r=t.run(f,'Recover',okay=False);assert 'Unsupported transaction operation/state'in r.stderr;t.assert_state(f,'After');assert p.read_bytes()==before
    return dict(case='unknown_journal_operation',status='PASS',checksum_valid_unknown_operation_refused=True)
def same_process(failure=False):
    f=t.fixture('same_process_'+('error'if failure else'success'))
    q=lambda p:"'"+str(p).replace("'","''")+"'"
    command='& '+q(t.SCRIPT)+' -Component Core -Action Install -FixtureRoot '+q(f['root'])+' -FixtureManifest '+q(f['manifest'])+' -FixtureManifestSHA '+q(t.sha(f['manifest']))
    if failure:command+=' -FailurePoint AfterBackup'
    host=f['root']/'host.ps1';proof=f['root']/'host_proof.json'
    host.write_text("$ErrorActionPreference='Stop'\n$caught=$false\ntry { "+command+" } catch { $caught=$true }\n"+"if($caught -ne $"+str(failure).lower()+"){throw 'Unexpected called-script result'}\n"+"$p="+q(f['root']/'installer.lock')+"\n$held=[IO.FileStream]::new($p,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)\ntry { [IO.File]::WriteAllText("+q(proof)+",'{\"lock_reopened_in_same_process\":true}') } finally { $held.Dispose() }\n",encoding='utf8')
    result=subprocess.run(['pwsh','-NoProfile','-File',str(host)],capture_output=True,text=True)
    (f['root']/'host.stdout').write_text(result.stdout+'\nSTDERR\n'+result.stderr)
    assert result.returncode==0,(result.stdout,result.stderr);assert json.loads(proof.read_text())['lock_reopened_in_same_process']
    t.assert_state(f,'Before'if failure else'After');assert t.tree(f['save'])==f['saves_before']
    if failure:
        r=t.run(f,'Recover',okay=False);assert 'Recover requires an interrupted transaction'in r.stderr
    return dict(case=f['root'].name,status='PASS',explicit_disposal_after='error'if failure else'success')
def main():
    assert not t.SUITE.exists();t.SUITE.mkdir(parents=True)
    jobs=[committed,bad_journal,lambda:same_process(False),lambda:same_process(True)];results=[];errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:
        for f in concurrent.futures.as_completed([pool.submit(j)for j in jobs]):
            try:results.append(f.result())
            except Exception as e:errors.append(str(e))
    result=dict(status='PASS_RECEIPT_BOUNDARIES_AND_EXPLICIT_LOCK_DISPOSAL'if not errors else'FAIL',cases=results,errors=errors,script_sha256=t.sha(t.SCRIPT),test_sha256=t.sha(Path(__file__)),real_game_calls=0,real_save_calls=0)
    out=H/'receipt_guards_result_01.json';assert not out.exists();t.writejson(out,result);print(json.dumps(dict(status=result['status'],cases=len(results),errors=errors[:2])));assert not errors
if __name__=='__main__':main()
