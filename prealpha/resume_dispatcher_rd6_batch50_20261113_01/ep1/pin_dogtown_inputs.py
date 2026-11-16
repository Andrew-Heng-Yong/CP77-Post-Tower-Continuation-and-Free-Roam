"""Pin the installed Dogtown providers and offline graph exports."""
from argparse import ArgumentParser
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'resume_dispatcher_rd6_gigs_20261113_01'))
from pin_inputs import BASELINE, RD5, baseline, read, readonly, sha, write


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('plan_root', nargs='?', default=HERE, type=Path)
    plan_root = parser.parse_args().plan_root
    installed = baseline()
    archive_proof = RD5 / 'archive_01/readback.json'
    assert sha(archive_proof) == 'BDCA1C2415301C1BA2068758AE0720201F10E9D71509EA5D9041AF64EB25CDCC'
    archive = read(archive_proof)
    assert archive['archive_sha256'] == installed['archive_sha256']
    members = {r['depot']: r['sha256'] for r in archive['members']}
    assert len(members) == installed['archive_payloads'] == 1745
    plan_path = plan_root / 'plan.json'
    plan = read(plan_path)
    ids = dict.fromkeys((plan['wrapper'], plan['main'], plan['body'], *plan['support']))
    with readonly('registry_02/registry.sqlite3') as db:
        resources = [dict(db.execute('SELECT * FROM resources WHERE rid=?', (rid,)).fetchone()) for rid in ids]
    for row in resources:
        assert sha(row['export_path']) == row['export_sha256']
        if row['role'] == 'PTFR':
            assert members[row['depot']] == row['sha256']
    output = plan_root / 'evidence_01'
    output.mkdir()
    write(output / 'inputs.json', {
        'game': installed['game_root'], 'baseline_sha256': sha(BASELINE),
        'archive_sha256': installed['archive_sha256'], 'plan_sha256': sha(plan_path),
        'resources': resources,
    })
    print(f"Pinned {len(resources)} {plan['title']} providers against installed RD5.")


if __name__ == '__main__':
    main()
