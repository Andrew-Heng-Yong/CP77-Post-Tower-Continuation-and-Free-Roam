"""Verify exact v4 source lifecycle and reject v3's unrelated Phone EndCall wait."""
from pathlib import Path
import sys,copy,itertools,collections,json
H=Path(__file__).resolve().parent;W=H.parents[2];sys.path.insert(0,str(H));import propose_listener as P;import propose_listener_v4 as V
from common import read,write,sha,value,walk
from model import Resource
def run(o):
 assert not o.exists();D,pins=P.sources();base=Resource(D[P.ENTRY]).normalize();native=Resource(D[P.ACT]).normalize();p=H/'proposal_readback_04/proposed_entry.NONPRODUCTION.questphase.json';doc=read(p);m=Resource(doc).normalize();g=m['graphs']['root'];cg=m['graphs']['root/65010'];ng=native['graphs']['root/9'];T=[]
 def ck(n,b,e=None):T.append({'name':n,'pass':bool(b),'evidence':e});assert b,n
 ck('actual typed serialization readback resolves handles',not m['errors'],m['errors']);ck('original existing root identifiers and sockets retained',set(base['graphs']['root']['nodes'])<set(g['nodes'])and all(g['nodes'][i]['sockets']==n['sockets']for i,n in base['graphs']['root']['nodes'].items()));ck('only new root IDs65007..65014',set(g['nodes'])-set(base['graphs']['root']['nodes'])==set(map(str,range(65007,65015))))
 for i,n in base['graphs']['root']['nodes'].items():
  if i!='65002':ck('original caller entry payload preserved '+i,g['nodes'][i]['payload']==n['payload'])
 ck('original entry child2 unchanged',m['graphs']['root/2']==base['graphs']['root/2']);guard=g['nodes']['65002']['payload']['condition'];old=base['graphs']['root']['nodes']['65002']['payload']['condition'];ck('original full guard retained as exact AND term',guard['operation']=='AND'and guard['conditions'][0]==old)
 expected=P.logic('OR',[P.atom('ep1_installed',1,'Less'),P.logic('AND',[P.atom(f)for f in P.FACTS]+[P.atom(P.ISSUED)]+[P.atom(f)for f in V.FLIGHTS])]);ck('fresh history and private flights fence exact',guard['conditions'][1]==expected)
 be=set(map(tuple,base['graphs']['root']['edges']));es=set(map(tuple,g['edges']));new={('65003','Out','65007','In'),('65007','False','2','In1'),('65007','True','65008','In'),('65008','Out','65009','In'),('65009','Out','65010','In1'),('65009','Out','2','In1'),('65006','Out','65014','In'),('65014','True','65011','In'),('65011','Out','65012','In'),('65012','CutSource','65010','CutDestination'),('65012','Out','65013','In')};ck('only reviewed future dispatch/cleanup edges',es==(be-{('65003','Out','2','In1')})|new)
 ck('no old/basegame owner cleanup adoption',g['nodes']['65014']['payload']['condition']==P.atom(P.ISSUED,1)and not any(e[0]=='65014'and e[1]=='False'for e in g['edges']));idle=g['nodes']['65011']['payload']['condition'];ck('cleanup uses only three private scene flights',idle==P.logic('AND',[P.atom(f)for f in V.FLIGHTS])and not any(x.get('$type')=='questPhone_ConditionType'for x in walk(idle)))
 for bits in itertools.product([0,1],repeat=3):ck('actual idle condition closed on all active scene states '+str(bits),all(f==0 for f in bits)==all(dict(zip(V.FLIGHTS,bits))[a['type']['factName']]==a['type']['value']for a in idle['conditions']))
 ck('exact marker load guard before any body/scene dispatch',g['nodes']['65009']['payload']['condition']=={'$type':'questNodeLoadingCondition','objectRef':{'$type':'NodeRef','$storage':'string','$value':P.MARKER},'inverted':0})
 ne=set(map(tuple,ng['edges']));ce=set(map(tuple,cg['edges']));replaced={(li,'Out','13',inp)for li,inp,_,_,_,_ in V.ROUTES};adds=set()
 for listener,inputname,fact,outputs,onid,offid in V.ROUTES:
  adds|={(listener,'Out',str(onid),'In'),(str(onid),'Out','13',inputname)};adds|={('13',out,str(offid),'In')for out in outputs}
  ck('scene entry sets only its own private inflight '+inputname,cg['nodes'][str(onid)]['writes']==[{'$type':'questSetVar_NodeType','factName':fact,'setExactValue':1,'value':1}]);ck('scene exit clears only its own private inflight '+inputname,cg['nodes'][str(offid)]['writes']==[{'$type':'questSetVar_NodeType','factName':fact,'setExactValue':1,'value':0}]);ck('clear has only matching terminal source outputs '+inputname,{(e[0],e[1])for e in cg['edges']if e[2]==str(offid)}=={('13',out)for out in outputs})
 ck('exact native child edges retained except three explicit pre-input splices',ce==(ne-replaced)|adds)
 for i,n in ng['nodes'].items():
  expected=copy.deepcopy(n['payload'])
  if i=='13':expected['sceneLocation']['nodeRef']['$value']=P.MARKER
  ck('native listener node payload/socket unchanged '+i,cg['nodes'][i]['payload']==expected and cg['nodes'][i]['sockets']==n['sockets'])
 sp=next(x for x in pins if x['depot'].endswith('mr_hands_combat_zone_default.scene'));sd=read(Path(sp['json']));sm=Resource(sd).normalize()['graphs']['scene'];exits={value(x['name']):str(x['nodeId']['id'])for x in sd['Data']['RootChunk']['exitPoints']};exitproof=[]
 for _,_,fact,outs,_,off in V.ROUTES:
  for name in outs:
   i=exits[name];sn=sm['nodes'][i];ck('private idle clear tied to exact native terminating scene exit '+name,sn['type']=='scnEndNode'and sn['payload']['type']=='Terminating'and ('13',name,str(off),'In')in ce);exitproof.append({'name':name,'scene_node':i,'private_clear_node':str(off),'fact':fact})
 for callback,writer in [('prebrief_out','6'),('prebrief_rejected_out','6'),('debrief_failed_end_out','11'),('debrief_perfect_end_out','10'),('debrief_rejected_failed_out','12'),('debrief_rejected_perfect_out','9')]:ck('real native outcome callback unmodified '+callback,('13',callback,writer,'In')in ce and cg['nodes'][writer]['writes']==ng['nodes'][writer]['writes'])
 for output,writer in [('Holocall INT','8'),('Holocall RET','7')]:ck('native interruption bridge retained without fake idle '+output,('13',output,writer,'In')in ce and not any(e[0]=='13'and e[1]==output and e[2]in ['24','25','26']for e in cg['edges']))
 body=Resource(D[P.BODY]).normalize()['graphs']['root/8/10'];allowed=[];todo=[('200',[])];seen=set()
 while todo:
  i,route=todo.pop()
  if i=='84':allowed=route;break
  if i in seen:continue
  seen.add(i)
  for e in body['edges']:
   if e[0]==i and e[1]!='CutSource'and e[3]!='CutDestination'and e[2]not in ['208','215','217']:todo.append((e[2],route+[e]))
 ck('actual muted body route reaches native Out without selected call producer',bool(allowed)and allowed[0][:2]==['200','True'],allowed);ck('no-scene branch is vacuously idle without unrelated phone event',all(x['type']['value']==0 for x in idle['conditions']))
 v3=Resource(read(H/'proposal_readback_03/proposed_entry.NONPRODUCTION.questphase.json')).normalize();v3c=v3['graphs']['root']['nodes']['65011']['payload']['condition'];ck('prior peer-rejected actual proposal fails exact source-specific idle control',v3c!=idle and any(x.get('$type')=='questPhone_ConditionType'for x in walk(v3c)))
 muts=[]
 for name in ['premature_interrupt_idle','missing_terminal_clear','fake_native_ack']:
  md=copy.deepcopy(doc);rr=Resource(md);phase=next(x for x in rr.handles.values()if x.get('id')==65010 and x.get('$type')=='questPhaseNodeDefinition');child=rr.d(phase['phaseGraph']);nodes={str(rr.d(x)['id']):rr.d(x)for x in child['nodes']}
  if name=='fake_native_ack':rr.d(nodes['21']['type'])['factName']='new_q110_prebrief_rejected_or_end';detected=Resource(md).normalize()['graphs']['root/65010']['nodes']['21']['writes'][0]['factName']!=V.FLIGHTS[0]
  else:
   target=rr.d(next(x for x in nodes['13']['sockets']if value(rr.d(x)['name'])=='prebrief_out'));con=rr.d(target['connections'][-1]);int_socket=rr.hid(next(x for x in nodes['13']['sockets']if value(rr.d(x)['name'])=='Holocall INT'))
   if name=='premature_interrupt_idle':con['source']={'HandleRefId':int_socket}
   else:con['destination']={'HandleRefId':int_socket}
   mm=Resource(md).normalize();mes=set(map(tuple,mm['graphs']['root/65010']['edges']));detected=('13','Holocall INT','24','In')in mes if name=='premature_interrupt_idle'else ('13','prebrief_out','24','In')not in mes
  ck('actual document lifecycle mutant caught '+name,detected);write(o/('mutant_'+name+'.json'),md);muts.append(name)
 write(o/'tests.json',T);write(o/'evidence.json',{'status':'SOURCE_SPECIFIC_PRIVATE_V4_STATIC_CHECKS_PASS_PENDING_INDEPENDENT_PEER','checks':len(T),'raw_document_mutants':muts,'actual_native_muted_route':allowed,'native_terminal_exits':exitproof,'proposal_raw':str(p.with_suffix('')),'proposal_raw_sha256':sha(p.with_suffix('')),'readback_json':str(p),'readback_json_sha256':sha(p),'baseline':'QR6:00 same QR5:08candidate03','saved_policy':'No new-controller adoption for already-entered owners. New cleanup runs only after new Issued1; receipts persist. No-scene routes clear nothing and require no phone event. Missing terminal callbacks preserve active hold.','remaining':['Current actor/community provider follow-up','Independent peer approval of ownership/lifecycle/source proposal','Coordinator final package validation if integrated','Engine scene startup/render/interruption/save-reload observations remain LIVE_ONLY']});print({'checks':len(T),'mutants':len(muts),'evidence':str(o/'evidence.json')})
if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser();a.add_argument('--output',required=True);run(Path(a.parse_args().output))
