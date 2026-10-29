import hashlib,json,zipfile
from pathlib import Path
W=Path(__file__).resolve().parents[2]
R=W/'prealpha/credits_cover_lc4'
C=R/'candidate_02'
B=W/'prealpha/world_support_wa3/candidate_02'
G=Path('C:/Program Files (x86)/Steam/steamapps/common/Cyberpunk 2077')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
b=read(B/'install_manifest_01.json');build=read(C/'build_01.json')
assert len(build['package_files'])==51
assert sha(G/'archive/pc/mod/zzzz_PTFR_Combined.archive')==build['base_archive_sha256']
old={x['path']:x for x in b['package_files']}
files=[]
for x in sorted(build['package_files'],key=lambda v:v['path']):
    row=dict(path=x['path'],before=old[x['path']]['after'],after=x['after'])
    assert sha(G/row['path'])==row['before']
    assert sha(C/'package'/row['path'])==row['after']
    files.append(row)
assert [x['path'] for x in files if x['before']!=x['after']]==['archive/pc/mod/zzzz_PTFR_Combined.archive']
co=b['compatibility_files'][0].copy();co['before']=co['after']
assert sha(G/co['path'])==co['after']
runtime=[]
for x in b['runtime_inputs']:
    actual=sha(G/x['path'])
    if actual!=x['sha256']:
        assert x['path'] in ('r6/scripts/PTFR_Consolidated/PTFR_RestorationBaseline.reds','r6/scripts/virtual-atelier-full/SetupNewTab.reds')
    runtime.append(dict(path=x['path'],sha256=actual))
assert len(runtime)==112
archives=sorted(p.relative_to(G).as_posix() for p in (G/'archive/pc').rglob('*.archive'))
externals=[dict(path=p,sha256=sha(G/p)) for p in archives if p!='archive/pc/mod/zzzz_PTFR_Combined.archive']
save_root=Path.home()/'Saved Games/CD Projekt Red/Cyberpunk 2077'
assert save_root.is_dir(),save_root
saves=[dict(path=p.relative_to(save_root).as_posix(),sha256=sha(p),size=p.stat().st_size) for p in sorted(save_root.rglob('*')) if p.is_file()]
write(C/'save_baseline_01.json',dict(status='READ_ONLY_BEFORE_LC4_INSTALL',root=str(save_root),files=saves))
proofs=[dict(path=str(C/'build_01.json'),sha256=sha(C/'build_01.json')),
        dict(path=str(C/'save_baseline_01.json'),sha256=sha(C/'save_baseline_01.json')),
        dict(path=str(B/'compile_01/result.json'),sha256=sha(B/'compile_01/result.json'))]
m=dict(status='LC4_FULL_51_PATH_SUCCESSOR_STAGED',game_root=str(G),backup_root=str(W/'recovery/credits_cover_lc4_01'),
    package_files=files,compatibility_files=[co],changed_paths=1,managed_paths=52,archive_members=1563,
    runtime_inputs=runtime,external_archives=externals,proofs=proofs,
    compilation='Reused exact112-source WA3 compiled stack; every current source hash checked.',
    game_writes=0,save_writes=0,public_release=False)
write(C/'install_manifest_01.json',m)
(C/'install_manifest_01.json.sha256').write_text(sha(C/'install_manifest_01.json')+'\n')
zip_path=C/'dist/PTFR_credits_cover_lc4_full_51.zip';zip_path.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for x in files:z.write(C/'package'/x['path'],x['path'])
with zipfile.ZipFile(zip_path) as z:
    assert set(z.namelist())=={x['path'] for x in files}
    assert all(hashlib.sha256(z.read(x['path'])).hexdigest().upper()==x['after'] for x in files)
write(C/'zip_proof_01.json',dict(status='FULL_51_PATH_ZIP_READBACK_PASS',path=str(zip_path),sha256=sha(zip_path),members=51))
print(json.dumps(dict(status='PREPARED',archive_sha256=build['archive_sha256'],full_paths=51,managed_paths=52,replacements=1,runtime_sources=len(runtime),archive_inputs=len(archives),save_files=len(saves),zip_sha256=sha(zip_path))))
