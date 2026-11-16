"""Pin both resume bodies to current inputs and prior fixture evidence."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BATCH = HERE.parent/'resume_dispatcher_rd5_gigs_20261113_01'
RD5 = HERE.parent/'resume_dispatcher_rd5_rite_20261113_02'
BASELINE = RD5/'deployment_01/installed_manifest_01.json'
BASELINE_SHA = 'C298EA55F984CB0CAC95388848705C9B15C7CCD74958EE901C794BDFDEE28C36'
sys.path.insert(0, str(BATCH))
from verify_batch import readonly, read, sha, write
from capture import plain


def baseline():
    assert sha(BASELINE) == BASELINE_SHA
    manifest = read(BASELINE)
    assert manifest['core_epoch'] == 'RD5_RITE_OF_PASSAGE_RESUME'
    assert len(manifest['core_files']) == 51 and len(manifest['required_files']) == 26
    game = Path(manifest['game_root'])
    for entry in manifest['core_files'] + manifest['required_files']:
        path = game/entry['path']
        plain(path)
        assert sha(path) == entry['sha256'], path
    return manifest


def main():
    manifest = baseline()
    packed = read(RD5/'archive_01/readback.json')
    assert sha(RD5/'archive_01/readback.json') == 'BDCA1C2415301C1BA2068758AE0720201F10E9D71509EA5D9041AF64EB25CDCC'
    assert packed['archive_sha256'] == manifest['archive_sha256']
    members = {r['depot']: r['sha256'] for r in packed['members']}
    assert len(members) == manifest['archive_payloads'] == 1745
    out = HERE/'evidence_02'
    plan = read(HERE/'entrances.json')['quests']
    ids = sorted({rid for q in plan for rid in (q['wrapper'], q['main'], q['body'], *q['support'])})
    with readonly('registry_02/registry.sqlite3') as db:
        resources = [dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone()) for rid in ids]
    for row in resources:
        assert sha(row['export_path']) == row['export_sha256']
        if row['role'] == 'PTFR':
            assert members[row['depot']] == row['sha256']
    out.mkdir()
    write(out/'inputs.json', {'game': manifest['game_root'], 'archive_sha256': manifest['archive_sha256'],
          'baseline_sha256': BASELINE_SHA, 'plan_sha256': sha(HERE/'entrances.json'), 'resources': resources})
    print(f'Pinned {len(resources)} resource inputs against the installed RD5 manifest.')


if __name__ == '__main__':
    main()
