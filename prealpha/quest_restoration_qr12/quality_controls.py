"""Offline safeguards and preserved diagnostic receipts; no game/save writes."""
from pathlib import Path
import hashlib,json,subprocess
H=Path(__file__).resolve().parent
PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main():
    output=H/'quality_controls.json';assert not output.exists()
    checks=[]
    for name in ['read_saves.ps1','read_history_package.ps1']:
        args=[str(PS),'-NoLogo','-NoProfile','-File',str(H/name),'-Tag','NUL']
        p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',errors='replace')
        assert p.returncode!=0 and 'non-device' in p.stderr
        checks.append({'control':name+' reserved NUL tag rejected before source/DLL access','command':args,'exit_code':p.returncode,'expected':'nonzero parameter guard','stderr':p.stderr})
    a=read(H/'history_package_01.json');b=read(H/'history_package_verified_02.json')
    assert a['sha256']==b['sha256'] and a['rows']==b['rows'] and b['save_writes']==0
    checks.append({'control':'hardened MemoryStream SHA check preserves exact selected saved fields','before_sha256':sha(H/'history_package_01.json'),'after_sha256':sha(H/'history_package_verified_02.json'),'result':'PASS_NO_SEMANTIC_CHANGE'})
    t=read(H/'classification_controls_02.json');assert len(t['checks'])==12
    checks.append({'control':'prerequisite and independent private-marker controls','path':str(H/'classification_controls_02.json'),'sha256':sha(H/'classification_controls_02.json'),'count':12})
    output.write_text(json.dumps({'status':'PASS_OFFLINE_SAFEGUARDS','checks':checks,'preserved_failed_attempt':{
        'command':'python -X utf8 -B prealpha/quest_restoration_qr12/test_classification.py',
        'observed':'AssertionError after adding private-admission gate: old actual-state expectation REQUIRES_MANUAL_PREREQUISITE was invalid because actual M24 contains Issued1 and Entered1.',
        'correction':'Actual negative fixture must be BLOCKED_BY_HISTORY; hypothetical READY uses a separate in-memory copy without private admission. Native earned history remains UNKNOWN.',
        'game_or_save_changes':0},'limits':'Synthetic controls and static source safeguards are not gameplay tests. No 171-body reparse or diagnostic implementation change.'},indent=2)+'\n',encoding='utf-8')
    print({'status':'PASS_OFFLINE_SAFEGUARDS','guard_tests':2,'classification_controls':12,'selected_probe_equal':True})
if __name__=='__main__':main()
