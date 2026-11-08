"""NONPRODUCTION hypothesis. Build a private JSON proposal; no candidate/runtime writes.

Passing these structural controls does not resolve scene actor acquisition semantics.
"""
from pathlib import Path
import sys,json,copy
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,write,sha,value,walk
from model import Resource
OLD=W/'prealpha/quest_restoration_qr5/groups/G11/reviews/CVI02_EP1'
ENTRY=r'towercontinued\native_gigs_u9\sts_pac_cvi_02_entry.questphase'
ACT=r'base\open_world\fixers\mr_hands\scenes\mr_hands_new_scenes_activators.questphase'
BODY=r'base\open_world\street_stories\pacifica\coastview\sts_pac_cvi_02\phases\sts_pac_cvi_02.questphase'
EP=r'ep1\quest\ep1.questphase'
FO=r'ep1\openworld\fixers\mr_hands\phases\mr_hands_combat_zone_default.questphase'
FACTS=['new_sts_pac_cvi_02_holocall_prebrief','new_sts_pac_cvi_02_holocall_debrief_failed','new_sts_pac_cvi_02_holocall_debrief_perfect','new_q110_prebrief_rejected_or_end','new_q110_debrief_failed_end','new_q110_debrief_perfect_end','new_q110_rejected_failed_out','new_q110_rejected_perfect_out']
ISSUED='PTFRQR7_CVI02_CustomControllerIssued';RETIRED='PTFRQR7_CVI02_CustomControllerRetired'
MARKER='$/03_night_city/c_pacifica/combat_zone_prefabUEX7DCY/monument_av_prefabCJD7Q4Q/loc_sts_ep1_06_prefab7J2LN5A/loc_sts_ep1_06_openworld_prefabV7KAIGA/mr_hands_combat_zone_default_prefabPY55PSI/#mr_sm_hands_combat_zone_default'
def sources():
 pins=[x for x in read(OLD/'verification_03/source_pins.json')if 'depot'in x];D={x['depot']:read(Path(x['json']))for x in pins};return D,pins
def atom(f,v=0,comparison='Equal'):return {'$type':'questFactsDBCondition','type':{'$type':'questVarComparison_ConditionType','comparisonType':comparison,'factName':f,'value':v}}
def logic(op,children):return {'$type':'questLogicalCondition','operation':op,'conditions':children}
class Edit:
 def __init__(self,doc):
  self.doc=doc;self.r=Resource(doc);self.next=max(int(x)for x in self.r.handles)+1
 def h(self,data):
  h={'HandleId':str(self.next),'Data':data};self.next+=1;return h
 def node(self,g,i):return next(self.r.d(n)for n in g['nodes']if self.r.d(n)['id']==i)
 def socket(self,n,name):
  for s in n['sockets']:
   d=s.get('Data')or self.r.d(s)
   if value(d['name'])==name:return {'HandleId':self.r.hid(s),'Data':d}
  raise KeyError(name)
 def add(self,g,payload,sockets):
  n=copy.deepcopy(payload);n['sockets']=[self.h({'$type':'questSocketDefinition','name':{'$type':'CName','$storage':'string','$value':name},'type':typ,'connections':[]})for name,typ in sockets];g['nodes'].append(self.h(n));return n
 def link(self,a,s,b,t):
  src=self.socket(a,s);dst=self.socket(b,t);c=self.h({'$type':'graphGraphConnectionDefinition','source':{'HandleRefId':src['HandleId']},'destination':{'HandleRefId':dst['HandleId']}});src['Data']['connections'].append(c);dst['Data']['connections'].append({'HandleRefId':c['HandleId']})
 def unlink(self,a,s,b,t):
  src=self.socket(a,s);dst=self.socket(b,t);found=[]
  for c in src['Data']['connections']:
   d=self.r.d(c)
   if d and self.r.hid(d.get('destination'))==dst['HandleId']:found.append(self.r.hid(c))
  assert len(found)==1
  for z in [src,dst]:z['Data']['connections']=[c for c in z['Data']['connections']if self.r.hid(c)not in found]
 def clone_graph(self,source,gp):
  model=source.normalize()['graphs'][gp];g={'$type':'questGraphDefinition','nodes':[]};ns={}
  # Native root/9 contains no nested graphs. Copy payloads; reconstruct every handle and edge.
  for i,n in model['nodes'].items():ns[i]=self.add(g,n['payload'],[(s['name'],s['type'])for s in n['sockets']])
  for a,s,b,t in model['edges']:self.link(ns[a],s,ns[b],t)
  return g
