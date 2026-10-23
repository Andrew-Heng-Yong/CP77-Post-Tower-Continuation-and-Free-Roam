"""Inventory bounded owners, not proof of all stages or live gameplay."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
def main(revision):
 pins={}
 def read(rel):
  p=ROOT/rel;pins[rel]=sha(p);return json.loads(p.read_text(encoding='utf-8-sig'))
 inv=read('research/sidejobs_s21_failed/inventory_02.json')['jobs']
 jobs={j['id']:{'id':j['id'],'title':j['title'],'bounded_routes':[],'all_stages_supported':False,'live_pass_inferred':False} for j in inv}
 assert len(jobs)==58
 def add(ids,tag,source,kind):
  for id in ids:
   assert id in jobs,id
   row={'owner':tag,'source':source,'coverage':kind}
   if row not in jobs[id]['bounded_routes']:jobs[id]['bounded_routes'].append(row)
 for stage,rel in [('S23','prealpha/sidejobs_s23/build/s23_02/build.json'),('S24','prealpha/sidejobs_s24/build/s24_02/build.json'),('S25',f'prealpha/sidejobs_s25/build/{revision}/build.json')]:
  manifest=read(rel)
  for component in manifest['components']:
   cm=read(component['manifest'])
   if not cm.get('contract'):continue
   path=cm['contract'];contract=read(path)
   for owner in contract.get('owners',contract.get('contracts',[contract])):
    if 'id' not in owner:continue
    add(owner.get('ids',[owner['id']]),owner.get('tag',owner.get('key')),path,
        'bounded fresh entry' if stage in ('S24','S25') else 'existing bounded entry/resume; not every stage')
 # Existing small fresh owners are preserved; no new coverage inferred from markers.
 s2=read('prealpha/sidejobs_s2/build/s2_02/build.json')
 for activity in s2['activities']:
  add([activity['key']],'PTFRS2_'+activity['tag'],'prealpha/sidejobs_s2/build/s2_02/build.json','existing bounded fresh entry')
 # Use the original whitelist's existing-owner mapping for S1 and S22 children,
 # then retain the owner mapping as evidence rather than guessing child names.
 historical=read('research/sidejobs_s23/coverage_01.json')
 for row in historical['jobs']:
  adapter=row.get('existing_adapter') or row.get('existing_parent_adapter')
  if adapter:add([row['id']],adapter,'research/sidejobs_s23/coverage_01.json','existing bounded adapter; not fresh-family proof')
 pending=[{'id':r['id'],'title':r['title']} for r in jobs.values() if not r['bounded_routes']]
 out={'status':'OWNER_COVERAGE_INVENTORY_NOT_ALL_STAGES_OR_LIVE','whitelist_roots':58,
      'roots_with_a_bounded_route':58-len(pending),'uncovered_roots':pending,'jobs':list(jobs.values()),
      'policy':'New activation requires actual Inactive root plus native per-job admission. Existing issued progress remains untouched.',
      'limits':['Coverage is a route inventory, not proof every Inactive or partly completed state is supported.',
                'Native prerequisites, unknown history and shared family progress can defer admission.',
                'Existing user gameplay passes do not imply these newly added routes passed.'],
      'source_pins':pins,'generator_sha256':sha(Path(__file__))}
 target=ROOT/f'prealpha/sidejobs_s25/build/{revision}/coverage.json';assert not target.exists()
 target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:out[k] for k in ('status','whitelist_roots','roots_with_a_bounded_route','uncovered_roots')}))
if __name__=='__main__':main(sys.argv[1])
