from prepare import *
from inspect_sources import val,walk
import argparse,copy,collections
def reverse(x):
 if isinstance(x,dict):return{k:reverse(v)for k,v in x.items()if k!='payload_sha256'}
 if isinstance(x,list):return[reverse(v)for v in x]
 if isinstance(x,str):
  if '\\native\\'in x and x.startswith('towercontinued'):return x.split('\\native\\',1)[1]
  if x==r'towercontinued\sidejobs_s28\vehicles\mq050_johnny_start.scene':return r'base\quest\minor_quests\mq050\scenes\mq050_johnny_start.scene'
 return x
def diff(a,b,p=''):
 if type(a)!=type(b):return[(p,a,b)]
 if isinstance(a,dict):return sum((diff(a.get(k),b.get(k),p+'/'+str(k))for k in set(a)|set(b)),[])
 if isinstance(a,list):
  if len(a)!=len(b):return[(p+'/length',len(a),len(b))]
  return sum((diff(x,y,p+'/'+str(i))for i,(x,y)in enumerate(zip(a,b))),[])
 return []if a==b else[(p,a,b)]
def compact(n):
 p=n['payload'];x={'id':n['id'],'type':n['type']}
 if n['reads']:x['reads']=n['reads']
 if n['writes']:x['writes']=n['writes']
 if n['refs']:x['refs']=n['refs']
 if n['journal_paths']:x['journals']=n['journal_paths']
 if n['node_refs']:x['node_refs']=n['node_refs']
 if not (n['reads']or n['writes']or n['refs']or n['journal_paths'])and p.get('type'):x['type_payload']=p['type']
 return x
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('group');a=ap.parse_args();H=W/'prealpha/quest_restoration_qr6/groups'/a.group;M=read(H/'inspection_01/models.json');out=[]
 pairs=[]
 for d,m in M.items():
  if not d.startswith('towercontinued'):continue
  native= d.split('\\native\\',1)[1]if '\\native\\'in d else {r'towercontinued\sidejobs_s28\vehicles\mq050.questphase':r'base\quest\minor_quests\mq050\mq050.questphase',r'towercontinued\sidejobs_s28\vehicles\mq050_johnny_start.scene':r'base\quest\minor_quests\mq050\scenes\mq050_johnny_start.scene'}.get(d)
  if native and native in M:
   ds=diff(reverse(M[native]),reverse(m));pairs.append({'native':native,'restored':d,'differences':ds});out.append('PAIR '+d+' '+str(len(ds))+' DIFFS\n'+json.dumps(ds,ensure_ascii=False)[:20000])
 save(H/'inspection_01/comparisons.json',pairs)
 for q in read(H/'selected_inputs.json'):
  out.append('\nQUEST '+q['id'])
  token=q['id'].split('_')[0]
  for d,m in M.items():
   if d.startswith('towercontinued')or not('\x5c'+token+'\x5c'in d or '\x5c'+token+'_'in d or q['id']in d):continue
   if d.endswith('.scene'):continue
   out.append('RESOURCE '+d+' PF '+str(m['root_prefabs']))
   for gp,g in m['graphs'].items():
    out.append('GRAPH '+gp+' ENTRIES '+str(g['entries'])+' EDGES '+str(g['edges']))
    for n in g['nodes'].values():out.append(json.dumps(compact(n),ensure_ascii=False))
 (H/'inspection_01/compact.txt').write_text('\n'.join(out),encoding='utf-8')
 print('pairs',len(pairs),'differences',sum(len(p['differences'])for p in pairs))
