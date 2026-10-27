"""Capture current baseline and stage a full successor without game writes."""
import shutil
from datetime import datetime,timezone
from common import *
assert not CANDIDATE.exists(),'Use successor candidate'
old=read(PRIOR/'manifest.json')
assert len(old['files'])==51
for r in old['files']:
    assert sha(GAME/r['path'])==r['sha256'],r['path']
    assert sha(PRIOR/'package'/r['path'])==r['sha256'],r['path']
resources=read(AUDIT/'current_resources_01.json')['members'];assert len(resources)==1172
for r in resources:assert sha(PRIOR/'archive_source'/r['depot'])==r['sha256'],r['depot']
rows=[{'path':str(p),'sha256':sha(p),'save':p.is_relative_to(SAVES)} for p in protected_paths()]
CANDIDATE.mkdir()
write_new(CANDIDATE/'baseline_01.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'files':rows,'save_count':sum(r['save'] for r in rows),'protected_count':len(rows),'prior_manifest_sha256':sha(PRIOR/'manifest.json'),'package_files':old['files'],'resources':resources})
shutil.copytree(PRIOR/'archive_source',CANDIDATE/'archive_source')
shutil.copytree(PRIOR/'package',CANDIDATE/'package')
shutil.copytree(PRIOR/'package',CANDIDATE/'archived_previous')
print(f'Staged 51 files,1172 resources; protected {len(rows)} files, {sum(r["save"] for r in rows)} saves. No game writes.')
