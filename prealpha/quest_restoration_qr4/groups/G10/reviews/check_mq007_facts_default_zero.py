"""Correct the earlier conservative missing-fact fixture; source unchanged."""
from pathlib import Path
import sys,json,argparse
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha
from model import Resource
BASE=H/'MQ007_serialized'
def evaluate(c,f):
 if c['$type']=='questLogicalCondition':
  a=[evaluate(x,f) for x in c['conditions']];return all(a) if c['operation']=='AND' else any(a)
 if c['$type']=='questFactsDBCondition':return evaluate(c['type'],f)
 assert c['$type']=='questVarComparison_ConditionType' and c['comparisonType']=='Equal'
 return f.get(c['factName'],0)==c['value']
def run(O):
 assert not O.exists();old=BASE/'verification_01/review.json';checks=[];sources=read(BASE/'readback_01/sources.json')
 def check(name,ok,e):checks.append(dict(name=name,status='PASS' if ok else 'FAIL',evidence=e));assert ok,name
 for p in sources['resources']:
  if not p['label'].endswith('_after'):continue
  check('same actual serialized source '+p['label'],sha(p['binary'])==p['sha256'] and sha(p['json'])==p['json_sha256'],p)
  n=Resource(read(p['json'])).normalize()['graphs']['root']['nodes']['1200'];c=n['payload']['condition'];facts={x['factName']:x['value'] for x in n['reads']};positives={k:v for k,v in facts.items() if v!=0};zeros={k:v for k,v in facts.items() if v==0}
  check('all actual explicit requirements accepted '+p['label'],evaluate(c,facts),facts)
  check('absent zero-valued facts accepted as engine zero '+p['label'],evaluate(c,positives),dict(absent_zero_facts=list(zeros),required_positive_facts=positives))
  for k in zeros:check('individual absent-zero fixture '+p['label']+k,evaluate(c,{x:v for x,v in facts.items() if x!=k}),k)
  for k in positives:check('individual missing required-positive reads zero and rejects '+p['label']+k,not evaluate(c,{x:v for x,v in facts.items() if x!=k}),k)
  for k in ['mq007_done','mq007_skippy_re_acquiring_done','PTFRQR4_MQ007_ReacquisitionIssued']:check('explicit already-done receipt still rejects '+p['label']+k,not evaluate(c,facts|{k:1}),k)
 report=dict(status='CORRECTED_FIXTURE_INTERPRETATION_NO_RESOURCE_CHANGE',supersedes_claim='The earlier serialized verifier and review treated every absent fact as unknown/rejected. That Python policy is not engine FactsDB missing-zero proof.',preserved_original=dict(path=str(old),sha256=sha(old)),checks=len(checks),tests=checks,faithful_model='Equal comparisons use facts.get(name,0). Missing requirements for0 accept; missing required positives naturally reject as zero. This models known FactsDB read behavior and does not deserialize any save.',correction=['Do not count the original per-key missing-input fixtures as engine assertions for zero-valued facts. Keep them only as conservative unknown-input model tests.','The serialized immediate condition and approved future1101 attachment remain unchanged. New shared-claim absence reading0 is expected; native done absence reading0 alone is not historical proof.','Source scope relies on actual future1101 execution and required positive private Issued/Entered/Tower facts, together with unchanged supported admission. Old Entered facts without a new event do not enroll. Already returned/reacquired/claimed1 still rejects.'],runtime_changes=[],game_writes=0,save_writes=0)
 write(O/'FACTSDB_DEFAULT_ZERO_CORRECTION.json',report);return dict(checks=len(checks),status=report['status'])
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);a=ap.parse_args();print(json.dumps(run(Path(a.output).resolve())))
