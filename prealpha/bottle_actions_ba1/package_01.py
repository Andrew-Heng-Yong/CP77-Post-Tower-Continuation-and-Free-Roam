"""Pin BA1's complete package, unchanged 64-source compile inputs and fixtures."""
from pathlib import Path
from hashlib import sha256
import argparse
import json
import zipfile

H=Path(__file__).resolve().parent
W=H.parents[1]
C=H/'candidate_01'
B=W/'prealpha/coaster_cutoff_cc1/candidate_01'
G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Cyberpunk 2077')
S=Path(r'C:\Users\Ayong\Saved Games\CD Projekt Red\Cyberpunk 2077')
digest=lambda p:sha256(p.read_bytes()).hexdigest().upper()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
parser=argparse.ArgumentParser()
parser.add_argument('--semantic-proof',required=True)
parser.add_argument('--proof',action='append',default=[])
args=parser.parse_args()
semantic=Path(args.semantic_proof).resolve()
assert semantic.is_relative_to(H), 'Semantic proof must be inside BA1 workspace'
verified=read(semantic)
assert str(verified['status']).startswith('PASS'), 'Independent owner verification not passed'
mp=C/'install_manifest_01.json'
for p in [mp,C/'zip_proof_01.json',C/'save_baseline_01.json',C/'compile_reuse_01.json',C/'dist']:
    assert not p.exists(),f'Preserve previous evidence: {p}'
old=read(B/'install_manifest_01.json')
packed=read(C/'package_proof_01.json')
owner=read(C/'owner_proof_01.json')
compiled=read(B/'compile_01/result.json')
assert packed['status']=='BA1_51_PATH_ARCHIVE_READBACK_PASS'
assert packed['archive_members']==1186 and packed['unchanged_members']==1185
assert packed['reds_changed']==0 and packed['xl_append_only'] and not packed['collisions']
assert owner['status']=='BA1_OWNER_SERIALIZED'
assert compiled['status']=='PASS' and compiled['source_count']==64
assert old['archive_members']==1185 and len(old['package_files'])==51
P=C/'package'
changes={'archive/pc/mod/zzzz_PTFR_Combined.archive','archive/pc/mod/zzzz_PTFR_Combined.archive.xl'}
files=[]
for row in old['package_files']:
    rel=row['path']
    assert digest(B/'package'/rel)==row['after'],rel
    assert digest(G/rel)==row['after'],f'Installed drift: {rel}'
    after=digest(P/rel)
    assert (after!=row['after'])==(rel in changes),rel
    files.append({'path':rel,'before':row['after'],'after':after})
assert len(files)==51==sum(p.is_file() for p in P.rglob('*'))
assert {p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file()}=={r['path'] for r in files}
assert packed['archive_sha256']==digest(P/'archive/pc/mod/zzzz_PTFR_Combined.archive')
dep=packed['new_resource']
assert digest(C/'source'/dep)==digest(C/'archive_source'/dep)==packed['new_resource_sha256']
assert verified['candidate_sha256']==packed['new_resource_sha256'],'Independent semantic proof refers to different resource'
for row in verified['pins']:
    assert digest(Path(row['path']))==row['sha256'],'Independent semantic input changed: '+row['path']
assert len(packed['checked_members'])==1186
for row in packed['checked_members']:
    assert digest(C/'archive_source'/row['depot'])==row['sha256'],row['depot']

# Reuse the actual CC1 compile only when all 64 source bytes and their set match.
roots={'game':G/'r6/scripts','Codeware':G/'red4ext/plugins/Codeware/Scripts',
       'ArchiveXL':G/'red4ext/plugins/ArchiveXL/Scripts','TweakXL':G/'red4ext/plugins/TweakXL/Scripts',
       'mod_settings':G/'red4ext/plugins/mod_settings'}
archived=B/'compile_01/scripts'
compiled_sources={p.relative_to(archived).as_posix():p for p in archived.rglob('*.reds')}
current_sources={name+'/'+p.relative_to(root).as_posix():p for name,root in roots.items() for p in root.rglob('*.reds')}
assert compiled_sources.keys()==current_sources.keys() and len(current_sources)==64,'Compile source inventory drift'
inputs=[]
for key,current in current_sources.items():
    h=digest(current)
    assert h==digest(compiled_sources[key]),'Compiled/current source differs: '+key
    package_source=P/'r6/scripts'/key.removeprefix('game/')
    if key.startswith('game/PTFR_Consolidated/'):
        assert digest(package_source)==h,'Candidate script differs: '+key
    inputs.append({'source':str(current),'compiled_source':str(compiled_sources[key]),'sha256':h})
