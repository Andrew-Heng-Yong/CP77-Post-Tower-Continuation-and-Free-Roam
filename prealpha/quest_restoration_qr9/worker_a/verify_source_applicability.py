"""Prove precisely which prior fixture paths are unchanged in final deployment tool."""
from pathlib import Path
import hashlib,json,difflib,shutil
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p):return p.read_text().replace('\r\n','\n')
e=H/'evidence';e.mkdir(exist_ok=True)
middle=e/'deploy_guarded_C8EE.ps1'
if not middle.exists():
    current=H/'deploy_qr9_guarded.ps1';assert sha(current)=='C8EE599B3898E4A7C28B5E4FA51D1B768D7EA53C24B7913AC0213B1D9F64DD7A';shutil.copyfile(current,middle)
old=H/'deploy_qr9.ps1';final=H/'deploy_qr9_guarded_final.ps1'
a=read(old);b=read(middle);c=read(final)
assert sha(middle)=='C8EE599B3898E4A7C28B5E4FA51D1B768D7EA53C24B7913AC0213B1D9F64DD7A'
assert sha(final)=='CE020172988081100199A35C9FAA9131444DB4DED52893480F2BA746EFFDA39E'
base=b.replace(",'HoldAfterLock')][string]$FailurePoint=''", ")][string]$FailurePoint=''")
base=base.replace("$PinnedDiagnosticsManifestSHA='C41A1547DB7B33F0F97B68ADC7509E937A6487B85D95E34F7AAFBF83991C38E1'","$PinnedDiagnosticsManifestSHA=''")
start=base.index('$script:transactionLock=$null\n');end=base.index('function Full(',start)
base=base[:start]+'\n'+base[end:]
base=base.replace('LockMutations\nClosed\n','Closed\n')
if base!=a:print(''.join(difflib.unified_diff(a.splitlines(True),base.splitlines(True)))[:2500])
assert base==a,'Unexpected changes beyond lock/pin/fixture control additions'
reduced=c
for line in [
 " if($j.operation -notin @('Install','Rollback') -or $j.state -notin @('PREPARING','PREPARED','APPLYING','INSTALLED_VERIFIED','ROLLING_BACK','ROLLED_BACK_VERIFIED','RESTORED_BEFORE_VERIFIED','RECOVERY_REQUIRED')){throw 'Unsupported transaction operation/state; preserve the journal for review'}\n",
 " if($script:journal.state -notin @('PREPARING','PREPARED','APPLYING','ROLLING_BACK','RECOVERY_REQUIRED')){throw 'Recover requires an interrupted transaction; use Verify or ValidateRollback for a committed receipt'}\n"]:
    assert reduced.count(line)==1;reduced=reduced.replace(line,'')
reduced=reduced.replace('try {\n# Resolve real paths only','# Resolve real paths only',1)
suffix="} finally {\n if($null -ne $script:transactionLock){$script:transactionLock.Dispose();$script:transactionLock=$null}\n}\n"
assert reduced.count(suffix)==1;reduced=reduced.replace(suffix,'')
assert reduced==b,'Unexpected final-revision changes'
diff=''.join(difflib.unified_diff(a.splitlines(True),c.splitlines(True),fromfile='suite02_unlocked',tofile='final_guarded_CE020'))
(e/'deployment_source_delta.diff').write_text(diff)
result=dict(status='PASS_EXACT_SOURCE_DELTA_APPLICABILITY',original_sha256=sha(old),guarded_c8ee_sha256=sha(middle),final_sha256=sha(final),
    unchanged=['All path/containment/reparse checks','All package/hash/dependency/closed-process checks','Save and unmanaged protection snapshots/comparison','Master backup plan/copy/verification','Payload stage/replace and guarded removal','Journal checksum/write/read root binding','RestoreActionStart body and exact managed-state preservation','Rollback and Verify behavior apart from encompassing finally disposal'],
    additions=['Stable worker-level mutating-action lock independent of recovery root','Separate frozen diagnostic manifest pin','Fixture-only held-lock checkpoint','Journal operation/state enum validation','Incomplete-state-only Recover admission','Lock disposal in outer finally for success and error'],
    prior_result_applicability='Prior fixture outputs retain their original script hashes; only unchanged behavior is reused. Focused final fixtures and independent review cover introduced admission/lifecycle guards.',
    no_real_installer_calls=True)
out=e/'source_applicability.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],sha256=sha(out))))
