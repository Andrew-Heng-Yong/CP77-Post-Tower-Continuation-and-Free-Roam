"""Independent source-authority/condition review of Worker C's MQ060 proposal."""
from pathlib import Path
import sys,copy,itertools,collections,json
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
C=W/'prealpha/quest_restoration_qr7/worker_c/nitro_authority_03'
ENTRY=r'towercontinued\sidejobs_s29\entries\mq060_nitro.questphase';NATIVE=r'base\quest\bugfixing\quest_bugfixing.questphase'
def ev(c,owned,facts):
 t=c['$type']
 if t=='questLogicalCondition':
  xs=[ev(x,owned,facts)for x in c['conditions']];return all(xs)if c['operation']=='AND'else any(xs)if c['operation']=='OR'else (_ for _ in[]).throw(ValueError(c))
 if t in ['questFactsDBCondition','questVehicleCondition']:return ev(c['type'],owned,facts)
 if t=='questVehicleAvailable_ConditionType':assert c['vehicleType']=='SpecificVehicle';return c['vehicleName']in owned
 if t=='questVarComparison_ConditionType':
  a=facts[c['factName']];b=c['value'];return {'GreaterOrEqual':a>=b,'Greater':a>b,'Equal':a==b,'Less':a<b,'NotEqual':a!=b}[c['comparisonType']]
 raise ValueError(c)
def reachable(g,a,b):
 todo=[a];seen={a}
 while todo:
  n=todo.pop()
  for x,s,y,t in g['edges']:
   if x==n and s!='CutSource'and t!='CutDestination'and y not in seen:seen.add(y);todo.append(y)
 return b in seen
