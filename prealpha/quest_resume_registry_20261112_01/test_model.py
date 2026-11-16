"""Regression controls for nested graph handles and exact stage identity."""
import copy
import json
import unittest
from pathlib import Path
from model import journal_refs, normalize, reachable, resource_refs, walk

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'research/activity_state_r3/native_sources/json/base/quest/minor_quests/mq007/mq007.questphase.json'

class GraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads(SOURCE.read_text(encoding='utf-8-sig'))
        cls.model=normalize(cls.source)

    def test_delivery_and_grant_are_distinct(self):
        g=next(g for g in self.model['graphs'] if g['path']=='root/5')
        n={n['id']:n for n in g['nodes']}
        self.assertIn(('quests/minor_quest/mq007_smartgun/mq007_smartgun/01_deliver_skippy','gameJournalQuestObjective'),journal_refs(n[11]['parameters']))
        self.assertIn('Items.mq007_skippy',json.dumps(n[30]['parameters']))
        self.assertNotIn('Items.mq007_skippy',json.dumps(n[11]['parameters']))

    def test_nested_support_is_not_flattened_into_parent(self):
        graphs={g['path']:g for g in self.model['graphs']}
        self.assertIn('root/5/20',graphs)
        self.assertEqual(13,len(graphs['root/5/20']['nodes']))
        self.assertEqual(74,len(graphs['root/5']['nodes']))

    def test_every_edge_has_local_endpoints(self):
        for g in self.model['graphs']:
            ids={n['id'] for n in g['nodes']}
            for e in g['edges']:
                self.assertIn(e[0],ids);self.assertIn(e[3],ids)

    def test_bad_handle_is_rejected(self):
        o=copy.deepcopy(self.source)
        o['Data']['RootChunk']['graph']['Data']['nodes'][0]={'HandleRefId':'invalid'}
        with self.assertRaises(ValueError):normalize(o)

    def test_duplicate_node_is_rejected(self):
        o=copy.deepcopy(self.source);ns=o['Data']['RootChunk']['graph']['Data']['nodes']
        ns.append(copy.deepcopy(ns[0]))
        with self.assertRaises(ValueError):normalize(o)

    def test_null_connection_is_explicit_without_losing_the_graph(self):
        o=copy.deepcopy(self.source)
        connection=next(x for x in walk(o) if x.get('$type')=='graphGraphConnectionDefinition'
                        and isinstance(x.get('source'),dict) and 'HandleRefId' in x['source'])
        connection['source']=None
        m=normalize(o)
        self.assertEqual(len(self.model['graphs']),len(m['graphs']))
        self.assertTrue(any(g.get('unresolved_connections') for g in m['graphs']))

    def test_cycles_and_disconnected_nodes(self):
        self.assertEqual({1,2,3,4},reachable([1],[(1,2),(2,3),(3,2),(2,4),(8,9)]))

    def test_numeric_resource_reference_preserved(self):
        self.assertEqual(['12345678'],resource_refs({'x':{'DepotPath':{'$storage':'uint64','$value':'12345678'}}}))

    def test_empty_resource_is_not_a_dependency(self):
        self.assertEqual([],resource_refs({'DepotPath':{'$value':'0'}}))

    def test_distinct_parallel_connections_are_preserved(self):
        def ref(n):return {'HandleRefId':str(n)}
        def handle(n,x):return {'HandleId':str(n),'Data':x}
        def connection(n):return handle(n,{'$type':'graphGraphConnectionDefinition','source':ref(2),'destination':ref(3)})
        source=handle(2,{'name':{'$value':'Out'},'type':'Output','connections':[connection(4),connection(5)]})
        dest=handle(3,{'name':{'$value':'In'},'type':'Input','connections':[ref(4),ref(5)]})
        obj={'Data':{'RootChunk':{'$type':'questQuestPhaseResource','graph':handle(0,{'nodes':[
          handle(6,{'$type':'questInputNodeDefinition','id':1,'socketName':{'$value':'In1'},'sockets':[source]}),
          handle(7,{'$type':'questOutputNodeDefinition','id':2,'socketName':{'$value':'Out'},'sockets':[dest]})]})}}}
        g=normalize(obj)['graphs'][0]
        self.assertEqual(2,len(g['edges']))
        self.assertEqual(g['edges'][0],g['edges'][1])

if __name__=='__main__':unittest.main()
