"""Reject a flattened-fact false positive using the actual nested guard."""
from pathlib import Path
import sys,copy
W=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
R=O/'shared/tier3_condition_readback_01';pin=read(R/'pin.json');assert sha(pin['raw'])==pin['sha256']and sha(pin['json'])==pin['json_sha256']
doc=read(pin['json']);m=Resource(doc).normalize();n=m['graphs']['root/50']['nodes']['65000'];c=n['payload']['condition'];facts={x['factName']:x['value']for x in n['reads']if'factName'in x}
def ev(c,f):
 if c['$type']=='questLogicalCondition':return (all if c['operation']=='AND'else any)(ev(x,f)for x in c['conditions'])
 if c['$type']=='questFactsDBCondition':return ev(c['type'],f)
 assert c['$type']=='questVarComparison_ConditionType'and c['comparisonType']=='Equal'
 return f.get(c['factName'],0)==c['value']
rows=[]
for six,seven in [(0,1),(1,0),(0,0),(1,1)]:
 ff=facts|{'PTFRU9_sts_ep1_06_Request':six,'PTFRU9_sts_ep1_06_Permit':six,'PTFRU9_sts_ep1_07_Request':seven,'PTFRU9_sts_ep1_07_Permit':seven};actual=ev(c,ff);assert actual==bool(six or seven);rows.append({'06_pair':six,'07_pair':seven,'actual_guard':actual})
# Actual raw guard handle mutation, rather than changing an abstract expected flag.
bad=copy.deepcopy(doc);rr=Resource(bad);rg=rr.d(rr.root['graph']);phase=next(rr.d(h)for h in rg['nodes']if rr.d(h)['id']==50);bg=rr.d(phase['phaseGraph']);node=next(rr.d(h)for h in bg['nodes']if rr.d(h)['id']==65000);top=rr.d(node['condition']);pair=rr.d(top['conditions'][-1]);assert pair['operation']=='OR';pair['operation']='AND';bm=Resource(bad).normalize();bc=bm['graphs']['root/50']['nodes']['65000']['payload']['condition'];witness=facts|{'PTFRU9_sts_ep1_06_Request':0,'PTFRU9_sts_ep1_06_Permit':0,'PTFRU9_sts_ep1_07_Request':1,'PTFRU9_sts_ep1_07_Permit':1};assert ev(c,witness)and not ev(bc,witness)
out=R/'disjunction_tests.json';assert not out.exists()
write(out,{'status':'PASS_ACTUAL_OR_NOT_JOINT_FRESH_COHORT','fixtures':rows,'actual_raw_mutation_detected':True,'source_pins':pin,'checker_sha256':sha(__file__),'resolution':'Current gate is OR of two request/permit AND pairs. A flattened set containing all four names does not require both jobs. Proposed cohort deadlock hypothesis rejected; no runtime change.','limits':'Facts are explicit fixture values, not inferred save history or engine delivery proof. Native message timing/adoption remain source-specific separate contracts.'})
print({'status':'PASS_ACTUAL_OR_NOT_JOINT_FRESH_COHORT','fixtures':4,'raw_mutations':1})
