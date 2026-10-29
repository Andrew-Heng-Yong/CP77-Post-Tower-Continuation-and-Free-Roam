"""Pin the complete VD1 successor, unchanged compiler inputs and save baseline."""
import hashlib,json,shutil,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];C=H/'candidate_02'
B=W/'prealpha/credits_cover_lc4/candidate_02'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest().upper()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
assert not (C/'install_manifest_01.json').exists()
b=read(B/'install_manifest_01.json');build=read(C/'build_01.json');verify=read(C/'verification_01.json')
assert verify['status']=='PASS_INDEPENDENT_SERIALIZED_OWNER_CHECKS'
assert len(build['package_files'])==51
for row in build['package_files']:
    assert sha(G/row['path'])==row['before'],('Installed drift',row['path'])
    assert sha(C/'package'/row['path'])==row['after']
assert {p.relative_to(C/'package').as_posix() for p in (C/'package').rglob('*') if p.is_file()}=={x['path'] for x in build['package_files']}
roots={'game':G/'r6/scripts','Codeware':G/'red4ext/plugins/Codeware/Scripts','ArchiveXL':G/'red4ext/plugins/ArchiveXL/Scripts','TweakXL':G/'red4ext/plugins/TweakXL/Scripts','mod_settings':G/'red4ext/plugins/mod_settings'}
current={prefix+'/'+p.relative_to(root).as_posix():p for prefix,root in roots.items() for p in root.rglob('*.reds')}
compiled=W/'prealpha/world_support_wa3/candidate_02/compile_01'
staged={p.relative_to(compiled/'scripts').as_posix():p for p in (compiled/'scripts').rglob('*.reds')}
assert current.keys()==staged.keys() and len(current)==112
for key,path in current.items():assert sha(path)==sha(staged[key]),('Compiled source mismatch',key)
result=read(compiled/'result.json')
assert result['status']=='PASS' and sha(compiled/'cache/compiled.redscripts')==result['compiled_sha256']
reuse={'status':'PASS_EXACT_112_SOURCE_COMPILE_REUSE','source_count':112,'result_sha256':sha(compiled/'result.json'),'cache_sha256':result['compiled_sha256'],'inputs':[{'path':p.relative_to(G).as_posix(),'sha256':sha(p)} for p in current.values()]}
write(C/'compile_inputs_01.json',reuse)
actual_archives={p.relative_to(G).as_posix() for p in (G/'archive/pc').rglob('*.archive')}
assert actual_archives=={x['path'] for x in b['external_archives']}|{'archive/pc/mod/zzzz_PTFR_Combined.archive'}
for row in b['external_archives']:assert sha(G/row['path'])==row['sha256'],('External archive drift',row['path'])
for row in b['compatibility_files']:assert sha(G/row['path'])==row['after']
saves=[{'path':p.relative_to(S).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(S.rglob('*')) if p.is_file()]
write(C/'save_baseline_01.json',{'status':'READ_ONLY_BEFORE_VD1_INSTALL','root':str(S),'files':saves})
diagnostics=W/'diagnostics/viktor_door_20261029_01/logs';diagnostics.mkdir(exist_ok=False)
for path in [G/'bin/x64/plugins/cyber_engine_tweaks/scripting.log',G/'r6/logs/redscript_rCURRENT.log']:
    shutil.copy2(path,diagnostics/path.name)
proofs=[C/'build_01.json',C/'verification_01.json',C/'compile_inputs_01.json',C/'save_baseline_01.json',H/'native_review_03/providers.json',H/'build_01.ps1',H/'verify_01.py',H/'deploy_01.ps1',compiled/'result.json']
manifest={'status':'VD1_FULL_51_PATH_SUCCESSOR_STAGED','game_root':str(G),'backup_root':str(W/'recovery/viktor_door_vd1_01'),'package_files':build['package_files'],'compatibility_files':b['compatibility_files'],'changed_paths':2,'managed_paths':52,'archive_members':1564,'runtime_inputs':reuse['inputs'],'external_archives':b['external_archives'],'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],'compilation':'Exact112-source WA3 compile reuse; every current source compared to compiled copy. No REDscript changes.','game_writes':0,'save_writes':0,'public_release':False}
write(C/'install_manifest_01.json',manifest)
(C/'install_manifest_01.json.sha256').write_text(sha(C/'install_manifest_01.json')+'\n')
dist=C/'dist';dist.mkdir()
zp=dist/'PTFR_viktor_door_vd1_full_51.zip'
with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for row in build['package_files']:z.write(C/'package'/row['path'],row['path'])
with zipfile.ZipFile(zp) as z:
    assert len(z.namelist())==51 and z.testzip() is None
    for row in build['package_files']:assert hashlib.sha256(z.read(row['path'])).hexdigest().upper()==row['after']
write(C/'zip_proof_01.json',{'status':'FULL_51_PATH_ZIP_READBACK_PASS','path':str(zp),'sha256':sha(zp),'members':51})
print(json.dumps({'status':manifest['status'],'files':51,'replacements':2,'compile_sources':112,'save_files':len(saves),'archives':len(actual_archives),'zip_sha256':sha(zp)}))
