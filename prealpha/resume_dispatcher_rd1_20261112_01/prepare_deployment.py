"""Prepare the user-authorized RD1 five-file transaction in fresh workspace outputs.

Only selected, previously inspected function definitions are copied from the
pinned predecessor. Its historical prepare/install entry points are never run.
"""
import ast
from hashlib import sha256
from pathlib import Path
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED
from common import HERE, ROOT, BASELINE, BASELINE_SHA, HISTORY, RED_DIR, baseline, plain, read, sha, write

BASE=ROOT/'prealpha/history_file_loader_hs4_20261112_01'
EPOCH='RD1_EARNED_STAGE_RESUME'
BEFORE='HS4_GLOBAL_LATEST_HISTORY'
SCHEMA='PTFR_RD1_EARNED_STAGE_RESUME_CORE_V1'
ARCHIVE='archive/pc/mod/zzzz_PTFR_Combined.archive'
CHANGES={ARCHIVE,ARCHIVE+'.xl',HISTORY,RED_DIR+'/PTFR_SideJobsS22.reds',RED_DIR+'/PTFR_SideJobsS23.reds'}
PACKAGE=HERE/'candidate_04/package'
MANIFEST=HERE/'core_manifest_01.json'
INSTALLER=HERE/'deploy_core.ps1'
DEPLOYMENT=HERE/'deployment_01'
PS=Path(r'C:\Users\Ayong\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\powershell\pwsh.exe')


def one(source,before,after):
    assert source.count(before)==1,before
    return source.replace(before,after,1)


