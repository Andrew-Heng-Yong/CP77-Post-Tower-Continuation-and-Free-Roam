from summarize import *
import argparse
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('group');a=ap.parse_args();H=W/'prealpha/quest_restoration_qr6/groups'/a.group;M=read(H/'inspection_01/models.json');out={}
 for q in read(H/'selected_inputs.json'):
  token=q['id'].split('_')[0];priv=[d for d in q['restored_candidates']if d in M];nat=[d for d in M if not d.startswith('towercontinued')and(('\\'+token+'\\'in d or '\\'+token+'_'in d)if not q['id'].startswith('mws_')else q['id']in d)]
  entry=next((d for d in priv if '\\entries\\'in d or d.endswith('_entry.questphase')),priv[0]);em=M[entry];one={'entry':entry,'entry_edges':em['graphs'].get('root',{}).get('edges'), 'guards':{},'native_graphs':{},'parent_matches':[],'handlers':[]}
  for gp,g in em['graphs'].items():
   for i,n in g['nodes'].items():
    if int(i)>=65000 or i=='4':
     if n['reads']:
      one['guards'][gp+':'+i]={'facts':[x for x in n['reads']if'factName'in x],'journal_count':len(n['journal_paths']),'condition':n['payload'].get('condition')}
  candidate_nodes={i:n for i,n in em['graphs'].get('root',{}).get('nodes',{}).items()if int(i)<65000}
  for d,m in M.items():
   if d.startswith('towercontinued')or d in nat:continue
   for gp,g in m['graphs'].items():
    matches=[i for i,n in candidate_nodes.items()if i in g['nodes']and reverse(n)==reverse(g['nodes'][i])]
    if len(matches)>=3:one['parent_matches'].append({'depot':d,'graph':gp,'matched_nodes':matches,'edges':[e for e in g['edges']if e[0]in matches and e[2]in matches],'parent_external_incoming':[e for e in g['edges']if e[2]in matches and e[0]not in matches]})
  for d in nat:
   m=M[d];one['native_graphs'][d]={'prefabs':m['root_prefabs'],'graphs':{gp:{'entries':g['entries'],'edges':g['edges'],'nodes':len(g['nodes']),'unreachable':g.get('unreachable_nodes')}for gp,g in m['graphs'].items()}}
   for gp,g in m['graphs'].items():
    for i,n in g['nodes'].items():
     one['handlers'].append({'depot':d,'graph':gp,'node':i,'incoming':[e for e in g['edges']if e[2]==i],'outgoing':[e for e in g['edges']if e[0]==i],**compact(n)})
  out[q['id']]=one
 save(H/'inspection_01/traces.json',out)
 for q,o in out.items():
  print('\nQUEST',q,'ENTRY',o['entry'],'MATCH',[(x['depot'],x['graph'],len(x['matched_nodes']))for x in o['parent_matches']])
  print('ENTRYEDGES',o['entry_edges'])
  for d,v in o['native_graphs'].items():
   if not d.endswith('.scene'):print('BODY',d,'PF',v['prefabs'],'graphs',[(gp,g['nodes'])for gp,g in v['graphs'].items()])
