"""Prepare the provider census and seal the read-back Core51 package."""

import argparse
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from baseline import ARCHIVE, BASE, HERE, JB3, OUT, XL, installed_baseline, inventory, read, sha, write

PROOF = HERE / 'verification_01.json'
PACK_PLAN = HERE / 'input_01/pack_plan.json'
ARCHIVE_PROOF = HERE / 'archive_readback_01.json'
BUNDLE = HERE / 'JB4_Core51_02.zip'


def prepare_pack():
    assert not PACK_PLAN.exists() and not (HERE / 'pack.ps1').exists()
    check = read(PROOF)
    assert check['status'] == 'PASS_JB4_COOKED_AND_BOUNDED_FLOW'
    baseline = read(HERE / 'baseline.json')
    providers, edits = {}, []
    for part, batch in (('batch5', 'batch5'), ('batch6', 'batch6_02')):
        path = HERE / 'input_01' / (batch + '.json')
        assert check[part + '_plan_sha256'] == sha(path)
        plan = read(path)
        for row in plan['providers']:
            assert providers.get(row['depot'], row) == row, row['depot']
            providers[row['depot']] = row
        edits.extend(plan['edits'])
    assert len(edits) == len({r['depot'] for r in edits}) == 121
    assert sum(r['is_new'] for r in edits) == 87
    write(PACK_PLAN, {
        'candidate': str(OUT), 'game_root': baseline['game_root'],
        'old_archive_count': baseline['old_archive_count'], 'providers': list(providers.values()),
        'edits': edits, 'verification_sha256': sha(PROOF),
    })
    # Preserve the verified predecessor's archive writer and independent
    # payload/provider readback. Only the input and proof bindings differ.
    source = (JB3 / 'pack.ps1').read_text(encoding='utf-8-sig')
    changes = {
        "'input_01/plan.json'": "'input_01/pack_plan.json'",
        "'PASS_JB3_COOKED_AND_BOUNDED_FLOW'": "'PASS_JB4_COOKED_AND_BOUNDED_FLOW'",
        "$proof.plan_sha256 -cne (Get-FileHash -LiteralPath $planPath).Hash":
            "$plan.verification_sha256 -cne (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'verification_01.json')).Hash",
        "'PASS_JB3_ARCHIVE_AND_PROVIDERS'": "'PASS_JB4_ARCHIVE_AND_PROVIDERS'",
        "'Unverified JB3 inputs'": "'Unverified JB4 inputs'",
    }
    for old, new in changes.items():
        assert source.count(old) == 1, old
        source = source.replace(old, new)
    with (HERE / 'pack.ps1').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(source)


def seal():
    installed = installed_baseline()
    manifest_path = OUT / 'package_manifest.json'
    assert not manifest_path.exists() and not BUNDLE.exists()
    plan, archive, verification = map(read, (PACK_PLAN, ARCHIVE_PROOF, PROOF))
    assert archive['status'] == 'PASS_JB4_ARCHIVE_AND_PROVIDERS' and archive['plan_sha256'] == sha(PACK_PLAN)
    assert plan['verification_sha256'] == sha(PROOF) and archive['new_xl_registrations'] == 0
    compiled_path = HERE / 'compile_01/result.json'
    compiled = read(compiled_path)
    assert compiled['status'] == 'PASS_JB4_COMPLETE_SOURCE_COMPILE' and compiled['exit_code'] == 0
    assert compiled['source_count'] == len(compiled['sources']) == 148
    assert all(sha(p) == digest for p, digest in compiled['input_pins'].items())

    cooked = {}
    for part, batch in (('batch5', 'batch5'), ('batch6', 'batch6_02')):
        proof = HERE / ('readback_' + batch) / 'manifest.json'
        assert sha(proof) == verification[part + '_readback_sha256']
        for row in read(proof)['resources']:
            assert row['depot'] not in cooked and sha(row['raw']) == row['sha256']
            cooked[row['depot']] = row['sha256']
    previous = read(BASE / 'package_manifest.json')['source_resources']
    members = {r['depot']: r['sha256'] for r in archive['resources']}
    assert len(members) == len(archive['resources']) == 1723
    assert len({r['key'] for r in archive['resources']}) == 1723
    assert members == previous | cooked == inventory(OUT / 'archive_source', '\\')
    new_depots = members.keys() - previous.keys()
    changed_depots = {d for d in previous if members[d] != previous[d]}
    assert new_depots == {e['depot'] for e in plan['edits'] if e['is_new']}
    assert changed_depots == {e['depot'] for e in plan['edits'] if not e['is_new']}

    pkg = OUT / 'package'
    files = inventory(pkg)
    before = {r['path']: r['sha256'] for r in installed['core_files']}
    assert files.keys() == before.keys() and len(files) == 51
    assert files[XL] == before[XL] and files[ARCHIVE] == archive['archive_sha256']
    changes = sorted(p for p in files if files[p] != before[p])
    overlay = {r['path']: r['after'] for r in compiled['overlays']}
    assert set(changes) == {ARCHIVE, *overlay} and len(changes) == 4
    game = Path(installed['game_root'])
    for p, row in compiled['sources'].items():
        expected = files.get(Path(p).relative_to(game).as_posix(), compiled['input_pins'][p])
        assert expected == row['sha256'] == sha(row['staged'])

    file_rows = [{'path': p, 'sha256': digest, 'bytes': (pkg / p).stat().st_size}
                 for p, digest in sorted(files.items())]
    with ZipFile(BUNDLE, 'x', compression=ZIP_DEFLATED, compresslevel=6) as z:
        for row in file_rows:
            z.write(pkg / row['path'], row['path'])
    with ZipFile(BUNDLE) as z:
        assert len(z.namelist()) == len(files) and set(z.namelist()) == files.keys()
        for row in file_rows:
            with z.open(row['path']) as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest().upper() == row['sha256']

    write(manifest_path, {
        'status': 'STAGED_JB4_READBACK_VERIFIED', 'epoch': 'JB4', 'predecessor': 'JB3',
        'archive_payloads': len(members), 'source_resources': members, 'files': file_rows,
        'new_depots': sorted(new_depots), 'changed_depots': sorted(changed_depots),
        'changed_paths': changes, 'new_xl_registrations': 0,
        'zip_sha256': sha(BUNDLE), 'compiled_sources': 148, 'scene_fixtures': verification['fixture_count'],
        'proofs': {str(p.relative_to(HERE)): sha(p) for p in (PROOF, PACK_PLAN, ARCHIVE_PROOF, compiled_path)},
    })
    print(f'Sealed and verified {len(files)} Core files and {len(members)} archive payloads.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'seal'))
    args = parser.parse_args()
    (prepare_pack if args.action == 'prepare' else seal)()
