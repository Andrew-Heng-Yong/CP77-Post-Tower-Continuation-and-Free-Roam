"""Derive scanner owners from stock district wiring and actual POI variants."""
import argparse, json, sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'prealpha/ncpd_scanner_n1'))
from native_inspect import SafeResource, flatten
from catalog import journal, JP
from catalog_gig_rollout_r2 import read,sha,walk,value
OUT=ROOT/'research/ncpd_scanners_n2'
PARENTS=ROOT/'research/ncpd_scanner_n1/parents_02/json'
ENCOUNTERS=ROOT/'research/ncpd_scanner_n1/encounters_02/json'
def relative(p):return p.relative_to(ROOT).as_posix()
def load(p):
 r=SafeResource(read(p));return r,{g['path']:g for g in flatten(r,r.obj['Data']['RootChunk'])}
def ns(g):return {n['id']:n for n in g['nodes']}
def closure(edges,starts,reverse=False,stop=()):
 seen=set();pending=list(starts)
 while pending:
  i=pending.pop()
  if i in seen:continue
  seen.add(i)
  if i in stop:continue
  pending.extend(e[0] if reverse else e[2] for e in edges if e[3]!='CutDestination' and (e[2] if reverse else e[0])==i)
 return seen
def facts(root):return sorted({v['factName'] for v in walk(root) if isinstance(v.get('factName'),str)})
def main(revision):
 OUT.mkdir(parents=True,exist_ok=True);dest=OUT/f'catalog_{revision}.json'
 assert not dest.exists(),'preserve old evidence'
 pois=journal();lib={}
 for folder in (PARENTS,ENCOUNTERS):
  for p in folder.rglob('*.json'):
   r,gs=load(p);d=str(p.relative_to(folder))[:-5].replace('/','\\');lib[d]=(p,r,gs)
 rows=[];issues=[];all_refs=[]
 for p in PARENTS.rglob('*.json'):
  if p.name in ('open_world_minor_activities.questphase.json','badlands_minor_activities.questphase.json','bls_ina_custom_minor_activities.questphase.json'):continue
  r,gs=load(p);g=gs['root'];n=ns(g);edges=g['edges']
  inputs=[x['id'] for x in n.values() if x['$type']=='questInputNodeDefinition' and value(x['socketName']) in ('In1','In2')]
  assert len(inputs)==1,(p,inputs)
  phases={i for i,v in n.items() if v['$type']=='questPhaseNodeDefinition'}
  # Inline utility phases (e.g. Pacifica's outside-area wait) are not a
  # separate encounter and must remain on the stock startup path.
  barriers={i for i in phases if value(n[i].get('phaseResource',{}).get('DepotPath')) not in (None,'0',0)}
  initial=closure(edges,inputs,stop=barriers)
  for child in sorted(phases & initial):
   dep=value(n[child].get('phaseResource',{}).get('DepotPath'));own=lib.get(dep)
   # Kabuki has one inline owner; inspect its actual nested graph too.
   if dep in (None,'0',0):
    graphs={k:v for k,v in gs.items() if k.startswith(f'root/{child}')};source=relative(p)
   elif own:
    source=relative(own[0]);graphs=own[2]
   else:
    issues.append({'parent':relative(p),'child':child,'unresolved':dep});continue
   payloads=[v for gg in graphs.values() for v in gg['nodes']]
   paths={v['realPath'] for v in walk(payloads) if 'realPath'in v}
   pre=[e for e in edges if e[2]==child and e[0] in initial and e[3]!='CutDestination']
   assert len(pre)==1,(p,child,pre)
   mapnode=n[pre[0][0]]
   parentpoi=mapnode.get('type',{}).get('path',{}).get('realPath') if mapnode['$type']=='questJournalNodeDefinition' else None
   hits=sorted(({parentpoi} if parentpoi in pois else set())|(paths&pois.keys()))
   all_refs.append({'parent':relative(p),'child':child,'depot':dep,'pois':hits})
   if not hits:continue
   # Prefix contains only input/waits/conditions/hubs and this map; other owners
   # are terminal during startup traversal. Preserve output cleanup/retry edges.
   entry=mapnode['id'] if parentpoi in pois else child
   upstream=closure(edges,[entry],reverse=True,stop=barriers-{entry}) & initial
   downstream=closure(edges,[child])
   selected=upstream|downstream
   extra_phases=(selected & phases)-{child}
   if extra_phases & barriers:issues.append({'parent':relative(p),'child':child,'other_phase_in_slice':sorted(extra_phases & barriers)})
   for i in extra_phases:
    payloads.extend(v for k,gg in gs.items() if k.startswith(f'root/{i}') for v in gg['nodes'])
   writes=[v for v in walk(payloads) if v.get('$type')=='questSetVar_NodeType']
   start=sorted({v['factName'] for v in writes if v['factName'].endswith(('_start','_started')) and v.get('value',0)>0})
   finish=sorted({v['factName'] for v in writes if v['factName'].endswith(('_finished','_done')) and v.get('value',0)>0})
   scenes=sorted({value(v['sceneFile']['DepotPath']) for v in walk(payloads) if 'sceneFile'in v})
   refs=sorted({value(v['phaseResource']['DepotPath']) for v in walk(payloads) if 'phaseResource'in v}-{None,'0',0})
   key=pois[parentpoi]['id'] if parentpoi in pois else pois[hits[0]]['id']
   rows.append({'key':key,'pois':[pois[h]|{'path':h} for h in hits], 'parent':relative(p),'parent_depot':str(p.relative_to(PARENTS))[:-5].replace('/','\\'),
    'input':inputs[0],'child':child,'entry':entry,'native_depot':dep,'source':source,'selected_nodes':sorted(selected),
    'startup_nodes':sorted(upstream),'outputs':[e for e in edges if e[0]==child],
    'admission_edges':[e for e in edges if e[2]==entry and e[0] in upstream-{entry}],
    'native_input':pre[0][3],'start_facts':start,'finish_facts':finish,'facts':facts(payloads),'scenes':scenes,'phase_refs':refs,
    'writes':writes,'prefix_payloads':[n[i] for i in sorted(upstream-{child})],
    'nested_graphs':[k for k in gs if k!='root' and int(k.split('/')[1]) in selected],
    'root_prefabs':r.obj['Data']['RootChunk']['phasePrefabs'],
    'extra_parent_gate':'sts_bls_ina_tier_1' if '/badlands/'in relative(p) else None})
 covered={p['path'] for row in rows for p in row['pois']}
 report={'status':'CATALOG_NOT_IMPLEMENTATION','rows':rows,'issues':issues,'unbound':[v|{'path':p} for p,v in pois.items() if p not in covered],
  'all_parent_refs':all_refs,'sources':{relative(p):sha(p) for p,_,_ in lib.values()},'journal_source':relative(JP),'journal_sha256':sha(JP)}
 dest.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'rows':len(rows),'covered':len(covered),'types':dict(Counter(p['variant'] for r in rows for p in r['pois'])),
  'issues':issues,'unbound':report['unbound'],
  'exceptions':[{k:r[k] for k in ('key','start_facts','finish_facts','phase_refs','outputs','admission_edges')} for r in rows if not r['start_facts'] or not r['finish_facts'] or len(r['admission_edges'])!=1 or r['phase_refs'] or len(r['outputs'])>1],
  'scene_count':len({s for r in rows for s in r['scenes']})},indent=2))
if __name__=='__main__':main(sys.argv[1])
