"""Resolve identities through corrected donor lineage, exact recipes and journal IDs.
Identity resolution never certifies restoration behavior or legacy-owner activation.
"""
import sys,collections,subprocess
from pathlib import Path
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import *
from engine import Models
b=read(H/'baseline.json');o=Path(b['audit']);current=b['private_resources'];q=read(H/'queue.json');ids={x['id']:x for x in q['quests']};m=read(H/'identity_resolution_01.json')['mappings'];idx=read(o/'resource_inventory.json');cat={r['id']:r for r in read(o/'catalogues.json')['quests']};regs=read(o/'registration_inventory.json')['bindings'];paths={r['path'] for r in regs}
crpath=W/'prealpha/consolidation_repair_cr1/donor_review/selection_01.json';cr=read(crpath);repairs={r['depot']:r for r in cr['rows'] if current.get(r['depot'])==r['selected_sha256']}
for qid,rs in m.items():
 for r in rs:
  if r['status']=='DECLARATION_UNBOUND' and r['resource']in repairs:
   c=repairs[r['resource']];r.update(status='HASH_BOUND_CORRECTED_DONOR',corrected_donor={'selection':str(crpath),'selection_sha256':sha(crpath),'depot':c['depot'],'sha256':c['selected_sha256'],'repair':c['repair'],'rationale':c['rationale']})
def add(qid,r):
 if qid in ids and r['resource']in current:m.setdefault(qid,[]).append({**r,'resource_sha256':current[r['resource']],'registered':r['resource']in paths,'limit':'Exact declared identity/current source correlation, not native ownership or complete quest verification'})
sp=W/'prealpha/sidejobs_s2/build/s2_01/build.json';s2=read(sp)
for r in s2['activities']:
 add(r['key'],{'resource':r['depot'],'native_depot':r['native_depot'],'source':str(sp),'source_sha256':sha(sp),'status':'HASH_BOUND_RECIPE' if current.get(r['depot'])==s2['resources'].get(r['depot']) else 'DECLARATION_UNBOUND','native_nodes':r['selected_nodes']})
qp=read(o/'queries.json')
for source in qp['metadata_sources']:
 p=Path(source['path']);j=read(p)
 if not isinstance(j,dict):continue
 for r in j.get('recipes',[])+j.get('jobs',[]):
  if not isinstance(r,dict) or r.get('id')not in ids:continue
  dep=r.get('depot')
  if dep in current:add(r['id'],{'resource':dep,'native_depot':r.get('native'),'source':str(p),'source_sha256':sha(p),'status':'DECLARED_RECIPE_CURRENT_PATH','limit':'Current path linked to historical recipe; lifecycle and precise deltas remain separate'})
  if r.get('private_native') in current:
   dep='towercontinued\\sidejobs_s29\\entries\\'+r['id']+'.questphase'
   if dep in current and r['private_native']in idx.get(dep,{}).get('refs',[]):add(r['id'],{'resource':dep,'native_depot':r.get('native'),'private_native':r['private_native'],'source':str(p),'source_sha256':sha(p),'status':'EXACT_CURRENT_DISPATCH_REFERENCE'})
 for qid,native in j.get('quests',{}).items():
  dep='towercontinued\\sidejobs_s30\\entries\\'+qid+'.questphase'
  if dep in current:add(qid,{'resource':dep,'native_depot':native,'source':str(p),'source_sha256':sha(p),'status':'DECLARED_RECIPE_CURRENT_PATH'})
# Exact primary journal path is stronger than basename/short-ID heuristics.
for qid,rs in list(m.items()):
 for r in rs:
  if r['status']=='DECLARATION_UNBOUND' and cat[qid].get('journal_path') in idx.get(r['resource'],{}).get('journal_paths',[]):
   r.update(status='EXACT_JOURNAL_IDENTITY',journal_path=cat[qid]['journal_path'],source_json=idx[r['resource']]['json'],source_json_sha256=sha(idx[r['resource']]['json']))
old_gaps=read(o/'catalogue_reconciliation.json')['registry_ids_missing_declaration_and_entry'];resolved={k for k,rs in m.items() if any(r['status']!='DECLARATION_UNBOUND' for r in rs)}
# Resolve remaining older aliases from an exact primary journal gate on a
# registered private admission root, rather than guessing from a quest title.
store=Models(o/'models',Models(o.parent/'models'))
for qid in set(ids)-resolved:
 jp=cat[qid].get('journal_path')
 for dep in ids[qid]['restored_candidates']:
  if dep not in paths or jp not in idx.get(dep,{}).get('journal_paths',[]):continue
  model=store.get(dep)
  if not model:continue
  gates=[{'graph':gp,'node':i} for gp,g in model['graphs'].items() for i,n in g['nodes'].items() if jp in n['journal_paths'] and any(x.get('factName','').startswith('PTFR') and x.get('factName','').endswith(('_Permit','_Request')) for x in n['reads'])]
  if gates:add(qid,{'resource':dep,'journal_path':jp,'source_json':idx[dep]['json'],'source_json_sha256':sha(idx[dep]['json']),'admission_nodes':gates,'status':'EXACT_REGISTERED_JOURNAL_ADMISSION_IDENTITY'})
resolved={k for k,rs in m.items() if any(r['status']!='DECLARATION_UNBOUND' for r in rs)}
generic=read(o/'catalogue_reconciliation.json')['entry_like_bindings_not_mapped']
for binding in generic:
 dep=binding['path'];model=store.get(dep)
 if not model:continue
 for qid in ids:
  jp=cat[qid].get('journal_path')
  gates=[{'graph':gp,'node':i} for gp,g in model['graphs'].items() for i,n in g['nodes'].items() if jp in n['journal_paths'] and any(x.get('factName','').startswith('PTFR') and x.get('factName','').endswith(('_Permit','_Request')) for x in n['reads'])]
  if gates:add(qid,{'resource':dep,'journal_path':jp,'source_json':idx[dep]['json'],'source_json_sha256':sha(idx[dep]['json']),'admission_nodes':gates,'status':'EXACT_GENERIC_BINDING_JOURNAL_IDENTITY'})
generic_results=[{'binding':r,'quest_ids':[k for k,vs in m.items() if any(v['resource']==r['path'] and v['status']!='DECLARATION_UNBOUND' for v in vs)]} for r in generic]
write(H/'identity_resolution_02.json',{'mappings':m,'resolved_identity_candidates':sorted(resolved),'remaining_selected_identity_gaps':sorted(set(ids)-resolved),'original_32_resolved':sorted(set(old_gaps)&resolved),'original_32_remaining':sorted(set(old_gaps)-resolved),'generic_bindings':generic_results,'scope':'Identity declarations and source pins only. Multiple routes and legacy resources remain explicit; no new entry activation or admission policy.'});print(json.dumps({'resolved':len(resolved),'remaining':len(set(ids)-resolved),'original_32_resolved':len(set(old_gaps)&resolved),'original_32_remaining':sorted(set(old_gaps)-resolved),'generic_bindings_resolved':sum(bool(r['quest_ids']) for r in generic_results)}))
