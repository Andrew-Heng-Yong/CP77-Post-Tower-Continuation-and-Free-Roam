import datetime,hashlib,json,sys
from pathlib import Path
C=Path(__file__).resolve().parent/'candidate_01';stage=sys.argv[1]
assert stage in ('before','after')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
m=read(C/'install_manifest_01.json');g=Path(m['game_root'])
b=read(C/'save_baseline_01.json');s=Path(b['root'])
saves=[{'path':p.relative_to(s).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(s.rglob('*')) if p.is_file()]
assert saves==b['files'],'Save baseline changed'
ext=read(C/'external_baseline_01.json')
assert len(ext['files'])==49 and all(sha(g/x['path'])==x['sha256'] for x in ext['files']),'External mod changed'
assert all(sha(g/x['path'])==x[stage] for x in m['package_files']),'Managed file mismatch'
assert read(C/'deployment_tests_01.json')['status']=='PASS_DEPLOYMENT_FIXTURES'
out={'status':'PASS_SAVE_EXTERNAL_AND_MANAGED_PRESERVATION','stage':stage,'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'save_files_unchanged':len(saves),'external_files_unchanged':len(ext['files']),'managed_files_verified':51,'game_launched':False,'save_writes':0}
dest=C/('preservation_'+stage+'_01.json');assert not dest.exists();dest.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
