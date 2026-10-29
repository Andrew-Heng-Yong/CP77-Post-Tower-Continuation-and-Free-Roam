"""Capture immutable save evidence only after fixture success and with the game closed."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timezone
import json,subprocess
H=Path(__file__).resolve().parent;C=H/'candidate_01'
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
PW=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def closed():
    result=subprocess.run([str(PW),'-NoProfile','-Command',"$ErrorActionPreference='Stop';if(Get-Process -Name Cyberpunk2077,REDprelauncher -ErrorAction SilentlyContinue){exit 42};exit 0"],capture_output=True,text=True,timeout=20)
    assert result.returncode==0,'Save capture requires game and launcher closed'
def pinned(path):
    assert digest(path)==Path(str(path)+'.sha256').read_text().strip(),'Changed proof: '+str(path)
out=C/'save_baseline_01.json'
assert not out.exists() and not Path(str(out)+'.sha256').exists(),'Preserve existing save baseline'
closed()
manifest=C/'install_manifest_01.json';fixtures=C/'deployment_tests_01.json';zip_proof=C/'zip_proof_01.json'
for p in (manifest,fixtures,zip_proof):pinned(p)
m=read(manifest);f=read(fixtures);z=read(zip_proof)
assert m['status']=='WA3_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED' and m['full_package_count']==51
assert f['status']=='PASS' and f['fixture_actions']==26 and f['interruption_points']==7 and f['all_interrupted_states_recoverable'] and f['normal_install_verify_rollback']
assert z['status']=='UNRELEASED_FULL_51_PATH_ZIP_VERIFIED' and z['members']==51 and digest(Path(z['path']))==z['sha256']
paths=sorted(p for p in S.rglob('*') if p.is_file());assert paths,'Empty save directory'
rows=[{'path':str(p.relative_to(S)),'sha256':digest(p),'size':p.stat().st_size} for p in paths]
assert paths==sorted(p for p in S.rglob('*') if p.is_file()),'Save inventory changed during capture'
assert all(digest(S/r['path'])==r['sha256'] and (S/r['path']).stat().st_size==r['size'] for r in rows),'Save bytes changed during capture'
closed()
result={'status':'BEFORE_WA3_INSTALL_READ_ONLY_CAPTURE','captured_utc':datetime.now(timezone.utc).isoformat(),'game_and_launcher_closed':True,'manifest_sha256':digest(manifest),'fixture_proof_sha256':digest(fixtures),'files':rows,'game_writes':0,'save_writes':0}
out.write_text(json.dumps(result,indent=2)+'\n');Path(str(out)+'.sha256').write_text(digest(out)+'\n')
print(json.dumps({'status':result['status'],'save_files':len(rows),'sha256':digest(out)}))
