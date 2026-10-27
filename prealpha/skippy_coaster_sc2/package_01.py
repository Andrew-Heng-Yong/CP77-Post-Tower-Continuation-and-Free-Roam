"""Full 51-path SC2 successor, changing only the S23 REDscript file."""
from hashlib import sha256
from pathlib import Path
import json
import shutil
import zipfile

H=Path(__file__).resolve().parent
W=H.parents[1]
B=W/'prealpha/skippy_coaster_sc1/candidate_07'
C=H/'candidate_01'
P=C/'package'
GAME=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
assert not P.exists()
source=C/'script_source/PTFR_SideJobsS23.reds'
compile=json.loads((C/'compile_01/result.json').read_text())
assert compile['status']=='PASS' and compile['source_count']==64
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
assert digest(source)==compile['candidate_sha256']
old=json.loads((B/'install_manifest_01.json').read_text())
assert len(old['package_files'])==51
for f in old['package_files']:
 assert digest(GAME/f['path'])==f['after'],('Installed SC1 drift',f['path'])
shutil.copytree(B/'package',P)
path='r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'
shutil.copyfile(source,P/path)
files=[]
for f in old['package_files']:
 before=f['after'];after=digest(P/f['path'])
 assert (before!=after)==(f['path']==path),f['path']
 files.append({'path':f['path'],'before':before,'after':after})
assert len([x for x in P.rglob('*') if x.is_file()])==51
proof={'status':'SC2_51_PATH_CANDIDATE_PACKED_NOT_INSTALLED','base_package_paths':51,'new_package_paths':51,'changed_paths':[path],'archive_sha256':digest(P/'archive/pc/mod/zzzz_PTFR_Combined.archive'),'xl_sha256':digest(P/'archive/pc/mod/zzzz_PTFR_Combined.archive.xl'),'archive_members_unchanged':1184,'script_sha256':digest(P/path),'game_writes':0,'save_writes':0}
(C/'package_proof_01.json').write_text(json.dumps(proof,indent=2)+'\n')
evidence=[C/'script_proof_01.json',C/'compile_01/result.json',C/'package_proof_01.json',W/'prealpha/skippy_coaster_sc1/candidate_04/cooked_scene_semantics_01.json',B/'collisions_01.json']
assert all(x.is_file() for x in evidence)
m={'status':'SC2_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','game_root':str(GAME),'backup_root':str(W/'recovery/skippy_coaster_sc2_01'),'full_package_count':51,'changed_paths':1,'archive_members':1184,'package_files':files,'retired':[],'proofs':[{'path':str(x),'sha256':digest(x)} for x in evidence],'game_writes':0,'save_writes':0,'public_release':False}
manifest=C/'install_manifest_01.json'
manifest.write_text(json.dumps(m,indent=2)+'\n')
Path(str(manifest)+'.sha256').write_text(digest(manifest)+'\n')
dist=C/'dist';dist.mkdir(exist_ok=False)
zip_path=dist/'Post-Tower-Continuation-and-Free-Roam-SC2-unreleased.zip'
with zipfile.ZipFile(zip_path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for f in files:z.write(P/f['path'],f['path'])
with zipfile.ZipFile(zip_path) as z:
 assert z.namelist()==[f['path'] for f in files]
 assert all(sha256(z.read(f['path'])).hexdigest().upper()==f['after'] for f in files)
zp=C/'zip_proof_01.json'
zp.write_text(json.dumps({'status':'UNRELEASED_FULL_51_PATH_ZIP_VERIFIED','path':str(zip_path),'sha256':digest(zip_path),'members':51,'public_release':False,'game_writes':0},indent=2)+'\n')
Path(str(zp)+'.sha256').write_text(digest(zp)+'\n')
print(json.dumps({'status':m['status'],'paths':len(files),'changed':1,'zip_sha256':digest(zip_path)}))
