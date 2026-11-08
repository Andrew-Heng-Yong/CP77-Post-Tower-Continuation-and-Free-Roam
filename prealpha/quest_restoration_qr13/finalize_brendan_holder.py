"""Coordinator closes support-release acknowledgement and old-owner completion paths."""
from pathlib import Path
import hashlib,json
from resource_edit import Edit,Resource,STANDARD,value
H=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def reset(ed,g,model):
 ns={i:ed.node(g,int(i))for i in model['nodes']}
 for i,n in ns.items():n['sockets']=[ed.h({'$type':'questSocketDefinition','name':{'$type':'CName','$storage':'string','$value':s['name']},'type':s['type'],'connections':[]})for s in model['nodes'][i]['sockets']]
 for a,s,b,t in model['edges']:ed.link(ns[a],s,ns[b],t)
 ed.r=Resource(ed.doc);return ns
def unlink(ed,a,s,b,t):
 x,sd=ed.socket(a,s);y,td=ed.socket(b,t);ids=[ed.r.hid(h)for h in sd['connections']if ed.r.hid(ed.r.d(h)['destination'])==str(y)];assert len(ids)==1
 for socket in [sd,td]:socket['connections']=[h for h in socket['connections']if ed.r.hid(h)not in ids]
def main():
 out=H/'coordinator/brendan_06';assert not out.exists();out.mkdir(parents=True)
 p=read(H/'coordinator/brendan_05/serialization_plan.json');d=read(p['resources'][0]['proposed_json']);before=Resource(d).normalize();ed=Edit(d);g=ed.graph('root');ns=reset(ed,g,before['graphs']['root'])
 hg=ed.r.d(ns['1110']['phaseGraph']);hn=reset(ed,hg,before['graphs']['root/1110'])
 unlink(ed,hn['1'],'Out',hn['5'],'In');unlink(ed,hn['5'],'Out',hn['6'],'In');ed.link(hn['1'],'Out',hn['6'],'In')
 hg['nodes']=[h for h in hg['nodes']if ed.r.d(h)['id']!=5];ed.r=Resource(d)
 clear=ed.add(g,{'$type':'questFactsDBManagerNodeDefinition','id':1112,'type':ed.h({'$type':'questSetVar_NodeType','factName':'PTFRQR13_MQ037_FinalSupportHeld','setExactValue':1,'value':0})},STANDARD)
 complete=ed.add(g,{'$type':'questConditionNodeDefinition','id':1113,'condition':ed.logic('AND',[ed.fact('PTFRS23_MQ037_Issued',1),ed.fact('PTFRS23_MQ037_Entered',1)])},[('CutDestination','CutDestination'),('In','Input'),('True','Output'),('False','Output')])
 unlink(ed,ns['34'],'Out1',ns['1007'],'In');unlink(ed,ns['1104'],'False',ns['1002'],'In')
 for a,s,b,t in [(ns['1111'],'False',ns['1007'],'In'),(ns['1110'],'Out1',clear,'In'),(clear,'Out',complete,'In'),(complete,'True',ns['1007'],'In')]:ed.link(a,s,b,t)
 result=ed.ordered();m=Resource(result).normalize();assert not m['errors'],m['errors']
 assert m['graphs']['root/1102']==before['graphs']['root/1102']
 f=out/'mq037.questphase.json';f.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 p.update(status='COORDINATOR_SUPPORT_TERMINATION_ACK_CORRECTED_PENDING_PEER_REVIEW',previous=str(H/'coordinator/brendan_05/serialization_plan.json'),
  resources=[{'depot':p['resources'][0]['depot'],'proposed_json':str(f),'proposed_json_sha256':hashlib.sha256(f.read_bytes()).hexdigest().upper()}],
  termination_fix=['Held remains1 until holderTerminatingOut1 acknowledgement; only outer1112 clears it.','Old body34Out1 Held0 follows1111False directlytoexisting1007; no holder initialization.','New body34Out1 Held1 releasesholder, thenclear/IssuedEntered1 route reachesexisting1007; wrapper cannot terminate before borrowed support release.','Preclaimabort/recheckfalse releasesholder andclearsHeld; Issued0 prevents completion. No automatic blind retry or native clock restart.'])
 (out/'serialization_plan.json').write_text(json.dumps(p,indent=2)+'\n',encoding='utf-8');print({'new_root_holder_ids':[1110,1111,1112,1113],'holder_nodes':len(hg['nodes']),'world_clones':0})
if __name__=='__main__':main()
