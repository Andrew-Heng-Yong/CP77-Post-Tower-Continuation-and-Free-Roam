"""Side-effect-free paths, pinned input checks and exclusive evidence writes."""
import hashlib
import json
import stat
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = HERE.parent / 'quest_history_autoload_20261112_01'
REGISTRY = HERE.parent / 'quest_resume_registry_20261112_01'
MANIFEST = BASE / 'deployment_01/installed_manifest_01.json'
RED = 'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
LUA = 'bin/x64/plugins/cyber_engine_tweaks/mods/PTFR_HistorySnapshotHS1/init.lua'
ARCHIVE = 'archive/pc/mod/zzzz_PTFR_Combined.archive'
WK = ROOT / 'research/sidejobs_s28/tooling/wolvenkit_9_1_0/package'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest().upper()

def write(path, obj):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def plain(path):
    for p in (path, *path.parents):
        assert not p.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, p

def baseline():
    m = read(MANIFEST)
    assert m['core_epoch'] == 'QP2_QUEST_HISTORY_AUTOLOAD'
    game = Path(m['game_root'])
    for r in m['core_files'] + m['required_files']:
        p = game / r['path']; plain(p)
        assert p.stat().st_size == r['bytes'] and sha(p) == r['sha256'], p
    return m, game

def one(text, old, new):
    assert text.count(old) == 1, old[:140]
    return text.replace(old, new, 1)

def walk(x):
    if isinstance(x, dict):
        yield x
        for v in x.values(): yield from walk(v)
    elif isinstance(x, list):
        for v in x: yield from walk(v)

def value(x):
    return x.get('$value', x.get('id', x)) if isinstance(x, dict) else x
