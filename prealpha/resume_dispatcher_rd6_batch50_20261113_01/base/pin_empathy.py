"""Pin the offline Empathy entrance to the current installed RD5 inputs."""
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'resume_dispatcher_rd6_gigs_20261113_01'))
from pin_inputs import RD5, BASELINE_SHA, baseline, read, readonly, sha, write


def main():
    installed = baseline()
    archive_readback = RD5 / 'archive_01/readback.json'
    assert sha(archive_readback) == 'BDCA1C2415301C1BA2068758AE0720201F10E9D71509EA5D9041AF64EB25CDCC'
    packed = read(archive_readback)
    assert packed['archive_sha256'] == installed['archive_sha256']
    members = {row['depot']: row['sha256'] for row in packed['members']}
    assert len(members) == installed['archive_payloads'] == 1745
    plan = HERE / 'empathy.json'
    with readonly('registry_02/registry.sqlite3') as db:
        resources = [dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone())
                     for rid in read(plan)['providers']]
    for row in resources:
        assert sha(row['export_path']) == row['export_sha256']
        if row['role'] == 'PTFR':
            assert members[row['depot']] == row['sha256']
    evidence = HERE / 'evidence_01'
    evidence.mkdir()
    write(evidence / 'inputs.json', {
        'game': installed['game_root'], 'archive_sha256': installed['archive_sha256'],
        'baseline_sha256': BASELINE_SHA, 'plan_sha256': sha(plan), 'resources': resources,
    })
    print(f'Pinned {len(resources)} Empathy providers against the installed RD5 baseline.')


if __name__ == '__main__':
    main()
