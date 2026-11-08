"""Fault injection on captured real inputs, in memory only. Independent historical oracles."""
from common import *
from model import Resource,compare_graph
from checks import *
import copy,unittest,sys

OUT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('diagnostics/vanilla_parity_20261029_01')
CAP=read(OUT/read(OUT/'capture_pointer.json')['capture'])
ROWS=CAP['resources']
def row(match):return next(r for r in ROWS if match(r) and r.get('json'))

class CorpusMutations(unittest.TestCase):
 def test_ph1_actual_mark_listener_removed(self):
  r=row(lambda r:r['stock'] and r['depot'].endswith('mark_bana_holocall.questphase'));raw=read(r['json']);before=Resource(raw).normalize()
  facts={x['factName'] for n in walk(raw) if n.get('$type')=='questVarComparison_ConditionType' for x in [n] if 'factName'in x}
  self.assertIn('audio_mark_bana_calls_v_start_activate',facts) # native contract oracle, not derived from detector
  mutant=copy.deepcopy(raw)
  for n in walk(mutant):
   if n.get('factName')=='audio_mark_bana_calls_v_start_activate':n['factName']='deliberately_removed_listener'
  after=Resource(mutant).normalize();ds=compare_graph(before,after)
  self.assertTrue(any(d.get('condition_changed') for d in ds))
  available={x['factName'] for n in walk(mutant) if n.get('$type')=='questVarComparison_ConditionType' for x in [n] if 'factName'in x}
  self.assertTrue(phone_contract({'audio_mark_bana_calls_v_start_activate':['scene']},{f:['listener'] for f in available},{})[0]['missing_listener'])
 def test_ph3_actual_root_support_omission(self):
  r=row(lambda r:r['stock'] and r['depot']==r'ep1\quest\holocalls\holocall_initializers_ep1.questphase');j=read(r['json']);m=Resource(j).normalize()
  self.assertIn('#holocalls_studio_ep1',m['root_prefabs'])
  q=copy.deepcopy(j);q['Data']['RootChunk']['phasePrefabs']=[];bad=Resource(q).normalize()
  self.assertEqual(studio_gaps(m['root_prefabs'],bad['root_prefabs']),sorted(m['root_prefabs']))
 def test_cr1_pinned_old_payload_rejected(self):
  repairs=read('prealpha/consolidation_repair_cr1/candidate_01/selected_resources_01.json')['resources'];r=next(r for r in repairs if r['before']!=r['after'])
  self.assertEqual(superseded({r['depot']:r['before']},{r['depot']:r['after']})[0]['expected'],r['after'])
  self.assertEqual(sha(r['donor_raw']),r['after'])
 def test_real_cleanup_connection_removed(self):
  r=row(lambda r:r['depot']==r'towercontinued\gig_phone_u9\fixer_cleanup.questphase');j=read(r['json']);a=Resource(j).normalize()
  # Select a real connection, then remove its handle from both endpoint lists.
  ns=list(walk(j));co=next(n for n in ns if 'HandleId'in n and isinstance(n.get('Data'),dict) and 'source'in n['Data'] and 'destination'in n['Data']);h=co['HandleId']
  q=copy.deepcopy(j)
  for n in walk(q):
   if isinstance(n.get('connections'),list):n['connections']=[x for x in n['connections'] if str(x.get('HandleId',x.get('HandleRefId')))!=str(h)]
  self.assertTrue(any(d['kind']=='EDGE_REMOVED' for d in compare_graph(a,Resource(q).normalize())))
 def test_real_missing_reference_detected(self):
  r=row(lambda r:'sts_ep1_08' in r['depot']);refs=set(depots(read(r['json'])));self.assertTrue(refs)
  victim=sorted(refs)[0];self.assertEqual(unresolved(refs,refs-{victim}),[victim])
 def test_current_root_ids_have_no_ph2_collision(self):
  # The actual historic collision value is independently recorded in PH2 evidence and literal tests.
  from engine import registrations
  regs,errors,_=registrations(Path(read(OUT/'prepared.json')['game']));self.assertFalse([e for e in errors if 'PTFR' in e['file']])
  rows=[r for r in regs if r['parent']==r'ep1\quest\ep1.quest'];self.assertTrue(rows)
  self.assertFalse(registration_collisions(rows,set()))
 def test_held_quest_is_not_selected(self):
  c=read(OUT/'catalogues.json');r=next(r for r in c['quests'] if r['id']=='mq057_motorbreath');self.assertTrue(r['held']);self.assertEqual(r['decision'],'EXCLUDE')
 def test_meredith_unused_native_branch_negative_control(self):
  from model import reachable
  r=row(lambda r:r['stock'] and r['depot']==r'base\quest\main_quests\prologue\q003\scenes\q003_07a_final_corp.scene');m=Resource(read(r['json'])).normalize();g=m['graphs']['scene']
  self.assertEqual(g['entries']['q003_07a_stout_sex_end_in'],'2197');self.assertEqual(g['nodes']['3300']['writes'][0]['factName'],'holo_meredith_calls_v_start_activate');self.assertNotIn('3300',reachable(g['nodes'],g['edges'],['2197']))
 def test_frank_native_ack_alias_control(self):
  r=row(lambda r:r['stock'] and r['depot']==r'base\quest\holocalls\frank\frank_holocall.scene');j=read(r['json']);writes=[n for n in walk(j) if n.get('$type')=='questSetVar_NodeType' and n.get('value')==1]
  self.assertTrue(any(n.get('factName')=='holo_frank_nostra_calls_v_start_done' for n in writes));self.assertFalse(any(n.get('factName')=='holo_frank_calls_v_start_done' for n in writes))

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(CorpusMutations);result=unittest.TextTestRunner(verbosity=2).run(suite)
 write(OUT/'corpus_mutation_tests.json',{'run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'success':result.wasSuccessful(),'scope':'Captured native/current raw JSON mutated in memory only; no runtime resources written','oracles':['Native Mark Bana request literal','Native root studio literal','Pinned CR1 before/after hashes','Actual cleanup connection','Actual graph dependency','All installed XL IDs','Current catalogue hold']})
 raise SystemExit(0 if result.wasSuccessful() else 1)
