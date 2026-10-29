exec(open('prealpha/world_support_wa3/combat_review/review_lifecycle_01.py').read().split('for r in rows:')[0])
for i in [1211,1220,1235,1237,1238,1242,1243]:
 g=next(g for g in groups if g['id']==i);ps=cache[g['source']];p=ps[g['node_path']];print('ID',i)
 for n in p['payload']['phaseGraph']['nodes']:
  if n['id'] in [25,41,42,43,97,95] and ('condition' in n or n['$type']=='questLogicalHubNodeDefinition'):print(n['id'],json.dumps(n))
 print('outputs',[n for n in p['payload']['phaseGraph']['nodes'] if n['$type']=='questOutputNodeDefinition'])
 if i==1242:
  for path in ['root','root/20']:
   p=ps[path];print(path,[(n['id'],n.get('condition')) for n in p['payload']['phaseGraph']['nodes'] if 'condition'in n],p['edges'])
