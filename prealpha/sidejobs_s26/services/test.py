"""Validate the evidence-labelled roster; not a gameplay or restart test."""
import copy, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def check(m):
    inv=read(ROOT/'research/sidejobs_s21_failed/inventory_02.json')['jobs']
    assert m['whitelist_count']==len(m['rows'])==58
    assert len({r['id'] for r in m['rows']})==58
    assert {r['id']:r['journal_path'] for r in m['rows']}=={r['id']:r['journal_path'] for r in inv}
    assert not m['runtime_changes'] and not m['game_writes'] and not m['save_writes']
    assert m['generator_sha256']==sha(ROOT/'prealpha/sidejobs_s26/services/audit.py')
    for rel,digest in m['sources'].items():
        p=(ROOT/rel).resolve()
        assert p.is_relative_to(ROOT.resolve()) and p.is_file()
        assert sha(p)==digest,rel
    for r in m['rows']:
        assert r['npc_services'] and r['treatment'] and r['unverified'] and r['evidence_files']
        assert r['scanned_resources']>0,r['id']
        assert r['live_service_proof'] is False and r['restart_safety_proof'] is False
        assert all(p in m['sources'] for p in r['evidence_files'])
        if r['classification'].startswith('unimplemented_'): assert not r['bounded_routes']
    assert sum(not r['bounded_routes'] for r in m['rows'])==6

def main(revision):
    path=ROOT/f'research/sidejobs_s26/services/matrix_{revision}.json'
    m=read(path);check(m)
    mutations=[lambda x:x['rows'].pop(),
               lambda x:x['rows'].__setitem__(0,copy.deepcopy(x['rows'][1])),
               lambda x:x.update(game_writes=True),
               lambda x:x['rows'][0].update(live_service_proof=True),
               lambda x:x['rows'][0].update(restart_safety_proof=True),
               lambda x:x['rows'][0].update(scanned_resources=0),
               lambda x:x['sources'].update({'../outside':'0'*64})]
    for change in mutations:
        bad=copy.deepcopy(m);change(bad)
        try:check(bad)
        except AssertionError:continue
        raise AssertionError('negative fixture admitted')
    result={'status':'PASS_SERVICE_INVENTORY_NOT_GAMEPLAY_PROOF','roots':58,
      'native_resources_scanned_sum':sum(r['scanned_resources'] for r in m['rows']),
      'source_pins':len(m['sources']),'negative_cases':len(mutations),
      'matrix_sha256':sha(path),'tester_sha256':sha(Path(__file__)),
      'new_runtime_resources':0,'game_writes':False,'save_writes':False}
    out=path.with_name(f'tests_{revision}.json');assert not out.exists()
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result))
if __name__=='__main__': main(sys.argv[1])
