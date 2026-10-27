"""Pin a complete 51-path CC1 successor and the current closed-game baseline."""
from pathlib import Path
from hashlib import sha256
import json
import zipfile

H=Path(__file__).resolve().parent
W=H.parents[1]
C=H/'candidate_01'
B=W/'prealpha/skippy_ambient_sc3/candidate_02'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
old=read(B/'install_manifest_01.json')
build=read(C/'build_01.json')
verified=read(C/'verification_01.json')
compiled=read(C/'compile_01/result.json')
assert build['status']=='CC1_STAGED_NOT_INSTALLED' and verified['status']=='PASS_TWO_CUTOFF_GUARDS_ONLY'
assert compiled['status']=='PASS' and compiled['source_count']==64
assert old['archive_members']==1185 and len(old['package_files'])==51
P=C/'package'
changes={'archive/pc/mod/zzzz_PTFR_Combined.archive','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds'}
files=[]
for row in old['package_files']:
    rel=row['path']
    assert digest(B/'package'/rel)==row['after'],rel
    assert digest(G/rel)==row['after'],f'installed drift: {rel}'
    after=digest(P/rel)
    assert (after!=row['after'])==(rel in changes),rel
    files.append({'path':rel,'before':row['after'],'after':after})
assert len(files)==51==sum(p.is_file() for p in P.rglob('*'))
assert read(C/'build_01.json')['archive_sha256']==digest(P/'archive/pc/mod/zzzz_PTFR_Combined.archive')
assert read(C/'compile_01/result.json')['candidate_sha256']==digest(P/'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS29.reds')
proofs=[C/'build_01.json',C/'verification_01.json',C/'compile_01/result.json',H/'build_01.ps1',H/'verify_01.ps1',H/'verify_01.py',H/'compile_01.py',H/'package_01.py']
manifest={'status':'CC1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','game_root':str(G),'backup_root':str(W/'recovery/coaster_cutoff_cc1_01'),'full_package_count':51,'changed_paths':2,'archive_members':1185,'package_files':files,'retired':[],'proofs':[{'path':str(p),'sha256':digest(p)} for p in proofs],'scope':'Block new one-time Jean Love Rollercoaster entry after q105 completion; preserve current issued story and repeatable ride.','game_writes':0,'save_writes':0,'public_release':False}
mp=C/'install_manifest_01.json'
mp.write_text(json.dumps(manifest,indent=2)+'\n')
Path(str(mp)+'.sha256').write_text(digest(mp)+'\n')
dist=C/'dist';dist.mkdir(exist_ok=False)
zp=dist/'Post-Tower-Continuation-and-Free-Roam-CC1-unreleased.zip'
with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for row in files:z.write(P/row['path'],row['path'])
with zipfile.ZipFile(zp) as z:
    assert z.namelist()==[r['path'] for r in files]
    for row in files:assert sha256(z.read(row['path'])).hexdigest().upper()==row['after']
zz=C/'zip_proof_01.json'
zz.write_text(json.dumps({'status':'UNRELEASED_FULL_51_PATH_ZIP_VERIFIED','path':str(zp),'sha256':digest(zp),'members':51,'public_release':False,'game_writes':0},indent=2)+'\n')
Path(str(zz)+'.sha256').write_text(digest(zz)+'\n')
snapshot={'status':'BEFORE_CC1_INSTALL','files':[]}
for p in sorted(S.rglob('*')):
    if p.is_file():snapshot['files'].append({'path':str(p.relative_to(S)),'sha256':digest(p),'size':p.stat().st_size})
sp=C/'save_baseline_01.json'
sp.write_text(json.dumps(snapshot,indent=2)+'\n')
Path(str(sp)+'.sha256').write_text(digest(sp)+'\n')
print(json.dumps({'status':manifest['status'],'manifest_sha256':digest(mp),'zip_sha256':digest(zp),'save_files':len(snapshot['files'])}))
