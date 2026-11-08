"""Coordinator implements the source-reviewed Ronald proposal in fresh JSON only."""
from pathlib import Path
import copy,json,sys
from resource_edit import Edit,Resource,STANDARD,value
H=Path(__file__).resolve().parent;W=H.parents[1]
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import read,sha,walk
def main():
 out=H/'coordinator/ronald_02';assert not out.exists();out.mkdir(parents=True)
 plan=H/'worker_a/proposal_02.json';p=read(plan);pins=read(H/'worker_a/enrollment_contract_01.json')['source_pins']
 def doc(depot):
  r=next(x for x in pins if x['depot']==depot);assert sha(r['json'])==r['json_sha256'];return read(r['json'])
 scene_dep=r'towercontinued\b0_story_eight\ronald.scene';phase_dep=r'towercontinued\b0_story_eight\ronald.questphase'
 native_phase=Resource(doc(r'ep1\quest\main_quests\q302\phases\q302_ronald_tree.questphase'))
 native_scene=Resource(doc(r'ep1\quest\main_quests\q302\scenes\q302_05_bar.scene'))
 sd=doc(scene_dep);ed=Edit(sd);sg=ed.r.d(ed.r.root['sceneGraph'])
 ns={str(ed.r.d(n)['nodeId']['id']):ed.r.d(n)for n in sg['graph']}
 ng=native_scene.d(native_scene.root['sceneGraph']);nn={str(native_scene.d(n)['nodeId']['id']):native_scene.d(n)for n in ng['graph']}
 assert '60000'not in ns
 for index in [3,4]:
  ns['839']['options'][index]=ed.clone(nn['839']['options'][index],native_scene)
  ns['839']['outputSockets'][index]=copy.deepcopy(nn['839']['outputSockets'][index])
 receipt=ed.clone(ns['1755'],ed.r,skip=('connections',));receipt['nodeId']['id']=60000
 q=receipt['questNode']['Data'];q['id']=60000;q['type']['Data']['factName']='PTFRQR13_RonaldEnrollment_ConsentEarned'
 # The clone's embedded socket connections are empty in the original1755.
 for socket in q['sockets']:socket['Data'].setdefault('connections',[])
 receipt['outputSockets'][0]['destinations']=[];sg['graph'].append(ed.h(receipt))
 destination=next(copy.deepcopy(d)for n in ns.values()for s in n.get('outputSockets',[])for d in s.get('destinations',[])if d['nodeId']['id']==1755)
 assert destination['isockStamp']['name']==0 and destination['isockStamp']['ordinal']==1
 destination['nodeId']['id']=60000;ns['1755']['outputSockets'][0]['destinations'].append(destination)
 sd=ed.ordered();assert not Resource(sd).normalize()['errors']
 pd=doc(phase_dep);ed=Edit(pd);g=ed.graph('root');parent=ed.node(g,5);child=ed.r.d(parent['phaseGraph']);old=ed.r.normalize()['graphs']['root/5']
 assert not {'203','204','205'}&set(old['nodes'])
 prefab=next(x for x in native_phase.root['phasePrefabs']if value(x['prefabNodeRef'])=='#q302_pr_bar')
 assert not parent['phaseInstancePrefabs'];parent['phaseInstancePrefabs'].append(copy.deepcopy(prefab))
 wait=ed.add(child,{'$type':'questPauseConditionNodeDefinition','id':203,'condition':ed.logic('AND',[
  ed.fact('PTFRQR13_RonaldEnrollment_ConsentEarned',1,'GreaterOrEqual'),ed.fact('q302_ronald_messages_enabled',1,'GreaterOrEqual'),
  ed.fact('PTFRQR13_RonaldEnrollment_ContactIssued'),ed.journal('ep1/contacts/ronald','gameJournalContact','Inactive')])},STANDARD)
 issue=ed.add(child,{'$type':'questFactsDBManagerNodeDefinition','id':204,'type':ed.h({'$type':'questSetVar_NodeType','factName':'PTFRQR13_RonaldEnrollment_ContactIssued','setExactValue':1,'value':1})},STANDARD)
 nm=native_phase.normalize()['graphs']['root/11'];native_graph=native_phase.d(next(native_phase.d(n)for n in native_phase.d(native_phase.root['graph'])['nodes']if native_phase.d(n)['id']==11)['phaseGraph'])
 native_nodes={str(native_phase.d(n)['id']):native_phase.d(n)for n in native_graph['nodes']};cg={'$type':'questGraphDefinition','nodes':[]};cn={}
 keep={'0','158','159','154','23','121','155','156'}
 for ident in nm['nodes']:
  if ident not in keep:continue
  raw=ed.clone(native_nodes[ident],native_phase,skip=('sockets',))
  cn[ident]=ed.add(cg,raw,[(s['name'],s['type'])for s in nm['nodes'][ident]['sockets']])
 for a,s,b,t in nm['edges']:
  if a in keep and b in keep:ed.link(cn[a],s,cn[b],t)
 join_payload=ed.clone(native_nodes['67'],native_phase,skip=('sockets',));join_payload['id']=200;join_payload['inputSocketCount']=2
 join=ed.add(cg,join_payload,[('CutDestination','CutDestination'),('In1','Input'),('In2','Input'),('Out1','Output')])
 term_payload=ed.clone(native_nodes['1'],native_phase,skip=('sockets',));term_payload['id']=201
 term=ed.add(cg,term_payload,[('CutDestination','CutDestination'),('In','Input')])
 for a,s,b,t in [(cn['121'],'Out',join,'In1'),(cn['159'],'Out',join,'In2'),(cn['156'],'Out',join,'In2'),(join,'Out1',term,'In')]:ed.link(a,s,b,t)
 phase_payload=ed.clone(next(native_phase.d(n)for n in native_phase.d(native_phase.root['graph'])['nodes']if native_phase.d(n)['id']==11),native_phase,skip=('sockets','phaseGraph'))
 phase_payload['id']=205;phase_payload['phaseGraph']=ed.h(cg)
 contact=ed.add(child,phase_payload,[('CutDestination','CutDestination'),('In1','Input'),('Out1','Output')])
 ed.link(ed.node(child,2),'Out',wait,'In');ed.link(wait,'Out',issue,'In');ed.link(issue,'Out',contact,'In1')
 pd=ed.ordered();assert not Resource(pd).normalize()['errors']
 resources=[]
 for dep,d in [(scene_dep,sd),(phase_dep,pd)]:
  f=out/(Path(dep).name+'.json');f.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8');resources.append({'depot':dep,'proposed_json':str(f),'proposed_json_sha256':sha(f)})
 (out/'serialization_plan.json').write_text(json.dumps({'status':'COORDINATOR_JSON_IMPLEMENTATION_PENDING_TYPED_AND_PEER_CHECK','source_plan':str(plan),'source_plan_sha256':sha(plan),'resources':resources},indent=2)+'\n',encoding='utf-8')
 print({'resources':len(resources),'scene_nodes_added':1,'contact_child_nodes':len(cg['nodes']),'runtime_install_writes':0})
if __name__=='__main__':main()
