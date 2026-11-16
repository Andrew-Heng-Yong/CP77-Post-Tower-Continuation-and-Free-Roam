"""Pin the selected staged candidate; writes only a new local checkpoint."""
from datetime import datetime, timezone
from common import HERE, MANIFEST, RED, LUA, ARCHIVE, baseline, read, sha, write
from build import definitions, edit_legacy


def main():
    target = HERE / 'checkpoint.json'
    assert not target.exists(), 'Preserve the selected checkpoint'
    installed, game = baseline()
    package = HERE / 'candidate_04/package'
    manifest = read(HERE / 'candidate_04/manifest.json')
    assert not manifest['installed'] and manifest['baseline_sha256'] == sha(MANIFEST)
    paths = {p.relative_to(package).as_posix() for p in package.rglob('*') if p.is_file()}
    assert paths == {r['path'] for r in manifest['core_files']} and len(paths) == 51
    for row in manifest['core_files']:
        path = package / row['path']
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes']
    assert set(manifest['changed_files']) == {RED, LUA, ARCHIVE}
    catalogue = read(HERE / 'evidence_01/catalogue.json')
    generated = edit_legacy((game / RED).read_text(encoding='utf-8')) + '\n' + definitions(catalogue) + '\n' + (HERE / 'capture_hs3.reds').read_text(encoding='utf-8')
    assert generated == (package / RED).read_text(encoding='utf-8')
    packet_count = sum(len(catalogue[k]) for k in ('journals', 'facts', 'items'))
    assert (HERE / 'export.lua').read_text(encoding='utf-8').replace('__HS3_COUNT__', str(packet_count)) == (package / LUA).read_text(encoding='utf-8')
    artifacts = ['candidate_04/manifest.json', 'candidate_04/scripts.json', 'compile_04/result.json',
                 'archive_02/readback.json', 'evidence_01/plan.json', 'evidence_01/catalogue.json',
                 'evidence_01/catalogue_sources.json', 'verification_01/export_fixtures.json',
                 'verification_04/verification.json', 'verification_04/semantic_diff.json',
                 'verification_06/protocol_fixtures.json', 'verification_07/plugin_providers.json',
                 'fixtures_saves_01/manifest.json', 'verification_saves_01/verification.json',
                 'verification_saves_01/REPORT.md']
    assert manifest['compile_sha256'] == sha(HERE / 'compile_04/result.json')
    assert manifest['archive_readback_sha256'] == sha(HERE / 'archive_02/readback.json')
    assert manifest['verification_sha256'] == sha(HERE / 'verification_04/verification.json')
    assert read(HERE / 'compile_04/result.json')['staged_hashes'][RED] == sha(package / RED)
    assert read(HERE / 'archive_02/readback.json')['archive_sha256'] == sha(package / ARCHIVE)
    for rel, file in [('verification_01/export_fixtures.json', LUA),
                      ('verification_06/protocol_fixtures.json', RED),
                      ('verification_saves_01/verification.json', RED)]:
        assert read(HERE / rel)['candidate_sha256'] == sha(package / file)
    for proof, tool in [('verification_01/export_fixtures.json', 'test_export.py'),
                        ('verification_04/verification.json', 'verify.py'),
                        ('verification_06/protocol_fixtures.json', 'test_protocol.py'),
                        ('verification_07/plugin_providers.json', 'check_plugin_providers.ps1'),
                        ('fixtures_saves_01/manifest.json', 'capture_save_fixtures.ps1'),
                        ('verification_saves_01/verification.json', 'verify_save_fixtures.py'),
                        ('archive_02/readback.json', 'pack.ps1')]:
        assert read(HERE / proof)['tool_sha256'] == sha(HERE / tool)
    for row in read(HERE / 'fixtures_saves_01/manifest.json')['saves']:
        record = read(HERE / 'fixtures_saves_01' / (row['slot'] + '.json'))
        assert sha(record['source']) == record['sha256']
        artifacts += ['fixtures_saves_01/' + row['slot'] + '.json',
                      'fixtures_saves_01/' + row['slot'] + '_PTFR.HistorySnapshotHS1.SnapshotStateHS1.json']
    sources = sorted(p.name for p in HERE.iterdir() if p.is_file() and p.name != 'checkpoint.json')
    write(target, {'schema': 1, 'updated_utc': datetime.now(timezone.utc).isoformat(),
                   'status': 'STEP_2_IMPLEMENTED_OFFLINE_VERIFIED_NOT_DEPLOYED',
                   'step_1': 'Accepted completed by the user; no reopened step-1 work.',
                   'candidate': 'candidate_04', 'core_epoch': manifest['core_epoch'],
                   'installed_baseline': installed['core_epoch'], 'baseline_manifest_sha256': sha(MANIFEST),
                   'core_paths': 51, 'changed_paths': manifest['changed_files'], 'compiled_sources': 148,
                   'archive_members': 1740, 'retained_archive_members': 1738,
                   'catalogue_fingerprint': catalogue['fingerprint'], 'packets': packet_count,
                   'tests': {'export_lua': 14, 'structural_source_package': 22, 'source_protocol': 19, 'real_save_source': 24},
                   'preferred_live_fixture': 'ManualSave-26', 'gameplay': 'NOT_RUN',
                   'deployment': 'NOT_PREPARED_OR_EXECUTED', 'game_writes': 0, 'save_writes': 0,
                   'artifacts': {p: sha(HERE / p) for p in artifacts},
                   'sources': {p: sha(HERE / p) for p in sources},
                   'next': 'Prepare an authorized guarded deployment, then qualify native capture and save/reload on ManualSave-26 and the alternate cutoff route.',
                   'limits': ['Bounded source/fixture checks do not establish engine timing, persistence, future save compatibility or all-stage coverage.',
                              'Existing old saves cannot acquire missing history retroactively; native owners and stage adapters remain separate steps.']})
    print('Selected candidate_04 pinned; current 51 Core files and 26 dependencies remain unchanged.')


if __name__ == '__main__':
    main()
