"""Independent cooked-graph, guard and exact script-delta checks."""
import copy,json
from pathlib import Path
from prepare import WORK,OWNER,NATIVE_OWNER,SCRIPT,read,sha,write

class Resource:
 def __init__(self,doc):
  self.handles={}
  def walk(x):
   if isinstance(x,dict):
    if 'HandleId' in x:
     assert x['HandleId'] not in self.handles
     self.handles[x['HandleId']]=x['Data']
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(doc)
 def deref(self,x):
  if not isinstance(x,dict):return x
  if 'HandleId' in x:return self.handles[x['HandleId']]
  if 'HandleRefId' in x:return self.handles.get(x['HandleRefId'])
  return x
 def plain(self,x):
  if isinstance(x,list):return [self.plain(v) for v in x]
  if not isinstance(x,dict):return x
  if 'HandleId' in x or 'HandleRefId' in x:return self.plain(self.deref(x))
  return {k:self.plain(v) for k,v in x.items()}

def main():
 pins=read(WORK/'inputs.json');gpin=read(WORK/'graph_01/manifest.json');checks=[]
 def check(name,ok):
  assert ok,name
  checks.append(name)
 check('source audit unchanged',sha(WORK/'audit_01.json')==pins['audit_sha256'])
 check('serialized private phase unchanged',sha(gpin['path'])==gpin['sha256'] and sha(gpin['json'])==gpin['json_sha256'])
 d=read(gpin['json']);r=Resource(d);root=d['Data']['RootChunk'];g=r.deref(root['graph'])
 check('no private acquired world support',root['phasePrefabs']==[] and root['inplacePhases']==[])
 nodes={r.deref(h)['id']:r.deref(h) for h in g['nodes']}
 check('eight explicit nodes',set(nodes)==set(range(8)))
 socket_owner={}
 for i,n in nodes.items():
  for h in n['sockets']:
   key=h.get('HandleId',h.get('HandleRefId'));s=r.deref(h)
   socket_owner[key]=(i,s['name']['$value'])
 edges=set()
 for n in nodes.values():
  for hh in n['sockets']:
   socket=r.deref(hh)
   for h in socket['connections']:
    c=r.deref(h)
    a=c['source'].get('HandleId',c['source'].get('HandleRefId'));b=c['destination'].get('HandleId',c['destination'].get('HandleRefId'))
    edges.add((*socket_owner[a],*socket_owner[b]))
 expected={(0,'Out',1,'In'),(1,'Out',2,'In'),(2,'Out',3,'In'),(3,'True',4,'In'),(3,'False',2,'In'),(4,'Out',5,'In'),(5,'Out',6,'In'),(6,'Out',7,'In')}
 check('complete serialized edges',edges==expected)
 c=r.plain(nodes[2]['condition']);check('immediate guard recheck',r.plain(nodes[3]['condition'])==c)
 source=read(pins['shell']['json']);sr=Resource(source);sg=sr.deref(source['Data']['RootChunk']['graph'])
 source_nodes={sr.deref(h)['id']:sr.deref(h) for h in sg['nodes']}
 original=sr.plain(source_nodes[2]['condition'])
 check('all existing genuine completion and ownership gates retained',c['operation']=='AND' and c['conditions'][:len(original['conditions'])]==original['conditions'])
 facts={x['type']['factName']:x['type']['value'] for x in c['conditions']}
 check('all comparisons exact',all(x['$type']=='questFactsDBCondition' and x['type']['comparisonType']=='Equal' for x in c['conditions']))
 check('only applied, permit and one-time receipt added',len(facts)==18 and facts['PTFRMV_Applied']==1 and facts['PTFRWO1_CleanupPermit']==1 and facts['PTFRWO1_CleanupDone']==0)
 def accepts(values):return all(values.get(x['type']['factName'],0)==x['type']['value'] for x in c['conditions'])
 check('qualified state admitted',accepts(facts))
 for name,good in facts.items():
  for bad in (-1,good+1,good+2):
   q=dict(facts);q[name]=bad;check('reject '+name+'='+str(bad),not accepts(q))
 q=dict(facts);q['PTFRWO1_CleanupDone']=1;check('saved completed receipt cannot reacquire',not accepts(q))
 native=read(pins['native_cleanup']['json']);nr=Resource(native);ng=nr.deref(native['Data']['RootChunk']['graph'])
 native22=next(nr.deref(h) for h in ng['nodes'] if nr.deref(h)['id']==22)
 native_params=nr.plain(native22['type'])['params']
 native_pair=next(x for x in native_params if x['prefabNodeRef']['$value']==NATIVE_OWNER)
 toggle=r.plain(nodes[4]['type'])
 expected_pair=copy.deepcopy(native_pair);expected_pair['prefabNodeRef']['$value']=OWNER
 check('only exact native final state on canonical compiled owner',toggle=={'$type':'questTogglePrefabVariant_NodeType','params':[expected_pair]})
 check('final scene off and original street on',[(v['name']['$value'],v['show']) for v in expected_pair['variantStates']]==[('q307_final_scene',0),('q307_final_scene_hide',1)])
 writes=[r.plain(nodes[i]['type']) for i in (1,5,6)]
 check('only private registration, completion and permit writes',[(x['factName'],x['value'],x['setExactValue']) for x in writes]==[('PTFRWO1_CleanupRegistered',1,1),('PTFRWO1_CleanupDone',1,1),('PTFRWO1_CleanupPermit',0,1)])
 check('no spawn, door, journal, reward or scene commands',set(n['$type'] for n in nodes.values())=={'questInputNodeDefinition','questFactsDBManagerNodeDefinition','questPauseConditionNodeDefinition','questConditionNodeDefinition','questWorldDataManagerNodeDefinition','questOutputNodeDefinition'})
 staged=Path(pins['script']['path']).read_text(encoding='utf-8');original_script=(Path(pins['game'])/SCRIPT).read_text(encoding='utf-8-sig')
 check('script input pins',sha(Path(pins['game'])/SCRIPT)==pins['script']['before'] and sha(pins['script']['path'])==pins['script']['after'])
 def method(s,name):
  start=s.index('func '+name+'(');brace=s.index('{',start);depth=1;i=brace+1
  while depth:
   depth+=(s[i]=='{')-(s[i]=='}');i+=1
  return s[start:i]
 for name in ['Completed','Safe','Schedule','OnDetach']:
  check('unchanged existing driver '+name,method(staged,name)==method(original_script,name))
 poll=method(staged,'Poll');oldpoll=method(original_script,'Poll')
 check('existing street activation untouched',poll.replace('    if IsDefined(q) { this.RefreshStreetCleanupPermit(q, p); }\n','')==oldpoll)
 helper=method(staged,'RefreshStreetCleanupPermit')
 check('500 m exclusion and existing idle checks',all(t in helper for t in ['this.Completed(q) && this.Safe(p)','q.GetFact(n"PTFRMV_Applied") == 1','q.GetFact(n"PTFRWO1_CleanupRegistered") == 1','q.GetFact(n"PTFRWO1_CleanupDone") == 0','pos.X + 1475.0','pos.Y - 1080.0','dx * dx + dy * dy > 250000.0']))
 check('permit defaults off and resets on attach','let permit = 0;' in helper and 'SetFact(n"PTFRWO1_CleanupPermit", 0)' in method(staged,'OnAttach'))
 check('source inventory compiles',read(WORK/'compile_01/assessment.json')['status']=='PASS')
 # This compares the serialized action with source and evaluates its guards;
 # it does not label a dispatch receipt as successful live geometry cleanup.
 write(WORK/'assessment.json',dict(status='PASS',checks=len(checks),details=checks,
  phase_sha256=gpin['sha256'],phase_json_sha256=gpin['json_sha256'],facts=facts,edges=sorted(edges),
  exact_native_cleanup_pair=expected_pair,scope='Only the q307 final-scene decoration owner; separate FX, clinic, Zetatech and other native owners are untouched.',
  safety='No acquired prefabs, story progress writes or actor commands; after genuine Tower completion, idle and over 500 m from the affected area.',
  limits=['Native cleanup dispatch and collision/visual release require a live check.','The group also contains original cinematic props/vehicle spawners; the repair uses their authored variant lifecycle rather than issuing separate actor commands.'],game_writes=0,save_writes=0))
 print('PASS:',len(checks),'serialized graph, native-action, negative-guard and script-preservation checks.')
if __name__=='__main__':main()
