"""Offline log-reader regression tests; fixtures never invoke CET or game APIs."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from analyze_gig_live_probe import analyze


def snapshot(post=False, revision=2):
    return {'tag': 'PTFR_GIG_AUDIT', 'probe_revision': revision, 'utc': 'fixture',
            'user_label': 'INTENTIONALLY_WRONG',
            'facts': dict.fromkeys(['PostTowerFreeRoamActive', 'q307_done', 'q307_finished',
                                   'q307_2079', 'q307_main_game_killed'], int(post)),
            'errors': [], 'journal': {'candidate': {'present': True, 'state': 4 if post else 2}},
            'player_before': {'id': '18446744073709551615ULL'},
            'player_after': {'id': '18446744073709551615ULL'},
            'tracked_before': {'present': False}, 'tracked_after': {'present': False},
            'delayed_before': False, 'delayed_after': False}


def line(row):
    return '[2026-10-08 20:20:00 UTC-04:00] [123] ' + json.dumps(row)


class LogTests(unittest.TestCase):
    def read(self, rows, revision=None, suffix=''):
        path = Path('fixture-only-scripting.log')
        raw = ('\n'.join(line(r) for r in rows) + suffix).encode('utf-8')
        with patch.object(Path, 'read_bytes', return_value=raw) as reader:
            result = analyze(path, revision)
            reader.assert_called_once_with()
            return result

    def test_revision_filter_and_complete_pair(self):
        r = self.read([snapshot(revision=1), snapshot(True, 1), snapshot(), snapshot(True)], 2)
        self.assertEqual(r['record_count'], 2)
        self.assertEqual(r['pair']['journal_state_differences']['candidate']['post_name'], 'Failed')
        self.assertEqual(r['summary'][0]['errors'], 0)
        self.assertEqual(r['summary'][0]['numeric_states'], 1)

    def test_reverse_order(self):
        r = self.read([snapshot(True), snapshot()], 2)
        self.assertEqual(r['pair']['journal_states']['candidate']['pre'], 2)

    def test_mixed_revisions_not_paired(self):
        self.assertIsNone(self.read([snapshot(revision=1), snapshot(True)])['pair'])

    def test_duplicates_not_arbitrarily_selected(self):
        self.assertIsNone(self.read([snapshot(), snapshot(), snapshot(True)], 2)['pair'])

    def test_partial_result_not_reconstructed(self):
        tail = '\n[time] [123] {"tag":"PTFR_GIG_AUDIT","delayed_after":'
        r = self.read([snapshot()], 2, tail)
        self.assertEqual(r['incomplete_or_invalid_result_lines'], [2])
        self.assertIsNone(r['pair'])

    def test_command_history_not_result(self):
        r = self.read([snapshot()], 2, '\n[time] [123] > print("PTFR_GIG_AUDIT")')
        self.assertEqual(r['record_count'], 1)
        self.assertEqual(r['incomplete_or_invalid_result_lines'], [])

    def test_unknown_is_not_equal_state_proof(self):
        pre, post = snapshot(), snapshot(True)
        pre['journal']['candidate']['state'] = post['journal']['candidate']['state'] = 'UNKNOWN'
        r = self.read([pre, post], 2)
        self.assertIsNone(r['pair']['journal_states']['candidate']['changed'])

    def test_invalid_state_types(self):
        for value in [True, False, 1.5, '2', -1, 5, None]:
            with self.subTest(value=value):
                pre = snapshot()
                pre['journal']['candidate']['state'] = value
                r = self.read([pre, snapshot(True)], 2)
                self.assertEqual(r['summary'][0]['numeric_states'], 0)
                self.assertEqual(r['pair']['unavailable_state_comparisons'], ['candidate'])

    def test_missing_entry_not_zero(self):
        post = snapshot(True)
        post['journal'] = {}
        r = self.read([snapshot(), post], 2)
        self.assertIsNone(r['pair']['journal_states']['candidate']['post'])

    def test_error_object_and_signed_hash(self):
        pre = snapshot()
        pre['errors'] = {'field': 'getter failed'}
        pre['journal']['candidate']['hash'] = -1292115168
        r = self.read([pre], 2)
        self.assertEqual(r['summary'][0]['errors'], 1)
        self.assertEqual(r['records'][0]['snapshot']['journal']['candidate']['hash'], -1292115168)

    def test_mixed_tower_markers_not_paired(self):
        post = snapshot(True)
        post['facts']['q307_done'] = 0
        self.assertIsNone(self.read([snapshot(), post], 2)['pair'])

    def test_unknowns_and_false_retained(self):
        pre = snapshot()
        original = copy.deepcopy(pre)
        r = self.read([pre], 2)
        self.assertEqual(pre, original)
        self.assertEqual(r['summary'][0]['same_tracking_during_read'], True)
        self.assertEqual(r['summary'][0]['delayed_after'], False)
        self.assertEqual(r['records'][0]['snapshot']['player_after']['id'], '18446744073709551615ULL')


if __name__ == '__main__':
    unittest.main()
