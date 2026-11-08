"""Independent literal fixtures plus deliberate raw-input mutations; never mutates mod files."""
import unittest,copy
from model import Resource,compare_graph,reachable
from checks import *
def fixture():
 # Hand-authored two-entry graph: used branch 1->2->3, unused 8->9; cut 6 must not execute 9.
 ns=[];hid=10;socket={}
 for i,typ,name in [(1,'questInputNodeDefinition','In1'),(2,'questPauseConditionNodeDefinition',None),(3,'questOutputNodeDefinition','Out1'),(6,'questCutControlNodeDefinition',None),(8,'questInputNodeDefinition','Unused'),(9,'questFactsDBManagerNodeDefinition',None)]:
  n={'$type':typ,'id':i,'sockets':[]}
  if name:n['socketName']={'$type':'CName','$value':name}
  if i==2:n['condition']={'HandleId':'300','Data':{'$type':'questFactsDBCondition','type':{'HandleId':'301','Data':{'$type':'questVarComparison_ConditionType','factName':'native_gate','comparisonType':'Equal','value':1}}}}
  for s in ['In','Out','CutDestination','CutSource']:
   h={'HandleId':str(hid),'Data':{'$type':'questSocketDefinition','name':{'$value':s},'type':'Input' if s=='In' else 'Output','connections':[]}};hid+=1;n['sockets'].append(h);socket[(i,s)]=h
  ns.append({'HandleId':str(100+i),'Data':n})
 for ix,(a,s,b,d) in enumerate([(1,'Out',2,'In'),(2,'Out',3,'In'),(8,'Out',9,'In'),(6,'CutSource',9,'CutDestination')]):
  c={'HandleId':str(400+ix),'Data':{'source':{'HandleRefId':socket[a,s]['HandleId']},'destination':{'HandleRefId':socket[b,d]['HandleId']}}};socket[a,s]['Data']['connections'].append(c);socket[b,d]['Data']['connections'].append({'HandleRefId':c['HandleId']})
 return {'Data':{'RootChunk':{'$type':'questQuestPhaseResource','phasePrefabs':[{'$type':'questQuestPrefabEntry','prefabNodeRef':{'$type':'NodeRef','$value':'#studio'}}],'graph':{'HandleId':'1','Data':{'nodes':ns}}}}}
