import json
import sqlite3
import unittest
from build_registry import create_db
from trace_entries import Tracer

class EntryTests(unittest.TestCase):
    def make_db(self):
        db=sqlite3.connect(':memory:');create_db(db)
        root='towercontinued\\test.questphase';scene='base\\test.scene'
        for rid,depot,support in [(1,root,{}),(2,scene,{'entryPoints':[
          {'name':{'$value':'Play'},'nodeId':{'id':101}}, {'name':{'$value':'Debug'},'nodeId':{'id':102}}]})]:
            db.execute('INSERT INTO resources VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(rid,depot,str(rid),'STOCK','fixture','same'+str(rid),'fixture','fixture','EXPORTED',None,'fixture',json.dumps(support)))
        db.executemany('INSERT INTO graphs VALUES(?,?,?,?)',[(1,'root','quest','[1]'),(2,'scene','scene','[101,102]')])
        nodes=[(1,'root',1,'questInputNodeDefinition',{'socketName':{'$value':'In'}}),
               (1,'root',2,'questSceneNodeDefinition',{'sceneFile':{'DepotPath':{'$value':scene}}}),
               (2,'scene',101,'scnStartNode',{}),(2,'scene',102,'scnStartNode',{}),
               (2,'scene',111,'scnEndNode',{}),(2,'scene',112,'scnEndNode',{})]
        for rid,g,n,t,p in nodes:db.execute('INSERT INTO nodes VALUES(?,?,?,?,?,?,?)',(rid,g,n,t,1,json.dumps(p),'[]'))
        db.executemany('INSERT INTO edges VALUES(?,?,?,?,?,?,?,?)',[
          (1,'root',1,'Out','Output',2,'Play','Input'),
          (2,'scene',101,'out','Output',111,'in','Input'),
          (2,'scene',102,'out','Output',112,'in','Input')])
        return db,root

    def test_only_caller_selected_scene_entry_is_traversed(self):
        db,root=self.make_db();contexts,nodes,links,unknown=Tracer(db).trace(root)
        self.assertIn((2,'scene','Play'),contexts)
        self.assertNotIn((2,'scene','Debug'),contexts)
        self.assertIn((2,'scene',111),nodes)
        self.assertNotIn((2,'scene',112),nodes)
        self.assertFalse(unknown)

    def test_cut_does_not_activate_scene(self):
        db,root=self.make_db();db.execute("UPDATE edges SET source_type='CutSource' WHERE rid=1")
        contexts,nodes,links,unknown=Tracer(db).trace(root)
        self.assertNotIn((2,'scene','Play'),contexts)

    def test_resource_case_alias_preserves_entry_case(self):
        db,root=self.make_db();contexts,nodes,links,unknown=Tracer(db).trace(root.upper())
        self.assertIn((2,'scene','Play'),contexts)
        self.assertFalse(unknown)

    def test_missing_entry_remains_a_boundary(self):
        db,root=self.make_db();db.execute("UPDATE edges SET destination_socket='Missing' WHERE rid=1")
        contexts,nodes,links,unknown=Tracer(db).trace(root)
        self.assertTrue(any(x['kind']=='INPUT_UNRESOLVED' for x in unknown))
        self.assertNotIn((2,'scene',111),nodes)

if __name__=='__main__':unittest.main()
