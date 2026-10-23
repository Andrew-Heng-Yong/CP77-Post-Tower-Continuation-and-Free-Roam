"""Read-only stock failure-edge evidence for fresh/installed-resume exclusivity."""
import hashlib,json,argparse
from pathlib import Path
from inspect import graphs,walk,read,value
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest().upper()
spec=read(HERE/'contract02.json');rows=[];pins={};checks=0
def pin(p):pins[p.relative_to(ROOT).as_posix()]=sha(p);return p
def graph(rel,gp='root'):
 return graphs(pin(ROOT/'research/sidejobs_s24/ep1/native_01/json'/rel))[gp]
def node(g,i):return next(n for n in g['nodes'] if n['id']==i)
def edge(g,e):
 global checks
 assert e in g['edges'],e;checks+=1
def assertion(v,why):
 global checks
 assert v,why;checks+=1
def fact(n,k,v):
 assertion(any(value(x.get('factName'))==k and x.get('value')==v for x in walk(n)),(k,v))
def path(n,p):assertion(any(x.get('realPath')==p for x in walk(n)),p)
pin(HERE/'contract02.json');pin(Path(__file__));pin(HERE/'inspect.py')
for o in spec['owners']:
 if o['key']=='MQ305_FRESH':continue
 root='ep1/quests/minor_quest/'+o['id']
 for depot in o['native_dependencies']:
  p=list((ROOT/'research/sidejobs_s24/ep1').glob('native_*/json/'+depot.replace('\\','/')+'.json'))[0]
  pin(p)
  if not depot.endswith('.questphase'):continue
  for gp,g in graphs(p).items():
   for n in g['nodes']:
    if n['$type']!='questJournalNodeDefinition' or not any(x.get('realPath')==root for x in walk(n)):continue
    for e in g['edges']:
     if e[2]==n['id'] and e[3]=='Failed':rows.append({'owner':o['key'],'source':p.relative_to(ROOT).as_posix(),'graph':gp,'target':n['id'],'edge':e})
oldmq=next(o for o in read(pin(ROOT/'prealpha/sidejobs_s23/ep1/contract.json'))['owners'] if o['key']=='MQ306')
oldcar=read(pin(ROOT/'prealpha/sidejobs_s22/ep1_jobs/admission.json'))
assertion(oldmq['journals'][0]['states']==[1,4],'Old MQ306 rejects Active and Succeeded')
assertion(oldcar['journal_guards'][0]['allowed_states']==[1,4],'Old car route rejects Active and Succeeded')
for f in ('mq306_leaving_ripper','mq306_clinic_reached','mq306_intimidate','mq306_truth','mq306_aaron_intimidate_end'):
 assertion(oldmq['facts_equal'][f]==1,('late preserved marker',f))