def build(D):
 d=copy.deepcopy(D[ENTRY]);e=Edit(d);g=e.r.d(d['Data']['RootChunk']['graph']);gm=e.r.normalize()['graphs']['root'];oldnodes={i:e.node(g,int(i))for i in gm['nodes']}
 # Original JSON can store a socket definition inside its peer connection. Rebuild
 # every root socket/edge before removing an edge, avoiding orphaned handle refs.
 for i,n in oldnodes.items():n['sockets']=[e.h({'$type':'questSocketDefinition','name':{'$type':'CName','$storage':'string','$value':s['name']},'type':s['type'],'connections':[]})for s in gm['nodes'][i]['sockets']]
 for a,s,b,t in gm['edges']:e.link(oldnodes[a],s,oldnodes[b],t)
 e.r=Resource(d);ns={i:e.node(g,i)for i in [2,65002,65003,65006]}
 original_condition=Resource(d).clean(ns[65002]['condition'])
 future=logic('AND',[atom(f)for f in FACTS]+[atom(ISSUED)])
 ns[65002]['condition']=e.h(logic('AND',[original_condition,logic('OR',[atom('ep1_installed',1,'Less'),future])]))
 standard=[('CutDestination','CutDestination'),('In','Input'),('Out','Output')]
 split=e.add(g,{'$type':'questConditionNodeDefinition','id':65007,'condition':e.h(atom('ep1_installed',0,'Greater'))},[('CutDestination','CutDestination'),('In','Input'),('False','Output'),('True','Output')])
 claim=e.add(g,{'$type':'questFactsDBManagerNodeDefinition','id':65008,'type':e.h({'$type':'questSetVar_NodeType','factName':ISSUED,'setExactValue':1,'value':1})},standard)
 wait=e.add(g,{'$type':'questPauseConditionNodeDefinition','id':65009,'condition':e.h({'$type':'questNodeLoadingCondition','objectRef':{'$type':'NodeRef','$storage':'string','$value':MARKER},'inverted':0})},standard)
 ar=Resource(D[ACT]);am=ar.normalize();phase=copy.deepcopy(am['graphs']['root']['nodes']['9']['payload']);phase['id']=65010;phase['phaseGraph']=e.h(e.clone_graph(ar,'root/9'))
 service=e.add(g,phase,[('CutDestination','CutDestination'),('In1','Input'),('Out1','Output')])
 sg=service['phaseGraph']['Data'];sn=next(n['Data']for n in sg['nodes']if n['Data']['id']==13);sn['sceneLocation']['nodeRef']['$value']=MARKER
 # Restore payload handle boundaries removed by normalization.
 for n in sg['nodes']:
  for key in ['condition','type']:
   if isinstance(n['Data'].get(key),dict)and '$type'in n['Data'][key]:n['Data'][key]=e.h(n['Data'][key])
 end=e.add(g,{'$type':'questPauseConditionNodeDefinition','id':65011,'condition':e.h({'$type':'questSystemCondition','type':e.h({'$type':'questPhone_ConditionType','caller':None,'addressee':None,'callPhase':'EndCall'})})},standard)
 cut=e.add(g,{'$type':'questCutControlNodeDefinition','id':65012,'permanent':0},[('In','Input'),('Out','Output'),('CutSource','CutSource')])
 retired=e.add(g,{'$type':'questFactsDBManagerNodeDefinition','id':65013,'type':e.h({'$type':'questSetVar_NodeType','factName':RETIRED,'setExactValue':1,'value':1})},standard)
 e.unlink(ns[65003],'Out',ns[2],'In1');e.link(ns[65003],'Out',split,'In');e.link(split,'False',ns[2],'In1');e.link(split,'True',claim,'In');e.link(claim,'Out',wait,'In');e.link(wait,'Out',service,'In1');e.link(wait,'Out',ns[2],'In1')
 e.link(ns[65006],'Out',end,'In');e.link(end,'Out',cut,'In');e.link(cut,'CutSource',service,'CutDestination');e.link(cut,'Out',retired,'In')
 # Restore every normalized CHandle boundary and order first handle definitions
 # before references: WolvenKit JSON does not accept forward handle references.
 def wrap(x):
  if isinstance(x,list):return [wrap(z)for z in x]
  if not isinstance(x,dict):return x
  result={}
  for k,v in x.items():
   v=wrap(v)
   if k in ['condition','type']and isinstance(v,dict)and '$type'in v:v=e.h(v)
   if k=='conditions'and isinstance(v,list):v=[e.h(z)if isinstance(z,dict)and '$type'in z else z for z in v]
   result[k]=v
  return result
 d=wrap(d);rr=Resource(d);seen=set()
 def ordered(x):
  if isinstance(x,list):return [ordered(z)for z in x]
  if not isinstance(x,dict):return x
  if 'HandleId'in x or 'HandleRefId'in x:
   k=rr.hid(x)
   if k in ['-1','0']and k not in rr.handles:return x
   if k in seen:return {'HandleRefId':k}
   seen.add(k);return {'HandleId':k,'Data':ordered(rr.handles[k])}
  return {k:ordered(v)for k,v in x.items()}
 return ordered(d)
