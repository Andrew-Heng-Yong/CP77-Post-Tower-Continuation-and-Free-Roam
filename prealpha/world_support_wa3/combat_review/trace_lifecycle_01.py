exec(open('prealpha/world_support_wa3/combat_review/review_lifecycle_01.py').read().split('for r in rows:')[0])
for r in rows:
 if not r['owner_fact_conditions']:continue
 g=next(g for g in groups if g['id']==r['id']);p=cache[g['source']][g['node_path']];nodes={n['id']:n for n in p['payload']['phaseGraph']['nodes']};print('\nID',r['id'])
 for f in r['owner_fact_conditions']:
  start=f['node'];paths=[([start],e) for e in p['edges'] if e[0]==start];results=[]
  while paths:
   path,e=paths.pop(0);z=e[2]
   if z in path:continue
   n=nodes[z];np=path+[z];typ=n['$type'];val=''
   if typ=='questSpawnManagerNodeDefinition':val=','.join(a['type']['action'] for a in n['actions'])
   elif typ=='questOutputNodeDefinition':val=n['socketName']['$value']+':'+str(n.get('type'))
   elif typ=='questWorldDataManagerNodeDefinition':val='variant'
   elif typ=='questPhaseNodeDefinition':val='subphase'
   if val:results.append((np,typ,val))
   if typ not in ['questPhaseNodeDefinition','questOutputNodeDefinition','questConditionNodeDefinition','questPauseConditionNodeDefinition'] and len(np)<9:
    paths += [(np,e) for e in p['edges'] if e[0]==z]
  print(f['condition'],results)
