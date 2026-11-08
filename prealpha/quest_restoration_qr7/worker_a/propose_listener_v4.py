"""NONPRODUCTION v4: replace rejected global phone cleanup with exact scene exits."""
from pathlib import Path
import sys,copy,json
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(H));import propose_listener as P
from common import read,write,sha,value,walk
from model import Resource
FLIGHTS=['PTFRQR7_CVI02_PrebriefInFlight','PTFRQR7_CVI02_FailedInFlight','PTFRQR7_CVI02_PerfectInFlight']
ROUTES=[('17','prebrief_in',FLIGHTS[0],['prebrief_out','prebrief_rejected_out'],21,24),('16','debrief_failed_in',FLIGHTS[1],['debrief_failed_end_out','debrief_rejected_failed_out'],22,25),('18','debrief_perfect_in',FLIGHTS[2],['debrief_perfect_end_out','debrief_rejected_perfect_out'],23,26)]
def resocket(e,g,gp):
 model=e.r.normalize()['graphs'][gp];ns={i:e.node(g,int(i))for i in model['nodes']}
 for i,n in ns.items():n['sockets']=[e.h({'$type':'questSocketDefinition','name':{'$type':'CName','$storage':'string','$value':s['name']},'type':s['type'],'connections':[]})for s in model['nodes'][i]['sockets']]
 for a,s,b,t in model['edges']:e.link(ns[a],s,ns[b],t)
 return ns
def finalize(e,d):
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
 def order(x):
  if isinstance(x,list):return [order(z)for z in x]
  if not isinstance(x,dict):return x
  if 'HandleId'in x or'HandleRefId'in x:
   k=rr.hid(x)
   if k not in rr.handles:return x
   if k in seen:return {'HandleRefId':k}
   seen.add(k);return {'HandleId':k,'Data':order(rr.handles[k])}
  return {k:order(v)for k,v in x.items()}
 return order(d)
def build(D):
 d=P.build(D);e=P.Edit(d);root=e.r.d(d['Data']['RootChunk']['graph']);ns=resocket(e,root,'root');e.r=Resource(d)
 service=ns['65010'];sg=e.r.d(service['phaseGraph']);sn=resocket(e,sg,'root/65010');e.r=Resource(d)
 guard=e.r.d(ns['65002']['condition']);branch=e.r.d(guard['conditions'][1]);fresh=e.r.d(branch['conditions'][1]);fresh['conditions'] += [e.h(P.atom(f))for f in FLIGHTS]
 standard=[('CutDestination','CutDestination'),('In','Input'),('Out','Output')]
 for listener,inputname,fact,outputs,onid,offid in ROUTES:
  on=e.add(sg,{'$type':'questFactsDBManagerNodeDefinition','id':onid,'type':e.h({'$type':'questSetVar_NodeType','factName':fact,'setExactValue':1,'value':1})},standard)
  off=e.add(sg,{'$type':'questFactsDBManagerNodeDefinition','id':offid,'type':e.h({'$type':'questSetVar_NodeType','factName':fact,'setExactValue':1,'value':0})},standard)
  e.unlink(sn[listener],'Out',sn['13'],inputname);e.link(sn[listener],'Out',on,'In');e.link(on,'Out',sn['13'],inputname)
  for out in outputs:e.link(sn['13'],out,off,'In')
 ns['65011']['condition']=e.h(P.logic('AND',[P.atom(f)for f in FLIGHTS]))
 cleanup=e.add(root,{'$type':'questConditionNodeDefinition','id':65014,'condition':e.h(P.atom(P.ISSUED,1))},[('CutDestination','CutDestination'),('In','Input'),('False','Output'),('True','Output')])
 e.unlink(ns['65006'],'Out',ns['65011'],'In');e.link(ns['65006'],'Out',cleanup,'In');e.link(cleanup,'True',ns['65011'],'In')
 return finalize(e,d)
def run(o):
 assert not o.exists();D,pins=P.sources();d=build(D);m=Resource(d).normalize();assert not m['errors'],m['errors'];write(o/'proposed_entry.NONPRODUCTION.json',d)
 scene=next(x for x in pins if x['depot'].endswith('mr_hands_combat_zone_default.scene'));scene_doc=read(Path(scene['json']));sm=Resource(scene_doc).normalize()['graphs']['scene'];exits={value(x['name']):str(x['nodeId']['id'])for x in scene_doc['Data']['RootChunk']['exitPoints']};exitproof=[]
 for _,_,_,outs,_,_ in ROUTES:
  for name in outs:
   i=exits[name];n=sm['nodes'][i];assert n['type']=='scnEndNode'and n['payload']['type']=='Terminating';exitproof.append({'output':name,'node':i,'type':n['type'],'termination':n['payload']['type']})
 write(o/'plan.json',{'status':'NONPRODUCTION_V4_SOURCE_SPECIFIC_IDLE_PROPOSAL_PENDING_INDEPENDENT_REVIEW','supersedes_rejected':'proposal_03 global Phone EndCall cleanup; immutable prior failure retained','target':P.ENTRY,'baseline_raw_sha256':sha(W/'prealpha/quest_restoration_qr5/candidate_03/archive_source'/P.ENTRY),'source_pins':pins,'added_root_ids':list(range(65007,65015)),'new_child_ids':list(range(21,27)),'native_child_node_ids':list(Resource(D[P.ACT]).normalize()['graphs']['root/9']['nodes']),'inflight_receipts':FLIGHTS,'routes':ROUTES,'terminating_exit_proof':exitproof,'cleanup':'Only new Issued1 owners enter cleanup. Existing OwnerFinished →65014 True→65011 waits allthree private inflight0→65012 cutonlynew65010→65013 Retired1. No global phone event and no native ACK reset/fabrication. A no-scene muted route has allthree0 and retires without any unrelated call.','interrupts':'Native Holocall INT/RET callback edges and payloads remain unchanged. They do not clear private inflight because they are not terminating scene exits. Missing terminal output holds cleanup closed instead of claiming idle.','scope':'Only initial future EP1 entry; unchanged original admission is an exact AND term and all8native request/outcome histories plus3private flights/Issued must be0. No already-entered adoption, private world, full PIP/default owner, or changed caller body.','remaining':'Actor provider follow-up and independent static/source review; engine call delivery/render/reload remain LIVE_ONLY after source contracts pass.','proposal_sha256':sha(o/'proposed_entry.NONPRODUCTION.json')});print({'output':str(o),'root_nodes':len(m['graphs']['root']['nodes']),'custom_nodes':len(m['graphs']['root/65010']['nodes']),'terminal_outputs':len(exitproof)})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