def exclusive(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as stream:stream.write(text)


def main():
    assert all(not p.exists() for p in (MANIFEST,INSTALLER,DEPLOYMENT,HERE/'deploy.py',HERE/'fixtures',HERE/'recovery'))
    previous,game=baseline();checkpoint=read(HERE/'checkpoint.json')
    candidate_path=HERE/'candidate_04/qualified_manifest.json'
    assert checkpoint['candidate']=='candidate_04' and sha(candidate_path)==checkpoint['manifest_sha256']
    assert checkpoint['manifest_sha256']=='226A0805F0167AA88A54A94A9DCB01438F56AB4E1D7D5961BFE5A1BB512E7F3B'
    candidate=read(candidate_path)
    assert candidate['baseline_manifest_sha256']==BASELINE_SHA
    for name,digest in candidate['source_pins'].items():assert sha(HERE/name)==digest,name
    assessment=HERE/checkpoint['assessment'];assert sha(assessment)==checkpoint['assessment_sha256']
    assert read(assessment)['status']=='PASS_BOUNDED_OFFLINE_QUALIFICATION'
    compiled_path=HERE/'compile_02/result.json';compiled=read(compiled_path)
    assert compiled['status']=='PASS' and compiled['source_count']==148
    for rel,digest in compiled['staged_hashes'].items():
        source=PACKAGE/rel if (PACKAGE/rel).is_file() else game/rel
        assert sha(source)==digest,rel
    for rel,digest in compiled['input_pins'].items():assert sha(game/rel)==digest,rel
    pins=read(HERE/'archive_04/readback.json')
    assert sha(PACKAGE/ARCHIVE)==pins['archive_sha256']
    assert read(assessment)['input_pins']['native_readback']==sha(HERE/'archive_04/readback.json')
    assert len(pins['members'])==1742
    current_archives=[]
    for root in (game/'archive/pc',game/'mods'):
        if root.exists():
            plain(root)
            for path in root.rglob('*'):
                plain(path)
                if path.is_file() and path.suffix.lower()=='.archive':current_archives.append(path)
    assert {str(p) for p in current_archives}=={r['path'] for r in pins['archive_inventory']}
    for row in pins['archive_inventory']:
        path=Path(row['path']);st=path.stat()
        # .NET UTC ticks and Python file timestamps refer to the same instant.
        assert st.st_size==row['bytes'] and st.st_mtime_ns//100+621355968000000000==row['mtime_ticks'],path
    registrations=read(HERE/'candidate_04/registration_inventory.json')
    current_xl={str(p) for root in (game/'archive',game/'mods') if root.exists() for p in root.rglob('*.xl')}
    assert current_xl=={p['path'] for p in registrations['xl_inputs']}
    for row in registrations['xl_inputs']:plain(Path(row['path']));assert sha(row['path'])==row['sha256']
    assert read(HERE/'candidate_04/additional_providers.json')['status']=='PASS'
    after_by_path={r['path']:r for r in candidate['core_files']}
    assert set(after_by_path)=={r['path'] for r in previous['core_files']}
    files=[]
    for row in previous['core_files']:
        target=PACKAGE/row['path'];plain(target);new=after_by_path[row['path']]
        assert sha(target)==new['sha256'] and target.stat().st_size==new['bytes']
        files.append({'path':row['path'],'before':row['sha256'],'before_bytes':row['bytes'],'after':new['sha256'],'after_bytes':new['bytes']})
    assert len(files)==51 and {r['path'] for r in files if r['before']!=r['after']}==CHANGES
    assert {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob('*') if p.is_file()}==set(after_by_path)
    for folder in (DEPLOYMENT,HERE/'fixtures',HERE/'recovery'):
        folder.mkdir();exclusive(folder/'.gitignore','*\n!.gitignore\n!REPORT.md\n!installed_manifest_01.json\n')
    zip_path=DEPLOYMENT/'RD1_candidate_04.zip'
    with ZipFile(zip_path,'x',compression=ZIP_DEFLATED,compresslevel=6) as z:
        for row in files:z.write(PACKAGE/row['path'],row['path'])
    with ZipFile(zip_path) as z:
        assert len(z.namelist())==51 and set(z.namelist())==set(after_by_path) and z.testzip() is None
        assert all(sha256(z.read(r['path'])).hexdigest().upper()==r['after'] for r in files)
    write(DEPLOYMENT/'zip_readback.json',{'status':'PASS','files':51,'sha256':sha(zip_path)})
    write(DEPLOYMENT/'current_input_verification.json',{'status':'PASS_CURRENT_BASELINE_CANDIDATE_COMPILE_PROVIDER_XL_INPUTS',
        'baseline_manifest_sha256':sha(BASELINE),'qualified_manifest_sha256':sha(candidate_path),
        'archives':len(current_archives),'xl_files':len(current_xl),'core_paths':51,'dependencies':26,'game_writes':0})
    proofs=[BASELINE,candidate_path,assessment,compiled_path,HERE/'archive_04/readback.json',
        HERE/'candidate_04/registration_inventory.json',HERE/'candidate_04/additional_providers.json',
        DEPLOYMENT/'zip_readback.json',DEPLOYMENT/'current_input_verification.json']
    manifest={'schema':SCHEMA,'component':'Core','source_epoch':EPOCH,'predecessor_epoch':BEFORE,
        'scope':'User explicitly requested: install it pls. Install RD1 candidate_04 for the AutoSave-2 genuine Tower and earned-stage gameplay test.',
        'game_root':str(game),'save_root':previous['save_root'],'package_root':str(PACKAGE),
        'process_names':read(BASE/'core_manifest_01.json')['process_names'],'files':files,'changing_paths':sorted(CHANGES),
        'required_files':previous['required_files'],'protected_saves':[],'working_save_files':[],
        'zip':str(zip_path),'zip_sha256':sha(zip_path),'proofs':[{'path':str(p),'sha256':sha(p)} for p in proofs],
        'compile_inputs':{str(game/p):digest for p,digest in compiled['input_pins'].items()}}
    write(MANIFEST,manifest)
    template=BASE/'deploy_core.ps1'
    assert sha(template)=='BF431273617EEA0F0AFFF35F3C51637DE17E16C88F2BE44DB276DAD7CC38D280'
    script=template.read_text(encoding='utf-8-sig')
    for before,after in (
        ('# Replace exactly the two snapshot scripts for global-latest loading.','# Replace exactly the five reviewed RD1 candidate_04 files; retain global-latest loading.'),
        (sha(BASE/'core_manifest_01.json'),sha(MANIFEST)),
        ('PTFR_HS4_GLOBAL_LATEST_HISTORY_CORE_V1',SCHEMA),
        ("$manifest.source_epoch -cne 'HS4_GLOBAL_LATEST_HISTORY'",f"$manifest.source_epoch -cne '{EPOCH}'"),
        ("$manifest.predecessor_epoch -cne 'HS3_NATIVE_HISTORY_CAPTURE'",f"$manifest.predecessor_epoch -cne '{BEFORE}'"),
        ('recovery/core_global_latest_hs4_01','recovery/core_resume_rd1_01'),
        ("$wanted=@('bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua','r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds')",
         '$wanted=@('+','.join("'"+p+"'" for p in sorted(CHANGES))+')'),
        ('$changes.Count -ne 2','$changes.Count -ne 5'),
        ('Core51/two-file HS4 global-latest scope drift','Core51/five-file RD1 resume scope drift')):
        script=one(script,before,after)
    exclusive(INSTALLER,script)
    # Copy only inspected functions, with explicit globals; never execute the
    # old deployment entry point or import its old builder module.
    source=BASE/'deploy.py';assert sha(source)=='564AFD55AAE0C4496DE006502848F0D1808B64750D75E41133B37D7E574E05C2'
    old=source.read_text(encoding='utf-8');tree=ast.parse(old)
    picked={n.name:ast.get_source_segment(old,n) for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('run_fixtures','record')}
    assert set(picked)=={'run_fixtures','record'}
    record=picked['record']
    for before,after in (("'archive_payloads': 1740","'archive_payloads': 1742"),
        ("'archive_source': previous['archive_source']","'archive_source': str(HERE/'archive_04/archive_source')"),
        ("'unchanged_core_paths': 49","'unchanged_core_paths': 46"),
        ("'gameplay': 'PENDING_USER_GLOBAL_LATEST_LOAD_OBSERVATION'","'gameplay': 'PENDING_USER_AUTOSAVE2_EARNED_STAGE_TEST'")):
        record=one(record,before,after)
    header='''"""RD1 fixture runner and installation recorder; no game launch."""
import argparse
from copy import deepcopy
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
from common import HERE, BASELINE, plain, read, sha, write
from prepare_deployment import EPOCH, BEFORE, CHANGES, ARCHIVE, PACKAGE, MANIFEST, INSTALLER, DEPLOYMENT, PS
RECOVERY=HERE/'recovery/core_resume_rd1_01'
'''
    runner=header+'\n'+picked['run_fixtures']+'\n\n'+record+'''

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('fixtures','record'));args=parser.parse_args()
    if args.action=='record':record()
    else:
        actions=run_fixtures(read(MANIFEST))
        write(HERE/'fixture_results.json',{'status':'PASS','installer_sha256':sha(INSTALLER),'actions':actions})
        write(HERE/'scope_review.json',{'scope':read(MANIFEST)['scope'],'changed_paths':sorted(CHANGES),
            'manifest_sha256':sha(MANIFEST),'gameplay':'User will test; no game launch'})
        write(HERE/'readiness.json',{'status':'READY_NOT_INSTALLED','manifest_sha256':sha(MANIFEST),
            'installer_sha256':sha(INSTALLER),'fixture_result':'fixture_results.json','fixture_result_sha256':sha(HERE/'fixture_results.json'),
            'scope_review':'scope_review.json','scope_review_sha256':sha(HERE/'scope_review.json')})
        print(f'PASS: {len(actions)} deployment/recovery fixture actions; real installation not started.')
'''
    ast.parse(runner);exclusive(HERE/'deploy.py',runner)
    write(DEPLOYMENT/'tool_lineage.json',{'template':str(template),'template_sha256':sha(template),'installer_sha256':sha(INSTALLER),
        'function_source':str(source),'function_source_sha256':sha(source),'adapted_functions':['run_fixtures','record'],
        'runner_sha256':sha(HERE/'deploy.py'),'preparer_sha256':sha(__file__),'game_writes':0})
    print('Prepared exact five-file RD1 transaction and fully verified 51-file local ZIP; fixture run pending.')


if __name__=='__main__':main()
