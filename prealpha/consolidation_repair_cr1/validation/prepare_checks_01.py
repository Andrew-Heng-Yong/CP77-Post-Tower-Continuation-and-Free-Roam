"""Bind regression targets to pre-existing repair contracts, not the CR1 builder."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;W=HERE.parents[2]
AUDIT=W/'diagnostics/sidejob_entry_phone_audit_20261026_01'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
donors=read(AUDIT/'collision_decoded_01/inventory.json')
depots={r['depot'] for r in donors}
depots.update(read(W/'prealpha/sidejob_repair_sr1/candidate_02/build_native_02.json')['resources'])
depots.add(r'towercontinued\judy_dennis_jd1\dennis_phone.questphase')
depots.update(r['depot'] for r in read(W/'prealpha/sidejobs_s30/serialized_02/entries_manifest.json')['entries'])
depots.add(r'towercontinued\sidejob_repair_sr1\en-us.lipmap')
sources=[AUDIT/'collision_decoded_01/inventory.json',
         W/'prealpha/sidejobs_s25/policy/plan02.json',
         W/'prealpha/sidejobs_s25/services/test.py',
         W/'prealpha/sidejobs_s25/families/test.py',
         W/'prealpha/judy_dennis_jd1/test_03.py',
         W/'prealpha/sidejob_repair_sr1/test_native_01.py',
         W/'prealpha/sidejob_repair_sr1/candidate_02/build_native_02.json',
         W/'prealpha/sidejobs_s30/serialized_02/entries_manifest.json',
         W/'prealpha/sidejobs_s30/prepared_02/contracts.json',
         W/'prealpha/sidejobs_s30/candidate_02/manifest.json']
for r in donors:
    assert sha(Path(r['donor_raw']))==r['donor_sha256']
    sources.extend([Path(r['donor_raw']),Path(r['donor_json'])])
result={'status':'INDEPENDENT_PREEXISTING_REPAIR_CONTRACT_INPUTS','depots':sorted(depots),
        'sources':{p.relative_to(W).as_posix():sha(p) for p in sources},
        'expectation':'Thirty corrective donor payloads, original S25/SR1/JD1 conditions and native routes, and retained S30 content. No CR1 generator output is an expected semantic input.'}
p=HERE/'checks_contract_01.json';encoded=json.dumps(result,indent=2)+'\n'
if p.exists():assert p.read_text()==encoded
else:p.write_text(encoded)
print(json.dumps({'resources_to_decode':len(depots),'independent_source_pins':len(result['sources'])}))
