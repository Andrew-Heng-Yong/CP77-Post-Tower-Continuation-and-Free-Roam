"""Compare captured getters with pinned native graph data. No game API or save writes."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import unittest

import test_analyze_gig_live_probe

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / 'research/gig_restoration'
NID = 'quests/street_stories/watson/northside_industrial_district/sts_wat_nid_02'
SOURCE = RESEARCH / 'watson_sources/json/base/open_world/street_stories/watson/northside_industrial_district/sts_wat_northside_industrial_district.questphase.json'
INDEX = RESEARCH / 'watson_analysis/analysis.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def audit():
    pins = {SOURCE: '5D3AB6095D0262DECAD105B16C1A57A4B6AD5C297EA8608F4AA245C7DEE07129',
            INDEX: '0E4D0E2BDCDB291B08970980896AE75301FA34740C26FDC9B51DD6DF1AF06B6E'}
    for path, expected in pins.items():
        assert sha(path) == expected, f'Source changed: {path}'
    pair_path = RESEARCH / 'live_pair_v2_20261009.json'
    report = read(pair_path)
    assert report['record_count'] == 2 and not report['incomplete_or_invalid_result_lines']
    pair = report['pair']
    assert pair['probe_revision'] == 2 and not pair['unavailable_state_comparisons']
    assert all(s['errors'] == 0 and s['numeric_states'] == 22 and s['resolved_entries'] == 22
               and s['same_player_during_read'] and s['same_tracking_during_read']
               and s['delayed_before'] is False and s['delayed_after'] is False for s in report['summary'])
    changed = pair['journal_state_differences']
    expected_paths = {NID, NID + '/sts_wat_nid_02', NID + '/sts_wat_nid_02/inside'}
    assert set(changed) == expected_paths | {'ep1/quests/main_quest/q307_before_tomorrow'}
    assert all((changed[p]['pre'], changed[p]['post']) == (2, 4) for p in expected_paths)
    assert all(name.startswith('q307_') or name == 'PostTowerFreeRoamActive' for name in pair['fact_differences'])
    assert len(pair['fact_differences']) == 6

    # Verify text pasted for each observed result against the offline-tested
    # v2 source pin. Treat log text only as bytes; never eval or execute it.
    log = Path(report['log'])
    raw_log = log.read_bytes()
    assert hashlib.sha256(raw_log).hexdigest().upper() == report['log_sha256_at_read']
    log_lines = raw_log.decode('utf-8-sig', errors='replace').splitlines()
    expected_command_hash = read(RESEARCH / 'live_probe_v2_validation.json')['source_sha256']
    command_checks = []
    for record in report['records']:
        command_line = log_lines[record['line'] - 2]
        match = re.fullmatch(r'\[[^\]]+\] \[\d+\] > (do .*probe_revision=2.*)', command_line)
        assert match, 'Expected immediately preceding v2 command text'
        digest = hashlib.sha256((match[1] + '\n').encode('utf-8')).hexdigest().upper()
        assert digest == expected_command_hash, 'Captured command differs from tested v2'
        command_checks.append({'result_line': record['line'], 'source_sha256_with_LF': digest})

    source, index = read(SOURCE), read(INDEX)
    raw_nodes = source['Data']['EmbeddedFiles'][7]['Content']['graph']['Data']['nodes'][3]['Data']['phaseGraph']['Data']['nodes']
    nodes = {n['Data']['id']: n['Data'] for n in raw_nodes}
    graph = next(n['graph'] for n in index['nodes'] if n['node_id'] == 83
                 and n['details'].get('type.Data.path.Data.realPath') == NID + '/sts_wat_nid_02/inside')
    edges = {(e['source_node_id'], e['source_socket'], e['destination_node_id'], e['destination_socket'])
             for e in index['edges'] if e['graph'] == graph}
    required_edges = [
        (3, 'Out', 136, 'In'), (136, 'Out', 81, 'In'), (81, 'Out', 80, 'In'),
        (3, 'Out', 207, 'In'), (207, 'Out', 208, 'In'),
        (3, 'Out', 217, 'In'), (217, 'Out', 287, 'In'),
        (79, 'Out1', 26, 'In'), (79, 'Out1', 48, 'In'),
        (79, 'Out1', 49, 'In'), (79, 'Out1', 127, 'In'),
        (79, 'Out1', 120, 'In'), (79, 'Out1', 141, 'In'),
        (26, 'Out', 47, 'In1'), (48, 'Out', 47, 'In2'),
        (49, 'Out', 47, 'In3'), (127, 'Out', 47, 'In4'),
        (47, 'Out1', 50, 'Succeeded'), (50, 'Out', 63, 'Active'), (63, 'Out', 168, 'In'),
        (168, 'Out', 171, 'In'), (171, 'Out', 172, 'In'), (172, 'Out', 96, 'Succeeded'),
        (96, 'Out', 97, 'Active'), (279, 'Out', 50, 'Succeeded'),
    ]
    assert all(e in edges for e in required_edges)
    assert nodes[81]['type']['Data']['setExactValue'] == 0
    assert nodes[136]['type']['Data']['setExactValue'] == 0
    assert nodes[279]['socketName']['$value'] == 'retrofix'
    assert nodes[208]['type']['Data']['params'][0]['Data']['lootOperations'][0]['Data']['quantity'] == 1
    assert nodes[168]['condition']['Data']['type']['Data']['deviceConditionFunction']['$value'] == 'IsPersonalLinkConnected'
    anchors = sorted({x for e in required_edges for x in (e[0], e[2])})
    suite = unittest.defaultTestLoader.loadTestsFromModule(test_analyze_gig_live_probe)
    result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
    assert result.wasSuccessful(), 'Log-reader regression tests failed'
    preserved = RESEARCH / 'live_probe.lua'
    return {
        'status': 'NATIVE_GETTER_PAIR_CONFIRMED_RESUME_NOT_IMPLEMENTED',
        'sources': {str(p.relative_to(ROOT)): sha(p) for p in [SOURCE, INDEX, pair_path,
                    Path(__file__), ROOT / 'tools/analyze_gig_live_probe.py', ROOT / 'tools/test_analyze_gig_live_probe.py']},
        'probe_revision': 2, 'command_pin_checks': command_checks,
        'native_reads': {'snapshots': 2, 'journal_states_each': 22, 'facts_each': 25, 'getter_errors': 0},
        'analyzer_tests': {'methods': result.testsRun, 'passed': result.wasSuccessful()},
        'verified_graph_edges': len(required_edges), 'graph': graph,
        'edges': required_edges,
        'anchors': [{k: v for k, v in nodes[n].items() if k not in ('sockets', 'phaseGraph')} for n in anchors],
        'observed_state': 'Candidate root, phase and inside are Active pre-Tower and Failed post-Tower. Ten other candidate objectives stay Inactive. This compares saves, not a watched transition.',
        'interpretation': 'The compared journal pattern is consistent with Tower cleanup of an already-started early-stage gig; it is not new-start admission or proof of native execution-token resumption.',
        'rejected_shortcuts': [
            'Normal In1 repeats additive start/glossary writes, the start checkpoint/briefing branch and worker_003 shard injection; idempotence is not established.',
            'Authored retrofix input279 sends node50 Succeeded and advances to authorization; it skips the observed unfinished inside objective.',
            'Entering at hub79 is not read-only: it also ForceOpens a door and disables van interactions. It is a research boundary, not a verified resume point.',
            'Journal changes alone cannot reconstruct terminated gameplay, spawn and device owners.',
        ],
        'next_offline_scope': 'Audit gameplay/community ownership and persisted computer/van/loot/death state before designing a guarded resume adapter. Preserve briefing, rewards and cross-gig journal state.',
        'probe_source_preserved': {'path': str(preserved.relative_to(ROOT)), 'bytes': preserved.stat().st_size,
                                   'sha256': sha(preserved), 'matches_tested_v2': sha(preserved) == expected_command_hash,
                                   'action': 'Left unrelated edit untouched; captured commands were hash-verified instead.'},
        'game_writes': 0, 'save_writes': 0, 'installed': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.resolve()
    destination.relative_to(RESEARCH.resolve())
    assert destination.suffix == '.json' and not destination.exists(), 'Use a new research JSON output.'
    result = audit()
    destination.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('status', 'native_reads', 'analyzer_tests', 'verified_graph_edges', 'probe_source_preserved')}))
