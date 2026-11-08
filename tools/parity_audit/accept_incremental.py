"""Reuse independent closure only when all prior exports remain exactly pinned.
Read newly decoded exports independently; verify all requested and binary refs queried.
"""
from common import *
def accept(o,previous,current,prior_check):
 a=read(o/previous);b=read(o/current);check=read(o/prior_check);known={(r.get('json'),r.get('json_sha256')) for r in a['resources'] if r.get('json')};queried={r['depot'] for r in b['resources']}|set(b['missing']);old={(r['depot'],r['archive'],r.get('sha256'),r.get('json_sha256')) for r in a['resources']};new={(r['depot'],r['archive'],r.get('sha256'),r.get('json_sha256')) for r in b['resources']};assert old<=new,'Reused provider evidence changed'
 refs=set(check['not_queried']);seen=set()
 for r in b['resources']:
  if r.get('json') and (r['json'],r['json_sha256'])not in known and r['json']not in seen:
   seen.add(r['json']);assert sha(r['json'])==r['json_sha256'];refs.update(depots(read(r['json'])))
 refs={d for d in refs if d.lower()not in ('none','0','')};missing=sorted(refs-queried)
 if missing or b['truncated']:
  number=int(re.search(r'pass_(\d+)',current)[1])+1;name=f'pass_{number:02d}';n=o/name;assert not n.exists(),'Fresh pass required';n.mkdir();q=read(o/'queries.json');q['wanted']=sorted(refs|{r['depot'] for r in b['resources']}|set(b['truncated']));q['cache'] += [r for r in b['resources'] if r.get('json')];write(n/'queries.json',q);write(n/'prepared.json',read(o/'prepared.json'))
  report={'capture':current,'prior_independent_check':prior_check,'not_queried':missing,'new_exports_independently_read':len(seen),'next_pass':name,'resume_capture':current};write(o/('incremental_closure_'+Path(current).parent.name+'.json'),report);print(json.dumps(report));return
 proof={'capture':current,'prior_independent_check':prior_check,'prior_capture':previous,'old_provider_records_retained':len(old),'new_exports_independently_read':len(seen),'new_references_unqueried':missing,'queried_missing':len(b['missing']),'accepted_for_analysis':True,'scope':'Incremental extension of complete independent JSON traversal; original missing/decode/semantic limits remain'}
 write(o/'final_closure_check.json',proof);write(o/'capture_pointer.json',{'capture':current,'closure_check':'final_closure_check.json','missing':b['missing'],'truncated':b['truncated'],'accepted_for_analysis':True});print(json.dumps(proof))
if __name__=='__main__':
 import sys
 accept(Path(sys.argv[1]),sys.argv[2],sys.argv[3],sys.argv[4])