def run(o):
 assert not o.exists();D,pins=sources();candidate=W/'prealpha/quest_restoration_qr5/candidate_03/archive_source'/ENTRY
 p=next(x for x in pins if x['depot']==ENTRY);assert sha(candidate)==p['raw_sha256']
 d=build(D);m=Resource(d).normalize();assert not m['errors'],m['errors'];write(o/'proposed_entry.NONPRODUCTION.json',d)
 write(o/'plan.json',{'status':'NONPRODUCTION_STRUCTURAL_PROPOSAL_REQUIRES_PEER_AND_SCENE_STARTUP_EVIDENCE','target':ENTRY,'baseline_raw':str(candidate),'baseline_raw_sha256':sha(candidate),'source_pins':pins,'added_local_ids':list(range(65007,65014)),'guarded_native_history':FACTS,'private_receipts':[ISSUED,RETIRED],'marker':MARKER,'scope':'Only fresh ep1-installed initial entry before original65003 is consumed. No retro-adoption of ParentEntered1, changed journals, resets, fake ACKs, world changes, FO1 changes, generic controller changes or native caller body changes.','retirement':'Native ep1 root/10 journal q307 Succeeded OR PONR>=1 →8.Out→9 cut→openworld5; only9.Out→10 writes q307_ep1_killed. Existing original entry retained-session guard is unchanged as an AND term.','cleanup':'After existing OwnerFinished65006 event, wait real Phone EndCall, then cut only new65010 descendant; retain one-time Issued and Retired receipts. No native fact cleanup is synthesized.','missing_gate':'Global scene actor acquisition when physical default0 is unavailable is not proved by selected-input holo-only closure or AlwaysLoaded marker. Do not integrate as a proven full repair until adjudicated.','new_json_sha256':sha(o/'proposed_entry.NONPRODUCTION.json'),'requires':['Independent actual-resource review','WK serialization/readback validation of typed proposal','Owner lifecycle/scene startup decision','Affected final package validation by coordinator if approved']})
 print({'proposal':str(o),'nodes':len(m['graphs']['root']['nodes']),'child_nodes':len(m['graphs']['root/65010']['nodes']),'errors':m['errors']})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
