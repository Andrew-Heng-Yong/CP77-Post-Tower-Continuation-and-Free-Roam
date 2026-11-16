"""Prepare a reviewed TP2 transaction and ZIP; no game/save writes."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
from capture import HERE, ROOT, BASELINE, BASELINE_SHA, sha, read, write, plain
from prepare import COVER, R1, one
BASE=ROOT/'prealpha/tower_presentation_tp1_20261112_01'
EPOCH='TP2_RETAINED_PRESENTATION_REPAIR';BEFORE='TP1_FPP_HANDBACK_DIAGNOSTIC'
SCHEMA='PTFR_TP2_RETAINED_PRESENTATION_REPAIR_CORE_V1'
CHANGES={COVER,R1};ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
PACKAGE=HERE/'candidate_03/package';MANIFEST=HERE/'core_manifest_01.json'
INSTALLER=HERE/'deploy_core.ps1';DEPLOYMENT=HERE/'deployment_01'
PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')

def exclusive(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    assert all(not p.exists() for p in (MANIFEST,INSTALLER,DEPLOYMENT,HERE/'fixtures',HERE/'recovery',HERE/'deploy.py'))
    assert sha(BASELINE)==BASELINE_SHA
    previous=read(BASELINE);game=Path(previous['game_root']);candidate=read(HERE/'candidate_03/manifest.json')
    assessment=read(HERE/'assessment_03.json');compiled=read(HERE/'compile_03/result.json')
    assert assessment['status']=='PASS_BOUNDED_STATIC_QUALIFICATION_LIVE_FIX_UNVERIFIED'
    assert assessment['candidate_manifest_sha256']==sha(HERE/'candidate_03/manifest.json')
    assert assessment['compile_sha256']==sha(HERE/'compile_03/result.json')
    assert compiled['status']=='PASS' and compiled['source_count']==148
    for n,h in assessment['source_pins'].items():assert sha(HERE/n)==h,n
    for row in previous['core_files']+previous['required_files']:plain(game/row['path']);assert sha(game/row['path'])==row['sha256']
    for rel,h in compiled['input_pins'].items():assert sha(game/rel)==h
    for rel,h in compiled['staged_hashes'].items():assert sha(PACKAGE/rel if (PACKAGE/rel).is_file() else game/rel)==h
    after={r['path']:r['sha256'] for r in candidate['files']};files=[]
    for row in previous['core_files']:
        p=PACKAGE/row['path'];plain(p);assert sha(p)==after[row['path']]
        files.append({'path':row['path'],'before':row['sha256'],'before_bytes':row['bytes'],'after':after[row['path']],'after_bytes':p.stat().st_size})
    assert len(files)==51 and {r['path'] for r in files if r['before']!=r['after']}==CHANGES
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()}==set(after)
    for folder in (DEPLOYMENT,HERE/'fixtures',HERE/'recovery'):folder.mkdir()
    zipfile=DEPLOYMENT/'TP2_candidate_03.zip'
    with ZipFile(zipfile,'x',ZIP_DEFLATED,compresslevel=6) as z:
        for row in files:z.write(PACKAGE/row['path'],row['path'])
    with ZipFile(zipfile) as z:
        assert len(z.namelist())==51 and set(z.namelist())==set(after) and z.testzip() is None
        assert all(hashlib.sha256(z.read(r['path'])).hexdigest().upper()==r['after'] for r in files)
    write(DEPLOYMENT/'zip_readback.json',{'status':'PASS','files':51,'sha256':sha(zipfile)})
    proofs=[BASELINE,HERE/'candidate_03/manifest.json',HERE/'assessment_03.json',HERE/'compile_03/result.json',DEPLOYMENT/'zip_readback.json']
    manifest={'schema':SCHEMA,'component':'Core','source_epoch':EPOCH,'predecessor_epoch':BEFORE,
        'scope':'Prepared two-script TP2 candidate: one-shot covered body refresh and ending loading-presentation cleanup. Gameplay unverified; installation requires separate user authorization. No game launch/save edit.',
        'game_root':str(game),'save_root':previous['save_root'],'package_root':str(PACKAGE),
        'process_names':read(BASE/'core_manifest_01.json')['process_names'],'files':files,'changing_paths':sorted(CHANGES),
        'required_files':previous['required_files'],'protected_saves':[],'working_save_files':[],
        'zip':str(zipfile),'zip_sha256':sha(zipfile),'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],
        'compile_inputs':{str(game/p):h for p,h in compiled['input_pins'].items()}}
    write(MANIFEST,manifest)
    template=BASE/'deploy_core.ps1';assert sha(template)=='97F26926411A0B0ECA51959B6C73837A29CEF6C615AB0AA00D1DD3143A4D72D7'
    source=template.read_text(encoding='utf-8-sig')
    for old,new in (
        ('# Replace exactly the two TP1 scripts after separate installation authorization.','# Replace exactly the two TP2 scripts after separate installation authorization.'),
        (sha(BASE/'core_manifest_01.json'),sha(MANIFEST)),
        ('PTFR_TP1_FPP_HANDBACK_DIAGNOSTIC_CORE_V1',SCHEMA),
        ("$manifest.source_epoch -cne 'TP1_FPP_HANDBACK_DIAGNOSTIC'",f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'RD1_EARNED_STAGE_RESUME'",f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_presentation_tp1_01','recovery/core_presentation_tp2_01'),
        ('Core51/two-script TP1 presentation scope drift','Core51/two-script TP2 presentation scope drift')):source=one(source,old,new)
    exclusive(INSTALLER,source)
    runner=BASE/'deploy.py';assert sha(runner)=='065955BF275BF83CA3144701F831414259BD2807A22323C91B69FBA33ABE2DC4'
    source=runner.read_text(encoding='utf-8')
    for old,new in (
        ('TP1 fixture runner','TP2 fixture runner'),
        ('recovery/core_presentation_tp1_01','recovery/core_presentation_tp2_01'),
        ("'compile_02/result.json'","'compile_03/result.json'"),
        ("'PENDING_FPP_HANDBACK_AND_BLACKOUT_OBSERVATION'","'PENDING_TP2_FRESH_TOWER_ARMS_AND_FAST_TRAVEL_TEST'")):source=one(source,old,new)
    exclusive(HERE/'deploy.py',source)
    write(DEPLOYMENT/'tool_lineage.json',{'template':str(template),'template_sha256':sha(template),'installer_sha256':sha(INSTALLER),
        'runner_source':str(runner),'runner_source_sha256':sha(runner),'preparer_sha256':sha(__file__),'runner_sha256':sha(HERE/'deploy.py'),'game_writes':0})
    print('Prepared exact two-script TP2 transaction; 51 ZIP entries read back. Not installed; fixtures pending.')

if __name__=='__main__':main()
