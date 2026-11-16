"""Pin the offline Meet Kirk entrance to the installed RD5 source providers."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'resume_dispatcher_rd6_gigs_20261113_01'))
from pin_inputs import RD5, BASELINE_SHA, baseline, readonly, read, sha, write


def main():
    manifest = baseline()
    packed_path = RD5 / 'archive_01/readback.json'
    assert sha(packed_path) == 'BDCA1C2415301C1BA2068758AE0720201F10E9D71509EA5D9041AF64EB25CDCC'
    packed = read(packed_path)
    assert packed['archive_sha256'] == manifest['archive_sha256']
    members = {row['depot']: row['sha256'] for row in packed['members']}
    assert len(members) == manifest['archive_payloads'] == 1745

    spec_path = HERE / 'entrance.json'
    spec = read(spec_path)
    ids = set(spec['provider_review']) | {part['rid'] for part in spec['resources'].values()}
    columns = 'rid, depot, key, archive, role, sha256, export_path, export_sha256'
    with readonly('registry_02/registry.sqlite3') as db:
        resources = [dict(db.execute(f'SELECT {columns} FROM resources WHERE rid=?', (rid,)).fetchone())
                     for rid in sorted(ids)]
    for row in resources:
        assert sha(row['export_path']) == row['export_sha256']
        if row['role'] == 'PTFR':
            assert members[row['depot']] == row['sha256']

    out = HERE / 'evidence_02'
    out.mkdir()
    write(out / 'inputs.json', {'game': manifest['game_root'], 'archive_sha256': manifest['archive_sha256'],
          'baseline_sha256': BASELINE_SHA, 'entrance_sha256': sha(spec_path), 'resources': resources})
    print(f'Pinned {len(resources)} providers to the installed RD5 manifest.')


if __name__ == '__main__':
    main()
