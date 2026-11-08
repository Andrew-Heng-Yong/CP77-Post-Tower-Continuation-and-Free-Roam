"""Conservative contradiction detection over actual serialized admission predicates.
Unknown condition types are unconstrained, never invented successful evaluations.
"""
import sys,itertools,collections
from pathlib import Path
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import *
from engine import Models,allnodes

class BoundExceeded(Exception):pass
def clauses(x,negate=False):
 if not isinstance(x,dict):return [[]]
 t=x.get('$type','')
 if t=='questLogicalCondition':
  op=x['operation']
  if op=='NOR':op='OR';negate=not negate
  if op not in ('AND','OR'):return [[]]
  rows=[clauses(v,negate) for v in x['conditions']];op=({'AND':'OR','OR':'AND'}[op] if negate else op)
  if op=='OR':return [v for row in rows for v in row]
  out=[[]]
  for row in rows:
   if len(out)*len(row)>512:raise BoundExceeded()
   out=[a+b for a in out for b in row]
  return out
 if t in ('questFactsDBCondition','questJournalCondition'):return clauses(x['type'],negate)
 if t=='questVarComparison_ConditionType':
  op=x['comparisonType'];op={'Equal':'NotEqual','NotEqual':'Equal','Greater':'LessOrEqual','GreaterOrEqual':'Less','Less':'GreaterOrEqual','LessOrEqual':'Greater'}.get(op,op) if negate else op
  return [[(x['factName'],op,x['value'])]]
 if t=='questJournalEntryState_ConditionType':
  path=x.get('path',{}).get('realPath');state={'Inactive':1,'Active':2,'Succeeded':3,'Failed':4}.get(x.get('state'));inv=negate ^ bool(x.get('inverted',False))
  if path and state is not None:return [[('journal:'+str(value(x['path'].get('className','')))+':'+path,'NotEqual' if inv else 'Equal',state)]]
  return [[]]
 if t=='questVarVsVarComparison_ConditionType' and x['factName1']==x['factName2']:
  result=x['comparisonType']in ('Equal','GreaterOrEqual','LessOrEqual');result=not result if negate else result
  return [[]] if result else []
 return [[]]

def contradiction(row,context=None):
 rows=list(row)+[(k,'Equal',v) for k,v in (context or {}).items()];ranges={};not_eq=collections.defaultdict(set)
 for key,op,val in rows:
  lo,hi=ranges.get(key,(-10**15,10**15))
  if op=='Equal':lo=max(lo,val);hi=min(hi,val)
  elif op=='Greater':lo=max(lo,val+1)
  elif op=='GreaterOrEqual':lo=max(lo,val)
  elif op=='Less':hi=min(hi,val-1)
  elif op=='LessOrEqual':hi=min(hi,val)
  elif op=='NotEqual':not_eq[key].add(val)
  ranges[key]=(lo,hi)
  if lo>hi or (lo==hi and lo in not_eq[key]):return {'fact':key,'bounds':[lo,hi],'constraints':[list(x) for x in rows if x[0]==key]}
 return None

def run():
 b=read(H/'baseline.json');o=Path(b['audit']);idx=read(o/'resource_inventory.json');s=Models(o/'models',Models(o.parent/'models'));rows=[];bad=[]
 context={'PostTowerFreeRoamActive':1,'q307_done':1,'q307_finished':1,'q307_2079':1,'q307_main_game_killed':1,'q307_ep1_killed':1,'q307_active':0}
 for d,r in idx.items():
  if not r.get('private') or not r.get('graphs'):continue
  m=s.get(d)
  for gp,i,n in allnodes(m):
   if not any(x.get('factName','').startswith('PTFR') and x.get('factName','').endswith(('_Permit','_Request')) for x in n['reads']):continue
   cond=n['payload'].get('condition')
   if not cond:continue
   try:
    cs=clauses(cond);alone=[contradiction(c) for c in cs];tower=[contradiction(c,context) for c in cs];state='UNSAT' if all(alone) else 'TOWER_UNSAT' if all(tower) else 'NO_KNOWN_CONTRADICTION'
    row={'resource':d,'graph':gp,'node':i,'sha256':r['sha256'],'source_json':r['json'],'status':state,'clauses':len(cs),'contradictions':[x for x in (alone if state=='UNSAT' else tower) if x],'limit':'Integer fact/journal-state predicates solved; unknown/native conditions remain unproved'}
    if state in ('UNSAT','TOWER_UNSAT'):bad.append(row)
   except BoundExceeded:row={'resource':d,'graph':gp,'node':i,'status':'OPAQUE_DNF_BOUND'}
   rows.append(row)
 write(H/'admission_guard_checks_01.json',{'nodes_checked':len(rows),'states':dict(collections.Counter(r['status'] for r in rows)),'contradictions':bad,'nodes':rows});print(json.dumps({'nodes_checked':len(rows),'states':dict(collections.Counter(r['status'] for r in rows)),'contradictions':bad},indent=2))
if __name__=='__main__':run()
