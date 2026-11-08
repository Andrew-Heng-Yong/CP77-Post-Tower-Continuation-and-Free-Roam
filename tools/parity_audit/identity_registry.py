"""Validate a separate identity-corroboration registry without approving behavior."""
def bind_registry(registry,current,selected_ids):
 result={}
 for qid,rows in registry['mappings'].items():
  if qid not in selected_ids:raise ValueError('Identity registry contains unselected ID: '+qid)
  good=[]
  for r in rows:
   if r.get('status')=='DECLARATION_UNBOUND':continue
   if r['resource'] not in current or current[r['resource']]!=r['resource_sha256']:raise ValueError('Stale identity resource pin: '+r['resource'])
   good.append(r)
  if good:result[qid]=good
 return result