assertion(oldmq['facts_equal']['mq306_done']==0 and oldmq['facts_equal']['mq306_finished']==0,'Old MQ306 terminal facts protected')
assertion([(x['graph'],x['target'],x['edge']) for x in rows if x['owner']=='MQ306_FRESH']==[('root',51,[50,'True',51,'Failed']),('root/58',12,[8,'Out',12,'Failed'])],'Exactly the two original phase root-failure writers')
tech=graph('ep1/quest/minor_quests/mq306/phases/mq306_02_tech_expo.questphase.json','root/58')
fact(node(tech,13),'mq306_leaving_ripper',0)
assertion(node(tech,13)['condition']['type']['comparisonType']=='Greater','Late leaving-ripper disables abandon watcher')
for e in ([0,'Out',13,'In'],[13,'Out',14,'In'],[14,'CutSource',2,'CutDestination'],[14,'CutSource',4,'CutDestination'],[14,'CutSource',7,'CutDestination'],[14,'CutSource',10,'CutDestination'],[7,'Out',8,'Active'],[8,'Out',12,'Failed']):edge(tech,e)
mqmain=graph('ep1/quest/minor_quests/mq306/mq306.questphase.json')
for e in ([3,'Out2',35,'In1'],[4,'failed',35,'In1'],[35,'Out1',39,'In1'],[39,'Out1',32,'In'],[32,'Out',31,'In'],[31,'Out',33,'In']):edge(mqmain,e)
fact(node(mqmain,32),'mq306_done',1);fact(node(mqmain,31),'mq306_finished',1);fact(node(mqmain,33),'mq306_active',0)
# The only car-failure entry is downstream of loading-area completion. Its
# first-door objective is already Succeeded; S22 explicitly requires Inactive.
door='ep1/quests/minor_quest/q304_car_retrieval/01_car_retrieval/01_reach_the_door1'
assertion(next(j for j in oldcar['journal_guards'] if j['path']==door)['state']==1,'S22 later-door must remain Inactive')
assertion([(x['graph'],x['target'],x['edge']) for x in rows if x['owner']=='Q304_FRESH']==[('root/355/4',3,[4,'Out',3,'Failed'])],'Exactly one original car root-failure writer')
car=graph('ep1/quest/main_quests/q304/phases/q304_car_retrieval.questphase.json')
for e in ([65,'Out1',66,'In1'],[66,'Out1',80,'In1'],[300,'False',355,'q304_left_behind'],[292,'False',355,'q304_left_behind']):edge(car,e)
assertion([e for e in car['edges'] if e[2]==355 and e[3]=='q304_left_behind']==[[292,'False',355,'q304_left_behind'],[300,'False',355,'q304_left_behind']],'No early independent left-behind root-failure source')
failure=graph('ep1/quest/main_quests/q304/phases/q304_car_retrieval.questphase.json','root/355')
assertion(value(node(failure,3)['socketName'])=='q304_left_behind','Failure input identity')
edge(failure,[3,'Out',4,'In1'])
loading=graph('ep1/quest/main_quests/q304/phases/subphases/q304_car_retrieval_loading_area.questphase.json')
path(node(loading,12),door)
edge(loading,[10,'Out',12,'Succeeded']);edge(loading,[12,'Out',1,'In'])
assertion([e for e in loading['edges'] if e[2]==1]==[[12,'Out',1,'In']],'Every loading-area output crosses Succeeded objective')
assertion(value(node(loading,1)['socketName'])=='Out1','Loading output identity')
# Independent reviewer resolved scene quest-node sockets rather than treating
# every scene journal node's available Failed socket as an executed failure.
scene=read(pin(ROOT/'research/sidejobs_s24/base/ep1_scene_review_01.json'))
reviewer=pin(ROOT/'prealpha/sidejobs_s24/base/review_ep1_scenes.py')
assertion(scene['contract_sha256']==sha(HERE/'contract02.json'),'Scene reviewer bound to final fresh contract')
assertion(scene['reviewer_sha256']==sha(reviewer),'Scene reviewer provenance')
for owner in scene['owners']:
 for s in owner['scenes']:assertion(sha(pin(ROOT/s['path']))==s['sha256'],'Scene bytes reviewed')
 for writer in owner['root_writers']:
  assertion(all(e['input']=='Succeeded' for e in writer['incoming']),'Scene root writer cannot fail root')
result={'status':'PASS_NATIVE_FAILURE_BOUNDARIES','checks':checks,'source_pins':pins,'phase_failure_writers':rows,'scene_review':'research/sidejobs_s24/base/ep1_scene_review_01.json','findings':[
 'Fresh MQ306 and Q304 admission require original started/progress zero and old owner Issued zero. Existing runtime and boot repeat their exact native guards; normal new Active or Succeeded roots reject both installed partial routes.',
 'MQ306 has exactly two questphase root-Failed writes: intro refusal and tech-expo abandonment. Its late leaving_ripper condition cuts the abandonment delay and entry watchers before the Aaron-intimidation aftermath required by S23. Both failure outputs use original cleanup and set done/finished1, which S23 rejects. The scenes add only Succeeded root writes.',
 'Q304 has exactly one questphase root-Failed write, reached from outer/inner garage left-behind handling after loading-area completion. The only loading-area output runs through 01_reach_the_door1 Succeeded. Installed S22 explicitly requires that objective Inactive, so root failure does not reopen its older first-door resume seam. The scenes have no root writers.',
 'No prior owner or native progress/reward facts are changed to establish exclusivity; retained native progress is the boundary.'
 ],'limitations':['Static original-graph and contract proof, not engine scheduling or live gameplay proof. Manual journal/fact tampering or a second ending replay on an already restored branch is outside these fresh admission assumptions.']}
dest=ROOT/'research/sidejobs_s24/ep1/transition_01.json';assert not dest.exists();dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'checks':checks,'phase_failure_writers':len(rows)}))
