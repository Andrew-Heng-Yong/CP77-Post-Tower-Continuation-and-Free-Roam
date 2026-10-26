"""Record the requested remainder without changing the pinned selection."""
import hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'research/sidejobs_s29'
OUT.mkdir(parents=True, exist_ok=True)
def read(p): return json.loads((ROOT / p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest().upper()
old = read('research/sidejobs_s28/scope_01.json')['remaining_after_this_batch_if_installed']
catalogue = read('prealpha/history_snapshot_hs1/candidate_01/catalogue.json')
rows = catalogue['rows'] if isinstance(catalogue, dict) else catalogue
byid = {r['id']: r for r in rows}
targets = [{**r, 'snapshot_row': byid[r['id']]} for r in old]
assert len(targets) == 18 and len({r['id'] for r in targets}) == 18
result = dict(status='IMPLEMENTATION_IN_PROGRESS_NOT_INSTALLED', targets=targets,
    selection='research/gig_restoration/lore_whitelists_v6_1_dependencies.json',
    selection_sha256=sha('research/gig_restoration/lore_whitelists_v6_1_dependencies.json'),
    policy=['Preserve completed, failed and earned unfinished progress.',
            'Unstarted jobs enter original beginnings with native eligibility.',
            'Existing issued owners continue; unsupported saved stages defer without restart.',
            'Prerequisites retain native AND/OR outcomes; excluded parents are never replayed.',
            'Prefer pre-ending history; explicit recorded post-ending fallback remains accepted.',
            'Three Sinnerman journals share one owner and native follow-up flow.'],
    game_writes=0, save_writes=0, game_launches=0)
p = OUT / 'scope_01.json'
assert not p.exists(), p
p.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print('S29 scope:', len(targets), 'journals')
