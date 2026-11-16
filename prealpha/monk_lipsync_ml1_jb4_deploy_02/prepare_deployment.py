"""Refresh the verified monk patch transaction for the current game session."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
STAGED = HERE.parent / 'monk_lipsync_ml1_jb4'
sys.path.insert(0, str(STAGED))
from stage import ARCHIVE, BASE, baseline, checked, plain, read, sha, write

TRANSACTION = 'core_manifest_01.json'
ALLOWED = [ARCHIVE]
SOURCE_PACKAGE = BASE / 'package'


def write_new(path, source):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)


def main():
    target = HERE / TRANSACTION
    assert not target.exists() and not (HERE / 'deploy_core.ps1').exists()
    installed, _ = baseline()
    previous = checked(STAGED / TRANSACTION, '0E46C0A62C294989A8CCD96A44DCED6E089E2F07E871657DB42BBA9489CB05DE')
    installer = checked(STAGED / 'deploy_core.ps1', 'C392ADFE1A87EBF2F78EAEBA8AD9DF6C4CC0F86732430D1E10F0C4CAEC6B51AD')
    ready = read(checked(STAGED / 'readiness.json', 'D6FE60BD0DB1FDD649946AACD08E27BB16FBEEF35C18D59F6014D7846C86D3E0'))
    assert ready['status'] == 'READY_NOT_INSTALLED'
    assert ready['manifest_sha256'] == sha(previous) and ready['installer_sha256'] == sha(installer)
    previous_fixtures = checked(STAGED / ready['fixture_result'], ready['fixture_result_sha256'])
    checked(STAGED / ready['independent_review'], ready['independent_review_sha256'])
    tx = read(previous)
    assert tx['source_epoch'] == 'ML1' and tx['predecessor_epoch'] == 'JB4' and tx['changing_paths'] == ALLOWED
    assert tx['required_files'] == installed['required_files']
    for row in tx['proofs']:
        checked(row['path'], row['sha256'])
    checked(tx['zip'], tx['zip_sha256'])

    timestamp = tx['compile_coverage']['timestamp_sidecar']
    assert len(timestamp) == 1 and Path(timestamp[0]['path']) == Path(tx['game_root']) / 'r6/cache/final.redscripts.ts'
    path = Path(timestamp[0]['path'])
    plain(path)
    assert path.stat().st_size == timestamp[0]['bytes'] == 16
    old = timestamp[0]['current_sha256']
    current = sha(path)
    assert tx['compile_inputs'][str(path)] == old
    tx['compile_inputs'][str(path)] = current
    timestamp[0]['current_sha256'] = current
    for path, digest in tx['compile_inputs'].items():
        checked(path, digest)
    for row in tx['protected_saves']:
        checked(Path(tx['save_root']) / row['path'], row['sha256'])
    write(target, tx)

    body = installer.read_text(encoding='utf-8-sig')
    delta = {
        "$PinnedCoreManifestSHA='" + sha(previous) + "'": "$PinnedCoreManifestSHA='" + sha(target) + "'",
        'recovery/core_ml1_jb4_01': 'recovery/core_ml1_jb4_02',
    }
    for before, after in delta.items():
        assert body.count(before) == 1, before
        body = body.replace(before, after)
    write_new(HERE / 'deploy_core.ps1', body)
    write(HERE / 'installer_review.json', {
        'status': 'PASS_ML1_JB4_REFRESHED_TRANSACTION',
        'installer_sha256': sha(HERE / 'deploy_core.ps1'), 'manifest_sha256': sha(target),
        'previous_installer_sha256': sha(installer), 'previous_manifest_sha256': sha(previous),
        'previous_fixture_sha256': sha(previous_fixtures), 'substitutions': delta,
        'timestamp_sidecar': {'before': old, 'current': current, 'bytes': 16},
        'changing_paths': ALLOWED,
    })
    test = checked(STAGED / 'test_deployment.py', '3BE749936DC7C539E08845CD324BAA27259FF2AE3BB89645E25D66CBF2FC9C40')
    write_new(HERE / 'test_deployment.py', test.read_text(encoding='utf-8-sig'))
    print('Refreshed the runtime timestamp pin for the sealed one-archive update.')


if __name__ == '__main__':
    main()
