"""New bounded checks plus actual PH3/native controls; all mutations are in memory."""
import sys,unittest,copy,io,collections
from pathlib import Path
W=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(W/'tools/parity_audit'))
from common import *
from model import Resource,compare_graph
from engine import Models
from guard_checks import clauses,contradiction
from identity_registry import bind_registry
from checks import provider_ambiguity

def fact(name,v):return {'$type':'questVarComparison_ConditionType','factName':name,'comparisonType':'Equal','value':v}
def logic(op,*xs):return {'$type':'questLogicalCondition','operation':op,'conditions':list(xs)}
def unsat(x):return all(contradiction(c) for c in clauses(x))

class QR1Tests(unittest.TestCase):
 def test_real_false_delamain_repair_is_rejected(self):
  m=Resource(read(H/'candidate_01/delamain_before.json')).normalize()
  for i in ['1002','1003']:
   c=m['graphs']['root']['nodes'][i]['payload']['condition'];facts=[x for x in walk(c) if x.get('factName')=='PTFRS25_SQ025_FRESH_Issued'];self.assertEqual([x['value'] for x in facts],[0]);self.assertTrue(all(contradiction(row,{'PTFRS25_SQ025_FRESH_Issued':1}) for row in clauses(c)))
 def test_integer_contradiction(self):self.assertTrue(unsat(logic('AND',fact('a',0),fact('a',1))))
 def test_or_is_not_and(self):self.assertFalse(unsat(logic('OR',fact('a',0),fact('a',1))))
 def test_nor_negation(self):self.assertTrue(unsat(logic('AND',fact('a',1),logic('NOR',fact('a',1)))))
 def test_journal_state_contradiction(self):
  a={'$type':'questJournalEntryState_ConditionType','path':{'realPath':'native/q','className':{'$value':'gameJournalQuest'}},'state':'Inactive','inverted':0};b=copy.deepcopy(a);b['state']='Active';self.assertTrue(unsat(logic('AND',a,b)));self.assertFalse(unsat(logic('OR',a,b)))
 def test_unknown_not_assumed_false(self):self.assertFalse(unsat(logic('AND',fact('a',1),{'$type':'UnsupportedNativeCondition'})))
 def test_provider_diagnostics_preserve_competing_mod(self):
  stock={'archive':'base.archive','sha256':'native'};mod={'archive':'thirdparty.archive','sha256':'changed'};r=provider_ambiguity('native.questphase',[stock,mod],[stock]);self.assertEqual([p['archive'] for p in r['providers']],['base.archive','thirdparty.archive']);self.assertEqual(len(r['comparison_candidates']),1)
 def test_identity_registry_rejects_stale_resource(self):
  with self.assertRaises(ValueError):bind_registry({'mappings':{'included':[{'status':'HASH_BOUND','resource':'r','resource_sha256':'old'}]}},{'r':'new'},{'included'})
 def test_identity_registry_does_not_expand_selection(self):
  with self.assertRaises(ValueError):bind_registry({'mappings':{'held':[]}},{},{'included'})
 def test_all_identities_have_corroboration(self):
  i=read(H/'identity_resolution_02.json');self.assertFalse(i['remaining_selected_identity_gaps']);self.assertFalse(i['original_32_remaining']);self.assertTrue(all(x['quest_ids'] for x in i['generic_bindings']))
 def test_fixture_manifests_are_not_identity_authority(self):
  i=read(H/'identity_resolution_02.json');self.assertTrue(all('fixtures' not in Path(p['manifest']).parts for vs in i['mappings'].values() for r in vs for p in r.get('manifest_proofs',[])))
 def test_staged_readback_preserves_all_current_resources(self):
  b=read(H/'baseline.json');r=read(H/'candidate_01/rebuild_01.json');self.assertEqual({x['depot']:x['sha256'] for x in r['resources']},b['private_resources']);self.assertFalse(r['gameplay_delta']);self.assertFalse(r['changed_resources'])
 def test_all_critical_corrected_donors_preserved(self):
  current=read(H/'baseline.json')['private_resources'];r=read(W/'prealpha/consolidation_repair_cr1/candidate_01/selected_resources_01.json')['resources'];ph1=read(W/'prealpha/phone_support_ph1/candidate_03/build_01.json')['resources']
  for x in r:self.assertEqual(current[x['depot']],ph1[x['depot']] if 'fixer_cleanup' in x['depot'] else x['after'])
 def test_compilation_corresponds_to_actual_package(self):
  r=read(H/'candidate_01/compile_01/result.json');self.assertEqual(r['status'],'PASS');self.assertTrue(r['installed_inputs_unchanged']);b=read(H/'baseline.json')
  for row in b['package_files']:
   if row['path'].endswith('.reds'):self.assertEqual(sha(H/'candidate_01/compile_01/scripts/game'/Path(row['path']).relative_to('r6/scripts')),row['after'])

suite=unittest.defaultTestLoader.loadTestsFromTestCase(QR1Tests);stream=io.StringIO();r=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);(H/'candidate_01/tests_01.log').write_text(stream.getvalue(),encoding='utf-8');write(H/'candidate_01/tests_01.json',{'status':'PASS' if r.wasSuccessful() else 'FAIL','tests':r.testsRun,'failures':[str(t) for t,_ in r.failures],'errors':[str(t) for t,_ in r.errors],'scope':'Identity/guard/build/preservation controls; not all quest lifecycle validation'});print(stream.getvalue());raise SystemExit(0 if r.wasSuccessful() else 1)
