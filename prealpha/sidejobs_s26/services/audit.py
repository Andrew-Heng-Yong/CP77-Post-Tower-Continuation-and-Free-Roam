"""Read-only service dependency audit; no activation, reset or deployment code."""
from __future__ import annotations
import collections, hashlib, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'research/sidejobs_s26/services'
PINS = {}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(rel):
    p = ROOT / rel
    PINS[p.relative_to(ROOT).as_posix()] = sha(p)
    return json.loads(p.read_text(encoding='utf-8-sig'))
def walk(value):
    yield value
    if isinstance(value, dict):
        for sub in value.values(): yield from walk(sub)
    elif isinstance(value, list):
        for sub in value: yield from walk(sub)
def strings(value): return {v for v in walk(value) if isinstance(v, str)}

NATIVE_ROOTS = [
 'research/activity_state_r3/native_sources/json',
 'research/sidejobs_s2/sacrum_audit/native_01/json',
 'research/sidejobs_s23/native_01/json',
 'research/sidejobs_s23/base_a/native_02/json',
 'research/sidejobs_s23/support/native_01/json',
 'research/sidejobs_s23/ep1/native_03/json',
 'research/sidejobs_s24/base/native_01/json',
 'research/sidejobs_s24/ep1/native_01/json',
 'research/sidejobs_s24/services/native_01/json',
 'research/sidejobs_s24/support/native_01/json',
 'research/sidejobs_s25/services/native_01/json',
 'research/sidejobs_s25/families/native_01/json',
 'research/b0_vendor_rollout/special_scene_sources/json',
]
EXTRA_SEEDS = {
 'mq306_dumpster': ['ep1\\quest\\minor_quests\\mq306\\mq306.questphase'],
 'q304_splinter_stash': ['ep1\\quest\\main_quests\\q304\\phases\\q304_slider_stash.questphase'],
 'wst_ep1_05': ['ep1\\openworld\\world_stories\\wst_ep1_05\\wst_ep1_05.questphase', 'ep1\\quest\\tertiary_characters\\default_dialogs\\hasan_default\\sts_04_hasan_default.questphase'],
 'wst_ep1_04': ['ep1\\openworld\\world_stories\\wst_ep1_04\\wst_ep1_04.questphase'],
 'mq046_cave_vehicle': ['base\\open_world\\minor_activities\\badlands\\inland_avenue_se1\\ma_bls_ina_se1_40\\ma_bls_ina_se1_40_phase.questphase'],
 'mq047_ad_vehicle': ['base\\open_world\\minor_activities\\badlands\\inland_avenue_se1\\ma_bls_ina_se1_44\\ma_bls_ina_se1_44_phase.questphase'],
 'sts_ep1_08_steven_meeting_night_city': ['ep1\\quest\\tertiary_characters\\default_dialogs\\steven_santos_default\\steven_default.questphase'],
 '07_nc_underground': ['base\\quest\\side_quests\\sq024\\sq024.questphase'],
}
CONTRACTS = [
 'prealpha/sidejobs_s23/base_a_v2/contract.json',
 'prealpha/sidejobs_s23/base_b/contract.json',
 'prealpha/sidejobs_s23/ep1/contract.json',
 'prealpha/sidejobs_s24/base/contract03.json',
 'prealpha/sidejobs_s24/ep1/contract02.json',
 'prealpha/sidejobs_s24/services/contract.json',
 'prealpha/sidejobs_s25/services/contract02.json',
 'prealpha/sidejobs_s25/families/contract03.json',
 'prealpha/sidejobs_s25/prophet/contract.json',
]

def native_index():
    index = {}
    for folder in NATIVE_ROOTS:
        base = ROOT / folder
        if not base.exists(): continue
        for p in base.rglob('*.json'):
            rel = p.relative_to(base).as_posix()
            if not rel.startswith(('base/', 'ep1/')): continue
            key = rel[:-5].replace('/', '\\').lower()
            index[key] = p.relative_to(ROOT).as_posix()
    return index

def resource_refs(data):
    return sorted(s.lower().replace('/', '\\') for s in strings(data)
                  if s.lower().startswith(('base\\', 'ep1\\', 'base/', 'ep1/'))
                  and s.lower().endswith(('.questphase', '.scene')))

def closure(seeds, index):
    pending = list(seeds); seen = set(); loaded = {}; unresolved = set()
    while pending:
        key = pending.pop().replace('/', '\\').lower()
        if key in seen: continue
        seen.add(key)
        rel = index.get(key)
        if not rel:
            unresolved.add(key); continue
        data = read(rel); loaded[key] = data
        pending.extend(resource_refs(data))
    return loaded, sorted(unresolved)

