from model import *
W=Path.cwd();C=W/'prealpha/phone_support_ph1/candidate_03';b=read(C/'build_01.json');q=read(W/'diagnostics/phone_restoration_preparation_20261029_01/queries_01.json')
a=[]
for r in q['repair_controls']:
 p=C/'archive_source'/r['depot'];a.append({'depot':r['depot'],'preserved_bytes':sha(p)==r['after'],'planned_change':r['depot'] in b['resources']})
assert all(x['preserved_bytes'] or x['planned_change'] for x in a)
(C/'cr1_controls_01.json').write_text(json.dumps(a,indent=2)+'\n');print(sum(x['preserved_bytes'] for x in a),'of',len(a),'byte-exact', [x['depot'] for x in a if not x['preserved_bytes']])
