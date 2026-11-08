"""Independent serialized Cheetah prefix/lease/lifecycle verification, no root checker imports."""
from pathlib import Path
import sys,json,copy,collections,argparse
H=Path(__file__).resolve().parent;W=H.parents[4];F=W/'prealpha/quest_restoration_qr5';sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,walk,value
from model import Resource,reachable

def run(O):
 assert not O.exists();tests=[];pins=[];M={};R={};mut=[]
 def ck(k,v,e):
  tests.append({'name':k,'status':'PASS'if v else'FAIL','evidence':e})
  if not v:write(O/'failed_tests.json',tests);raise AssertionError(k)
 for p in read(H/'readback_01/manifest.json'):
  ck('independent fresh binary+JSON '+p['name'],sha(p['binary'])==p['sha256']and sha(p['json'])==p['json_sha256'],p);pins.append(p);R[p['name']]=read(p['json']);M[p['name']]=Resource(R[p['name']]).normalize();ck('decode '+p['name'],not M[p['name']]['errors'],M[p['name']]['errors'])
 b,a,nat=M['before'],M['after'],M['native'];np='root/3';ap='root/1202'
 def nd(m,k,g='root'):return m['graphs'][g]['nodes'][str(k)]
 def ed(m,x,s,y,t,g='root'):return [str(x),s,str(y),t]in m['graphs'][g]['edges']
 source=F/'reviews/worker_a/CHEETAH/verification_03/review.json';proposal=F/'groups/G12/cheetah_proposal_02/proposal.json'
 for p,h in [(source,'EE79127D3C79EE3F54AC45F0DA126805E890DC3DC5175DC46E71D0603659376E'),(proposal,'32086A3AB3812DE1FF6C4E5BE95DBD6872A79B6741A99827CDB2B582A09DB3A3')]:ck('approved source/proposal pin '+p.parent.name,sha(p)==h,str(p));pins.append({'path':str(p),'sha256':sha(p)})
 # Independently specified approved delta, not a comparison against root's checker assertions.
 removed=[['65003','Out','2','In1']];added=[['65003','Out','1200','In'],['1200','True','1201','In'],['1200','False','2','In1'],['1201','Out','1202','In1'],['1201','Out','2','In1']]
 ck('only clone graph hierarchy added',set(a['graphs'])-set(b['graphs'])=={ap,ap+'/10'}and not set(b['graphs'])-set(a['graphs']),list(a['graphs']))
 ck('resource root metadata and prefabs exact',all(a[k]==b[k]for k in ['metadata','root_prefabs','embedded_files']),b['metadata_sha256'])
 for gp,g in b['graphs'].items():
  ag=a['graphs'][gp];ck('old graph IDs retained '+gp,set(g['nodes'])<=set(ag['nodes']),len(g['nodes']))
  for i,x in g['nodes'].items():ck('old node payload/socket exact '+gp+'/'+i,x==ag['nodes'][i],x['payload_sha256'])
  if gp=='root':
   bc=collections.Counter(map(tuple,g['edges']));ac=collections.Counter(map(tuple,ag['edges']));rm=[list(e)for e,c in(bc-ac).items()for _ in range(c)];ad=[list(e)for e,c in(ac-bc).items()for _ in range(c)];ck('only one old edge removed',rm==removed,rm);ck('exact five ordered fork edges',sorted(ad)==sorted(added),ad);ck('three unused local IDs added',set(ag['nodes'])-set(g['nodes'])=={'1200','1201','1202'},'1200 immediate guard,1201 private claim,1202 native scoped clone')
  else:ck('old descendant edges exact '+gp,g['edges']==ag['edges'],len(g['edges']))
 # Exact native3 wrapper metadata/lease except its local id. Empty resource PF is not adequate.
 expected=copy.deepcopy(nd(nat,3));expected['id']='1202';expected['payload']['id']=1202;expected.pop('payload_sha256');actual=copy.deepcopy(nd(a,1202));actual.pop('payload_sha256');ck('clone wrapper complete native phase3 metadata/sockets',actual==expected,nd(a,1202))
 ck('exact streetstory PIP retained',nd(a,1202)['prefabs']==['#sts_wat_nid_03_streetstory']and nat['root_prefabs']==[],'parent empty native root list does not remove node3 lease')
 for src,dst in [(np,ap),(np+'/10',ap+'/10')]:
  sg=nat['graphs'][src];ag=a['graphs'][dst];ck('clone exact native identity set '+dst,set(sg['nodes'])==set(ag['nodes']),len(sg['nodes']))
  for i,x in sg['nodes'].items():ck('clone native exact payload/socket '+dst+'/'+i,x==ag['nodes'][i],x['payload_sha256'])
  if src==np:
   ee=[e for e in sg['edges']if e!=['0','Out','8','In']]+[['0','Out','12','In'],['0','Out','13','In']];ck('only native prefix bypass',ag['edges']==sorted(ee),'old8/9 remain exact orphaned IDs; all other native edge multiplicities retained')
  else:ck('recursive helper10 all edges exact',ag['edges']==sg['edges'],len(sg['edges']))
 ck('XOR17 actual type, later AND24 exact',nd(a,17,ap)['type']=='questLogicalXorNodeDefinition'and nd(a,24,ap)['type']=='questLogicalAndNodeDefinition','no imposition of both future prerequisites')
 ck('native independent future waits',nd(a,12,ap)['type']=='questPauseConditionNodeDefinition'and nd(a,12,ap)['reads'][0]['state']=='Active'and nd(a,13,ap)['reads'][0]['factName']=='sts_wat_nid_03_bugfixing','input activates both original pauses then native XOR')
 ck('old CYB arm unreachable without reset',not {'8','9'}&set(a['graphs'][ap]['reachable'])and nd(a,9,ap)['writes']==nd(nat,9,np)['writes'],'native CYB writer remains exact saved identity, not executed by new input')
 ck('native end18 exact increment and routes',nd(a,18,ap)['writes']==[{'$type':'questSetVar_NodeType','factName':'sts_wat_nid_03_bugfixing_end','setExactValue':0,'value':1}]and ed(a,10,'Out1',18,'In',ap)and ed(a,10,'Out3',18,'In',ap),'no fake completion or end acknowledgement')
 ck('original completed Out2 exclusion retained',not any(e[0]=='10'and e[1]=='Out2'for e in a['graphs'][ap]['edges']),'preserve native no-end route; not universal fallback completion claim')
 ck('native output recursion/lifetime retained',nd(a,1,ap)['payload']['type']=='Terminating'and nd(a,69,ap+'/10')['payload']['type']=='NonTerminating'and not any(v['type']=='questOutputNodeDefinition'for v in a['graphs']['root']['nodes'].values()),'only cloned phase owns its termination; main sibling remains independent')
 # Guard exactly13 authored predicates with positive event provenance. Ordinary absent scalar=0.
 expectedfacts={
  'PTFRU9_sts_wat_nid_03_ParentEntered':1,'PTFRU9_sts_wat_nid_03_Started':0,'PTFRU9_sts_wat_nid_03_MainFinished':0,'PTFRU9_sts_wat_nid_03_OwnerFinished':0,'PTFRU9_sts_wat_nid_03_Fault':0,'PTFRU9_Support_Issued':1,'PTFRU9_Support_Fault':0,'PTFRU9_sts_wat_nid_03_MonitorEntered':0,'nid_03_start':0,'nid_03_finished':0,'sts_wat_nid_03_bugfixing':0,'sts_wat_nid_03_bugfixing_end':0,'sts_wat_nid_03_completed':0}
 guard=nd(a,1200);gg=guard['payload']['condition'];facts={x['factName']:x['value']for x in guard['reads']};ck('immediate13-clause exact AND guard',guard['type']=='questConditionNodeDefinition'and gg['operation']=='AND'and len(guard['reads'])==13 and all(x['comparisonType']=='Equal'for x in guard['reads'])and facts==expectedfacts,facts)
 ck('only private receipt claim',nd(a,1201)['writes']==[{'$type':'questSetVar_NodeType','factName':'PTFRU9_sts_wat_nid_03_MonitorEntered','setExactValue':1,'value':1}],nd(a,1201)['payload'])
 ck('existing prestate pulse remains exact',ed(a,65003,'Out',64000,'In1')and nd(a,64000)==nd(b,64000),'does not replace native prestate/claim timing')
 def ev(c,f):
  if c['$type']=='questLogicalCondition':return all(ev(x,f)for x in c['conditions'])if c['operation']=='AND'else any(ev(x,f)for x in c['conditions'])
  if c['$type']=='questFactsDBCondition':return ev(c['type'],f)
  if c['$type']=='questVarComparison_ConditionType':return f.get(c['factName'],0)==c['value']
  raise ValueError(c['$type'])
 good={k:v for k,v in expectedfacts.items()if v};ck('missing expected-zero scalars accepted',ev(gg,good)and not ev(gg,{}),'positive ParentEntered/SupportIssued required; existing genuineTower65002 gate unchanged')
 for k,v in expectedfacts.items():ck('refuse altered provenance/history '+k,not ev(gg,good|{k:0 if v else 1}),'False still reaches original main2 once')
 for cyb in [0,1]:ck('CYB history neither blocks nor resets '+str(cyb),ev(gg,good|{'CYB-626818':cyb}),'does not infer no history from missing scalar')
 beforeguard=nd(b,65002)['payload']['condition'];positive={x['factName']:x['value']for x in nd(b,65002)['reads']};ck('alreadyEntered save cannot generate enrollment event',not ev(beforeguard,positive|{'PTFRU9_sts_wat_nid_03_ParentEntered':1}),'future65003 pulse only, no retroactive poll')
 ck('future static route bound to guard before native2',all(e in a['graphs']['root']['edges']for e in added)and not ed(a,65003,'Out',2,'In1'),'native2 can never precede1200 on repaired65003 route; refusal preserves main')
 # Actor carrier is a separate already-reviewed resource and remains byte-identical.
 actor=F/'candidate_02/archive_source/towercontinued/native_gigs_u9/sts_ep1_08_entry.questphase';ck('prior Steven repair resource preserved',sha(actor)=='5D1FE58F41739C231B5006FF134EB78207FC879B9AB8652FADE69899242C2F62',str(actor));pins.append({'path':str(actor),'sha256':sha(actor)})
 # Mutate actual freshly decoded resources, resolving graph/socket/condition handles.
 def gn(r,path):
  z=Resource(r);g=z.d(z.root['graph'])
  for i in path.split('/')[1:]:g=z.d(next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==i)['phaseGraph'])
  return z,g
 def rn(r,path,i):
  z,g=gn(r,path);return z,next(z.d(h)for h in g['nodes']if str(z.d(h)['id'])==str(i))
 def rm(r,path,ee):
  z,g=gn(r,path);ss={z.hid(sh):(str(z.d(h)['id']),str(value(z.d(sh)['name'])))for h in g['nodes']for sh in z.d(h)['sockets']};bad=set()
  for h in g['nodes']:
   for sh in z.d(h)['sockets']:
    for ch in z.d(sh).get('connections',[]):
     co=z.d(ch)
     if [*ss.get(z.hid(co['source']),('','')),*ss.get(z.hid(co['destination']),('',''))]==ee:bad.add(z.hid(ch))
  for h in g['nodes']:
   for sh in z.d(h)['sockets']:z.d(sh)['connections']=[x for x in z.d(sh).get('connections',[])if z.hid(x)not in bad]
 def alterfact(r,path,i,f,changes):
  for x in walk(rn(r,path,i)[1]):
   if x.get('factName')==f:x.update(changes)
 for label,change,oracle in [
  ('drop_refusal_main',lambda r:rm(r,'root',['1200','False','2','In1']),lambda m:ed(m,1200,'False',2,'In1')),
  ('strip_native_PIP',lambda r:rn(r,'root',1202)[1].update(phaseInstancePrefabs=[]),lambda m:nd(m,1202)['prefabs']==['#sts_wat_nid_03_streetstory']),
  ('replace_XOR_by_AND',lambda r:rn(r,ap,17)[1].update({'$type':'questLogicalAndNodeDefinition'}),lambda m:nd(m,17,ap)['type']=='questLogicalXorNodeDefinition'),
  ('changed_end_producer',lambda r:alterfact(r,ap,18,'sts_wat_nid_03_bugfixing_end',{'factName':'QR5_wrong_end'}),lambda m:any(x.get('factName')=='sts_wat_nid_03_bugfixing_end'for x in nd(m,18,ap)['writes'])),
  ('allow_already_started',lambda r:alterfact(r,'root',1200,'PTFRU9_sts_wat_nid_03_Started',{'value':1}),lambda m:any(x.get('factName')=='PTFRU9_sts_wat_nid_03_Started'and x['value']==0 for x in nd(m,1200)['reads'])),
  ('break_future_request_wait',lambda r:alterfact(r,ap,13,'sts_wat_nid_03_bugfixing',{'factName':'QR5_wrong_request'}),lambda m:nd(m,13,ap)['reads'][0]['factName']=='sts_wat_nid_03_bugfixing')]:
  r=copy.deepcopy(R['after']);change(r);mm=Resource(r).normalize();ck('actual raw fault '+label,oracle(a)and not oracle(mm),label);fp=O/'mutations'/str(label+'.json');write(fp,r);mut.append({'fault':label,'path':str(fp),'sha256':sha(fp),'detected':True})
 write(O/'tests.json',tests);write(O/'source_pins.json',pins);write(O/'mutations.json',mut)
 result={'status':'APPROVE_EXACT_SERIALIZED_BOUNDED_FUTURE_CHEETAH_MONITOR','checks':len(tests),'mutations':len(mut),'failures':0,'fresh_exports':3,'before_sha256':pins[0]['sha256'],'after_sha256':pins[1]['sha256'],'tests':str(O/'tests.json'),'source_pins':str(O/'source_pins.json'),'code':str(Path(__file__).resolve()),'code_sha256':sha(__file__),'scope':'Only approved prefix adaptation of native3, exact PIP/recursive10/actions/outputs/XOR17/AND24; root immediate13-clause guard/private claim/refusal original main2.','limits':['Future positive65003 enrollment only; old already-entered/started/progressed saved owners are not adopted.','Original completed helperOut2 noend edge remains; normal273 completion route remains; no universal fallback/gameplay success claim.','Native world/PIP relative actor binding/streaming/engine lease and reload behavior remain opaque/live-only.','Final package and aggregate source preservation remain root gates; no installation/save/fact/game action.'],'runtime_changes':[]};write(O/'review.json',result);print(json.dumps(result))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);run(Path(ap.parse_args().output).resolve())