def main(revision):
    inventory = read('research/sidejobs_s21_failed/inventory_02.json')['jobs']
    coverage = read('prealpha/sidejobs_s25/build/s25_04/coverage.json')
    covered = {r['id']: r for r in coverage['jobs']}
    index = native_index()
    contracts = collections.defaultdict(list)
    for path in CONTRACTS:
        c = read(path)
        for owner in c.get('owners', [c]):
            for id in owner.get('ids', [owner.get('id')]):
                if id: contracts[id].append((path, owner))
    treatments = read('prealpha/sidejobs_s26/services/treatments.json')
    manual = {}
    for group in treatments['groups']:
        for id in group['ids']:
            assert id not in manual, id
            manual[id] = group
    assert set(manual) == {j['id'] for j in inventory}, set(manual) ^ {j['id'] for j in inventory}
    rows = []
    for job in inventory:
        id = job['id']; item = manual[id]
        seeds = set(item.get('native_seeds', [])) | set(EXTRA_SEEDS.get(id, []))
        for ref in job.get('native_parent_refs', []): seeds.add(ref['native_phase'])
        for rel in job.get('native_root_phase_candidates', []):
            m = re.search(r'/json/((?:base|ep1)/.+)\.json$', rel)
            if m: seeds.add(m.group(1).replace('/', '\\'))
        for path, owner in contracts[id]:
            if owner.get('native_depot'): seeds.add(owner['native_depot'])
        loaded, missing = closure(seeds, index)
        evidence = []
        for depot, data in loaded.items():
            vals = strings(data)
            gates = sorted(v for v in vals if re.fullmatch(r'[a-zA-Z0-9_]+',v)
                           and ('default_on' in v or 'vendor' in v or 'ripper' in v or 'QuestOwns' in v))
            contact_paths = sorted(v for v in vals if v.startswith('contacts/'))
            community_refs = sorted(v for v in vals if v.endswith(('.community','.community.xml')))
            if gates or contact_paths or community_refs:
                evidence.append({'depot': depot, 'source': index[depot],
                  'service_or_lifecycle_strings': gates, 'contact_path_strings': contact_paths,
                  'community_reference_strings': community_refs})
        rows.append({'id': id, 'title': job['title'], 'journal_path': job['journal_path'],
          'classification': item['classification'], 'npc_services': item['npc_services'],
          'treatment': item['treatment'], 'evidence_files': item['evidence_files'],
          'unverified': item['unverified'],
          'bounded_routes': covered[id]['bounded_routes'],
          'native_seeds': sorted(seeds), 'scanned_resources': len(loaded),
          'unresolved_references': missing, 'native_reference_evidence': evidence,
          'live_service_proof': False, 'restart_safety_proof': False})
        for file in item['evidence_files']:
            p = ROOT / file
            assert p.is_file(), file
            PINS[file] = sha(p)
    result = {
      'status':'COMPLETE_58_ROOT_SERVICE_INVENTORY_NOT_FULL_EXECUTION_OR_LIVE_PROOF',
      'whitelist_count':58, 'rows':rows,
      'counts':dict(collections.Counter(r['classification'] for r in rows)),
      'policy':'Latest user policy: completed remain completed; unfinished jobs restart from beginning. Restart migration is separately owned. This audit does not reset or start jobs.',
      'limits':[
       'All 58 whitelist roots have an evidence-labelled row; this is not a claim that every transitive asset or every outcome has been audited.',
       'Native reference strings are not proof that a node executes on a selected path. Unresolved dependencies are explicit; absent strings do not prove absent dependencies.',
       'An exact copied NPC scene or open shop is not proof that the quest reward item, eligibility, transaction or completion watcher works.',
       'Do not create duplicate actors or restart default-dialogue/phone roots merely because a quest restarts.',
       'Existing B0 service modifications must remain except separately audited whitelisted quest choices. Johnny visual policy and restriction profile remain unchanged.'
      ],
      'sources': PINS, 'generator_sha256':sha(Path(__file__)),
      'runtime_changes':False, 'game_writes':False, 'save_writes':False
    }
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / f'matrix_{revision}.json'; assert not target.exists()
    target.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'rows':len(rows),'counts':result['counts'],
                      'source_pins':len(PINS),'scanned_resources_sum':sum(r['scanned_resources'] for r in rows)}))
if __name__ == '__main__': main(sys.argv[1])
