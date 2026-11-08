"""Independent serialized NID02 monitor oracle; no coordinator verifier imports."""
from pathlib import Path
import sys,copy,json,collections
W=Path(__file__).resolve().parents[5];H=Path(__file__).resolve().parent;O=H/'verification_01'
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource
GUARD={'PTFRU9_sts_wat_nid_02_ParentEntered':1,'PTFRU9_sts_wat_nid_02_Started':0,'PTFRU9_sts_wat_nid_02_MainFinished':0,'PTFRU9_sts_wat_nid_02_OwnerFinished':0,'PTFRU9_sts_wat_nid_02_Fault':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'nid_02_start':0,'nid_02_finished':0,'sts_wat_nid_02_fail':0,'PTFRU9_sts_wat_nid_02_FailureMonitorEntered':0}
REM=['65003','Out','2','In1'];ADD=[['65003','Out','1300','In'],['1300','True','1301','In'],['1301','Out','1302','In1'],['1301','Out','2','In1'],['1300','False','2','In1']]
def facteval(c,f):
 if c['$type']=='questLogicalCondition':
  rs=[facteval(x,f)for x in c['conditions']];return all(rs)if c['operation']=='AND'else any(rs)if c['operation']=='OR'else False
 if c['$type']=='questFactsDBCondition':return facteval(c['type'],f)
 if c['$type']=='questVarComparison_ConditionType':
  a,b=f.get(c['factName'],0),c['value'];return {'Equal':a==b,'NotEqual':a!=b,'Greater':a>b,'GreaterOrEqual':a>=b,'Less':a<b,'LessOrEqual':a<=b}[c['comparisonType']]
 raise AssertionError(c['$type'])
def rawgraph(r,gp):
 g=r.d(r.root['graph'])
 for i in gp.split('/')[1:]:g=r.d(next(r.d(h)for h in g['nodes']if str(r.d(h)['id'])==i)['phaseGraph'])
 return g
def drop_raw_edge(doc,gp,target):
 r=Resource(doc);g=rawgraph(r,gp);socks={};all_sockets=[]
 for h in g['nodes']:
  n=r.d(h)
  for sh in n.get('sockets',[]):s=r.d(sh);socks[r.hid(sh)]=(str(n['id']),str(value(s['name'])));all_sockets.append(s)
 keys=set()
 for s in all_sockets:
  for ch in s.get('connections',[]):
   co=r.d(ch);a=socks.get(r.hid(co['source']));b=socks.get(r.hid(co['destination']))
   if a and b and [*a,*b]==target:keys.add(r.hid(ch))
 assert keys,target
 for s in all_sockets:s['connections']=[ch for ch in s.get('connections',[])if r.hid(ch)not in keys]

