"""Pin the installed TP2 baseline and preserve the failed session evidence."""
import hashlib
import json
from pathlib import Path
import shutil
import stat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = ROOT / 'prealpha/tower_presentation_tp2_20261112_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA = 'D92CC15808F2657691802C79DB7C8CA6A784A7857759F578BEF3D07E5948A323'

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

def plain(path):
    for part in (path, *path.parents):
        assert not part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, part

def main():
    assert sha(BASELINE) == BASELINE_SHA
    baseline = read(BASELINE)
    game = Path(baseline['game_root'])
    out = HERE / 'evidence_01'
    out.mkdir()
    paths = ('bin/x64/plugins/cyber_engine_tweaks/gamelog.log',
             'red4ext/logs/red4ext-2026-11-12-20-01-01.log',
             'r6/logs/redscript_r2026-11-12_20-01-09.log')
    rows = []
    for name in paths:
        source = game / name
        dest = out / source.name
        pin = sha(source)
        shutil.copyfile(source, dest)
        assert sha(source) == sha(dest) == pin, name
        rows.append({'source': name, 'sha256': pin})
    lines = (out / 'gamelog.log').read_text(encoding='utf-8-sig', errors='replace').splitlines()
    session = [x for x in lines if x.startswith('[2026-11-12 20:0')]
    heartbeats = [x for x in session if 'steps=11/12' in x and 'Checking available jobs' in x]
    assert len(heartbeats) >= 30
    assert any('stock hands attachment confirmed' in x for x in session)
    assert any('inkFastTravelLoadingState -> inkGameState' in x for x in session)
    assert not any('native representation activation queued' in x for x in session)
    write(out / 'observation.json', {'logs': rows, 'heartbeats': len(heartbeats),
        'first_wait': heartbeats[0], 'last_wait': heartbeats[-1],
        'presentation_activation_logged': False})

if __name__ == '__main__':
    main()
