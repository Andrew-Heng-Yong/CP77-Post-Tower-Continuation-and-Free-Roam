"""Coordinator correction: gated native-support lifetime around the final adapter."""
from pathlib import Path
import copy,json
from resource_edit import Edit,Resource,STANDARD,value
H=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
 out=H/'coordinator/brendan_05';assert not out.exists();out.mkdir(parents=True)
 plan=read(H/'coordinator/brendan_03/serialization_plan.json');doc=read(plan['resources'][0]['proposed_json']);before=Resource(doc).normalize();ed=Edit(doc);g=ed.graph('root')
 # Rebuild peer socket definitions before removing one edge; preserve names and topology.
 ns={i:ed.node(g,int(i))for i in before['graphs']['root']['nodes']}
 for i,n in ns.items():n['sockets']=[ed.h({'$type':'questSocketDefinition','name':{'$type':'CName','$storage':'string','$value':s['name']},'type':s['type'],'connections':[]})for s in before['graphs']['root']['nodes'][i]['sockets']]
 for a,s,b,t in before['graphs']['root']['edges']:ed.link(ns[a],s,ns[b],t)
 ed.r=Resource(doc);held='PTFRQR13_MQ037_FinalSupportHeld'
 assert not {'1110','1111'}&set(before['graphs']['root']['nodes'])
 for ident in [1002,1004]:
  arm=ed.r.d(ed.r.d(ns[str(ident)]['condition'])['conditions'][1]);arm['conditions'].append(ed.fact(held))
 for ident,number in [(1100,0),(1101,1),(1104,1)]:ed.r.d(ns[str(ident)]['condition'])['conditions'].append(ed.fact(held,number))
 providers=read(H/'brendan_provider_validation_01/manifest.json');native=Resource(read(next(r['json']for r in providers['resources']if r['depot'].endswith('mq037_brendan.questphase'))))
 cg={'$type':'questGraphDefinition','nodes':[]}
 entry=ed.add(cg,{'$type':'questInputNodeDefinition','id':0,'socketName':{'$type':'CName','$storage':'string','$value':'In1'}},[('Out','Output')])
 release=ed.add(cg,{'$type':'questInputNodeDefinition','id':1,'socketName':{'$type':'CName','$storage':'string','$value':'Release'}},[('Out','Output')])
 def setter(ident,number):return ed.add(cg,{'$type':'questFactsDBManagerNodeDefinition','id':ident,'type':ed.h({'$type':'questSetVar_NodeType','factName':held,'setExactValue':1,'value':number})},STANDARD)
 own=setter(2,1);clear=setter(5,0)
 loaded=[]
 for ref in ['#mq037_com_characters','#mq037_tr_theo_final']:
  loaded.append(ed.h({'$type':'questNodeLoadingCondition','objectRef':{'$type':'NodeRef','$storage':'string','$value':ref},'inverted':0}))
 wait=ed.add(cg,{'$type':'questPauseConditionNodeDefinition','id':3,'condition':ed.logic('AND',loaded)},STANDARD)
 ready=ed.add(cg,{'$type':'questOutputNodeDefinition','id':4,'socketName':{'$type':'CName','$storage':'string','$value':'Ready'},'type':'NonTerminating'},[('In','Input')])
 done=ed.add(cg,{'$type':'questOutputNodeDefinition','id':6,'socketName':{'$type':'CName','$storage':'string','$value':'Out1'},'type':'Terminating'},[('In','Input')])
 for a,s,b,t in [(entry,'Out',own,'In'),(own,'Out',wait,'In'),(wait,'Out',ready,'In'),(release,'Out',clear,'In'),(clear,'Out',done,'In')]:ed.link(a,s,b,t)
 holder=ed.add(g,{'$type':'questPhaseNodeDefinition','id':1110,'phaseInstancePrefabs':copy.deepcopy(native.root['phasePrefabs']),
  'phaseResource':{'DepotPath':{'$type':'ResourcePath','$storage':'uint64','$value':'0'},'Flags':'Soft'},'phaseGraph':ed.h(cg),'saveLock':0,'unfreezingTriggerNodeRef':{'$type':'NodeRef','$storage':'uint64','$value':'0'}},
  [('CutDestination','CutDestination'),('In1','Input'),('Release','Input'),('Ready','Output'),('Out1','Output')])
 guard=ed.add(g,{'$type':'questConditionNodeDefinition','id':1111,'condition':ed.fact(held,1)},[('CutDestination','CutDestination'),('In','Input'),('True','Output'),('False','Output')])
 # Delete exactly selector->actor edge; all other original/new body history stays intact.
 x,sd=ed.socket(ns['1100'],'True');y,td=ed.socket(ns['1101'],'In');matches=[]
 for h in sd['connections']:
  c=ed.r.d(h)
  if ed.r.hid(c['destination'])==str(y):matches.append(ed.r.hid(h))
 assert len(matches)==1
 for socket in [sd,td]:socket['connections']=[h for h in socket['connections']if ed.r.hid(h)not in matches]
 for a,s,b,t in [(ns['1100'],'True',holder,'In1'),(holder,'Ready',ns['1101'],'In'),(ns['1102'],'safe_out',holder,'Release'),(ns['1104'],'False',holder,'Release'),(ns['34'],'Out1',guard,'In'),(guard,'True',holder,'Release')]:ed.link(a,s,b,t)
 result=ed.ordered();m=Resource(result).normalize();assert not m['errors'],m['errors']
 assert m['graphs']['root/1102']==before['graphs']['root/1102'],'Official anti-scene/timer graph must remain exact'
 for ident in ['1005','1006','1007','1008','34','54','80','55']:assert m['graphs']['root']['nodes'][ident]['payload']==before['graphs']['root']['nodes'][ident]['payload']
 from hashlib import sha256
 p=out/'mq037.questphase.json';p.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 prior=copy.deepcopy(plan);prior.update(status='COORDINATOR_GATED_SUPPORT_HOLDER_CORRECTION_PENDING_REVIEW',previous=str(H/'coordinator/brendan_03/serialization_plan.json'),
   resources=[{'depot':plan['resources'][0]['depot'],'proposed_json':str(p),'proposed_json_sha256':sha256(p.read_bytes()).hexdigest().upper()}],
   support_scope_review=str(H/'worker_c/brendan_support_scope_01/review.json'),support_capture=str(H/'brendan_support_capture_01/manifest.json'),
   support_limits=['Exact native prefab references only; no copied world nodes or actor commands.','Machine-spot placement remains OPAQUE. Node loading gates require critical refs before actor absence/safety checks.','Lease held through outside loop and native body; release only safe abort/recheck failure or actual34.Out1 with Held1 guard.','PrivateHeld flag does not alter any native fact or one-time Issued/Entered receipt.'])
 (out/'serialization_plan.json').write_text(json.dumps(prior,indent=2)+'\n',encoding='utf-8');print({'resources':1,'holder_nodes':len(cg['nodes']),'new_root_ids':[1110,1111],'world_clones':0})
if __name__=='__main__':main()
