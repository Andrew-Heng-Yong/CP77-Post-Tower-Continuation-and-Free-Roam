"""Seal the reviewed SC3 candidate and full unreleased distribution."""
from pathlib import Path
import json,hashlib,zipfile
H=Path(__file__).resolve().parent;W=H.parents[1]
C=H/'candidate_02';P=C/'package';B=W/'prealpha/skippy_coaster_sc2/candidate_01'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest().upper()
out=C/'install_manifest_01.json';assert not out.exists()
old=read(B/'install_manifest_01.json')
graph=read(H/'native_review/candidate_02/native_graphs_01.json')
payload=read(H/'native_review/candidate_02/payload_checks_01.json')
runtime=read(H/'runtime_review/verification_01.json')
assert graph['status']=='PASS_NATIVE_GRAPHS' and graph['graphs']==6 and graph['edges']==73
assert payload['status']=='PASS_SC3_NATIVE_LIFECYCLE_STATIC_NOT_LIVE' and payload['checks']==74
assert runtime['status']=='PASS_INDEPENDENT_SC3_LIFECYCLE_SOURCE_AND_SAVED_STATE_NOT_LIVE'
assert runtime['negative_controls']==3 and all(r['passed'] for r in runtime['results'])
for pin in runtime['pins']:assert sha(W/pin['path'])==pin['sha256'],pin['path']
for pin in read(H/'native_review/assessment_01.json')['pins']:
 assert sha(H/'native_review'/pin['path'])==pin['sha256'],pin['path']
packed=read(C/'package_proof_01.json')
assert packed['status']=='SC3_51_PATH_ARCHIVE_READBACK_PASS' and packed['unchanged_members']==1184
assert packed['archive_members']==1185 and packed['new_resource_sha256']=='E9A06A80006EEA94ECF74D074B74942268DB42D5E4E50A3093BF5C71FA156B19'
assert read(C/'dependency_winners_01.json')['status']=='PASS_NO_INSTALLED_MOD_OVERRIDES'
assert sha(P/'r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds')==read(C/'compile_01/result.json')['candidate_sha256']
replacements={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl','r6/scripts/PTFR_Consolidated/PTFR_SideJobsS23.reds'}
files=[]
for row in old['package_files']:
 path=row['path'];assert sha(B/'package'/path)==row['after']
 after=sha(P/path);assert (after!=row['after'])==(path in replacements),path
 files.append({'path':path,'before':row['after'],'after':after})
assert len(files)==51==len([p for p in P.rglob('*') if p.is_file()])
evidence=[C/'script_proof_01.json',C/'compile_01/result.json',C/'package_proof_01.json',C/'dependency_winners_01.json',
 H/'native_review/assessment_01.json',H/'native_review/candidate_02/owner_proof_01.json',
 H/'native_review/candidate_02/native_graphs_01.json',H/'native_review/candidate_02/payload_checks_01.json',
 H/'runtime_review/verification_01.json',H/'deploy_02.ps1',H/'test_deploy_02.py']
m={'status':'SC3_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','game_root':old['game_root'],
 'backup_root':str(W/'recovery/skippy_ambient_sc3_01'),'full_package_count':51,'changed_paths':3,
 'archive_members':1185,'package_files':files,'retired':[],
 'proofs':[{'path':str(p),'sha256':sha(p)} for p in evidence],
 'live_scope':'Fix source-proven Skippy terminal unequip lifecycle and saved receipt dead-end; audible/visible result untested.',
 'game_writes':0,'save_writes':0,'public_release':False}
out.write_text(json.dumps(m,indent=2)+'\n');Path(str(out)+'.sha256').write_text(sha(out)+'\n')
dist=C/'dist';dist.mkdir(exist_ok=False)
zpath=dist/'Post-Tower-Continuation-and-Free-Roam-SC3-unreleased.zip'
with zipfile.ZipFile(zpath,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for row in files:z.write(P/row['path'],row['path'])
with zipfile.ZipFile(zpath) as z:
 assert z.namelist()==[r['path'] for r in files]
 for row in files:assert hashlib.sha256(z.read(row['path'])).hexdigest().upper()==row['after']
zp=C/'zip_proof_01.json'
zp.write_text(json.dumps({'status':'UNRELEASED_FULL_51_PATH_ZIP_VERIFIED','path':str(zpath),'sha256':sha(zpath),'members':51,'public_release':False,'game_writes':0},indent=2)+'\n')
Path(str(zp)+'.sha256').write_text(sha(zp)+'\n')
print(json.dumps({'status':m['status'],'manifest_sha256':sha(out),'zip_sha256':sha(zpath),'native_checks':74,'runtime_checks':runtime['checks']}))
