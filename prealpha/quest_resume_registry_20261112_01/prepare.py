"""Pin current installation and reusable exports for a read-only quest census."""
import hashlib
import json
import re
import stat
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MANIFEST = ROOT / 'prealpha/quest_history_autoload_20261112_01/deployment_01/installed_manifest_01.json'
SELECTION = ROOT / 'research/gig_restoration/lore_whitelists_v6_3_prophet_exclusion.json'

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8-sig'))

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest().upper()

def write(p, data):
    with Path(p).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')

def plain(p):
    for x in (p, *p.parents):
        assert not x.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT, x

def main():
    out = HERE / 'evidence_01'
    assert not out.exists(), 'Use a fresh output'
    m = read(MANIFEST)
    game = Path(m['game_root'])
    checks = []
    for r in m['core_files'] + m['required_files']:
        p = game / r['path']
        plain(p)
        h = sha(p)
        assert h == r['sha256'] and p.stat().st_size == r['bytes'], p
        checks.append({'path': str(p), 'sha256': h, 'bytes': p.stat().st_size})
    selection = read(SELECTION)
    script = game / 'r6/scripts/PTFR_Consolidated/PTFR_HistorySnapshotHS1.reds'
    text = script.read_text(encoding='utf-8-sig')
    snapshot = {int(i): q for i,q in re.findall(r'func ID(\d+)\(\) -> String \{ return "([^"]+)";', text)}
    assert len(snapshot) == 158 and sorted(snapshot) == list(range(158))
    # Reuse only exports whose raw payload equals the freshly extracted provider.
    # Capture verifies the export bytes against their recorded checksum before reuse.
    caches = []
    pins = []
    for p in sorted((ROOT/'prealpha').glob('johnny_dialogue_index_*/evidence_*/exports*.jsonl')):
        pins.append({'path': str(p), 'sha256': sha(p)})
        for line in p.read_text(encoding='utf-8-sig').splitlines():
            r = json.loads(line)
            if r.get('status') == 'EXPORTED' and r.get('json') and r.get('json_sha256'):
                caches.append({k:r.get(k) for k in ['depot','sha256','json','json_sha256','root_type']})
    out.mkdir()
    write(out/'prepared.json', {'schema':1,'scope':'Step 1 static restoration registry; no game/save mutation',
        'core_epoch':m['core_epoch'],'game_root':str(game),'manifest':str(MANIFEST),
        'manifest_sha256':sha(MANIFEST),'selection':str(SELECTION),'selection_sha256':sha(SELECTION),
        'checks':checks,'cache_pins':pins,'cached_exports':caches,
        'snapshot': [{'index':i,'id':q} for i,q in sorted(snapshot.items())]})
    write(out/'selection.json', {'rows':selection['decision_registry'], 'snapshot':snapshot,
        'counts':dict(Counter(r['decision'] for r in selection['decision_registry'])),
        'policy_notice':'Only row selection and explicit prerequisites are used. Historical restart/Johnny prose is superseded by current PROJECT and user decisions.'})
    print(json.dumps({'verified_files':len(checks),'snapshot_rows':len(snapshot),'selection_rows':len(selection['decision_registry']),
        'selection_counts':dict(Counter(r['decision'] for r in selection['decision_registry'])),'cached_exports':len(caches)}))

if __name__ == '__main__': main()
