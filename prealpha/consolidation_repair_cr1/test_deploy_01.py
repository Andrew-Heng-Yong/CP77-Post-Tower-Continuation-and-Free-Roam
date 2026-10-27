"""Real replacement code against disposable workspace fixtures only."""
import shutil,subprocess
from common import *
M=read(CANDIDATE/'install_manifest_01.json')
PWSH=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
F=CANDIDATE/'deploy_fixtures';assert not F.exists();F.mkdir()
before={r['path']:sha(GAME/r['path']) for r in M['package_files']}
assert before=={r['path']:r['before'] for r in M['package_files']}
actions=[]
def run(action,root,point='',okay=True):
    cmd=[str(PWSH),'-NoProfile','-File',str(HERE/'deploy_01.ps1'),'-Action',action,'-FixtureRoot',str(root)]
    if point:cmd+=['-TestFailPoint',point]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=90)
    assert (result.returncode==0)==okay,(action,root,point,result.stdout[-1000:],result.stderr[-1000:])
    actions.append({'action':action,'fixture':root.name,'point':point,'expected_success':okay,'exit_code':result.returncode,'output':(result.stdout+result.stderr)[-1600:]})
def setup(name):
    root=F/name;root.mkdir()
    shutil.copytree(CANDIDATE/'archived_previous',root/'game')
    return root
def state(root,which):
    for r in M['package_files']:assert sha(root/'game'/r['path'])==r[which],(root,r['path'],which)
    assert not list((root/'game').rglob('*.ptfr-cr1-stage'))
root=setup('normal')
for action in ['Validate','Install','Verify','ValidateRollback','Rollback']:run(action,root)
state(root,'before')
run('Rollback',root);state(root,'before')
for point in ['AfterBackup','AfterStage','BeforeReplace','AfterReplace','BeforeReceipt','AfterReceipt']:
    root=setup('interrupt_'+point)
    run('Validate',root);run('Install',root,point,False)
    run('ValidateRollback',root);run('Rollback',root);state(root,'before')
root=setup('partial_stage')
run('Install',root,'AfterStage',False)
stage=root/'game'/(M['files'][0]['target']+'.ptfr-cr1-stage')
stage.write_bytes(b'fixture simulates interruption midway through a staging copy')
partial_hash=sha(stage)
run('ValidateRollback',root);run('Rollback',root);state(root,'before')
held=root/'backup/interrupted_stage'/(M['files'][0]['target']+'.'+partial_hash)
assert sha(held)==partial_hash,'Partial stage not preserved'
root=setup('later_target_drift')
run('Install',root)
target=root/'game'/M['files'][0]['target'];target.write_bytes(b'user changed this fixture after install')
drift=sha(target);run('ValidateRollback',root,okay=False);assert sha(target)==drift
shutil.copyfile(CANDIDATE/'package'/M['files'][0]['target'],target)
run('Rollback',root);state(root,'before')
root=setup('unaffected_file_drift')
untouched=next(r for r in M['package_files'] if r['before']==r['after'])
(root/'game'/untouched['path']).write_bytes(b'unrelated fixture mod edit')
run('Validate',root,okay=False);assert not (root/'backup').exists()
run('Validate',CANDIDATE/'outside_fixture',okay=False)
assert before=={r['path']:sha(GAME/r['path']) for r in M['package_files']},'Real game drifted during fixture run'
result={'status':'PASS','actions':actions,'action_count':len(actions),'interruption_points':6,'partial_stage_recovered':True,'later_changes_refused':True,'unaffected_path_drift_refused':True,'path_escape_refused':True,'full_real_package_unchanged':51,'game_writes':0,'save_writes':0}
write_new(CANDIDATE/'deployment_tests_01.json',result)
(CANDIDATE/'deployment_tests_01.json.sha256').write_text(sha(CANDIDATE/'deployment_tests_01.json')+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='actions'}))