reuse={'status':'PASS_EXACT_64_SOURCE_CC1_COMPILE_REUSE','source_count':64,'compile_result':str(B/'compile_01/result.json'),
       'compile_result_sha256':digest(B/'compile_01/result.json'),'compiled_cache_sha256':digest(B/'compile_01/cache/compiled.redscripts'),
       'candidate_reds_unchanged':True,'inputs':inputs,'game_writes':0,'save_writes':0}
rp=C/'compile_reuse_01.json';rp.write_text(json.dumps(reuse,indent=2)+'\n')
proofs=[C/'package_proof_01.json',C/'owner_proof_01.json',semantic,rp,B/'install_manifest_01.json',B/'compile_01/result.json',
        H/'build_owner_01.ps1',H/'package_01.ps1',H/'package_01.py',H/'derive_deploy_01.py',H/'deploy_01.ps1',H/'test_deploy_01.py',H/'postinstall_verify_01.py']
proofs.extend(Path(p).resolve() for p in args.proof)
proofs.extend(Path(p['path']) for p in verified['pins'])
proofs.extend(compiled_sources.values())
proofs=list(dict.fromkeys(proofs))
manifest={'status':'BA1_51_PATH_SUCCESSOR_STAGED_NOT_INSTALLED','game_root':str(G),'backup_root':str(W/'recovery/bottle_actions_ba1_01'),
          'full_package_count':51,'changed_paths':2,'archive_members':1186,'package_files':files,'retired':[],
          'proofs':[{'path':str(p),'sha256':digest(p)} for p in proofs],
          'runtime_inputs':[{'path':p.relative_to(G).as_posix(),'sha256':digest(p)} for p in current_sources.values()],
          'external_archives':[{'path':Path(r['path']).relative_to(G).as_posix(),'sha256':r['sha256']} for r in packed['archive_inventory'] if Path(r['path']).name!='zzzz_PTFR_Combined.archive'],
          'scope':'One isolated native bottle action controller for W3 group 179, gated by Tower and existing owner eligibility; no W3 restart, native facts or AI role reset.',
          'compile_reused':True,'game_writes':0,'save_writes':0,'public_release':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
Path(str(mp)+'.sha256').write_text(digest(mp)+'\n')
dist=C/'dist';dist.mkdir()
zp=dist/'Post-Tower-Continuation-and-Free-Roam-BA1-unreleased.zip'
with zipfile.ZipFile(zp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for row in files:z.write(P/row['path'],row['path'])
with zipfile.ZipFile(zp) as z:
    assert z.namelist()==[r['path'] for r in files]
    for row in files:assert sha256(z.read(row['path'])).hexdigest().upper()==row['after']
zz=C/'zip_proof_01.json'
zz.write_text(json.dumps({'status':'UNRELEASED_FULL_51_PATH_ZIP_VERIFIED','path':str(zp),'sha256':digest(zp),'members':51,'public_release':False,'game_writes':0},indent=2)+'\n')
Path(str(zz)+'.sha256').write_text(digest(zz)+'\n')
snapshot={'status':'BEFORE_BA1_INSTALL_READ_ONLY_CAPTURE','files':[]}
savepaths=sorted(p for p in S.rglob('*') if p.is_file())
for p in savepaths:snapshot['files'].append({'path':str(p.relative_to(S)),'sha256':digest(p),'size':p.stat().st_size})
assert savepaths==sorted(p for p in S.rglob('*') if p.is_file()),'Save inventory changed during capture'
assert all(digest(S/r['path'])==r['sha256'] for r in snapshot['files']),'Save changed during capture'
sp=C/'save_baseline_01.json';sp.write_text(json.dumps(snapshot,indent=2)+'\n')
Path(str(sp)+'.sha256').write_text(digest(sp)+'\n')
print(json.dumps({'status':manifest['status'],'manifest_sha256':digest(mp),'zip_sha256':digest(zp),'save_files':len(snapshot['files']),'compile_reuse_sources':64}))
