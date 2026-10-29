exec(open('prealpha/world_support_wa3/combat_review/review_lifecycle_01.py').read().split('for r in rows:')[0])
for i in [1220,1225,1232,1233,1243,1249]:
 g=next(g for g in groups if g['id']==i);p=cache[g['source']][g['node_path']];print('ID',i,'admitted',g['community_refs'],'edges',p['edges'])
 for n in p['payload']['phaseGraph']['nodes']:
  if n['$type']=='questSpawnManagerNodeDefinition':print(n['id'],[(a['type']['action'],a['type'].get('spawnerReference'),a['type'].get('communityEntryPhaseName')) for a in n['actions']])
