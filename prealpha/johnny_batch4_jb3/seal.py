"""Seal the verified Core51 package for offline handoff."""

import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from prepare import ARCHIVE, BASE, HERE, INPUT, INSTALLED, OUT, XL, inventory
from resources import read, sha, write


def main():
    bundle = HERE / 'JB3_Core51_01.zip'
    manifest = OUT / 'package_manifest.json'
    checkpoint = HERE / 'checkpoint.json'
    assert all(not p.exists() for p in (bundle, manifest, checkpoint))
    plan_path = INPUT / 'plan.json'
    archive_proof = HERE / 'archive_readback_01.json'
    flow_proof = HERE / 'verification_01.json'
    pl, archive, flow = read(plan_path), read(archive_proof), read(flow_proof)
    assert archive['status'] == 'PASS_JB3_ARCHIVE_AND_PROVIDERS'
    assert flow['status'] == 'PASS_JB3_COOKED_AND_BOUNDED_FLOW'
    assert archive['plan_sha256'] == flow['plan_sha256'] == sha(plan_path)
    assert archive['new_xl_registrations'] == 0
    assert sha(INSTALLED) == pl['installed_baseline_sha256']
    installed = read(INSTALLED)
    assert installed['core_epoch'] == 'JB1'
    game = Path(installed['game_root'])
    for row in installed['core_files'] + installed['required_files']:
        assert sha(game / row['path']) == row['sha256'], row['path']

    prior = BASE / 'package_manifest.json'
    assert sha(prior) == pl['baseline_package_sha256']
    before = read(prior)
    cooked_path = HERE / 'readback_01/manifest.json'
    assert sha(cooked_path) == flow['readback_sha256']
    cooked = {r['depot']: r['sha256'] for r in read(cooked_path)['resources']}
    members = {r['depot']: r['sha256'] for r in archive['resources']}
    assert len(members) == len(archive['resources'])
    old_members = before['source_resources']
    assert members == old_members | cooked
    added = members.keys() - old_members.keys()
    changed = {p for p in old_members if old_members[p] != members[p]}
    assert added == {r['depot'] for r in pl['edits'] if r['is_new']}
    assert changed == {r['depot'] for r in pl['edits'] if not r['is_new']}
    assert len(members) == before['archive_payloads'] + len(added)

    pkg = OUT / 'package'
    files = inventory(pkg)
    prior_files = {r['path']: r['sha256'] for r in before['files']}
    assert files.keys() == prior_files.keys() and len(files) == 51
    assert files[ARCHIVE] == archive['archive_sha256']
    assert {p for p in files if files[p] != prior_files[p]} == {ARCHIVE}
    assert files[XL] == prior_files[XL]
    installed_files = {r['path']: r['sha256'] for r in installed['core_files']}
    assert files.keys() == installed_files.keys()
    relative_to_jb1 = sorted(p for p in files if files[p] != installed_files[p])
    assert set(relative_to_jb1) == {ARCHIVE, *(r['path'] for r in read(BASE.parent / 'compile_01/result.json')['overlays'])}
    file_rows = [{'path': p, 'sha256': h, 'bytes': (pkg / p).stat().st_size}
                 for p, h in sorted(files.items())]
    with ZipFile(bundle, 'x', compression=ZIP_DEFLATED, compresslevel=6) as out:
        for row in file_rows:
            out.write(pkg / row['path'], row['path'])
    with ZipFile(bundle) as check:
        assert len(check.namelist()) == len(files) and set(check.namelist()) == files.keys()
        for row in file_rows:
            with check.open(row['path']) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest().upper() == row['sha256'], row['path']

    write(manifest, {
        'status': 'STAGED_JB3_READBACK_VERIFIED', 'epoch': 'JB3', 'predecessor': 'JB2',
        'files': file_rows, 'archive_payloads': len(members), 'source_resources': members,
        'new_depots': sorted(added), 'changed_depots': sorted(changed), 'changed_paths': [ARCHIVE],
        'retained_archive_members': len(old_members) - len(changed), 'new_xl_registrations': 0,
        'installed': False, 'gameplay_validation': 'PENDING_GENUINE_PRE_SCENE_FIXTURES',
    })
    write(checkpoint, {
        'status': 'JB3_BATCH4_STAGED_OFFLINE', 'date': '2026-11-09',
        'candidate': OUT.name, 'package': bundle.name, 'package_sha256': sha(bundle),
        'package_manifest': str(manifest.relative_to(HERE)), 'package_manifest_sha256': sha(manifest),
        'archive_sha256': files[ARCHIVE], 'archive_payloads': len(members),
        'installed_epoch': 'JB1', 'installed_manifest_sha256': sha(INSTALLED),
        'changes_relative_to_installed': relative_to_jb1, 'core_paths': len(files),
        'required_dependencies_verified': len(installed['required_files']),
        'changed_resources': len(changed), 'new_depot_paths': len(added),
        'fixture_count': flow['fixture_count'], 'new_xl_registrations': 0,
        'proofs': {str(p.relative_to(HERE)): sha(p) for p in (plan_path, cooked_path, flow_proof, archive_proof)},
        'gameplay_status': 'PENDING_GENUINE_PRE_SCENE_FIXTURES',
        'game_writes': 0, 'save_writes': 0,
    })
    print(f'Sealed and verified {len(files)} Core files and {len(members)} archive payloads.')


if __name__ == '__main__':
    main()