def run():
 assert not(O/'review.json').exists();ts=[];pins=[];doc={};model={}
 def ck(k,v,e):ts.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e});assert v,k
 rows=read(O/'raw_02/manifest.json')
 for row in rows:
  ck('fresh_actual_raw_export '+row['key'],sha(row['raw'])==row['raw_sha256']and sha(row['json'])==row['json_sha256'],row);doc[row['key']]=read(row['json']);model[row['key']]=Resource(doc[row['key']]).normalize();ck('fresh_decode_integrity '+row['key'],not model[row['key']]['errors'],model[row['key']]['errors']);pins.append(row)
 B,A,N=(model[k]for k in ['before','after','native']);BG=B['graphs']['root'];AG=A['graphs']['root'];NG=N['graphs']['root/23'];CG=A['graphs']['root/1302']
 prop=W/'prealpha/quest_restoration_qr5/groups/G11/nid02_failure/proposal_01/proposal.json';ck('exact_approved_source_proposal',sha(prop)=='FEA112924B05C2116620F3952843649693B8F6B8646692443DADAF6787D6B214',str(prop));ck('proposal_guard_independently_matched',read(prop)['initial_guard_facts']==GUARD,GUARD)
 # Native-source oracle: inspect the raw serialized graph independently of implementation plans.
 def oracle(m):
  errors=[];gs=m['graphs'];gr=gs['root'];ns=gr['nodes']
  if m['errors']:errors.append('decode')
  if set(ns)!=set(BG['nodes'])|{'1300','1301','1302'}:errors.append('parent_ids')
  for i,n in BG['nodes'].items():
   if ns.get(i)!=n:errors.append('old_parent_node_'+i)
  expected=collections.Counter(map(tuple,BG['edges']));expected.subtract([tuple(REM)]);expected.update(map(tuple,ADD));expected=+expected
  if collections.Counter(map(tuple,gr['edges']))!=expected:errors.append('parent_edges')
  for gp,g in B['graphs'].items():
   if gp!='root'and gs.get(gp)!=g:errors.append('old_descendant_'+gp)
  if m['metadata']!=B['metadata']or m['embedded_files']!=B['embedded_files']:errors.append('root_metadata')
  guard=ns.get('1300',{});readers=guard.get('reads',[])
  if guard.get('type')!='questConditionNodeDefinition'or guard.get('payload',{}).get('condition',{}).get('operation')!='AND'or len(readers)!=11 or {r.get('factName'):r.get('value')for r in readers}!=GUARD or any(r.get('comparisonType')!='Equal'for r in readers):errors.append('exact_immediate_guard11')
  claim=ns.get('1301',{}).get('writes',[])
  if claim!=[{'$type':'questSetVar_NodeType','factName':'PTFRU9_sts_wat_nid_02_FailureMonitorEntered','setExactValue':1,'value':1}]:errors.append('private_claim_only')
  outer=copy.deepcopy(ns.get('1302',{}).get('payload',{}));outer['id']=23
  if outer!=N['graphs']['root']['nodes']['23']['payload']:errors.append('complete_native_phase_metadata')
  cg=gs.get('root/1302')
  if not cg:errors.append('native_monitor_missing');return errors
  if set(cg['nodes'])!=set(NG['nodes']):errors.append('native_node_ids')
  for i,n in NG['nodes'].items():
   if cg['nodes'].get(i)!=n:errors.append('native_payload_sockets_'+i)
  expected=collections.Counter(map(tuple,NG['edges']));expected.subtract([('0','Out','12','In')]);expected.update([('0','Out','33','In')]);expected=+expected
  if collections.Counter(map(tuple,cg['edges']))!=expected:errors.append('native_edges')
  if set(gs)!=set(B['graphs'])|{'root/1302'}:errors.append('graph_inventory')
  if any(str(i)in cg['reachable']for i in [12,13]):errors.append('native_arm_reachable')
  return errors
 ck('actual_defective_before_fails_native_monitor_oracle',bool(oracle(B)),oracle(B));ck('actual_serialized_after_satisfies_native_monitor_oracle',not oracle(A),oracle(A))
 ck('exact_parent_delta_only',set(AG['nodes'])-set(BG['nodes'])=={'1300','1301','1302'},ADD)
 for i in sorted(NG['nodes'],key=int):ck('entire_native_node_exact '+i,CG['nodes'][i]==NG['nodes'][i],{'native_graph':'root/23','current_graph':'root/1302','node':i,'payload_sha256':NG['nodes'][i]['payload_sha256']})
 ck('actual_XOR_AND_classes',{i:CG['nodes'][i]['type']for i in ['41','9','48']}=={'41':'questLogicalXorNodeDefinition','9':'questLogicalAndNodeDefinition','48':'questLogicalXorNodeDefinition'},'health/water XOR41; link/sceneAND9; call/SMSXOR48')
 ck('native_arm_IDs_retained_dead',{'12','13'}.issubset(CG['nodes'])and not({'12','13'}&set(CG['reachable']))and CG['nodes']['13']['writes'][0]['factName']=='CYB-651268','Native prefix12/13 preserved byte-semantic identities, bypassed only input edge; no CYB reset')
 ck('zero_new_root_or_recursive_prefab_lease',not A['root_prefabs']and not AG['nodes']['1302']['prefabs']and all(not n['prefabs']for n in CG['nodes'].values()),{'root_prefabs':A['root_prefabs'],'phase1302':AG['nodes']['1302']['payload']})
 ck('no_new_parent_terminator',not any(n['type']=='questOutputNodeDefinition'and n['payload'].get('type')=='Terminating'for n in AG['nodes'].values()),'native output1 terminates isolated helper only; unchanged parent/body lifetime')
 # Evaluate actual immediate native condition and traverse only newly inserted adapters.
 def dispatch(f):
  f=f.copy();q=collections.deque(['1300']);arrived=[];guard=AG['nodes']['1300']['payload']['condition'];seen=0
  while q:
   ni=q.popleft();seen+=1;assert seen<12
   if ni in ['2','1302']:arrived.append(ni);continue
   if ni=='1300':socket='True'if facteval(guard,f)else'False'
   else:
    for wr in AG['nodes'][ni]['writes']:f[wr['factName']]=wr['value']if wr['setExactValue']else f.get(wr['factName'],0)+wr['value']
    socket='Out'
   q.extend(y for x,s,y,t in AG['edges']if x==ni and s==socket)
  return arrived,f
 for cyb in [0,1]:
  arr,f=dispatch(GUARD|{'CYB-651268':cyb});ck('positive_fresh_CYB'+str(cyb)+'_main_and_helper_once',collections.Counter(arr)=={'2':1,'1302':1}and f['CYB-651268']==cyb and f['PTFRU9_sts_wat_nid_02_FailureMonitorEntered']==1,arr)
 for fact,v in GUARD.items():
  fixture=GUARD|{fact:0 if v else 1};arr,_=dispatch(fixture);ck('refusal_preserves_original_main_once '+fact,arr==['2'],fixture)
 # Representative mutations operate on actual freshly exported after JSON, never production.
 muts=[]
 for name,gp,edge in [('missing_native_health_connection','root/1302',['2','Out','41','In1']),('missing_native_water_connection','root/1302',['49','Out','41','In2']),('missing_refusal_main_connection','root',['1300','False','2','In1']),('missing_native_failure_cleanup_connection','root/1302',['41','Out1','34','In'])]:
  d=copy.deepcopy(doc['after']);drop_raw_edge(d,gp,edge);mm=Resource(d).normalize();problems=oracle(mm);ck('raw_mutation '+name,bool(problems),problems);muts.append({'name':name,'errors':problems,'raw_edge':edge})
 for name,ni,newclass in [('wrong_failure_join',41,'questLogicalAndNodeDefinition'),('wrong_cleanup_join',9,'questLogicalXorNodeDefinition')]:
  d=copy.deepcopy(doc['after']);r=Resource(d);g=rawgraph(r,'root/1302');n=next(r.d(h)for h in g['nodes']if r.d(h)['id']==ni);n['$type']=newclass;problems=oracle(Resource(d).normalize());ck('raw_mutation '+name,bool(problems),problems);muts.append({'name':name,'errors':problems})
 d=copy.deepcopy(doc['after']);r=Resource(d);g=rawgraph(r,'root');n=next(r.d(h)for h in g['nodes']if r.d(h)['id']==1300);conditions=n['condition']['Data']['conditions']if 'Data'in n['condition']else n['condition']['conditions'];conditions.pop();problems=oracle(Resource(d).normalize());ck('raw_mutation_missing_guard_predicate',bool(problems),problems);muts.append({'name':'missing_guard_predicate','errors':problems})
 write(O/'tests.json',ts);write(O/'source_pins.json',pins);write(O/'mutations.json',muts)
 report={'status':'PASS_INDEPENDENT_SERIALIZED_REPAIR_WITH_LIMITS','quest_id':'sts_wat_nid_02','before_sha256':rows[0]['raw_sha256'],'after_sha256':next(r['raw_sha256']for r in rows if r['key']=='after'),'source_proposal':str(prop),'source_proposal_sha256':sha(prop),'checks':len(ts),'raw_mutations':len(muts),'fresh_raw_exports':3,'tests':str(O/'tests.json'),'tests_sha256':sha(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'source_pins_sha256':sha(O/'source_pins.json'),'findings':['Actual serialized candidate02 directly re-exported independently from pinned raw; complete old parent/descendant graphs preserved except approved interposition.','Actual11-predicate immediate guard, once-only private claim, True main+helper dispatch once and False main dispatch once verified from actual graph. CYB0 and legitimate prearmedCYB1 both accepted unchanged.','Full exact native23 cloned as1302; all original node payloads/sockets/IDs/actions and edges preserved except input0→12 replaced0→33. Native12/13 retained unreachable, no CYB writer/reset newly executes.','Health2/water49→XOR41, link AND9, call-or-SMSXOR48 and every native failure/journal/phone/link/token/achievement/cleanup node exact. No added root/recursive PIP lease or parent terminator.'],'limits':['Static source/readback/synthetic branch fixture checks are not an engine scheduling or saved-owner/gameplay guarantee. Existing entered/progressed owners are not adopted.','Final package reconstruction/readback and preservation of unrelated staged repairs remain coordinator gates. This does not certify installed PH3 or deployment.','First export attempt used coordinator supplied nonexistent archive_inputs paths and stopped before reading; corrected archive_source with identical pinned hashes exported to fresh raw_02, preserving first empty attempt.'],'runtime_changes':[]}
 write(O/'review.json',report);print(json.dumps({'checks':len(ts),'mutations':len(muts),'review_sha256':sha(O/'review.json')},ensure_ascii=True))
if __name__=='__main__':run()
