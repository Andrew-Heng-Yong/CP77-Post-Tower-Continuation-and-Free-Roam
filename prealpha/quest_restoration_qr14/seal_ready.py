"""Bind final engine03 to independently tested guard and unchanged transaction proof."""
from pathlib import Path
from prepare import H, read, sha, write

def main():
    script = H / 'deploy_core.ps1'; manifest = H / 'core_manifest_02.json'
    matrix_path = H / 'run_02_results.json'; matrix = read(matrix_path)
    review_path = H / 'review_01/review.json'; review = read(review_path)
    assert review['status'].startswith(('PASS', 'APPROVE')), review['status']
    assert review['installer_sha256'] == sha(script)
    assert review['manifest_sha256'] == sha(manifest)
    assert review['test_source_sha256'] == sha(H / 'test_deployment.py')
    assert review['protocol_equivalent_to_engine02'] is True
    assert Path(review['main_matrix_result']) == matrix_path
    assert review['main_matrix_result_sha256'] == sha(matrix_path)
    assert sha(review['fixture_result']) == review['fixture_result_sha256']
    assert matrix['status'] == 'PASS_DEPLOYMENT_FIXTURES'
    assert matrix['installer_sha256'] == sha(H / 'engine_02/deploy_core.ps1')
    assert matrix['manifest_sha256'] == sha(manifest)
    compile_path = H / 'verification/compile_01/result.json'; cp = read(compile_path)
    assert cp['status'] == 'PASS_RUNTIME_REGISTERED148_INTEGRATION_COMPILE'
    summary = {'status': 'PASS_FINAL_ENGINE03_COMPOSED_FIXTURE_COVERAGE',
        'installer_sha256': sha(script), 'manifest_sha256': sha(manifest),
        'main_matrix': {'path': str(matrix_path), 'sha256': sha(matrix_path), 'engine': 'engine02',
            'checks': len(matrix['checks']), 'actions': matrix['command_count'],
            'scope': 'Normal install/rollback, caught/hard interruptions/recovery, corrupt/unknown/dependency/save refusal, reparse targets, lock contention, exact actual Core51 integration.'},
        'final_engine_controls': {'path': review['fixture_result'], 'sha256': review['fixture_result_sha256'],
            'engine': 'engine03', 'scope': 'Final source inventory guard, benign log links, added/deleted/renamed/linked sources/directories and drift; final actual Core51 and recovery/rollback.'},
        'independent_review': {'path': str(review_path), 'sha256': sha(review_path)},
        'protocol_equivalent_to_engine02': True,
        'limits': 'Main98-action matrix ran engine02. Engine03 changes only source-inventory link classification; final guard and actual integration independently executed on engine03. Do not claim matrix98 executed engine03.',
        'real_installations': 0}
    write(H / 'fixture_summary.json', summary)
    ready = {'status': 'READY_NOT_INSTALLED', 'purpose': 'Exact QR13:02 Core deployment requires separate explicit user authorization.',
        'installer_sha256': sha(script), 'manifest_sha256': sha(manifest),
        'fixture_result': 'fixture_summary.json', 'fixture_result_sha256': sha(H / 'fixture_summary.json'),
        'independent_review': 'review_01/review.json', 'independent_review_sha256': sha(review_path),
        'compile_result': str(compile_path), 'compile_result_sha256': sha(compile_path),
        'source_count': cp['source_count'], 'compile_input_pins': len(cp['input_pins']),
        'candidate_epoch': 'QR13:02', 'installed_core': 'QR8:02', 'managed_paths': 51, 'changing_paths': 3,
        'diagnostics': 'QR10D01/D00E unchanged', 'real_installations': 0, 'real_replacement_permissions_exercised': False,
        'fixture_qualification': 'No new behavior READY; see fixture_assessment.json', 'runtime_certification': False}
    write(H / 'readiness.json', ready)
    print({'status': ready['status'], 'installer_sha256': ready['installer_sha256'], 'manifest_sha256': ready['manifest_sha256']})

if __name__ == '__main__':
    main()
