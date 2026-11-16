"""Prepare the concrete TP1 transaction. Does not authorize or install it."""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import hashlib
from capture import HERE,ROOT,BASELINE,BASELINE_SHA,sha,plain,read,write
from prepare import COVER,R1,one

BASE=ROOT/'prealpha/resume_dispatcher_rd1_20261112_01'
EPOCH='TP1_FPP_HANDBACK_DIAGNOSTIC';BEFORE='RD1_EARNED_STAGE_RESUME'
SCHEMA='PTFR_TP1_FPP_HANDBACK_DIAGNOSTIC_CORE_V1'
CHANGES={COVER,R1};ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
PACKAGE=HERE/'candidate_02/package';MANIFEST=HERE/'core_manifest_01.json'
INSTALLER=HERE/'deploy_core.ps1';DEPLOYMENT=HERE/'deployment_01'
PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')

def exclusive(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)

def main():
    assert all(not p.exists() for p in (MANIFEST,INSTALLER,DEPLOYMENT,HERE/'fixtures',HERE/'recovery',HERE/'deploy.py'))
    assert sha(BASELINE)==BASELINE_SHA
    previous=read(BASELINE);game=Path(previous['game_root']);candidate=read(HERE/'candidate_02/manifest.json')
    assessment=read(HERE/'assessment_02.json');compiled=read(HERE/'compile_02/result.json')
    assert assessment['status']=='PASS_BOUNDED_STATIC_QUALIFICATION_LIVE_FIX_UNVERIFIED'
    assert assessment['candidate_manifest_sha256']==sha(HERE/'candidate_02/manifest.json')
    assert assessment['compile_sha256']==sha(HERE/'compile_02/result.json')
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
    for folder in (DEPLOYMENT,HERE/'fixtures',HERE/'recovery'):
        folder.mkdir();exclusive(folder/'.gitignore','*\n!.gitignore\n!REPORT.md\n!installed_manifest_01.json\n')
    zipfile=DEPLOYMENT/'TP1_candidate_02.zip'
    with ZipFile(zipfile,'x',ZIP_DEFLATED,compresslevel=6) as z:
        for row in files:z.write(PACKAGE/row['path'],row['path'])
    with ZipFile(zipfile) as z:
        assert len(z.namelist())==51 and set(z.namelist())==set(after) and z.testzip() is None
        assert all(hashlib.sha256(z.read(r['path'])).hexdigest().upper()==r['after'] for r in files)
    write(DEPLOYMENT/'zip_readback.json',{'status':'PASS','files':51,'sha256':sha(zipfile)})
    proofs=[BASELINE,HERE/'candidate_02/manifest.json',HERE/'assessment_02.json',HERE/'compile_02/result.json',DEPLOYMENT/'zip_readback.json']
    manifest={'schema':SCHEMA,'component':'Core','source_epoch':EPOCH,'predecessor_epoch':BEFORE,
        'scope':'Prepared two-script TP1 candidate: native FPP handback and bounded blackout/mesh diagnostics. Installation requires separate user authorization; no game launch or save edit.',
        'game_root':str(game),'save_root':previous['save_root'],'package_root':str(PACKAGE),
        'process_names':read(BASE/'core_manifest_01.json')['process_names'],'files':files,'changing_paths':sorted(CHANGES),
        'required_files':previous['required_files'],'protected_saves':[],'working_save_files':[],
        'zip':str(zipfile),'zip_sha256':sha(zipfile),'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],
        'compile_inputs':{str(game/p):h for p,h in compiled['input_pins'].items()}}
    write(MANIFEST,manifest)
    template=BASE/'deploy_core.ps1';assert sha(template)=='746ABC358FCE1FFDBD3AE8082D8010C565847B0123F5D838CED460887CA1E8D0'
    source=template.read_text(encoding='utf-8-sig')
    old_wanted=next(x for x in source.splitlines() if x.startswith('$wanted=@('))
    for a,b in (
        ('# Replace exactly the five reviewed RD1 candidate_04 files; retain global-latest loading.','# Replace exactly the two TP1 scripts after separate installation authorization.'),
        (sha(BASE/'core_manifest_01.json'),sha(MANIFEST)),
        ('PTFR_RD1_EARNED_STAGE_RESUME_CORE_V1',SCHEMA),
        ("$manifest.source_epoch -cne 'RD1_EARNED_STAGE_RESUME'",f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'HS4_GLOBAL_LATEST_HISTORY'",f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_resume_rd1_01','recovery/core_presentation_tp1_01'),
        (old_wanted,'$wanted=@('+','.join("'"+p+"'" for p in sorted(CHANGES))+')'),
        ('$changes.Count -ne 5','$changes.Count -ne 2'),
        ('Core51/five-file RD1 resume scope drift','Core51/two-script TP1 presentation scope drift')):source=one(source,a,b)
    exclusive(INSTALLER,source)
    runner=BASE/'deploy.py';assert sha(runner)=='107F6DBF969FA025233C5D1769414637A96EC55739FE6A148CA495115BB0E98E'
    text=runner.read_text(encoding='utf-8')
    for a,b in (
        ('RD1 fixture runner','TP1 fixture runner'),('from common import','from capture import'),
        ('recovery/core_resume_rd1_01','recovery/core_presentation_tp1_01'),
        ("'archive_source': str(HERE/'archive_04/archive_source')","'archive_source': previous['archive_source']"),
        ("'unchanged_core_paths': 46","'unchanged_core_paths': 49"),
        ("'gameplay': 'PENDING_USER_AUTOSAVE2_EARNED_STAGE_TEST'","'gameplay': 'PENDING_FPP_HANDBACK_AND_BLACKOUT_OBSERVATION'")):text=one(text,a,b)
    exclusive(HERE/'deploy.py',text)
    write(DEPLOYMENT/'tool_lineage.json',{'template':str(template),'template_sha256':sha(template),'installer_sha256':sha(INSTALLER),
        'runner_source':str(runner),'runner_source_sha256':sha(runner),'preparer_sha256':sha(__file__),'runner_sha256':sha(HERE/'deploy.py'),'game_writes':0})
    print('Prepared exact two-script transaction and read back all 51 ZIP paths. Not installed; fixture run pending.')

if __name__=='__main__':main()
