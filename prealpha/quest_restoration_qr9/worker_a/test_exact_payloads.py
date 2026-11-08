"""Actual pinned payloads, synthetic saves/game roots only. No installed-file reads."""
from pathlib import Path
import importlib.util,json,shutil,concurrent.futures
H=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('qr9_fixture_helpers',H/'test_deployment.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
t.SUITE=H/'fixtures/exact_payloads_01'
t.SCRIPT=H/'deploy_qr9_guarded.ps1'
def case(component):
    f=t.fixture(component.lower(),component)
    if component=='Core':
        m=json.loads((H/'core_manifest_02.json').read_text())
        before=H.parents[1]/'phone_studios_ph3/candidate_01/package'
    else:
        m=json.loads((H/'diagnostics_manifest_01.json').read_text());before=None
    for row in m['files']:
        src=Path(m['package_root'])/row['path'];assert t.sha(src)==row['after'];shutil.copyfile(src,f['package']/row['path'])
        if before:
            src=before/row['path'];assert t.sha(src)==row['before'];shutil.copyfile(src,f['game']/row['path'])
    f['data']['files']=m['files'];f['data']['changing_paths']=m['changing_paths'];t.writejson(f['manifest'],f['data'])
    t.run(f,'Preflight',backup=component=='Core');t.run(f,'Install',backup=component=='Core');t.assert_state(f,'After');t.run(f,'Verify');t.run(f,'ValidateRollback')
    if component=='Diagnostics':t.put(f['game']/'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_QR9_Diagnostics/QR9_capture_actual_payload_fixture.jsonl',b'RETAIN_SYNTHETIC_LOG')
    t.run(f,'Rollback');t.assert_state(f,'Before');t.run(f,'Verify',state='Before')
    assert t.tree(f['save'])==f['saves_before']
    return dict(component=component,status='PASS_ACTUAL_PAYLOAD_WORKSPACE_ONLY',managed_paths=len(m['files']),changing_paths=len(m['changing_paths']),actual_payload_source=m['package_root'],source_sha256=[dict(path=r['path'],before=r['before'],after=r['after'])for r in m['files']],save_source='SYNTHETIC_FIXTURE_ONLY')
def main():
    assert not t.SUITE.exists();t.SUITE.mkdir(parents=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2)as p:results=list(p.map(case,['Core','Diagnostics']))
    result=dict(status='PASS_ACTUAL_CORE51_AND_ADDON2_WORKSPACE_TRANSACTIONS',results=results,real_game_writes=0,real_save_reads_copies_writes=0,script_sha256=t.sha(t.SCRIPT),test_sha256=t.sha(Path(__file__)))
    out=H/'exact_payload_result_01.json';assert not out.exists();t.writejson(out,result);print(json.dumps(dict(status=result['status'],script_sha256=result['script_sha256'])))
if __name__=='__main__':main()