class Mutations(unittest.TestCase):
 def setUp(self):self.raw=fixture();self.a=Resource(self.raw).normalize()
 def test_literal_oracle(self):
  g=self.a['graphs']['root'];self.assertEqual({tuple(e) for e in g['edges']},{('1','Out','2','In'),('2','Out','3','In'),('8','Out','9','In'),('6','CutSource','9','CutDestination')});self.assertEqual(reachable(g['nodes'],g['edges'],['1']),{'1','2','3'});self.assertFalse(self.a['errors'])
 def test_changed_native_entry_condition(self):
  q=copy.deepcopy(self.raw);q['Data']['RootChunk']['graph']['Data']['nodes'][1]['Data']['condition']['Data']['type']['Data']['value']=0
  self.assertTrue(any(d.get('condition_changed') for d in compare_graph(self.a,Resource(q).normalize())))
 def test_missing_branch_and_ack_cleanup_edge(self):
  q=copy.deepcopy(self.raw);ns=q['Data']['RootChunk']['graph']['Data']['nodes'];ns[1]['Data']['sockets'][1]['Data']['connections']=[];ns[2]['Data']['sockets'][0]['Data']['connections']=[]
  d=compare_graph(self.a,Resource(q).normalize());self.assertTrue(any(x['kind']=='EDGE_REMOVED' for x in d));self.assertTrue(any(x['kind']=='BRANCH_BECAME_UNREACHABLE' for x in d))
 def test_unresolved_handle_and_node(self):
  q=copy.deepcopy(self.raw);q['Data']['RootChunk']['graph']['Data']['nodes'][1]['Data']['sockets'][0]['Data']['connections']=[{'HandleRefId':'99999'}]
  self.assertTrue(Resource(q).normalize()['errors'])
 def test_duplicate_node_id(self):
  q=copy.deepcopy(self.raw);q['Data']['RootChunk']['graph']['Data']['nodes'].append(copy.deepcopy(q['Data']['RootChunk']['graph']['Data']['nodes'][0]));self.assertTrue(any(x['kind']=='DUPLICATE_NODE_ID' for x in Resource(q).normalize()['errors']))
 def test_missing_dependency(self):self.assertEqual(unresolved(['a.scene','b.ent'],{'a.scene'}),['b.ent'])
 def test_missing_listener_and_ack(self):
  q=phone_contract({'holo_ana_calls_v_start_activate':['caller']},{},{})[0];self.assertTrue(q['missing_listener']);self.assertTrue(q['missing_ack'])
 def test_missing_cleanup_counter(self):self.assertEqual(cleanup_gap(['holo_a_start_count'],[]),['holo_a_start_count'])
 def test_ph2_real_id_collision(self):
  r=[{'path':r'towercontinued\native_gigs_u9\sts_wat_kab_101_map1.questphase','input_node':'1'},{'path':r'towercontinued\phone_support_ph1\mark_bana.questphase','input_node':'1'}]
  self.assertEqual(registration_collisions(r,set())[0]['id'],40560);r[1]['path']=r'towercontinued\phone_merge_ph2\mark_bana_listener.questphase';self.assertFalse(registration_collisions(r,set()))
 def test_cr1_outdated_donor(self):self.assertEqual(len(superseded({'corrected':'old'},{'corrected':'new'})),1)
 def test_ph3_missing_root_prefabs(self):
  q=copy.deepcopy(self.raw);q['Data']['RootChunk']['phasePrefabs']=[];m=Resource(q).normalize();self.assertEqual(studio_gaps(self.a['root_prefabs'],m['root_prefabs']),['#studio']);self.assertTrue(any(x['kind']=='RESOURCE_METADATA_CHANGED' for x in compare_graph(self.a,m)))
 def test_nested_phase_removal(self):
  q=copy.deepcopy(self.raw);n=q['Data']['RootChunk']['graph']['Data']['nodes'][1]['Data'];n['phaseGraph']={'HandleId':'900','Data':copy.deepcopy(self.raw['Data']['RootChunk']['graph']['Data'])};a=Resource(q).normalize();del n['phaseGraph'];self.assertTrue(any(x['kind']=='GRAPH_REMOVED' for x in compare_graph(a,Resource(q).normalize())))
 def test_scene_socket_mutation(self):
  q={'Data':{'RootChunk':{'$type':'scnSceneResource','entryPoints':[{'name':{'$value':'entry'},'nodeId':{'id':1}}],'sceneGraph':{'Data':{'graph':[]},'HandleId':'1'}}}}
  q['Data']['RootChunk']['sceneGraph']['Data']['graph']=[{'HandleId':'2','Data':{'$type':'scnStartNode','nodeId':{'id':1},'outputSockets':[{'stamp':{'name':0,'ordinal':0},'destinations':[{'nodeId':{'id':2},'isockStamp':{'name':0,'ordinal':0}}]}]}},{'HandleId':'3','Data':{'$type':'scnEndNode','nodeId':{'id':2},'outputSockets':[]}}]
  a=Resource(q).normalize();q['Data']['RootChunk']['sceneGraph']['Data']['graph'][0]['Data']['outputSockets'][0]['destinations'][0]['isockStamp']['ordinal']=1;self.assertTrue(any(x['kind']=='EDGE_REMOVED' for x in compare_graph(a,Resource(q).normalize())))
 def test_embedded_graph_is_not_omitted(self):
  q=copy.deepcopy(self.raw);embedded=copy.deepcopy(self.raw['Data']['RootChunk'])
  for n in walk(embedded):
   for k in ('HandleId','HandleRefId'):
    if k in n:n[k]=str(int(n[k])+1000)
  q['Data']['EmbeddedFiles']=[{'FileName':{'$value':r'dlc\test\inside.questphase'},'Content':embedded}]
  m=Resource(q).normalize();self.assertEqual(sum(len(g['nodes']) for g in m['graphs'].values()),12);self.assertIn(r'embedded/dlc\test\inside.questphase/root',m['graphs'])
  bad=copy.deepcopy(q);bad['Data']['EmbeddedFiles']=[];self.assertTrue(any(x['kind']=='GRAPH_REMOVED' for x in compare_graph(m,Resource(bad).normalize())))
 def test_native_protocol_alias_not_guessed_from_request(self):
  request='holo_frank_calls_v_start_activate';ack='holo_frank_nostra_calls_v_start_done';c=phone_contract({request:['caller']},{request:['listener'],ack:['waiter']},{ack:['scene']},{request:{'ack':ack,'evidence':'native listener scene'}})[0];self.assertFalse(c['missing_ack']);self.assertEqual(c['expected_ack'],ack)
if __name__=='__main__':unittest.main()
