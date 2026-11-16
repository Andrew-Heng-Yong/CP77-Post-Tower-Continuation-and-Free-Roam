"""Read-only pins for the installed RD4 baseline."""
from pathlib import Path
import hashlib
import json
import stat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = ROOT / 'prealpha/resume_dispatcher_rd4_20261113_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA = '3DDA172011D2049A0EDBC4E006E6F40AE79F8751B23FAF0BEBCDC1706A62F0BC'

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')

def plain(path):
    for entry in (path, *path.parents):
        assert not entry.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, entry

def baseline():
    assert sha(BASELINE) == BASELINE_SHA
    m = read(BASELINE)
    assert m['core_epoch'] == 'RD4_BEAT_ON_THE_BRAT_RESUME'
    game = Path(m['game_root'])
    assert len(m['core_files']) == 51 and len(m['required_files']) == 26
    for row in m['core_files'] + m['required_files']:
        p = game / row['path']
        plain(p)
        assert sha(p) == row['sha256'], p
    return m, game
