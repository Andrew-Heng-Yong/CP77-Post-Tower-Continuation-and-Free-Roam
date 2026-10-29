import json,shutil,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[2]
C=W/'prealpha/credits_cover_lc4/candidate_02'
G=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
P=Path('C:/Users/Ayong/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe')
S=W/'prealpha/credits_cover_lc4/deploy_01.ps1'
m=json.loads((C/'install_manifest_01.json').read_text())
paths=[x['path'] for x in m['package_files']]+[m['compatibility_files'][0]['path']]
root=C/'deploy_fixtures_01';root.mkdir(exist_ok=False)
results=[]
for name,fail in [('normal',None),('backup','AfterBackup'),('stage','AfterStage'),('replace','AfterFirstReplace'),('receipt','BeforeReceipt')]:
 case=root/name;game=case/'game'
 for rel in paths:
  dest=game/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(G/rel,dest)
 def run(action,fp=None):
  cmd=[str(P),'-NoLogo','-NoProfile','-File',str(S),'-Action',action,'-FixtureRoot',str(case)]
  if fp:cmd+=['-TestFailPoint',fp]
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
  return dict(action=action,failpoint=fp,exit=p.returncode,stdout=p.stdout[-750:],stderr=p.stderr[-750:])
 rows=[run('Validate'),run('Install',fail)]
 assert rows[0]['exit']==0,rows
 assert (rows[1]['exit']!=0 if fail else rows[1]['exit']==0),rows
 if not fail:
  rows.extend([run('Verify'),run('ValidateRollback')])
  assert all(x['exit']==0 for x in rows[2:]),rows
 rows.append(run('Rollback'))
 assert rows[-1]['exit']==0,rows
 for x in m['package_files']:
  import hashlib
  assert hashlib.sha256((game/x['path']).read_bytes()).hexdigest().upper()==x['before'],x['path']
 results.append(dict(case=name,actions=rows,status='PASS'))
report=dict(status='PASS',cases=len(results),interrupted=4,results=results,game_writes=0,save_writes=0)
(C/'deployment_tests_01.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(status='PASS',cases=len(results),interrupted=4)))
