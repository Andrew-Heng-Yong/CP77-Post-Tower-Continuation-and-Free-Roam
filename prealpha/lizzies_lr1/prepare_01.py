import hashlib,json,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_02'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
assert read(C/'verification_01.json')['status']=='PASS_FULL_ARCHIVE_READBACK_NO_COLLISION'
paths=sorted(p.relative_to(C/'package').as_posix() for folder in ('archive','bin','r6') for p in (C/'package'/folder).rglob('*') if p.is_file())
assert len(paths)==51
rows=[]
for path in paths:
    src=C/'package'/path;dst=G/path
    rows.append({'path':path,'before':sha(dst),'after':sha(src),'bytes':src.stat().st_size})
changed=[x for x in rows if x['before']!=x['after']]
assert {x['path'] for x in changed}=={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'}
assert rows[0]['path'].startswith('archive/')
external=G/'archive/pc/mod/LizziesBDs.archive'
assert sha(external)==read(C/'verification_01.json')['external_lizzies_archive_sha256']
saves=[{'path':p.relative_to(S).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(S.rglob('*')) if p.is_file()]
write(C/'save_baseline_01.json',{'root':str(S),'files':saves,'status':'READ_ONLY_BEFORE_INSTALL'})
manifest={'status':'LR1_STAGED_51_PATH_SUCCESSOR','game_root':str(G),'backup_root':str(W/'recovery/lizzies_lr1_01'),'package_files':rows,'changed_paths':[x['path'] for x in changed],
          'external_lizzies_archive_sha256':sha(external),'archive_members':1565,'source_archive_sha256':sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive'),
          'source_xl_sha256':sha(C/'package/archive/pc/mod/zzzz_PTFR_Combined.archive.xl'),
          'validation_sha256':sha(C/'verification_01.json'),'save_baseline_sha256':sha(C/'save_baseline_01.json'),'game_writes':0,'save_writes':0,'live_result':'pending'}
write(C/'install_manifest_01.json',manifest)
(C/'install_manifest_01.json.sha256').write_text(sha(C/'install_manifest_01.json')+'\n')
zp=C/'PTFR_lizzies_lr1_full_51.zip'
with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for path in paths:z.write(C/'package'/path,path)
with zipfile.ZipFile(zp) as z:
    assert len(z.namelist())==51 and z.testzip() is None
    for row in rows:assert hashlib.sha256(z.read(row['path'])).hexdigest().upper()==row['after']
write(C/'zip_proof_01.json',{'status':'PASS_FULL_51_PATH_READBACK','path':str(zp),'sha256':sha(zp),'members':51})
print(json.dumps({'status':manifest['status'],'package_files':51,'replacements':len(changed),'save_files':len(saves),'zip_sha256':sha(zp)}))
