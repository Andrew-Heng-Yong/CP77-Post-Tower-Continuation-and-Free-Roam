"""Pin the installed HS4 inputs and existing stage resources for RD1."""
import json
import argparse
from pathlib import Path
import shutil
import sqlite3
import sys
from common import HERE, ROOT, REGISTRY, BASELINE, baseline, read, sha, write


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', required=True, type=int)
    args = parser.parse_args()
    out = HERE / f'evidence_{args.attempt:02d}'
    base = HERE / f'base_{args.attempt:02d}'
    assert not out.exists() and not base.exists()
    manifest, game = baseline()
    out.mkdir()
    package = base / 'package'
    for row in manifest['core_files']:
        if row['path'].endswith('.reds') or row['path'].endswith('.xl'):
            dst = package / row['path']
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(game / row['path'], dst)
            assert sha(dst) == row['sha256']
    conn = sqlite3.connect(REGISTRY.as_uri() + '?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    sys.path.insert(0, str(REGISTRY.parent.parent))
    from model import load_export, normalize
    ids = {6542, 12821, 9197, 14545, 14686, 15234, 15402}
    sources, models = [], {}
    donor = Path(manifest['archive_source'])
    for rid in sorted(ids):
        row = dict(conn.execute('select * from resources where rid=?', (rid,)).fetchone())
        assert sha(row['export_path']) == row['export_sha256']
        if row['role'] == 'PTFR':
            assert sha(donor / row['depot']) == row['sha256'], row['depot']
        models[str(rid)] = normalize(load_export(Path(row['export_path'])))
        sources.append({key: row[key] for key in ('rid', 'depot', 'role', 'key', 'archive', 'sha256', 'export_path', 'export_sha256')})
    roster = [json.loads(row[0]) for row in conn.execute('select record_json from quests order by id')]
    write(out / 'sources.json', sources)
    write(out / 'graphs.json', models)
    write(out / 'roster.json', roster)
    write(out / 'baseline.json', {'manifest': str(BASELINE), 'manifest_sha256': sha(BASELINE),
        'core_epoch': manifest['core_epoch'], 'game_root': str(game), 'archive_source': str(donor),
        'core_files': manifest['core_files'], 'required_files': manifest['required_files'],
        'scope': 'Shared resume dispatcher, Deliver Skippy and Moving Heat first-door adapter work; no deployment.'})
    print(f'Pinned {len(manifest["core_files"])} Core files and {len(manifest["required_files"])} dependencies; read {len(sources)} stage resources.')


if __name__ == '__main__':
    main()
