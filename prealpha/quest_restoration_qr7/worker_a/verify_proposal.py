"""Reproducible controls on pinned native sources and private actual CR2W readback.

This verifies structure and the explicitly conditional proposal, not gameplay.
"""
from pathlib import Path
import sys,json,struct,copy,hashlib
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'));sys.path.insert(0,str(H))
from common import read,write,sha,walk,value,fnv
from model import Resource
import propose_listener as P
def edges(m,gp='root'):return set(map(tuple,m['graphs'][gp]['edges']))
def validate(doc,base,native):
 m=Resource(doc).normalize();out=[]
 def ck(name,b,e=None):out.append({'name':name,'pass':bool(b),'evidence':e})
 ck('actual CR2W graph handles/nodes/sockets resolve',not m['errors'],m['errors'])
 g=m['graphs']['root'];bg=base['graphs']['root'];ng=native['graphs']['root/9'];ns=g['nodes'];es=edges(m)
 ck('existing root node identities retained',set(bg['nodes'])<=set(ns));ck('only reviewed new local identities',set(ns)-set(bg['nodes'])==set(map(str,range(65007,65014))))
 for i,n in bg['nodes'].items():
  if i=='65002':continue
  ck('original payload preserved node'+i,ns.get(i,{}).get('payload')==n['payload']);ck('original sockets preserved node'+i,ns.get(i,{}).get('sockets')==n['sockets'])
 ck('original child2 graph unchanged',m['graphs'].get('root/2')==base['graphs']['root/2'])
 if '65002'in ns:
  c=ns['65002']['payload']['condition'];old=bg['nodes']['65002']['payload']['condition'];ck('entire original admission retained as exact AND term',c.get('operation')=='AND'and c.get('conditions',[None])[0]==old)
  gate=c.get('conditions',[None,None])[1];expected=P.logic('OR',[P.atom('ep1_installed',1,'Less'),P.logic('AND',[P.atom(f)for f in P.FACTS]+[P.atom(P.ISSUED)])]);ck('future-only request/outcome history fence exact',gate==expected)
 preserve=edges(base)-{('65003','Out','2','In1')};ck('every other original root connection retained',preserve<=es)
 intended={('65003','Out','65007','In'),('65007','False','2','In1'),('65007','True','65008','In'),('65008','Out','65009','In'),('65009','Out','65010','In1'),('65009','Out','2','In1'),('65006','Out','65011','In'),('65011','Out','65012','In'),('65012','CutSource','65010','CutDestination'),('65012','Out','65013','In')}
 ck('exact future-only wiring and cleanup, no extra root edges',es==preserve|intended)
 ck('EP1 branch predicate unchanged native205',ns.get('65007',{}).get('reads')==[{'$type':'questVarComparison_ConditionType','comparisonType':'Greater','factName':'ep1_installed','value':0}])
 ck('native marker readiness is actual condition, not a receipt',ns.get('65009',{}).get('payload',{}).get('condition')=={'$type':'questNodeLoadingCondition','objectRef':{'$type':'NodeRef','$storage':'string','$value':P.MARKER},'inverted':0})
 cg=m['graphs'].get('root/65010',{});cn=cg.get('nodes',{});ck('exact16-node specialized native subtree retained',set(cn)==set(ng['nodes']))
 for i,n in ng['nodes'].items():
  expected=copy.deepcopy(n['payload'])
  if i=='13':expected['sceneLocation']['nodeRef']['$value']=P.MARKER
  ck('native custom payload and socket parity node'+i,cn.get(i,{}).get('payload')==expected and cn.get(i,{}).get('sockets')==n['sockets'])
 ck('all native request/listener/callback/interrupt connections retained',set(map(tuple,cg.get('edges',[])))==set(map(tuple,ng['edges'])))
 for req,node,callback,writer in [('prebrief','17','prebrief_out','6'),('debrief_failed','16','debrief_failed_end_out','11'),('debrief_perfect','18','debrief_perfect_end_out','10')]:
  ck('request route and real outcome '+req,('13',callback,writer,'In')in set(map(tuple,cg.get('edges',[]))) and any(x.get('factName')=='new_sts_pac_cvi_02_holocall_'+req for x in cn.get(node,{}).get('reads',[])))
 ck('no new or rehosted physical/PIP owner',not m['root_prefabs']and all(not n['prefabs']for gr in m['graphs'].values()for n in gr['nodes'].values()))
 newwrites=[x for i,n in ns.items()if i not in bg['nodes']for x in n['writes']];ck('only private once receipts written outside exact native callbacks',{x['factName']for x in newwrites}=={P.ISSUED,P.RETIRED}and all(x['value']==1 and x['setExactValue']==1 for x in newwrites))
 ck('cleanup waits actual Phone EndCall',any(x.get('$type')=='questPhone_ConditionType'and x.get('callPhase')=='EndCall'for x in walk(ns.get('65011',{}).get('payload',{}))))
 return out