def run(o):
 assert not o.exists();pins=read(C/'source_pins.json');D={};M={};T=[]
 def ck(n,b,e=None):T.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 for p in pins:
  ck('independently pinned raw '+p['depot'],sha(Path(p['raw']))==p['raw_sha256']);ck('independently pinned typed source '+p['depot'],sha(Path(p['json']))==p['json_sha256']);D[p['depot']]=read(Path(p['json']));M[p['depot']]=Resource(D[p['depot']]).normalize()
 ep=read(W/'prealpha/quest_restoration_qr7/worker_c/startup_01/manifest.json');targets=[r'base\quest\cyberpunk2077.gamedef',r'ep1\quest\ep1_standalone.gamedef',r'base\quest\minor_quests\mq060\mq060.quest']
 for d in targets:ck('current archives have unique exact target provider '+d,len([p for p in ep['resources']if p['depot']==d])==1)
 roots={d:[value(x['questFile']['DepotPath'])for x in walk(D[d])if x.get('$type')=='gsmMainQuest']for d in targets[:2]}
 ck('positive main game definition owns main quest route',roots[targets[0]]==[r'base\quest\cyberpunk2077.quest']);ck('both actual game definitions exclude standalone MQ060',all(targets[2]not in rs for rs in roots.values()))
 info=read(C/'evidence.json')
 for a in info['registered_route']:
  g=M[a['depot']]['graphs'][a['graph']];ck('independent normal-edge ancestry '+a['depot']+':'+a['graph'],reachable(g,a['start'],a['end']));
  if a['next_resource']:ck('ancestry resource binding '+a['depot'],g['nodes'][a['end']]['refs']==[a['next_resource']])
 ng=M[NATIVE]['graphs']['root/3'];nativebike=ng['nodes']['93']['payload']['condition'];nativecount=ng['nodes']['104']['payload']['condition'];ck('native join is genuinely AND106',ng['nodes']['106']['type']=='questLogicalAndNodeDefinition'and all(e in ng['edges']for e in [['93','Out','106','In1'],['104','Out','106','In2'],['106','Out1','89','Start']]))
 proposed=Resource(read(C/'private_proposed_resource.json')).normalize();current=M[ENTRY];g=proposed['graphs']['root'];old=current['graphs']['root'];ck('all saved existing graphs/node IDs/sockets/edges preserved',set(proposed['graphs'])==set(current['graphs'])and all(gp in current['graphs']and x['edges']==current['graphs'][gp]['edges']and x['entries']==current['graphs'][gp]['entries']and set(x['nodes'])==set(current['graphs'][gp]['nodes'])and all(n['sockets']==current['graphs'][gp]['nodes'][i]['sockets']for i,n in x['nodes'].items())for gp,x in proposed['graphs'].items()))
 for gp,gr in proposed['graphs'].items():
  for i,n in gr['nodes'].items():
   if gp=='root'and i in ['65003','65004']:continue
   ck('unaffected actual payload '+gp+'/'+i,n['payload']==current['graphs'][gp]['nodes'][i]['payload'])
 for i in ['65003','65004']:
  pc=g['nodes'][i]['payload']['condition'];oc=old['nodes'][i]['payload']['condition'];ck('only append native gates at existing pre-Issued '+i,pc['operation']=='AND'and pc['conditions'][:-2]==oc['conditions']and pc['conditions'][-2:]==[nativebike,nativecount])
 ck('both amended conditions precede one-time Issued without new edge',all(e in g['edges']for e in [['65003','Out','65004','In'],['65004','True','65005','In']])and g['nodes']['65005']['writes']==old['nodes']['65005']['writes'])
 bikes=[x['vehicleName']for x in walk(nativebike)if x.get('$type')=='questVehicleAvailable_ConditionType'];tyger='Vehicle.v_sportbike1_yaiba_kusanagi_tyger_player';fixtures=[]
 for bits in itertools.product([False,True],repeat=4):
  owned={b for b,v in zip(bikes+[tyger],bits)if v}
  for n in range(5):
   facts={'carbought_counter':n};expected=ev(nativebike,owned,facts)and ev(nativecount,owned,facts)
   # Evaluate exact appended resource conditions and exact old four pause nodes;
   # do not reuse C's hardcoded selector arithmetic as the oracle.
   four=any(ev(old['nodes'][i]['payload']['condition'],owned,facts)for i in ['8','9','10','11']);actual=four and all(ev(c,owned,facts)for c in g['nodes']['65003']['payload']['condition']['conditions'][-2:]);ck('independent actual predicate parity '+str((bits,n)),actual==expected);fixtures.append({'bits':bits,'purchases':n,'native':expected,'proposal':actual,'old':four})
 bad=copy.deepcopy(read(C/'private_proposed_resource.json'));rr=Resource(bad);guard=next(x for x in rr.handles.values()if x.get('id')==65003 and x.get('$type')=='questPauseConditionNodeDefinition');cc=rr.d(guard['condition']);cc['conditions'].pop();bm=Resource(bad).normalize();ck('actual source-document dropped-count mutation detected',len(bm['graphs']['root']['nodes']['65003']['payload']['condition']['conditions'])!=len(g['nodes']['65003']['payload']['condition']['conditions']));write(o/'mutant_drop_native_count.json',bad)
 write(o/'tests.json',T);write(o/'fixtures.json',fixtures);write(o/'review.json',{'status':'APPROVE_SOURCE_AUTHORITY_AND_MINIMAL_FUTURE_GATE_SCOPE_PENDING_COORDINATOR_TYPED_PACKAGE_GATES','reviewed_evidence':str(C/'evidence.json'),'reviewed_evidence_sha256':sha(C/'evidence.json'),'reviewed_proposal_sha256':sha(C/'private_proposed_resource.json'),'checks':len(T),'actual_document_mutations':1,'decision':'Positive current game-definition registration and normal-edge rooted caller ancestry establish the global native AND3-variant/purchases>=3 route as the appropriate main retained-session source. The standalone four-variant donor is authored but lacks current root registration. There is sufficient source evidence for this narrow prospective correction; no invented native-loader absence proof is needed.','preservation':'Appending the exact two native predicates at both existing pre-Issued guards preserves saved identifiers, edges, receipts, body reference, already-issued descendants and rewards. Already-issued owners are explicitly outside this prospective gate correction.','limits':['No game launched or save examined; actual gameplay reachability and delayed predicate notifications remain live-only.','This adjudication does not authorize tightening already-issued saved owners.','Coordinator must serialize/readback proposed current full resource, compare unaffected payloads, run relevant preservation controls and validate final package before integration.'],'source_authority_conflict':'Resolved for fresh initial main-root entry by positive startup owner evidence; standalone file preserved as historical alternate/test authoring.','runtime_writes':0});print({'checks':len(T),'review':str(o/'review.json')})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
