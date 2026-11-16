"""RD1 build helpers. Importing defines functions; it performs no file writes."""
from pathlib import Path
import hashlib
import json
import stat

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE = ROOT / 'prealpha/history_file_loader_hs4_20261112_01/deployment_01/installed_manifest_01.json'
BASELINE_SHA = '638948D80D2AEA77BF78F04B70E8C4914E4941A6812B9AA359E004FD326BB38C'
REGISTRY = ROOT / 'prealpha/quest_resume_registry_20261112_01/registry_02/registry.sqlite3'
RED_DIR = 'r6/scripts/PTFR_Consolidated'
HISTORY = RED_DIR + '/PTFR_HistorySnapshotHS1.reds'


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
    manifest = read(BASELINE)
    assert manifest['core_epoch'] == 'HS4_GLOBAL_LATEST_HISTORY'
    game = Path(manifest['game_root'])
    for row in manifest['core_files'] + manifest['required_files']:
        path = game / row['path']
        plain(path)
        assert sha(path) == row['sha256'], path
    return manifest, game
