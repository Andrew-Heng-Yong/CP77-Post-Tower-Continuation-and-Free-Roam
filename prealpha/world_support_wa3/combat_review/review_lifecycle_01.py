import json,collections,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[2];ns={'__file__':str(W/'prealpha/world_actions_wa2/native_review/census_02.py')};exec((W/'prealpha/world_actions_wa2/native_review/census_02.py').read_text().split('manifest=read(MANIFEST)')[0],ns)
read=ns['read'];groups=read(R/'identity_cohort_01.json')['groups'];cache={};rows=[]
for g in groups:
 if g['source'] not in cache:
  d=read(Path(g['source']));hs=ns['handles'](d);ps=ns['phases']({'$type':'questPhaseNodeDefinition','id':-1,'phaseGraph':d['Data']['RootChunk']['graph'],'phaseInstancePrefabs':[]},'root',hs);cache[g['source']]={p['path']:p for p in ps}
 ps=cache[g['source']];ances=[]
 paths=g['node_path'].split('/');prefix='root'
 for k in paths[1:]:
  p=ps[prefix];nodes=p['payload']['phaseGraph']['nodes'];dest=int(k);rev={};
  for e in p['edges']:rev.setdefault(e[2],set()).add(e[0])
  seen={dest};queue=[dest]
  while queue:
   for q in rev.get(queue.pop(),[]):
    if q not in seen:seen.add(q);queue.append(q)
  facts=[]
  for n in nodes:
   if n['id'] not in seen:continue
   for path,v in ns['walk'](n.get('condition',{})):
    if isinstance(v,dict) and v.get('$type')=='questVarComparison_ConditionType':facts.append({'node':n['id'],'condition':v,'incoming':[e for e in p['edges'] if e[2]==n['id']],'outgoing':[e for e in p['edges'] if e[0]==n['id']]})
  ances.append({'path':prefix,'child':dest,'edges':p['edges'],'preceding_fact_conditions':facts,'ancestor_node_ids':sorted(seen)})
  prefix+='/'+k
 # Direct owner fact conditions affect support lifetime if they terminate it; nested child facts do not by themselves.
 p=ps[g['node_path']];direct=[]
 for n in (p['payload'].get('phaseGraph') or {}).get('nodes',[]):
  for path,v in ns['walk'](n.get('condition',{})):
   if isinstance(v,dict) and v.get('$type')=='questVarComparison_ConditionType':direct.append({'node':n['id'],'condition':v,'outgoing':[e for e in p['edges'] if e[0]==n['id']]})
 rows.append({'id':g['id'],'source':g['source'],'node_path':g['node_path'],'ancestors':ances,'owner_fact_conditions':direct,'owner_output_nodes':[{'id':n['id'],'name':n.get('socketName'),'type':n.get('type')} for n in (p['payload'].get('phaseGraph') or {}).get('nodes',[]) if n['$type']=='questOutputNodeDefinition'],'owner_edges':p['edges']})
(R/'lifecycle_inventory_01.json').write_text(json.dumps({'source_count':len(cache),'rows':rows},indent=2)+'\n',newline='\n')
for r in rows:
 facts=[(x['path'],f['node'],f['condition']) for x in r['ancestors'] for f in x['preceding_fact_conditions']];of=r['owner_fact_conditions']
 if facts or of:print(r['id'],r['node_path'],'ancestor',json.dumps(facts),'owner',json.dumps(of))
