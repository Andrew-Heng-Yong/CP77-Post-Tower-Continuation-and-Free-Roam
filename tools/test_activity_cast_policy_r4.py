"""New independent R4 tests; do not rerun predecessor generation/install mains."""
import copy
import io
import json
import unittest
from catalog_gig_rollout_r2 import ROOT, read, sha, walk, normalize
from catalog_activity_state_r3 import all_quests, ALIASES
from validate_activity_cast_policy_r4 import PATH, LIVE, ARCHIVAL, cast_verdict, validate
from test_activity_batches_b1 import current_install_check


class CastPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = read(PATH)

    def test_exact_candidate_revision(self):
        self.assertEqual(validate(self.data), {
            'two_year_aware': {'gigs': 34, 'side_and_minor_jobs': 30, 'total': 64},
            'ignore_two_year_gap': {'gigs': 72, 'side_and_minor_jobs': 58, 'total': 130}})

    def test_excluded_actor_all_live_optional_kinds(self):
        for name in ('Panam', 'Panam Palmer', 'Kerry', 'Kerry Eurodyne', 'Judy', 'Judy Alvarez'):
            for kind in LIVE:
                with self.subTest(name=name, kind=kind):
                    self.assertEqual(cast_verdict([{'character': name, 'kind': kind}], 'supporting', True),
                                     'EXCLUDED_PARTICIPANT')

    def test_known_exclusion_dominates_incomplete_audit(self):
        self.assertEqual(cast_verdict([{'character': 'Judy', 'kind': 'optional_message'}], 'unknown', False),
                         'EXCLUDED_PARTICIPANT')

    def test_historical_prerequisite_is_not_live_cast(self):
        for name in ('Panam', 'Kerry', 'Judy', 'Johnny'):
            for kind in ARCHIVAL:
                with self.subTest(name=name, kind=kind):
                    self.assertEqual(cast_verdict([{'character': name, 'kind': kind}], 'none', True),
                                     'CANDIDATE_CAST_COMPATIBLE_NOT_RUNTIME_ADMISSION')

    def test_supporting_johnny_requires_presentation_adapter(self):
        for kind in LIVE:
            self.assertEqual(cast_verdict([{'character': 'Johnny Silverhand', 'kind': kind}], 'supporting', True),
                             'CANDIDATE_VOICE_ONLY_ADAPTATION_REQUIRED')

    def test_johnny_central_always_excluded(self):
        for complete in (False, True):
            self.assertEqual(cast_verdict([], 'central', complete), 'EXCLUDED_JOHNNY_CENTRAL')

    def test_unknown_cannot_prove_absence(self):
        for args in (([], 'none', False), ([], 'unknown', True), ([], 'none', None),
                     ([], 'none', 1), (None, 'none', True), ([], 'invalid', True),
                     ([{'character': 'Judy', 'kind': 'unsupported'}], 'none', True),
                     ([{'character': 'Judy', 'kind': []}], 'none', True),
                     ([{'character': 'Judy', 'kind': {}}], 'none', True),
                     ([None], 'none', True), ([], [], True),
                     ([{'character': '', 'kind': 'live_scene'}], 'none', True)):
            self.assertEqual(cast_verdict(*args), 'DEFER_UNKNOWN')

    def test_contradictory_audit_refuses(self):
        self.assertEqual(cast_verdict([{'character': 'Johnny', 'kind': 'live_scene'}], 'none', True),
                         'DEFER_CONTRADICTORY_AUDIT')

    def test_exact_character_identity_not_substring_search(self):
        self.assertEqual(cast_verdict([{'character': 'PlayerWithJohnnyAppearanceOption', 'kind': 'live_scene'}], 'none', True),
                         'CANDIDATE_CAST_COMPATIBLE_NOT_RUNTIME_ADMISSION')
        self.assertEqual(cast_verdict([{'character': 'Bob Sagan', 'kind': 'live_scene'}], 'none', True),
                         'CANDIDATE_CAST_COMPATIBLE_NOT_RUNTIME_ADMISSION')

    def test_native_positive_message_witnesses(self):
        witnesses = {e['title']: e for e in self.data['still_excluded_examples'] if 'native_witness' in e}
        self.assertEqual(set(witnesses), {'Dazed and Confused', "I'll Fly Away"})
        for title, row in witnesses.items():
            with self.subTest(title=title):
                refs = [n for n in walk(read(ROOT / row['native_source']))
                        if n.get('$type') == 'gameJournalPath' and n.get('realPath') == row['native_witness']]
                self.assertTrue(refs)
                self.assertTrue(all(r['className']['$value'] == 'gameJournalPhoneMessage' for r in refs))

    def test_new_candidate_exact_stock_journal_bindings(self):
        loc = {}
        for file in ('research/misty_viktor_world/bradbury_localization/json/base/localization/en-us/onscreens/onscreens.json.json',
                     'research/misty_viktor_world/street_localization/json/ep1/localization/en-us/onscreens/onscreens.json.json'):
            for e in read(ROOT / file)['Data']['RootChunk']['root']['Data']['entries']:
                loc[str(e['primaryKey'])] = e['femaleVariant']
        quests = []
        for file in ('research/gig_restoration/journal_sources/json/base/journal/cooked_journal.journal.json',
                     'research/phase2b_p2/extracted/json/ep1/journal/cooked_journal.journal.json'):
            quests += all_quests(ROOT / file, loc)
        expected = {'Playing for Keeps': 'sts_wat_lch_05', 'No Easy Way Out': 'mq306_dumpster',
                    'Spellbound': 'mq015_wizardbook', "The Prophet's Song": 'mq026_conspiracy'}
        for title, ident in expected.items():
            with self.subTest(title=title):
                names = {normalize(n) for n in ALIASES.get(title, [title])}
                matched = [q for q in quests if normalize(q['native_title'] or '') in names]
                self.assertEqual(len(matched), 1)
                self.assertEqual(matched[0]['id'], ident)
                self.assertTrue(matched[0]['journal_entries'])

    def test_policy_guard_mutants_rejected(self):
        for key in ('johnny_voice', 'johnny_visible_appearance', 'johnny_central_jobs',
                    'johnny_takeover_or_relic_abilities'):
            mutant = copy.deepcopy(self.data)
            mutant['cast_policy'][key] = not mutant['cast_policy'][key]
            with self.assertRaises(AssertionError):
                validate(mutant)
        for character in ('Panam Palmer', 'Kerry Eurodyne', 'Judy Alvarez'):
            mutant = copy.deepcopy(self.data)
            mutant['cast_policy']['excluded_live_characters'].remove(character)
            with self.assertRaises(AssertionError):
                validate(mutant)

    def test_list_mutants_rejected(self):
        for title in ('Dazed and Confused', "I'll Fly Away", 'Balls to the Wall', "Chippin' In", 'Blistering Love'):
            mutant = copy.deepcopy(self.data)
            mutant['ignore_two_year_gap']['side_and_minor_jobs'].append(title)
            with self.assertRaises(AssertionError):
                validate(mutant)

    def test_runtime_claim_mutants_rejected(self):
        for key, value in (('voice_only_adapter_implemented', True), ('new_adapters', 1),
                           ('installed_changes', 1), ('completed_replay_implemented', True)):
            mutant = copy.deepcopy(self.data)
            mutant['runtime_status'][key] = value
            with self.assertRaises(AssertionError):
                validate(mutant)


def main():
    output = io.StringIO()
    result = unittest.TextTestRunner(stream=output, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(CastPolicyTests))
    checked = current_install_check() if result.wasSuccessful() else []
    report = {'status': 'OFFLINE_R4_POLICY_PASS_NOT_RUNTIME_PROOF' if result.wasSuccessful() else 'FAIL',
              'test_methods': result.testsRun, 'success': result.wasSuccessful(),
              'policy_sha256': sha(PATH), 'validator_sha256': sha(ROOT / 'tools/validate_activity_cast_policy_r4.py'),
              'tests_sha256': sha(ROOT / 'tools/test_activity_cast_policy_r4.py'),
              'candidate_counts': read(PATH)['counts'], 'installed_files_unchanged': checked,
              'protected_inputs_unchanged': len(read(PATH)['protected_inputs']) if result.wasSuccessful() else 0,
              'new_adapters': 0, 'installed_changes': 0, 'game_writes': 0, 'save_writes': 0,
              'test_output': output.getvalue()}
    print(json.dumps(report, indent=2))
    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == '__main__':
    main()
