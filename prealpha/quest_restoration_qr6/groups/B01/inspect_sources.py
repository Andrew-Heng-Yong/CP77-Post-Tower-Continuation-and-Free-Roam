"""Normalize fresh binary readbacks and emit bounded inspection records."""
from prepare import *
import argparse
def val(x):return x.get('$value',x)if isinstance(x,dict)else x
def walk(x):
 if isinstance(x,dict):
  yield x
  for v in x.values():yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
def brief(n):
 p=n['payload'];return {'id':n['id'],'type':n['type'].replace('quest',''),'payload':p,'sockets':n['sockets'],'reads':n['reads'],'writes':n['writes'],'refs':n['refs'],'prefabs':n['prefabs'],'journal_paths':n['journal_paths'],'node_refs':n['node_refs']}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('group');a=ap.parse_args();H=W/'prealpha/quest_restoration_qr6/groups'/a.group
 out=H/'inspection_01';assert not out.exists();out.mkdir()
 ex=read(H/'raw_exports_01/manifest.json');models={};pins=[]
 for r in ex:
  assert sha(r['raw'])==r['raw_sha256']
  if r['status']!='EXPORTED':continue
  assert sha(r['json'])==r['json_sha256'];models[r['depot']]=Resource(read(r['json'])).normalize();pins.append(r)
 save(out/'models.json',models);save(out/'pins.json',pins)
 for q in read(H/'selected_inputs.json'):
  token=q['id'].split('_')[0];sel={d:m for d,m in models.items()if '\\'+token+'\\'in d or '\\'+token+'_'in d or d in q['restored_candidates']}
  # mws individual path identity; eliminate broad journal-containing correlation roots.
  if q['id'].startswith('mws_'):sel={d:m for d,m in models.items()if q['id']in d}
  save(out/(q['id']+'.json'),sel)
  txt=[]
  for d,m in sel.items():
   txt.append('\nRESOURCE '+d+'\nPREFABS '+json.dumps(m.get('root_prefabs'))+'\nMETADATA '+json.dumps(m.get('metadata',{}))[:2500])
   for gp,g in m['graphs'].items():
    txt.append('GRAPH '+gp+' entries '+str(g['entries'])+' unreachable '+str(g.get('unreachable_nodes'))+'\nEDGES '+str(g['edges']))
    for i,n in g['nodes'].items():
     txt.append(i+' '+n['type']+' '+json.dumps(n['payload'],ensure_ascii=False))
  (out/(q['id']+'.txt')).write_text('\n'.join(txt),encoding='utf-8')
 print(a.group,len(models),'fresh readbacks normalized; scoped reports generated')