def mutate_connection(doc,source_node,socket_name):
 r=Resource(doc);phase=next(x for x in r.handles.values()if x.get('$type')=='questPhaseNodeDefinition'and x.get('id')==65010);g=r.d(phase['phaseGraph']);n=next(r.d(x)for x in g['nodes']if r.d(x)['id']==source_node);s=next(r.d(x)for x in n['sockets']if value(r.d(x)['name'])==socket_name);assert s['connections'];co=r.d(s['connections'][0]);co['destination']={'HandleRefId':r.hid(next(x for x in n['sockets']if value(r.d(x)['name'])=='Holocall RET'))}
def run(o):
 assert not o.exists();D,pins=P.sources();base=Resource(D[P.ENTRY]).normalize();native=Resource(D[P.ACT]).normalize();rb=H/'proposal_readback_03/proposed_entry.NONPRODUCTION.questphase.json';doc=read(rb);T=[]
 def ck(name,b,e=None):T.append({'name':name,'pass':bool(b),'evidence':e});assert b,name
 for pin in pins:
  ck('source raw hash '+pin['depot'],sha(Path(pin['raw']))==pin['raw_sha256']);ck('source JSON hash '+pin['depot'],sha(Path(pin['json']))==pin['json_sha256'])
 for d in [P.ENTRY,r'towercontinued\fixer_offices_fo1\mr_hands.questphase']:
  p=next(x for x in pins if x['depot']==d);cp=W/'prealpha/quest_restoration_qr5/candidate_03/archive_source'/d;ck('exact QR5:08 current payload '+d,sha(cp)==p['raw_sha256'])
 for t in validate(doc,base,native):ck(t['name'],t['pass'],t['evidence'])
 before=validate(D[P.ENTRY],base,native);ck('defective actual baseline fails missing subtree/wiring controls',not all(t['pass']for t in before),[t['name']for t in before if not t['pass']]);write(o/'before_failures.json',[t for t in before if not t['pass']])
 marker=read(H/'current_marker_01/evidence.json');pin=marker['source_pins'][0];buf=H/'raw_buffers_01/current.buffer';raw=buf.read_bytes();span=raw[4670*144:4671*144];layout=W/'research/framework_pr63_01/archivexl/src/Red/StreamingSector.hpp';ndhash=W/'research/framework_pr63_01/codeware/vendor/RED4ext.SDK/include/RED4ext/NodeRef.hpp';target=marker['current'];node=target['node']['Data']
 ck('current raw buffer exact pin',sha(buf)=='C1095531705C2215215FCE62710F9AD431E509B420572E62F4FD5698F72BF29C');ck('144-byte raw span maps to node2577',len(raw)==7961*144 and (struct.unpack_from('<Q',span,0x70)[0]&0x7ffff)==2577)
 ck('raw node ref matches independent SDK skip-hash grammar',struct.unpack_from('<Q',span,0x58)[0]==int(fnv(P.MARKER.replace('#',''))));ck('raw current transform matches expected native marker',struct.unpack_from('<3f',span,0) == (-1584.0894775390625,-2340.8798828125,57.86000061035156))
 ck('ordinary WK index failure preserved',target['placement']['NodeIndex']==13935 and target['placement']['NodeIndex']>=4146);ck('raw native distances finite/source confirmed',struct.unpack_from('<ff',span,0x78)==(1745.7010498046875,512.0));ck('marker definition and stable placement unchanged current provider',marker['typed_target_equal']and marker['stable_placement_fields_equal']);ck('typed marker has no external resource or actor/workspot binding',marker['external_marker_refs']==[]and node['$type']=='worldStaticMarkerNode'and node['data']['Data']['workspotMarkers']==[])
 desc=next(x['descriptor']for x in marker['related_descriptors']if x['descriptor']['category']=='AlwaysLoaded');ck('exact marker sector descriptor independent of quest PIP',value(desc['questPrefabNodeRef'])=='0'and desc['numNodeRanges']==1 and desc['variants']==[] and marker['sector_variant_nodes']==[]and marker['sector_variant_indices']==[0])
 ep=Resource(D[P.EP]).normalize();eg=ep['graphs']['root/10'];ck('retirement cut includes actual EP1 openworld node5',('9','CutSource','5','CutDestination')in edges(ep,'root/10')and eg['nodes']['5']['refs']==[r'ep1\openworld\ep1_open_world.questphase']);ck('ep1 killed receipt follows actual native cut',('8','Out','9','In')in edges(ep,'root/10')and ('9','Out','10','In')in edges(ep,'root/10')and eg['nodes']['10']['writes'][0]['factName']=='q307_ep1_killed')
 muts=[]
 for name,fn in [('missing_actual_prebrief_callback',lambda x:mutate_connection(x,13,'prebrief_out')),('changed_marker_readiness',lambda x:[z.update({'$value':'#missing_marker'})for z in walk(x)if z.get('$type')=='NodeRef'and value(z)==P.MARKER]),('fake_native_ack_outside_callbacks',lambda x:[z.update({'factName':'new_q110_prebrief_rejected_or_end'})for z in walk(x)if z.get('$type')=='questSetVar_NodeType'and z.get('factName')==P.ISSUED])]:
  md=copy.deepcopy(doc);fn(md);failed=[x['name']for x in validate(md,base,native)if not x['pass']];ck('raw resource document mutant detected '+name,bool(failed),failed);write(o/('mutant_'+name+'.json'),md);muts.append({'name':name,'failed_controls':failed})
 span_mut=bytearray(span);struct.pack_into('<Q',span_mut,0x70,struct.unpack_from('<Q',span_mut,0x70)[0]^1);ck('independent raw packed-index mutation detected',(struct.unpack_from('<Q',span_mut,0x70)[0]&0x7ffff)!=2577);(o/'mutant_marker_span.bin').write_bytes(span_mut)
 write(o/'tests.json',T);write(o/'evidence.json',{'status':'PRIVATE_STRUCTURAL_PROPOSAL_PASS_NOT_GAMEPLAY_OR_PRODUCTION_APPROVAL','checks':len(T),'resource_document_mutants':muts,'raw_buffer_mutants':1,'proposal':str(rb),'proposal_sha256':sha(rb),'private_raw':str(rb.with_suffix('')),'private_raw_sha256':sha(rb.with_suffix('')),'marker_evidence':str(H/'current_marker_01/evidence.json'),'layout_source':str(layout),'layout_sha256':sha(layout),'NodeRef_hash_source':str(ndhash),'NodeRef_hash_source_sha256':sha(ndhash),'raw_marker_span_offset':4670*144,'raw_marker_span_hex':span.hex(),'raw_marker_span_sha256':hashlib.sha256(span).hexdigest().upper(),'baseline_failures':[t['name']for t in before if not t['pass']],'remaining':['Independent peer review of all source and lifecycle assumptions','Trace actor0 spawnSet actual world provider/current loading eligibility; independent AlwaysLoaded marker is not proof the full physical actor is acquired','Global scene actor acquisition remains engine-dependent unless exact native source evidence closes it','Saved new-controller transition fixtures and in-game call delivery are not executed here'],'candidate_or_runtime_writes':0});print({'checks':len(T),'mutants':4,'evidence':str(o/'evidence.json')})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
