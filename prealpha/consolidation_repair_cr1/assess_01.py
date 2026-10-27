"""Seal CR1 evidence after deployment; read-only outside this workspace."""
from datetime import datetime, timezone
from common import *

manifest = read(CANDIDATE/'manifest.json')
install_path = CANDIDATE/'install_manifest_02.json'
install = read(install_path)
assert sha(install_path) == install_path.with_suffix('.json.sha256').read_text().strip()
for proof in install['proofs']:
    assert sha(Path(proof['path'])) == proof['sha256'], proof['path']
for row in install['package_files']:
    assert sha(GAME/row['path']) == row['after'], row['path']
    assert sha(CANDIDATE/'archived_previous'/row['path']) == row['before'], row['path']
for row in install['files']:
    assert sha(Path(install['backup_root'])/row['target']) == row['before']
    assert not (GAME/(row['target']+'.ptfr-cr1-stage')).exists()
receipt_path = Path(install['backup_root'])/'receipt.json'
receipt = read(receipt_path)
assert receipt['status'] == 'CR1_CONSOLIDATED_INSTALLED_LIVE_PENDING'
assert receipt['manifest_sha256'] == sha(install_path)

positive = read(HERE/'validation/candidate_positive_01.json')
negative = read(HERE/'validation/s30_negative_01.json')
assert positive['checks'] == 2057 and positive['groups'] == 30 and not positive['failed_groups']
assert negative['status'] == 'NEGATIVE_CONTROL_DETECTED_KNOWN_S30_REGRESSIONS'
for report in [positive, negative]:
    assert sha(Path(report['readback_index'])) == report['readback_index_sha256']
    assert sha(HERE/'validation/checks_contract_01.json') == report['checks_contract_sha256']
    assert sha(HERE/'validation/test_semantics_01.py') == report['tester_sha256']
archive = read(CANDIDATE/'archive_readback_01.json')
assert archive['status'] == 'PASS' and archive['member_count'] == 1172
assert not archive['external_collisions']
assert archive['archive_sha256'] == sha(GAME/ARCHIVE)
assert manifest['repaired_members'] == 30 and manifest['unchanged_members'] == 1142
assert manifest['changed_install_files'] == 1 and manifest['unchanged_install_files'] == 50
compile_proof = read(HERE/'compile_01/result.json')
assert compile_proof['status'] == 'PASS' and compile_proof['source_count'] == 64
for path, digest in compile_proof['installed_source_pins'].items():
    assert sha(Path(path)) == digest, path
tests = read(CANDIDATE/'deployment_tests_02.json')
assert tests['status'] == 'PASS' and tests['action_count'] == 38
assert sha(CANDIDATE/'deployment_tests_02.json') == (CANDIDATE/'deployment_tests_02.json.sha256').read_text().strip()
pre = read(CANDIDATE/'preinstall_preservation_01.json')
post = read(CANDIDATE/'postinstall_preservation_01.json')
assert pre['status'] == post['status'] == 'PASS'
assert post['save_files_unchanged'] == 295 and post['unaffected_files_unchanged'] == 498
dist = read(CANDIDATE/'dist/manifest.json')
assert sha(Path(dist['path'])) == dist['sha256'] and dist['files'] == 51
actions = {}
for name, status in [('validate','READY'),('install','CR1_CONSOLIDATED_INSTALLED_LIVE_PENDING'),('verify','VERIFIED'),('validate_rollback','ROLLBACK_READY')]:
    actions[name] = read(CANDIDATE/('actual_'+name+'_01.txt'))
    assert actions[name]['status'] == status

evidence = [CANDIDATE/name for name in [
    'manifest.json','selected_resources_01.json','archive_readback_01.json',
    'install_manifest_02.json','deployment_tests_02.json','baseline_01.json',
    'preinstall_preservation_01.json','postinstall_preservation_01.json',
    'actual_validate_01.txt','actual_install_01.txt','actual_verify_01.txt',
    'actual_validate_rollback_01.txt','dist/manifest.json']]
evidence += [HERE/name for name in [
    'donor_review/selection_01.json','donor_review/review_01.json',
    'validation/checks_contract_01.json','validation/candidate_positive_01.json',
    'validation/s30_negative_01.json','compile_01/result.json',
    'raymond/assessment_01.json','raymond/native_owner_trace_02.json']]
evidence += [receipt_path, WS/'docs/consolidation_repair_cr1.md']
evidence += sorted(HERE.glob('*.py')) + sorted(HERE.glob('*.ps1'))
evidence += [HERE/'donor_review/select_donors_01.py',HERE/'validation/test_semantics_01.py',
             HERE/'validation/decode_checks_01.ps1',HERE/'raymond/verify_01.py']
pins = [{'path':str(p.relative_to(WS)), 'sha256':sha(p)} for p in evidence]
assert all(p['sha256'] for p in pins)
assessment = {
    'status':'CR1_INSTALLED_VERIFIED_LIVE_PENDING',
    'created_utc':datetime.now(timezone.utc).isoformat(),
    'scope':'Implement the all-81-sidejob audit consolidation repairs; no 11-marker identification.',
    'package':{'install_paths':51,'replaced_paths':[ARCHIVE],'new_paths':0,
               'resources':1172,'restored_corrective_resources':30,'unchanged_resources':1142,
               'unchanged_other_install_files':50,'archive_sha256':sha(GAME/ARCHIVE),
               'zip_path':str(Path(dist['path']).relative_to(WS)),'zip_sha256':dist['sha256']},
    'validation':{'independent_assertions':2057,'groups':30,'negative_control':'PASS',
                  'compile_sources':64,'deployment_fixture_actions':38,
                  'interruption_points':6,'installed_hashes':51,'actual_actions':actions},
    'preservation':post,
    'recovery':{'backup':str(Path(install['backup_root']).relative_to(WS)),
                'installer':'prealpha/consolidation_repair_cr1/deploy_02.ps1',
                'order':'CR1 before S30 and older layers','save_undo':False},
    'remaining':[
        'Live gameplay, calls, choices, rewards, reload and already-serialized owner behavior are untested.',
        'Raymond partial-owner admission remains unchanged because original owner retirement is unproven.',
        'MQ018/MQ028 partial-state candidates remain source-only and unconfirmed.',
        'The 11-marker difference was not identified or claimed repaired.'
    ],
    'game_launches':0,'save_writes':0,'fact_writes':0,'framework_changes':0,
    'github_push':False,'published':False,'pins':pins
}
output = CANDIDATE/'assessment_01.json'
write_new(output,assessment)
output.with_suffix('.json.sha256').write_text(sha(output)+'\n',encoding='utf-8')
print(json.dumps({'status':assessment['status'],'pins':len(pins),'sha256':sha(output)}))
