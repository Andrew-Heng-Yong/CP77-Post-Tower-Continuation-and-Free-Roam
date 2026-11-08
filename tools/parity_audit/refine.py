"""Independent exported-JSON reference closure check, separate from binary extraction."""
from common import *
def refine(w,o,capture_relative,next_name):
 cap=read(o/capture_relative);q=read(o/'queries.json');available={r['depot'] for r in cap['resources']};refs=set();seen=set();errors=[]
 for r in cap['resources']:
  if not r.get('json') or r['json']in seen:continue
  seen.add(r['json'])
  try:refs.update(depots(read(r['json'])))
  except (ValueError,OSError) as e:errors.append({'json':r['json'],'error':str(e)})
 missing=sorted(refs-available-set(cap['missing']));report={'capture':capture_relative,'exports_independently_read':len(seen),'json_depot_references':len(refs),'not_queried':missing,'queried_missing':cap['missing'],'errors':errors,'scope':'Phase/scene exported references; asset internals and dynamic script references remain separate limitations'}
 write(o/(next_name+'_closure_check.json'),report)
 if missing:
  n=o/next_name;assert not n.exists(),'Fresh pass directory required';n.mkdir()
  q['wanted']=sorted(set(q['wanted'])|refs|{r['depot'] for r in cap['resources']});q['cache']+=[r for r in cap['resources'] if r.get('json')]
  write(n/'queries.json',q);write(n/'prepared.json',read(o/'prepared.json'))
 else:write(o/'capture_pointer.json',{'capture':capture_relative,'closure_check':next_name+'_closure_check.json','missing':cap['missing'],'truncated':cap['truncated'],'accepted_for_analysis':not errors})
 print(json.dumps({'independent_json_refs':len(refs),'new_queries':len(missing),'next_pass':next_name if missing else None,'missing_already_queried':len(cap['missing'])}))
