import sys
from pathlib import Path
H=Path(__file__).resolve().parent;W=H.parents[1];sys.path.insert(0,str(W/'prealpha/phone_support_ph1'))
from model import *
C=H/'candidate_01';g=model(C/'owner_readback_01.json');spec=read(C/'build_01.json');guard=g['root']['nodes'][1]['condition'];checks=[]
def run(c,f,j=True):
 t=c['$type']
 if t=='questLogicalCondition':return all(run(x,f,j) for x in c['conditions'])
 if t in ('questFactsDBCondition','questJournalCondition'):return run(c['type'],f,j)
 if t=='questJournalEntryState_ConditionType':return j
 if t=='questVarComparison_ConditionType':
  assert c['comparisonType']=='Equal';return f.get(c['factName'],0)==c['value']
 raise AssertionError(t)
def check(name,ok):
 assert ok,name
 checks.append(name)
f=spec['facts'];check('fresh postTower support',run(guard,f))
for k,v in f.items():
 bad=dict(f);bad[k]=0 if v else 1;check('reject mismatched '+k,not run(guard,bad))
check('incomplete Tower journal',not run(guard,f,False))
for k in ['holo_setup_active','holo_setup_started','holo_interrupt_call','holo_interrupt_call_manual','holo_active_call_interrupted','holo_reset']:
 pending=dict(f);pending[k]=1;check('allow queued or active recovery '+k,run(guard,pending))
for k in ['PTFRPH3_Claimed','PTFRPH3_Entered','PTFRPH3_Ready']:
 saved=dict(f);saved[k]=1;check('serialized owner refuses duplicate '+k,not run(guard,saved))
out={'status':'PASS_STUDIO_ADMISSION_CASES','checks':len(checks),'details':checks,'limitation':'Evaluates serialized conditions; no claim of engine scheduling, actor streaming or save restoration simulation.'}
(C/'state_cases_01.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'],len(checks))
