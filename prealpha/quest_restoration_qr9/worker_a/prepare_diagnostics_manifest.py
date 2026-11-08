"""Bind the separately reviewed optional addon; no game/save reads or writes."""
from pathlib import Path
import json, hashlib
H=Path(__file__).resolve().parent
R=H.parent
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper()
baseline_path=R/'baseline.json'
baseline=json.loads(baseline_path.read_text())
addon_path=R/'worker_b/addon_manifest_04.json'
assert sha(addon_path)=='59B3CE96220B807D87AF67B66A47ED02549D66B59A5BEA8F620C2910D55C0580'
addon=json.loads(addon_path.read_text())
cet=next(x for x in baseline['external_dependencies'] if x['path']=='bin/x64/plugins/cyber_engine_tweaks.asi')
assert len(addon['dependencies'])==1 and addon['dependencies'][0]['sha256']==cet['sha256']
files=[]
for row in addon['files']:
    src=Path(addon['source_root'])/row['path']
    assert row['before']=='ABSENT_REQUIRED' and sha(src)==row['sha256'] and src.stat().st_size==row['bytes']
    files.append(dict(path=row['path'],before=None,before_bytes=0,after=row['sha256'],after_bytes=row['bytes']))
m=dict(schema='PTFR_QR9_COMPONENT_V1',component='Diagnostics',status='PREPARED_NOT_INSTALLED',
       source_epoch='QR8:02',game_root=baseline['game_root'],save_root=baseline['save_root'],
       package_root=addon['source_root'],zip='',zip_sha256=None,files=files,
       changing_paths=[r['path'] for r in files],
       required_files=[dict(path=cet['path'],sha256=cet['sha256'],bytes=cet['bytes'],active_only=False)],
       proofs=[dict(path=str(p.resolve()),sha256=sha(p)) for p in [baseline_path,addon_path,R/'worker_b/api_proof_02.json',R/'worker_b/verification_04/result.json']],
       process_names=['Cyberpunk2077','REDprelauncher','REDlauncher'],
       installed_core_observation='NOT_OBSERVED_BY_CET; separate Core Verify receipt is required before gameplay.',
       expected_core=dict(epoch='QR8:02',files=[dict(path=x['path'],sha256=x['after']) for x in baseline['core_files'] if x['changing']]),
       rollback_policy='Remove only the exact unchanged two addon files; retain JSONL logs, unknown files and all directories. Never recursively delete.',
       runtime_limits=addon['active_dependencies_scope'])
out=H/'diagnostics_manifest_01.json'
assert not out.exists()
out.write_text(json.dumps(m,indent=2)+'\n',encoding='utf8')
out.with_suffix('.sha256').write_text(sha(out)+'\n',encoding='ascii')
print(json.dumps(dict(path=str(out),sha256=sha(out),managed_paths=len(files),game_writes=0,save_writes=0)))
