import hashlib,json,shutil,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;C=H/'candidate_01';M=json.loads((C/'install_manifest_01.json').read_text());G=Path(M['game_root'])
F=C/'deploy_fixtures_01';assert not F.exists();F.mkdir()
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def run(root,action,fail=''):
    cmd=['pwsh','-NoProfile','-File',str(H/'deploy_01.ps1'),'-Action',action,'-FixtureRoot',str(root)]
    if fail:cmd+=['-TestFailPoint',fail]
    return subprocess.run(cmd,capture_output=True,text=True)
results=[]
for case,fail in [('clean',''),('interrupt_after_backup','AfterBackup'),('interrupt_after_first_replace','AfterFirstReplace'),('interrupt_before_receipt','BeforeReceipt')]:
    root=F/case;game=root/'game';game.mkdir(parents=True)
    for row in M['package_files']:
        dst=game/row['path'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(G/row['path'],dst)
    a=run(root,'Validate');assert a.returncode==0,(case,'validate',a.stdout,a.stderr)
    b=run(root,'Install',fail);assert (b.returncode==0)==(not fail),(case,'install',b.stdout,b.stderr)
    if not fail:
        for action in ('Verify','ValidateRollback','Rollback'):
            x=run(root,action);assert x.returncode==0,(case,action,x.stdout,x.stderr)
    else:
        receipt=json.loads((root/'backup/receipt.json').read_text());assert receipt['status']=='INTERRUPTED_ROLLED_BACK'
    assert all(sha(game/x['path'])==x['before'] for x in M['package_files']),case
    assert not list(game.rglob('*.PTFRPH2_STAGE')),case
    results.append({'case':case,'validate':'PASS','install':'PASS' if not fail else 'EXPECTED_INTERRUPT_ROLLED_BACK','baseline_restored':True})
out={'status':'PASS_DEPLOYMENT_FIXTURES','cases':results,'game_writes':0,'save_writes':0}
(C/'deployment_tests_01.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))


