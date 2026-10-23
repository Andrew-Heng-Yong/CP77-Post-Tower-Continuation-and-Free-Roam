"""Independent S27 integration/deployment proof review; no game mutations."""
import hashlib
import json
import sys
from pathlib import Path

from review_normalization import compare

ROOT = Path(__file__).resolve().parents[3]
HERE = ROOT / 'prealpha/sidejobs_s27'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main(revision, name):
    build = HERE / 'build' / revision
    output = ROOT / 'research/sidejobs_s27/runtime' / name
    assert not output.exists(), 'Immutable review receipt'
    checks = []
    def check(label, condition):
        assert condition, label
        checks.append(label)
    source = (HERE / 'deploy.ps1').read_text(encoding='utf-8-sig')
    builder = (HERE / 'build.ps1').read_text(encoding='utf-8-sig')
    compiler = (HERE / 'compile.py').read_text(encoding='utf-8-sig')
    expected = ['archive/pc/mod/0000000_TowerContinued_SideJobs_S27.archive',
                'archive/pc/mod/0000000_TowerContinued_SideJobs_S27.archive.xl',
                'r6/scripts/TowerContinued_SideJobs_S27/SideJobsS27.reds']
    for token in expected:
        check('Exact live target ' + token, token in source)
    for token in ["if(@($files).Count -ne 3", "'No replacement metadata allowed'",
                  "'Only exact new script leaf may be created'", "'Addition exists; refusing overwrite'",
                  "'New recovery directory required'", "'Recovery identity mismatch'",
                  "'Interrupted/previous rollback requires inspection'", "'Already rolled back'",
                  "[IO.File]::Move($target,$removed,$false)", "Scope $txn.files", "Closed;Match $target",
                  "Closed;$target=Bound", "CopyExact", "$count=Same $protected",
                  "'Installed script identity set changed since compilation'", "'Compiler include roots changed'",
                  "'Compiler input identity mismatch'", "'Installed archive identities changed'",
                  "'Installed ArchiveXL identities changed'", "'Unsafe source pin'",
                  "'Matching deployment fixtures required'", "'Only appended phone cleanup override allowed'"]:
        check('Installer check ' + token, token in source)
    for token in ['Remove-Item', 'RemoveAllItems', 'Stop-Process', 'git reset', 'SetFactStr']:
        check('No forbidden installer operation ' + token, token not in source)
    check('Safety helper version pinned', '1D1D204D792D65FF30757B455E57826787E395A1DF0C1D5352A60D0757EC3307' in source)
    for token in ['Source identity set changed before compile', 'Source identity set changed during compile',
                  "'EquipmentEx.reds' in log", "'EquipmentEx.OutfitSystem.GetInstance' in text",
                  "'script_environment_complete': True", "'combined_cli': True", "'full_scc': True"]:
        check('Compiler check ' + token, token in compiler)
    for token in ['Native raw/witness mismatch:', 'Cleanup raw/witness mismatch', 'Packed readback mismatch',
                  'Installed XL set changed during build', 'Source changed during build:']:
        check('Builder check ' + token, token in builder)
    manifest = read(build / 'build.json')
    build_hash = sha(build / 'build.json')
    check('Exact additive manifest', [f['relative'] for f in manifest['files']] == expected and
          not any('old_sha256' in f for f in manifest['files']))
    check('Only current mod cleanup override', manifest['official_overrides'] == [] and
          manifest['mod_overrides'] == ['towercontinued\\gig_phone_u9\\fixer_cleanup.questphase'])
    for row in manifest['files']:
        check('Artifact hash ' + row['relative'], sha(build / Path(row['relative']).name) == row['sha256'])
    for path, digest in manifest['source_pins'].items():
        assert sha(ROOT / path) == digest, path
    check('All aggregate source pins current', bool(manifest['source_pins']))
    for row in manifest['native_source_readbacks']:
        assert sha(ROOT / row['raw']) == row['raw_sha256']
        assert sha(ROOT / row['witness']) == row['witness_sha256']
        assert sha(build / row['fresh']) == row['fresh_sha256']
        assert compare(read(ROOT / row['witness'])['Data'], read(build / row['fresh'])['Data'])
    check('Raw native bytes freshly decoded; only validated TweakDBID representation differences', bool(manifest['native_source_readbacks']))
    normalizations = []
    for path in (ROOT / 'research/sidejobs_s27/runtime').glob('normalization_review_*.json'):
        proof = read(path)
        if proof.get('build_sha256') == build_hash and proof.get('reviewer_sha256') == sha(HERE / 'runtime/review_normalization.py') and proof.get('normalizer_sha256') == sha(HERE / 'raw_compare.py'):
            normalizations.append((path, proof))
    check('Current strict independent normalization proof', bool(normalizations))
    normalization_path, normalization = sorted(normalizations, key=lambda pair: str(pair[0]))[-1]
    check('Strict typed bitwiseCRC payload comparison passed', normalization['status'] == 'PASS_INDEPENDENT_STRICT_NATIVE_NORMALIZATION_NOT_LIVE' and normalization['strict_types'] is True and normalization['native_readbacks'] == len(manifest['native_source_readbacks']))
    proofs = {name: read(build / name) for name in ['tests.json', 'compile_result.json', 'resource_check.json']}
    for name, proof in proofs.items():
        check('Build-bound proof ' + name, proof['build_sha256'] == build_hash and proof['status'].startswith('PASS'))
    check('Native/test tool current', proofs['tests.json']['tester_sha256'] == sha(HERE / 'test.py'))
    compiled = proofs['compile_result.json']
    check('Compiler tool current', compiled['compiler_sha256'] == sha(HERE / 'compile.py'))
    check('Compiled target source current', compiled['script_sha256'] == manifest['files'][2]['sha256'])
    for key in ['full_scc', 'combined_cli', 'body_readback', 'equipmentex', 'live_files_unchanged', 'script_environment_complete']:
        check('Positive compiler flag ' + key, compiled[key] is True)
    check('Complete compiler identity maps', all(compiled[key] for key in ['dependencies', 'protected', 'compiler_inputs', 'script_roots']))
    audit = proofs['resource_check.json']
    check('Resource checker current', audit['checker_sha256'] == sha(HERE / 'resource_check.ps1'))
    check('Actual archive/XL maps bound', bool(audit['archive_pins']) and audit['xl_pins'] == manifest['installed_xl_pins'])
    check('Cleanup wins without explicit modlist', audit['modlist_absent'] is True and audit['new_overrides_first'] is True)
    check('Both used-journal metadata variants audited', len(audit['metadata_variants']) == 2 and
          audit['exact_byte_resources'] == audit['official_comparisons'] - 1)
    runtime = ROOT / manifest['runtime']
    rt_manifest, rt_tests = read(runtime / 'manifest.json'), read(runtime / 'tests.json')
    check('Runtime test source current', rt_tests['test_sha256'] == sha(HERE / 'runtime/test.py'))
    check('Runtime manifest bound', rt_tests['manifest_sha256'] == sha(runtime / 'manifest.json'))
    for path, digest in rt_tests['source_pins'].items():
        assert manifest['source_pins'][path] == digest == sha(ROOT / path), path
    check('All transitive runtime test pins bound', bool(rt_tests['source_pins']))
    check('All newly admitted family roots Inactive', all(j['states'] == [1] for row in rt_manifest['rows']
          for j in row['journals'] if j['class'] == 'gameJournalQuest'))
    fixtures = []
    for path in (HERE / 'fixtures').glob('*/results.json'):
        result = read(path)
        if result.get('build_sha256') == build_hash and result.get('installer_sha256') == sha(HERE / 'deploy.ps1') and result.get('tester_sha256') == sha(HERE / 'test_deploy.py'):
            fixtures.append((path, result))
    check('Current matching completed fixture suite', bool(fixtures))
    path, fixture = sorted(fixtures, key=lambda pair: str(pair[0]))[-1]
    check('Fixture suite passed without live writes', fixture['status'] == 'PASS_WORKSPACE_FIXTURES_NOT_LIVE' and
          fixture['game_writes'] == fixture['save_writes'] == 0 and fixture['fixtures_only'] is True)
    for case in ['normal_recoverable_add_only_no_repeat', 'busy', 'source_hash_drift', 'script_added', 'include_added',
                 'compiler_tool_drift', 'archive_set_drift', 'xl_added', 'xl_changed', 'xl_removed',
                 'after_first_recoverable', 'after_backup_recoverable', 'target_drift_refused',
                 'transaction_drift', 'staged_drift', 'extra_user_file_preserved', 'junction_game_refused',
                 'junction_save_refused', 'junction_build_refused', 'junction_target_parent_refused']:
        check('Fixture exercised ' + case, case in fixture['case_names'])
    report = {'status': 'PASS_INDEPENDENT_DEPLOYMENT_REVIEW_NOT_LIVE', 'checks': len(checks), 'check_names': checks,
              'build_sha256': build_hash, 'reviewer_sha256': sha(Path(__file__)),
              'installer_sha256': sha(HERE / 'deploy.ps1'), 'fixture_tester_sha256': sha(HERE / 'test_deploy.py'),
              'fixture_proof': path.relative_to(ROOT).as_posix(), 'fixture_sha256': sha(path),
              'normalization_proof': normalization_path.relative_to(ROOT).as_posix(), 'normalization_sha256': sha(normalization_path),
              'normalization_reviewer_sha256': sha(HERE / 'runtime/review_normalization.py'),
              'sources_current': len(manifest['source_pins']), 'native_readbacks': len(manifest['native_source_readbacks']),
              'additions': 3, 'replacements': 0, 'game_writes_by_review': 0,
              'limits': 'Static/native/package and workspace fixtures are not live gameplay, reward, phone or save/reload proof. General unfinished-sidejob restart remains unimplemented.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'check_names'}))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
