"""Pin the full 51-path Skippy/coaster successor and local unreleased ZIP."""
from hashlib import sha256
from pathlib import Path
import json
import zipfile

H=Path(__file__).resolve().parent
W=H.parents[1]
C=H/'candidate_07'
P=C/'package'
B=W/'prealpha/world_workspots_w2/candidate_04'
old=json.loads((B/'install_manifest_01.json').read_text())
out=C/'install_manifest_01.json'
assert not out.exists()
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
replacements={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'}
files=[]
for f in old['package_files']:
 path=f['path'];before=f['after']
 assert digest(B/'package'/path)==before
 after=digest(P/path)
 assert (before!=after)==(path in replacements),path
 files.append({'path':path,'before':before,'after':after})
assert len(files)==51==len([p for p in P.rglob('*') if p.is_file()])
evidence=[H/'candidate_04/cooked_scene_semantics_01.json',H/'candidate_05/compile_01/result.json',H/'candidate_06/skippy_owner_proof_01.json',C/'package_proof_01.json',C/'collisions_01.json']
assert all(p.is_file() for p in evidence)
m={'status':'SC1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','game_root':old['game_root'],'backup_root':str(W/'recovery/skippy_coaster_sc1_01'),'full_package_count':51,'changed_paths':3,'archive_members':1184,'package_files':files,'retired':[],'proofs':[{'path':str(p),'sha256':digest(p)} for p in evidence],'game_writes':0,'save_writes':0,'live_scope':'Skippy ambient and Johnny-free MQ006 finale await user gameplay acceptance; W3 hostile NPC fix retained','public_release':False}
out.write_text(json.dumps(m,indent=2)+'\n')
Path(str(out)+'.sha256').write_text(digest(out)+'\n')
dist=C/'dist';dist.mkdir(exist_ok=False)
zip_path=dist/'Post-Tower-Continuation-and-Free-Roam-SC1-unreleased.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(P/f['path'],f['path'])
with zipfile.ZipFile(zip_path) as z:
 assert z.namelist()==[f['path'] for f in files]
 assert all(sha256(z.read(f['path'])).hexdigest().upper()==f['after'] for f in files)
zp=C/'zip_proof_01.json'
zp.write_text(json.dumps({'status':'UNRELEASED_FULL_51_PATH_ZIP_VERIFIED','path':str(zip_path),'sha256':digest(zip_path),'members':51,'public_release':False,'game_writes':0},indent=2)+'\n')
Path(str(zp)+'.sha256').write_text(digest(zp)+'\n')
print(json.dumps({'manifest_sha256':digest(out),'zip_sha256':digest(zip_path),'paths':len(files)}))
