exec(open('prealpha/world_support_wa3/combat_review/review_lifecycle_01.py').read().split('for r in rows:')[0])
for r in rows:
 if r['id'] not in [1202,1204,1215,1216,1220,1225,1232,1233,1235,1237,1238,1239,1240,1242,1243,1249]:continue
 g=next(g for g in groups if g['id']==r['id']);p=cache[g['source']][g['node_path']];print('\nID',r['id'],'edges',p['edges'])
 for n in p['payload']['phaseGraph']['nodes']:
  if n['$type']=='questPhaseNodeDefinition':continue
  ty=n.get('type'); print(n['id'],n['$type'],json.dumps(n.get('condition') or n.get('socketName') or n.get('actions') or (ty if isinstance(ty,dict) else ty) or n.get('deletedNodeIds') or ''))
